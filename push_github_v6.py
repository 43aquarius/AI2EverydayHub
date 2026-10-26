#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v6: ①仓库改名 GitHub2XiaoHeiHeiEveryday → AGI2iaoHeiHeiEveryday
    ②更新 description/homepage
    ③推送本轮: illustrator.py(新) + 文章模式发帖器 + 管线集成 + README/API文档"""
import json
import os
import re as _re
import subprocess
import tempfile
import time

OLD_REPO = "43aquarius/GitHub2XiaoHeiHeEveryday"
NEW_NAME = "AGI2iaoHeiHeiEveryday"
NEW_REPO = f"43aquarius/{NEW_NAME}"
BRANCH = "main"
BASE = "/home/z/my-project/github-hot-heybox"

_v2_src = open("/home/z/my-project/scripts/push_github_v2.py",
               encoding="utf-8").read()
_m = _re.search(r'TOKEN = \(\s*"(.+?)"\s*\n\s*"(.+?)"\s*\)', _v2_src)
assert _m, "无法从 push_github_v2.py 提取 TOKEN"
TOKEN = _m.group(1) + _m.group(2)


def gh(method, url, body=None):
    cmd = ["curl", "-s", "-X", method, url,
           "-H", f"Authorization: Bearer {TOKEN}",
           "-H", "Accept: application/vnd.github+json",
           "-H", "User-Agent: github2xiaoheihe-sync",
           "-H", "X-GitHub-Api-Version: 2022-11-28",
           "-w", "\n%{http_code}"]
    body_file = None
    if body is not None:
        with tempfile.NamedTemporaryFile("w", suffix=".json",
                                         delete=False) as tf:
            tf.write(json.dumps(body))
            body_file = tf.name
        cmd += ["-H", "Content-Type: application/json",
                "--data", "@" + body_file]
    try:
        for attempt in range(8):
            out = subprocess.run(cmd, capture_output=True, text=True,
                                 timeout=120)
            lines = out.stdout.rsplit("\n", 1)
            try:
                status = int(lines[1].strip())
            except (ValueError, IndexError):
                status = 0
            payload = {}
            if lines[0].strip():
                try:
                    payload = json.loads(lines[0])
                except json.JSONDecodeError:
                    payload = {}
            if 200 <= status < 300:
                return payload
            last_err = (f"HTTP {status}: "
                        f"{json.dumps(payload, ensure_ascii=False)[:200]}")
            if status in (400, 401, 403, 422) and "rate limit" not in last_err:
                raise RuntimeError(f"GitHub API 拒绝 {method} {url}: {last_err}")
            print(f"  [retry] 第{attempt+1}次 {status}, 12秒后重试...")
            time.sleep(12)
        raise RuntimeError(f"GitHub API 多次失败 {method} {url}: {last_err}")
    finally:
        if body_file:
            try:
                os.unlink(body_file)
            except OSError:
                pass


# ── ① 改名 + 资料 ─────────────────────────────────────────
print("== ① 仓库改名 ==")
repo = gh("GET", f"https://api.github.com/repos/{OLD_REPO}")
cur_name = repo.get("name")
if cur_name == NEW_NAME:
    print(f"  已经叫 {NEW_NAME}, 跳过改名")
    API = f"https://api.github.com/repos/{NEW_REPO}"
else:
    r = gh("PATCH", f"https://api.github.com/repos/{OLD_REPO}",
           {"name": NEW_NAME})
    print(f"  改名: {cur_name} → {r.get('name')} ✅")
    API = f"https://api.github.com/repos/{NEW_REPO}"

print("== ② 更新 description/homepage ==")
desc = ("AI 资讯自动运营机器人: 每天 09:30 AGI 日报 + 每周一 GitHub 周榜 | "
        "LLM 去AI味文案 + 小黑手绘行内配图 + 主题长图 + 文章模式自动发帖到小黑盒")
r = gh("PATCH", API, {"description": desc,
                      "homepage": "https://www.xiaoheihe.cn/"})
print(f"  description: {r.get('description', '')[:60]}...")
print(f"  url: {r.get('html_url')}")

# ── ③ 推送文件 ────────────────────────────────────────────
print("== ③ 推送代码 ==")
FILES = [
    "illustrator.py",       # 新增: 小黑手绘配图系统
    "heybox_publisher.py",  # 文章模式(行内插图) + delete_post
    "agi_news.py",          # 插图步骤 + 文章模式
    "main.py",              # 周榜插图 + 文章模式
    "config.example.json",  # illustrations 开关
    "README.md",            # 改名 + 新章节 + 致谢
    "API_RESEARCH.md",      # 文章编码/删帖API/渲染行为
]

ref = gh("GET", f"{API}/git/ref/heads/{BRANCH}")
parent_sha = ref["object"]["sha"]
parent = gh("GET", f"{API}/git/commits/{parent_sha}")
base_tree = parent["tree"]["sha"]
print(f"当前 {BRANCH}: {parent_sha[:10]} (tree {base_tree[:10]})")

tree_items = []
for rel in FILES:
    p = os.path.join(BASE, rel)
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    blob = gh("POST", f"{API}/git/blobs",
              {"content": content, "encoding": "utf-8"})
    tree_items.append({"path": rel, "mode": "100644", "type": "blob",
                       "sha": blob["sha"]})
    print(f"  blob: {rel} → {blob['sha'][:10]}")

tree = gh("POST", f"{API}/git/trees",
          {"base_tree": base_tree, "tree": tree_items})
print(f"新 tree: {tree['sha'][:10]}")

commit = gh("POST", f"{API}/git/commits", {
    "message": "小黑手绘配图系统 + 文章模式行内插图 + 仓库改名 AGI2iaoHeiHei\n\n"
               "- illustrator.py(新): 内化 helloianneo/ian-xiaohei-illustrations\n"
               "  skill(MIT, 已致谢) — LLM挑认知锚点→发明低科技隐喻→\n"
               "  1344x768生图→VLM质检(不合格重生成一次再跳过),\n"
               "  插图行内插入对应新闻/项目文字块后面\n"
               "- 逆向突破: 图文帖(27)的img块会被服务器归一化到文末;\n"
               "  文章帖(11)用 {type:html} 块+行内 <img data-*> 标签,\n"
               "  位置保留且渲染在文字中间(测试帖验证), 必须传 topic_ids\n"
               "- heybox_publisher: publish(article=True) 文章模式默认开,\n"
               "  _blocks_from_segments_article 组装器,\n"
               "  delete_post(/bbs/app/link/delete)\n"
               "- agi_news/main: [4.5]配图步骤, config illustrations 开关\n"
               "  (enabled/agi_max=3/weekly_max=2), 清理逻辑覆盖插图文件\n"
               "- 今日AGI帖已用文章模式重发: 行内图在第1/8条新闻后\n"
               "  (link_id=194383105), 旧图文帖已删\n"
               "- README: 新名/双栏目定位/配图系统/文章模式章节 + 致谢;\n"
               "  API_RESEARCH: 文章编码/删帖API/网页渲染行为补充",
    "tree": tree["sha"], "parents": [parent_sha]})
print(f"新 commit: {commit['sha'][:10]}")

gh("PATCH", f"{API}/git/refs/heads/{BRANCH}",
   {"sha": commit["sha"], "force": True})
print(f"✅ {BRANCH} 已更新 → {commit['sha'][:10]}")
print(f"https://github.com/{NEW_REPO}/commit/{commit['sha']}")
