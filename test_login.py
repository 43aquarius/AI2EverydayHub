# -*- coding: utf-8 -*-
"""测试1: 验证登录态 + 获取板块分类列表,寻找「盒友杂谈」"""
import json
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from heybox_client import HeyboxClient

with open("/home/z/my-project/github-hot-heybox/config.json") as f:
    cfg = json.load(f)

client = HeyboxClient(cfg["cookie"])

# 1. 验证登录态
print("=" * 60)
print("[1] 验证登录态 /bbs/app/user/message")
try:
    data = client.check_login()
    print("status:", data.get("status"))
    if data.get("status") == "ok":
        result = data.get("result") or {}
        print("登录态: OK ✓")
        # 打印部分结构
        print(json.dumps(result, ensure_ascii=False)[:500])
    else:
        print("登录态异常:", json.dumps(data, ensure_ascii=False)[:300])
except Exception as e:
    print("请求失败:", e)

# 2. 板块分类
print()
print("=" * 60)
print("[2] 板块分类 /bbs/app/topic/categories")
try:
    data = client.get_topic_categories()
    print("status:", data.get("status"))
    result = data.get("result") or {}
    # 遍历分类结构,寻找"盒友杂谈"
    def walk(obj, depth=0):
        if isinstance(obj, dict):
            name = obj.get("name") or obj.get("title") or obj.get("topic_name")
            tid = obj.get("topic_id") or obj.get("id")
            if name:
                print("  " * depth + f"- {name} (topic_id={tid})")
            for v in obj.values():
                if isinstance(v, (list, dict)):
                    walk(v, depth + (1 if name else 0))
        elif isinstance(obj, list):
            for item in obj:
                walk(item, depth)
    walk(result)
except Exception as e:
    print("请求失败:", e)
