# -*- coding: utf-8 -*-
"""用 link/tree 接口查看帖子实际内容结构"""
import json
import sys

BASE = "/home/z/my-project/github-hot-heybox"
sys.path.insert(0, BASE)

from heybox_client import HeyboxClient


def main():
    with open(f"{BASE}/config.json") as f:
        cfg = json.load(f)
    client = HeyboxClient(cfg["cookie"])

    data = client.get("/bbs/app/link/tree", {
        "link_id": "194210321", "is_first": "1", "page": "1", "index": "1",
        "limit": "20", "owner_only": "0"})
    print("status:", data.get("status"))
    res = data.get("result") or {}
    link = res.get("link") or {}
    print("标题:", link.get("title"))
    print("板块:", link.get("topic_name") or link.get("topic_info"))
    text = link.get("text") or link.get("content") or ""
    print("text 字段类型:", type(text).__name__, "长度:", len(str(text)))
    s = str(text)
    print("包含TOP1:", "TOP1" in s, " 包含TOP10:", "TOP10" in s,
          " 包含#GitHub#:", "#GitHub#" in s)
    print("\n----- text 前1500字符 -----")
    print(s[:1500])
    # 图片
    if isinstance(text, str) and text.startswith("["):
        try:
            blocks = json.loads(text)
            types = [b.get("type") for b in blocks]
            print("\n块类型序列:", types[:20])
        except Exception as e:
            print("解析块失败:", e)
    imgs = link.get("images") or link.get("imgs") or []
    print("\nimages 字段:", json.dumps(imgs, ensure_ascii=False)[:300])


if __name__ == "__main__":
    main()
