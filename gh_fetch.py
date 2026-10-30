#!/usr/bin/env python3
"""Contents API 拉取: python3 gh_fetch.py <owner/repo> <path[:dst]>..."""
import base64
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gh_token import get_token


def fetch(owner_repo, path, dst=None):
    url = f"https://api.github.com/repos/{owner_repo}/contents/{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {get_token()}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "heal-bot",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    content = base64.b64decode(data["content"])
    if dst is None:
        dst = "/tmp/" + os.path.basename(path)
    d = os.path.dirname(dst)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(dst, "wb") as f:
        f.write(content)
    print(f"OK {owner_repo}/{path} -> {dst} ({len(content)} bytes)")
    return dst


if __name__ == "__main__":
    import urllib.request
    owner_repo = sys.argv[1]
    for spec in sys.argv[2:]:
        path, _, dst = spec.partition(":")
        fetch(owner_repo, path, dst or None)
