#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""urnetwork 登录后验证: 1) 代理出口IP测试 2) 账号状态探测
token 从 /network/proxies 现场获取, 不硬编码不回显
"""
import json
import urllib.request

BASE = "https://api.bringyour.com"
PROXY = "socks5h://127.0.0.1:10820"
JWT_PATH = "/home/z/.secrets/urnetwork_jwt.json"
EMAIL = "URNETWORK_EMAIL@example.com"


def api(method, path, body=None, jwt=None):
    h = {"Content-Type": "application/json", "Origin": "https://ur.io",
         "Referer": "https://ur.io/", "Accept": "application/json"}
    if jwt:
        h["Authorization"] = f"Bearer {jwt}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    try:
        with opener.open(req, timeout=40) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {}


def socks_test(proxy_url, user=None, pwd=None, label=""):
    """测试 crisp socks5 代理出口"""
    import subprocess
    cmd = ["curl", "-s", "--max-time", "25",
           "--socks5-hostname", proxy_url, "https://api.ipify.org?format=json"]
    if user:
        cmd += ["--proxy-user", f"{user}:{pwd or ''}"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        ok = '"ip"' in out.stdout
        ip = out.stdout.strip()[:60] if ok else (out.stdout or out.stderr)[:120]
        print(f"[{label}] {'OK' if ok else 'FAIL'} {ip}")
        return ok
    except Exception as e:
        print(f"[{label}] EXC {str(e)[:80]}")
        return False


def main():
    jwt = json.load(open(JWT_PATH))["by_jwt"]
    print("== 1) 账号/网络状态 ==")
    for p in ["/network/status", "/user", "/network/usage", "/network/clients"]:
        st, r = api("GET", p, jwt=jwt)
        s = json.dumps(r, ensure_ascii=False)
        print(f"GET {p} -> {st} {s[:180]}")

    print("\n== 2) 取代理信息 ==")
    st, r = api("GET", "/network/proxies", jwt=jwt)
    if st != 200:
        print("取代理失败", st); return
    pc = r["clients"][0]["proxy_client"]
    host, sport = pc["proxy_host"], pc["socks_proxy_port"]
    token = pc["auth_token"]
    print(f"host={host} socks_port={sport} plan_pro={r['plan']['pro']}")

    print("\n== 3) 出口IP测试(尝试3种鉴权模式) ==")
    # 模式A: 用户名=token
    socks_test(f"{host}:{sport}", user=token, pwd="", label="A user=token")
    # 模式B: 用户名=token 密码=token
    socks_test(f"{host}:{sport}", user=token, pwd=token, label="B user+pwd=token")
    # 模式C: 无鉴权(IP白名单/已激活)
    socks_test(f"{host}:{sport}", label="C no-auth")

    print("\n== 4) 代理API探测 ==")
    for p in ["/", "/status", "/help"]:
        url = f"https://api.{host}:{pc['api_port']}{p}"
        try:
            req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
            with opener.open(req, timeout=15) as rr:
                print(f"GET {url} -> {rr.status} {rr.read().decode()[:150]}")
        except Exception as e:
            print(f"GET {url} -> {str(e)[:100]}")


if __name__ == "__main__":
    main()
