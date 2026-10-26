#!/usr/bin/env python3
"""scheduler AGI 档期调度逻辑单测(不真实发帖)"""
import datetime
import json
import os
import sys
import tempfile

BASE = "/home/z/my-project/github-hot-heybox"
sys.path.insert(0, BASE)

import scheduler

BJT = scheduler.BJT
PASS, FAIL = 0, 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name}")


def mkstate(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


def main():
    tmp = tempfile.mkdtemp()
    state_path = os.path.join(tmp, "state.json")
    cfg_path = os.path.join(tmp, "config.json")
    scheduler.STATE = state_path
    scheduler.CONFIG = cfg_path

    # 周日 10:00 (档期前)
    sun = datetime.datetime(2026, 10, 18, 10, 0, tzinfo=BJT)  # 周日
    # 周一 09:00 / 09:40
    mon_early = datetime.datetime(2026, 10, 19, 9, 0, tzinfo=BJT)
    mon_late = datetime.datetime(2026, 10, 19, 9, 40, tzinfo=BJT)

    print("== slot_datetime / state_marker ==")
    check("agi 档期=今日09:30",
          scheduler.slot_datetime("agi", sun) ==
          sun.replace(hour=9, minute=30))
    check("agi 标记=今日日期",
          scheduler.state_marker("agi", sun) == "2026-10-18")

    print("== catch_up_due: AGI ==")
    # case1: 档期前(09:00) → 不补发
    mkstate(state_path, {})
    check("09:00 档期前不补发",
          not scheduler.catch_up_due("agi", [], now=mon_early,
                                     state={"last_agi": ""}))
    # case2: 档期后无标记 → 补发(即使创作者中心无帖, 无新期属正常)
    check("09:40 无标记补发",
          scheduler.catch_up_due("agi", [], now=mon_late,
                                 state={"last_agi": ""}))
    # case3: 今日已处理 → 不补发
    check("今日已处理不补发",
          not scheduler.catch_up_due("agi", [], now=mon_late,
                                     state={"last_agi": "2026-10-19"}))
    # case4: 昨日处理过 → 今日档期后应补发
    check("昨日处理过今日应补",
          scheduler.catch_up_due("agi", [], now=mon_late,
                                 state={"last_agi": "2026-10-18"}))

    print("== active_periods 开关 ==")
    mkstate(cfg_path, {"post": {"daily_enabled": False,
                                "weekly_enabled": True,
                                "agi_enabled": True}})
    check("agi 开关读取", scheduler.active_periods() == ("weekly", "agi"))
    mkstate(cfg_path, {"post": {"daily_enabled": False,
                                "weekly_enabled": True,
                                "agi_enabled": False}})
    check("agi 关闭时不含", "agi" not in scheduler.active_periods())

    print("== next_run(agi) 为每日 UTC 01:30 ==")
    t = scheduler.next_run("agi")
    check("UTC 01:30", (t.hour, t.minute) == (1, 30))

    print("== agi_news 防重/标记函数 ==")
    sys.path.insert(0, BASE)
    import agi_news
    agi_news.STATE_PATH = state_path
    mkstate(state_path, {"agi_last_issue": "20261008"})
    check("已发期判定(>=)", agi_news.already_posted_issue("20261008"))
    check("更新期判定(<)", not agi_news.already_posted_issue("20261009"))
    agi_news.mark_day_processed()
    check("mark_day_processed 写 last_agi",
          json.load(open(state_path)).get("last_agi") ==
          datetime.date.today().isoformat())
    agi_news.mark_issue_posted("20261009", "http://x", "测试标题")
    st = json.load(open(state_path))
    check("mark_issue_posted 双写",
          st.get("agi_last_issue") == "20261009" and
          st.get("last_agi") == datetime.date.today().isoformat())

    print(f"\n结果: {PASS} 通过 / {FAIL} 失败")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
