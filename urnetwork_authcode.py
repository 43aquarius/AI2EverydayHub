#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ur.io: 尝试 Auth code 登录路径"""
import time
from playwright.sync_api import sync_playwright

EMAIL = "URNETWORK_EMAIL@example.com"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True,
        proxy={"server": "socks5://127.0.0.1:10820"},
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"])
    ctx = browser.new_context(user_agent=UA, viewport={"width": 1280, "height": 900}, locale="en-US")
    page = ctx.new_page()
    page.goto("https://ur.io/?auth&next=%2Fapp%2Fproxies", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)
    inp = page.locator('input[placeholder*="email"]').first
    inp.fill(EMAIL)
    page.wait_for_timeout(400)
    try:
        page.locator("button", has_text="Auth code").first.click(timeout=6000)
        print("已点 Auth code")
    except Exception as e:
        print("Auth code 按钮点击失败:", str(e)[:120])
    page.wait_for_timeout(6000)
    for sel in ["[role=dialog]", "form"]:
        try:
            t = page.locator(sel).first.inner_text(timeout=3000)
            print(f"=== {sel} 文本 ===")
            print(t[:800])
            break
        except Exception:
            continue
    for e in page.locator("input").all()[:8]:
        try:
            print("INPUT:", e.get_attribute("type"), "| ph=", e.get_attribute("placeholder"))
        except Exception:
            pass
    for e in page.locator("button").all()[:20]:
        try:
            print("BTN:", (e.inner_text(timeout=800) or "").strip()[:60].replace("\n", "/"))
        except Exception:
            pass
    page.screenshot(path="/home/z/my-project/output_preview/urio_authcode.png")
    browser.close()
