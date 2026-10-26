# -*- coding: utf-8 -*-
"""检查消息通知: 发帖审核结果通常会有系统消息"""
import json
import sys

BASE = "/home/z/my-project/github-hot-heybox"
sys.path.insert(0, BASE)

from heybox_client import HeyboxClient


def main():
    with open(f"{BASE}/config.json") as f:
        cfg = json.load(f)
    client = HeyboxClient(cfg["cookie"])

    for lt in ("0", "1", "2", "3", "4"):
        try:
            data = client.get("/bbs/app/user/message", {
                "list_type": lt, "offset": "0", "limit": "10",
                "no_more": "false"})
        except Exception as e:
            print(f"list_type={lt}: {str(e)[:60]}")
            continue
        status = data.get("status")
        res = data.get("result")
        if status != "ok":
            print(f"list_type={lt}: status={status}")
            continue
        # 结构探查
        if isinstance(res, dict):
            keys = list(res.keys())
            print(f"list_type={lt}: keys={keys}")
            for k in ("list", "items", "messages"):
                lst = res.get(k)
                if isinstance(lst, list):
                    for m in lst[:10]:
                        s = json.dumps(m, ensure_ascii=False)
                        print("   ", s[:220])
                    break
        else:
            print(f"list_type={lt}: result={str(res)[:100]}")


if __name__ == "__main__":
    main()
