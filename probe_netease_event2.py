#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测动态数据结构: 评论threadId / 话题 / json字段"""
import json
import sys
sys.path.insert(0, "/home/z/my-project/netease-music-poster")
from config import load_config
from netease_client import NeteaseClient

cfg = load_config()
c = NeteaseClient(cfg["cookie"])
st = c.login_status()
print("[账号]", st)
events = c.user_events(pagesize=5)
print(f"[动态] 共 {len(events)} 条")
for ev in events[:3]:
    print("=" * 70)
    # 顶层关键字段
    print("id:", ev.get("id"), "| type:", ev.get("type"),
          "| showTime:", ev.get("showTime"), "| actName:", ev.get("actName"))
    # resource 里通常有 threadId / 评论数 / 话题
    res = ev.get("resource") or {}
    print("resource keys:", sorted(res.keys())[:40])
    print("threadId:", res.get("threadId"), "| commentCount:", res.get("commentCount"),
          "| likedCount:", res.get("likedCount"), "| shareCount:", res.get("shareCount"))
    # topic 信息
    for k in ("topic", "topics", "shareTicket", "resourceCreators"):
        if res.get(k):
            print(f"resource.{k}:", json.dumps(res[k], ensure_ascii=False)[:300])
    # json 内容(分享的msg与pics)
    try:
        j = json.loads(ev.get("json") or "{}")
    except Exception:
        j = {}
    print("json keys:", sorted(j.keys())[:40])
    print("json.msg:", (j.get("msg") or "")[:120].replace("\n", " / "))
    print("json.pics:", json.dumps(j.get("pics"), ensure_ascii=False)[:400])
    # 顶层可能的评论入口
    for k in ("resourceInfo", "info", "commentInfo"):
        if ev.get(k):
            v = json.dumps(ev[k], ensure_ascii=False)
            print(f"event.{k}:", v[:300])
print("=" * 70)
# 单独看一条完整结构(第一条, 截断)
ev0 = events[0]
dump = json.dumps(ev0, ensure_ascii=False, indent=1)
print("[第一条完整结构前3500字]")
print(dump[:3500])
