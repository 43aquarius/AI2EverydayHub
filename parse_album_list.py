# -*- coding: utf-8 -*-
"""解析合集页 cgiData.articleList → 全部期数列表"""
import re
import sys
import datetime
sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from agi_news import _http_get, _html_unescape

ALBUM_URL = ("https://mp.weixin.qq.com/mp/appmsgalbum"
             "?__biz=MjM5OTE0ODA2MQ==&action=getalbum"
             "&album_id=3349853949226418182")

html = _http_get(ALBUM_URL, timeout=40)

# articleList 条目: title/create_time/url (JS 对象字面量, 单引号字符串)
pat = re.compile(
    r"title:\s*'([^']*)',\s*"
    r"create_time:\s*'(\d+)',\s*"
    r"cover_img_1_1:\s*'([^']*)',\s*"
    r"url:\s*'([^']*)'", re.S)
items = pat.findall(html)
print(f"解析出 {len(items)} 期:")
for title, ts, cover, url in items[:15]:
    t = datetime.datetime.fromtimestamp(int(ts))
    url_clean = _html_unescape(url).replace("\\x26", "&")
    print(f"  {t:%Y-%m-%d %H:%M} | {title} | {url_clean[:80]}")

# 检查日期连续性(最近10期)
dates = []
for title, ts, cover, url in items:
    m = re.search(r"(\d{8})", title)
    if m:
        dates.append(m.group(1))
print("最近10期期号:", dates[:10])
