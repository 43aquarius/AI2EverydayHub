# -*- coding: utf-8 -*-
"""检查微信合集页今天最新一期(发帖前防重确认)"""
import sys, json, re

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
import agi_news

meta = agi_news.latest_issue_meta()
print("latest_issue_meta →")
print(json.dumps({k: (str(v)[:80]) for k, v in meta.items()}, ensure_ascii=False, indent=2))

# 再看合集页最近几期列表
import urllib.request
html = agi_news._http_get(agi_news.WX_ALBUM_URL, timeout=30) if hasattr(agi_news, "_http_get") else None
if html:
    m = re.search(r'cgiData\s*=\s*\{.*?"articleList"\s*:\s*(\[.*?\])', html, re.S)
    if m:
        raw = m.group(1)
        items = re.findall(r'\{"title":"([^"]+)".*?"createTime":(\d+)', raw)
        import datetime
        for t, ts in items[:6]:
            dt = datetime.datetime.fromtimestamp(int(ts), datetime.timezone(datetime.timedelta(hours=8)))
            print(f"  {dt:%m-%d %H:%M} | {t[:52]}")
