#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reddit 魔法链接登录 v3: 干净重试
- DOM + cookie(reddit_session) 双判定, 不再依赖被Fastly边缘403的 /api/me.json
- 捕获红色错误横幅原文
- 成功 → storage_state三层 + reddit_account.json + profile tar
"""
import json
import os
import tarfile
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
TS = time.strftime("%Y%m%d_%H%M%S")


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def cookie_names(ctx):
    return [c["name"] for c in ctx.cookies("https://www.reddit.com")]


def logged_in(page, ctx):
    """cookie判定: reddit_session 是登录态专属; 匿名会话没有"""
    if "reddit_session" in cookie_names(ctx):
        return "cookie:reddit_session"
    try:
        if page.locator('button[id^="user-draggable-menu"], '
                        'faceplate-tracker[noun="profile"]').count() > 0:
            return "dom:user-menu"
        if page.locator('#login-button, [data-testid="login-button"]').count() > 0:
            return None  # 明确未登录
    except Exception:
        pass
    return None


def error_banner(page):
    try:
        for sel in ['[data-testid="error-banner"]', 'div[role="alert"]',
                    'faceplate-banner', 'shreddit-alert']:
            el = page.locator(sel).first
            if el.count() > 0 and el.inner_text().strip():
                return f"{sel}: {el.inner_text().strip()[:200]}"
    except Exception:
        pass
    return ""


def save_all(ctx):
    me = None
    # 最后一搏: 试试 old.reddit 的 me.json (老域名边缘策略不同)
    return me


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
    log(f"打开魔法链接(第2次尝试) ...")
    page.goto(MAGIC, wait_until="domcontentloaded", timeout=90000)

    how = None
    t0 = time.time()
    seen_banner = ""
    while time.time() - t0 < 120:
        page.wait_for_timeout(6000)
        how = logged_in(page, ctx)
        if how:
            break
        b = error_banner(page)
        if b and b != seen_banner:
            seen_banner = b
            log(f"错误横幅: {b}")
        if int(time.time() - t0) % 30 < 6:
            log(f"等待... URL={page.url[:90]} cookies={cookie_names(ctx)}")

    if how:
        log(f"★ 登录成功! 判定依据: {how}")
        page.screenshot(path=f"{OUT}/rd_magic3_ok.png")
        try:
            page.goto("https://www.reddit.com/", wait_until="domcontentloaded",
                      timeout=60000)
            page.wait_for_timeout(6000)
        except Exception:
            pass
        os.makedirs("/home/z/.secrets", exist_ok=True)
        for path in ["/home/z/.secrets/reddit_state.json",
                     "/home/z/my-project/secrets/reddit_state.json",
                     f"/home/z/my-project/secrets/reddit_state_{TS}.json"]:
            try:
                ctx.storage_state(path=path)
                os.chmod(path, 0o600)
            except Exception as e:
                log(f"存 {path} 失败: {e}")
        # DOM里抠用户名
        uname = ""
        try:
            for sel in ['button[id^="user-draggable-menu"] img',
                        'faceplate-tracker[noun="profile"] img',
                        'img[alt*="avatar" i]']:
                el = page.locator(sel).first
                if el.count() > 0:
                    uname = (el.get_attribute("alt") or "").strip()
                    if uname:
                        break
        except Exception:
            pass
        page.screenshot(path=f"{OUT}/rd_magic3_home.png")
        json.dump({"username": uname or "(见截图确认)",
                   "email": "REDDIT_EMAIL@example.com",
                   "login_time": time.strftime("%F %T"),
                   "method": "magic_link_v3",
                   "exit": "urnetwork-residential-47.154.5.206"},
                  open("/home/z/my-project/secrets/reddit_account.json", "w"),
                  ensure_ascii=False, indent=1)
        try:
            with tarfile.open(
                    f"/home/z/my-project/secrets/reddit_profile_{TS}.tar.gz",
                    "w:gz") as tf:
                tf.add(PROFILE, arcname="reddit_profile")
            log("profile tar 备份 ✓")
        except Exception as e:
            log(f"tar失败(不影响): {e}")
        print(json.dumps({"ok": True, "how": how, "username_hint": uname},
                         ensure_ascii=False))
    else:
        page.screenshot(path=f"{OUT}/rd_magic3_fail.png")
        body = ""
        try:
            body = page.inner_text("body")[:600]
        except Exception:
            pass
        print(json.dumps({"ok": False, "url": page.url[:100],
                          "banner": seen_banner,
                          "cookies": cookie_names(ctx),
                          "body": body[:300]}, ensure_ascii=False, indent=1))
    ctx.close()
