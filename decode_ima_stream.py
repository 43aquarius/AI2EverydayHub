#!/usr/bin/env python3
"""解码 ima shareId 页面的 Remix turbo-stream 数据"""
import re
import json

html = open('/tmp/ima_share.html', encoding='utf-8').read()
m = re.search(
    r'window\.__remixContext\.streamController\.enqueue\("(.*?)"\);', html, re.S)
if not m:
    raise SystemExit("未找到 stream 数据")
raw = m.group(1)
# JS 字符串转义还原
raw = raw.encode().decode('unicode_escape')
data = json.loads(raw)
print(f"数据块数: {len(data)}")

# turbo-stream 格式: 数组交替出现 {键编码:值编码} 和实际值
# 编码形如 {"_1":2} 表示键位置1 -> 值位置2，负数为特殊类型
# 先粗暴提取所有字符串值看看有什么
strings = []
for i, item in enumerate(data):
    if isinstance(item, str):
        strings.append((i, item))
    elif isinstance(item, dict):
        for k, v in item.items():
            pass

print(f"字符串总数: {len(strings)}")
for i, (idx, s) in enumerate(strings):
    print(f"[{idx}] {s[:160]}")
    if i > 60:
        break
