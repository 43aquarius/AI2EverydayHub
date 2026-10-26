#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VLM 分析小红书发布失败截图"""
import json
import subprocess

def vlm_check(image_path, question):
    out = "/home/z/my-project/logs/vlm_diag.json"
    cmd = ["z-ai", "vision", "-p", question, "-i", image_path, "-o", out]
    subprocess.run(cmd, capture_output=True, timeout=300, check=True)
    with open(out) as f:
        data = json.load(f)
    return (data.get("choices") or [{}])[0].get("message", {}).get("content", "")

D = "/home/z/my-project/output_preview/xhs_pub_20261023"
q = ("这是小红书创作者平台发布页截图。请描述: 1)图片上传区域状态"
     "(几张图/是否有上传中或处理中的遮罩进度条) 2)标题输入框是否已填"
     "3)正文编辑区是否可见、是否被弹窗或遮罩覆盖 4)页面底部按钮。"
     "简洁列出。")
for name in ("p05_images_uploaded", "p99_error"):
    print(f"===== {name} =====")
    try:
        print(vlm_check(f"{D}/{name}.png", q)[:600])
    except Exception as e:
        print("VLM失败:", e)
