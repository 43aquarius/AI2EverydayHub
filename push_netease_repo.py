#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""创建 AI2NeteaseEveryday 仓库并推送网易云项目(token 取自 push_github_v2.py)"""
import json
import re
import sys
import time
from pathlib import Path

import requests

# 从 push_github_v2.py 抠 token(两段字符串隐式拼接, 不执行其顶层代码)
_src = Path("/home/z/my-project/scripts/push_github_v2.py").read_text(encoding="utf-8")
_m = re.search(r"TOKEN\s*=\s*\(([^)]*)\)", _src, re.S)
TOKEN = "".join(re.findall(r'"([^"]*)"', _m.group(1)))

OWNER = "43aquarius"
REPO = "AI2NeteaseEveryday"
API = f"https://api.github.com"
H = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}

SRC = Path("/home/z/my-project/netease-music-poster")
FILES = [
    "README.md", "netease_client.py", "daily_post.py", "config.py",
    "main.py", "scheduler.py", "run_daemon.py", ".gitignore",
    "requirements.txt", "config.example.json",
    "image_maker.py", "comment_reply.py", "rebuild_config.py",
    "examples/示例-卡片配图.jpg",
]


def gh(method, url, **kw):
    r = requests.request(method, url, headers=H, timeout=30, **kw)
    if r.status_code == 403 and "rate limit" in r.text.lower():
        raise RuntimeError("rate limit")
    return r


def main():
    # 1. 建仓库
    r = gh("POST", f"{API}/user/repos", json={
        "name": REPO,
        "description": "网易云音乐「每日一歌」自动发布机器人: 每日推荐选歌 + LLM 走心文案 + 歌曲卡片动态 (纯 Python 复刻 weapi/eapi 协议)",
        "private": False,
        "has_issues": True,
    })
    if r.status_code == 201:
        print(f"[仓库] 创建成功: {OWNER}/{REPO}")
    elif r.status_code == 422:
        print(f"[仓库] 已存在, 跳过创建")
    else:
        print(f"[仓库] {r.status_code} {r.text[:200]}")
        if r.status_code not in (201, 422):
            sys.exit(1)

    # 2. 逐文件 Contents API 推送(不推 config.json/state.json 等敏感/本地文件)
    for i, name in enumerate(FILES):
        path = SRC / name
        content = path.read_bytes()
        import base64
        for attempt in range(3):
            # 查当前 sha(已存在文件需 sha 才能更新)
            r = gh("GET", f"{API}/repos/{OWNER}/{REPO}/contents/{name}")
            sha = r.json().get("sha") if r.status_code == 200 else None
            r = gh("PUT", f"{API}/repos/{OWNER}/{REPO}/contents/{name}", json={
                "message": f"add {name}",
                "content": base64.b64encode(content).decode(),
                "branch": "main",
                **({"sha": sha} if sha else {}),
            })
            if r.status_code in (200, 201):
                print(f"[{i+1}/{len(FILES)}] {name} ✓ ({r.status_code})")
                break
            print(f"[{i+1}/{len(FILES)}] {name} {r.status_code} {r.text[:120]} 重试{attempt+1}")
            time.sleep(3)
        else:
            sys.exit(f"推送 {name} 失败")

    print(f"\n完成 → https://github.com/{OWNER}/{REPO}")


if __name__ == "__main__":
    main()
