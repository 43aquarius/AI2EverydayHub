# -*- coding: utf-8 -*-
"""调查小黑盒真实帖子的富文本块结构:
- 空行如何表示(空 text 块? \\n 块内换行? 特殊字符?)
- 图文交错帖子的块顺序
- 我们自己已发帖子(194210321)的实际块结构
"""
import json
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient

with open("/home/z/my-project/github-hot-heybox/config.json") as f:
    cfg = json.load(f)
client = HeyboxClient(cfg["cookie"])


def dump_post(link_id: str, label: str, max_blocks: int = 60):
    print(f"\n{'='*70}\n[{label}] link_id={link_id}")
    try:
        data = client.get_post_tree(link_id)
    except Exception as e:
        print("  获取失败:", e)
        return
    result = data.get("result") or {}
    link = result.get("link") or result
    # text 字段可能是 JSON 字符串
    text_raw = link.get("text")
    print("  title:", (link.get("title") or "")[:40])
    print("  text 原始类型:", type(text_raw).__name__)
    blocks = None
    if isinstance(text_raw, str):
        try:
            blocks = json.loads(text_raw)
        except json.JSONDecodeError:
            print("  text 非JSON,前200字:", text_raw[:200])
    elif isinstance(text_raw, list):
        blocks = text_raw
    if not isinstance(blocks, list):
        print("  无法解析为块数组, keys:", list(link.keys())[:20])
        return
    print(f"  共 {len(blocks)} 个块:")
    n_empty = 0
    n_text = 0
    n_img = 0
    for i, b in enumerate(blocks[:max_blocks]):
        t = b.get("type")
        if t == "text":
            n_text += 1
            txt = b.get("text", "")
            if not txt.strip():
                n_empty += 1
                show = f"(空块! raw={txt!r})"
            else:
                # 标出块内是否有 \n
                nl = " [含\\n]" if "\n" in txt else ""
                show = txt[:50].replace("\n", "⏎") + ("" if len(txt) <= 50 else "…") + nl
            print(f"    {i:>3} text   | {show}")
        elif t == "img":
            n_img += 1
            print(f"    {i:>3} img    | {str(b.get('url'))[:60]}")
        else:
            print(f"    {i:>3} {t!r:8}| {json.dumps(b, ensure_ascii=False)[:60]}")
    if len(blocks) > max_blocks:
        print(f"    … 还有 {len(blocks)-max_blocks} 块")
    print(f"  统计: text={n_text} img={n_img} 空text块={n_empty}")


# 1) 我们自己的帖子
dump_post("194210321", "我们的帖子-当前格式")

# 2) 抓盒友杂谈 feed 里的帖子看别人的排版
print("\n" + "=" * 70 + "\n拉取 盒友杂谈(7214) feeds...")
feeds = client.get_topic_feeds(7214, offset=0, limit=30)
items = ((feeds.get("result") or {}).get("links")
         or (feeds.get("result") or {}).get("feeds") or [])
print(f"拿到 {len(items)} 条")
seen = 0
for it in items:
    link_id = str(it.get("linkid") or it.get("link_id") or "")
    if not link_id:
        # feeds 可能嵌套
        inner = it.get("link") or {}
        link_id = str(inner.get("linkid") or "")
        if not link_id:
            continue
    word_num = it.get("word_num") or (it.get("link") or {}).get("word_num") or 0
    if not word_num:  # 只要文字帖(有正文的才看排版)
        continue
    if seen >= 3:
        break
    dump_post(link_id, f"杂谈帖子 word_num={word_num}")
    seen += 1
