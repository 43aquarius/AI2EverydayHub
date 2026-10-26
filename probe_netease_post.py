#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测发动态可用端点: 老版 weapi 路径(不加 /weapi 前缀)"""
import json
import sys

sys.path.insert(0, "/home/z/my-project/netease-music-poster")
from config import load_config
from netease_client import NeteaseClient, weapi

cfg = load_config()
c = NeteaseClient(cfg["cookie"])
c.login_status()
print("[账号]", c.nickname, c.uid)

SONG_ID = 487527980  # 言って。 - ヨルシカ


def try_post(url, data, label):
    try:
        form = weapi(data)
        r = c.s.post(url, data=form, headers={
            "Cookie": c.cookie,
            "Content-Type": "application/x-www-form-urlencoded",
        }, timeout=15)
        print(f"[{label}] HTTP {r.status_code} → {r.text[:200]}")
        return r.status_code == 200 and r.text.strip()
    except Exception as e:
        print(f"[{label}] 异常: {e}")
        return None


# 候选1: 老版 share_resource (interface 域, 无 weapi 前缀)
try_post("https://interface.music.163.com/e/event/share/resource",
         {"type": "song", "msg": "测试分享(可删)", "id": SONG_ID},
         "interface/e/event/share/resource")

# 候选2: music.163.com 域老版路径
try_post("https://music.163.com/e/event/share/resource",
         {"type": "song", "msg": "测试分享(可删)", "id": SONG_ID},
         "music/e/event/share/resource")
