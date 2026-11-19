#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""登录状态统一审计 + X状态重建 + 多层落盘 (2026-11-19)
用户指令: "这些登录状态都要保存好"
动作:
  1. X状态重建: 从 x_post_test.py 常量恢复 auth_token/twid → 双层落盘
  2. 全平台状态盘点: urnetwork / B站 / 小黑盒 / 网易云 / X / Reddit
  3. my-project/secrets 集中加固(第二层) + 索引文件
  4. 打印总表
"""
import json
import os
import shutil
import time

TS = time.strftime("%F %T")
HOME_SEC = "/home/z/.secrets"
PROJ_SEC = "/home/z/my-project/secrets"
os.makedirs(HOME_SEC, exist_ok=True)
os.makedirs(PROJ_SEC, exist_ok=True)

# ---- 1) X 状态重建 ----
X_AUTH = "<X_AUTH_TOKEN>"
X_TWID = "u%3D<X_USER_ID>"
x_state = {
    "cookies": [
        {"name": "auth_token", "value": X_AUTH, "domain": ".x.com",
         "path": "/", "httpOnly": True, "secure": True},
        {"name": "twid", "value": X_TWID, "domain": ".x.com",
         "path": "/", "secure": True},
    ],
    "origins": [],
    "note": "重建自 x_post_test.py 常量; ct0 由会话自动重发",
    "rebuilt": TS,
}
for p in [f"{HOME_SEC}/x_state.json", f"{PROJ_SEC}/x_state.json"]:
    json.dump(x_state, open(p, "w"), indent=1)
    os.chmod(p, 0o600)
with open(f"{HOME_SEC}/x_cookies.txt", "w") as f:
    f.write(f"auth_token={X_AUTH}; twid={X_TWID}")
print("[X] 状态已重建双层落盘 ✓")


def check(path, desc):
    ok = os.path.exists(path)
    size = os.path.getsize(path) if ok else 0
    valid = ""
    if ok and size > 0 and path.endswith(".json"):
        try:
            json.load(open(path))
            valid = "JSON✓"
        except Exception:
            valid = "JSON✗"
    return {"desc": desc, "path": path, "ok": ok, "size": size, "valid": valid}


states = [
    # urnetwork
    check(f"{HOME_SEC}/urnetwork_jwt.json", "urnetwork JWT(L1)"),
    check(f"{PROJ_SEC}/urnetwork_jwt.json", "urnetwork JWT(L2)"),
    # B站
    check(f"{HOME_SEC}/bilibili_cookies.txt", "B站cookies(L1)"),
    check("/home/z/my-project/bilibili-poster/config.json", "B站config(L2)"),
    check("/home/z/my-project/bilibili-poster/secrets_backup.json", "B站backup(L3)"),
    check(f"{HOME_SEC}/bilibili_toy_session.json", "B站toy会话"),
    # 小黑盒
    check("/home/z/my-project/github-hot-heybox/state.json", "小黑盒state(L1)"),
    check(f"{HOME_SEC}/heybox_state_backup.json", "小黑盒backup(L2)"),
    check("/home/z/my-project/github-hot-heybox/secrets_backup.json", "小黑盒backup(L3)"),
    # 网易云
    check(f"{HOME_SEC}/netease_state.json", "网易云state(L1)"),
    # X
    check(f"{HOME_SEC}/x_state.json", "X状态(L1-重建)"),
    check(f"{PROJ_SEC}/x_state.json", "X状态(L2-重建)"),
    # Reddit
    check(f"{PROJ_SEC}/reddit_profile", "Reddit浏览器profile(JS挑战cookie)"),
]

# ---- 2) 网易云补第二层 ----
if os.path.exists(f"{HOME_SEC}/netease_state.json") and \
        not os.path.exists(f"{PROJ_SEC}/netease_state.json"):
    shutil.copy(f"{HOME_SEC}/netease_state.json", f"{PROJ_SEC}/netease_state.json")
    states.append(check(f"{PROJ_SEC}/netease_state.json", "网易云state(L2-新增)"))

# ---- 3) B站 toy 会话补第二层 ----
if os.path.exists(f"{HOME_SEC}/bilibili_toy_session.json") and \
        not os.path.exists(f"{PROJ_SEC}/bilibili_toy_session.json"):
    shutil.copy(f"{HOME_SEC}/bilibili_toy_session.json",
                f"{PROJ_SEC}/bilibili_toy_session.json")
    states.append(check(f"{PROJ_SEC}/bilibili_toy_session.json",
                        "B站toy会话(L2-新增)"))

# ---- 4) 小黑盒 ~/.secrets 层 → 项目层加固 ----
if os.path.exists(f"{HOME_SEC}/heybox_state_backup.json") and \
        not os.path.exists(f"{PROJ_SEC}/heybox_state_backup.json"):
    shutil.copy(f"{HOME_SEC}/heybox_state_backup.json",
                f"{PROJ_SEC}/heybox_state_backup.json")
    states.append(check(f"{PROJ_SEC}/heybox_state_backup.json",
                        "小黑盒backup(项目层-新增)"))

# ---- 5) 索引文件 ----
index = {
    "updated": TS,
    "states": states,
    "notes": [
        "Reddit账密登录: 两个密码变体均被Reddit明确拒绝(Invalid email or password), "
        "待用户提供正确凭据或改走一次性链接/Google SSO",
        "Reddit profile 内含已通过JS挑战的cookie, 后续登录可复用",
        "X auth_token 重建自 x_post_test.py, ct0无持久化必要",
        "urnetwork JWT 2026-11-19 12:41 由验证码083194新签发",
    ],
}
json.dump(index, open(f"{PROJ_SEC}/LOGIN_STATES_INDEX.json", "w"),
          ensure_ascii=False, indent=1)

print(f"\n{'状态':<28}{'OK':<4}{'大小':<8}{'校验'}")
print("-" * 60)
for s in states:
    print(f"{s['desc']:<28}{'✓' if s['ok'] else '✗':<4}{s['size']:<8}{s['valid']}")
missing = [s for s in states if not s["ok"]]
print("-" * 60)
print(f"共 {len(states)} 项, 缺失 {len(missing)} 项")
if missing:
    for m in missing:
        print("  缺失:", m["desc"], m["path"])
