#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回复接口变体矩阵测试: 排除法定位404根因"""
import json
import sys
import time
import uuid as _uuid

sys.path.insert(0, "/home/z/my-project/netease-music-poster")
from config import load_config
from netease_client import NeteaseClient, eapi

cfg = load_config()
c = NeteaseClient(cfg["cookie"])
st = c.login_status()
assert st.get("ok")
SONG_ID = 487527980

# 发一条测试动态
UUID = _uuid.uuid4().hex
body = c._eapi_android("/api/share/friends/resource", {
    "type": "song", "id": SONG_ID,
    "msg": "回复接口调试帖, 稍后删。", "uuid": UUID})
ev_id = body.get("id")
assert ev_id, body
time.sleep(1)
events = c.user_events(pagesize=2)
assert events[0].get("id") == ev_id, "回读不一致"
tid = (events[0].get("info") or {}).get("threadId")
print(f"[测试帖] id={ev_id} threadId={tid}")

results = []

def try_reply(label, fn):
    cm = c.add_comment(tid, f"矩阵测试{label}")
    cid = str((cm.get("comment") or {}).get("commentId"))
    try:
        r = fn(cid)
        code = r.get("code")
        results.append((label, code, r.get("message") or r.get("msg") or ""))
        print(f"  [{label}] code={code} {(r.get('message') or '')[:40]}"
              + (f" replyId={(r.get('comment') or {}).get('commentId')}" if code == 200 else ""))
    except Exception as e:
        results.append((label, None, str(e)[:80]))
        print(f"  [{label}] 异常: {str(e)[:90]}")
    return cid

def eapi_raw(uri, data, appver="9.1.65", os_name="android", add_header=True):
    data = dict(data)
    if add_header:
        data["header"] = {"os": os_name, "appver": appver,
                          "channel": "10005124",
                          "requestId": _uuid.uuid4().hex}
    form = eapi(uri, data)
    cookie = "; ".join(p for p in c.cookie.split("; ")
                       if not p.startswith("os="))
    cookie += (f"; os={'Android' if os_name == 'android' else os_name}"
               f"; appver={appver}; osver=16; buildver={int(time.time())}"
               f"; deviceId={c.DEVICE_ID}")
    if appver == "9.3.40":
        cookie += "; resolution=1920x1080"
    r = c.s.post(f"https://music.163.com/eapi/{uri[5:]}", data=form,
                 headers={"Cookie": cookie,
                          "Content-Type": "application/x-www-form-urlencoded",
                          "User-Agent": c.ANDROID_UA}, timeout=30)
    return r.json()

print("\n[矩阵] 每项: 新评论→变体回复→记录")
# V1: 标准eapi(当前实现, 基线)
try_reply("V1基线", lambda cid: c._eapi_android(
    "/api/v1/resource/comments/reply",
    {"threadId": tid, "commentId": cid, "content": "回复V1",
     "forwardEvent": "0"}))
# V2: appver 9.3.40 + os=Android大写
try_reply("V2新版伪装", lambda cid: eapi_raw(
    "/api/v1/resource/comments/reply",
    {"forwardEvent": "0", "threadId": tid, "commentId": cid,
     "content": "回复V2"}, appver="9.3.40"))
# V3: + resourceType '0'
try_reply("V3加resourceType", lambda cid: eapi_raw(
    "/api/v1/resource/comments/reply",
    {"threadId": tid, "commentId": cid, "content": "回复V3",
     "resourceType": "0", "forwardEvent": "0"}, appver="9.3.40"))
# V4: 无header字段body(Go版原样)
try_reply("V4无header", lambda cid: eapi_raw(
    "/api/v1/resource/comments/reply",
    {"forwardEvent": "0", "threadId": tid, "commentId": cid,
     "content": "回复V4"}, appver="9.3.40", add_header=False))
# V5: weapi os=pc 老路径 /api/resource/comments/reply
try_reply("V5weapi老路径", lambda cid: c._post_weapi(
    "https://music.163.com/weapi/resource/comments/reply",
    {"threadId": tid, "commentId": cid, "content": "回复V5",
     "csrf_token": c._csrf()}))

print("\n[汇总]")
for label, code, msg in results:
    print(f"  {label}: {code} {msg[:50]}")
print("\n[清理] 删除测试动态:", c.del_event(ev_id).get("code"))
