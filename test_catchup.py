# -*- coding: utf-8 -*-
"""catch_up_due 判定逻辑单元测试(不启动调度器, 不写 state)"""
import datetime
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
import scheduler as S

BJT = S.BJT


def t(day_offset, hh, mm):
    """以 2026-10-18(今天)为基准构造北京时间"""
    base = datetime.datetime(2026, 10, 18, hh, mm, tzinfo=BJT)
    return base + datetime.timedelta(days=day_offset)


# 今天是周几
print("2026-10-18 是星期", datetime.date(2026, 10, 18).weekday(), "(0=周一)")
# 昨天最后一条帖子: 2026-10-17 22:17 北京时间
yesterday_post = datetime.datetime(2026, 10, 17, 22, 17, tzinfo=BJT)

# 拦截 heal_state 防止测试写 state.json
S.heal_state = lambda *a, **k: None

cases = [
    # (说明, now, period, posts, state, 期望)
    ("今天周日09:30 无state 昨晚有帖 → 日榜需补发",
     t(0, 9, 30), "daily", [yesterday_post], {}, True),
    ("今天周日09:30 周榜未到档期 → 不补",
     t(0, 9, 30), "weekly", [yesterday_post], {}, False),
    ("今天周日08:00 档期未到 → 不补",
     t(0, 8, 0), "daily", [yesterday_post], {}, False),
    ("今天09:30 state已有今日记录 → 不补",
     t(0, 9, 30), "daily", [yesterday_post],
     {"last_daily": "2026-10-18"}, False),
    ("今天09:30 今早9点已发过帖(API对账) → 不补",
     t(0, 9, 30), "daily", [t(0, 9, 0), yesterday_post], {}, False),
    ("今天09:30 对账失败(_none) → 补发(宁试勿漏)",
     t(0, 9, 30), "daily", None, {}, True),
    ("明天周一11:00 日榜周榜都错过 → 都补",
     t(1, 11, 0), "daily", [yesterday_post], {}, True),
    ("明天周一11:00 日榜已发9点 周榜错过 → 只补周榜",
     t(1, 11, 0), "daily", [t(1, 9, 0), yesterday_post], {}, False),
    ("明天周一11:00 日榜已发9点 周榜错过 → 只补周榜(weekly)",
     t(1, 11, 0), "weekly", [t(1, 9, 0), yesterday_post], {}, True),
    ("明天周一11:00 双双已发(9点+10点) → 都不补",
     t(1, 11, 0), "daily", [t(1, 10, 0), t(1, 9, 0)], {}, False),
    ("明天周一11:00 双双已发(9点+10点) → 都不补(weekly)",
     t(1, 11, 0), "weekly", [t(1, 10, 0), t(1, 9, 0)], {}, False),
    ("周二15:00 state丢失 但周一10点有帖 → 周榜视为已发",
     t(2, 15, 0), "weekly", [t(1, 10, 0), t(1, 9, 0)], {}, False),
    ("周二15:00 今日无帖 → 日榜补发",
     t(2, 15, 0), "daily", [t(1, 10, 0), t(1, 9, 0)], {}, True),
]

fails = 0
for desc, now, period, posts, state, expect in cases:
    got = S.catch_up_due(period, posts, now=now, state=state)
    mark = "PASS" if got == expect else "FAIL"
    if got != expect:
        fails += 1
    print(f"[{mark}] {desc}: got={got} expect={expect}")

print(f"\n{'全部通过' if fails == 0 else f'{fails} 个失败'} ({len(cases)} 用例)")
sys.exit(1 if fails else 0)
