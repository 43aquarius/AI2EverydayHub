#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-21 补丁推送: 未转义引号修复器(两仓库)

根因: LLM 写中文引语输出 "..."(U+0022) 不转义, json.loads 报
"Expecting ',' delimiter"; 此前误诊为截断问题。
修复: _fix_unescaped_quotes 状态机 — 字符串内 " 后跟(跳空白)
: } ] 或 ,+"{[ 判为收尾, 其余转义; 回退闭合也基于修复文本。
"""
import json
import os
import re as _re
import subprocess
import tempfile

_v2_src = open("/home/z/my-project/scripts/push_github_v2.py",
               encoding="utf-8").read()
_m = _re.search(r'TOKEN = \(\s*"(.+?)"\s*\n\s*"(.+?)"\s*\)', _v2_src)
TOKEN = _m.group(1) + _m.group(2)

MSG = ("fix: 未转义ASCII引号修复器(中文引语导致JSON解析失败的真根因), "
       "回退闭合也基于修复文本")


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
     "/home/z/my-project/github-hot-heybox", ["summarizer.py"])
push("43aquarius/AI2WeiboEveryday",
     "/home/z/my-project/weibo-agi-poster", ["copywriter.py"])
