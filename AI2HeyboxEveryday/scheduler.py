# -*- coding: utf-8 -*-
"""常驻定时调度器(容器环境无 cron,用本进程替代)

时间表(北京时间, 由 config.json post.*_enabled 控制):
  - weekly_enabled  : 每周一 10:00 → 周榜 (UTC 周一 02:00)
  - daily_enabled   : 每日 09:00 → 日榜 (UTC 01:00)   [当前默认关闭]
  - agi_enabled     : 每日 09:30 → AGI 日报 (UTC 01:30)
    agi_news.py 自带期号防重(知识库同步延迟时无新期则跳过,
    跳过也写当日标记,不触发重试)

自愈能力(v2, 2026-10-18):
  - 启动补发(catch-up): 环境/进程重启后,若当日日榜或本周周榜
    档期已过却未发布(state.json 丢失或无标记),启动时立即补发。
    是否"已发"优先用 小黑盒创作者中心最新帖子 对账(防止 state
    丢失后重复发帖),对账失败则退回 state 判断。
  - 失败重试: 档期任务失败(GitHub 超时/LLM 异常等)后每 30 分钟
    自动重试,单档期每周期最多 3 次,成功即停。
  - 补发冷却: 距上次补发尝试不足 15 分钟不重复补发(防 watchdog
    疯狂拉起时高频触发)。
  - 日志轮转: scheduler.log 超 5MB 清空。

用法:
  nohup python3 scheduler.py >/dev/null 2>&1 &   # 或用 run_scheduler.sh
日志: scheduler.log (同目录)
"""
import datetime
import json
import os
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(BASE, "scheduler.log")
STATE = os.path.join(BASE, "state.json")
CONFIG = os.path.join(BASE, "config.json")
CATCHUP_MARK = os.path.join(BASE, "catchup.at")
MAX_LOG_BYTES = 5 * 1024 * 1024

BJT = datetime.timezone(datetime.timedelta(hours=8))  # 北京时间
UTC = datetime.timezone.utc

DAILY_SLOT = (9, 0)        # 每日 09:00 (北京时间)
WEEKLY_SLOT = (10, 0)      # 周一 10:00 (北京时间)
AGI_SLOT = (9, 30)         # 每日 09:30 (北京时间), 错开周榜
SERIES_SLOT = (12, 10)     # 隔天 12:10 系列档(北京时间)
RETRY_INTERVAL = 30 * 60   # 失败重试间隔(秒)
SLOT_GRACE = 10 * 60       # 正点唤醒宽容窗口(秒): sleep醒来常带毫秒级迟到, 修复边界竞态 2026-11-05
MAX_RETRY = 3              # 每档期每周期最多重试次数
CATCHUP_COOLDOWN = 15 * 60  # 补发尝试冷却(秒)


def active_periods() -> tuple:
    """从 config.json 读取启用的档期; 读不到时退回 daily+weekly 兼容旧配置"""
    try:
        with open(CONFIG) as f:
            cfg = json.load(f)
        post = cfg.get("post", {})
        periods = []
        if post.get("daily_enabled", True):
            periods.append("daily")
        if post.get("weekly_enabled", True):
            periods.append("weekly")
        if post.get("agi_enabled", True):
            periods.append("agi")
        if post.get("series_enabled", True):
            periods.append("series")
        return tuple(periods) if periods else ("weekly",)
    except (OSError, ValueError):
        return ("daily", "weekly", "agi", "series")


def log(msg: str):
    try:
        if os.path.exists(LOG) and os.path.getsize(LOG) > MAX_LOG_BYTES:
            with open(LOG, "w") as f:  # 轮转
                f.write("")
        with open(LOG, "a") as f:
            f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except OSError:
        pass


def beijing_now() -> datetime.datetime:
    return datetime.datetime.now(BJT)


def load_state() -> dict:
    try:
        with open(STATE) as f:
            return json.load(f)
    except (OSError, ValueError):
        pass
    # 2026-11-01 修复: state.json 被沙箱深度回滚清掉 → 从 ~/.secrets 镜像恢复
    # (当天系列被 6 连发的直接原因: state 丢失后 catch-up 误判未发)
    try:
        mirror = os.path.expanduser("~/.secrets/heybox_state_backup.json")
        if os.path.exists(mirror):
            with open(mirror) as f:
                st = json.load(f)
            with open(STATE, "w") as f:
                json.dump(st, f, ensure_ascii=False, indent=2)
            log("   state.json 丢失, 已从 ~/.secrets 镜像恢复")
            return st
    except Exception:
        pass
    return {}


