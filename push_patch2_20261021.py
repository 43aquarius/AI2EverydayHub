#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-21 补丁2推送: project_post 加长硬校验+数字铁律,
publisher 修 articles 键名(小黑盒)"""
import json
import os
import re as _re
import subprocess
import tempfile

_v2_src = open("/home/z/my-project/scripts/push_github_v2.py",
               encoding="utf-8").read()
_m = _re.search(r'TOKEN = \(\s*"(.+?)"\s*\n\s*"(.+?)"\s*\)', _v2_src)
TOKEN = _m.group(1) + _m.group(2)

MSG = ("fix: 单帖文案加长硬校验(body<320带反馈重试)+数字铁律"
       "(第N章是章号不是数量); get_latest_post_id 修 articles 键名")


def gh(method, url, body=None):
    cmd = ["curl", "-s", "-X", method, url,
           "-H", f"Authorization: Bearer {TOKEN}",
           "-H", "Accept: application/vnd.github+json",
           "-H", "User-Agent: sync",
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


def push(repo, base, files):
    head = gh("GET", f"https://api.github.com/repos/{repo}/git/ref/heads/main")
    parent_sha = head["object"]["sha"]
    parent = gh("GET",
                f"https://api.github.com/repos/{repo}/git/commits/{parent_sha}")
    base_tree = parent["tree"]["sha"]
    print(f"[{repo}] main: {parent_sha[:10]}")
    tree_items = []
    for rel in files:
        content = open(os.path.join(base, rel), encoding="utf-8").read()
        blob = gh("POST", f"https://api.github.com/repos/{repo}/git/blobs",
                  {"content": content, "encoding": "utf-8"})
        tree_items.append({"path": rel, "mode": "100644", "type": "blob",
                           "sha": blob["sha"]})
    tree = gh("POST", f"https://api.github.com/repos/{repo}/git/trees",
              {"base_tree": base_tree, "tree": tree_items})
    commit = gh("POST", f"https://api.github.com/repos/{repo}/git/commits",
                {"message": MSG, "tree": tree["sha"], "parents": [parent_sha]})
    gh("PATCH", f"https://api.github.com/repos/{repo}/git/refs/heads/main",
       {"sha": commit["sha"]})
    print(f"  ✅ {commit['sha'][:10]} → {len(files)} 文件")


push("43aquarius/AGI2iaoHeiHeiEveryday",
     "/home/z/my-project/github-hot-heybox", ["project_post.py", "heybox_publisher.py"])
