# -*- coding: utf-8 -*-
"""验证今日微博两条帖子: 内容完整性 + 红线检查"""
import json, sys, re

sys.path.insert(0, "/home/z/my-project/weibo-agi-poster")
from weibo_client import WeiboClient

cfg = json.load(open("/home/z/my-project/weibo-agi-poster/config.json", encoding="utf-8"))
wb = WeiboClient(cfg["weibo_cookie"])
uid, nick = wb.whoami()
posts = wb.my_posts(page=1)
print(f"@{nick} 最近 {len(posts)} 条:\n")

for p in posts[:3]:
    txt = p.get("text_raw") or ""
    print(f"◆ [{p.get('created_at')}] id={p.get('id')} mblogid={p.get('mblogid')}")
    print(f"  字数: {len(txt)}  长文: {bool(p.get('isLongText'))}  图: {len(p.get('pic_ids') or [])}张")
    head = txt[:90].replace("\n", " ⏎ ")
    print(f"  开头: {head}")
    tail = txt[-80:].replace("\n", " ⏎ ")
    print(f"  结尾: {tail}")
    # 红线
    bad = [kw for kw in ["ima", "IMA", "知识库", "腾讯研究院"] if kw in txt]
    print(f"  红线: {'❌ ' + str(bad) if bad else '✓ 干净'}")
    # 话题与链接
    print(f"  话题: {re.findall(r'#([^#]{2,14})#', txt)[:5]}")
    print(f"  微信链接数: {txt.count('weixin.qq.com')} (微博版应为0)")
    print()
