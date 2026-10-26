#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试: ①评论读取(昨日动态) ②图片上传三步链路"""
import io
import sys
import json

sys.path.insert(0, "/home/z/my-project/netease-music-poster")
from config import load_config
from netease_client import NeteaseClient

cfg = load_config()
c = NeteaseClient(cfg["cookie"])
st = c.login_status()
print("[账号]", st)
assert st.get("ok")

# ---------- ① 评论读取 ----------
THREAD = "A_EV_2_38005566369_12108131883"  # 昨日《言って。》动态
print("\n[1] 评论读取:", THREAD)
try:
    body = c.read_comments(THREAD, limit=20)
    print("    code:", body.get("code"), "| total:", body.get("total"),
          "| 最新评论数:", len(body.get("comments") or []))
    for cm in (body.get("comments") or [])[:5]:
        u = cm.get("user") or {}
        print(f"    - [{cm.get('commentId')}] {u.get('nickname')}: "
              f"{(cm.get('content') or '')[:50]}")
except Exception as e:
    print("    失败:", e)

# ---------- ② 图片上传三步链路 ----------
print("\n[2] 图片上传链路测试")
# 生成一张小测试图(纯色 JPEG 400x400)
try:
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (400, 400), (200, 30, 30))
    d = ImageDraw.Draw(img)
    d.text((20, 20), "NetEase Upload Test", fill=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    data = buf.getvalue()
    print(f"    测试图生成: {len(data)} bytes")
except ImportError:
    # 无 PIL 则用最小合法 JPEG(1x1 红点)
    data = bytes.fromhex(
        "ffd8ffe000104a46494600010100000100010000ffdb00430003020203020203030303"
        "0403030405080505080a0606090a0d090b0c0c0c0c0c0d0e0f0e0f1011121311121414"
        "1517151617191819191a1b1d1c1d1f1e1f1f1f201f21232223202425252626272826"
        "2727272829282929292a2a2b2d2c2b2e2f2e30323130333235343537353737383838"
        "38393a3a3a3a3b3b3b3b3b3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c"
        "3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c"
        "ffc00011080001000103012200021101031101ffc4001f0000010501010101010100"
        "000000000000000102030405060708090a0bffc400b5100002010303020403050504"
        "040000017d01020300041105122131410613516107227114328191a1082342b1c115"
        "52d1f02433627282090a161718191a25262728292a3435363738393a434445464748"
        "494a535455565758595a636465666768696a737475767778797a838485868788898a"
        "92939495969798999aa2a3a4a5a6a7a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7c8"
        "c9cad2d3d4d5d6d7d8d9dae1e2e3e4e5e6e7e8e9eaf1f2f3f4f5f6f7f8f9faffda00"
        "08010100003f00fbfa28a2803ffd9")
    print(f"    测试图(最小JPEG): {len(data)} bytes")

try:
    entry = c.upload_image(data, "test_upload_probe.jpg")
    print("    ✅ 上传链路成功")
    print("    pics 条目:", json.dumps(entry, ensure_ascii=False))
except Exception as e:
    print("    ❌ 上传失败:", e)
    import traceback
    traceback.print_exc()
