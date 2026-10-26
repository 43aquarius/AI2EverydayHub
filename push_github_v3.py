# -*- coding: utf-8 -*-
"""推送本轮改动到 GitHub(Git Data API 模式, 复用 v2 的 curl 重试)
变更: 调度改每周一档 / 单项目安利帖管线 / README 同步"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request

REPO = "43aquarius/GitHub2XiaoHeiHeEveryday"  # 注意用户名是 43aquarius(带u)
BRANCH = "main"
BASE = "/home/z/my-project/github-hot-heybox"

# 从 v2 推送脚本提取真实 TOKEN(两段拼接),避免在本文件再次明文复制
import re as _re
_v2_src = open("/home/z/my-project/scripts/push_github_v2.py",
               encoding="utf-8").read()
_m = _re.search(r'TOKEN = \(\s*"(.+?)"\s*\n\s*"(.+?)"\s*\)', _v2_src)
assert _m, "无法从 push_github_v2.py 提取 TOKEN"
TOKEN = _m.group(1) + _m.group(2)

API = f"https://api.github.com/repos/{REPO}"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "github2xiaoheihe-sync",
    "X-GitHub-Api-Version": "2022-11-28",
}


def gh(method, url, body=None):
    """curl 单发 + 耐心重试(本环境 api.github.com Git Data API 阵发性 404)"""
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
                raise RuntimeError(
                    f"GitHub API 拒绝 {method} {url}: {last_err}")
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
    "scheduler.py",
    "image_maker.py",
    "project_post.py",
    "README.md",
]

# 1) 当前 main 的 commit/tree
ref = gh("GET", f"{API}/git/ref/heads/{BRANCH}")
parent_sha = ref["object"]["sha"]
parent = gh("GET", f"{API}/git/commits/{parent_sha}")
base_tree = parent["tree"]["sha"]
print(f"当前 {BRANCH}: {parent_sha[:10]} (tree {base_tree[:10]})")

# 2) 逐文件 blob
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

# 3) 新 tree
tree = gh("POST", f"{API}/git/trees",
          {"base_tree": base_tree, "tree": tree_items})
print(f"新 tree: {tree['sha'][:10]}")

# 4) commit
commit = gh("POST", f"{API}/git/commits", {
    "message": "改每周一档 + 新增单项目安利帖管线 project_post.py\n\n"
               "- scheduler v3: 档期由 config post.daily_enabled/weekly_enabled 控制,\n"
               "  当前 daily 关闭只发周一 10:00 周榜(GitHub 日榜内容重复度高)\n"
               "- project_post.py: 单项目深挖帖——meta 双路(core API→search 兜底,\n"
               "  core 配额与共享 IP 常瞬时耗尽) + README 三路抓取\n"
               "  (core→jsdelivr CDN 免配额→raw) + LLM 生成/终审(复用榜单红线)\n"
               "  + 单项目海报图(亮点列表版式) + 批量连发防重发(state.project_posts)\n"
               "- image_maker: render_project_poster 单项目海报\n"
               "- README: 双帖子形态说明 + 每周档期 + project_post 用法",
    "tree": tree["sha"], "parents": [parent_sha]})
print(f"新 commit: {commit['sha'][:10]}")

# 5) 移动 main
gh("PATCH", f"{API}/git/refs/heads/{BRANCH}",
   {"sha": commit["sha"], "force": True})
print(f"✅ {BRANCH} 已更新 → {commit['sha'][:10]}")
print(f"https://github.com/{REPO}/commit/{commit['sha']}")
