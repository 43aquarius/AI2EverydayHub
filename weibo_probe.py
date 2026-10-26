#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""微博 Web API 探测: 登录态验证"""
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


def curl(method, url, extra=None, data=None):
    cmd = ["curl", "-s", "--compressed", "-X", method, url,
           "-H", f"Cookie: {COOKIE}",
           "-H", f"X-Xsrf-Token: {XSRF}",
           "-H", f"User-Agent: {UA}",
           "-H", "Accept: application/json, text/plain, */*",
           "-H", "Referer: https://weibo.com/",
           "-w", "\n%{http_code}"]
    if extra:
        cmd += extra
    if data is not None:
        cmd += ["-H", "Content-Type: application/json;charset=UTF-8",
                "--data", data]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    parts = out.stdout.rsplit("\n", 1)
    code = parts[1].strip() if len(parts) > 1 else "?"
    body = parts[0]
    try:
        return code, json.loads(body)
    except json.JSONDecodeError:
        return code, body[:500]


# ② 发帖接口测试: POST /ajax/statuses/update
import time
test_content = f"接口连通性测试 {int(time.time())}，稍后删除"
code, r = curl("POST", "https://weibo.com/ajax/statuses/update",
               data=json.dumps({"content": test_content}, ensure_ascii=False))
print("\n② statuses/update:", code)
print("   ", json.dumps(r, ensure_ascii=False)[:400])
post_id = None
if isinstance(r, dict) and r.get("ok"):
    post_id = r["data"].get("id") or r["data"].get("idstr") or r["data"].get("mid")
    print("   ✅ 发帖成功! post_id =", post_id)

# ③ 立即删除测试帖
if post_id:
    code, r = curl("POST", f"https://weibo.com/ajax/statuses/destroy?id={post_id}")
    print("③ destroy:", code, json.dumps(r, ensure_ascii=False)[:200])
