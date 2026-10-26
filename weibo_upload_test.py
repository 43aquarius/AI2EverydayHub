#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""复刻微博图片上传: 验证最小必需参数"""
import hashlib
import json
import subprocess

COOKIE = ("PC_TOKEN=adb6111839; XSRF-TOKEN=Tv-UcOPDSqFFz6hGINq27mjL; "
          "SCF=AmsyKYDV6nkgF-gAcGQCQwA6hHPU4O1RaFSKNmtf2elLhfuzST9J0ck_JgBq27OiyFG4xR7ah-6jXR2qtFEvzpY.; "
          "SUB=_2A25H0dcJDeRhGe9O4lcQ9CnFzzqIHXVkr1bBrDV8PUNbmtAYLVjzkW9NdDQhjB1hLQH0Iv-MqH4KJa_o-qJVc4aU; "
          "SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5iQbVE0-kYCRXXbIE4l_pp5JpX5KzhUgL.Fo.71K-pShM4Shq2dJLoIEBLxK.L1KnLB.qLxK-LB.2L1KeLxK-LBo5L1KBLxKqL1KqLB-qt; "
          "ALF=02_1794978905; "
          "WBPSESS=fYdJAurzczjxFGMLYJKiP0UWeVqo7CL_1paCNFL2ZmhmE224vTw6tNttVDake9xEgqi0cHkJ3VVKQatk_XbCR4OlyzIfrf4gLxmnqxHqTu5oH9qfdm83YoUM5aB0JgvNl-beGtPkCYBM9PK0_p3OOw==")
XSRF = "Tv-UcOPDSqFFz6hGINq27mjL"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
UID = "9095147946"

import time


def upload(path, note=""):
    data = open(path, "rb").read()
    md5 = hashlib.md5(data).hexdigest()
    t = int(time.time() * 1000)
    url = ("https://picupload.weibo.com/interface/upload.php"
           f"?file_source=1&cs={t % 2147483647}&ent=miniblog&appid=339644097"
           f"&uid={UID}&raw_md5={md5}&ori=1&mpos=1"
           f"&nick=%40%E9%98%BF%E5%BA%93%E5%B0%94%E6%96%AF&pri=0"
           f"&request_id={t}&file_size={len(data)}")
    cmd = ["curl", "-s", "--compressed", "-X", "POST", url,
           "-H", f"Cookie: {COOKIE}", "-H", f"User-Agent: {UA}",
           "-H", "Referer: https://weibo.com/",
           "-H", "Content-Type: image/jpeg",
           "--data-binary", f"@{path}",
           "-w", "\n%{http_code}"]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    parts = out.stdout.rsplit("\n", 1)
    print(f"[{note}] HTTP {parts[1].strip()}: {parts[0][:200]}")
    try:
        return json.loads(parts[0])
    except json.JSONDecodeError:
        return None


r = upload("/tmp/test_weibo.jpg", "完整参数复刻")
if r and r.get("ret"):
    print("✅ pid =", r["pic"]["pid"])
