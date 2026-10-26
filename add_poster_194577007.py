# -*- coding: utf-8 -*-
"""给 194577007(AMMH 安利帖, 纯文字版) 补上海报图
流程: 上传海报 → edit/info 取块 → 追加 img 块 → POST edit=1"""
import json
import re
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient
from heybox_publisher import HeyboxPublisher, count_words

LINK_ID = "194577007"
POSTER = ("/home/z/my-project/github-hot-heybox/output/"
          "project_ai-money-maker-handbook_20261021_032133.png")

cfg = json.load(open("/home/z/my-project/github-hot-heybox/config.json",
                     encoding="utf-8"))
c = HeyboxClient(cfg["cookie"])

# 1) 上传海报
pub = HeyboxPublisher(c, topic_ids="7214")
up = pub.upload_local_image(POSTER)
print("上传:", json.dumps(up, ensure_ascii=False)[:160])
url = up["url"] if isinstance(up, dict) else up

# 2) 取当前块
d = c.get("/bbs/app/link/edit/info", {"link_id": LINK_ID})
link = d["result"]["link"]
blocks = json.loads(link["text"])
title = link["title"]
print(f"当前 {len(blocks)} 块, 标题: {title}")

# 3) 追加 img 块(与实发帖同构)
img_block = {"url": url, "width": "2160", "type": "img", "height": "2408"}
blocks.append(img_block)

# 4) 编辑提交(文章模式 link_tag=11)
full_text = blocks[0]["text"] if blocks[0]["type"] == "html" else ""
plain = re.sub(r"<[^>]+>", " ", full_text)
body = {
    "edit": "1",
    "link_id": LINK_ID,
    "link_tag": "11",
    "text": json.dumps(blocks, ensure_ascii=False),
    "title": title,
    "desc": re.sub(r"\s", " ", plain)[:80],
    "words_count": str(count_words(plain)),
    "topic_ids": "7214",
    "hashtags": "[]",
    "schedule_ts": "0",
    "view_limit": "1",
    "post_type": "1",
    "original": "1",
    "declaration": "0",
}
resp = c.post_form("/bbs/app/api/link/post", body)
print("编辑响应:", json.dumps(resp, ensure_ascii=False)[:200])

# 5) 回读验证
d2 = c.get("/bbs/app/link/edit/info", {"link_id": LINK_ID})
blocks2 = json.loads(d2["result"]["link"]["text"])
n_img = sum(1 for b in blocks2 if b.get("type") == "img")
print(f"回读: {len(blocks2)} 块, img 块 {n_img}")
print("✅ 海报已补上" if n_img >= 1 else "❌ 未生效")
