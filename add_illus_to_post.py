# -*- coding: utf-8 -*-
"""给已发布的 AGI 日报帖插入小黑手绘配图(编辑 API 全量提交)

流程:
  1. GET /bbs/app/link/edit/info 取全量块
  2. 从正文块解析新闻条目(编号emoji识别)
  3. illustrator.make_illustrations 生成配图(LLM挑锚点→生图→VLM质检)
  4. 上传配图 → 插入到对应新闻文字块后面
  5. POST /bbs/app/api/link/post (edit=1) 全量提交

用法: python add_illus_to_post.py <link_id> [--go]
不加 --go 只预览不提交。
"""
import json
import re
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient
from heybox_publisher import HeyboxPublisher, count_words
from illustrator import make_illustrations

LINK_ID = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].isdigit() else "194368242"
GO = "--go" in sys.argv

NUM_MAP = {"1️⃣": 1, "2️⃣": 2, "3️⃣": 3, "4️⃣": 4, "5️⃣": 5,
           "6️⃣": 6, "7️⃣": 7, "8️⃣": 8, "9️⃣": 9, "🔟": 10,
           "1️⃣1️⃣": 11, "1️⃣2️⃣": 12}

cfg = json.load(open("/home/z/my-project/github-hot-heybox/config.json"))
c = HeyboxClient(cfg["cookie"])
pub = HeyboxPublisher(c, topic_ids=str(cfg.get("topic_ids", "7214")))

# 1) 取全量编辑数据
r = c.get("/bbs/app/link/edit/info", params={"link_id": LINK_ID})
assert r.get("status") == "ok", r
link = r["result"]["link"]
blocks = json.loads(link["text"])
title = link["title"]
print(f"取到帖子 {LINK_ID}: {title}")
print(f"现有块: {len(blocks)} "
      f"({sum(1 for b in blocks if b['type']=='text')}文字/"
      f"{sum(1 for b in blocks if b['type']=='img')}图片)")

# 2) 解析新闻条目(块索引 + 序号 + 标题 + 正文)
news = []           # [(block_idx, num, headline, full_text)]
for i, b in enumerate(blocks):
    if b.get("type") != "text":
        continue
    first_line = b["text"].split("\n", 1)[0]
    num = None
    for emoji, n in NUM_MAP.items():
        if first_line.startswith(emoji):
            num = n
            headline = first_line[len(emoji):].strip()
            break
    if num:
        news.append((i, num, headline, b["text"]))
print(f"识别到 {len(news)} 条新闻条目")

# 3) 生成配图
items = [{"num": n, "headline": h, "summary": t[:400]} for _, n, h, t in news]
illus_cfg = cfg.get("illustrations") or {}
MAX = int(illus_cfg.get("agi_max", 3))
illustrations = make_illustrations(
    title, items, "/home/z/my-project/github-hot-heybox/output",
    prefix="agi_illus_edit", max_count=MAX)
if not illustrations:
    print("没有生成任何配图, 退出")
    sys.exit(1)

# 4) 上传 + 插入(从高索引往低插, 不破坏前面的索引)
idx_by_num = {n: i for i, n, _, _ in news}
plan = []                                  # [(插入位置(其后), img_block)]
for num, path in sorted(illustrations.items(), reverse=True):
    blk = pub.upload_local_image(path)
    print(f"   上传第{num}条配图 → {blk['url'][:60]}...")
    plan.append((idx_by_num[num] + 1, {"type": "img", **blk}))
for pos, img_blk in plan:
    blocks.insert(pos, img_blk)

print(f"\n插入后块数: {len(blocks)} "
      f"({sum(1 for b in blocks if b['type']=='text')}文字/"
      f"{sum(1 for b in blocks if b['type']=='img')}图片)")

# 5) 组装编辑请求
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
    print("\n[DRY] 仅预览, 加 --go 真实提交")
    print("块序列: " + " → ".join(
        f"文字{len(b['text'])}字" if b["type"] == "text" else
        f"图{b['width']}x{b['height']}" for b in blocks))
else:
    resp = c.post_form("/bbs/app/api/link/post", body)
    print("\n提交结果:", json.dumps(resp, ensure_ascii=False)[:300])
    if resp.get("status") == "ok":
        print(f"✅ 编辑成功: https://www.xiaoheihe.cn/community/7214/list/{LINK_ID}")
