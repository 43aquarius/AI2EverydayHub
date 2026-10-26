# -*- coding: utf-8 -*-
"""API 发布文章帖测试: 验证 link_tag=11 + html 块的行内插图位置是否被保留

编码知识来自浏览器编辑器拦截:
  text = [{"type":"html","text":"<p>段1</p><p><img data-type=\"image\"
          data-original=\"URL\" data-width=\"W\" data-height=\"H\"
          data-description=\"\"></p><p>段2</p>"},
          {"type":"img","url":"URL","width":"W","height":"H"}]
  link_tag = 11 (文章), 必须带 topic_ids(分区), 否则报"请添加分区"
"""
import json
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient
from heybox_publisher import count_words

IMG = "https://imgheybox.max-c.com/web/bbs/2026/10/19/2c28482320a77aa6fb38270732747e4b.png"

html_text = (
    '<p>段落一:这张手绘图应该出现在本段和下一段之间。</p>'
    f'<p><img data-type="image" data-original="{IMG}" '
    f'data-width="1344" data-height="768" data-description=""></p>'
    '<p>段落二:如果你能看到这张图夹在两段文字中间,说明行内位置被保留了。</p>'
)

text_param = json.dumps([
    {"type": "html", "text": html_text},
    {"type": "img", "url": IMG, "width": "1344", "height": "768"},
], ensure_ascii=False)

body = {
    "link_tag": "11",
    "text": text_param,
    "title": "行内插图编码测试(稍后删除)",
    "desc": "段落一:这张手绘图应该出现在本段和下一段之间。",
    "words_count": "42",
    "topic_ids": "7214",
    "hashtags": "[]",
    "schedule_ts": "0",
    "view_limit": "1",
    "post_type": "1",
    "original": "1",
    "declaration": "0",
}

cfg = json.load(open("/home/z/my-project/github-hot-heybox/config.json"))
c = HeyboxClient(cfg["cookie"])

print("[1] 发布文章帖(带分区)...")
resp = c.post_form("/bbs/app/api/link/post", body)
print("   响应:", json.dumps(resp, ensure_ascii=False)[:300])

if resp.get("status") != "ok":
    sys.exit("发布失败")

print("\n[2] 取最新 link_id...")
link_id = ""
r = c.get("/bbs/app/author/concept/article/list", {
    "article_type": "all", "artilce_state": "all",
    "sort_filter": "create_at", "offset": "0", "limit": "3"})
links = (r.get("result") or {}).get("links") or []
if links:
    link_id = str(links[0].get("linkid") or "")
print("   link_id:", link_id or "(列表未返回, 手动查)")

if link_id:
    print("\n[3] edit/info 回读验证行内位置...")
    r2 = c.get("/bbs/app/link/edit/info", params={"link_id": link_id})
    blocks = json.loads(r2["result"]["link"]["text"])
    for i, b in enumerate(blocks):
        if b["type"] == "html":
            print(f"   [{i}] html: {b['text'][:200]}")
        else:
            print(f"   [{i}] {b['type']}: {str(b.get('url'))[:60]}")
    with open("/tmp/test_article_link_id.txt", "w") as f:
        f.write(link_id)
