# -*- coding: utf-8 -*-
"""调查2: 盒友杂谈 feed 帖子的字段结构 + 文字帖的块格式"""
import json
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient

with open("/home/z/my-project/github-hot-heybox/config.json") as f:
    cfg = json.load(f)
client = HeyboxClient(cfg["cookie"])

feeds = client.get_topic_feeds(7214, offset=0, limit=30)
result = feeds.get("result") or {}
print("result keys:", list(result.keys()))
items = result.get("links") or result.get("feeds") or []
print(f"items={len(items)}")
if items:
    print("第一条 keys:", list(items[0].keys()))
    print(json.dumps(items[0], ensure_ascii=False)[:800])

# 找出所有 linkid + word_num
cands = []
for it in items:
    link = it.get("link") if isinstance(it.get("link"), dict) else it
    lid = str(link.get("linkid") or link.get("link_id") or "")
    wn = link.get("word_num") or 0
    if lid:
        cands.append((lid, wn, link.get("title") or ""))
print("\n候选帖子:")
for lid, wn, title in cands:
    print(f"  {lid}  words={wn}  {title[:30]}")
