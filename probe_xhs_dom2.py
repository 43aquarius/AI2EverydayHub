#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针2: 专找存草稿按钮 + 话题按钮交互流程"""
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

    # 1. 无限制找所有button的完整清单
    all_btns = page.evaluate("""
    (() => {
      const out = [];
      document.querySelectorAll('button').forEach(el => {
        out.push({cls: String(el.className).slice(0, 60),
                  text: (el.textContent || '').trim().slice(0, 24)});
      });
      return out;
    })()""")
    print("== 全部button(共%d个) ==" % len(all_btns))
    for b in all_btns:
        if b["text"]:
            print(json.dumps(b, ensure_ascii=False)[:150])

    # 2. 含"存""暂""草稿"字样的任意元素
    draft_els = page.evaluate("""
    (() => {
      const out = [];
      const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
      while (walk.nextNode()) {
        const el = walk.currentNode;
        const own = Array.from(el.childNodes).filter(n => n.nodeType === 3)
                        .map(n => n.textContent.trim()).join('');
        if (/存草稿|暂存/.test(own)) {
          out.push({tag: el.tagName, cls: String(el.className).slice(0, 70), text: own.slice(0, 20)});
        }
        if (out.length > 10) break;
      }
      return out;
    })()""")
    print("\\n== 含'存草稿/暂存'的元素 ==")
    for d in draft_els:
        print(json.dumps(d, ensure_ascii=False)[:180])

    # 3. 测试话题按钮点击后出现什么
    page.locator("button.topic-btn").click()
    time.sleep(2)
    topic_dom = page.evaluate("""
    (() => {
      // 找新出现的弹层/输入框
      const out = [];
      document.querySelectorAll('input, [contenteditable="true"]').forEach(el => {
        const ph = el.placeholder || el.getAttribute('data-placeholder') || '';
        if (ph) out.push({tag: el.tagName, ph: String(ph).slice(0, 40),
                          cls: String(el.className).slice(0, 50)});
      });
      return out;
    })()""")
    print("\\n== 点话题按钮后新增输入框 ==")
    for t in topic_dom:
        print(json.dumps(t, ensure_ascii=False)[:160])
    c._shot("probe2_topic")
finally:
    try:
        c.browser.close(); c._pw.stop()
    except Exception:
        pass
    xvfb.terminate()
