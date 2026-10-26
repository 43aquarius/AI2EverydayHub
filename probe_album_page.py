# -*- coding: utf-8 -*-
"""抓微信合集页(appmsgalbum) → 解析文章列表(标题/链接/发布时间)"""
import re
import sys
import json
import datetime
sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from agi_news import _http_get, _js_unescape

ALBUM_URL = ("https://mp.weixin.qq.com/mp/appmsgalbum"
             "?__biz=MjM5OTE0ODA2MQ==&action=getalbum"
             "&album_id=3349853949226418182")

html = _http_get(ALBUM_URL, timeout=40)
print("合集页大小:", len(html))

# 方式1: window.__appmsgalbumData (SSR JSON)
m = re.search(r'window\.__appmsgalbumData\s*=\s*(\{.*?\})\s*[;<]', html, re.S)
print("__appmsgalbumData found:", bool(m))
if m:
    raw = _js_unescape(m.group(1))
    try:
        data = json.loads(raw)
        print("keys:", list(data.keys()))
        items = data.get("getalbum_resp", {}).get("getalbum_resp_data", {}).get("article_list", [])
        print("文章数(本页):", len(items))
        for it in items[:12]:
            ts = it.get("create_time") or it.get("update_time")
            t = datetime.datetime.fromtimestamp(int(ts)) if ts else "?"
            print(f"  {t} | {it.get('title') or it.get('title_plain')} | "
                  f"{(it.get('url') or '')[:60]}")
    except Exception as e:
        print("JSON 解析失败:", e)
        print(raw[:500])
else:
    # 方式2: 正则逐条解析 <li class="album__list-item">
    items = re.findall(
        r'<li class="album__list-item[^"]*"[^>]*>.*?'
        r'<div class="album__item-title-wrp">\s*<div class="album__item-title">([^<]+)</div>.*?'
        r'<div class="album__item-info-item">([^<]*)</div>.*?'
        r'href="([^"]+)"', html, re.S)
    print("regex items:", len(items))
    for t, d, u in items[:12]:
        print(f"  {d} | {t} | {u[:60]}")
