# -*- coding: utf-8 -*-
"""Stage 4 升级版测试:年龄句+受众收尾句双清理"""
import sys
sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
import py_compile
py_compile.compile("/home/z/my-project/github-hot-heybox/summarizer.py",
                   doraise=True)
print("✓ 语法检查通过")

from summarizer import _post_dedupe

data = {"items": [
    # 1: 受众句(保留,第1处)
    {"rank": 1, "summary": "XERJ是个本地AI搜索工具,能自动索引代码、文档、日志和PDF文件。它用40倍于grep更少的token完成搜索,安装简单,一条命令就能完成索引和设置。经常需要在大代码库找代码的会喜欢这个工具。"},
    # 2: 受众句(保留,第2处)
    {"rank": 2, "summary": "ai-memory解决了AI编码助手长期记忆问题,用Rust编写。不同AI助手可以共享一个记忆库,实现工作交接,在Claude Code中完成任务后切换到Codex,新助手能立即知道之前的进度、失败点和待办事项。团队协作和使用多种AI助手的用户会需要这个。"},
    # 3: 无问题
    {"rank": 3, "summary": "Android官方推出的skills库是一组AI优化的模块化指令,帮助AI助手更好地理解和执行Android开发最佳实践。Android CLI可以安装特定技能,比如r8-analyzer,或者安装所有技能到检测到的代理目录。"},
    # 4: 年龄句(保留,第1处)
    {"rank": 4, "summary": "Laya是个多语言非自回归System 1决策引擎,支持100多种语言,单次前向传递完成类型化决策,仅需33毫秒。它通过强化学习针对严格proper scoring规则进行训练。29天前创建,已经有33222颗星。"},
    # 5: 受众句(第3处,保留)
    {"rank": 5, "summary": "Strata能在普通消费级硬件上运行Qwen3.8-Flash-Next模型,支持Windows和Linux系统,一键安装。性能测试显示,在RTX 5070上可以达到53-94 tokens/秒的输出速度。需要本地运行大模型但不想购买服务器的会喜欢这个工具。"},
    # 6: 受众句(第4处,应删)+年龄句(第2处保留)
    {"rank": 6, "summary": "dsh插件无需登录、注册或填写API Key,就能免费使用包括DeepSeek V4.1 Flash、Kimi K3在内的前沿模型。插件支持多种上游来源,透明度高,支持公告中心和实时推送。需要免费使用前沿大模型但不想处理复杂配置的会觉得实用。22天前创建的项目已经有20668颗星。"},
    # 7: 年龄句(第3处,保留)+受众句(第5处,应删)
    {"rank": 7, "summary": "Compositor是macOS上的免费开源Photoshop替代品,围绕合成和后期处理工作流设计。图层和文件夹管理、完整的混合模式、图层蒙版、调整层和图层效果它都包了,可以下载Xcode项目自由修改。30天前创建的项目已经积累了17259颗星。不想支付高昂价格的mac用户会喜欢这个工具。"},
    # 8: 年龄句(第4处,应删)+受众句(第6处,应删)
    {"rank": 8, "summary": "PdfCraft是用纯Rust从头编写的开源PDF阅读器和编辑器,可以在macOS、Windows、Linux、FreeBSD和Web上运行,提供阅读、组织、合并、分割和保护PDF的功能。需要处理PDF文件但不想使用Adobe Acrobat的会喜欢这个工具。17天前创建的项目已经有15249颗星。"},
]}
out = _post_dedupe(data)
print("\n处理后:")
for it in out["items"]:
    print(f"  [{it['rank']}] ({len(it['summary'])}字) ...{it['summary'][-40:]}")

checks = [
    ("会喜欢这个" in out["items"][0]["summary"], "第1条受众句应保留"),
    ("用户会需要这个" in out["items"][1]["summary"], "第2条受众句应保留"),
    ("会喜欢这个" in out["items"][4]["summary"], "第5条受众句应保留(第3处)"),
    ("觉得实用" not in out["items"][5]["summary"], "第6条受众句应删(第4处)"),
    ("mac用户会喜欢" not in out["items"][6]["summary"], "第7条受众句应删"),
    ("会喜欢这个" not in out["items"][7]["summary"], "第8条受众句应删"),
    ("29天前创建" in out["items"][3]["summary"], "第4条年龄句应保留(第1处)"),
    ("22天前创建" in out["items"][5]["summary"], "第6条年龄句应保留(第2处)"),
    ("30天前创建" in out["items"][6]["summary"], "第7条年龄句应保留(第3处)"),
    ("17天前创建" not in out["items"][7]["summary"], "第8条年龄句应删(第4处)"),
    (len(out["items"][7]["summary"]) > 80, "第8条删后不应过短"),
]
ok = True
for cond, msg in checks:
    if not cond:
        print(f"  ✗ {msg}")
        ok = False
assert ok
print("\n✓ 双清理测试通过:年龄句留3删1,受众句留3删3,无残篇")
