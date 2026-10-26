#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针3: 更多菜单 + 离开页面拦截 + 底部栏"""
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
    # 填点内容(有内容才可能有草稿概念)
    page.locator("div.d-input input").first.fill("测试草稿标题")
    ed = page.locator("div.tiptap.ProseMirror").first
    ed.click(); time.sleep(0.5)
    ed.type("这是一段测试正文内容。", delay=60)
    time.sleep(2)

    # 1. 点「更多」看菜单
    try:
        page.locator("button.more").click()
        time.sleep(2)
        menu = page.evaluate("""
        (() => {
          const out = [];
          document.querySelectorAll('div, li, span').forEach(el => {
            const own = Array.from(el.childNodes).filter(n => n.nodeType === 3)
                            .map(n => n.textContent.trim()).join('');
            if (own && own.length < 20 && /存|草稿|定时|保存/.test(own))
              out.push({tag: el.tagName, cls: String(el.className).slice(0, 50), text: own});
          });
          return out.slice(0, 15);
        })()""")
        print("== 更多菜单含'存/草稿'项 ==")
        for m in menu:
            print(json.dumps(m, ensure_ascii=False)[:150])
        c._shot("probe3_more_menu")
        page.keyboard.press("Escape")
    except Exception as e:
        print("更多菜单失败:", str(e)[:80])

    # 2. 页面底部完整截图(滚动到底)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(1)
    c._shot("probe3_bottom")

    # 3. 尝试离开页面(点创作者中心logo/首页链接) → 看是否弹拦截窗
    try:
        # 先监听dialog
        dialogs = []
        page.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))
        # 找顶部的首页链接
        page.evaluate("""
        (() => {
          const a = document.querySelector('a[href*="home"], a[href*="/new/home"]');
          if (a) { a.click(); return true; }
          return false;
        })()""")
        time.sleep(3)
        print("\\n== 离开页面后 ==")
        print("browser dialog:", dialogs)
        # 查看是否出现自定义弹窗(含存草稿/暂存)
        modal = page.evaluate("""
        (() => {
          const out = [];
          document.querySelectorAll('div').forEach(el => {
            const own = (el.textContent || '').trim();
            if (/暂存|存草稿/.test(own) && own.length < 120 && el.children.length < 6)
              out.push({cls: String(el.className).slice(0, 60), text: own.slice(0, 60)});
          });
          return out.slice(0, 8);
        })()""")
        print("自定义弹窗:", json.dumps(modal, ensure_ascii=False)[:400])
        c._shot("probe3_leave_modal")
        print("当前URL:", page.url)
    except Exception as e:
        print("离开测试失败:", str(e)[:100])
finally:
    try:
        c.browser.close(); c._pw.stop()
    except Exception:
        pass
    xvfb.terminate()
