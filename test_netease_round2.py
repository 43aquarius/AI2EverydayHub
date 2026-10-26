#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二轮实测:
① 修正msg格式(单\n+尾随空格) → 验证tag挂载
② note端点混合形态(song+pics) → 验证歌曲卡片+配图能否共存
③ note端点(noresource+pics+activityInfoList乐迷团挂载)
④ reply commentId字符串
全部测试完清理"""
import json
import sys
import time

sys.path.insert(0, "/home/z/my-project/netease-music-poster")
from config import load_config
from netease_client import NeteaseClient

cfg = load_config()
c = NeteaseClient(cfg["cookie"])
st = c.login_status()
assert st.get("ok"), st
print("[账号]", st["nickname"])
SONG_ID = 487527980  # 言って。 - ヨルシカ
det = c.song_detail([SONG_ID])
song = det[0]
print("[歌曲]", song["name"], "-", song["ar"][0]["name"])


def readback(label):
    time.sleep(1.5)
    events = c.user_events(pagesize=2)
    ev0 = events[0]
    j = json.loads(ev0.get("json") or "{}")
    ext = ev0.get("extJsonInfo") or {}
    print(f"    [{label}] id={ev0.get('id')} type={ev0.get('type')} "
          f"actIds={ext.get('actIds')} actName={ev0.get('actName')!r} "
          f"song={'✓' if j.get('song') else '✗'} "
          f"pics={'✓' if j.get('pics') else '✗'}")
    tid = (ev0.get("info") or {}).get("threadId") or ev0.get("threadId")
    return ev0.get("id"), tid, j


# ============ 实验1: 修正msg格式 + reply字符串 ============
print("\n[实验1] 歌曲分享 + 正确tag格式")
msg1 = ("深夜练习曲, 一首温柔到让人想落泪的歌。\n"
        "#每日一歌# #ヨルシカ# #今日份听歌打卡# ")
body = c.share_resource(SONG_ID, msg1, rtype="song")
ev1 = body.get("id")
print("    发布 code:", body.get("code"), "id:", ev1)
ev1_id, tid1, j1 = readback("歌曲分享")

# 评论回复(字符串commentId)
print("    评论回复测试(commentId字符串):")
cm = c.add_comment(tid1, "求这首歌的歌单!")
cm_id = str((cm.get("comment") or {}).get("commentId"))
print("      评论:", cm_id)
try:
    rp = c.reply_comment(tid1, cm_id, "已经收藏进每日循环歌单啦, 安利给你!")
    print("      回复: code =", rp.get("code"),
          "id =", (rp.get("comment") or {}).get("commentId"))
except Exception as e:
    print("      回复失败:", e)
    # 备用路径: /api/resource/comments/reply (Binaryify路径)
    try:
        body = c._eapi_android("/api/resource/comments/reply", {
            "threadId": tid1, "commentId": cm_id,
            "content": "已经收藏进每日循环歌单啦, 安利给你!",
            "forwardEvent": "0"})
        print("      备用路径回复:", body.get("code"), body.get("message") or "")
    except Exception as e2:
        print("      备用路径也失败:", e2)
print("    删除实验1动态:", c.del_event(ev1_id).get("code"))

# ============ 实验2: note端点 song+pics 混合 ============
print("\n[实验2] note端点混合形态(type=song + pics)")
with open("/home/z/my-project/output_preview/netease_e2e_test.jpg", "rb") as f:
    img = f.read()
pics_entry = c.upload_image(img, "note_test.jpg")
import uuid as _uuid
uuid_str = _uuid.uuid4().hex
try:
    body = c._eapi_android("/api/note/share/friends/resource", {
        "msg": "note端点混合测试\n#每日一歌# ",
        "type": "song", "id": SONG_ID,
        "uuid": uuid_str, "pics": json.dumps([pics_entry]),
        "addComment": "false",
    })
    print("    发布 code:", body.get("code"), "msg:", body.get("message") or "",
          "id:", body.get("id"))
    if body.get("code") == 200:
        ev2_id, tid2, j2 = readback("note混合")
        print("    删除实验2动态:", c.del_event(ev2_id).get("code"))
except Exception as e:
    print("    失败:", e)

# ============ 实验3: note端点 noresource+pics+activityInfoList ============
print("\n[实验3] note端点图文+乐迷团挂载")
ACT_LIST = json.dumps([
    {"id": "13827903", "type": 3, "subType": 11,
     "name": "音乐合伙人的乐迷团", "selected": True, "canChange": True},
    {"id": "195425749", "type": 2, "subType": 0,
     "name": "申请音乐合伙人", "selected": True, "canChange": True},
], ensure_ascii=False)
try:
    body = c._eapi_android("/api/note/share/friends/resource", {
        "msg": "今日份的循环曲目, 分享给同样需要它的你。\n#每日一歌# #今日份听歌打卡# ",
        "type": "noresource",
        "uuid": uuid_str,
        "pics": json.dumps([pics_entry]),
        "addComment": "false",
        "privacySetting": "0",
        "socialSpaceVisible": 1,
        "activityInfoList": ACT_LIST,
    })
    print("    发布 code:", body.get("code"), "msg:", body.get("message") or "",
          "id:", body.get("id"))
    if body.get("code") == 200:
        ev3_id, tid3, j3 = readback("note图文")
        # 检查乐迷团挂载
        evs = c.user_events(pagesize=1)
        ext3 = (evs[0].get("extJsonInfo") or {})
        print("    extJsonInfo.actIds:", ext3.get("actIds"),
              "circleId:", ext3.get("circleId"))
        print("    删除实验3动态:", c.del_event(ev3_id).get("code"))
except Exception as e:
    print("    失败:", e)

print("\n[完成]")
