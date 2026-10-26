# -*- coding: utf-8 -*-
"""VLM 质检图片(z-ai vision, 本地文件路径)"""
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

Q_BANNER = ("这是一张社区帖子的封面图。请检查:1)文字是否完整无截断无重叠 "
            "2)排版是否美观 3)有没有渲染错误(乱码/黑块/错位)。简短回答,先给结论(合格/不合格)。")

Q_CARD = ("这是帖子里的项目信息卡片图。请检查:1)文字是否完整无截断 "
          "2)深色背景与卡片是否协调 3)排名徽章/语言圆点/星数/标语/链接行是否都正常显示。"
          "简短回答,先给结论(合格/不合格)。")

if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else \
        "/home/z/my-project/github-hot-heybox/output/slices_smoke_test"
    for img, q, label in [
        (f"{base}/banner.png", Q_BANNER, "封面"),
        (f"{base}/card_01.png", Q_CARD, "卡片1"),
        (f"{base}/card_02.png", Q_CARD, "卡片2"),
    ]:
        print(f"\n===== {label} =====")
        try:
            print(vlm_check(img, q)[:500])
        except Exception as e:
            print("VLM失败:", e)
