#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""评论回复 xeapi 终验(受控测试, 2026-10-22)

流程:
1. 在今日帖下发自评(自然内容, eapi add)
2. 用 xeapi reply 回复该评论
3. 回读评论区确认两条都落地
内容设计为博主自我互动, 可长期保留不影响观感。
"""
import sys, json
sys.path.insert(0, "/home/z/my-project/netease-music-poster")
from netease_client import NeteaseClient
from config import load_config

EVENT_ID = 38006241770
UID = 12108131883
THREAD = f"A_EV_2_{EVENT_ID}_{UID}"

c = NeteaseClient(load_config()["cookie"])

# 1) 博主自评(自然内容)
r1 = c.add_comment(THREAD, "评论区聊聊，你最近单曲循环的是哪一首？")
print("[自评] code:", r1.get("code"))
cid = (r1.get("comment") or {}).get("commentId") or r1.get("commentId")
print("[自评] commentId:", cid)

if not cid:
    print("[失败] 未拿到 commentId, 响应:", json.dumps(r1, ensure_ascii=False)[:300])
    sys.exit(1)

# 2) xeapi 回复该评论(终验目标)
try:
    r2 = c.reply_comment(THREAD, cid, "我先来，今天这首《言って。》已经循环第八遍了。")
    print("[xeapi回复] ✅ code:", r2.get("code"))
except Exception as e:
    print("[xeapi回复] ❌:", str(e)[:300])

# 3) 回读评论区
body = c.read_comments(THREAD, limit=10)
comments = body.get("comments") or []
print(f"[回读] 评论区共 {len(comments)} 条:")
for cm in comments:
    print(f"  - id={cm.get('commentId')} user={cm.get('user',{}).get('nickname')} "
          f"content={cm.get('content')!r}")
