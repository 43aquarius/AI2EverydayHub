#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""推送本轮改动到 GitHub(Git Data API, 复用 v2 的 TOKEN 提取与 curl 重试)
变更: 新增 AGI 日报栏目 agi_news.py + scheduler 集成 agi 档期"""
import base64
import json
import os
import subprocess
import sys
import time

REPO = "43aquarius/GitHub2XiaoHeiHeEveryday"
BRANCH = "main"
BASE = "/home/z/my-project/github-hot-heybox"

import re as _re
_v2_src = open("/home/z/my-project/scripts/push_github_v2.py",
               encoding="utf-8").read()
_m = _re.search(r'TOKEN = \(\s*"(.+?)"\s*\n\s*"(.+?)"\s*\)', _v2_src)
assert _m, "无法从 push_github_v2.py 提取 TOKEN"
TOKEN = _m.group(1) + _m.group(2)

API = f"https://api.github.com/repos/{REPO}"


def gh(method, url, body=None):
    cmd = ["curl", "-s", "-X", method, url,
           "-H", f"Authorization: Bearer {TOKEN}",
           "-H", "Accept: application/vnd.github+json",
           "-H", "User-Agent: github2xiaoheihe-sync",
           "-H", "X-GitHub-Api-Version: 2022-11-28",
           "-w", "\n%{http_code}"]
    body_file = None
    if body is not None:
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as tf:
            tf.write(json.dumps(body))
            body_file = tf.name
        cmd += ["-H", "Content-Type: application/json",
                "--data", "@" + body_file]
    last_err = ""
    try:
        for attempt in range(8):
            out = subprocess.run(cmd, capture_output=True, text=True,
                                 timeout=120)
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
            last_err = (f"HTTP {status}: "
                        f"{json.dumps(payload, ensure_ascii=False)[:200]}")
            if status in (400, 401, 403, 422) and "rate limit" not in last_err:
                raise RuntimeError(f"GitHub API 拒绝 {method} {url}: {last_err}")
            print(f"  [retry] 第{attempt+1}次 {status}, 12秒后重试...")
            time.sleep(12)
        raise RuntimeError(f"GitHub API 多次失败 {method} {url}: {last_err}")
    finally:
        if body_file:
            try:
                os.unlink(body_file)
            except OSError:
                pass


FILES = [
    "agi_news.py",
    "scheduler.py",
    "image_maker.py",
    "README.md",
    "config.example.json",
]

ref = gh("GET", f"{API}/git/ref/heads/{BRANCH}")
parent_sha = ref["object"]["sha"]
parent = gh("GET", f"{API}/git/commits/{parent_sha}")
base_tree = parent["tree"]["sha"]
print(f"当前 {BRANCH}: {parent_sha[:10]} (tree {base_tree[:10]})")

tree_items = []
for rel in FILES:
    p = os.path.join(BASE, rel)
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    blob = gh("POST", f"{API}/git/blobs",
              {"content": content, "encoding": "utf-8"})
    tree_items.append({"path": rel, "mode": "100644", "type": "blob",
                       "sha": blob["sha"]})
    print(f"  blob: {rel} → {blob['sha'][:10]}")

tree = gh("POST", f"{API}/git/trees",
          {"base_tree": base_tree, "tree": tree_items})
print(f"新 tree: {tree['sha'][:10]}")

commit = gh("POST", f"{API}/git/commits", {
    "message": "新增 AGI 日报栏目 agi_news.py(每日 09:30)\n\n"
               "- 数据链路: ima 分享页 SSR(Remix turbo-stream 解码,\n"
               "  免登录)→ 微信公众号原文(块级标签→换行, 中文序号切章节,\n"
               "  UI 噪音过滤, gzip+重试防断流)→ LLM 文案(复用榜单写作红线,\n"
               "  每条 110~170字, 截断自动修复 + 退避重试)→ AGI 日报长图\n"
               "  (与榜单同一套 GitHub Dark+小黑盒橙视觉)→ 发布\n"
               "- 防重: state.agi_last_issue 期号防重(知识库同步延迟时\n"
               "  同一期绝不重发), 无新期跳过也写 last_agi 当日标记\n"
               "- scheduler v3: agi 档期(每日 09:30, config agi_enabled),\n"
               "  catch_up 对 AGI 不做创作者中心对账(无新期属正常)\n"
               "- image_maker: render_agi_image 总览长图\n"
               "- 内容红线: 帖子不标明数据来自 ima, 只说数据来源于网络整理",
    "tree": tree["sha"], "parents": [parent_sha]})
print(f"新 commit: {commit['sha'][:10]}")

gh("PATCH", f"{API}/git/refs/heads/{BRANCH}",
   {"sha": commit["sha"], "force": True})
print(f"✅ {BRANCH} 已更新 → {commit['sha'][:10]}")
print(f"https://github.com/{REPO}/commit/{commit['sha']}")
