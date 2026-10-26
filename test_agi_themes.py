# -*- coding: utf-8 -*-
"""快速渲染 4 套 AGI 主题预览(模拟数据, 检查视觉)"""
import sys
sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from image_maker import render_agi_image

meta = {"date": "20261019", "title": "腾讯研究院AI速递 20261019"}
items = [
    {"num": 1, "headline": "Meta开源Muse Spark Open，两台Mac即可满血运行",
     "tagline": "开源界又丢下重磅炸弹", "category": "开源项目",
     "img_points": ["参数量405B,Mac双机可跑", "权重+训练代码全公开"]},
    {"num": 2, "headline": "ChatGPT接入Chrome，Work模式授权后可代人操作网页",
     "tagline": "浏览器变成AI的双手", "category": "产品发布",
     "img_points": ["需用户逐步授权操作", "先企业版灰度,周内开放"]},
    {"num": 3, "headline": "VAST开源实时渲染器EdenLive，单张5090帧率超24FPS",
     "tagline": "一张显卡撑起一个片场", "category": "研究突破",
     "img_points": ["单卡24帧,双卡近60帧", "几何场方案,开源可复现"]},
    {"num": 4, "headline": "DeepSeek V4.1 Flash新版上线，开放自研搜索API",
     "tagline": "便宜大碗还联网", "category": "大模型",
     "img_points": ["搜索API免费额度1000次", "推理成本再降四成"]},
    {"num": 5, "headline": "腾讯混元升级Hy Memory 2.0，三层全开源",
     "tagline": "记忆这个短板补上了", "category": "大模型",
     "img_points": ["模型+框架+应用全开源", "长文召回提升35%"]},
]
kws = ["开源", "大模型", "视频生成", "机器人"]

for theme in ["matrix", "ember", "ocean", "violet"]:
    out = f"/home/z/my-project/output_preview/agi_{theme}.png"
    render_agi_image("今天的AI圈: Meta开源405B模型,ChatGPT学会操作浏览器",
                     meta, items, out, keywords=kws, theme_key=theme)
print("done")