def state_marker(period: str, now=None) -> str:
    """该档期'已完成'时写入 state 的标记值(今日日期 / 本ISO周)"""
    now = now or beijing_now()
    if period in ("daily", "agi", "series"):
        return now.date().isoformat()
    iso = now.isocalendar()
    return f"{iso.year}-W{iso.week}"


def slot_datetime(period: str, now=None) -> datetime.datetime:
    """本周期档期应运行的时刻(北京时间)。daily=今日09:00; weekly=本周一10:00; agi=今日09:30"""
    now = now or beijing_now()
    if period == "daily":
        return now.replace(hour=DAILY_SLOT[0], minute=DAILY_SLOT[1],
                           second=0, microsecond=0)
    if period == "agi":
        return now.replace(hour=AGI_SLOT[0], minute=AGI_SLOT[1],
                           second=0, microsecond=0)
    if period == "series":
        return now.replace(hour=SERIES_SLOT[0], minute=SERIES_SLOT[1],
                           second=0, microsecond=0)
    monday = now.date() - datetime.timedelta(days=now.weekday())
    return datetime.datetime.combine(
        monday, datetime.time(WEEKLY_SLOT[0], WEEKLY_SLOT[1]), BJT)


def _slot_done(period: str, slot_utc) -> bool:
    """该档期在 slot 所在周期是否已完成(state 标记)。防重复发布。"""
    try:
        st = load_state()
    except Exception:
        return False
    bj = slot_utc.astimezone(BJT)
    if period in ("daily", "agi", "series"):
        return st.get("last_" + period) == bj.date().isoformat()
    iso = bj.isocalendar()
    return st.get("last_weekly") == "%d-W%d" % (iso.year, iso.week)


def _defer_next_slot(t, now, period) -> bool:
    """档期时刻 t 已过时是否推到下一周期:
    已发布(state标记, 防重复) 或 错过超过宽容窗口(交由启动补发/巡检兜底) → True;
    刚错过且未发布(<=SLOT_GRACE) → False, 仍返回今日t, 主循环grace内立即触发。
    修复: 原版 `t <= now` 一律推明天, sleep迟醒毫秒级即静默跳档(2026-11-05 AGI 09:30 实证)。"""
    if t > now:
        return False
    return _slot_done(period, t) or (now - t).total_seconds() > SLOT_GRACE


def next_run(period: str) -> datetime.datetime:
    """下一次正常档期(UTC)。北京 09:00 = UTC 01:00;周一 10:00 = UTC 周一 02:00; 09:30 = UTC 01:30"""
    now = datetime.datetime.now(UTC)
    if period == "daily":
        t = now.replace(hour=1, minute=0, second=0, microsecond=0)
        if _defer_next_slot(t, now, "daily"):
            t += datetime.timedelta(days=1)
    elif period == "agi":
        t = now.replace(hour=1, minute=30, second=0, microsecond=0)
        if _defer_next_slot(t, now, "agi"):
            t += datetime.timedelta(days=1)
    elif period == "series":
        # 隔天一班(锚点 2026-10-24 起); 已发过(state)则找下一个班日
        from series_maker import is_series_day
        d = now.date()
        for _ in range(8):
            if is_series_day(d):
                t = datetime.datetime.combine(
                    d, datetime.time(SERIES_SLOT[0], SERIES_SLOT[1]), BJT)
                t = t.astimezone(UTC)
                if t > now and load_state().get("last_series") \
                        != d.isoformat():
                    return t
                # 边界修复(2026-11-05): 刚错过且未发布 → 仍返回今日t, grace内立即触发
                if t <= now and not _slot_done("series", t) \
                        and (now - t).total_seconds() <= SLOT_GRACE:
                    return t
            d += datetime.timedelta(days=1)
        t = now + datetime.timedelta(days=8)
        return t
    else:  # weekly: 每周一北京时间 10:00
        t = now.replace(hour=2, minute=0, second=0, microsecond=0)
        days_ahead = (0 - t.weekday()) % 7  # Monday == 0
        t += datetime.timedelta(days=days_ahead)
        if _defer_next_slot(t, now, "weekly"):
            t += datetime.timedelta(days=7)
    return t


