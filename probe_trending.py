# -*- coding: utf-8 -*-
"""探测 GitHub Trending 全量候选 + 仓库元数据,为"老项目过滤"算法设计提供数据"""
import re
import html as html_module
import json
import time
from datetime import datetime, timezone

import requests

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
API = "https://api.github.com"


def fetch_page(since):
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    r = s.get("https://github.com/trending", params={"since": since}, timeout=30)
    r.raise_for_status()
    html = r.text
    out = []
    for art in re.findall(r'<article class="Box-row">(.*?)</article>', html, re.S):
        m = re.search(r'<h2[^>]*>\s*<a[^>]+href="/([^"]+)"', art, re.S)
        if not m:
            continue
        full_name = m.group(1).strip().strip("/")
        desc = ""
        md = re.search(r'<p class="col-9[^"]*">\s*(.*?)\s*</p>', art, re.S)
        if md:
            desc = html_module.unescape(re.sub(r"<[^>]+>", "", md.group(1))).strip()
        ml = re.search(r'itemprop="programmingLanguage">([^<]+)<', art)
        lang = ml.group(1).strip() if ml else ""
        ms = re.search(r'href="/[^"]+/stargazers[^"]*".*?</svg>\s*([\d,]+)', art, re.S)
        stars = int(ms.group(1).replace(",", "")) if ms else 0
        mp = re.search(r'([\d,]+)\s+stars\s+(today|this week|this month)', art)
        gained = int(mp.group(1).replace(",", "")) if mp else 0
        period = mp.group(2) if mp else ""
        out.append({"full_name": full_name, "lang": lang, "stars": stars,
                    "gained": gained, "period": period, "desc": desc[:80]})
    return out


def fetch_meta(full_name):
    r = requests.get(f"{API}/repos/{full_name}",
                     headers={"User-Agent": UA,
                              "Accept": "application/vnd.github+json"},
                     timeout=20)
    r.raise_for_status()
    d = r.json()
    return {"created_at": d.get("created_at", ""),
            "stars": d.get("stargazers_count", 0)}


def main():
    now = datetime.now(timezone.utc)
    for since in ("daily", "weekly"):
        repos = fetch_page(since)
        print(f"\n===== {since.upper()} trending: {len(repos)} 个候选 =====")
        print(f"{'#':>2} {'repo':<45} {'stars':>8} {'gained':>7} "
              f"{'ratio':>6} {'age_mo':>7} created")
        for i, r in enumerate(repos, 1):
            try:
                meta = fetch_meta(r["full_name"])
            except Exception as e:
                meta = {"created_at": "", "stars": r["stars"]}
                print(f"   [meta失败 {r['full_name']}: {e}]")
            time.sleep(0.35)
            total = meta["stars"] or r["stars"]
            created = meta["created_at"]
            age_mo = ""
            if created:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                age_mo = round((now - dt).days / 30.4, 1)
            ratio = round(r["gained"] / max(total, 1), 3) if r["gained"] else 0
            print(f"{i:>2} {r['full_name']:<45} {total:>8} {r['gained']:>7} "
                  f"{ratio:>6} {str(age_mo):>7} {created[:10]}  {r['desc'][:40]}")


if __name__ == "__main__":
    main()
