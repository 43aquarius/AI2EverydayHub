# -*- coding: utf-8 -*-
"""隔离验证: 在真实帖子上复现 add_illus_to_post.py 的插入逻辑"""
import json
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient

NUM_MAP = {"1️⃣": 1, "2️⃣": 2, "3️⃣": 3, "4️⃣": 4, "5️⃣": 5,
           "6️⃣": 6, "7️⃣": 7, "8️⃣": 8, "9️⃣": 9, "🔟": 10,
           "1️⃣1️⃣": 11, "1️⃣2️⃣": 12}

cfg = json.load(open("/home/z/my-project/github-hot-heybox/config.json"))
c = HeyboxClient(cfg["cookie"])
r = c.get("/bbs/app/link/edit/info", params={"link_id": "194368242"})
blocks = json.loads(r["result"]["link"]["text"])

# --- 完全复刻 add_illus_to_post.py 的解析与插入 ---
news = []
for i, b in enumerate(blocks):
    if b.get("type") != "text":
        continue
    first_line = b["text"].split("\n", 1)[0]
    num = None
    for emoji, n in NUM_MAP.items():
        if first_line.startswith(emoji):
            num = n
            break
    if num:
        news.append((i, num))
print("解析出的 (块索引, 序号):", news)

idx_by_num = {n: i for i, n in news}
print("idx_by_num:", idx_by_num)

# 模拟: 第1条和第8条后插图
illustrations = {1: "/fake/1.png", 8: "/fake/8.png"}
plan = []
for num, path in sorted(illustrations.items(), reverse=True):
    plan.append((idx_by_num[num] + 1, {"type": "img", "url": path,
                                       "width": 1344, "height": 768}))
print("plan(插入位置):", [(p, b["url"]) for p, b in plan])
for pos, img_blk in plan:
    blocks.insert(pos, img_blk)

print(f"\n插入后总块数: {len(blocks)}")
for i, b in enumerate(blocks):
    if b["type"] == "text":
        print(f"[{i:2d}] text {len(b['text']):4d}字 | {b['text'][:30]!r}")
    else:
        print(f"[{i:2d}] IMG  {b['width']}x{b['height']} | {b['url']}")
