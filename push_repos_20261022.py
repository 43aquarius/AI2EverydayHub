#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""推送三平台代码更新到 GitHub(2026-10-22)

- AI2NeteaseEveryday: config.py(三层持久化) + scheduler.py(优雅等待+对账)
  + rebuild_config.py(新) + README(持久化文档)
- AI2WeiboEveryday: 五栏目矩阵全量代码 + README(转型文档) + hitokoto 语料

token 取自 push_github_v2.py(两段字符串隐式拼接)。
显式文件清单 — config.json / secrets_backup.json 永不推送。
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

JOBS = [
    {
        "repo": "AI2NeteaseEveryday",
        "src": Path("/home/z/my-project/netease-music-poster"),
        "files": ["config.py", "scheduler.py", "rebuild_config.py", "README.md"],
        "msg": "凭据三层持久化 + 调度器优雅等待与发帖前对账防双发 + cookie一键重建",
    },
    {
        "repo": "AI2WeiboEveryday",
        "src": Path("/home/z/my-project/weibo-agi-poster"),
        "files": [
            "README.md", "main.py", "scheduler.py", "matrix_common.py",
            "card_renderer.py", "sources.py", "col_morning.py", "col_yiyan.py",
            "col_pet.py", "col_history.py", "col_hot.py", "config.example.json",
            "data/hitokoto.json",
        ],
        "msg": "转型五栏目内容矩阵: 早安AI壁纸/一言/萌宠/历史上的今天/热榜聚合 + 对账防双发修复",
    },
]


def push_file(repo: str, src: Path, rel: str, msg: str):
    local = src / rel
    content = base64.b64encode(local.read_bytes()).decode()
    url = f"{API}/repos/{OWNER}/{repo}/contents/{rel}"
    r = requests.get(url, headers=H, timeout=20)
    sha = r.json().get("sha") if r.status_code == 200 else None
    body = {"message": msg, "content": content, "branch": "main"}
    if sha:
        body["sha"] = sha
    for attempt in range(3):
        w = requests.put(url, headers=H, json=body, timeout=60)
        if w.status_code in (200, 201):
            print(f"  ✅ {repo}/{rel} ({'更新' if sha else '新建'})")
            return True
        if w.status_code == 403 and "rate limit" in w.text.lower():
            print("  ⏳ rate limit, 等 30s")
            time.sleep(30)
            continue
        print(f"  ❌ {repo}/{rel}: {w.status_code} {w.text[:150]}")
        return False
    return False


def main():
    ok = True
    for job in JOBS:
        print(f"[{job['repo']}] {len(job['files'])} 个文件 — {job['msg'][:40]}")
        for f in job["files"]:
            if not (job["src"] / f).exists():
                print(f"  ⚠ 缺文件跳过: {f}")
                continue
            ok = push_file(job["repo"], job["src"], f, job["msg"]) and ok
            time.sleep(1)
    print("\n" + ("全部推送完成 ✅" if ok else "存在失败 ⚠"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
