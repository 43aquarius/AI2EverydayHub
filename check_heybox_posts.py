#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看小黑盒最近帖子(标题+时间+话题), 用于重建 series 状态"""
import datetime
import json
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient

BJT = datetime.timezone(datetime.timedelta(hours=8))
cfg = json.load(open("/home/z/my-project/github-hot-heybox/config.json"))
client = HeyboxClient(cfg["cookie"])

data = client.get("/bbs/app/author/concept/article/list", {
    "article_type": "all", "artilce_state": "all",
    "sort_filter": "create_at", "offset": "0", "limit": "25"})
arts = (data.get("result") or {}).get("articles") or []
print(f"获取到 {len(arts)} 帖:")
for a in arts:
    ts = a.get("create_at")
    when = datetime.datetime.fromtimestamp(int(ts), BJT)
    title = (a.get("title") or "(无标题)")[:50]
    link = a.get("link_id")
    print(f"  [{when:%m-%d %H:%M}] link={link} {title}")
