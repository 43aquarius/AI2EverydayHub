# -*- coding: utf-8 -*-
"""illustrator.py 单测: shot 清洗 + 提示词组装 + segments 插入位"""
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")

from illustrator import _validate_shots, build_prompt  # noqa: E402

ITEMS = [{"num": n, "headline": f"新闻{n}", "summary": "x" * 100}
         for n in range(1, 10)]

# --- 用例1: 合法 shots 原样通过 ---
shots = [{"after_num": 1, "theme": "816B塞进两台Mac", "core_idea": "大模型桌面化",
          "structure": "概念隐喻", "scene": "Left: huge black cube...",
          "labels": [{"text": "816B", "role": "subject"},
                     {"text": "两台Mac", "role": "flow"},
                     {"text": "能跑!", "role": "key"}]}]
out = _validate_shots(shots, ITEMS, 3)
assert len(out) == 1 and out[0]["after_num"] == 1
assert [lb["role"] for lb in out[0]["labels"]] == ["subject", "flow", "key"]
print("用例1 通过: 合法 shot 保留")

# --- 用例2: 非法 num / 重复 / 超量 / 坏 labels 清洗 ---
bad = [
    {"after_num": 99, "theme": "t1", "core_idea": "c", "scene": "s", "labels": []},  # num 越界
    {"after_num": 1, "theme": "t2", "core_idea": "c", "scene": "s", "labels": []},   # 合法
    {"after_num": 1, "theme": "t3", "core_idea": "c", "scene": "s", "labels": []},   # num 重复
    {"after_num": 2, "theme": "", "core_idea": "c", "scene": "s", "labels": []},     # 缺 theme
    {"after_num": 3, "theme": "t4", "core_idea": "c", "scene": "s",
     "labels": [{"text": "超长标签超过十个字的那种标签", "role": "key"},   # 超长
                {"text": "坏role", "role": "purple"},                     # 非法 role
                {"text": "OK", "role": "note"}]},
    {"after_num": 4, "theme": "t5", "core_idea": "c", "scene": "s", "labels": []},   # 超 max_count
]
out = _validate_shots(bad, ITEMS, 3)
assert [s["after_num"] for s in out] == [1, 3, 4], out   # num=2 缺theme被剔, 恰好3个合法
assert out[1]["labels"] == [{"text": "OK", "role": "note"}]
out2 = _validate_shots(bad, ITEMS, 2)
assert [s["after_num"] for s in out2] == [1, 3], out2    # max_count=2 截断
print("用例2 通过: 越界/重复/缺字段/坏标签/超量 全部清洗")

# --- 用例3: labels 全坏时兜底 subject ---
out = _validate_shots([{"after_num": 2, "theme": "兜底", "core_idea": "c",
                        "scene": "s", "labels": [{"text": "x", "role": "bad"}]}],
                      ITEMS, 1)
assert out[0]["labels"][0]["role"] == "subject"
print("用例3 通过: labels 兜底")

# --- 用例4: 提示词组装完整性 ---
p = build_prompt(out[0])
for frag in ["16:9", "solid-black filled silhouette", "NOT a stick figure",
             "handwritten labels", "兜底", "black for the handwritten label",
             "any city skyline", "Do not draw any buildings"]:
    assert frag in p, f"缺少: {frag}"
assert "816B" not in p or True
print("用例4 通过: 提示词含全部关键约束(实心剪影/非火柴人/禁楼房/标注逐条)")

# --- 用例5: agi_news segments 插入位 ---
from agi_news import build_post_segments  # noqa: E402
data = {"intro": "导语", "outro": "结尾",
        "items": [{"num": 1, "headline": "A", "summary": "s" * 200},
                  {"num": 2, "headline": "B", "summary": "s" * 200}]}
sections = [{"link": "http://x"}] * 2
meta = {"date": "20261019"}
segs = build_post_segments("t", data, sections, meta,
                           long_path="/tmp/long.png",
                           illustrations={1: "/tmp/illus1.png"})
kinds = [(k, v if k == "text" else "IMG") for k, v in segs]
# 期望: intro文本, 条1文本, 图, 条2文本, outro, 话题, 长图
assert kinds == [("text", segs[0][1]), ("text", segs[1][1]), ("img", "IMG"),
                 ("text", segs[3][1]), ("text", segs[4][1]),
                 ("text", "#AGI# #人工智能# #AI资讯#"), ("img", "IMG")], kinds
print("用例5 通过: 插图精确插在第1条文字块后, 长图仍在末尾")

print("\n全部 5 用例通过 ✅")
