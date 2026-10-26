#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DOM探针: 找正文编辑器/存草稿按钮的真实选择器"""
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
    # 传一张图激活表单
    img = glob.glob("/home/z/my-project/xhs-draft-poster/output/xhs_cover_*.jpg")[0]
    inputs = page.locator("input[type='file']")
    inputs.nth(inputs.count() - 1).set_input_files(img)
    time.sleep(4)

    # 1. 找正文编辑器(带placeholder的可编辑元素)
    editors = page.evaluate("""
    (() => {
      const out = [];
      document.querySelectorAll('[contenteditable="true"]').forEach(el => {
        const ph = el.getAttribute('data-placeholder') || el.textContent.trim().slice(0, 30);
        const cls = el.className;
        // 找父级链的class
        let p = el, chain = [];
        for (let i = 0; i < 4 && p; i++) {
          chain.push(p.tagName + (p.className ? '.' + String(p.className).split(' ').join('.') : ''));
          p = p.parentElement;
        }
        out.push({ph, cls, chain: chain.join(' < ')});
      });
      return out;
    })()""")
    print("== contenteditable 元素 ==")
    for e in editors:
        print(json.dumps(e, ensure_ascii=False)[:220])

    # 2. 找所有按钮
    buttons = page.evaluate("""
    (() => {
      const out = [];
      document.querySelectorAll('button, [class*=btn], [class*=button]').forEach(el => {
        const t = (el.textContent || '').trim().slice(0, 20);
        if (t && out.length < 40) out.push({tag: el.tagName, cls: String(el.className).slice(0, 80), text: t});
      });
      return out;
    })()""")
    print("\\n== 按钮 ==")
    seen = set()
    for b in buttons:
        k = b["text"]
        if k not in seen:
            seen.add(k)
            print(json.dumps(b, ensure_ascii=False)[:180])

    # 3. 标题输入框结构
    titles = page.evaluate("""
    (() => {
      const out = [];
      document.querySelectorAll('input[placeholder*="标题"]').forEach(el => {
        let p = el, chain = [];
        for (let i = 0; i < 4 && p; i++) {
          chain.push(p.tagName + (p.className ? '.' + String(p.className).split(' ').join('.') : ''));
          p = p.parentElement;
        }
        out.push({ph: el.placeholder, chain: chain.join(' < ')});
      });
      return out;
    })()""")
    print("\\n== 标题输入框 ==")
    for t in titles:
        print(json.dumps(t, ensure_ascii=False)[:220])

    c._shot("probe_page")
finally:
    try:
        c.browser.close(); c._pw.stop()
    except Exception:
        pass
    xvfb.terminate()
