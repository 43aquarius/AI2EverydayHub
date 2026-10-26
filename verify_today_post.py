# -*- coding: utf-8 -*-
"""验证3: 确认今天的帖子已在创作者中心上线"""
import json
import sys
import datetime

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient

with open("/home/z/my-project/github-hot-heybox/config.json") as f:
    cfg = json.load(f)

BJT = datetime.timezone(datetime.timedelta(hours=8))
client = HeyboxClient(cfg["cookie"])
data = client.get("/bbs/app/author/concept/article/list", {
    "article_type": "all", "artilce_state": "all",
    "sort_filter": "create_at", "offset": "0", "limit": "3"})
arts = (data.get("result") or {}).get("articles") or []
print(f"最近 {len(arts)} 条:")
for a in arts:
    ts = a.get("create_at")
    when = datetime.datetime.fromtimestamp(ts, BJT).strftime(
        "%Y-%m-%d %H:%M:%S") if isinstance(ts, (int, float)) else "?"
    print(f"- [{when} 北京时间] link_id={a.get('link_id')} "
          f"图×{len(a.get('imgs') or [])} 《{a.get('title')}》")
    print(f"  分享链接: {a.get('share_url')}")
