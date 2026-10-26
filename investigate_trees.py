# -*- coding: utf-8 -*-
"""调查3: 拉几篇真实文字帖的正文块, 看空行/分段/表情怎么编码"""
import json
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient

with open("/home/z/my-project/github-hot-heybox/config.json") as f:
    cfg = json.load(f)
client = HeyboxClient(cfg["cookie"])

POSTS = [
    ("194003789", "教你怎么用Pi(图文教程)"),
    ("194050614", "大项目不要开AI记忆系统"),
    ("194030566", "200万人看过的提示词"),
    ("194125083", "北邮小黑盒校招"),
]

for lid, label in POSTS:
    print(f"\n{'='*70}\n[{label}] {lid}")
    try:
        data = client.get_post_tree(lid)
    except Exception as e:
        print("  失败:", e)
        continue
    link = (data.get("result") or {}).get("link") or {}
    text_raw = link.get("text")
    blocks = None
    if isinstance(text_raw, str):
        try:
            blocks = json.loads(text_raw)
        except json.JSONDecodeError:
            pass
    elif isinstance(text_raw, list):
        blocks = text_raw
    if not isinstance(blocks, list):
        print("  text 解析失败")
        continue
    print(f"  块数: {len(blocks)}")
    for i, b in enumerate(blocks[:40]):
        t = b.get("type")
        if t == "text":
            txt = b.get("text", "")
            if not txt.strip():
                print(f"    {i:>3} text   | <空块 raw={txt!r}>")
            else:
                nl = " ⏎含换行" if "\n" in txt else ""
                print(f"    {i:>3} text   | {txt[:46]!r}{nl}")
        elif t == "img":
            print(f"    {i:>3} img    | {str(b.get('url'))[:50]}")
        else:
            print(f"    {i:>3} {t!r} | {json.dumps(b, ensure_ascii=False)[:50]}")
    if len(blocks) > 40:
        print(f"    …还有{len(blocks)-40}块")
