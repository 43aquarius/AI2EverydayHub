#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""决定性测试: ①老帖有无他人评论 ②公共歌曲评论区: 自己评论→自回复 ③add端点带commentId
④weapi os=pc + 浏览器UA 回复"""
import json
import sys
import time
import uuid as _uuid

sys.path.insert(0, "/home/z/my-project/netease-music-poster")
from config import load_config
from netease_client import NeteaseClient

cfg = load_config()
c = NeteaseClient(cfg["cookie"])
st = c.login_status()
assert st.get("ok")

# ① 老帖(37102224895)评论情况
print("[1] 老帖评论")
cs = c.read_comments("A_EV_2_37102224895_12108131883", limit=20)
print("    total =", cs.get("total"))
for x in (cs.get("comments") or [])[:5]:
    u = x.get("user") or {}
    print(f"    - [{x.get('commentId')}] {u.get('nickname')}: "
          f"{(x.get('content') or '')[:40]} uid={u.get('userId')}")

# ② 公共歌曲评论区测试(言って。 487527980, 用自己评论测试自回复)
SONG_THREAD = "R_SO_4_487527980"
print("\n[2] 歌曲评论区自评论→自回复(R_SO_4线程)")
cm = c.add_comment(SONG_THREAD, "好歌!")
cid = str((cm.get("comment") or {}).get("commentId"))
print("    歌曲评论OK:", cid)
try:
    rp = c._eapi_android("/api/v1/resource/comments/reply", {
        "threadId": SONG_THREAD, "commentId": cid,
        "content": "自回复测试", "forwardEvent": "0"})
    print("    歌曲自回复:", rp.get("code"))
except Exception as e:
    print("    歌曲自回复:", str(e)[:100])

# 找一条他人的热门评论回复(只读, 看真实回复长什么样)
cs2 = c.read_comments(SONG_THREAD, limit=30)
others = [x for x in cs2.get("comments") or []
          if (x.get("user") or {}).get("userId") != st["uid"]]
print(f"    他人在场评论数: {len(others)}")
# ③ add端点带commentId(模拟回复语义)
print("\n[3] add端点+commentId变体(自己歌曲评论)")
try:
    r = c._eapi_android("/api/v1/resource/comments/add", {
        "threadId": SONG_THREAD, "content": "add带commentId测试",
        "commentId": cid, "forwardEvent": "0",
        "resourceType": "0", "expressionPicId": "-1", "bubbleId": "-1"})
    print("    add+commentId:", r.get("code"),
          (r.get("comment") or {}).get("commentId"))
except Exception as e:
    print("    add+commentId:", str(e)[:100])

# ④ weapi + 浏览器UA + os=pc cookie
print("\n[4] weapi浏览器态回复")
try:
    r = c._post_weapi("https://music.163.com/weapi/resource/comments/reply",
                      {"threadId": SONG_THREAD, "commentId": cid,
                       "content": "weapi回复测试",
                       "csrf_token": c._csrf()})
    print("    weapi回复:", r.get("code"), (r.get("message") or "")[:50])
except Exception as e:
    print("    weapi回复:", str(e)[:100])

# 清理: 删自己的歌曲评论
print("\n[清理] 删除歌曲评论", cid)
try:
    r = c._eapi_android("/api/resource/comments/delete", {
        "threadId": SONG_THREAD, "commentId": cid})
    print("    删除:", r.get("code"))
except Exception as e:
    print("    删除失败:", str(e)[:100])
