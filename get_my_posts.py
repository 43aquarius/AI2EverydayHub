# -*- coding: utf-8 -*-
"""通过创作者中心接口获取我的帖子列表(含 link_id)"""
import json
import sys

BASE = "/home/z/my-project/github-hot-heybox"
sys.path.insert(0, BASE)

from heybox_client import HeyboxClient


def main():
    with open(f"{BASE}/config.json") as f:
        cfg = json.load(f)
    client = HeyboxClient(cfg["cookie"])

    data = client.get("/bbs/app/author/concept/article/list", {
        "article_type": "all", "artilce_state": "all",
        "sort_filter": "create_at", "offset": "0", "limit": "20"})
    print("status:", data.get("status"))
    res = data.get("result") or {}
    links = res.get("links") or res.get("list") or res.get("articles") or []
    if not links and isinstance(res, dict):
        print("result keys:", list(res.keys()))
        print(json.dumps(res, ensure_ascii=False)[:800])
        return
    print(f"共 {len(links)} 条")
    for it in links[:12]:
        title = it.get("title") or (it.get("text") or "")[:30]
        print(f"  linkid={it.get('linkid') or it.get('link_id')}"
              f"  {it.get('create_at') or it.get('modified_at')}  {title[:36]}"
              f"  浏览{it.get('views')} 赞{it.get('like_num')}")


if __name__ == "__main__":
    main()
