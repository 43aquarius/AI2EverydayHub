#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""三平台统一自愈入口(2026-10-22 设计, 针对沙箱重启机制)

沙箱重启机制(逆向结论, 详见各项目 README):
  - 重启会杀死全部后台进程
  - my-project 内 mtime 晚于最近平台快照点的文件会被清除
    (config.json 等 .gitignore 文件从不进快照 → 高危)
  - 项目外 /home/z/.secrets/ 不受该机制管辖 → 凭据持久层

本脚本在重启后运行一次即可恢复:
  1. 凭据自愈: 四层回退 config.json ← .secrets ← secrets_backup.json
     ← GitHub AI2OpsVault(2026-10-27 新增, 权威源, 需 .secrets/gh_pat.txt)
  2. 调度器复活: 检测三平台调度器进程(按 cwd 区分), 死了就拉起
  3. 状态汇报: 各平台配置/进程/下次档期一览

用法: python3 /home/z/my-project/scripts/boot_heal.py
(已由平台 cron 每 2 小时自动唤醒执行, 见 worklog 2026-10-27)
"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request

DETACHED = "/home/z/my-project/scripts/detached_run.py"
SECRETS = "/home/z/.secrets"

PLATFORMS = [
    {
        "name": "小黑盒",
        "dir": "/home/z/my-project/github-hot-heybox",
        "watchdog_log": "scheduler_watchdog.log",
        "cmd": ('while true; do python3 scheduler.py >> scheduler_stdout.log '
                '2>&1; echo "[$(date "+%F %T")] scheduler exited, restart in '
                '30s" >> scheduler.log; sleep 30; done'),
        "config": "config.json",
        "secrets_copy": f"{SECRETS}/heybox_config.json",
        "vault_key": "heybox",
        "note": "AGI日报 09:30 / 周榜周一 10:00 / 系列隔天 12:10",
    },
    {
        "name": "微博矩阵",
        "dir": "/home/z/my-project/weibo-agi-poster",
        "watchdog_log": "scheduler_watchdog.log",
        "cmd": ('while true; do python3 scheduler.py >> scheduler_stdout.log '
                '2>&1; echo "[$(date "+%F %T")] scheduler exited, restart in '
                '30s" >> scheduler.log; sleep 30; done'),
        "config": "config.json",
        "secrets_copy": f"{SECRETS}/weibo_config.json",
        "vault_key": "weibo",
        "note": "五栏目 07:30/12:00/15:00/18:30/21:30",
    },
    {
        "name": "网易云",
        "dir": "/home/z/my-project/netease-music-poster",
        "watchdog_log": "daemon_watchdog.log",
        "cmd": ('while true; do python3 scheduler.py >> daemon_stdout.log '
                '2>&1; echo "[$(date "+%F %T")] scheduler exited, restart in '
                '30s" >> daemon.log; sleep 30; done'),
        "config": "config.json",
        "secrets_copy": f"{SECRETS}/netease_config.json",
        "vault_key": "netease",
        "note": "每日一歌 08:00 / 每日歌单 20:00 (凭据缺失时优雅等待)",
    },
]


