# -*- coding: utf-8 -*-
"""交叉验证 Python 与 JS 签名实现的一致性"""
import subprocess
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import compute_hkey

cases = [
    ("/bbs/app/topic/categories", 1792231298, "3C7078C8EB59C6E71C253354F2A075AB"),
    ("/bbs/app/feeds", 1792231400, "AABBCCDD1122334455667788990011FF"),
    ("/bbs/app/api/post/post", 1700000001, "0123456789ABCDEF0123456789ABCDEF"),
    ("/bbs/app/link/favour", 1234567890, "FFFFAAAABBBBCCCCDDDDEEEE00001111"),
    ("/account/get_qrcode_url/", 1000000000, "1234567890ABCDEF1234567890ABCDEF"),
]

all_ok = True
for path, ts, nonce in cases:
    py = compute_hkey(path, ts, nonce)
    js = subprocess.run(
        ["node", "/home/z/my-project/scripts/sig_verify.js", path, str(ts), nonce],
        capture_output=True, text=True).stdout.strip()
    ok = py == js
    all_ok = all_ok and ok
    print(f"{'PASS' if ok else 'FAIL'}  py={py}  js={js}  path={path}")

print("\nALL PASS" if all_ok else "\nMISMATCH FOUND!")
sys.exit(0 if all_ok else 1)
