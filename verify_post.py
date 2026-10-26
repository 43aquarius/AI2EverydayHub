# -*- coding: utf-8 -*-
"""验证发帖结果: 查询盒友杂谈板块列表 + 搜索接口, 确认帖子是否真实创建"""
import json
import sys

BASE = "/home/z/my-project/github-hot-heybox"
sys.path.insert(0, BASE)

from heybox_client import HeyboxClient

TITLE_KEY = "XERJ"


def main():
    with open(f"{BASE}/config.json") as f:
        cfg = json.load(f)
    client = HeyboxClient(cfg["cookie"])

    # 1) 板块 feeds 里找自己的帖子
    print("===== 盒友杂谈(topic 7214) 最新帖子 =====")
    found = []
    for offset in (0, 30):
        try:
            data = client.get_topic_feeds(7214, offset=offset, limit=30)
        except Exception as e:
            print("feeds 请求失败:", e)
            break
        items = (data.get("result") or {}).get("links") \
            or (data.get("result") or {}).get("items") \
            or []
        if offset == 0 and not items:
            # 打印 result 顶层结构辅助排查
            print("result keys:", list((data.get("result") or {}).keys()))
        for it in items:
            title = it.get("title") or it.get("text") or ""
            link_id = it.get("linkid") or it.get("link_id") or it.get("id")
            uid = str(it.get("userid") or it.get("user_id") or "")
            mod = ""
            if TITLE_KEY in title or uid == client.heybox_id:
                mod = "  <== 我的帖子"
                found.append((link_id, title, uid, it))
            if offset == 0 and (TITLE_KEY in title or uid == client.heybox_id or True):
                pass
            print(f"  [{link_id}] u{uid} {title[:40]}{mod}")
        if found:
            break

    if found:
        link_id, title, uid, it = found[0]
        print(f"\n✅ 找到帖子 link_id={link_id}")
        print("链接: https://www.xiaoheihe.cn/community/7214/list/" + str(link_id))
        print("详情字段:", json.dumps(
            {k: it.get(k) for k in ("linkid", "link_id", "title", "userid",
                                    "created_at", "post_time", "views",
                                    "like_num", "share_num") if k in it},
            ensure_ascii=False))
        return

    # 2) 搜索接口兜底
    print("\n===== 搜索 'XERJ' =====")
    try:
        data = client.search("XERJ")
        res = data.get("result") or {}
        links = res.get("links") or []
        print(f"搜索到 {len(links)} 条")
        for it in links[:10]:
            print(" -", it.get("title", "")[:50],
                  "linkid:", it.get("linkid") or it.get("link_id"))
    except Exception as e:
        print("搜索失败:", e)

    print("\n未在板块列表中找到该帖子")


if __name__ == "__main__":
    main()
