# -*- coding: utf-8 -*-
"""测试 _repair_truncated_json 修复器(含真实截断案例)"""
import sys
sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from agi_news import _repair_truncated_json

# 案例1: 截断在字符串值中间(旧版必败的场景)
t1 = '''```json
{
  "title": "AI圈大爆发",
  "intro": "AGI日报来啦！",
  "items": [
    {"num": 1, "headline": "Meta开源", "summary": "Meta搞了个大新闻，开源了816B参数的模型，激活42B"},
    {"num": 2, "headline": "ChatGPT接入Chrome", "summary": "OpenAI把计算机使用能力引入Chrom'''
r1 = _repair_truncated_json(t1)
print("案例1(字符串中间截断):", "✓" if r1 and len(r1.get("items", [])) == 2 else "✗", 
      r1.get("items", []) and [i["num"] for i in r1["items"]] if r1 else None)

# 案例2: 截断在 key 后的冒号处
t2 = '{"title": "T", "items": [{"num": 1, "headline": "A", "summary": "B"}, {"num": 2, "headline": "C",'
r2 = _repair_truncated_json(t2)
print("案例2(逗号处截断):", "✓" if r2 and len(r2.get("items", [])) == 2 else "✗")

# 案例3: 截断在 key 名中间(修复器返回 {"num":2} 空壳, 由上层过滤)
t3 = '{"title": "T", "items": [{"num": 1, "headline": "A", "summary": "B"}, {"num": 2, "sum'
r3 = _repair_truncated_json(t3)
items3 = [it for it in (r3 or {}).get("items", [])
          if (it.get("headline") or "").strip() and (it.get("summary") or "").strip()]
print("案例3(key中间截断+过滤):", "✓" if len(items3) == 1 else "✗", r3)

# 案例4: 完整 JSON 应该也正常通过
t4 = '{"title": "T", "items": [{"num": 1, "headline": "A"}], "outro": "完"}'
r4 = _repair_truncated_json(t4)
print("案例4(完整JSON幂等):", "✓" if r4 and r4.get("outro") == "完" else "✗")

# 案例6: 中文内容+转义字符混合, 截断在img_points数组中
t6 = '''{
  "keywords": ["开源", "大模型"],
  "items": [
    {"num": 1, "headline": "A\\"B", "img_points": ["要点1", "要点'''
r6 = _repair_truncated_json(t6)
print("案例6(数组字符串中截断+转义):", "✓" if r6 and r6.get("keywords") == ["开源", "大模型"] else "✗", r6)

print("\n全部用例执行完毕")
