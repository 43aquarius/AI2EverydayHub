# -*- coding: utf-8 -*-
"""用 oneshot 模式重生成第1条配图(加强: 巨大黑立方体, 禁写实动物)"""
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from illustrator import make_illustrations

ITEMS = [{"num": n, "headline": f"新闻{n}", "summary": "x"} for n in range(1, 9)]
ITEMS[0] = {"num": 1, "headline": "Meta开源Muse Spark Open",
            "summary": "816B总参数42B激活, 两台M5 Ultra Mac Studio合计1TB内存就能完整运行, 同级模型首次上桌面"}

oneshot = {
    "after_num": 1,
    "theme": "巨型模型缩进桌面",
    "core_idea": "816B大模型被压进两台桌面小电脑完整运行",
    "scene": ("Left: a giant abstract BLACK CUBE drawn as simple wobbly ink outline "
              "with flat solid black fill, like a minimalist geometric block, NOT an "
              "animal, NOT a creature, no face, no fur, no realistic rendering. "
              "Center: the huge cube is being pushed down through a big hand-drawn "
              "funnel. Right: below the funnel stand two small cardboard boxes with "
              "tiny stick legs, the boxes are slightly bulging and sweating small "
              "drops, showing they struggle but hold. 小黑 stands beside the funnel "
              "pushing the cube down with both arms, deadpan serious face. "
              "A single orange arrow shows the cube flowing down through the funnel "
              "into the two boxes. Lots of white space around."),
    "labels": [
        {"text": "816B", "role": "subject"},
        {"text": "两台Mac", "role": "flow"},
        {"text": "能跑!", "role": "key"},
        {"text": "呜...", "role": "note"},
    ],
}

result = make_illustrations(
    "Meta开源816B模型，两台Mac就能跑", ITEMS,
    "/home/z/my-project/github-hot-heybox/output",
    prefix="agi_illus_edit_v2", max_count=1, oneshot=oneshot)
print("结果:", result)
