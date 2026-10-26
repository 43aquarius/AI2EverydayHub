#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证草稿箱: 打开笔记管理-草稿列表确认"""
import json, os, subprocess, sys, time
sys.path.insert(0, "/home/z/my-project/xhs-draft-poster")

xvfb = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1440x900x24"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.5)
os.environ["DISPLAY"] = ":99"

from xhs_client import XhsDraftClient

cfg = json.load(open("/home/z/my-project/xhs-draft-poster/config.json"))
c = XhsDraftClient(cfg["cookie"], headless=False)
try:
    page = c._launch()
    page.goto("https://www.xiaohongshu.com", wait_until="domcontentloaded", timeout=45000)
    time.sleep(2)
    # 笔记管理页
    page.goto("https://creator.xiaohongshu.com/publish/manage?",
              wait_until="domcontentloaded", timeout=45000)
    time.sleep(3.5)
    c._shot("manage_page1")
    # 找草稿tab
    tabs = page.evaluate("""
    (() => {
      const out = [];
      document.querySelectorAll('div, span, a').forEach(el => {
        const own = Array.from(el.childNodes).filter(n => n.nodeType === 3)
                        .map(n => n.textContent.trim()).join('');
        if (/草稿/.test(own) && own.length < 12) out.push({tag: el.tagName, text: own});
      });
      return out.slice(0, 8);
    })()""")
    print("草稿tab:", json.dumps(tabs, ensure_ascii=False))
    for t in tabs:
        try:
            page.locator(f"{t['tag'].lower()}:has-text('{t['text']}')").first.click()
            time.sleep(2.5)
            break
        except Exception:
            continue
    c._shot("manage_drafts")
    # 读草稿列表
    drafts = page.evaluate("""
    (() => {
      const out = [];
      document.querySelectorAll('[class*=draft] , [class*=note-item], [class*=card]').forEach(el => {
        const t = (el.textContent || '').trim().replace(/\\s+/g, ' ');
        if (t && t.length > 5 && t.length < 120) out.push(t.slice(0, 100));
      });
      return [...new Set(out)].slice(0, 10);
    })()""")
    print("草稿列表:")
    for d in drafts:
        print("  -", d)
finally:
    try:
        c.browser.close(); c._pw.stop()
    except Exception:
        pass
    xvfb.terminate()
