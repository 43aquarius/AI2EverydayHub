# -*- coding: utf-8 -*-
"""测试: 小黑风格配图生成 + VLM 质检(用今日真实 AGI 新闻)"""
import json
import subprocess
import sys

PROMPT = """Generate one standalone 16:9 horizontal Chinese article illustration.

Visual DNA:
Pure white background. Minimalist black hand-drawn line art. Slightly wobbly pen lines. Lots of empty white space. Sparse red/orange/blue handwritten Chinese annotations. Clean absurd product-sketch feeling. No gradients, no shadows, no paper texture, no complex background, no commercial vector style, no PPT infographic look, no cute mascot poster, no children's illustration, no realistic UI.

Recurring IP character required:
小黑, a small solid-black absurd creature with white dot eyes, tiny thin legs, blank serious expression, slightly uneven hand-drawn body shape. 小黑 must perform the core conceptual action, not decorate the scene. Make 小黑 serious, deadpan, and slightly bizarre, not cute.

Theme:
一个816B参数的巨型开源模型,两台Mac桌面电脑就能完整运行

Structure type:
概念隐喻 conceptual metaphor

Core idea:
原本要整个数据中心才装得下的大模型,现在被压进两台小机器里跑起来了

Composition:
画面左侧画一个巨大的黑色立方体(代表816B大模型),小黑站在它顶上,用整个身体往下按压,把这个大立方体压进右侧两个并排的小纸箱里,两个小纸箱各冒出一缕细细的蒸汽表示正在努力运转;远处背景很小的位置画几栋小小的机房楼作对比。大部分画面留白。

Suggested elements:
巨大黑立方体 / 小黑向下按压 / 两个小纸箱 / 远处小机房

Chinese handwritten labels:
816B / 两台Mac / 能跑 / 机房失业了

Color use:
Black for main line art and 小黑. Orange for the pressing motion arrows. Red only for the tiny steam or key result. Blue only for the far small server buildings.

Constraints:
One image explains only one core structure. Keep the main subject around 40%-60% of the canvas. Preserve at least 35% blank white space. Use at most 5-8 short handwritten Chinese labels, each label only 2-8 Chinese characters. Do not write a title in the top-left corner. Do not write the structure type on the image. Do not make it a formal diagram, course slide, or dense explainer. It should be clear but not instructional, interesting but not childish, strange but clean."""

OUT = "/home/z/my-project/output_preview/test_xiaohei_01.png"

print("[1] 生成图片...")
r = subprocess.run(["z-ai", "image", "-p", PROMPT, "-o", OUT, "-s", "1344x768"],
                   capture_output=True, text=True, timeout=600)
print(r.stdout[-500:] if r.stdout else "", r.stderr[-300:] if r.stderr else "")
if r.returncode != 0:
    sys.exit(f"生图失败: {r.stderr[:500]}")

print("[2] VLM 质检...")
Q = ("这是一张中文文章配图,请逐项检查: "
     "1)背景是否纯白干净 2)是否有黑色实心小白点眼睛的小怪物角色,"
     "它是否在执行核心动作(按压方块)而非站着装饰 "
     "3)是否手绘线稿风格,不像PPT信息图 "
     "4)中文标注是否少而短且基本无错字 5)左上角是否有标题文字(不应有) "
     "6)留白是否充足。先给结论(合格/不合格),再简短列问题。")
r2 = subprocess.run(["z-ai", "vision", "-p", Q, "-i", OUT,
                     "-o", "/tmp/vlm_test.json"],
                    capture_output=True, text=True, timeout=300)
try:
    with open("/tmp/vlm_test.json") as f:
        data = json.load(f)
    print((data.get("choices") or [{}])[0].get("message", {}).get("content", ""))
except Exception as e:
    print("质检输出解析失败:", e, r2.stdout[-300:], r2.stderr[-300:])
