#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reddit magic link 全量诊断: 抓完整请求链(含document/重定向/表单提交)
搞清楚: JS挑战是否通过 → magic link token 是否被接受
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
LOG = []


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


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
            if "reddit.com" in req.url:
                LOG.append(f"--> {req.method} {req.resource_type} {req.url}")
        except Exception:
            pass

    def on_resp(resp):
        try:
            if "reddit.com" in resp.url:
                body = ""
                rt = resp.request.resource_type
                if rt in ("document", "xhr", "fetch"):
                    try:
                        body = resp.text()[:150].replace("\n", " ")
                    except Exception:
                        pass
                LOG.append(f"<-- {resp.status} {rt} "
                           f"{resp.url[:160]} | {body[:100]}")
        except Exception:
            pass

    page.on("request", on_req)
    page.on("response", on_resp)
    # 控制台错误也抓
    page.on("console", lambda m: LOG.append(f"[console.{m.type}] {m.text[:150]}")
            if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: LOG.append(f"[pageerror] {str(e)[:200]}"))

    log("打开魔法链接(全量捕获) ...")
    try:
        page.goto(MAGIC, wait_until="domcontentloaded", timeout=90000)
    except Exception as e:
        log(f"goto异常: {str(e)[:150]}")

    t0 = time.time()
    while time.time() - t0 < 75:
        page.wait_for_timeout(5000)
        cookies = [c["name"] for c in ctx.cookies("https://www.reddit.com")]
        if "reddit_session" in cookies:
            log("★ reddit_session 出现! 登录成功")
            break
        log(f"URL: {page.url}")
        log(f"cookies: {cookies}")

    page.screenshot(path=f"{OUT}/rd_diag_final.png")
    try:
        body = page.inner_text("body")[:400]
    except Exception:
        body = ""
    log(f"页面文本: {body[:300]}")
    print("\n===== 完整网络日志 =====")
    for line in LOG:
        print(line)
    ctx.close()
