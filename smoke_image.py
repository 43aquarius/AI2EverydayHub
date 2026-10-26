# -*- coding: utf-8 -*-
"""冒烟测试: 假数据渲染切片(banner+卡片+长图), 不走LLM和网络"""
import os
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from image_maker import render_post_images

repos = [
    {"rank": 1, "full_name": "xerj-org/xerj", "stars": 7400,
     "period_stars": "1,102 stars today", "language": "Rust",
     "url": "https://github.com/xerj-org/xerj",
     "created_at": "2026-08-01T00:00:00Z", "description": "AI search"},
    {"rank": 2, "full_name": "akitaonrails/ai-memory", "stars": 9700,
     "period_stars": "208 stars today", "language": "Rust",
     "url": "https://github.com/akitaonrails/ai-memory",
     "created_at": "2026-01-15T00:00:00Z", "description": "memory"},
    {"rank": 3, "full_name": "android/skills", "stars": 8200,
     "period_stars": "368 stars today", "language": "Python",
     "url": "https://github.com/android/skills",
     "created_at": "2026-09-20T00:00:00Z", "description": "skills"},
]
summaries = [
    {"rank": 1, "tagline": "给AI助手装的40倍速代码搜索",
     "summary": "还在挨个文件翻代码？XERJ是本地AI搜索工具，能自动索引代码、文档、日志和PDF。比grep快40倍。"},
    {"rank": 2, "tagline": "",  # 故意留空,测兜底提取
     "summary": "ai-memory解决AI编程助手的长期记忆问题。支持Claude Code、Cursor等平台共享记忆。"},
    {"rank": 3, "tagline": "Android官方出的AI技能库，专治LLM写不好的那部分",
     "summary": "Android官方推出的AI技能库。这些技能以SKILL.md文件的形式存在。"},
]

out = "/home/z/my-project/github-hot-heybox/output/smoke_test.png"
info = render_post_images("XERJ：AI搜索新方式，40倍效率提升",
                          repos, summaries, out, "daily")
print("\nbanner:", info["banner"], os.path.getsize(info["banner"]))
for c in info["cards"]:
    print("card:", c, os.path.getsize(c))
print("long:", info["long"], os.path.getsize(info["long"]))
