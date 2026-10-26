# -*- coding: utf-8 -*-
"""真实发布: 将用户已确认的预览帖子(文案+长图)发布到小黑盒盒友杂谈
数据源: output/post_daily_20261017_140203.md (今天 14:02 生成的最终确认版)
"""
import json
import os
import re
import sys

BASE = "/home/z/my-project/github-hot-heybox"
sys.path.insert(0, BASE)

from heybox_client import HeyboxClient
from heybox_publisher import HeyboxPublisher

POST_MD = os.path.join(BASE, "output", "post_daily_20261017_140203.md")


def parse_preview(path):
    """从预览 md 解析 title / text / image_path"""
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    # 标题: 首行 "# xxx"
    m = re.match(r"^#\s+(.+)\n", raw)
    title = m.group(1).strip() if m else ""
    # 正文: 标题后 到 "---" 分隔线前
    body = raw[m.end():] if m else raw
    body = body.split("\n---\n")[0].strip()
    # 图片路径
    im = re.search(r"^图片:\s*(\S+)$", raw, re.M)
    image_path = im.group(1) if im else None
    return title, body, image_path


def parse_repos(text):
    """从正文解析 TOPn owner/name -> mark_posted 用"""
    repos = []
    for m in re.finditer(r"^TOP(\d+)\s+(\S+)", text, re.M):
        repos.append({"rank": int(m.group(1)), "full_name": m.group(2)})
    return repos


def main():
    title, text, image_path = parse_preview(POST_MD)
    assert title, "标题解析失败"
    assert image_path and os.path.exists(image_path), f"长图不存在: {image_path}"
    print(f"标题: {title}")
    print(f"正文: {len(text)} 字符, 项目数: {len(parse_repos(text))}")
    print(f"长图: {image_path} ({os.path.getsize(image_path)//1024} KB)")

    with open(os.path.join(BASE, "config.json")) as f:
        cfg = json.load(f)

    client = HeyboxClient(cfg["cookie"])
    if not client.check_login_ok():
        print("[错误] Cookie 失效, 终止")
        sys.exit(1)
    print("登录态: OK")

    publisher = HeyboxPublisher(client, topic_ids=str(cfg.get("topic_ids", "7214")))
    print("正在上传长图 + 发布帖子 ...")
    result = publisher.publish(
        title=title,
        content_text=text,
        image_paths=[image_path],
        dry_run=False)

    print("\n===== 发布结果 =====")
    print(json.dumps({k: v for k, v in result.items() if k != "raw"},
                     ensure_ascii=False, indent=2))
    raw = result.get("raw", {})
    if raw:
        print("raw keys:", list(raw.keys())[:20])
        print("raw 摘要:", json.dumps(raw, ensure_ascii=False)[:500])

    # 写入 state.json 防止今日重复发布(cron 明早再发新的一期)
    from main import mark_posted
    mark_posted("daily", result.get("post_url", ""), parse_repos(text))
    print("\nstate.json 已更新(今日 daily 已标记)")


if __name__ == "__main__":
    main()
