#!/usr/bin/env python3
"""通用 Contents API PUT 推送(带 sha 更新)
用法: python3 push_files.py <owner/repo> <本地路径:仓库路径>...
"""
import base64
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gh_token import get_token


def push(owner_repo, local, repo_path, branch="main"):
    url = f"https://api.github.com/repos/{owner_repo}/contents/{repo_path}"
    headers = {
        "Authorization": f"token {get_token()}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "heal-bot",
    }
    sha = None
    req = urllib.request.Request(f"{url}?ref={branch}", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            sha = json.load(r)["sha"]
    except Exception:
        pass
    with open(local, "rb") as f:
        content = f.read()
    body = {
        "message": f"heal-push: {os.path.basename(repo_path)}",
        "content": base64.b64encode(content).decode(),
        "branch": branch,
    }
    if sha:
        body["sha"] = sha
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers=headers, method="PUT")
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)
    print(f"PUSHED {local} -> {owner_repo}/{repo_path} ({res['commit']['sha'][:7]})")


if __name__ == "__main__":
    owner_repo = sys.argv[1]
    for spec in sys.argv[2:]:
        local, _, repo_path = spec.partition(":")
        push(owner_repo, local, repo_path)