# ---------------------------------------------------------------------------
# 启动补发(catch-up)
# ---------------------------------------------------------------------------

def fetch_recent_posts(limit: int = 25):
    """创作者中心最近帖子(新在前); 返回 [{'time': 北京时间, 'link_id', 'title'}]
    兼容旧调用: 失败返回 None"""
    try:
        sys.path.insert(0, BASE)
        from heybox_client import HeyboxClient
        with open(CONFIG) as f:
            cfg = json.load(f)
        client = HeyboxClient(cfg["cookie"])
        # 2026-11-02 修复: 该API按 create_at 升序返回, 原 offset=0&limit=25
        # 拿到的是最旧的25篇(6月), 补发对账永远看不到今天的帖子。
        # 改为全量分页后取最新 limit 条, 保持"新在前"语义。
        arts = []
        for _off in range(0, 12 * 50, 50):
            data = client.get("/bbs/app/author/concept/article/list", {
                "article_type": "all", "artilce_state": "all",
                "sort_filter": "create_at", "offset": str(_off),
                "limit": "50"})
            # 2026-11-02 修复: articles 与 links 是两个独立数组, 旧写法
            # `articles or links` 在 articles 取完后会把整包 links(旧动态)
            # 误当下一页混入。对账只关心自己发的文章帖 → 只取 articles。
            batch = (data.get("result") or {}).get("articles") or []
            if not batch:
                break
            arts.extend(batch)
            if len(batch) < 50:
                break
        arts.sort(key=lambda a: a.get("create_at") or 0)
        arts = arts[-limit:]
        out = []
        for a in arts:
            ts = a.get("create_at")
            if isinstance(ts, (int, float)) and ts > 10 ** 9:
                out.append({"time": datetime.datetime.fromtimestamp(ts, BJT),
                            "link_id": str(a.get("link_id") or ""),
                            "title": a.get("title") or ""})
        out.reverse()          # 新在前(与原docstring语义一致)
        return out
    except Exception as e:
        log(f"   [warn] 补发对账接口失败,退回 state 判断: {e}")
        return None


def _post_tags_via(client, link_id: str):
    """拉帖子详情, 返回最后一个话题标签块(如 '#GitHub# #开源# ...')
    返回 None = 接口异常/验证码(无法验证); '' = 正常但无标签块"""
    try:
        data = client.get("/bbs/app/link/tree",
                          {"link_id": str(link_id)})
        if data.get("status") != "ok":
            return None   # show_captcha / 限流等 → 无法验证
        text = (((data.get("result") or {}).get("link") or {})
                .get("text") or "[]")
        blocks = json.loads(text)
        # 2026-11-02 修复: 文章模式(link_tag=11)把全部内容(含末尾话题标签行)
        # 合成单个 {"type":"html"} 块, 旧逻辑只认 type=="text" → 对文章帖
        # 永远返回'' → #GitHub# 标签对账失效 → state 清空后周榜/日榜重发
        # (11-02 12:20 与 18:20 两次周榜重发同根因)。
        # 现在兼容 html 块: 去掉标签取纯文本, 返回最后一个含 # 的非空行。
        import re as _re
        parts = []
        for b in blocks:
            t = b.get("text") or ""
            if t:
                parts.append(t)
        plain = _re.sub(r"<[^>]+>", "\n", "\n".join(parts))
        lines = [ln.strip() for ln in plain.splitlines()
                 if "#" in ln and ln.strip()]
        return lines[-1] if lines else ""
    except Exception:
        return None
    return ""


def _p_time(p):
    """兼容 datetime 与 dict 两种帖子表示"""
    return p["time"] if isinstance(p, dict) else p


def _p_link(p):
    return (p.get("link_id") if isinstance(p, dict) else "") or ""


