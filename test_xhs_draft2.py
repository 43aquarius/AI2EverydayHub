#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小红书存草稿端到端实测 v2(shadow已突破, TipTap选择器已修正)"""
import json, os, subprocess, sys, time
sys.path.insert(0, "/home/z/my-project/xhs-draft-poster")

xvfb = subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1440x900x24"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.5)
os.environ["DISPLAY"] = ":99"

from xhs_client import XhsDraftClient
import glob

# 复用已有文案(有缓存用缓存, 没有就现生成)
cache = "/tmp/xhs_issue_copy.json"
if os.path.exists(cache):
    copy_ = json.load(open(cache))
else:
    from content_maker import prepare_issue
    copy_ = prepare_issue()["copy"]
    json.dump(copy_, open(cache, "w"), ensure_ascii=False)

images = sorted(glob.glob("/home/z/my-project/xhs-draft-poster/output/xhs_*_20261022_17*.jpg"))
print(f"标题: {copy_['title']}")
print(f"图片: {len(images)} 张")

cfg = json.load(open("/home/z/my-project/xhs-draft-poster/config.json"))
client = XhsDraftClient(cfg["cookie"], headless=False)

try:
    result = client.save_draft(
        title=copy_["title"],
        body=copy_["body"],
        topics=[t.lstrip("#") for t in copy_["topics"]],
        image_paths=images,
        on_step=lambda s: print(f">>> {s}"))
    print("=== 结果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=1)[:600])
finally:
    xvfb.terminate()