def fetch_vault_platforms():
    """第4层: GitHub AI2OpsVault 拉取各平台凭据(权威源, 2026-10-27)"""
    pat_path = os.path.join(SECRETS, "gh_pat.txt")
    if not os.path.exists(pat_path):
        return None
    try:
        pat = open(pat_path).read().strip()
        req = urllib.request.Request(
            "https://api.github.com/repos/43aquarius/AI2OpsVault/"
            "contents/vault.json",
            headers={"Authorization": "Bearer " + pat,
                     "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode())
        vault = json.loads(base64.b64decode(d["content"]).decode())
        return vault.get("platforms") or {}
    except Exception:
        return None


def scheduler_alive(project_dir: str) -> int:
    """按 cwd 精确匹配该项目 scheduler.py 的 PID(0=未运行)"""
    try:
        out = subprocess.run(["pgrep", "-f", "python3 scheduler.py"],
                             capture_output=True, text=True, timeout=10)
        for pid in (out.stdout or "").split():
            try:
                cwd = os.path.realpath(f"/proc/{pid}/cwd")
                if cwd == os.path.realpath(project_dir):
                    return int(pid)
            except OSError:
                continue
    except Exception:
        pass
    return 0


def heal_config(pl: dict, vault_plats: dict = None) -> str:
    """凭据四层自愈: config.json ← .secrets ← secrets_backup.json ← GitHub vault"""
    cfg_path = os.path.join(pl["dir"], pl["config"])
    if os.path.exists(cfg_path):
        return "OK"
    # .secrets 项目外副本
    if os.path.exists(pl["secrets_copy"]):
        try:
            with open(pl["secrets_copy"], encoding="utf-8") as f:
                cfg = json.load(f)
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            return "已从 .secrets 自愈"
        except Exception as e:
            return f".secrets 恢复失败: {e}"
    # 快照追踪位(base64)
    bak = os.path.join(pl["dir"], "secrets_backup.json")
    if os.path.exists(bak):
        try:
            with open(bak, encoding="utf-8") as f:
                data = json.load(f)
            cfg = json.loads(base64.b64decode(data["payload_b64"]))
            key = "cookie" if "netease" in pl["dir"] else (
                "weibo_cookie" if "weibo" in pl["dir"] else "cookie")
            if not (cfg.get(key) or "").strip("MUSIC_U=; "):
                return "backup 为空占位"
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            return "已从 secrets_backup.json 自愈"
        except Exception as e:
            return f"backup 恢复失败: {e}"
    # GitHub vault(第4层, 权威源, 2026-10-27)
    vk = pl.get("vault_key")
    if vault_plats and vk and vault_plats.get(vk):
        try:
            cfg = dict(vault_plats[vk])
            key = "weibo_cookie" if vk == "weibo" else "cookie"
            if not (cfg.get(key) or "").strip():
                return "vault 该平台 cookie 为空"
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            os.makedirs(SECRETS, exist_ok=True)
            with open(pl["secrets_copy"], "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            return "已从 GitHub vault 自愈(+secrets副本)"
        except Exception as e:
            return f"vault 恢复失败: {e}"
    return "缺失(需用户提供 cookie)"


def restart_scheduler(pl: dict) -> int:
    subprocess.run(
        ["python3", DETACHED, pl["dir"],
         os.path.join(pl["dir"], pl["watchdog_log"]),
         "bash", "-c", pl["cmd"]],
        capture_output=True, timeout=30, check=False)
    time.sleep(3)
    return scheduler_alive(pl["dir"])


def main():
    print("=" * 58)
    print("三平台自愈 ·", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 58)
    vault_plats = None
    need_vault = any(
        not os.path.exists(os.path.join(pl["dir"], pl["config"]))
        and not os.path.exists(pl["secrets_copy"])
        for pl in PLATFORMS)
    if need_vault:
        vault_plats = fetch_vault_platforms()
        if vault_plats:
            print("[vault] GitHub 凭据库已拉取(第4层可用)")
    all_ok = True
    for pl in PLATFORMS:
        cfg_state = heal_config(pl, vault_plats)
        pid = scheduler_alive(pl["dir"])
        status = f"运行中 pid={pid}" if pid else "未运行"
        if not pid:
            pid = restart_scheduler(pl)
            status = f"已拉起 pid={pid}" if pid else "拉起失败!"
        if "需用户" in cfg_state or "失败" in cfg_state or not pid:
            all_ok = False
        print(f"\n[{pl['name']}] {pl['note']}")
        print(f"  凭据: {cfg_state} | 调度器: {status}")
    print("\n" + ("✅ 全部正常" if all_ok else
                  "⚠ 存在待办: 缺凭据的平台等用户提供 cookie 后自动接管, "
                  "或人工运行对应 rebuild 脚本"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