def heal_state(period: str, now=None):
    """API 对账判定'已发'但 state 无记录时补写标记,防重复发布"""
    now = now or beijing_now()
    state = load_state()
    state[f"last_{period}"] = state_marker(period, now)
    _save_state(state)
    log(f"   state.json 已补写 last_{period}={state_marker(period, now)} (API对账)")


def _save_state(state: dict):
    """写 state.json + ~/.secrets 镜像(重启后恢复用)"""
    import shutil
    with open(STATE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    try:
        os.makedirs(os.path.expanduser("~/.secrets"), exist_ok=True)
        shutil.copy2(STATE, os.path.expanduser("~/.secrets/heybox_state_backup.json"))
    except OSError:
        pass


def rebuild_agi_issue_state(posts, tag_lookup) -> None:
    """state 丢失时从创作者中心重建 agi_last_issue(防旧期重发, 2026-10-24)

    依据: 最近一条 #AGI# 标签帖的日期 D → 该期应为 D 日(或其前最近工作日)
    可得的最新期。弱证据: 无 #AGI# 标签可查时, 用 D 日 09:30 后的任意帖
    推定(该时段调度器活着, 日报几乎必然已发)。"""
    state = load_state()
    if state.get("agi_last_issue"):
        return
    if not posts:
        return
    strong_d = weak_d = None
    for p in posts:
        d = _p_time(p).date()
        if strong_d is None and tag_lookup:
            tags = tag_lookup(_p_link(p))
            if tags and "#AGI#" in tags:
                strong_d = d
        if weak_d is None and _p_time(p).hour >= 10:
            weak_d = d
        if strong_d:
            break
    d = strong_d or weak_d
    if d is None:
        return
    while d.weekday() >= 5:      # 周六日无新刊 → 前最近工作日
        d -= datetime.timedelta(days=1)
    state["agi_last_issue"] = d.strftime("%Y%m%d")
    _save_state(state)
    log(f"   state重建: agi_last_issue={state['agi_last_issue']} "
        f"({'#AGI#标签对账' if strong_d else '发帖时间推定'})")


def catch_up_due(period: str, posts, now=None, state=None,
                 tag_lookup=None) -> bool:
    """档期是否需要补发
    posts: 最近帖子列表(新在前; dict 含 time/link_id/title, 或裸 datetime)或 None
    判定规则(宁可少发不重发):
      daily : 今日北京时间 08:55 后已有【GitHub 标签帖】→ 视为已发
      weekly: 本周一 09:55 后已有【GitHub 标签帖】→ 视为已发
      (AGI 日报每天 09:30 先发, 其 #AGI# 标签帖不能顶替周榜/日榜,
       否则会被误判成榜单帖导致漏发 —— 2026-10-19 实际踩过)
    tag_lookup: link_id → 话题标签字符串; None 时退回旧行为(窗口内有帖即已发)
    """
    now = now or beijing_now()
    state = load_state() if state is None else state
    if state.get(f"last_{period}") == state_marker(period, now):
        return False  # state 已记录完成
    if now < slot_datetime(period, now):
        return False  # 档期未到,正常排程接管
    if period == "agi":
        # AGI: 无新期时本来就不发帖,创作者中心对账不适用;
        # 直接跑 agi_news.py,其内部期号防重兜底(已发期自动跳过)
        return True
    if period == "series":
        # 系列: 隔天一班, 非班日不补; state 防重(另有 ~/.secrets 镜像)
        from series_maker import is_series_day, SERIES_DEF
        if not is_series_day(now.date()):
            return False
        # 2026-11-01 修复: 深度回滚清 state 致系列 6 连发(12:21~22:21 每2h一条);
        # 增加创作者中心 API 对账 — 当日已有本系列文章则视为已发并重建期号
        if posts:
            import re as _re
            name2key = {d["name"]: k for k, d in SERIES_DEF.items()}
            for p in posts:
                if _p_time(p).date() != now.date():
                    continue
                title = (p.get("title") or "") if isinstance(p, dict) else ""
                key = next((name2key[nm] for nm in name2key
                            if title.startswith(nm)), None)
                if not key:
                    continue
                m = _re.search(r"第(\d+)期", title)
                state = load_state() if state is None else state
                s = dict((state.get("series") or {}).get(key) or {})
                s["last_date"] = now.date().isoformat()
                if m:
                    s["n"] = int(m.group(1))
                state.setdefault("series", {})[key] = s
                state["last_series"] = state_marker(period, now)
                _save_state(state)
                log(f"   [series] API对账: 今日已有 '{title[:24]}'"
                    f"(第{s.get('n', '?')}期) → 视为已发, 补写 state")
                return False
        return True
    if posts is None:
        return True   # 对账失败:宁可尝试(main.py 层仍有 state 去重)
    if period == "daily":
        cutoff = now.replace(hour=8, minute=55, second=0, microsecond=0)
        window = [p for p in posts
                  if _p_time(p).date() == now.date() and _p_time(p) >= cutoff]
    else:
        cutoff = slot_datetime("weekly", now).replace(hour=9, minute=55)
        window = [p for p in posts if _p_time(p) >= cutoff]
    if not window:
        return True
    # 取窗口内最早(最靠近档期日)的6条做标签对账 — 周榜帖在窗口尾端,
    # 取最新的几条会漏掉它(2026-10-24 实际踩过: 只查最新4条→误判未发→重发)
    check = window[-6:]
    if tag_lookup is None:
        done = True             # 无法验证标签 → 旧行为: 有帖即视为已发
    else:
        done, saw_unverifiable = False, False
        for p in check:
            link = _p_link(p)
            tags = tag_lookup(link)
            if tags is None:
                # 2026-11-02 修复: 单帖验证码/限流先重试一次
                time.sleep(3)
                tags = tag_lookup(link)
            if tags is None:
                saw_unverifiable = True
                continue         # 单帖无法验证 → 跳过
            if "#GitHub#" in tags:
                done = True
                break
        if not done and saw_unverifiable:
            # 2026-11-02 修复: 周榜帖标签查询恰逢验证码(返回None)而窗口内
            # AGI 帖可验签时, 旧逻辑误判"周榜未发"→重发(12:20 实际踩过一次)。
            # 贯彻"宁可少发不重发": 窗口内只要有验不了的帖子就视为已发;
            # 若真漏发, 下一轮巡检对账恢复后仍会补发, 自愈闭环。
            done = True
    if done:
        heal_state(period, now)
        return False
    return True


# ---------------------------------------------------------------------------
# 任务执行
# ---------------------------------------------------------------------------

def task_succeeded(period: str) -> bool:
    return load_state().get(f"last_{period}") == state_marker(period)


def run_task(period: str) -> bool:
    log(f"===== 开始 {period} 任务 =====")
    try:
        if period == "agi":
            cmd = [sys.executable, os.path.join(BASE, "agi_news.py")]
        elif period == "series":
            cmd = [sys.executable, os.path.join(BASE, "series_maker.py"),
                   "--auto"]
        else:
            cmd = [sys.executable, os.path.join(BASE, "main.py"),
                   "--period", period]
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=3600, cwd=BASE)
        tail_out = (r.stdout or "")[-2500:]
        tail_err = (r.stderr or "")[-800:]
        log(f"{period} 退出码 {r.returncode}")
        for line in tail_out.strip().splitlines()[-12:]:
            log(f"  | {line}")
        if tail_err.strip():
            log(f"  stderr: {tail_err.strip()[-500:]}")
    except Exception as e:
        log(f"{period} 任务异常: {e}")
    ok = task_succeeded(period)
    log(f"{period} 本期{'发布成功' if ok else '未成功'}")
    return ok


