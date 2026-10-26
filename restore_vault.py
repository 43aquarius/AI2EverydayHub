#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 AI2OpsVault 私库恢复四平台凭据 (Contents API, 不依赖 git)

vault.json 结构: {"platforms": {"heybox": {...}, "weibo": {...},
                  "netease": {...}, "xhs": {...}}, "github_pat_b64": "..."}
恢复目标(三层): 项目 config.json + /home/z/.secrets/*.json
"""
import base64
import json
import os
import sys
import urllib.request

sys.path.insert(0, "/home/z/my-project/scripts")
from gh_token import token as PAT

REPO = "43aquarius/AI2OpsVault"
SECRETS = "/home/z/.secrets"

TARGETS = {
    "heybox": ("/home/z/my-project/github-hot-heybox/config.json",
               f"{SECRETS}/heybox_config.json"),
    "weibo": ("/home/z/my-project/weibo-agi-poster/config.json",
              f"{SECRETS}/weibo_config.json"),
    "netease": ("/home/z/my-project/netease-music-poster/config.json",
                f"{SECRETS}/netease_config.json"),
    "xhs": ("/home/z/my-project/xhs-draft-poster/config.json",
            f"{SECRETS}/xhs_config.json"),
}


def gh_get(path):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/contents/{path}",
        headers={"Authorization": f"Bearer {PAT()}",
                 "Accept": "application/vnd.github+json",
                 "User-Agent": "vault-restore"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main():
    os.makedirs(SECRETS, exist_ok=True)
    try:
        data = gh_get("vault.json")
        vault = json.loads(base64.b64decode(data["content"]).decode())
    except Exception as e:
        print(f"❌ vault.json 获取失败: {e}")
        return 1

    print(f"vault 更新时间: {data.get('sha', '?')[:8]} / "
          f"平台: {list(vault.get('platforms', {}).keys())}")
    ok = 0
    for name, (cfg_path, secrets_copy) in TARGETS.items():
        cfg = (vault.get("platforms") or {}).get(name)
        if not cfg:
            print(f"[{name}] vault 无此平台凭据, 跳过")
            continue
        for p in (cfg_path, secrets_copy):
            with open(p, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            os.chmod(p, 0o600)
        key = "cookie" if "weibo" not in name else "weibo_cookie"
        has_auth = bool((cfg.get(key) or cfg.get("cookies") or
                         cfg.get("pkey") or "").strip())
        print(f"[{name}] ✅ 已回写 config.json + .secrets (登录凭据存在: {has_auth})")
        ok += 1

    # PAT 也存进 vault 的话同步校验
    pat_b64 = vault.get("github_pat_b64")
    if pat_b64:
        vpat = base64.b64decode(pat_b64).decode()
        if vpat != PAT():
            print("⚠ vault 内 PAT 与当前 .secrets PAT 不同 (以 .secrets 为准)")
    print(f"\n完成: {ok}/4 平台凭据已恢复")
    return 0


if __name__ == "__main__":
    sys.exit(main())
