#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""推送本轮改动到 GitHub(Git Data API, 复用 v2 的 TOKEN 提取与 curl 重试)
本轮: AGI 日报实时化(微信合集页) + 图片升级(4主题/富信息/footer修正)
     + LLM截断修复器 + 调度器标签对账 + 编辑API文档"""
import json
import os
import subprocess
import sys
import time
import tempfile

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
    "summarizer.py",
    "README.md",
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
    "message": "AGI 日报实时化 + 图片系统升级 + 稳定性加固\n\n"
               "- agi_news: 数据源主路改为微信公众号合集页(免登录 SSR,\n"
               "  每工作日16:01发布次日刊, 比知识库快10+天), ima 分享页\n"
               "  降级保留; LLM 输出新增 category/img_points/keywords\n"
               "  字段供长图使用; intro 条数声明与实际条目自动对齐\n"
               "- image_maker: AGI 长图重写为富信息版 — 四套主题按期号\n"
               "  轮换(ember/ocean/violet/matrix), TOP1-3 焦点卡渐变\n"
               "  描边, 分类chip+要点列表+本期看点统计条; 榜单卡片\n"
               "  增加项目描述与 Fork 数; footer 按栏目区分(只有\n"
               "  GitHub 榜单帖的图写'每周一 GitHub 周榜')\n"
               "- summarizer: _repair_truncated_json 截断修复器(逐字符\n"
               "  回退到语法边界+字符串感知补括号), summarize_repos\n"
               "  重试 2→3 次+退避, 修复条目过滤残壳\n"
               "- scheduler: 启动对账用话题标签区分帖子归属(榜单帖\n"
               "  #GitHub# vs AGI 帖 #AGI#), 修复 AGI 帖被误判为\n"
               "  周榜已发导致漏发的问题; fetch_recent_posts 带\n"
               "  link_id/title\n"
               "- README: 实时数据链路/编辑API/标签对账/时区说明",
    "tree": tree["sha"], "parents": [parent_sha]})
print(f"新 commit: {commit['sha'][:10]}")

gh("PATCH", f"{API}/git/refs/heads/{BRANCH}",
   {"sha": commit["sha"], "force": True})
print(f"✅ {BRANCH} 已更新 → {commit['sha'][:10]}")
print(f"https://github.com/{REPO}/commit/{commit['sha']}")
