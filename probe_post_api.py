# -*- coding: utf-8 -*-
"""测试2: 探测发帖/图片上传接口
策略: 发送空/无效参数,观察返回的 status/msg
- 端点存在但缺参数 → 返回 fail + 具体缺少什么的提示
- 端点不存在 → 404 / 其他错误
"""
import json
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient

with open("/home/z/my-project/github-hot-heybox/config.json") as f:
    cfg = json.load(f)

client = HeyboxClient(cfg["cookie"])

candidates = [
    # (方法, 路径, 描述)
    ("POST_FORM", "/bbs/app/api/post/post", "App发帖(推测)"),
    ("POST_FORM", "/bbs/app/post/post", "App发帖v2(推测)"),
    ("POST_FORM", "/bbs/app/web/post/post", "Web发帖(推测)"),
    ("POST_FORM", "/bbs/app/api/post/web/post", "Web发帖v2(推测)"),
    ("POST_FORM", "/bbs/app/api/upload/img", "图片上传(推测)"),
    ("POST_FORM", "/bbs/app/upload/img", "图片上传v2(推测)"),
    ("POST_FORM", "/bbs/app/api/post/upload/img", "发帖图片上传(推测)"),
    ("POST_FORM", "/bbs/app/web/post/upload/img", "Web发帖图片上传(推测)"),
    ("POST_FORM", "/bbs/app/community/upload/image", "社区图片上传(推测)"),
    ("GET", "/bbs/app/api/post/config", "发帖配置(推测)"),
    ("GET", "/bbs/app/api/post/topics", "发帖可用话题(推测)"),
]

for method, path, desc in candidates:
    print("-" * 70)
    print(f"[{desc}] {method} {path}")
    try:
        if method == "GET":
            data = client.get(path, {})
        else:
            data = client.post_form(path, {}, {})
        out = json.dumps(data, ensure_ascii=False)
        print("  HTTP OK →", out[:300])
    except Exception as e:
        msg = str(e)
        if hasattr(e, "response") and e.response is not None:
            print(f"  HTTP {e.response.status_code} →", e.response.text[:300])
        else:
            print("  ERR:", msg[:300])
