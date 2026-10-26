#!/usr/bin/env python3
"""
解析 ima shareId 分享页面的 Remix turbo-stream SSR 数据。
页面无需登录即可访问，SSR 携带知识库最新条目的完整数据：
  title / introduction(全文Markdown) / sourcePath(微信原文) / updateTime / abstract 等。
"""
import re
import json
import sys
import urllib.request

URL = ("https://ima.qq.com/wiki/?shareId="
       "c2cfaed7f9378e4869a5588a339dc550a84a25382bd68b661843c6b7e432ce24")


def fetch_html(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def js_unescape(s):
    """按 JS 字符串字面量语义还原转义，保持非转义字符(含中文)原样"""
    def rep(mo):
        e = mo.group(1)
        if e == "n":
            return "\n"
        if e == "r":
            return "\r"
        if e == "t":
            return "\t"
        if e in ('"', "'", "\\"):
            return e
        if e == "b":
            return "\b"
        if e == "f":
            return "\f"
        if e.startswith("u"):
            return chr(int(e[1:], 16))
        if e.startswith("x"):
            return chr(int(e[1:], 16))
        return mo.group(0)
    return re.sub(r'\\(u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2}|.)', rep, s)


def extract_stream_data(html):
    """提取所有 enqueue 块并合并为 turbo-stream 数据数组"""
    chunks = re.findall(
        r'window\.__remixContext\.streamController\.enqueue\("(.*?)"\);',
        html, re.S)
    if not chunks:
        raise RuntimeError("页面中未找到 stream 数据")
    merged = []
    for c in chunks:
        inner = js_unescape(c)
        # inner 是一个 JSON 文本（字符串/数组）
        merged.append(json.loads(inner))
    # 第一个块是整个数组
    data = merged[0] if isinstance(merged[0], list) else merged
    return data


def turbo_decode(data):
    """
    解码 turbo-stream 扁平数组为 Python 对象。
    结构: 数组元素交替为 hint 对象与值; hint 的 {"_keyPos": valPos}
    表示 key=data[keyPos], value=递归解析 data[valPos];
    负值索引是类型标记(-5=string 等)。
    实测该页面: 字符串值直接跟在类型标记后一位。
    """
    memo = {}

    def decode_at(pos):
        if pos in memo:
            return memo[pos]
        if pos < 0 or pos >= len(data):
            return None
        val = data[pos]
        memo[pos] = None  # 防循环引用
        result = decode_val(val, pos)
        memo[pos] = result
        return result

    def decode_val(val, pos):
        if isinstance(val, dict):
            # hint 对象: 每个 "_N": M 表示 key=data[N], value 递归 data[M]
            out = {}
            for k, v in val.items():
                if not k.startswith("_"):
                    out[k] = v
                    continue
                try:
                    key_pos = int(k[1:])
                except ValueError:
                    continue
                key = data[key_pos] if 0 <= key_pos < len(data) else key_pos
                if isinstance(v, bool):
                    continue
                if isinstance(v, (int, float)) and v < 0:
                    # 负索引 = 类型标记，值跟在当前位置之后？
                    # 实测: {"_372":-5} 尾部的这类是 null/undefined 标记
                    continue
                out[key] = decode_at(v) if isinstance(v, int) else v
            return out
        if isinstance(val, (int, float)) and val == int(val) and val < 0:
            # 类型标记位，真正值在下一位
            nxt = pos + 1
            if 0 <= nxt < len(data):
                return data[nxt]
            return None
        return val

    # root hint 在 data[0]
    if data and isinstance(data[0], dict):
        return decode_at(0)
    return None


def find_entries_flat(data):
    """
    务实策略: 不完整解码, 直接在扁平数组上定位 key-value 对。
    观察规律: key("introduction") 后一位是它的字符串值。
    返回 {key: value} 的简单映射(重复 key 取第一个非空)。
    """
    out = {}
    for i, item in enumerate(data):
        if isinstance(item, str) and item and not item.startswith("http"):
            if i + 1 < len(data) and isinstance(data[i + 1], str) and data[i + 1]:
                # key -> value 模式(排除数字/对象)
                if re.match(r'^[a-zA-Z][a-zA-Z0-9_]{2,30}$', item) and len(data[i + 1]) > 0:
                    if item not in out or (not out[item] and data[i + 1]):
                        out[item] = data[i + 1]
    return out


def main():
    html = fetch_html(URL)
    print(f"页面大小: {len(html)} bytes")
    data = extract_stream_data(html)
    print(f"stream 数据块: {len(data)} 元素")

    # 尝试完整解码
    try:
        obj = turbo_decode(data)
        print("完整解码成功, 顶层键:", list(obj.keys()) if isinstance(obj, dict) else type(obj))
        loader = obj.get("loaderData") if isinstance(obj, dict) else None
        if isinstance(loader, dict):
            route = loader.get("routes/_index")
            if isinstance(route, dict):
                init = route.get("initData")
                if isinstance(init, dict):
                    print("initData 键:", list(init.keys()))
                    lst = init.get("list")
                    if isinstance(lst, list):
                        print(f"list 条目数: {len(lst)}")
                        for it in lst[:3]:
                            if isinstance(it, dict):
                                print("  -", it.get("title"), "|",
                                      (it.get("introduction") or "")[:60].replace("\n", " "))
    except Exception as e:
        print("完整解码失败:", e)

    # 兜底: 扁平 key-value 提取
    flat = find_entries_flat(data)
    print("\n== 扁平提取的关键字段 ==")
    for k in ["title", "introduction", "abstract", "sourcePath", "sourceName",
              "updateTime", "createTime", "timeWording"]:
        v = flat.get(k)
        if v:
            print(f"[{k}] {str(v)[:200]}")

    # 保存完整数据供后续分析
    with open("/home/z/my-project/ima-skill/share_stream.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("\n已保存 /home/z/my-project/ima-skill/share_stream.json")


if __name__ == "__main__":
    main()
