#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小红书凭据三层持久化(仿网易云 config.py 模式)

三层:
  1. {项目}/config.json                 运行位(沙箱重启可能丢)
  2. /home/z/.secrets/xhs_config.json   项目外持久层(重启免疫)
  3. {项目}/secrets_backup.json         base64 快照追踪位
随后验证登录态(取用户信息)。
"""
import json, os, base64, sys

BASE = "/home/z/my-project/xhs-draft-poster"
os.makedirs(BASE, exist_ok=True)

RAW = """x-rednote-datactry=CN; x-rednote-holderctry=CN; web_session=040069b7fe59305d683f53e0ab384b897be9bb; id_token=VjEAADd27CP3DG0UqeFUDvsPgZojkq6nudP6qJQgylGo8uYUswFGvkVWpobHIeOnfeKh7xdr72LKOBx4Az6rki+fFxD8eEaJX5FxMPaOPO1Z27LbMF7b/GUphGVi6rQ4uMJi8LiJ; _gray_did=27fea04e-9d46-4fa6-b149-c1f4990bec76; ets=1792128438173; xsecappid=ugc; a1=1a1432dd04e4fhsj0a0l9nnbxwmk3n01uhafk3j0c50000211859; webId=1636598c1ebb17a4e85314de98b8650c; gid=y0y4qJfdKW7qy0y4qJff8xqV4d4ixMV8081j08SIIDCE6i28TqI8yT888JyyY2j80WiYK0Wi; customerClientId=313203651882869; webBuild=1.34.1; acw_tc=0a0d0f5817926853158804952e78015b8e999ea813c3870a9e7c2c855454f1; websectiga=3fff3a6f9f07284b62c0f2ebf91a3b10193175c06e4f71492b60e056edcdebb2; sec_poison_id=605ea32e-2288-44cc-9124-df681bd4c69e; customer-sso-sid=68c517699524884412760064brimejgp7wmp6m9k; x-user-id-creator.xiaohongshu.com=6ad35e680000000009036400; access-token-creator.xiaohongshu.com=customer.creator.AT-68c517699524884412760066slmojbq9s9d1plj6; galaxy_creator_session_id=MnLuO2PMs4fmKKt53z5AGmB2Eo4l1vZPhwnz; galaxy.creator.beaker.session.id=1792685334056009245514; loadts=1792685334224"""

# 解析去重(保留后值)
jar = {}
for part in RAW.split(";"):
    part = part.strip()
    if "=" in part:
        k, _, v = part.partition("=")
        jar[k.strip()] = v.strip()
cookie = "; ".join(f"{k}={v}" for k, v in jar.items())

cfg = {
    "cookie": cookie,
    "user_id": jar.get("x-user-id-creator.xiaohongshu.com", ""),
    "a1": jar.get("a1", ""),
    "web_session": jar.get("web_session", ""),
    "mode": "draft_only",
    "note": "只存草稿不发布, 用户手动发布",
}

# 1. 运行位
with open(os.path.join(BASE, "config.json"), "w") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)

# 2. 项目外持久层
with open("/home/z/.secrets/xhs_config.json", "w") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)

# 3. base64 快照追踪位
b64 = base64.b64encode(json.dumps(cfg, ensure_ascii=False).encode()).decode()
with open(os.path.join(BASE, "secrets_backup.json"), "w") as f:
    json.dump({"xhs": b64}, f)

print("[写入] 三层凭据完成")
print("  1.", os.path.join(BASE, "config.json"))
print("  2. /home/z/.secrets/xhs_config.json")
print("  3.", os.path.join(BASE, "secrets_backup.json"))
print("[字段] user_id =", cfg["user_id"], "| a1 =", cfg["a1"][:12] + "...")
