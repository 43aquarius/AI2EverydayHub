#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看小红书创作者通知/违规详情(只读, 不发布)"""
import json
import re
import sys
import time

sys.path.insert(0, "/home/z/my-project/xhs-draft-poster")
from xhs_client import XhsDraftClient, run_with_xvfb


def main():
    cfg = json.load(open("/home/z/my-project/xhs-draft-poster/config.json"))
    cookie = cfg.get("cookie") or ""
    client = XhsDraftClient(cookie)
    page = client._launch()
    try:
        # 通知/私信中心
        for url, shot in [
            ("https://creator.xiaohongshu.com/new/message", "/tmp/xhs_message.png"),
            ("https://creator.xiaohongshu.com/new/note-manager", "/tmp/xhs_note_mgr2.png"),
        ]:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            time.sleep(5)
            page.screenshot(path=shot, full_page=False)
            html = page.content()
            texts = re.findall(r'>([^<>]{6,90})<', html)
            seen = set()
            print(f"===== {url} =====")
            for t in texts:
                t = t.strip()
                if t and t not in seen and not t.startswith(
                        ("function", "window", "var ", "http")):
                    seen.add(t)
                    print("·", t[:80])
                if len(seen) > 20:
                    break
    finally:
        try:
            client.close()
        except Exception:
            pass


run_with_xvfb(main)
