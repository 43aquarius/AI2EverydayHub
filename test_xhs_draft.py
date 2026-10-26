#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小红书存草稿全流程实测(第一期正式草稿)

xvfb有头模式 → 创作者平台发布页 → 传6张卡 → 填标题正文话题
→ 点「存草稿」(绝不点发布) → 四层hook验证
"""
import json, os, subprocess, sys, time
sys.path.insert(0, "/home/z/my-project/xhs-draft-poster")

# 启动Xvfb
xvfb = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1440x900x24"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.5)
os.environ["DISPLAY"] = ":99"

from xhs_client import XhsDraftClient

# 用刚生成的内容
copy_ = json.load(open("/tmp/xhs_issue_copy.json")) if os.path.exists("/tmp/xhs_issue_copy.json") else None
if not copy_:
    # 重新准备(不重复拉star/LLM, 用固定第一期内容)
    from content_maker import prepare_issue, ISSUE_1
    issue = prepare_issue()
    copy_ = issue["copy"]

import glob
images = sorted(glob.glob("/home/z/my-project/xhs-draft-poster/output/xhs_*_20261022_172650.jpg"))
print(f"图片 {len(images)} 张")

cfg = json.load(open("/home/z/my-project/xhs-draft-poster/config.json"))
client = XhsDraftClient(cfg["cookie"], headless=False)

def progress(step):
    print(f">>> 进度: {step}")

try:
    result = client.save_draft(
        title=copy_["title"],
        body=copy_["body"],
        topics=[t.lstrip("#") for t in copy_["topics"]],
        image_paths=images,
        on_step=progress)
    print("=== 结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=1)[:500])
finally:
    xvfb.terminate()
