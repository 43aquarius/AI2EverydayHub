# -*- coding: utf-8 -*-
"""探测微信合集页: 从 ima 分享页拿最新一期微信原文 → 提取 __biz / 合集链接"""
import re
import sys
sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from agi_news import latest_issue_meta, _http_get

meta = latest_issue_meta()
print("ima 最新期:", meta["date"], meta["title"])
print("source_url:", meta["source_url"])

html = _http_get(meta["source_url"], timeout=40)
print("文章页大小:", len(html))

# 1) __biz
m = re.search(r'__biz=([A-Za-z0-9]+)', html)
print("__biz:", m.group(1) if m else None)

# 2) 合集 album 链接 (appmsgalbum)
albums = set(re.findall(r'(mp\.weixin\.qq\.com/mp/appmsgalbum[^"\']+)', html))
for a in list(albums)[:10]:
    print("album link:", a[:200])

# 3) 账号名
m = re.search(r'var nickname = htmlDecode\("([^"]+)"\)|<strong class="profile_nickname"[^>]*>([^<]+)</strong>|id="js_name"[^>]*>\s*([^<\s]+)', html)
print("nickname:", (m.group(1) or m.group(2) or m.group(3)) if m else None)

# 4) 发布时间
m = re.search(r'var ct = "?(\d+)"?|publish_time["\s:=]+(\d{10})', html)
ts = (m.group(1) or m.group(2)) if m else None
if ts:
    import datetime
    print("publish ts:", ts, datetime.datetime.fromtimestamp(int(ts)))
else:
    m2 = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', html)
    print("publish time str:", m2.group(1) if m2 else None)

# 5) 合集区块 (专辑名 + 计数)
for m in re.finditer(r'album[^>]*>', html[:100000]):
    pass
al = re.findall(r'album_id["\s:=]+(\d+)', html)
print("album_ids:", set(al))

# 6) 检查文内其他速递文章链接(往期)
links = set(re.findall(r'(https?://mp\.weixin\.qq\.com/s[/?][^"\'<>\s]+)', html))
print("文内微信链接数:", len(links))
for l in list(links)[:5]:
    print("  ", l[:150])
