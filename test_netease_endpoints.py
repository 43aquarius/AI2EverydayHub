#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据端点探针: 每日推荐 / 热歌榜 / 歌曲详情"""
import json
import sys

sys.path.insert(0, "/home/z/my-project/netease-music-poster")
from config import load_config
from netease_client import NeteaseClient

cfg = load_config()
c = NeteaseClient(cfg["cookie"])
print("[登录]", c.login_status())

print("\n=== 每日推荐 ===")
try:
    songs = c.daily_recommend_songs()
    print(f"共 {len(songs)} 首")
    for s in songs[:5]:
        arts = "/".join(a["name"] for a in s.get("ar", []))
        print(f"  {s['id']} | {s['name']} - {arts} | 专辑:{s.get('al',{}).get('name','')} | 热:{s.get('pop',0):.0f}")
    if songs:
        print("首条完整字段:", json.dumps({k: songs[0].get(k) for k in ("id", "name", "ar", "al", "pop", "dt")}, ensure_ascii=False)[:500])
except Exception as e:
    print("每日推荐失败:", e)

print("\n=== 歌曲详情(拿推荐第1首) ===")
try:
    detail = c.song_detail([songs[0]["id"]])
    d = detail[0]
    print(f"  {d['name']} - {'/'.join(a['name'] for a in d['ar'])} | 封面: {d['al'].get('picUrl','')[:60]}")
except Exception as e:
    print("详情失败:", e)

print("\n=== 热歌榜(降级路径) ===")
try:
    tl = c.toplist_tracks(3779629)
    print(f"trackIds {len(tl)} 条: {tl[:3]}")
except Exception as e:
    print("榜单失败:", e)
