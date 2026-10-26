# -*- coding: utf-8 -*-
"""确认待发帖的 GitHub 自媒体运营项目清单(元数据查询)"""
import json
import urllib.request

API = "https://api.github.com"
HEADERS = {"User-Agent": "research", "Accept": "application/vnd.github+json"}


def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def pick(repo):
    try:
        d = get(f"{API}/repos/{repo}")
        lic = (d.get("license") or {}).get("spdx_id", "")
        return {
            "full_name": d["full_name"], "stars": d["stargazers_count"],
            "forks": d["forks_count"], "language": d.get("language"),
            "license": lic, "created_at": d.get("created_at", "")[:10],
            "pushed_at": d.get("pushed_at", "")[:10],
            "topics": d.get("topics", [])[:8],
            "desc": (d.get("description") or "")[:160],
            "archived": d.get("archived", False),
        }
    except Exception as e:
        return {"full_name": repo, "error": str(e)[:120]}


def search(q, n=4):
    try:
        d = get(f"{API}/search/repositories?q={urllib.request.quote(q)}&sort=stars&per_page={n}")
        out = []
        for it in d.get("items", []):
            out.append(f"    {it['full_name']} ★{it['stargazers_count']} — {(it.get('description') or '')[:70]}")
        return "\n".join(out) or "    (无结果)"
    except Exception as e:
        return f"    搜索失败: {e}"


# 1) 已知精确名称的
KNOWN = ["NanmiCoder/MediaCrawler", "dreammis/social-auto-upload"]
for r in KNOWN:
    info = pick(r)
    print(json.dumps(info, ensure_ascii=False))

# 2) 需要搜索确认的
for q in ["xhs_content_agent", "xhs_ai_publisher", "XHS_ALL_IN_ONE",
          "xhs-mcp in:name", "xhs-toolkit in:name", "xiaohongshu publisher",
          "xhs auto post"]:
    print(f"\n[SEARCH] {q}")
    print(search(q))
