# -*- coding: utf-8 -*-
"""验证软推荐句检测(用上一轮 dry-run 的实际文案做回归)"""
import sys
sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from summarizer import _detect_repetition

# 上一轮 dry-run 产出的 10 条 summary(结尾软推荐句: TOP4特别有用/
# TOP5很合适/TOP6很实用/TOP8很合适/TOP10会需要这个)
items = [
    {"rank": 1, "summary": "还在挨个文件翻代码?XERJ是个AI驱动的本地数据搜索工具,能自动索引代码、文档、日志和PDF文件。"},
    {"rank": 2, "summary": "Android skills是个专门为AI优化、模块化的Android开发指导库。"},
    {"rank": 3, "summary": "ai-memory解决了不同AI编码助手之间的记忆共享问题。"},
    {"rank": 4, "summary": "处理大量非英语文本时特别有用。"},
    {"rank": 5, "summary": "想在家用电脑上运行大型AI模型,这个项目很合适。"},
    {"rank": 6, "summary": "想免费用前沿AI模型,这个项目很实用。"},
    {"rank": 7, "summary": "觉得Adobe Photoshop太贵,可以试试这个。"},
    {"rank": 8, "summary": "需要处理大量PDF文档,这个工具很合适。"},
    {"rank": 9, "summary": "对AI在数学研究中的应用感兴趣的研究者和开发者。"},
    {"rank": 10, "summary": "使用多个AI助手、多个提供商或多个账户的用户会需要这个。"},
]
findings = _detect_repetition(items)
print("检测结果:")
for pat, ranks in findings:
    print(f"  「{pat}」→ 条目 {ranks}")
assert any("结尾软推荐" in p for p, _ in findings), "软推荐句未被抓到!"
print("✓ 软推荐句合并检测生效(5条命中 > 阈值3)")
