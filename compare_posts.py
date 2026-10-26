# -*- coding: utf-8 -*-
"""调查: 对比 [昨天22:17帖子] [今天09:39帖子] [GitHub实时trending] 三方数据"""
import json
import re
import sys
import datetime

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient

# 1) 今天发的10个项目
today_repos = ["xerj-org/xerj", "android/skills", "akitaonrails/ai-memory",
               "NandhaKishorM/laya", "Niko1221/Strata",
               "Ebony-Vinyl/dsh-our-free-model", "robbietilton/Compositor",
               "storytold/pdfcraft", "wheresryan22/anatomy", "openai/math"]

# 2) 拉昨天帖子 (link_id=194210321) 的正文
cfg = json.load(open("/home/z/my-project/github-hot-heybox/config.json"))
client = HeyboxClient(cfg["cookie"])

yesterday_repos = []
for path, params in [
    ("/bbs/app/api/link/info", {"link_id": "194210321"}),
    ("/bbs/app/author/concept/article/detail",
     {"link_id": "194210321", "article_type": "all"}),
]:
    try:
        data = client.get(path, params)
        s = json.dumps(data, ensure_ascii=False)
        if data.get("status") == "ok" and len(s) > 500:
            print(f"[帖子正文] {path} 拉取成功, 长度 {len(s)}")
            yesterday_repos = sorted(set(re.findall(
                r"github\.com/([\w.-]+/[\w.-]+)", s)))
            # 打印正文文字片段
            m = re.search(r'"text"\s*:\s*"([^"]{50,200})', s)
            break
    except Exception as e:
        print(f"[帖子正文] {path} 失败: {e}")

print(f"\n昨天帖子中出现的仓库 ({len(yesterday_repos)}):")
for r in yesterday_repos:
    in_today = "★也在今天帖里" if r in today_repos else ""
    print(f"  - {r} {in_today}")

overlap = [r for r in yesterday_repos if r in today_repos]
print(f"\n重叠: {len(overlap)}/{len(today_repos)}")
