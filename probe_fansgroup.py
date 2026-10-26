#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测: 歌手乐迷团boardId获取路径 + weapi评论回复 + note端点全响应dump"""
import json
import sys
import time

sys.path.insert(0, "/home/z/my-project/netease-music-poster")
from config import load_config
from netease_client import NeteaseClient

cfg = load_config()
c = NeteaseClient(cfg["cookie"])
st = c.login_status()
assert st.get("ok")

SONG_ID = 487527980  # 言って。
det = c.song_detail([SONG_ID])
song = det[0]
AR_ID = song["ar"][0]["id"]
AR_NAME = song["ar"][0]["name"]
print(f"[歌曲] {song['name']} - {AR_NAME} (artistId={AR_ID})")

# ① 老帖乐迷团groupId验证(ずとまし, groupId=1567049848697880638 → boardId=301686?)
print("\n[1] 验证fansgroup详情接口(已知ずとましgroupId)")
try:
    body = c._eapi_android("/api/social/fansgroup/bff/detail/get",
                           {"groupId": "1567049848697880638"})
    info = ((body.get("data") or {}).get("fansGroupInfo") or {})
    print("    code:", body.get("code"),
          "| name:", info.get("fansGroupName"),
          "| boardId:", info.get("boardId"),
          "| artistId:", info.get("headId"))
except Exception as e:
    print("    失败:", e)

# ② 按歌手id查乐迷团: 候选端点探测
print("\n[2] 按artistId找乐迷团(ヨルシカ id=%s)" % AR_ID)
candidates = [
    ("eapi", "/api/social/fansgroup/artist/get", {"artistId": AR_ID}),
    ("eapi", "/api/social/fansgroup/bff/detail/get", {"artistId": AR_ID}),
    ("eapi", "/api/fansgroup/detail/get", {"artistId": AR_ID}),
    ("api",  "/api/social/fansgroup/bff/detail/get", {"artistId": AR_ID}),
]
for kind, uri, params in candidates:
    try:
        if kind == "eapi":
            body = c._eapi_android(uri, params)
        else:
            body = c._get_api(f"https://music.163.com{uri}", params)
        s = json.dumps(body, ensure_ascii=False)
        print(f"    [{uri}] code={body.get('code')} → {s[:250]}")
        if body.get("code") == 200 and ("fansGroup" in s or "groupId" in s):
            print("    ^^^^ 命中!")
    except Exception as e:
        print(f"    [{uri}] 异常: {str(e)[:100]}")

# ③ 歌手详情里找乐迷团字段(明文api多种参数)
print("\n[3] 歌手详情接口找乐迷团字段")
try:
    body = c._get_api(f"https://music.163.com/api/v1/artist/{AR_ID}", {})
    s = json.dumps(body, ensure_ascii=False)
    print("    v1 code:", body.get("code"), "|", s[:200])
    if "fansGroup" in s or "groupId" in s.lower():
        print("    ^^^^ 命中!")
except Exception as e:
    print("    v1 异常:", str(e)[:100])
try:
    body = c._post_weapi("https://music.163.com/weapi/artist/detail",
                         {"id": AR_ID, "top": 0})
    s = json.dumps(body, ensure_ascii=False)
    idx = s.find("ansgroup")
    print("    weapi code:", body.get("code"),
          "| fansgroup片段:", s[max(0, idx-40):idx+260] if idx > 0 else "无")
except Exception as e:
    print("    weapi 异常:", str(e)[:100])
