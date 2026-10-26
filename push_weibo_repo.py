#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""推送微博项目到 GitHub (Git Data API, 同小黑盒项目方式)"""
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

FILES = [
    "README.md", "weibo_client.py", "agi_daily.py", "ai_news.py",
    "copywriter.py", "image_maker.py", "scheduler.py", "main.py",
    "config.example.json", "requirements.txt", ".gitignore",
]


def gh(method, url, body=None):
    cmd = ["curl", "-s", "-X", method, url,
           "-H", f"Authorization: Bearer {TOKEN}",
           "-H", "Accept: application/vnd.github+json",
           "-H", "User-Agent: weibo-sync",
           "-H", "X-GitHub-Api-Version: 2022-11-28",
           "-w", "\n%{http_code}"]
    body_file = None
    if body is not None:
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as tf:
            tf.write(json.dumps(body))
            body_file = tf.name
        cmd += ["-H", "Content-Type: application/json",
                "--data", "@" + body_file]
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
        if status == 404 and attempt < 5:      # 间歇性404重试
            import time
            time.sleep(12)
            continue
        raise RuntimeError(f"GitHub API {method} {url}: HTTP {status}: "
                           f"{json.dumps(payload)[:200]}")
    raise RuntimeError(f"GitHub API 多次失败 {method} {url}")


# ① Contents API 放首个文件 → 初始化 main 分支(空仓库的 Git Data API 会 409)
import base64
readme = open(os.path.join(BASE, "README.md"), encoding="utf-8").read()
gh("PUT", f"https://api.github.com/repos/{REPO}/contents/README.md", {
    "message": "init", "branch": BRANCH,
    "content": base64.b64encode(readme.encode()).decode()})
print("  初始化 main: README.md")

# ② 拿当前 commit/tree
head = gh("GET", f"https://api.github.com/repos/{REPO}/git/ref/heads/{BRANCH}")
parent_sha = head["object"]["sha"]
parent = gh("GET", f"https://api.github.com/repos/{REPO}/git/commits/{parent_sha}")
base_tree = parent["tree"]["sha"]
print(f"当前 main: {parent_sha[:10]} (tree {base_tree[:10]})")

# ③ 其余文件 → blobs → 树 → commit
tree_items = []
for rel in FILES:
    if rel == "README.md":
        continue
    path = os.path.join(BASE, rel)
    content = open(path, encoding="utf-8").read()
    blob = gh("POST", "https://api.github.com/repos/{}/git/blobs".format(REPO),
              {"content": content, "encoding": "utf-8"})
    print(f"  blob: {rel} → {blob['sha'][:10]}")
    tree_items.append({"path": rel, "mode": "100644", "type": "blob",
                       "sha": blob["sha"]})

tree = gh("POST", "https://api.github.com/repos/{}/git/trees".format(REPO),
          {"base_tree": base_tree, "tree": tree_items})
print("新 tree:", tree["sha"][:10])
commit = gh("POST", "https://api.github.com/repos/{}/git/commits".format(REPO),
            {"message": "微博 AI 资讯自动运营机器人 v1: 双栏目(AGI日报+AI情报站) "
                        "全链路上线\n\n- 微博 Web API 客户端(CRC32 上传签名逆向/长文发帖)\n"
                        "- AGI 日报: 微信合集页实时源 + LLM 微博化文案 + 4主题长图\n"
                        "- AI 情报站: aihot.news /api/v1 24h精选\n"
                        "- 调度器: 08:30/12:00 双档期 + 失败重试 + 防重",
             "tree": tree["sha"], "parents": [parent_sha]})
print("新 commit:", commit["sha"][:10])

# ④ 快进 main
ref = gh("PATCH",
         f"https://api.github.com/repos/{REPO}/git/refs/heads/{BRANCH}",
         {"sha": commit["sha"], "force": True})
print("✅ main →", ref["object"]["sha"][:10])
print(f"https://github.com/{REPO}/commit/{commit['sha']}")
