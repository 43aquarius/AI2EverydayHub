# -*- coding: utf-8 -*-
"""重建被环境重启清除的 github-hot-heybox/state.json

2026-10-22 凌晨 04:03/04:12 调度器补发已成功(AGI 194675397 / 日榜 194675999),
但 07:05 重启把 state.json 清掉了。若不重建, 09:30 AGI 档期会因 agi_last_issue
丢失而重复发帖。本脚本按 agi_news.py/main.py 的写入格式精确复刻当日标记。
"""
import datetime
import json

STATE = "/home/z/my-project/github-hot-heybox/state.json"

today = datetime.date(2026, 10, 22)
iso = today.isocalendar()
week_marker = f"{iso.year}-W{iso.week}"  # 2026-W43

AGI_URL = ("https://www.xiaoheihe.cn/community/"
           "7214/list/194675397")
DAILY_URL = ("https://www.xiaoheihe.cn/community/"
             "7214/list/194675999")

state = {
    "agi_last_issue": "20261022",
    "last_agi": today.isoformat(),
    "last_daily": today.isoformat(),
    "last_weekly": week_marker,
    "history": [
        {
            "period": "agi", "issue": "20261022",
            "date": today.isoformat(), "url": AGI_URL,
            "title": "AI圈速递：14天建AI工厂，Claude 64小时设计31万种蛋白",
        },
        {
            "period": "daily", "date": today.isoformat(),
            "url": DAILY_URL, "repos": [],
        },
    ],
    # recent_repos 无法从帖子精确重建, 留空仅影响后续日榜换新面孔权重
    "recent_repos": {},
}

with open(STATE, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)

print("state.json 已重建:")
print(json.dumps(state, ensure_ascii=False, indent=2)[:600])