def catch_up(retry_state: dict, periods: tuple) -> None:
    """启动时补发错过的档期; 失败的任务登记进重试队列"""
    try:
        if time.time() - os.path.getmtime(CATCHUP_MARK) < CATCHUP_COOLDOWN:
            log("启动检查: 距上次补发尝试不足15分钟,跳过")
            return
    except OSError:
        pass
    try:
        open(CATCHUP_MARK, "w").close()
    except OSError:
        pass

    log("启动检查: 对账小黑盒创作者中心...")
    posts = fetch_recent_posts()
    tag_lookup = None
    if posts:
        recent = ", ".join(_p_time(p).strftime("%m-%d %H:%M")
                           for p in posts[:3])
        log(f"   最近帖子: {recent or '无'}")
        # 构造标签查询器: 用话题标签区分榜单帖(#GitHub#)与 AGI 帖(#AGI#)
        try:
            sys.path.insert(0, BASE)
            from heybox_client import HeyboxClient
            with open(CONFIG) as f:
                cfg = json.load(f)
            _client = HeyboxClient(cfg["cookie"])
            _cache = {}

            def tag_lookup(lid: str) -> str:
                if lid not in _cache:
                    _cache[lid] = _post_tags_via(_client, lid)
                return _cache[lid]
        except Exception as e:
            log(f"   [warn] 标签查询客户端构建失败, 退回时间判定: {e}")
    # state 丢失防护: 重建 agi_last_issue, 防止 09:30 补发重发旧期
    if posts:
        try:
            rebuild_agi_issue_state(posts, tag_lookup)
        except Exception as e:
            log(f"   [warn] agi state 重建失败: {e}")
    for period in periods:
        if not catch_up_due(period, posts, tag_lookup=tag_lookup):
            continue
        log(f"启动补发: {period} 档期已过但未发布,立即执行")
        if not run_task(period):
            retry_state[period] = {
                "at": datetime.datetime.now(UTC) +
                      datetime.timedelta(seconds=RETRY_INTERVAL),
                "left": MAX_RETRY}
            log(f"   {period} 补发失败,{RETRY_INTERVAL // 60}分钟后自动重试")


