#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一自愈 + 当日内容审计(2026-10-31, 用户需求: 巡检时检测当日内容, 缺发即补)

前置: /home/z/.secrets/gh_pat.txt 必须存在(cron 任务步骤1保证)。
用法: timeout 420 python3 heal_audit.py

流程:
  A. GitHub 刷新: vault.json(微博凭据) + 网易云5文件 + 小黑盒4文件
     (沙箱回滚会清掉新文件, 每次运行都从仓库刷新到最新代码)
  B. 恢复微博 config(.secrets + 项目目录双写)
  C. boot_heal.py 拉起三平台调度器(已运行则跳过)
  D. 沉淀 75s 后审计(北京时间):
       微博   : morning 07:30 / yiyan 12:00 / pet 15:00 / history 18:30 / hot 21:30
       网易云 : 每日一歌 08:00(含歌单) / 歌单 gap-fill 08:30 起自查自补
       小黑盒 : AGI 09:30 / 周榜周一 10:00 / 系列隔天 12:10
  E. 缺发处理: 精确 kill 该平台 scheduler.py 进程(按 /proc cwd 匹配),
     watchdog 30s 后重启, 由"启动补发+API对账"完成发布(各平台自带防重);
     小黑盒额外把 catchup.at 回拨 20 分钟解除补发冷却锁;
     平台日志 150s 内有活动(正在补发)则只等待不干预。
  F. 复查并输出报告。
