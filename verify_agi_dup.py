#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核实: 小黑盒今日00:16帖子的类型 + 微信合集最新一期"""
import datetime
import gzip
import io
import json
import re
import sys
import urllib.request

BJT = datetime.timezone(datetime.timedelta(hours=8))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
    return raw.decode("utf-8", "ignore")


# ---- 1. 小黑盒 00:16 帖子内容 ----
print("=" * 50, "\n[1] 小黑盒创作者中心最新帖内容")
sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient  # noqa: E402
cfg = json.load(open("/home/z/my-project/github-hot-heybox/config.json"))
client = HeyboxClient(cfg["cookie"])
data = client.get("/bbs/app/author/concept/article/list", {
    "article_type": "all", "artilce_state": "all",
    "sort_filter": "create_at", "offset": "0", "limit": "3"})
arts = (data.get("result") or {}).get("articles") or []
target = None
for a in arts:
    ts = a.get("create_at")
    t = datetime.datetime.fromtimestamp(ts, BJT) if isinstance(ts, (int, float)) and ts > 10**9 else None
    if t and t.strftime("%m-%d %H:%M") == "10-23 00:16":
        target = a
if not target and arts:
    target = arts[0]  # 退而求其次: 最新一条
    ts = target.get("create_at")
    t = datetime.datetime.fromtimestamp(ts, BJT)
    print(f"(未精确命中00:16, 用最新帖 {t:%m-%d %H:%M})")
if target:
    link_id = target.get("link_id")
    print(f"link_id={link_id} title={target.get('title','')[:40]}")
    tree = client.get("/bbs/app/link/tree", {"link_id": str(link_id)})
    text = (((tree.get("result") or {}).get("link") or {}).get("text") or "[]")
    try:
        blocks = json.loads(text)
        chars = 0
        for b in blocks:
            if b.get("type") == "text" and b.get("text"):
                print("  TEXT:", b["text"][:220].replace("\n", " ⏎ "))
                chars += len(b["text"])
                if chars > 400:
                    break
    except Exception as e:
        print("  [warn] text解析失败:", e)

# ---- 2. 微信合集最新一期 ----
print("=" * 50, "\n[2] 微信合集(腾讯研究院AI速递)最新期")
WX_ALBUM_URL = ("https://mp.weixin.qq.com/mp/appmsgalbum"
                "?__biz=MjM5OTE0ODA2MQ==&action=getalbum"
                "&album_id=3349853949226418182")
html = http_get(WX_ALBUM_URL)
m = re.search(r"var\s+cgiData\s*=\s*(\{.*?\});?\s*</script>", html, re.S)
if not m:
    m = re.search(r"articleList\s*[:=]\s*(\[.*?\])[,;]", html, re.S)
if m:
    try:
        raw = m.group(1)
        # js对象 → json 粗修
        raw = re.sub(r'(\w+)\s*:', r'"\1":', raw.count("{") and raw or raw)
        items = json.loads(raw)
    except Exception:
        items = json.loads(re.search(r"articleList\s*[:=]\s*(\[.*?\])[,;]",
                                     html, re.S).group(1))
else:
    items = []
if not items:
    # 退化: 直接正则抓标题
    titles = re.findall(r'title\s*:\s*["\']([^"\']{8,80})["\']', html)
    items = [{"title": t} for t in titles[:5]]
for it in items[:5]:
    ts = it.get("createTime") or it.get("create_time") or ""
    print(f"  [{ts}] {it.get('title','')[:60]}")
