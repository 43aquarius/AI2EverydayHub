#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针5: 填内容+滚到底后再找暂存离开"""
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

    # 填标题+正文
    page.locator("div.d-input input").first.click()
    page.locator("div.d-input input").first.fill("测试草稿标题")
    ed = page.locator("div.tiptap.ProseMirror").first
    ed.click(); time.sleep(0.5)
    ed.type("这是一段测试正文内容, 用来触发草稿按钮的出现。", delay=50)
    time.sleep(2)

    # 滚到底部
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(2)

    for sel in ["text=暂存离开", "text=存草稿", "button:has-text('暂存')"]:
        n = page.locator(sel).count()
        print(f"{sel!r} → {n}")

    # 再截底部图
    c._shot("probe5_bottom_filled")
    # 全页截图看按钮位置
    page.screenshot(path="/tmp/xhs_shots/probe5_full.png", full_page=True)
    print("done")
finally:
    try:
        c.browser.close(); c._pw.stop()
    except Exception:
        pass
    xvfb.terminate()
