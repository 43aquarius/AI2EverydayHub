#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三轮: ①share端点(song)+activityInfoList ②weapi评论回复 ③note端点interface3
安全规约: 删除仅用发布响应ID, 且回读ID一致才删"""
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
SONG_ID = 487527980  # 言って。- ヨルシカ

UUID = _uuid.uuid4().hex
ACT_LIST = json.dumps([
    # ZTMY乐迷团(已加入, 老帖同款挂载)
    {"id": "301686", "type": 3, "subType": 11,
     "name": "ずっと真夜中でいいのに。的乐迷团"},
    # 文本话题(显式ID挂载, 免文本解析)
    {"id": "151944318", "type": 2, "subType": 0, "name": "今日份听歌打卡"},
], ensure_ascii=False)

def dump_event(ev, label):
    j = json.loads(ev.get("json") or "{}")
    ext = ev.get("extJsonInfo") or {}
    print(f"    [{label}] id={ev.get('id')} type={ev.get('type')} "
          f"actIds={ext.get('actIds')} actName={ev.get('actName')!r} "
          f"song={'✓' if j.get('song') else '✗'} "
          f"pics={'✓' if j.get('pics') else '✗'}")
    acts = ext.get("activityInfos")
    if acts:
        print("    activityInfos:", [a.get("name") for a in acts])
    return ev.get("id")

# ============ 实验4: share端点 song + activityInfoList ============
print("[实验4] share端点(type=song) + activityInfoList")
body = c._eapi_android("/api/share/friends/resource", {
    "type": "song", "id": SONG_ID,
    "msg": "自动化管线验证帖, 马上删。\n#今日份听歌打卡# ",
    "uuid": UUID,
    "activityInfoList": ACT_LIST,
    "addComment": "false",
})
print("    发布响应(前400字):", json.dumps(body, ensure_ascii=False)[:400])
ev4 = body.get("id") or (body.get("event") or {}).get("id")
ev4_resp_acts = ((body.get("event") or {}).get("extJsonInfo") or {}).get("actIds")
print("    响应内actIds:", ev4_resp_acts, "| 响应actName:",
          (body.get("event") or {}).get("actName"))
if ev4:
    time.sleep(1.5)
    events = c.user_events(pagesize=2)
    if events and events[0].get("id") == ev4:
        dump_event(events[0], "回读")
        # 评论回复测试(weapi os=pc)
        tid = (events[0].get("info") or {}).get("threadId")
        print("    [回复测试-weapi] threadId:", tid)
        cm = c.add_comment(tid, "测试评论~")
        cm_id = str((cm.get("comment") or {}).get("commentId"))
        print("      评论OK:", cm_id)
        try:
            body2 = c._post_weapi(
                "https://music.163.com/weapi/resource/comments/reply",
                {"threadId": tid, "commentId": cm_id,
                 "content": "weapi回复测试!", "csrf_token": c._csrf()})
            print("      weapi回复:", json.dumps(body2, ensure_ascii=False)[:200])
        except Exception as e:
            print("      weapi回复异常:", str(e)[:150])
        # eapi再试一次(完整参数对齐Go版)
        try:
            body3 = c._eapi_android("/api/v1/resource/comments/reply", {
                "threadId": tid, "commentId": cm_id,
                "content": "eapi回复测试!", "forwardEvent": "0"})
            print("      eapi回复:", json.dumps(body3, ensure_ascii=False)[:200])
        except Exception as e:
            print("      eapi回复异常:", str(e)[:150])
        print("    删除实验4:", c.del_event(ev4).get("code"))
    else:
        print("    ⚠️ 回读ID不一致, 跳过删除! 最新=",
              events[0].get("id") if events else None, "期望=", ev4)

# ============ 实验5: note端点 interface3 + noresource + pics + activityInfoList ============
print("\n[实验5] note端点@interface3 图文+挂载")
with open("/home/z/my-project/output_preview/netease_e2e_test.jpg", "rb") as f:
    img = f.read()
try:
    pic = c.upload_image(img, "note3_test.jpg")
except Exception as e:
    print("    上传失败(复用实验2结果):", e)
    pic = None
if pic:
    import requests as _rq
    # 手动发 interface3 (eapi android 同参数)
    from netease_client import eapi
    data = {
        "msg": "自动化管线验证帖(图文), 马上删。\n#今日份听歌打卡# ",
        "type": "noresource", "uuid": UUID,
        "pics": json.dumps([pic], ensure_ascii=False, separators=(",", ":")),
        "addComment": "false", "privacySetting": "0",
        "socialSpaceVisible": 1, "activityInfoList": ACT_LIST,
        "header": {"os": "android", "appver": "9.1.65",
                   "channel": "10005124",
                   "requestId": _uuid.uuid4().hex},
    }
    form = eapi("/api/note/share/friends/resource", data)
    cookie = c.cookie.replace("os=pc", "os=android")
    cookie += f"; appver=9.1.65; osver=16; buildver={int(time.time())}; deviceId={c.DEVICE_ID}"
    r = c.s.post("https://interface3.music.163.com/eapi/note/share/friends/resource",
                 data=form, headers={
                     "Cookie": cookie,
                     "Content-Type": "application/x-www-form-urlencoded",
                     "User-Agent": c.ANDROID_UA}, timeout=30)
    body = r.json()
    print("    发布响应(前500字):", json.dumps(body, ensure_ascii=False)[:500])
    ev5 = body.get("id") or (body.get("event") or {}).get("id")
    if body.get("code") == 200 and ev5:
        time.sleep(1.5)
        events = c.user_events(pagesize=2)
        if events and events[0].get("id") == ev5:
            dump_event(events[0], "回读")
            print("    删除实验5:", c.del_event(ev5).get("code"))
        else:
            print("    ⚠️ 回读ID不一致:", events[0].get("id") if events else None, "vs", ev5)

print("\n[完成]")
