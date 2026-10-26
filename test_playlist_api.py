#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""歌单API链路受控验证(一轮: 创建→封面→加歌→回读→删除)

⚠ 控制频率防风控: 只跑一轮, 操作间 sleep
"""
import sys, time, json
sys.path.insert(0, "/home/z/my-project/netease-music-poster")
from netease_client import NeteaseClient
from config import load_config

c = NeteaseClient(load_config()["cookie"])
st = c.login_status()
print("[登录]", st.get("nickname"), st.get("uid"))

# 1. 创建测试歌单(隐私, 降低风控可见性)
name = "测试歌单_请忽略_" + str(int(time.time()))[-4:]
pid = c.create_playlist(name, privacy=10)
print("[创建] pid =", pid)
time.sleep(3)

# 2. 加2首歌(今日推荐里挑)
songs = c.daily_recommend_songs()
if not songs:
    songs = [{"id": 487527980, "name": "言って。"}]
ids = [s["id"] for s in songs[:2]]
r = c.add_playlist_tracks(pid, ids)
print("[加歌] code =", r.get("code"), "| ids =", ids)
time.sleep(3)

# 3. 改简介
r = c.update_playlist_desc(pid, "自动化测试歌单, 稍后删除。")
print("[简介] code =", r.get("code"))
time.sleep(3)

# 4. 回读验证
pls = c.user_playlists()
mine = next((p for p in pls if p.get("id") == pid), None)
if mine:
    print(f"[回读] ✓ 名称={mine.get('name')} 曲目数={mine.get('trackCount')} "
          f"隐私={mine.get('privacy')}")
else:
    print("[回读] ✗ 未找到")
time.sleep(3)

# 5. 封面更新(用现有卡片图测试, 300x300裁切)
try:
    from PIL import Image
    img = Image.open("/home/z/my-project/netease-music-poster/examples/daily_song_card.jpg") \
        if __import__("os").path.exists("/home/z/my-project/netease-music-poster/examples/daily_song_card.jpg") else None
except Exception:
    img = None
if img:
    img = img.convert("RGB")
    w, h = img.size
    side = min(w, h)
    img = img.crop(((w-side)//2, (h-side)//2, (w+side)//2, (h+side)//2)).resize((640, 640))
    img.save("/tmp/test_pl_cover.jpg", quality=88)
    r = c.update_playlist_cover(pid, "/tmp/test_pl_cover.jpg")
    print("[封面] code =", r.get("code"))
else:
    print("[封面] 无测试图, 跳过")
time.sleep(3)

# 6. 删除测试歌单(清理)
r = c.delete_playlist(pid)
print("[删除] code =", r.get("code"))
print("=== 验证完成 ===")
