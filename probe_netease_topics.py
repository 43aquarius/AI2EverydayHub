#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测: ①热门话题列表 ②话题详情验证 ③歌手乐迷团信息"""
import json
import sys

sys.path.insert(0, "/home/z/my-project/netease-music-poster")
from config import load_config
from netease_client import NeteaseClient

cfg = load_config()
c = NeteaseClient(cfg["cookie"])
st = c.login_status()
assert st.get("ok")

# ① 热门话题
print("[1] /api/act/hot 热门话题")
try:
    body = c._post_weapi("https://music.163.com/weapi/act/hot",
                         {"limit": 30, "offset": 0})
    print("    code:", body.get("code"))
    acts = body.get("hots") or body.get("data") or body.get("acts") or []
    if not acts:
        print("    返回keys:", list(body.keys()))
        print("    原始:", json.dumps(body, ensure_ascii=False)[:600])
    for a in acts[:30]:
        print(f"    - id={a.get('actId') or a.get('id')} {a.get('title') or a.get('name')} "
              f"participate={a.get('participateCount')}")
except Exception as e:
    print("    失败:", e)

# ② 已知话题验证(ncmm 的三个乐迷团/活动ID + 昨日帖话题)
print("\n[2] /api/act/detail 话题验证")
for actid, note in [(3081059, "欧美音乐(调研实测)"),
                    (13827903, "音乐合伙人的乐迷团(boardId)"),
                    (195425749, "申请音乐合伙人"),
                    (200773579, "音乐合伙人星探计划")]:
    try:
        body = c._post_weapi("https://music.163.com/weapi/act/detail",
                             {"actid": actid})
        d = body.get("act") or body
        print(f"    - {actid} → {d.get('title') or d.get('name')} "
              f"参与={d.get('participateCount')} ({note}) code={body.get('code')}")
    except Exception as e:
        print(f"    - {actid} 失败: {e}")

# ③ 歌手乐迷团(昨日歌曲 言って。 的歌手 ヨルシカ)
print("\n[3] 歌手详情找乐迷团入口(ヨルシカ)")
try:
    # 先拿歌曲详情找歌手id
    songs = c.song_detail([2610114070])  # 言って。的近似id, 失败则跳过
    print(songs[:1] and songs[0].get("name"))
except Exception as e:
    print("    跳过歌曲查询:", e)
# 直接用 artist 接口探测一个知名歌手(周杰伦 id=6452)
try:
    body = c._get_api("https://music.163.com/api/artist/detail",
                      {"id": 6452})
    print("    artist keys:", list((body.get("data") or {}).keys())[:30])
    d = body.get("data") or {}
    artist = d.get("artist") or {}
    print("    artist keys:", list(artist.keys())[:40])
    # 找粉丝团相关字段
    for k in artist.keys():
        if "fan" in k.lower() or "group" in k.lower():
            print(f"    artist.{k}:", json.dumps(artist[k], ensure_ascii=False)[:200])
except Exception as e:
    print("    失败:", e)