# ---------------------------------------------------------------------------
# 主循环
# ---------------------------------------------------------------------------

def main():
    periods = active_periods()
    slot_desc = {"daily": "每日北京 09:00 日榜", "weekly": "每周一北京 10:00 周榜",
                 "agi": "每日北京 09:30 AGI 日报",
                 "series": "隔天北京 12:10 内容系列(技能/提示词/冷知识轮换)"}
    log("调度器启动(v3): 启用档期 [" + " / ".join(slot_desc[p] for p in periods)
        + "] + 启动补发 + 失败重试")
    retry_state = {}  # period -> {"at": UTC时刻, "left": 剩余重试次数}
    catch_up(retry_state, periods)

    while True:
        now = datetime.datetime.now(UTC)
        cands = [(next_run(p), "slot", p) for p in periods]
        for p, st in retry_state.items():
            if st["left"] > 0:
                cands.append((st["at"], "retry", p))
        cands = [c for c in cands
                 if c[0] > now - datetime.timedelta(seconds=SLOT_GRACE)]
        if not cands:  # 理论不会发生:重试耗尽后 next_run 仍在
            time.sleep(600)
            continue
        target, kind, period = min(cands, key=lambda c: c[0])
        wait = (target - now).total_seconds()
        if wait > 0:
            if kind == "retry":
                log(f"待重试: {period} @ {target.astimezone(BJT).strftime('%H:%M')} "
                    f"(剩 {retry_state[period]['left']} 次)")
            else:
                log(f"下一次: {period} @ "
                    f"{target.astimezone(BJT).strftime('%Y-%m-%d %H:%M')} "
                    f"(约 {wait / 3600:.1f} 小时后)")
            time.sleep(min(wait, 1800))  # 分段睡,周期性重估
            continue

        # 到点执行
        ok = run_task(period)
        if kind == "retry":
            retry_state[period]["left"] -= 1
            if ok or retry_state[period]["left"] <= 0:
                if not ok:
                    log(f"{period} 重试仍失败,已达上限,等待下个周期")
                retry_state.pop(period, None)
            else:
                retry_state[period]["at"] = datetime.datetime.now(UTC) + \
                    datetime.timedelta(seconds=RETRY_INTERVAL)
                log(f"{period} 将于 {RETRY_INTERVAL // 60} 分钟后再次重试 "
                    f"(剩 {retry_state[period]['left']} 次)")
        elif not ok:
            retry_state[period] = {
                "at": datetime.datetime.now(UTC) +
                      datetime.timedelta(seconds=RETRY_INTERVAL),
                "left": MAX_RETRY}
            log(f"{period} 失败,{RETRY_INTERVAL // 60}分钟后自动重试"
                f"(最多 {MAX_RETRY} 次)")
        time.sleep(90)  # 跳过当前分钟,避免边界重复触发


if __name__ == "__main__":
    main()
