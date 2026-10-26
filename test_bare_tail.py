# -*- coding: utf-8 -*-
"""无谓语收尾句检测验证"""
import sys, re
sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
import py_compile
py_compile.compile("/home/z/my-project/github-hot-heybox/summarizer.py",
                   doraise=True)
print("✓ 语法检查通过")

from summarizer import _detect_repetition, _post_dedupe

# 上轮实际问题: TOP6/TOP7 无谓语收尾
items = [
    {"rank": 1, "summary": "还在挨个文件翻代码?XERJ帮你搞定,自动索引代码、文档、日志和PDF文件。安装简单,一条命令即可完成索引。"},
    {"rank": 2, "summary": "ai-memory解决不同AI编程助手间的记忆共享问题,切换工具时能交接工作进度、失败原因和待办事项。"},
    {"rank": 3, "summary": "Android官方推出的AI技能库,帮助AI助手更好地理解和执行Android开发最佳实践。"},
    {"rank": 4, "summary": "Laya是个多语言决策引擎,单次前向传递33毫秒,支持100多种语言。"},
    # TOP6 上轮原文(无谓语收尾)
    {"rank": 6, "summary": "Ebony-Vinyl的dsh插件让你无需登录就能使用前沿模型,完全免费且不限量。插件支持公共网关,选择器只广播可用模型,还带有公告中心和实时推送功能。免费使用前沿模型的用户,特别是那些不想在各种平台间切换的人。"},
    # TOP7 上轮原文(无谓语收尾)
    {"rank": 7, "summary": "Photoshop的订阅费又涨了?Compositor是Mac平台上的免费开源替代品,围绕合成和后期处理工作流设计,提供图层和文件夹、混合模式、图层蒙版、调整图层和图层效果等功能。需要图像编辑但不想支付高昂价格的设计师和创意工作者。"},
    # TOP8 正常(有谓语"可以用它")
    {"rank": 8, "summary": "PdfCraft是用纯Rust从头编写的开源PDF阅读器和编辑器,支持多个平台。经常跟PDF打交道的,可以用它批量合并、加密。"},
    # TOP9 正常(有谓语"可以查看")
    {"rank": 9, "summary": "OpenAI的math项目包含719篇手稿,组织成372个相关论文家族。数学研究者和对AI数学能力感兴趣的开发者,可以查看不同验证阶段的结果。"},
    # 正常名词结尾但有谓语
    {"rank": 10, "summary": "Magpie是个模型管理工具,可以从菜单栏切换不同的AI助手。经常用多个AI助手的,可以简化模型和账户管理。"},
]
f = _detect_repetition(items)
found = [p for p, _ in f if "无谓语" in p]
print("检测:", found)
assert found, "无谓语句未检出"

out = _post_dedupe({"items": items})
t6 = out["items"][4]["summary"]
t7 = out["items"][5]["summary"]
assert "特别是那些" not in t6, "TOP6 无谓语句未删"
assert "创意工作者" not in t7, "TOP7 无谓语句未删"
assert "可以用它批量合并" in out["items"][6]["summary"], "TOP8 正常句误删"
assert "可以查看" in out["items"][7]["summary"], "TOP9 正常句误删"
assert "可以简化" in out["items"][8]["summary"], "TOP10 正常句误删"
print(f"\nTOP6 删后: ...{t6[-35:]}")
print(f"TOP7 删后: ...{t7[-35:]}")
print("✓ 无谓语句:检出并删除,正常句零误伤")
