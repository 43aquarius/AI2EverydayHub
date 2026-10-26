# -*- coding: utf-8 -*-
"""把改版后的代码同步到 GitHub 仓库(走 Git Data API:
blobs → tree → commit → update ref,兼容只开了 Contents 权限的 fine-grained PAT)
token 只出现在本脚本的请求头里,不会进入任何仓库文件。
"""
import base64
import json
import os
import subprocess
import sys
import urllib.request

REPO = "43aquarius/GitHub2XiaoHeiHeEveryday"
BRANCH = "main"
TOKEN = ("github_pat_11BKS2Y4Q0CQaV8ffFpwmd_aRFJfPWvfd6bQGYQX7ef3mel6O"
         "DbZFubzNJfU05ncA7MHFCDWV5ZNnSUxsd")
BASE = "/home/z/my-project/github-hot-heybox"

API = f"https://api.github.com/repos/{REPO}"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "github2xiaoheihe-sync",
    "X-GitHub-Api-Version": "2022-11-28",
}


def gh(method: str, url: str, body=None):
    """实测: 本环境访问 api.github.com 的 Git Data API 会阵发性 404
    (好一阵坏一阵,与传输方式无关),curl 单发 + Python层耐心重试跨过坏窗口"""
    import time
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
        raise RuntimeError(
            f"GitHub API 多次失败 {method} {url}: {last_err}")
    finally:
        if body_file:
            try:
                os.unlink(body_file)
            except OSError:
                pass


# 本次变更的文件(相对于仓库根)
FILES = [
    ("main.py", None),
    ("image_maker.py", None),
    ("summarizer.py", None),
    ("heybox_publisher.py", None),
    ("README.md", None),
    ("config.example.json", None),
    ("examples/示例-帖子文案.md", None),
    ("examples/示例-封面图.png", None),
    ("examples/示例-项目卡片.png", None),
]

# 1) 当前 main 的 commit/tree
ref = gh("GET", f"{API}/git/ref/heads/{BRANCH}")
parent_sha = ref["object"]["sha"]
parent = gh("GET", f"{API}/git/commits/{parent_sha}")
base_tree = parent["tree"]["sha"]
print(f"当前 {BRANCH}: {parent_sha[:10]} (tree {base_tree[:10]})")

# 2) 逐文件创建 blob(二进制走 base64)
tree_items = []
for rel, _ in FILES:
    p = os.path.join(BASE, rel)
    is_bin = rel.endswith((".png", ".jpg"))
    if is_bin:
        with open(p, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        blob = gh("POST", f"{API}/git/blobs",
                  {"content": content, "encoding": "base64"})
    else:
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()
        blob = gh("POST", f"{API}/git/blobs",
                  {"content": content, "encoding": "utf-8"})
    tree_items.append({
        "path": rel, "mode": "100644", "type": "blob",
        "sha": blob["sha"]})
    print(f"  blob: {rel} → {blob['sha'][:10]}")

# 3) 新 tree(基于现有 tree,只覆盖变更文件)
tree = gh("POST", f"{API}/git/trees",
          {"base_tree": base_tree, "tree": tree_items})
print(f"新 tree: {tree['sha'][:10]}")

# 4) commit
commit = gh("POST", f"{API}/git/commits", {
    "message": "帖子版式改版: 图文交错 + 空行分段 + 封面/项目卡片切片\n\n"
               "- 正文改为「封面图→导语→项目(编号头+数据行+分段正文+链接→卡片图)→结尾」节奏\n"
               "- text 块内 \\n\\n 空行分段(小黑盒正文容器 break-spaces,已实测)\n"
               "- image_maker: 一次渲染产出 banner+每项目卡片切片+长图备份,卡片改用 tagline 短标语\n"
               "- summarizer: 新增 tagline 字段(LLM生成+各stage保留+确定性兜底)\n"
               "- publisher: segments 图文交错模式,单图上传失败自动跳过\n"
               "- config: post.append_long_image 可选把完整长图附帖尾(默认关)",
    "tree": tree["sha"], "parents": [parent_sha]})
print(f"新 commit: {commit['sha'][:10]}")

# 5) 移动 main
gh("PATCH", f"{API}/git/refs/heads/{BRANCH}",
   {"sha": commit["sha"], "force": True})
print(f"✅ {BRANCH} 已更新 → {commit['sha'][:10]}")
print(f"https://github.com/{REPO}/commit/{commit['sha']}")
