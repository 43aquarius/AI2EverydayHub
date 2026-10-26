# -*- coding: utf-8 -*-
"""catch_up_due v2 判定逻辑单元测试: 话题标签区分榜单帖与 AGI 帖
场景原型(2026-10-19 实际踩坑):
  AGI 日报 09:30 档期晚发于 10:15, 老逻辑把 AGI 帖误判为周榜已发 → 漏发周榜
"""
import datetime
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
import scheduler as S

BJT = S.BJT


def t(day_offset, hh, mm):
    base = datetime.datetime(2026, 10, 19, hh, mm, tzinfo=BJT)  # 周一
    return base + datetime.timedelta(days=day_offset)


def post(hh, mm, lid, day=0, title="x"):
    return {"time": t(day, hh, mm), "link_id": lid, "title": title}


S.heal_state = lambda *a, **k: None

TAGS = {
    "1001": "#AGI# #人工智能# #AI资讯#",       # AGI 帖
    "1002": "#GitHub# #开源# #程序员#",         # 周榜帖
    "1003": "#GitHub# #开源# #程序员#",         # 日榜/项目帖
    "": "",
}
lookup = lambda lid: TAGS.get(lid, "")

cases = [
    # (说明, now, period, posts, tag_lookup, state, 期望)
    ("周一10:30 AGI帖10:15在窗口 但标签是#AGI# → 周榜仍需补发",
     t(0, 10, 30), "weekly", [post(10, 15, "1001")], lookup, {}, True),
    ("周一10:30 窗口内是周榜帖(#GitHub#) → 不补",
     t(0, 10, 30), "weekly", [post(10, 5, "1002")], lookup, {}, False),
    ("周一10:30 窗口内 AGI+周榜都有 → 不补",
     t(0, 10, 30), "weekly", [post(10, 15, "1001"), post(10, 5, "1002")],
     lookup, {}, False),
    ("周一10:30 无tag_lookup(旧行为) 窗口有AGI帖 → 视为已发不补",
     t(0, 10, 30), "weekly", [post(10, 15, "1001")], None, {}, False),
    ("周一09:58 档期未到 → 不补",
     t(0, 9, 58), "weekly", [post(9, 40, "1001")], lookup, {}, False),
    ("周二15:00 state丢失 周一10点发的是AGI帖 → 周榜补发",
     t(1, 15, 0), "weekly", [post(10, 15, "1001")], lookup, {}, True),
    ("周二15:00 周一10点发的是周榜帖 → 不补",
     t(1, 15, 0), "weekly", [post(10, 5, "1002")], lookup, {}, False),
    ("周二15:00 state已有W43记录 → 不补",
     t(1, 15, 0), "weekly", [], lookup, {"last_weekly": "2026-W43"}, False),
    ("AGI档期: 无tag也不看对账, 期号防重内部兜底 → 总是True",
     t(0, 10, 30), "agi", [post(10, 15, "1001")], lookup, {}, True),
    ("裸datetime兼容(旧测试形态) 窗口有帖无lookup → 已发",
     t(0, 10, 30), "weekly", [t(0, 10, 15)], None, {}, False),
]

fails = 0
for desc, now, period, posts, tl, state, expect in cases:
    got = S.catch_up_due(period, posts, now=now, state=state, tag_lookup=tl)
    mark = "PASS" if got == expect else "FAIL"
    if got != expect:
        fails += 1
    print(f"[{mark}] {desc}  → {got}")

print()
print("全部通过 ✓" if fails == 0 else f"{fails} 个失败 ✗")
sys.exit(1 if fails else 0)
