# -*- coding: utf-8 -*-
"""编辑已发布帖子: 修正 AGI 日报 intro 的条数声明(9条→8条)
流程: GET edit/info(全量块) → 本地修正 → POST link/post (edit=1)
"""
import json
import re
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient
from heybox_publisher import count_words

LINK_ID = "194368242"

cfg = json.load(open("/home/z/my-project/github-hot-heybox/config.json"))
c = HeyboxClient(cfg["cookie"])

# 1) 取全量编辑数据
r = c.get("/bbs/app/link/edit/info", params={"link_id": LINK_ID})
d = r if isinstance(r, dict) else r.json()
assert d.get("status") == "ok", d
link = d["result"]["link"]
blocks = json.loads(link["text"])
title = link["title"]
print(f"取到帖子 {LINK_ID}: {title}")
print(f"块数: {len(blocks)} ({sum(1 for b in blocks if b['type']=='text')}文字"
      f"/{sum(1 for b in blocks if b['type']=='img')}图片)")

# 2) 修正 intro 块的条数声明
intro = blocks[0]["text"]
n_text_blocks = sum(1 for b in blocks if b["type"] == "text")
# 实际新闻条数 = 文字块数 - intro - outro - 话题标签(3个固定块)
n_news = n_text_blocks - 3
m = re.search(r"(\d+)\s*条", intro)
print(f"intro 当前: {intro[:60]}")
print(f"实际新闻条数: {n_news}")
if m and int(m.group(1)) != n_news:
    blocks[0]["text"] = intro[:m.start(1)] + str(n_news) + intro[m.end(1):]
    print(f"✓ 修正条数: {m.group(1)} → {n_news}")
else:
    print("条数一致或未找到声明, 无需修改")

# 3) 组装编辑请求(与浏览器编辑器完全同构)
full_text = "\n".join(b["text"] for b in blocks if b["type"] == "text")
desc = re.sub(r"\s", " ", blocks[0]["text"])[:80]
body = {
    "edit": "1",
    "link_id": LINK_ID,
    "link_tag": "27",
    "text": json.dumps(blocks, ensure_ascii=False),
    "title": title,
    "desc": desc,
    "words_count": str(count_words(full_text)),
    "topic_ids": "7214",
    "hashtags": "[]",
    "schedule_ts": "0",
    "view_limit": "1",
    "post_type": "1",
    "original": "1",
    "declaration": "0",
}

if "--go" not in sys.argv:
    print("\n[DRY] 仅预览, 加 --go 真实提交")
    print("新 intro:", blocks[0]["text"][:80])
    print("words_count:", body["words_count"], "| desc:", desc[:50])
else:
    resp = c.post_form("/bbs/app/api/link/post", body)
    print("\n提交结果:", json.dumps(resp, ensure_ascii=False)[:300])
