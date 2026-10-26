#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小红书登录态冒烟测试: xvfb有头模式打开创作者中心, 截图判断"""
import json, os, subprocess, sys, time
sys.path.insert(0, "/home/z/my-project/xhs-draft-poster")

cookie = json.load(open("/home/z/my-project/xhs-draft-poster/config.json"))["cookie"]

# 启动Xvfb虚拟显示
xvfb = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1440x900x24"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.5)
os.environ["DISPLAY"] = ":99"

from xhs_client import XhsDraftClient
c = XhsDraftClient(cookie, headless=False)
try:
    ok = c.check_login()
    print("登录态:", "✓ 有效" if ok else "✗ 失效(出现二维码)")
    print("截图: /tmp/xhs_shots/01_home.png")
finally:
    try:
        c.browser.close(); c._pw.stop()
    except Exception:
        pass
    xvfb.terminate()
