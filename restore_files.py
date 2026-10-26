#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 GitHub 仓库恢复被沙箱重启清除的项目文件 (Contents API)

用法: python3 restore_files.py <repo> <远程路径> <本地路径> [更多远程:本地对...]
"""
import base64
import os
import sys
import time
import urllib.request

sys.path.insert(0, "/home/z/my-project/scripts")
from gh_token import token as PAT


def gh_get(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(
                url, headers={"Authorization": f"Bearer {PAT()}",
                              "Accept": "application/vnd.github+json",
                              "User-Agent": "file-restore"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if i == retries - 1:
                raise
            time.sleep(2 * (i + 1))


import json


def restore_file(repo, remote_path, local_path):
    try:
        data = gh_get(
            f"https://api.github.com/repos/{repo}/contents/{remote_path}")
    except Exception as e:
        print(f"  ❌ {remote_path}: {e}")
        return False
    if isinstance(data, list):  # 目录
        os.makedirs(local_path, exist_ok=True)
        print(f"  📁 {remote_path}/ -> {local_path}/ ({len(data)} 项)")
        return True
    content = base64.b64decode(data["content"])
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "wb") as f:
        f.write(content)
    print(f"  ✅ {remote_path} -> {local_path} ({len(content)}B)")
    return True


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 1
    repo = sys.argv[1]
    pairs = sys.argv[2:]
    print(f"仓库: {repo}")
    ok = sum(restore_file(repo, pairs[i], pairs[i + 1])
             for i in range(0, len(pairs), 2))
    print(f"完成 {ok}/{len(pairs) // 2}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
