# -*- coding: utf-8 -*-
"""把今日 AGI 帖(图文模式,图被归一化到末尾)重发为文章模式(行内插图)

流程:
  1. edit/info 取旧帖全部内容(文字块 + 长图URL)
  2. 长图 URL 下载到本地(复用同一张图,不重渲染)
  3. segments 组装: 文字块原样 + 第1/8条新闻后插配图 + 末尾长图
  4. publisher.publish(article=True) 发文章帖
  5. 验证(edit/info 行内位置) → 删除旧帖 → 更新 state
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient
from heybox_publisher import HeyboxPublisher

OLD_ID = "194368242"
OUT = "/home/z/my-project/github-hot-heybox/output"
ILLUS = {1: f"{OUT}/agi_illus_edit_v2_20261019_041702_1.png",
         8: f"{OUT}/agi_illus_edit_20261019_041040_8.png"}
GO = "--go" in sys.argv

NUM_MAP = {"1️⃣": 1, "2️⃣": 2, "3️⃣": 3, "4️⃣": 4, "5️⃣": 5,
           "6️⃣": 6, "7️⃣": 7, "8️⃣": 8, "9️⃣": 9, "🔟": 10}

cfg = json.load(open("/home/z/my-project/github-hot-heybox/config.json"))
c = HeyboxClient(cfg["cookie"])
pub = HeyboxPublisher(c, topic_ids=str(cfg.get("topic_ids", "7214")))

# 1) 取旧帖内容
r = c.get("/bbs/app/link/edit/info", params={"link_id": OLD_ID})
assert r.get("status") == "ok", r
link = r["result"]["link"]
old_blocks = json.loads(link["text"])
title = link["title"]
print(f"旧帖: {title} ({len(old_blocks)}块)")

# 2) 长图: 优先用本地原图(线上 URL 是缩略图); 没有再下载
long_local = os.path.join(OUT, "agi_news_20261019_021527.png")
if not os.path.exists(long_local):
    long_url = ""
    for b in old_blocks:
        if b.get("type") == "img" and b.get("width") == 2160:
            long_url = b["url"]
            break
    assert long_url, "没找到长图块"
    long_local = os.path.join(OUT, "agi_long_reuse.png")
    req = urllib.request.Request(long_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp, open(long_local, "wb") as f:
        f.write(resp.read())
print(f"长图: {os.path.basename(long_local)} ({os.path.getsize(long_local)//1024}KB)")

# 3) 组装 segments
segs = []
for b in old_blocks:
    if b.get("type") == "text":
        t = b["text"]
        segs.append(("text", t))
        first_line = t.split("\n", 1)[0]
        for emoji, n in NUM_MAP.items():
            if first_line.startswith(emoji):
                if n in ILLUS:
                    segs.append(("img", ILLUS[n]))
                break
segs.append(("img", long_local))
kinds = ["T" if k == "text" else "I" for k, _ in segs]
print(f"segments: {''.join(kinds)} ({len(segs)}段, 图{len(ILLUS)+1}张)")

if not GO:
    print("\n[DRY] 预览 segments 序列(加 --go 真实发布+删旧帖):")
    for i, (k, v) in enumerate(segs):
        if k == "text":
            print(f"  [{i:2d}] T {v[:36]!r}")
        else:
            print(f"  [{i:2d}] I {os.path.basename(v)}")
    sys.exit(0)

# 4) 发布文章帖
result = pub.publish(title=title, segments=segs, dry_run=False)
new_id = result.get("link_id")
print(f"\n新帖: {new_id} → {result.get('post_url')}")
assert new_id and new_id != OLD_ID

# 5) 验证行内位置
r2 = c.get("/bbs/app/link/edit/info", params={"link_id": new_id})
blocks2 = json.loads(r2["result"]["link"]["text"])
h = blocks2[0].get("text", "")
checks_ok = True
# 简单校验: 行内图3张 + 图库3张
n_inline = h.count("<img ")
n_gallery = sum(1 for b in blocks2 if b.get("type") == "img")
print(f"验证: 行内图 {n_inline} 张, 图库 {n_gallery} 张")
checks_ok = n_inline == 3 and n_gallery == 3
# 第1条图在"Meta搞了个大新闻"之前
p1_img = h.find("<img ")
p1_body = h.find("Meta搞了个大新闻")
checks_ok = checks_ok and (h.find("欢迎来到") < p1_img < p1_body)
# 第8条图在"Anthropic内部报告"之后
p8_body = h.find("Anthropic内部报告")
p8_next = h.find("以上就是这个板块")
img_before_outro = h.rfind("<img ", 0, h.find("以上就是这个板块"))
checks_ok = checks_ok and (p8_body < img_before_outro < p8_next)
print("位置校验:", "通过 ✅" if checks_ok else "失败 ❌")
if not checks_ok:
    print(h[:600])
    sys.exit("校验失败, 保留旧帖, 请人工检查新帖")

# 6) 删旧帖 + 更新 state
resp = pub.delete_post(OLD_ID)
print(f"删除旧帖 {OLD_ID}: {json.dumps(resp, ensure_ascii=False)[:120]}")

STATE = "/home/z/my-project/github-hot-heybox/state.json"
state = json.load(open(STATE))
for h_entry in state.get("history", []):
    if h_entry.get("url", "").endswith(f"/{OLD_ID}"):
        h_entry["url"] = result["post_url"]
        h_entry["note"] = f"重发为文章模式(行内插图), 原帖{OLD_ID}已删"
json.dump(state, open(STATE, "w"), ensure_ascii=False, indent=2)
print("state history 已更新")
print(f"\n🎉 完成: {result['post_url']}")
