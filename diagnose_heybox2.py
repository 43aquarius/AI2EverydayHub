# -*- coding: utf-8 -*-
"""诊断2: dump 文章列表原始响应"""
import json
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient

with open("/home/z/my-project/github-hot-heybox/config.json") as f:
    cfg = json.load(f)

client = HeyboxClient(cfg["cookie"])
data = client.get("/bbs/app/author/concept/article/list", {
    "article_type": "all", "artilce_state": "all",
    "sort_filter": "create_at", "offset": "0", "limit": "5"})
print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])
