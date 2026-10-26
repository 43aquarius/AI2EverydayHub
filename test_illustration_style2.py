# -*- coding: utf-8 -*-
"""测试第2轮: 简化构图重生成"""
import json
import subprocess
import sys

PROMPT = """Generate one standalone 16:9 horizontal Chinese article illustration, hand-drawn sketch style.

Visual DNA:
Pure clean white background with absolutely no noise, no texture, no gray specks, no gradient. Minimalist black hand-drawn ink line art with slightly wobbly pen strokes. Lots of empty white space. Only a few short handwritten Chinese annotations in red/orange/blue. Absurd clean product-sketch feeling on white paper. No flat vector icons, no PPT infographic look, no commercial illustration, no cute mascot, no children style.

Recurring IP character required:
小黑: a small solid-black blob creature with two white dot eyes, tiny thin stick legs, blank deadpan serious expression, hand-drawn uneven round body. 小黑 must perform the core action of the picture, not stand aside. Serious, deadpan, slightly bizarre, NOT cute.

Theme:
巨型大模型被压缩进两台小电脑运行

Core idea:
816B参数的超大模型,居然在两台桌面小电脑上完整跑起来了

Composition:
Left side: a huge black cube drawn in rough hand-drawn outline, representing the giant model, with handwritten label "816B" beside it. Center: 小黑 stands on top of the huge cube, pushing it down with both arms, and the cube is being pressed down into two small cardboard boxes on the right side. The two small boxes have tiny legs and a few small sweat lines showing they are struggling but running. A small orange arrow flows from left cube into the two boxes. Handwritten label near the two boxes: "两台Mac". A red label with exclamation: "能跑!". Rest of canvas is empty white space.

Chinese handwritten labels (hand-drawn wobbly style, only these four):
816B / 两台Mac / 能跑! / 呜...

Color use:
Black ink for cube, boxes and 小黑. Orange for the one flow arrow. Red only for "能跑!". Blue only for "呜...".

Constraints:
One picture tells one idea. Main subject occupies about half the canvas, at least 40% pure white space. Do not draw any buildings, any servers, any city skyline. Do not write a title anywhere. Do not make it a diagram or flowchart. Strange but clean, clear but not instructional."""

OUT = "/home/z/my-project/output_preview/test_xiaohei_02.png"

print("[1] 生成图片...")
r = subprocess.run(["z-ai", "image", "-p", PROMPT, "-o", OUT, "-s", "1344x768"],
                   capture_output=True, text=True, timeout=600)
if r.returncode != 0:
    sys.exit(f"生图失败: {r.stderr[:500]}")

print("[2] VLM 质检...")
Q = ("这是一张中文文章配图,请逐项检查: "
     "1)背景是否纯白干净无噪点 2)是否有黑色实心、白点眼、细腿的小怪物,"
     "它是否在做核心动作(往下压方块) 3)是否手绘线稿风格,不像PPT/扁平矢量图 "
     "4)画面里是否只有816B/两台Mac/能跑/呜这几个中文标注且基本无错字 "
     "5)是否无标题、无楼房、无服务器、无城市剪影 6)留白是否充足。"
     "先给结论(合格/不合格),再简短列问题。")
r2 = subprocess.run(["z-ai", "vision", "-p", Q, "-i", OUT,
                     "-o", "/tmp/vlm_test.json"],
                    capture_output=True, text=True, timeout=300)
try:
    with open("/tmp/vlm_test.json") as f:
        data = json.load(f)
    print((data.get("choices") or [{}])[0].get("message", {}).get("content", ""))
except Exception as e:
    print("质检输出解析失败:", e, r2.stdout[-300:], r2.stderr[-300:])
