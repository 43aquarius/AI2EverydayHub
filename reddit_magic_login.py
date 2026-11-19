#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reddit 魔法链接登录 → 会话持久化 (v2: 2026-11-19 第二条链接)
同一持久profile + 住宅HTTPS出口(crisp 7167 token子域名直连) + 有头模式
登录成功 → storage_state三层 + profile tar + 账号信息
沙盒回收后 socks10820 不在, 但 crisp 7167 免鉴权直连实测 200, 直接硬编码
"""
import json
import os
import tarfile
import time

from playwright.sync_api import sync_playwright

MAGIC = ("https://www.reddit.com/magic_link/mlt:<MAGIC_TOKEN>/"
         "t2_<REDDIT_USER_ID>?$deep_link=true&otp=false")
# urnetwork 住宅HTTPS出口, token编在子域名, 免鉴权 (与JWT同周期, exp 2026-12-19)
PROXY = ("https://<URNETWORK_TOKEN>"
         ".crisp.bringyour.com:7167")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
OUT = "/home/z/my-project/output_preview"
PROFILE = "/home/z/my-project/secrets/reddit_profile"
TS = time.strftime("%Y%m%d_%H%M%S")


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def get_proxy():
    return PROXY


def verify_me(page):
    for base in ["", "https://www.reddit.com"]:
        try:
            me = page.evaluate(
                f"fetch('{base}/api/me.json', {{credentials:'include'}})"
                f".then(r=>r.json())")
            d = (me or {}).get("data") or {}
            if d.get("name"):
                return d
        except Exception:
            continue
    return None


def save_all(ctx, d):
    os.makedirs("/home/z/.secrets", exist_ok=True)
    os.makedirs("/home/z/my-project/secrets", exist_ok=True)
    for path in ["/home/z/.secrets/reddit_state.json",
                 "/home/z/my-project/secrets/reddit_state.json",
                 f"/home/z/my-project/secrets/reddit_state_{TS}.json"]:
        try:
            ctx.storage_state(path=path)
            os.chmod(path, 0o600)
        except Exception as e:
            log(f"存 {path} 失败: {e}")
    json.dump({"username": d["name"],
               "email": "REDDIT_EMAIL@example.com",
               "login_time": time.strftime("%F %T"),
               "method": "magic_link",
               "exit": "urnetwork-residential",
               "karma": d.get("total_karma"),
               "created_utc": d.get("created_utc")},
              open("/home/z/my-project/secrets/reddit_account.json", "w"),
              ensure_ascii=False, indent=1)
    try:
        with tarfile.open(
                f"/home/z/my-project/secrets/reddit_profile_{TS}.tar.gz",
                "w:gz") as tf:
            tf.add(PROFILE, arcname="reddit_profile")
        log("profile tar 备份 ✓")
    except Exception as e:
        log(f"tar备份失败(不影响): {e}")
    print(json.dumps({"ok": True, "username": d["name"],
                      "karma": d.get("total_karma"),
                      "coins": d.get("coin_balance"),
                      "created": d.get("created_utc")}, ensure_ascii=False))


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
    NET = []

    def on_response(resp):
        try:
            if resp.request.resource_type in ("xhr", "fetch") and \
                    "reddit.com" in resp.url:
                body = ""
                try:
                    body = resp.text()[:300]
                except Exception:
                    pass
                NET.append(f"{resp.request.method} {resp.status} "
                           f"{resp.url[:110]} | {body[:200]}")
        except Exception:
            pass

    page.on("response", on_response)
    log("打开魔法链接 ...")
    page.goto(MAGIC, wait_until="domcontentloaded", timeout=90000)

    # 魔法链接会经过若干跳转, 轮询验证登录态(最多150秒)
    d = None
    t0 = time.time()
    shots = 0
    while time.time() - t0 < 150:
        page.wait_for_timeout(5000)
        d = verify_me(page)
        if d:
            break
        if shots < 3:
            page.screenshot(path=f"{OUT}/rd_magic_{shots+1}.png")
            shots += 1
            log(f"等待登录... URL: {page.url[:80]}")

    if d:
        log(f"登录成功: u/{d['name']} karma={d.get('total_karma')}")
        page.screenshot(path=f"{OUT}/rd_magic_home.png")
        # 回首页让会话cookie充分固化
        try:
            page.goto("https://www.reddit.com/", wait_until="domcontentloaded",
                      timeout=60000)
            page.wait_for_timeout(5000)
            d2 = verify_me(page)
            if d2:
                d = d2
        except Exception:
            pass
        save_all(ctx, d)
    else:
        page.screenshot(path=f"{OUT}/rd_magic_fail.png")
        try:
            body = page.inner_text("body")[:800]
        except Exception:
            body = ""
        open(f"{OUT}/rd_magic_fail.txt", "w").write(
            f"URL: {page.url}\n\n{body}")
        print(json.dumps({"ok": False, "url": page.url[:100],
                          "body": body[:300]}, ensure_ascii=False))
        print("=== reddit XHR ===")
        for line in NET[-15:]:
            print(line)
    ctx.close()
