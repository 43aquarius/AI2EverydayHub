# -*- coding: utf-8 -*-
"""调试: project_post 的 LLM 生成为何解析不出 JSON"""
import json
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from github_trending import fetch_repo_meta, fetch_readme_excerpts
from summarizer import _call_llm, _STYLE_RULES, SYSTEM_PROMPT, _fmt_age
from project_post import _gen_prompt, build_repo

repo = build_repo("NanmiCoder/MediaCrawler", "多平台内容采集爬虫")
repo = fetch_readme_excerpts([repo])[0]
print("repo stars:", repo["stars"], "readme:", len(repo.get("readme_excerpt") or ""))

prompt = _gen_prompt(repo)
print("prompt 长度:", len(prompt))

raw = _call_llm(prompt, system=SYSTEM_PROMPT)
with open("/home/z/my-project/scripts/llm_raw_output.txt", "w") as f:
    f.write(raw)
print("输出长度:", len(raw))
print("=== 前 500 字 ===")
print(raw[:500])
print("=== 后 300 字 ===")
print(raw[-300:])
