#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""触发 Reddit 邮件一次性登录链接 (免密码路径)
复用持久profile(JS挑战cookie) + 有头模式
点击 "Email me a one-time link" → 链接发到 REDDIT_EMAIL@example.com
"""
import json
import time

from playwright.sync_api import sync_playwright

EMAIL = "REDDIT_EMAIL@example.com"
# urnetwork 住宅HTTPS出口, 免鉴权 (沙盒回收后 socks10820 不在, 直接硬编码)
PROXY = ("https://<URNETWORK_TOKEN>"
         ".crisp.bringyour.com:7167")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
OUT = "/home/z/my-project/output_preview"
PROFILE = "/home/z/my-project/secrets/reddit_profile"
NET = []


def get_proxy():
    return PROXY


def on_response(resp):
    try:
        if resp.request.resource_type in ("xhr", "fetch"):
            body = ""
            try:
                body = resp.text()[:300]
            except Exception:
                pass
            NET.append(f"{resp.request.method} {resp.status} {resp.url[:110]}"
                       f" | {body[:200]}")
    except Exception:
        pass


def fill_stable(page, sel, value, tries=5):
    for i in range(tries):
        try:
            el = page.locator(sel).first
            if el.is_visible():
                el.click()
                el.fill("")
                el.fill(value)
                page.keyboard.press("Tab")
                page.wait_for_timeout(500)
                if el.input_value() == value:
                    return True
        except Exception:
            pass
        page.wait_for_timeout(1200)
    return False


with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        PROFILE, headless=False,
        proxy={"server": get_proxy()},
        args=["--disable-blink-features=AutomationControlled",
              "--no-sandbox", "--disable-dev-shm-usage"],
        user_agent=UA, viewport={"width": 1280, "height": 900}, locale="en-US")
    ctx.add_init_script(
        "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.on("response", on_response)
    page.goto("https://www.reddit.com/login/", wait_until="domcontentloaded",
              timeout=90000)
    t0 = time.time()
    while time.time() - t0 < 75:
        if page.locator('input#login-username, input[name="username"]').count() > 0:
            break
        page.wait_for_timeout(2000)
    ok = (fill_stable(page, 'input#login-username', EMAIL)
          or fill_stable(page, 'input[name="username"]', EMAIL)
          or fill_stable(page, 'input[autocomplete="username"]', EMAIL))
    print(f"填邮箱: {ok}")
    page.screenshot(path=f"{OUT}/rd_link_filled.png")
    clicked = False
    for sel in ['button:has-text("Email me a one-time link")',
                'text=Email me a one-time link',
                'a:has-text("Email me a one-time link")']:
        try:
            b = page.locator(sel).first
            if b.is_visible():
                b.click(timeout=5000)
                clicked = True
                print(f"点击: {sel}")
                break
        except Exception:
            continue
    if not clicked:
        print("未找到一次性链接按钮!")
        page.screenshot(path=f"{OUT}/rd_link_nobutton.png")
    page.wait_for_timeout(6000)
    # 二级表单: Where should we send the link to? → 填邮箱 → Continue
    ok2 = (fill_stable(page, 'input[type="email"]', EMAIL)
           or fill_stable(page, 'input[name="email"]', EMAIL)
           or fill_stable(page, 'input[autocomplete="email"]', EMAIL))
    print(f"二级表单填邮箱: {ok2}")
    page.screenshot(path=f"{OUT}/rd_link_email2.png")
    ok_click = False
    for sel in ['button:has-text("Continue")', 'button[type=submit]']:
        try:
            b = page.locator(sel).first
            if b.is_visible():
                b.click(timeout=5000)
                ok_click = True
                print(f"点击: {sel}")
                break
        except Exception:
            continue
    if not ok_click:
        print("二级表单Continue未点到!")
    page.wait_for_timeout(12000)
    page.screenshot(path=f"{OUT}/rd_link_after.png")
    try:
        body = page.inner_text("body")[:900]
    except Exception:
        body = ""
    open(f"{OUT}/rd_link_body.txt", "w").write(f"URL: {page.url}\n\n{body}")
    print("=== 页面文本 ===")
    print(body[:600])
    print("=== 网络日志 ===")
    for line in NET[-8:]:
        print(line)
    ctx.close()
