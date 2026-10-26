# -*- coding: utf-8 -*-
"""给 194577007 补海报(行内<img data-*> + 图库块 双写, 与实发帖同构)
前次教训: 只加图库 img 块会被服务器剥离——文章模式图库块必须
有 html 内行内引用配对"""
import json
import re
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient
from heybox_publisher import count_words

LINK_ID = "194577007"
POSTER = ("/home/z/my-project/github-hot-heybox/output/"
          "project_ai-money-maker-handbook_20261021_032133.png")

cfg = json.load(open("/home/z/my-project/github-hot-heybox/config.json",
                     encoding="utf-8"))
c = HeyboxClient(cfg["cookie"])

# 1) 上传海报拿新 URL
from heybox_publisher import HeyboxPublisher
pub = HeyboxPublisher(c, topic_ids="7214")
up = pub.upload_local_image(POSTER)
url, w, h = up["url"], str(up["width"]), str(up["height"])
print(f"上传: {url[-40:]} ({w}x{h})")

# 2) 取当前块
d = c.get("/bbs/app/link/edit/info", {"link_id": LINK_ID})
link = d["result"]["link"]
blocks = json.loads(link["text"])
title = link["title"]
print(f"当前 {len(blocks)} 块")

# 3) 行内引用追加到 html 末尾 + 图库块(双写)
blocks[0]["text"] += (
    f'<p><img data-type="image" data-original="{url}" '
    f'data-width="{w}" data-height="{h}" data-description=""></p>')
blocks.append({"type": "img", "url": url, "width": w, "height": h})

# 4) 提交编辑
plain = re.sub(r"<[^>]+>", " ", blocks[0]["text"])
body = {
    "edit": "1", "link_id": LINK_ID, "link_tag": "11",
    "text": json.dumps(blocks, ensure_ascii=False),
    "title": title,
    "desc": re.sub(r"\s", " ", plain)[:80],
    "words_count": str(count_words(plain)),
    "topic_ids": "7214", "hashtags": "[]", "schedule_ts": "0",
    "view_limit": "1", "post_type": "1", "original": "1",
    "declaration": "0",
}
resp = c.post_form("/bbs/app/api/link/post", body)
print("编辑响应:", json.dumps(resp, ensure_ascii=False)[:160])

# 5) 回读验证(带重试, 服务器归一化有几秒延迟)
import time
for i in range(4):
    time.sleep(6)
    d2 = c.get("/bbs/app/link/edit/info", {"link_id": LINK_ID})
    blocks2 = json.loads(d2["result"]["link"]["text"])
    n_img = sum(1 for b in blocks2 if b.get("type") == "img")
    n_inline = blocks2[0]["text"].count("<img") if blocks2 else 0
    print(f"读{i+1}: {len(blocks2)} 块, img块 {n_img}, 行内 {n_inline}")
    if n_img >= 1 and n_inline >= 1:
        print("✅ 海报双写成功且稳定")
        break
else:
    print("⚠ 仍未稳定, 帖子保持纯文字(内容已完整)")