"""
import datetime
import json
import os
import subprocess
import sys
import time
import urllib.request

BJT = datetime.timezone(datetime.timedelta(hours=8))
PAT_FILE = "/home/z/.secrets/gh_pat.txt"
BOOT_HEAL = "/home/z/my-project/scripts/boot_heal.py"

VAULT_REPO = "43aquarius/AI2OpsVault"
NETEASE_REPO = "43aquarius/AI2NeteaseEveryday"
HEYBOX_REPO = "43aquarius/AI2HeyboxEveryday"

WEIBO_DIR = "/home/z/my-project/weibo-agi-poster"
NETEASE_DIR = "/home/z/my-project/netease-music-poster"
HEYBOX_DIR = "/home/z/my-project/github-hot-heybox"

NETEASE_FILES = ["scheduler.py", "daily_post.py", "playlist_maker.py",
                 "netease_client.py", "config.py"]
HEYBOX_FILES = ["series_maker.py", "copy_craft.py", "hotnews_post.py",
                "summarizer.py"]

WEIBO_SLOTS = {"morning": (7, 30), "yiyan": (12, 0), "pet": (15, 0),
               "history": (18, 30), "hot": (21, 30)}
NETEASE_POST_SLOT = (8, 0)
PLAYLIST_GAPFILL_SLOT = (8, 30)
PLAYLIST_LATE = (20, 0)     # 歌单到 20:00 仍未建 → 升级为缺发
AGI_SLOT = (9, 30)
WEEKLY_SLOT = (10, 0)
SERIES_SLOT = (12, 10)

SETTLE_SECS = 75            # 启动补发沉淀时间
RECHECK_SECS = 100          # 触发重启后的复查等待
LOG_ACTIVE_SECS = 150       # 日志多久内有动静算"正在工作"


def log(msg):
    print(f"[heal_audit] {msg}", flush=True)


def beijing_now():
    return datetime.datetime.now(BJT)


# ---------------------------------------------------------------- GitHub 拉取

def gh_fetch(repo, path, dst):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/contents/{path}",
        headers={"Authorization": "token " + open(PAT_FILE).read().strip(),
                 "Accept": "application/vnd.github.v3+json",
                 "User-Agent": "heal-bot"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    import base64
    content = base64.b64decode(data["content"])
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "wb") as f:
        f.write(content)
    return len(content)


def fetch_platform_files():
    """刷新平台代码 + 微博凭据(回滚后新文件全丢, 必须每次重拉)"""
    ok = True
    try:
        import base64
        req = urllib.request.Request(
            f"https://api.github.com/repos/{VAULT_REPO}/contents/vault.json",
            headers={"Authorization": "token " + open(PAT_FILE).read().strip(),
                     "Accept": "application/vnd.github.v3+json",
                     "User-Agent": "heal-bot"})
        with urllib.request.urlopen(req, timeout=30) as r:
            vault = json.loads(base64.b64decode(
                json.load(r)["content"]).decode("utf-8"))
        cfg = {"weibo_cookie": vault["platforms"]["weibo"]["weibo_cookie"],
               "weibo_post": {"agi_enabled": False, "ai_enabled": False},
               "matrix": {"morning_enabled": True, "yiyan_enabled": True,
                          "pet_enabled": True, "history_enabled": True,
                          "hot_enabled": True}}
        for p in (f"/home/z/.secrets/weibo_config.json",
                  os.path.join(WEIBO_DIR, "config.json")):
            with open(p, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        log("微博凭据已从 vault 恢复(双写)")
    except Exception as e:
        ok = False
        log(f"⚠ vault 拉取失败: {e}")
    for repo, files, dst_dir in ((NETEASE_REPO, NETEASE_FILES, NETEASE_DIR),
                                 (HEYBOX_REPO, HEYBOX_FILES, HEYBOX_DIR)):
        for fn in files:
            try:
                n = gh_fetch(repo, fn, os.path.join(dst_dir, fn))
                log(f"刷新 {repo.split('/')[-1]}/{fn} ({n}B)")
            except Exception as e:
                ok = False
                log(f"⚠ 拉取失败 {repo}/{fn}: {e}")
    # 代码标记校验(防旧层代码混入)
    checks = [(os.path.join(NETEASE_DIR, "netease_client.py"), "artist_hot_songs"),
              (os.path.join(NETEASE_DIR, "scheduler.py"), "PLAYLIST_GAPFILL_AT"),
              (os.path.join(HEYBOX_DIR, "summarizer.py"), "_balanced_braces")]
    for path, marker in checks:
        try:
            if marker not in open(path, encoding="utf-8").read():
                ok = False
                log(f"⚠ 代码标记缺失 {os.path.basename(path)}: {marker}")
        except OSError:
            ok = False
            log(f"⚠ 文件不存在: {path}")
    return ok


# ---------------------------------------------------------------- 进程操作

def scheduler_pid(project_dir):
    """按 cwd 精确匹配该项目 scheduler.py 的 PID(0=无)"""
    try:
        out = subprocess.run(["pgrep", "-f", "python3 scheduler.py"],
                             capture_output=True, text=True, timeout=10)
        for pid in (out.stdout or "").split():
            try:
                if os.path.realpath(f"/proc/{pid}/cwd") == \
                        os.path.realpath(project_dir):
                    return int(pid)
            except OSError:
                continue
    except Exception:
        pass
    return 0


def log_active(project_dir, secs=LOG_ACTIVE_SECS):
    """平台目录任一 .log 在 secs 内有更新 → 调度器正在工作"""
    try:
        newest = max(os.path.getmtime(os.path.join(project_dir, f))
                     for f in os.listdir(project_dir) if f.endswith(".log"))
        return time.time() - newest < secs
    except (OSError, ValueError):
        return False


def trigger_restart(project_dir, is_heybox=False):
    """精确 kill 调度器 python 进程, watchdog 30s 后重启触发启动补发"""
    if is_heybox:
        try:  # 解除 15 分钟补发冷却锁
            mark = os.path.join(project_dir, "catchup.at")
            old = time.time() - 20 * 60
            os.utime(mark, (old, old))
        except OSError:
            pass
    pid = scheduler_pid(project_dir)
    if not pid:
        log(f"  调度器未运行, 交由 boot_heal 拉起")
    else:
        try:
            os.kill(pid, 15)
            log(f"  已 kill 调度器 pid={pid}, 等 watchdog 重启...")
        except OSError as e:
            log(f"  kill 失败: {e}")
    for _ in range(14):           # 最多等 70s
        time.sleep(5)
        if scheduler_pid(project_dir):
            log(f"  调度器已重启 pid={scheduler_pid(project_dir)}")
            return True
    log("  watchdog 未拉起, 重跑 boot_heal...")
    subprocess.run([sys.executable, BOOT_HEAL], timeout=150,
                   capture_output=True)
    return bool(scheduler_pid(project_dir))


# ---------------------------------------------------------------- 审计

def read_state(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def audit(now=None):
    """返回 {platform: {"missing": [...], "pending": [...], "notdue": int}}"""
    now = now or beijing_now()
    today = now.strftime("%Y-%m-%d")
    hm = (now.hour, now.minute)
    rep = {}

    st = read_state(os.path.join(WEIBO_DIR, "state.json"))
    miss = [c for c, slot in WEIBO_SLOTS.items()
            if hm >= slot and st.get(f"matrix_{c}_last_date") != today]
    notdue = sum(1 for slot in WEIBO_SLOTS.values() if hm < slot)
    rep["微博"] = {"missing": miss, "pending": [], "notdue": notdue}

    st = read_state(os.path.join(NETEASE_DIR, "state.json"))
    miss, pend = [], []
    if hm >= NETEASE_POST_SLOT:
        if st.get("last_post_date") != today:
            miss.append("每日一歌")
        elif st.get("last_playlist_date") != today:
            if hm >= PLAYLIST_LATE:
                miss.append("歌单(gap-fill超时)")
            else:
                pend.append(f"歌单(gap-fill自补中, {PLAYLIST_LATE[0]:02d}:00 前不干预)")
    rep["网易云"] = {"missing": miss, "pending": pend,
                    "notdue": 0 if hm >= NETEASE_POST_SLOT else 2}

    st = read_state(os.path.join(HEYBOX_DIR, "state.json"))
    miss = []
    if hm >= AGI_SLOT and st.get("last_agi") != today:
        miss.append("AGI日报")
    iso = now.isocalendar()
    if now.weekday() == 0 and hm >= WEEKLY_SLOT and \
            st.get("last_weekly") != f"{iso.year}-W{iso.week}":
        miss.append("周榜")
    try:
        sys.path.insert(0, HEYBOX_DIR)
        from series_maker import is_series_day
        if is_series_day(now.date()) and hm >= SERIES_SLOT and \
                st.get("last_series") != today:
            miss.append("系列")
    except Exception:
        pass
    rep["小黑盒"] = {"missing": miss, "pending": [],
                    "notdue": 0 if hm >= AGI_SLOT else 1}
    return rep


def print_report(rep, tag="审计"):
    for plat, r in rep.items():
        items = []
        for m in r["missing"]:
            items.append(f"❌缺:{m}")
        for p in r["pending"]:
            items.append(f"⏳{p}")
        if r["notdue"]:
            items.append(f"未到档期x{r['notdue']}")
        if not items:
            items = ["✓全部完成"]
        log(f"{tag} {plat}: {' | '.join(items)}")


# ---------------------------------------------------------------- 主流程

def main():
    if not os.path.exists(PAT_FILE):
        log("❌ PAT 缺失, 请先执行 cron 任务步骤1")
        return 1
    log(f"开始 {beijing_now():%F %T}(北京时间)")

    fetch_platform_files()

    r = subprocess.run([sys.executable, BOOT_HEAL], timeout=150,
                       capture_output=True, text=True)
    tail = (r.stdout or "").strip().splitlines()[-3:]
    for line in tail:
        log(f"boot_heal | {line}")

    log(f"等待 {SETTLE_SECS}s 供启动补发/对账执行...")
    time.sleep(SETTLE_SECS)

    rep = audit()
    print_report(rep, "审计")

    plans = [("微博", WEIBO_DIR, False), ("网易云", NETEASE_DIR, False),
             ("小黑盒", HEYBOX_DIR, True)]
    triggered = []
    for plat, dir_, is_hb in plans:
        if not rep[plat]["missing"]:
            continue
        if log_active(dir_):
            log(f"{plat} 缺发但调度器正在工作(日志活跃), 等待自动补发")
            continue
        log(f"{plat} 缺发 {rep[plat]['missing']}, 触发调度器重启补发:")
        trigger_restart(dir_, is_hb)
        triggered.append(plat)

    if triggered:
        log(f"等待 {RECHECK_SECS}s 后复查...")
        time.sleep(RECHECK_SECS)
        rep2 = audit()
        print_report(rep2, "复查")
        still = {p: rep2[p]["missing"] for p in rep2 if rep2[p]["missing"]}
        if still:
            log(f"⚠ 仍有缺发(可能补发进行中, 各平台失败重试机制会继续兜底): {still}")
        else:
            log("✅ 补发完成, 当日应发内容已齐")
    else:
        bad = [p for p in rep if rep[p]["missing"]]
        log("✅ 无需干预, 当日应发内容已齐/未到档期" if not bad
            else f"⚠ 缺发项均在自动补发中: {[ (p, rep[p]['missing']) for p in bad ]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
