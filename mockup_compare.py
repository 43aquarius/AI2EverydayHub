# -*- coding: utf-8 -*-
"""生成新旧版式对比预览图(模拟小黑盒App渲染):
- 旧版式: 整墙文字 + 长图垫底 (今天已发布的真实内容)
- 新版式: 封面图 + 图文交错 + 空行分段 (dry-run产物)
渲染规则按实测: 正文 white-space:break-spaces, 块间距12px, 16px字号
"""
import os
import re
import sys

BASE = "/home/z/my-project/github-hot-heybox"
NEW_MD = f"{BASE}/output/post_daily_20261017_155506.md"
OLD_MD = f"{BASE}/output/post_daily_20261017_140203.md"
NEW_SLICES = f"{BASE}/output/slices_trending_daily_20261017_155506"
LONG_IMG = f"{BASE}/output/trending_daily_20261017_155506.png"
OUT = "/home/z/my-project/download/预览-新旧版式对比.png"


def parse_new_md(md_path):
    """新md → [(kind, text/img_path)] (text保留内部换行结构)"""
    lines = open(md_path).read().splitlines()
    elems = []
    buf = []
    for ln in lines[1:]:  # 跳过标题
        m = re.match(r"^!\[配图\]\((.+)\)$", ln.strip())
        if m:
            if buf:
                elems.append(("text", "\n".join(buf).strip()))
                buf = []
            p = m.group(1)
            if not os.path.isabs(p):
                p = os.path.join(os.path.dirname(md_path), p)
            elems.append(("img", p))
        else:
            buf.append(ln)
    if buf:
        elems.append(("text", "\n".join(buf).strip()))
    return elems


def parse_old_md(md_path):
    """旧md → 每行一个text块 + 末尾长图"""
    content = open(md_path).read()
    # 去掉头部标题和尾部图片说明
    content = content.split("\n", 1)[1]
    content = content.split("\n---\n")[0]
    elems = []
    for ln in content.splitlines():
        if ln.strip():
            elems.append(("text", ln.strip()))
    elems.append(("img", LONG_IMG))
    return elems


def phone_html(label, elems, clip_note=""):
    body = []
    for kind, val in elems:
        if kind == "text":
            v = (val.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;"))
            body.append(f'<div class="blk">{v}</div>')
        else:
            body.append(f'<img class="pic" src="file://{val}">')
    note = (f'<div class="fade-note">{clip_note}</div>' if clip_note else "")
    return f"""
  <div class="phone">
    <div class="tag">{label}</div>
    <div class="screen">
      <div class="navbar">9:41</div>
      <div class="post">
        <div class="ptitle">{'XERJ：AI搜索新方式' if '旧' in label else 'XERJ：AI搜索新方式，单日新增1100星'}</div>
        <div class="meta">锝嘚得 · 盒友杂谈 · 今天</div>
        {''.join(body)}
        {note}
      </div>
    </div>
  </div>"""


html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#e8eaed; font-family:"Noto Sans SC","PingFang SC",
    "Microsoft YaHei",sans-serif; padding:28px; display:flex; gap:28px;
    align-items:flex-start; }}
  .phone {{ width:375px; flex-shrink:0; }}
  .tag {{ text-align:center; font-size:15px; font-weight:700; color:#333;
    margin-bottom:10px; }}
  .screen {{ background:#f5f6f7; border-radius:18px; overflow:hidden;
    box-shadow:0 2px 12px rgba(0,0,0,.12); }}
  .navbar {{ background:#fff; padding:8px 16px; font-size:12px; color:#333;
    border-bottom:1px solid #f0f0f0; }}
  .post {{ background:#fff; padding:14px 16px 22px; }}
  .ptitle {{ font-size:19px; font-weight:700; color:#1a1a1a;
    line-height:1.4; margin-bottom:6px; }}
  .meta {{ font-size:12px; color:#999; margin-bottom:14px; }}
  /* 模拟小黑盒正文: break-spaces + 块间距 */
  .blk {{ font-size:16px; color:#333; line-height:1.62;
    white-space:break-spaces; margin:6px 0; word-break:break-all; }}
  .pic {{ width:100%; border-radius:6px; margin:10px 0; display:block; }}
  .fade-note {{ text-align:center; color:#bbb; font-size:13px;
    padding:18px 0 4px; letter-spacing:1px; }}
</style></head><body>
{phone_html("旧版式(改版前)", parse_old_md(OLD_MD), "…… 长图之后没有内容了(整墙文字,图片只垫底一张)")}
{phone_html("新版式(改版后)", parse_new_md(NEW_MD), "…… 后面 6 个项目同样是「文字 + 卡片图」节奏,结尾是互动话题")}
</body></html>"""

tmp = "/tmp/mockup_compare.html"
with open(tmp, "w") as f:
    f.write(html)

from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 860, "height": 1200},
                            device_scale_factor=2)
    page.goto("file://" + tmp)
    page.wait_for_timeout(1200)
    # 等图片加载
    page.wait_for_function("() => [...document.images].every(i => i.complete)")
    page.wait_for_timeout(300)
    h = page.evaluate("document.body.scrollHeight")
    print("页面高度:", h)
    page.screenshot(path=OUT, full_page=True)
    browser.close()
print("已生成:", OUT)
