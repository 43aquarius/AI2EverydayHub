# -*- coding: utf-8 -*-
"""VLM 质检 4 套 AGI 主题预览图"""
import json
import subprocess
import sys


def vlm_check(image_path: str, question: str) -> str:
    cmd = ["z-ai", "vision", "-p", question, "-i", image_path,
           "-o", "/tmp/vlm_out.json"]
    subprocess.run(cmd, capture_output=True, timeout=300, check=True)
    with open("/tmp/vlm_out.json") as f:
        data = json.load(f)
    return (data.get("choices") or [{}])[0].get("message", {}).get("content", "")


Q = ("这是一张AI日报栏目的长图。请逐项检查: "
     "1)所有文字是否完整无截断无重叠 "
     "2)头部/统计条/新闻卡片/页脚的排版是否美观 "
     "3)TOP1-3卡片是否有焦点样式(渐变描边),其他卡片是否普通样式 "
     "4)分类标签chip和要点列表是否正常显示 "
     "5)整体配色是否协调。简短回答,先给结论(合格/不合格),再列问题。")

for theme in ["matrix", "ember", "ocean", "violet"]:
    img = f"/home/z/my-project/output_preview/agi_{theme}.png"
    print(f"\n===== 主题 {theme} =====")
    try:
        print(vlm_check(img, Q))
    except Exception as e:
        print("质检失败:", e)
