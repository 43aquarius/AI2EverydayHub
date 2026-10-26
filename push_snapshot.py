#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GitHub 仓库全量快照推送 (Git Data API, 不依赖本地 git)

用法: python3 push_snapshot.py <本地目录> <owner/repo> [commit_message]
流程: .gitignore 过滤 → blobs → tree → commit → 移动 main 指针
空仓库(无任何提交): 先 Contents API 造根提交再走 Git Data API
注意: PAT = token() 是函数调用 (2026-10-24 踩坑: import token as PAT
      直接当字符串用导致 401)
"""
import base64
import fnmatch
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, "/home/z/my-project/scripts")
from gh_token import token as PAT

API = "https://api.github.com"
IGNORED = [".git", "__pycache__", "*.pyc", "node_modules", ".venv",
           "browser_profile", "output", "logs", "*.log", "*.pid",
           "state.json", "config.json", "secrets_backup.json", "cookies"]


def gh(method, path, body=None, retries=4):
    data = json.dumps(body).encode() if body is not None else None
    for i in range(retries):
        req = urllib.request.Request(
            API + path, data=data, method=method,
            headers={"Authorization": f"Bearer {PAT()}",
                     "Accept": "application/vnd.github+json",
                     "Content-Type": "application/json",
                     "User-Agent": "push-snapshot"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            if e.code in (409, 404, 405) and i < retries - 1:
                time.sleep(3 * (i + 1))
                continue
            body_txt = e.read().decode()[:200]
            raise RuntimeError(f"{method} {path} -> {e.code}: {body_txt}")
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(3 * (i + 1))


def should_ignore(name, rel):
    for pat in IGNORED:
        if fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel, pat):
            return True
    return False


def collect_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if not should_ignore(d, os.path.relpath(
                           os.path.join(dirpath, d), root))]
        for fn in filenames:
            rel = os.path.relpath(os.path.join(dirpath, fn), root)
            if should_ignore(fn, rel):
                continue
            out.append(rel)
    return sorted(out)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    root, repo = sys.argv[1], sys.argv[2]
    msg = sys.argv[3] if len(sys.argv) > 3 else f"snapshot {time.strftime('%F %T')}"
    files = collect_files(root)
    print(f"[推送] {repo} <- {root} ({len(files)} 文件)")

    # 空仓库检查
    try:
        ref = gh("GET", f"/repos/{repo}/git/ref/heads/main")
        base_sha = ref["object"]["sha"]
    except Exception:
        # 空仓库: Contents API 根提交
        readme = os.path.join(root, "README.md")
        content = ""
        if os.path.exists(readme):
            with open(readme, encoding="utf-8") as f:
                content = f.read()
        gh("PUT", f"/repos/{repo}/contents/README.md",
           {"message": "init root", "content":
            base64.b64encode(content.encode()).decode()})
        ref = gh("GET", f"/repos/{repo}/git/ref/heads/main")
        base_sha = ref["object"]["sha"]

    # blobs + tree
    tree_items = []
    for rel in files:
        with open(os.path.join(root, rel), "rb") as f:
            content = f.read()
        # >1MB 文件跳过(API限制)
        if len(content) > 1_000_000:
            print(f"  跳过大文件 {rel} ({len(content)}B)")
            continue
        blob = gh("POST", f"/repos/{repo}/git/blobs",
                  {"content": base64.b64encode(content).decode(),
                   "encoding": "base64"})
        tree_items.append({"path": rel.replace(os.sep, "/"),
                           "mode": "100644", "type": "blob",
                           "sha": blob["sha"]})
        print(f"  blob {rel}")
    tree = gh("POST", f"/repos/{repo}/git/trees",
              {"base_tree": base_sha, "tree": tree_items})
    commit = gh("POST", f"/repos/{repo}/git/commits",
                {"message": msg, "tree": tree["sha"],
                 "parents": [base_sha]})
    gh("PATCH", f"/repos/{repo}/git/refs/heads/main",
       {"sha": commit["sha"], "force": True})
    print(f"✅ 推送完成: {repo}@{commit['sha'][:8]} ({len(tree_items)} 文件)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
