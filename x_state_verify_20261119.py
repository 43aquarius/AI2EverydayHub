#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证重建的X登录状态: 注入auth_token/twid → 开x.com → 检查登录态"""
import json
import time

from playwright.sync_api import sync_playwright

st = json.load(open("/home/z/my-project/secrets/x_state.json"))
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True, proxy={"server": "socks5://127.0.0.1:10820"},
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"])
    ctx = browser.new_context(user_agent=UA, locale="en-US",
                              viewport={"width": 1280, "height": 900})
    ctx.add_cookies(st["cookies"])
    page = ctx.new_page()
    page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(6000)
    url = page.url
    title = page.title()
    logged_in = "login" not in url.lower() and "home" in url.lower()
    handle = ""
    try:
        a = page.locator('a[data-testid="AppTabBar_Profile_Link"]').first
        handle = a.get_attribute("href") or ""
    except Exception:
        pass
    # 补全: 拿到ct0等会话cookie后回写state文件(更完整)
    cookies = ctx.cookies("https://x.com")
    st["cookies"] = cookies
    st["completed"] = time.strftime("%F %T")
    for pth in ["/home/z/.secrets/x_state.json",
                "/home/z/my-project/secrets/x_state.json"]:
        json.dump(st, open(pth, "w"), indent=1)
    print(json.dumps({"logged_in": logged_in, "url": url[:60],
                      "title": title[:40], "handle": handle,
                      "cookies_saved": len(cookies)}, ensure_ascii=False))
    browser.close()
