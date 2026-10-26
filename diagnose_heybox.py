# -*- coding: utf-8 -*-
"""诊断: 验证登录态 + 拉取创作者中心最近帖子, 确认今天是否发过帖"""
import json
import sys
import datetime

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient

with open("/home/z/my-project/github-hot-heybox/config.json") as f:
    cfg = json.load(f)

client = HeyboxClient(cfg["cookie"])
print("== 登录态 ==")
ok = client.check_login_ok()
print("check_login_ok:", ok)

print("\n== 创作者中心最近5条帖子 ==")
try:
    data = client.get("/bbs/app/author/concept/article/list", {
        "article_type": "all", "artilce_state": "all",
        "sort_filter": "create_at", "offset": "0", "limit": "5"})
    links = (data.get("result") or {}).get("links") or []
    print(f"共取到 {len(links)} 条")
    now = datetime.datetime.now(datetime.timezone.utc)
    for l in links:
        title = l.get("title", "")
        linkid = l.get("linkid") or l.get("link_id")
        # 尝试多种时间字段
        ts = None
        for k in ("create_time", "ctime", "created_at", "modify_time",
                  "create_at", "time"):
            v = l.get(k)
            if isinstance(v, (int, float)) and v > 10**9:
                ts = v
                break
        when = "未知时间"
        if ts:
            when = datetime.datetime.fromtimestamp(
                ts, datetime.timezone.utc).astimezone().strftime(
                    "%Y-%m-%d %H:%M:%S")
            age = (now - datetime.datetime.fromtimestamp(
                ts, datetime.timezone.utc)).total_seconds() / 3600
            when += f" ({age:.1f}小时前)"
        print(f"- [{when}] #{linkid} {title[:50]}")
except Exception as e:
    print("拉取失败:", e)
