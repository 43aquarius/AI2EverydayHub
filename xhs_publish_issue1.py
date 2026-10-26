#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小红书首次真实发布试验(2026-10-23 用户授权)

用户原话: "小红书你先试试你可不可以发布, 谨慎点, 你要是实在不行, 就我来发吧"

策略(谨慎优先):
- 内容: 第1期发布包成品(图片已VLM质检+用户可见, 行为完全可预期)
- 流程: publish_note() 与已生产验证的存草稿完全同链路,
  仅最后一步点「发布」而非「暂存离开」
- 纪律: 单次尝试不重试; 任何风控信号(二维码/风控词/滑块)立即中止;
  失败则第1期发布包仍在 download/, 用户可手动发布(2分钟)
"""
import json
import os
import re
import subprocess
import sys
import time

PACK = "/home/z/my-project/download/小红书发布包-第1期"
BASE = "/home/z/my-project/xhs-draft-poster"
SHOTS = "/home/z/my-project/output_preview/xhs_pub_20261023"
sys.path.insert(0, BASE)


def parse_pack(pack_dir: str):
    """解析发布包: 标题/正文/话题/图片顺序"""
    txt = open(os.path.join(pack_dir, "文案-复制粘贴用.txt"),
               encoding="utf-8").read()
    title = body = ""
    topics, images = [], []
    m = re.search(r"【标题】[^\n]*\n(.+)", txt)
    if m:
        title = m.group(1).strip()
    m = re.search(r"【正文】[^\n]*\n(.*?)\n【话题】", txt, re.S)
    if m:
        body = m.group(1).strip()
    m = re.search(r"【话题】\n(.+)", txt)
    if m:
        topics = [t.strip().lstrip("#") for t in m.group(1).split()
                  if t.startswith("#")]
    for mm in re.finditer(r"^\d+\.\s+(\S+\.jpe?g)$", txt, re.M):
        images.append(os.path.join(pack_dir, mm.group(1)))
    return title, body, topics, images


def save_state_pub(title, result, verify):
    """记录发布状态(state.json, 供后续期号/频率管理)"""
    sp = os.path.join(BASE, "state.json")
    state = {}
    if os.path.exists(sp):
        try:
            state = json.load(open(sp))
        except Exception:
            pass
    state.setdefault("publications", []).append({
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "title": title, "result": result, "verify": verify,
        "authorized": "2026-10-23 用户IM授权试验性发布",
    })
    with open(sp, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)


def main():
    os.makedirs(SHOTS, exist_ok=True)
    title, body, topics, images = parse_pack(PACK)
    print(f"[解析] 标题: {title}")
    print(f"[解析] 正文: {len(body)}字 | 话题({len(topics)}): {topics}")
    print(f"[解析] 图片: {len(images)}张: {[os.path.basename(i) for i in images]}")
    assert title and body and images, "发布包解析不完整"

    cfg = json.load(open(os.path.join(BASE, "config.json")))
    from xhs_client import XhsDraftClient
    client = XhsDraftClient(
        cfg["cookie"], headless=False, screenshot_dir=SHOTS,
        user_data_dir=os.path.join(BASE, "browser_profile"))

    xvfb = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1440x900x24"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    os.environ["DISPLAY"] = ":99"
    try:
        print("\n[发布] 浏览器自动化流程启动(单次尝试)...")
        result = client.publish_note(
            title, body, topics, images,
            on_step=lambda s: print(f"   [step] {s}"))
        print(f"\n[结果] {json.dumps(result, ensure_ascii=False)[:800]}")

        verify = {}
        if result.get("ok") and not result.get("risk"):
            print("\n[验证] 打开笔记管理页确认...")
            time.sleep(3)
            client2 = XhsDraftClient(
                cfg["cookie"], headless=False, screenshot_dir=SHOTS,
                user_data_dir=os.path.join(BASE, "browser_profile"))
            verify = client2.verify_published(title)
            print(f"[验证] {json.dumps(verify, ensure_ascii=False)[:300]}")

        save_state_pub(title, result, verify)

        print("\n" + "=" * 50)
        if result.get("risk"):
            print("⛔ 检测到风控信号, 已中止。发布包仍可用于手动发布:")
            print("   ", PACK)
        elif result.get("ok"):
            print("✅ 发布流程成功完成!")
            if verify.get("found"):
                print(f"   笔记管理页已见到本条 | 状态关键词: "
                      f"{verify.get('status_kw')}")
        else:
            print(f"❌ 未成功: {result.get('error') or result.get('detail')}")
            print("   发布包仍可用于手动发布:", PACK)
        print("截图目录:", SHOTS)
    finally:
        xvfb.terminate()


if __name__ == "__main__":
    main()
