#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针4: Playwright text定位器穿透shadow DOM找暂存离开按钮"""
import json, os, subprocess, sys, time
sys.path.insert(0, "/home/z/my-project/xhs-draft-poster")

xvfb = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1440x900x24"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.5)
os.environ["DISPLAY"] = ":99"

from xhs_client import XhsDraftClient
import glob

cfg = json.load(open("/home/z/my-project/xhs-draft-poster/config.json"))
c = XhsDraftClient(cfg["cookie"], headless=False)
try:
    page = c._launch()
    page.goto("https://www.xiaohongshu.com", wait_until="domcontentloaded", timeout=45000)
    time.sleep(2.5)
    page.goto("https://creator.xiaohongshu.com/publish/publish?source=official",
              wait_until="domcontentloaded", timeout=45000)
    time.sleep(3.5)
    c._click_upload_tab()
    img = glob.glob("/home/z/my-project/xhs-draft-poster/output/xhs_cover_*.jpg")[0]
    inputs = page.locator("input[type='file']")
    inputs.nth(inputs.count() - 1).set_input_files(img)
    time.sleep(4)

    # Playwright text定位器(穿透shadow DOM)
    loc = page.locator("text=暂存离开")
    print("text=暂存离开 匹配数:", loc.count())
    # get_by_text 也试
    loc2 = page.get_by_text("暂存离开", exact=True)
    print("get_by_text 匹配数:", loc2.count())
    # span/button 含该文字
    loc3 = page.locator("button:has-text('暂存离开')")
    print("button:has-text 匹配数:", loc3.count())

    # 检查iframe数量
    frames = page.frames
    print("frames数:", len(frames), [f.url[:60] for f in frames])

    if loc.count() > 0:
        # 打印它的标签结构
        info = loc.first.evaluate(
            "el => ({tag: el.tagName, cls: String(el.className), "
            "parent: el.parentElement ? el.parentElement.tagName + '.' + "
            "String(el.parentElement.className).slice(0,50) : ''})")
        print("元素信息:", json.dumps(info, ensure_ascii=False))
        c._shot("probe4_found")
finally:
    try:
        c.browser.close(); c._pw.stop()
    except Exception:
        pass
    xvfb.terminate()
