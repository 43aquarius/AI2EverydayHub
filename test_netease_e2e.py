#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""端到端实测: 歌曲分享+配图+话题tag → 回读验证 → 评论回复闭环 → 清理
测试动态发完会删除, 不留痕"""
import json
import sys
import time

sys.path.insert(0, "/home/z/my-project/netease-music-poster")
from config import load_config
from netease_client import NeteaseClient
from image_maker import render_card

cfg = load_config()
c = NeteaseClient(cfg["cookie"])
st = c.login_status()
assert st.get("ok"), st
UID = st["uid"]
print("[账号]", st["nickname"], UID)

# ① 搜一首测试歌(言って。 - ヨルシカ)
print("\n[1] 搜索测试歌曲")
body = c._get_api("https://music.163.com/api/search/get/web",
                  {"s": "言って ヨルシカ", "type": 1, "limit": 3, "offset": 0})
songs = (body.get("result") or {}).get("songs") or []
assert songs, f"搜索失败: {body}"
s0 = songs[0]
print("    找到:", s0["name"], "-", "/".join(a["name"] for a in s0["artists"]),
      "id=", s0["id"])
# 换成详情结构(ar/al)
det = c.song_detail([s0["id"]])
song = det[0]
print("    详情: al.picUrl =", (song.get("al") or {}).get("picUrl", "")[:60], "…")

# ② 渲染卡片 + 上传
print("\n[2] 渲染卡片并上传")
copy_ = "测试动态: 这首歌像深夜便利店的灯光, 温柔地亮着。(自动化管线验证, 稍后删除)"
tags = ["每日一歌", "ヨルシカ", "今日份听歌打卡"]
img_path = render_card(song, copy_, tags,
                       out_path="/home/z/my-project/output_preview/netease_e2e_test.jpg")
with open(img_path, "rb") as f:
    img_data = f.read()
pics_entry = c.upload_image(img_data, "daily_song_test.jpg")
pics = [pics_entry]

# ③ 发测试动态: 歌曲卡片 + 配图 + tag
print("\n[3] 发布测试动态(歌曲+配图)")
msg = f"{copy_}\n\n" + " ".join(f"#{t}#" for t in tags)
body = c.share_resource(song["id"], msg, rtype="song", pics=pics)
print("    code:", body.get("code"), "| event id:", body.get("id"),
          "| eventId:", body.get("eventId"))
ev_id = body.get("id") or body.get("eventId")

# ④ 回读验证
print("\n[4] 回读验证")
time.sleep(2)
events = c.user_events(pagesize=3)
ev0 = events[0]
ev_json = json.dumps(ev0, ensure_ascii=False)
j = json.loads(ev0.get("json") or "{}")
print("    最新动态 id:", ev0.get("id"), "| type:", ev0.get("type"))
print("    json.song 存在:", bool(j.get("song")))
print("    json.pics:", json.dumps(j.get("pics"), ensure_ascii=False)[:200])
print("    actId/actName:", ev0.get("actId"), "/", ev0.get("actName"))
# topic 挂载详情(Ed Sheeran 案例里在 extJsonInfo)
ext = ev0.get("extJsonInfo")
if ext:
    try:
        print("    extJsonInfo:", ext[:200] if isinstance(ext, str) else json.dumps(ext, ensure_ascii=False)[:200])
    except Exception:
        pass
thread_id = (ev0.get("info") or {}).get("threadId") or ev0.get("threadId")
print("    threadId:", thread_id)

# ⑤ 评论闭环: 自己评论一条(模拟访客) → bot 回复 → 读取验证
print("\n[5] 评论回复闭环测试")
cm = c.add_comment(thread_id, "好听! 求歌单~")
my_cm_id = (cm.get("comment") or {}).get("commentId")
print("    评论发布: commentId =", my_cm_id)
rp = c.reply_comment(thread_id, my_cm_id,
                     "谢谢喜欢! 这首歌在每日推荐里挖到的, 已单曲循环一整天。")
print("    回复发布: code =", rp.get("code"),
      "| replyId =", (rp.get("comment") or {}).get("commentId"))
# 读取确认
cs = c.read_comments(thread_id, limit=10)
print("    评论回读: total =", cs.get("total"))
for x in cs.get("comments") or []:
    u = x.get("user") or {}
    be = (x.get("beReplied") or [{}])
    print(f"      - [{x.get('commentId')}] {u.get('nickname')}: "
          f"{(x.get('content') or '')[:40]}"
          + (f" ↩ @{(be[0].get('user') or {}).get('nickname')}" if be and be[0] else ""))

# ⑥ 清理: 删动态(评论随动态消失)
print("\n[6] 清理测试动态", ev_id)
try:
    r = c.del_event(ev_id)
    print("    删除:", r.get("code"))
except Exception as e:
    print("    删除失败(手动清理):", e)
print("\n[完成] 全链路测试结束")
