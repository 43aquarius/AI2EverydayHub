# -*- coding: utf-8 -*-
"""调试: 抓 AGI 生成的原始 LLM 输出, 分析截断修复器为何 0 条"""
import json, sys, re

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
import agi_news as agi
from summarizer import _call_llm, _extract_json, _repair_truncated_json

# 1) 取今日期数据
meta = agi.latest_issue_meta()
print("期号:", meta["date"])
html = agi._http_get(meta["source_url"], timeout=30)
text = agi.extract_wx_text(html)
sections = agi.split_sections(text)
print("切出条数:", len(sections))

slim = [{"num": i + 1, "title": s["title"], "points": s["points"],
         "link": s["link"]} for i, s in enumerate(sections)]

# 2) 复刻管线 prompt
import datetime
today = datetime.date.today()
issue_date_display = (f"{meta['date'][:4]}年{int(meta['date'][4:6])}月"
                      f"{int(meta['date'][6:])}日")
prompt = agi._GEN_PROMPT.format(
    today=today.isoformat(), issue_date_display=issue_date_display,
    sections_json=json.dumps(slim, ensure_ascii=False, indent=1),
    style_rules=agi._STYLE_RULES, extra_rules=agi.AGI_EXTRA_RULES)
print("prompt 长度:", len(prompt))

# 3) 调 LLM 一次, 存原始输出
raw = _call_llm(prompt, system=agi.AGI_SYSTEM)
with open("/home/z/my-project/scripts/agi_llm_raw.txt", "w", encoding="utf-8") as f:
    f.write(raw)
print("输出长度:", len(raw))
print("=== 前 400 字 ===")
print(raw[:400])
print("=== 后 400 字 ===")
print(raw[-400:])

# 4) 测两种解析
d1 = _extract_json(raw)
print("\n_extract_json:", "OK items=%d" % len(d1["items"]) if d1 and d1.get("items") else "FAIL")
d2 = _repair_truncated_json(raw)
n2 = len((d2 or {}).get("items") or [])
print("_repair_truncated_json:", f"OK items={n2}" if d2 else "FAIL/None")

# 5) 逐段分析结构
print("\n=== 结构分析 ===")
print("首字符:", repr(raw[:3]))
print("含 ```围栏:", "```" in raw)
print("{ 数量:", raw.count("{"), "} 数量:", raw.count("}"))
print("[ 数量:", raw.count("["), "] 数量:", raw.count("]"))
print("换行数:", raw.count("\n"))
