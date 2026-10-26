#!/usr/bin/env python3
"""微信速递文章结构化提取：块级标签→换行，按中文序号章节切分新闻条目"""
import re
import json
import sys
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def html_unescape(s):
    for a, b in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'),
                 ("&#39;", "'"), ("&nbsp;", " "), ("&mdash;", "—"), ("&ndash;", "–")]:
        s = s.replace(a, b)
    return re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), s)


def extract_text(html):
    m = re.search(r'<div[^>]*id="js_content"[^>]*>(.*)</div>', html, re.S)
    body = m.group(1) if m else html
    # 块级结束标签 → 换行
    body = re.sub(r"</(p|section|div|h\d|li|blockquote)>", "\n", body)
    body = re.sub(r"<br[^>]*>", "\n", body)
    # 去标签
    body = re.sub(r"<[^>]+>", "", body)
    body = html_unescape(body)
    # 清理空行但保留单换行
    lines = [ln.strip() for ln in body.split("\n")]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


def split_sections(text):
    """按 中文数字、章节标题切分。速递格式: '一、标题' 后跟 1./2./3. 要点"""
    # 章节头: 行首中文数字+顿号 (一、二、...十二、)
    pat = re.compile(r"^([一二三四五六七八九十]{1,3})、(.{4,60})$")
    sections = []
    cur = None
    for ln in text.split("\n"):
        m = pat.match(ln)
        if m and len(m.group(2)) >= 4:
            if cur:
                sections.append(cur)
            cur = {"num": m.group(1), "title": m.group(2).strip(), "body": []}
        elif cur is not None:
            cur["body"].append(ln)
    if cur:
        sections.append(cur)
    return sections


def main():
    if len(sys.argv) > 1:
        html = open(sys.argv[1], encoding="utf-8").read()
    else:
        html = fetch("https://mp.weixin.qq.com/s?__biz=MjM5OTE0ODA2MQ==&mid=2650998937"
                     "&idx=1&sn=0976a52b46b2259c031b8cc7d462f254"
                     "&chksm=bcc847eb8bbfcefd18170a20d04f0961d345c3ae4d37fcf1a864c2ef7d6cf5b524a8e81750da"
                     "&cur_album_id=3349853949226418182&scene=189")
        with open("/tmp/wx_article.html", "w", encoding="utf-8") as f:
            f.write(html)
    text = extract_text(html)
    print(f"提取文本长度: {len(text)} 字, 行数: {text.count(chr(10))+1}")
    print("=== 前 25 行 ===")
    for ln in text.split("\n")[:25]:
        print(" |", ln[:100])
    sections = split_sections(text)
    print(f"\n=== 章节数: {len(sections)} ===")
    for s in sections:
        body = "\n".join(s["body"])
        print(f"\n【{s['num']}、{s['title']}】 body {len(body)}字")
        print(body[:150].replace("\n", " ⏎ "))
    # 保存
    with open("/tmp/wx_text.txt", "w", encoding="utf-8") as f:
        f.write(text)


if __name__ == "__main__":
    main()
