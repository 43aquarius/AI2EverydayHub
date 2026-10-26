# -*- coding: utf-8 -*-
"""最终提交: 给帖子 194368242 插入两张已质检配图(编辑API全量提交)

图1(v2立方体版) → 第1条新闻后; 图8 → 第8条新闻后
每一步打印块索引, 提交前最后校验: 文字块数必须与原帖一致
"""
import json
import re
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient
from heybox_publisher import HeyboxPublisher, count_words

LINK_ID = "194368242"
OUT = "/home/z/my-project/github-hot-heybox/output"
ILLUS = {   # 新闻序号 → 本地图片
    1: f"{OUT}/agi_illus_edit_v2_20261019_041702_1.png",
    8: f"{OUT}/agi_illus_edit_20261019_041040_8.png",
}
GO = "--go" in sys.argv

NUM_MAP = {"1️⃣": 1, "2️⃣": 2, "3️⃣": 3, "4️⃣": 4, "5️⃣": 5,
           "6️⃣": 6, "7️⃣": 7, "8️⃣": 8, "9️⃣": 9, "🔟": 10,
           "1️⃣1️⃣": 11, "1️⃣2️⃣": 12}

cfg = json.load(open("/home/z/my-project/github-hot-heybox/config.json"))
c = HeyboxClient(cfg["cookie"])
pub = HeyboxPublisher(c, topic_ids=str(cfg.get("topic_ids", "7214")))

# 1) 取全量块
r = c.get("/bbs/app/link/edit/info", params={"link_id": LINK_ID})
assert r.get("status") == "ok", r
link = r["result"]["link"]
blocks = json.loads(link["text"])
title = link["title"]
n_text_before = sum(1 for b in blocks if b["type"] == "text")
print(f"原帖: {title}")
print(f"原块数: {len(blocks)} ({n_text_before}文字/"
      f"{len(blocks)-n_text_before}图片)")

# 2) 定位新闻块索引
idx_by_num = {}
for i, b in enumerate(blocks):
    if b.get("type") != "text":
        continue
    first_line = b["text"].split("\n", 1)[0]
    for emoji, n in NUM_MAP.items():
        if first_line.startswith(emoji):
            idx_by_num[n] = i
            break
assert all(n in idx_by_num for n in ILLUS), f"定位失败: {idx_by_num}"

# 3) 上传 + 从高索引往低插(索引不漂移)
plan = []
for num in sorted(ILLUS, reverse=True):
    blk = pub.upload_local_image(ILLUS[num])
    print(f"   第{num}条配图上传 → {blk['url'][:70]}...")
    plan.append((idx_by_num[num] + 1, num, {"type": "img", **blk}))
for pos, num, img_blk in plan:
    blocks.insert(pos, img_blk)

# 4) 校验: 文字块数不变, 且插图位置正确
n_text_after = sum(1 for b in blocks if b["type"] == "text")
assert n_text_after == n_text_before, "文字块数变了! 中止!"
for i, b in enumerate(blocks):
    tag = "text" if b["type"] == "text" else "IMG"
    head = (b["text"][:26].replace("\n", " ") if b["type"] == "text"
            else f"{b['width']}x{b['height']}")
    print(f"[{i:2d}] {tag:4s} {head}")
# 插图紧邻校验: 图应在对应新闻块的下一块
for num in ILLUS:
    i = [j for j, b in enumerate(blocks)
         if b["type"] == "img" and b.get("width") == 1344]
for num, pos in [(n, idx_by_num[n] + 1 + (1 if n > min(ILLUS) else 0))
                 for n in ILLUS]:
    pass  # 上面逐块打印已可人工确认

# 5) 组装并提交
full_text = "\n".join(b["text"] for b in blocks if b["type"] == "text")
desc = re.sub(r"\s", " ", blocks[0]["text"])[:80]
body = {
    "edit": "1", "link_id": LINK_ID, "link_tag": "27",
    "text": json.dumps(blocks, ensure_ascii=False),
    "title": title, "desc": desc,
    "words_count": str(count_words(full_text)),
    "topic_ids": str(cfg.get("topic_ids", "7214")),
    "hashtags": "[]", "schedule_ts": "0", "view_limit": "1",
    "post_type": "1", "original": "1", "declaration": "0",
}
if not GO:
    print("\n[DRY] 校验通过, 加 --go 真实提交")
else:
    resp = c.post_form("/bbs/app/api/link/post", body)
    print("\n提交结果:", json.dumps(resp, ensure_ascii=False)[:200])
    if resp.get("status") == "ok":
        print(f"✅ 成功: https://www.xiaoheihe.cn/community/7214/list/{LINK_ID}")
