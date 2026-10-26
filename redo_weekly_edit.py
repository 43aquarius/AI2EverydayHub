# -*- coding: utf-8 -*-
"""W43 周榜帖文案重生成 + 编辑(模板降级文案 → 全新 LLM 文案)

背景: 02:33 补发的周榜帖(194370432)因 LLM 服务抖动两次解析失败,
走了模板降级文案("X写的,已经N星"×10, 机械)。本脚本:
  1. 重抓 weekly trending(无 recent 惩罚, 与原帖同源)
  2. 校验仓库列表与原帖一致(≥8/10 匹配才继续)
  3. 完整三段式 LLM 文案管线 + 新长图渲染
  4. 通过编辑 API(edit=1) 替换帖子文字块与图片, 保留原帖 link_id
"""
import json
import os
import re
import sys

BASE = "/home/z/my-project/github-hot-heybox"
sys.path.insert(0, BASE)
os.chdir(BASE)

from github_trending import fetch_trending, enrich_details, fetch_readme_excerpts
from summarizer import summarize_repos
from image_maker import render_long_image
from main import build_post_segments, recent_repo_names
from heybox_client import HeyboxClient
from heybox_publisher import HeyboxPublisher, count_words

LINK_ID = "194370432"
POST_MD = "output/post_weekly_20261019_023444.md"

# 原帖仓库清单
orig_md = open(POST_MD, encoding="utf-8").read()
orig_names = set(re.findall(r"github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)",
                            orig_md))
print(f"原帖仓库: {len(orig_names)} 个")

# 1) 重抓(不传 recent, 保持与原帖同源)
print("\n[1/4] 重抓 weekly trending...")
repos = fetch_trending("weekly", top_n=10)
repos = enrich_details(repos)
new_names = {r["full_name"] for r in repos}
match = orig_names & new_names
print(f"   匹配 {len(match)}/{len(orig_names)}: {sorted(match)[:5]}...")
if len(match) < 8:
    print("   [中止] 榜单变化过大, 不宜原地换文案(原帖保持模板版)")
    sys.exit(1)
if len(match) < len(orig_names):
    missing = orig_names - new_names
    print(f"   [warn] 缺失: {missing} → 以新榜单为准继续")

# 2) README + LLM 三段式
print("\n[2/4] README 素材 + LLM 文案管线...")
repos = fetch_readme_excerpts(repos)
data = summarize_repos(repos, "weekly")
print(f"   新标题: {data['title']}")
lens = [len(it.get("summary") or "") for it in data["items"]]
print(f"   summary 长度 min{min(lens)}/avg{sum(lens)//len(lens)}/max{max(lens)}")

# 3) 新长图
print("\n[3/4] 渲染新长图...")
import datetime
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
image_path = os.path.join(BASE, "output", f"trending_weekly_redo_{ts}.png")
render_long_image(data["title"], repos, data["items"], image_path, "weekly")

# 4) 组装 blocks(上传新图) + 编辑提交
print("\n[4/4] 组装并编辑帖子...")
cfg = json.load(open("config.json"))
client = HeyboxClient(cfg["cookie"])
assert client.check_login_ok(), "Cookie 失效"
publisher = HeyboxPublisher(client, topic_ids=str(cfg.get("topic_ids", "7214")))

segments = build_post_segments(
    data["title"], data["intro"], repos, data["items"], "weekly",
    outro=data.get("outro", ""), long_path=image_path)
blocks, full_text = publisher._blocks_from_segments(segments)
print(f"   块数: {len(blocks)} "
      f"(文字 {sum(1 for b in blocks if b['type']=='text')} / "
      f"图片 {sum(1 for b in blocks if b['type']=='img')})")
assert any(b["type"] == "img" for b in blocks), "新图上传失败, 中止编辑"

desc = re.sub(r"\s", " ", data["intro"])[:80]
body = {
    "edit": "1",
    "link_id": LINK_ID,
    "link_tag": "27",
    "text": json.dumps(blocks, ensure_ascii=False),
    "title": data["title"],
    "desc": desc,
    "words_count": str(count_words(full_text)),
    "topic_ids": str(cfg.get("topic_ids", "7214")),
    "hashtags": "[]",
    "schedule_ts": "0",
    "view_limit": "1",
    "post_type": "1",
    "original": "1",
    "declaration": "0",
}

if "--go" not in sys.argv:
    print("\n[DRY] 预览模式。新文案前 3 块:")
    for b in blocks[:3]:
        if b["type"] == "text":
            print("---", b["text"][:150])
    print("...\n加 --go 真实编辑提交")
else:
    resp = client.post_form("/bbs/app/api/link/post", body)
    print("编辑结果:", json.dumps(resp, ensure_ascii=False)[:300])
    # 本地留档
    from main import segments_to_markdown
    with open(f"output/post_weekly_redo_{ts}.md", "w") as f:
        f.write(segments_to_markdown(data["title"], segments, "output"))
    print(f"文案留档: output/post_weekly_redo_{ts}.md")
