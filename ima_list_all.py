#!/usr/bin/env python3
"""翻页拉取 AGI 数据库知识库全部条目，按标题日期找最新一期"""
import json
import subprocess
import re
import sys

SKILL = "/home/z/my-project/ima-skill/extracted/ima-skill/ima_api.cjs"
KB_ID = "oalGkoohPXOk8tv7vD1O0c-ughzb3qF2Nz1TYCWEv-Q="


def call_api(path, body):
    r = subprocess.run(
        ["node", SKILL, path, json.dumps(body, ensure_ascii=False)],
        capture_output=True, text=True, timeout=60,
    )
    if r.returncode != 0:
        raise RuntimeError(f"API 调用失败: {r.stderr.strip()}")
    return json.loads(r.stdout)


def main():
    cursor, items = "", []
    while True:
        data = call_api("openapi/wiki/v1/get_knowledge_list", {
            "knowledge_base_id": KB_ID, "cursor": cursor, "limit": 50})
        if data.get("code") != 0:
            print("业务错误:", data)
            sys.exit(1)
        d = data["data"]
        items.extend(d.get("knowledge_list", []))
        if d.get("is_end") or not d.get("next_cursor"):
            break
        cursor = d["next_cursor"]

    print(f"总条目数: {len(items)}")
    # 提取带日期的速递条目
    dated = []
    for it in items:
        m = re.search(r"AI速递\s*(\d{8})", it.get("title", ""))
        if m:
            dated.append((m.group(1), it["title"], it["media_id"]))
    dated.sort(reverse=True)
    print(f"速递条目数: {len(dated)}")
    print("最新 10 期:")
    for date, title, mid in dated[:10]:
        print(f"  {date}  {title}  -> {mid}")

    # 其他非速递条目也看看
    others = [it for it in items if not re.search(r"AI速递\s*\d{8}", it.get("title", ""))]
    print(f"\n非速递条目数: {len(others)}")
    for it in others[:15]:
        print(f"  [{it.get('media_type')}] {it['title']}")

    # 保存全量供后续使用
    with open("/home/z/my-project/ima-skill/agi_kb_items.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    if dated:
        latest = dated[0]
        with open("/home/z/my-project/ima-skill/agi_latest.json", "w", encoding="utf-8") as f:
            json.dump({"date": latest[0], "title": latest[1], "media_id": latest[2]},
                      f, ensure_ascii=False, indent=2)
        print(f"\n最新一期: {latest[0]} {latest[1]}")


if __name__ == "__main__":
    main()
