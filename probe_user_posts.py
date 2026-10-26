# -*- coding: utf-8 -*-
"""探测: 查询用户自己的帖子列表(只读), 判断刚才的帖子是否已创建"""
import json
import sys

BASE = "/home/z/my-project/github-hot-heybox"
sys.path.insert(0, BASE)

from heybox_client import HeyboxClient

CANDIDATES = [
    ("/bbs/app/api/user/post/list",
     {"userid": "{uid}", "offset": "0", "limit": "20", "revert": "1"}),
    ("/bbs/app/user/post/list",
     {"userid": "{uid}", "offset": "0", "limit": "20"}),
    ("/bbs/app/api/user/link/list",
     {"userid": "{uid}", "offset": "0", "limit": "20"}),
    ("/bbs/app/user/homepage/link/list",
     {"userid": "{uid}", "offset": "0", "limit": "20"}),
    ("/bbs/app/profile/links",
     {"userid": "{uid}", "offset": "0", "limit": "20"}),
]


def main():
    with open(f"{BASE}/config.json") as f:
        cfg = json.load(f)
    client = HeyboxClient(cfg["cookie"])
    uid = client.heybox_id
    print(f"uid={uid}")

    for path, params in CANDIDATES:
        real = {k: v.format(uid=uid) for k, v in params.items()}
        try:
            data = client.get(path, real)
        except Exception as e:
            print(f"[{path}] 请求异常: {str(e)[:80]}")
            continue
        status = data.get("status")
        keys = list((data.get("result") or {}).keys()) \
            if isinstance(data.get("result"), dict) else type(data.get("result")).__name__
        print(f"[{path}] status={status} result_keys={keys}")
        if status == "ok":
            res = data.get("result")
            # 打印前几条
            links = []
            if isinstance(res, dict):
                for k in ("links", "link_list", "post_list", "items", "list"):
                    if isinstance(res.get(k), list):
                        links = res[k]
                        break
            print(json.dumps(res, ensure_ascii=False)[:600])
            return
    print("所有候选端点均未命中")


if __name__ == "__main__":
    main()
