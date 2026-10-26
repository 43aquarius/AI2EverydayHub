# -*- coding: utf-8 -*-
"""周榜帖标题修正: '单日新进22万星' → '一周暴涨22万星'(事实对齐, 正文不动)"""
import json
import re
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient
from heybox_publisher import count_words

LINK_ID = "194370432"
NEW_TITLE = "一周暴涨22万星,这个逆向工程AI工具火了"

cfg = json.load(open("/home/z/my-project/github-hot-heybox/config.json"))
c = HeyboxClient(cfg["cookie"])

r = c.get("/bbs/app/link/edit/info", params={"link_id": LINK_ID})
d = r if isinstance(r, dict) else r.json()
assert d.get("status") == "ok", d
link = d["result"]["link"]
blocks = json.loads(link["text"])
old_title = link["title"]
print(f"原标题: {old_title}")
print(f"新标题: {NEW_TITLE}")

full_text = "\n".join(b["text"] for b in blocks if b["type"] == "text")
desc = re.sub(r"\s", " ", blocks[0]["text"])[:80]
body = {
    "edit": "1", "link_id": LINK_ID, "link_tag": "27",
    "text": json.dumps(blocks, ensure_ascii=False),
    "title": NEW_TITLE, "desc": desc,
    "words_count": str(count_words(full_text)),
    "topic_ids": "7214", "hashtags": "[]", "schedule_ts": "0",
    "view_limit": "1", "post_type": "1", "original": "1",
    "declaration": "0",
}
if "--go" in sys.argv:
    resp = c.post_form("/bbs/app/api/link/post", body)
    print("编辑结果:", json.dumps(resp, ensure_ascii=False)[:200])
else:
    print("[DRY] 加 --go 真实提交")
