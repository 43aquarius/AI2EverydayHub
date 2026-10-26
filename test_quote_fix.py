# -*- coding: utf-8 -*-
"""单测: _fix_unescaped_quotes / _extract_json / _repair_truncated_json
夹具 = 2026-10-21 实际抓到的 LLM 原始输出(未转义中文引语)"""
import json
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from summarizer import _fix_unescaped_quotes, _extract_json, _repair_truncated_json

fails = 0

def check(name, cond, detail=""):
    global fails
    print(f"  {'✓' if cond else '✗'} {name} {detail}")
    if not cond:
        fails += 1

print("[1] 真实夹具: 今日 LLM 原始输出")
raw = open("/home/z/my-project/scripts/agi_llm_raw.txt", encoding="utf-8").read()
d = _extract_json(raw)
check("extract_json 解析成功", d is not None)
if d:
    check("9 条齐全", len(d.get("items", [])) == 9, f"实得 {len(d.get('items', []))}")
    musk = next((it for it in d["items"] if "马斯克" in (it.get("headline") or "")), None)
    check("找到马斯克条目", musk is not None)
    if musk:
        check("引语保留在 summary", "全民高收入" in musk["summary"],
              f"| {musk['summary'][:50]}")
        check("tagline 无损坏", musk.get("tagline") == "7200万儿童获赠SpaceX股票")
    check("img_points 数组完好", d["items"][8].get("img_points") ==
          ["总访问量破3亿次", "WorkBuddy领跑市场"])
r = _repair_truncated_json(raw)
check("repair 也成功", r is not None and len(r.get("items", [])) == 9)

print("[2] 构造: 未转义引语 + 截断")
t2 = ('```json\n{"intro":"今天3条","items":[\n'
      '{"num":1,"headline":"A","summary":"马斯克纠正为"全民高收入"，称AI会带来成本坍塌。"},\n'
      '{"num":2,"headline":"B","summary":"他说"别慌"，然后转身离开现场。"},\n'
      '{"num":3,"headline":"C","summary":"正常文案没有引号，长度足够通过过滤条件。"}')
r2 = _repair_truncated_json(t2)
check("截断+引语 修复", r2 is not None and len(r2.get("items", [])) >= 2,
      f"实得 {len((r2 or {}).get('items', []))}")
if r2 and r2.get("items"):
    check("引语内容未丢", "全民高收入" in r2["items"][0]["summary"])
    check("第二处引语未丢", "别慌" in r2["items"][1]["summary"])

print("[3] 构造: 合法 JSON 不被误改")
t3 = '{"a": "x, y", "b": ["p", "q"], "c": 1}'
check("fixer 输出等价", json.loads(_fix_unescaped_quotes(t3)) == json.loads(t3))
check("extract 原样", _extract_json(t3) == json.loads(t3))

print("[4] 构造: 值尾内容引号 + 逗号后接中文(最险场景)")
t4 = '{"a": "他说"好",然后走了", "b": 2}'
f4 = _fix_unescaped_quotes(t4)
try:
    v = json.loads(f4)
    check("险场景可解析", True, f"a={v.get('a')!r}")
except json.JSONDecodeError as e:
    check("险场景可解析", False, str(e))

print("[5] 构造: 前导文字 + 围栏 + 引语 三重叠加")
t5 = ('好的，以下是JSON：\n```json\n{"title":"T","items":['
      '{"num":1,"h":"x","s":"网友称"破防了"，评论区热闹。"},'
      '{"num":2,"h":"y","s":"第二条内容。"}]}\n```')
d5 = _extract_json(t5)
check("三重叠加", d5 is not None and len(d5.get("items", [])) == 2)
if d5 and d5.get("items"):
    check("引语保留", "破防了" in d5["items"][0]["s"])

print()
print("ALL PASS" if fails == 0 else f"{fails} FAILED")
sys.exit(1 if fails else 0)
