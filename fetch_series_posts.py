#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拉取 skills/prompts 第1期帖子内容, 提取选题 key 用于重建 series state"""
import json
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient

cfg = json.load(open("/home/z/my-project/github-hot-heybox/config.json"))
client = HeyboxClient(cfg["cookie"])

for link, name in [("194810909", "skills第1期"), ("194852761", "prompts第1期")]:
    data = client.get("/bbs/app/link/tree", {"link_id": link})
    text = (((data.get("result") or {}).get("link") or {}).get("text") or "[]")
    blocks = json.loads(text)
    print(f"===== {name} (link={link}) =====")
    for b in blocks:
        if b.get("type") == "text" and b.get("text"):
            t = b["text"]
            if len(t) > 3:
                print(t[:600])
                print("---")
