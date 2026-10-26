#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""推送三项目今日改动到 GitHub(2026-10-23)

- AI2HeyboxEveryday: cover_gen.py + assets/ 背景图 + main.py/agi_news.py 接入
- AI2NeteaseEveryday: playlist_maker.py + netease_client.py(歌单API) +
  scheduler.py(周歌单档期) + main.py(playlist命令) + config.py(state镜像)
- AI2XhsDraft: 新仓库(xhs_client/content_maker/card_maker/main/README/gitignore)

token 取自 push_github_v2.py(两段字符串隐式拼接)。
显式文件清单 — config.json / secrets_backup.json / browser_profile / output 永不推送。
"""
import base64
import re
import sys
import time
from pathlib import Path

import requests

_src = Path("/home/z/my-project/scripts/push_github_v2.py").read_text(encoding="utf-8")
_m = re.search(r"TOKEN\s*=\s*\(([^)]*)\)", _src, re.S)
TOKEN = "".join(re.findall(r'"([^"]*)"', _m.group(1)))

OWNER = "43aquarius"
API = "https://api.github.com"
H = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}


def gh(method, path, **kw):
    r = requests.request(method, API + path, headers=H, timeout=30, **kw)
    return r


def ensure_repo(repo, desc):
    r = gh("POST", "/user/repos", json={
        "name": repo, "description": desc, "private": True,
        "auto_init": False})
    if r.status_code in (201,):
        print(f"  [建仓] {repo} ✓")
    elif r.status_code == 422:
        pass  # 已存在
    else:
        print(f"  [建仓] {repo} ? {r.status_code} {r.text[:80]}")


def push_file(repo, path_local: Path, path_remote: str, msg: str):
    try:
        data = path_local.read_bytes()
    except FileNotFoundError:
        print(f"  [skip] {path_remote} (本地不存在)")
        return
    b64 = base64.b64encode(data).decode()
    # 取 sha(如已存在)
    sha = None
    r = gh("GET", f"/repos/{OWNER}/{repo}/contents/{path_remote}")
    if r.status_code == 200:
        sha = r.json().get("sha")
    body = {"message": f"{msg}: {path_remote}", "content": b64,
            "branch": "main"}
    if sha:
        body["sha"] = sha
    r = gh("PUT", f"/repos/{OWNER}/{repo}/contents/{path_remote}", json=body)
    ok = r.status_code in (200, 201)
    print(f"  {'✓' if ok else '✗'} {path_remote} ({len(data)}B)"
          + ("" if ok else f" {r.text[:100]}"))
    time.sleep(0.8)


MSG = "2026-10-23: heybox cover restyle / netease weekly playlist / xhs semi-auto draft"

JOBS = [
    {
        "repo": "AI2HeyboxEveryday",
        "desc": "GitHub热榜+AGI日报 → 小黑盒自动发帖(参考图风格首图封面)",
        "src": Path("/home/z/my-project/github-hot-heybox"),
        "files": ["cover_gen.py", "main.py", "agi_news.py",
                  "assets/desk_bg_github.png", "assets/desk_bg_agi.png"],
    },
    {
        "repo": "AI2NeteaseEveryday",
        "desc": "网易云音乐每日一歌+周歌单自动化(eapi/xsapi逆向)",
        "src": Path("/home/z/my-project/netease-music-poster"),
        "files": ["playlist_maker.py", "netease_client.py", "scheduler.py",
                  "main.py", "config.py"],
    },
    {
        "repo": "AI2XhsDraft",
        "desc": "小红书半自动发布工具(Playwright存草稿+发布包, 绝不自动发布)",
        "src": Path("/home/z/my-project/xhs-draft-poster"),
        "files": ["README.md", ".gitignore", "main.py", "xhs_client.py",
                  "content_maker.py", "card_maker.py",
                  "assets/desk_bg_xhs.png"],
    },
]

for job in JOBS:
    print(f"\n=== {job['repo']} ===")
    ensure_repo(job["repo"], job["desc"])
    for f in job["files"]:
        push_file(job["repo"], job["src"] / f, f, MSG)
print("\n完成")
