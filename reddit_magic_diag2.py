#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reddit magic link 诊断v2:
1. 记录浏览器出口IP(消费前后)
2. 抓 POST /svc/shreddit/account/login/magic_link 的完整请求体+请求头
3. 用同一浏览器上下文手动重放该POST(排除时序问题)
"""
import json
import time

from playwright.sync_api import sync_playwright

MAGIC = ("https://www.reddit.com/magic_link/mlt:<MAGIC_TOKEN>/"
         "t2_<REDDIT_USER_ID>?$deep_link=true&otp=false")
PROXY = ("https://<URNETWORK_TOKEN>"
         ".crisp.bringyour.com:7167")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
OUT = "/home/z/my-project/output_preview"
PROFILE = "/home/z/my-project/secrets/reddit_profile"
CAP = {"post": None, "headers": None}


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def browser_ip(page, label):
    try:
        page.goto("https://api.ipify.org?format=json", timeout=30000)
        ip = json.loads(page.inner_text("body")).get("ip")
        log(f"浏览器出口IP({label}): {ip}")
        return ip
    except Exception as e:
        log(f"IP获取失败({label}): {str(e)[:80]}")
        return None


with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        PROFILE, headless=False,
        proxy={"server": PROXY},
        args=["--disable-blink-features=AutomationControlled",
              "--no-sandbox", "--disable-dev-shm-usage"],
        user_agent=UA, viewport={"width": 1280, "height": 900}, locale="en-US")
    ctx.add_init_script(
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
    page = ctx.pages[0] if ctx.pages else ctx.new_page()

    def on_req(req):
        try:
            if "account/login/magic_link" in req.url and req.method == "POST":
                CAP["post"] = req.post_data
                CAP["headers"] = dict(req.headers)
                CAP["url"] = req.url
                log(f"捕获magic_link POST: {req.url}")
                log(f"POST body: {req.post_data}")
        except Exception:
            pass

    page.on("request", on_req)
    browser_ip(page, "消费前")
    log("打开magic link页 ...")
    page.goto(MAGIC, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(15000)

    if CAP["post"]:
        log("== 完整请求头 ==")
        for k, v in CAP["headers"].items():
            print(f"  {k}: {v[:120]}")
        # 等页面稳定后在同一上下文重放
        log("等待8秒后重放POST ...")
        page.wait_for_timeout(8000)
        try:
            result = page.evaluate(
                """async (body) => {
                    const r = await fetch('/svc/shreddit/account/login/magic_link', {
                        method: 'POST',
                        credentials: 'include',
                        headers: {'content-type': 'application/json'},
                        body: body
                    });
                    let text = '';
                    try { text = await r.text(); } catch(e) {}
                    return {status: r.status, body: text.slice(0, 300)};
                }""", CAP["post"])
            log(f"重放结果: {json.dumps(result, ensure_ascii=False)}")
        except Exception as e:
            log(f"重放失败: {str(e)[:150]}")
        # 重放后再看cookie
        cookies = [c["name"] for c in ctx.cookies("https://www.reddit.com")]
        log(f"重放后cookies: {cookies}")
    else:
        log("未捕获到POST(页面可能没走到消费步骤)")
        cookies = [c["name"] for c in ctx.cookies("https://www.reddit.com")]
        log(f"cookies: {cookies}")
    browser_ip(page, "消费后")
    ctx.close()
