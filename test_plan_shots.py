# -*- coding: utf-8 -*-
"""测试 plan_shots: 用今日真实 AGI 新闻跑 LLM 规划(不生图)"""
import json
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from illustrator import plan_shots, build_prompt

ITEMS = [
    {"num": 1, "headline": "Meta开源Muse Spark Open",
     "summary": "美国最强开源权重模型816B总参数42B激活,支持100万token,两台M5 Ultra Mac Studio合计1TB内存就能完整运行,同级首次上桌面,编程能力落后Kimi K3和GLM 5.3"},
    {"num": 2, "headline": "ChatGPT Chrome版能代人操作网页",
     "summary": "OpenAI把ChatGPT接入Chrome,跨标签页收集信息比较商品,Work模式授权后能发消息填表下载文件,还能把多标签页汇总成比价表"},
    {"num": 3, "headline": "VAST开源实时渲染器EdenLive",
     "summary": "用参考画面生成写实或风格化画面,单张RTX 5090就能跑,5B参数720P实时帧率超24FPS,端到端延迟百毫秒量级"},
    {"num": 4, "headline": "DeepSeek V4.1 Flash新版上线",
     "summary": "1017版本基准大幅提升,性能-费用帕累托最优,自反馈强化学习,少量提示完成故宫3D建模、传送门2复刻,搜索API每千次5元"},
    {"num": 5, "headline": "腾讯混元升级Hy Memory 2.0",
     "summary": "智能体记忆框架,新增工作与代码记忆,4个Benchmark开源第一,3B激活参数得分55.49超Opus5,接入自选股多跳召回率50%到90%"},
    {"num": 6, "headline": "可灵4.0上线原生30秒视频",
     "summary": "单次原生生成最长30秒,强化高速运动稳定性,全能参考单次组合15项素材,10张关键帧控制人物状态,续拍延展至2分钟"},
    {"num": 7, "headline": "英伟达开源机器人框架ASPIRE",
     "summary": "编程Agent为机器人写控制程序,根据多模态轨迹复盘失败改代码,技能库90多项Skill覆盖150多个任务,LIBERO-Pro成功率99%"},
    {"num": 8, "headline": "Anthropic:2030年AI将承担95%工作",
     "summary": "员工认为四年后AI做完75%工作,美国劳动者平均只认为28%,Agent工时已达人类6倍,研究部门19倍,预计2030年底95%"},
]

shots = plan_shots("Meta开源816B模型，两台Mac就能跑", ITEMS, max_count=3)
print(f"\n规划出 {len(shots)} 张:")
for s in shots:
    print(f"\n=== 第{s['after_num']}条后 | {s['theme']} ===")
    print(f"结构: {s['structure']}")
    print(f"核心: {s['core_idea']}")
    print(f"画面: {s['scene'][:120]}")
    print(f"标注: {[(lb['text'], lb['role']) for lb in s['labels']]}")

if shots:
    print("\n--- 第1张的完整生图提示词(前600字) ---")
    print(build_prompt(shots[0])[:600])
