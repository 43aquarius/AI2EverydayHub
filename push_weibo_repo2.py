#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补充推送: run_daemon.py + test_scheduler.py + README 更新"""
import json
import os
import re as _re
import subprocess
import tempfile

REPO = "43aquarius/AI2WeiboEveryday"
BRANCH = "main"
BASE = "/home/z/my-project/weibo-agi-poster"

_v2_src = open("/home/z/my-project/scripts/push_github_v2.py",
               encoding="utf-8").read()
_m = _re.search(r'TOKEN = \(\s*"(.+?)"\s*\n\s*"(.+?)"\s*\)', _v2_src)
TOKEN = _m.group(1) + _m.group(2)

FILES = ["README.md", "run_daemon.py", "test_scheduler.py"]


def gh(method, url, body=None):
    cmd = ["curl", "-s", "-X", method, url,
           "-H", f"Authorization: Bearer {TOKEN}",
           "-H", "Accept: application/vnd.github+json",
           "-H", "User-Agent: weibo-sync",
           "-H", "X-GitHub-Api-Version: 2022-11-28",
           "-w", "\n%{http_code}"]
    if body is not None:
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as tf:
            tf.write(json.dumps(body))
            cmd += ["-H", "Content-Type: application/json",
                    "--data", "@" + tf.name]
    for attempt in range(6):
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        lines = out.stdout.rsplit("\n", 1)
        try:
            status = int(lines[1].strip())
        except (ValueError, IndexError):
            status = 0
        payload = {}
        if lines[0].strip():
            try:
                payload = json.loads(lines[0])
            except json.JSONDecodeError:
                payload = {}
        if 200 <= status < 300:
            return payload
        if status == 404 and attempt < 5:
            import time
            time.sleep(12)
            continue
        raise RuntimeError(f"GitHub API {method} {url}: HTTP {status}: "
                           f"{json.dumps(payload)[:200]}")
    raise RuntimeError(f"GitHub API 多次失败 {method} {url}")


head = gh("GET", f"https://api.github.com/repos/{REPO}/git/ref/heads/{BRANCH}")
parent_sha = head["object"]["sha"]
parent = gh("GET", f"https://api.github.com/repos/{REPO}/git/commits/{parent_sha}")
base_tree = parent["tree"]["sha"]
print(f"当前 main: {parent_sha[:10]}")

tree_items = []
for rel in FILES:
    content = open(os.path.join(BASE, rel), encoding="utf-8").read()
    blob = gh("POST", f"https://api.github.com/repos/{REPO}/git/blobs",
              {"content": content, "encoding": "utf-8"})
    print(f"  blob: {rel} → {blob['sha'][:10]}")
    tree_items.append({"path": rel, "mode": "100644", "type": "blob",
                       "sha": blob["sha"]})

tree = gh("POST", f"https://api.github.com/repos/{REPO}/git/trees",
          {"base_tree": base_tree, "tree": tree_items})
commit = gh("POST", f"https://api.github.com/repos/{REPO}/git/commits",
            {"message": "补: 双fork守护进程启动器(沙箱环境实测可常驻) + 调度逻辑单测10例",
             "tree": tree["sha"], "parents": [parent_sha]})
gh("PATCH", f"https://api.github.com/repos/{REPO}/git/refs/heads/{BRANCH}",
   {"sha": commit["sha"]})
print("✅ main →", commit["sha"][:10])
print(f"https://github.com/{REPO}/commit/{commit['sha']}")
