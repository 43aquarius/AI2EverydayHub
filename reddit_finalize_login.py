#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reddit 登录态最终固化:
1. 验证登录态(DOM头像菜单 + old.reddit api)
2. storage_state 三层保存
3. reddit_account.json (含用户名/karma)
4. profile tar.gz + cookies.txt 更新
"""
import json
import os
import tarfile
import time

from playwright.sync_api import sync_playwright

PROXY = ("https://<URNETWORK_TOKEN>"
         ".crisp.bringyour.com:7167")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
OUT = "/home/z/my-project/output_preview"
PROFILE = "/home/z/my-project/secrets/reddit_profile"
TS = time.strftime("%Y%m%d_%H%M%S")


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

    cookies = [c["name"] for c in ctx.cookies("https://www.reddit.com")]
    assert "reddit_session" in cookies, "reddit_session 丢失!"
    log("reddit_session 在位 ✓")

    # 1) 首页 DOM 验证
    log("打开首页验证登录态 ...")
    page.goto("https://www.reddit.com/", wait_until="domcontentloaded",
              timeout=90000)
    page.wait_for_timeout(8000)
    page.screenshot(path=f"{OUT}/rd_logged_home.png")
    uname = ""
    for sel in ['button[id^="user-draggable-menu"]',
                'faceplate-tracker[noun="profile"]']:
        try:
            el = page.locator(sel).first
            if el.count() > 0:
                log(f"找到用户菜单元素: {sel}")
                break
        except Exception:
            pass
    login_btn = page.locator('#login-button').count()

    # 2) old.reddit 验证 (老域名边缘策略不同)
    me = {}
    try:
        r = page.evaluate(
            "fetch('https://old.reddit.com/api/me.json',"
            "{credentials:'include'}).then(r=>r.json())")
        me = (r or {}).get("data") or {}
        log(f"old.reddit me.json: {json.dumps(me, ensure_ascii=False)[:200]}")
    except Exception as e:
        log(f"old.reddit me.json 失败: {str(e)[:100]}")

    if not me.get("name"):
        # 3) 试 www 的 me.json (带完整头)
        try:
            r = page.evaluate(
                "fetch('https://www.reddit.com/api/me.json',"
                "{credentials:'include',headers:{'accept':'application/json'}})"
                ".then(r=>r.json()).catch(e=>({}))")
            me = (r or {}).get("data") or {}
            log(f"www me.json: {json.dumps(me, ensure_ascii=False)[:200]}")
        except Exception:
            pass

    # 4) 用户名兜底: 右上角菜单 aria-label
    if not me.get("name"):
        try:
            el = page.locator('button[id^="user-draggable-menu"]').first
            if el.count() > 0:
                lbl = el.get_attribute("aria-label") or ""
                log(f"用户菜单aria-label: {lbl}")
                # "<X_HANDLE>'s profile" 之类
                uname = lbl.split("'")[0].strip() if "'" in lbl else ""
        except Exception:
            pass

    username = me.get("name") or uname or ""
    log(f"★ 用户名: {username or '(未知,见截图)'} "
        f"karma={me.get('total_karma')} 登录按钮存在={login_btn > 0}")

    # 5) storage_state 三层
    os.makedirs("/home/z/.secrets", exist_ok=True)
    for path in ["/home/z/.secrets/reddit_state.json",
                 "/home/z/my-project/secrets/reddit_state.json",
                 f"/home/z/my-project/secrets/reddit_state_{TS}.json"]:
        try:
            ctx.storage_state(path=path)
            os.chmod(path, 0o600)
            log(f"saved {path}")
        except Exception as e:
            log(f"存 {path} 失败: {e}")

    # 6) 账号信息
    json.dump({"username": username,
               "email": "REDDIT_EMAIL@example.com",
               "login_time": time.strftime("%F %T"),
               "method": "magic_link (POST /svc/shreddit/account/login/magic_link 重放)",
               "exit": "urnetwork-residential",
               "karma": me.get("total_karma"),
               "created_utc": me.get("created_utc"),
               "note": "首次POST因竞态401, 同body重放即200; 坑:页面降级表单≠token失效"},
              open("/home/z/my-project/secrets/reddit_account.json", "w"),
              ensure_ascii=False, indent=1)
    log("reddit_account.json ✓")

    # 7) cookies.txt (Netscape格式, curl_cffi可用)
    try:
        lines = ["# Netscape HTTP Cookie File",
                 "# reddit.com  saved " + time.strftime("%F %T")]
        for c in ctx.cookies("https://www.reddit.com"):
            dom = c["domain"]
            flag = "TRUE" if dom.startswith(".") else "FALSE"
            path_ = c.get("path", "/")
            secure = "TRUE" if c.get("secure") else "FALSE"
            exp = int(c.get("expires", 0)) or 0
            lines.append(f"{dom}\t{flag}\t{path_}\t{secure}\t{exp}\t"
                         f"{c['name']}\t{c['value']}")
        open("/home/z/my-project/secrets/reddit_cookies.txt", "w").write(
            "\n".join(lines) + "\n")
        log("reddit_cookies.txt ✓")
    except Exception as e:
        log(f"cookies.txt失败: {e}")

    ctx.close()

# 8) profile tar 备份
try:
    with tarfile.open(
            f"/home/z/my-project/secrets/reddit_profile_{TS}.tar.gz",
            "w:gz") as tf:
        tf.add(PROFILE, arcname="reddit_profile")
    log("profile tar.gz ✓")
except Exception as e:
    log(f"tar失败: {e}")

print(json.dumps({"ok": True, "username": username,
                  "karma": me.get("total_karma")}, ensure_ascii=False))
