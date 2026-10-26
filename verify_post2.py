# -*- coding: utf-8 -*-
"""第二轮验证: 尝试最新排序feeds + 多关键词搜索, 彻底确认帖子是否创建"""
import json
import sys

BASE = "/home/z/my-project/github-hot-heybox"
sys.path.insert(0, BASE)

from heybox_client import HeyboxClient

UID = "74691929"


def try_feeds_variants(client):
    """尝试不同排序参数, 找到按时间排序的feed"""
    variants = [
        {},
        {"sort_type": "new"},
        {"filter_type": "new"},
        {"sort": "create_time"},
        {"order": "time"},
    ]
    for extra in variants:
        try:
            data = client.get("/bbs/app/topic/feeds", {
                "topic_id": "7214", "offset": "0", "limit": "30",
                "revert": "1", **extra})
        except Exception as e:
            print(f"  variant {extra}: {str(e)[:60]}")
            continue
        res = data.get("result") or {}
        links = res.get("links") or []
        if not links:
            continue
        ids = [it.get("linkid") for it in links[:8]]
        mine = [it for it in links
                if str(it.get("userid")) == UID
                or "XERJ" in (it.get("title") or "")]
        print(f"  variant {extra}: 前8个linkid={ids} 我的新帖={len(mine)}")
        for it in mine:
            print("    >>>", json.dumps(
                {k: it.get(k) for k in ("linkid", "title", "userid")},
                ensure_ascii=False))


def try_search(client):
    for q in ["XERJ", "GitHub每日热榜", "GitHub 热榜", "锝嘚得"]:
        try:
            data = client.search(q)
        except Exception as e:
            print(f"  search {q}: {str(e)[:60]}")
            continue
        res = data.get("result") or {}
        links = res.get("links") or []
        hit = [it for it in links if str(it.get("userid")) == UID
               or "XERJ" in (it.get("title") or "")]
        print(f"  search '{q}': {len(links)}条, 命中我的={len(hit)}")
        for it in hit[:5]:
            print("    >>>", json.dumps(
                {k: it.get(k) for k in ("linkid", "title", "userid")},
                ensure_ascii=False))


def main():
    with open(f"{BASE}/config.json") as f:
        cfg = json.load(f)
    client = HeyboxClient(cfg["cookie"])

    print("===== feeds 排序变体 =====")
    try_feeds_variants(client)
    print("\n===== 搜索 =====")
    try_search(client)


if __name__ == "__main__":
    main()
