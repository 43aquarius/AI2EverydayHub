#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""restore_round4_20261027.py — 第11次沙箱回滚恢复(v2, 纯API文件叠加)

⚠ 教训(v1事故): 平台目录是 /home/z/my-project 单仓的子目录(非独立仓库),
  对其 git reset --hard 会把整个单仓工作树打回外部仓库的树!
  → 本版一律走 GitHub Contents API 逐文件叠加, 不碰本地 git。

灾情: 快照回滚至10-23基线: boot_heal旧版(无vault层)/网易云回周歌单19:30/
  微博config丢失/.secrets大部分被清/y2a-proxy全灭/worklog今日条目丢失
恢复源: AI2EverydayHub(boot_heal四层版) + AI2NeteaseEveryday(每日歌单版)
  + AI2WeiboEveryday(五栏目) + AI2OpsVault(凭据权威)
"""
import base64
import json
import os
import urllib.request

PAT = open("/home/z/.secrets/gh_pat.txt").read().strip()
H = {"Authorization": "Bearer " + PAT, "Accept": "application/vnd.github+json"}
SECRETS = "/home/z/.secrets"
MP = "/home/z/my-project"

# 不覆盖的本地文件(state/凭据/日志——沙箱回滚幸存者, 比 repo 里的新或同等)
SKIP = {"config.json", "state.json", "secrets_backup.json.keep_local",
        "config.example.json"}
SKIP_SUFFIX = (".log", ".log.pid", ".pid", ".pyc")
SKIP_DIR = ("__pycache__", ".git", "examples")


def gh_json(url):
    req = urllib.request.Request(url, headers=H)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def overlay_repo(repo, dest, note):
    """把 repo@main 的全部 blob 叠加到 dest(跳过 SKIP 名单)"""
    tree = gh_json(f"https://api.github.com/repos/43aquarius/{repo}/git/trees/main?recursive=1")
    n = 0
    for t in tree.get("tree", []):
        if t["type"] != "blob":
            continue
        p = t["path"]
        base = os.path.basename(p)
        parts = p.split("/")
        if base in SKIP or p.endswith(SKIP_SUFFIX) or \
                any(d in parts[:-1] for d in SKIP_DIR):
            continue
        try:
            d = gh_json(f"https://api.github.com/repos/43aquarius/{repo}/contents/{p}")
            content = base64.b64decode(d["content"])
        except Exception as e:
            print(f"      ! {p}: {e}")
            continue
        target = os.path.join(dest, p)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "wb") as f:
            f.write(content)
        n += 1
    print(f"      {note}: {n} 个文件 ← {repo}@main")


print("[1/6] vault 拉取(凭据权威源)")
_vraw = gh_json("https://api.github.com/repos/43aquarius/AI2OpsVault/contents/vault.json")
vault = json.loads(base64.b64decode(_vraw["content"]).decode())
plats = vault.get("platforms", {})
print("      platforms:", sorted(plats.keys()))

print("[2/6] scripts ← AI2EverydayHub(boot_heal四层版+detached_run)")
overlay_repo("AI2EverydayHub", f"{MP}/scripts", "scripts")

print("[3/6] netease ← AI2NeteaseEveryday(每日歌单版)")
overlay_repo("AI2NeteaseEveryday", f"{MP}/netease-music-poster", "netease")

print("[4/6] weibo ← AI2WeiboEveryday(五栏目)")
overlay_repo("AI2WeiboEveryday", f"{MP}/weibo-agi-poster", "weibo")

print("[5/6] 凭据落盘(平台config + .secrets镜像)")
wb = plats.get("weibo") or {}
if (wb.get("weibo_cookie") or "").strip():
    for p in (f"{MP}/weibo-agi-poster/config.json", f"{SECRETS}/weibo_config.json"):
        with open(p, "w", encoding="utf-8") as f:
            json.dump(wb, f, ensure_ascii=False, indent=2)
    print("      微博: cookie", len(wb["weibo_cookie"]), "字节 ✓")
else:
    print("      微博: ✗ vault 无 cookie(需用户)")
nt = plats.get("netease") or {}
if (nt.get("cookie") or "").strip():
    for p in (f"{MP}/netease-music-poster/config.json", f"{SECRETS}/netease_config.json"):
        with open(p, "w", encoding="utf-8") as f:
            json.dump(nt, f, ensure_ascii=False, indent=2)
    print("      网易云: cookie", len(nt["cookie"]), "字节 ✓")
hb = f"{MP}/github-hot-heybox/config.json"
if os.path.exists(hb):
    with open(f"{SECRETS}/heybox_config.json", "w", encoding="utf-8") as f:
        json.dump(json.load(open(hb, encoding="utf-8")), f, ensure_ascii=False, indent=2)
    print("      小黑盒: config在位, 补.secrets镜像 ✓")

print("[6/6] 版本终检")
sched = open(f"{MP}/netease-music-poster/scheduler.py", encoding="utf-8").read()
print("      网易云每日歌单档:", "✓" if ("20, 0" in sched or "20:00" in sched) else "✗ 仍旧版!")
print("      playlist_maker:", os.path.exists(f"{MP}/netease-music-poster/playlist_maker.py"))
bh = open(f"{MP}/scripts/boot_heal.py", encoding="utf-8").read()
print("      boot_heal vault四层:", "✓" if "vault" in bh else "✗")
print("      detached_run:", os.path.exists(f"{MP}/scripts/detached_run.py"))
wcfg = json.load(open(f"{MP}/weibo-agi-poster/config.json", encoding="utf-8"))
print("      微博config:", "✓" if wcfg.get("weibo_cookie") else "✗")
print("完成")
