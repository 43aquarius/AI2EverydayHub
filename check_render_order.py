# -*- coding: utf-8 -*-
"""抓线上帖子页, 看正文与图片的实际渲染顺序"""
import re
import urllib.request

URL = "https://www.xiaoheihe.cn/community/7214/list/194368242"
req = urllib.request.Request(URL, headers={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"})
html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
print(f"页面大小: {len(html)}")

# SSR 内容通常在 __NUXT__ 或 window.__INITIAL_STATE__
# 找出正文中 段落文本 与 <img> 的相对顺序
m = re.search(r'window\.__NUXT__\s*=\s*(.+?)</script>', html, re.S)
if not m:
    m = re.search(r'__INITIAL_STATE__\s*=\s*(.+?);?\s*</script>', html, re.S)
if m:
    data = m.group(1)
    print("找到 NUXT 数据, 长度:", len(data))
    # 按 link/content 部分粗提取顺序: 依次找 文本片段 与 图片URL
    # 简化: 找所有 imgheybox URL 出现位置 + 关键文本锚点位置
    anchors = ["欢迎来到小黑盒", "Meta开源Muse Spark", "ChatGPT Chrome",
               "Anthropic", "以上就是这个板块", "AGI#", "816B",
               "imgheybox"]
    events = []
    for a in anchors[:6] + ["#AGI#"]:
        for mm in re.finditer(re.escape(a), data):
            events.append((mm.start(), "TEXT:" + a[:14]))
            break
    for mm in re.finditer(r'https://imgheybox[^"\\]+', data):
        url = mm.group(0)
        if "/thumb" in url or "format" in url:
            kind = "IMG?"
        else:
            kind = "IMG"
        events.append((mm.start(), kind + " " + url[-24:]))
    events.sort()
    for pos, e in events[:40]:
        print(f"  @{pos:>8} {e}")
else:
    print("未找到 NUXT 数据, 检查页面结构...")
    # 直接找正文容器
    for pat in ["content", "link-content", "article"]:
        found = re.findall(pat, html)
        print(f"  '{pat}' 出现 {len(found)} 次")
