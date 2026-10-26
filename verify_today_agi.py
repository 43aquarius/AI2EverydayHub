# -*- coding: utf-8 -*-
"""验证今日小黑盒 AGI 帖: 标题/正文完整性/行内插图位置/红线检查"""
import json, sys, re

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient

LINK_ID = sys.argv[1] if len(sys.argv) > 1 else "194471042"

cfg = json.load(open("/home/z/my-project/github-hot-heybox/config.json", encoding="utf-8"))
client = HeyboxClient(cfg["cookie"])

# 1) edit/info 拿全量块
data = client.get("/bbs/app/link/edit/info", {"link_id": LINK_ID})
res = data.get("result") or {}
print("status:", data.get("status"))
link = res.get("link") or {}
title = link.get("title") or ""
print("标题:", title)

blocks = json.loads(link.get("text") or "[]")
print(f"块数: {len(blocks)}")

full_text = ""
inline_imgs = 0
for i, b in enumerate(blocks):
    t = b.get("type")
    if t == "html" or "html" in str(t).lower() or b.get("html"):
        h = b.get("html") or b.get("content") or b.get("text") or ""
        imgs = h.count("<img")
        inline_imgs += imgs
        text = re.sub(r"<[^>]+>", " ", h)
        full_text += text + "\n"
        print(f"  [块{i}] {t} {len(h)}字 行内图{imgs} | {text.strip()[:56]}")
    elif t == "img":
        print(f"  [块{i}] img: {str(b.get('url') or b.get('imgs') or '')[:70]}")
    else:
        c = b.get("text") or b.get("content") or ""
        full_text += str(c) + "\n"
        print(f"  [块{i}] {t} | {str(c)[:56]}")

print(f"\n正文总字数(去标签): {len(re.sub(chr(10)+'| ', '', full_text))}")
print(f"行内插图总数: {inline_imgs}")

# 红线检查
for kw in ["ima", "IMA", "知识库", "腾讯研究院"]:
    n = full_text.count(kw)
    print(f"红线 '{kw}': {n} 次 {'❌' if n else '✓'}")

# 关键内容抽查: 9条新闻的编号标题是否都在
for kw in ["1️⃣", "9️⃣", "Meta", "Anthropic", "OpenAI", "机器人", "AGI"]:
    print(f"内容抽查 '{kw}': {'✓' if kw in full_text else '⚠ 缺失'}")

# 话题标签
tags = re.findall(r"#([^#\n]{2,12})#", full_text)
print("话题标签:", tags[:6])
