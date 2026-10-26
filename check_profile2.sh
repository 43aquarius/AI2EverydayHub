#!/bin/bash
# 用 document.cookie 设置父域 .xiaoheihe.cn 的 cookie(跨 api 子域生效), 再看个人主页
set -e

# 1. 生成设置 cookie 的 JS(从 config.json 解析)
python3 - > /tmp/set_cookies.js <<'EOF'
import json
cookie = json.load(open('/home/z/my-project/github-hot-heybox/config.json'))['cookie']
parts = []
for pair in cookie.split('; '):
    if '=' in pair:
        name, val = pair.split('=', 1)
        if name.startswith('.') or name in ('lang',):
            continue
        # 转义 JS 字符串里的引号
        val_js = val.replace('\\', '\\\\').replace("'", "\\'")
        parts.append(f"document.cookie = '{name}={val_js}; domain=.xiaoheihe.cn; path=/';")
print('\n'.join(parts))
print('document.cookie.length')
EOF

agent-browser open https://www.xiaoheihe.cn/ >/dev/null 2>&1
agent-browser wait --load networkidle >/dev/null 2>&1 || true
agent-browser eval "$(cat /tmp/set_cookies.js)" >/dev/null 2>&1
echo "cookies set on .xiaoheihe.cn"

# 2. 打开个人主页
agent-browser open "https://www.xiaoheihe.cn/app/user/74691929" >/dev/null 2>&1
agent-browser wait --load networkidle >/dev/null 2>&1 || true
agent-browser wait 4000 >/dev/null
echo "=== URL ==="
agent-browser get url
echo "=== 页面文本(前1500字) ==="
agent-browser eval "document.body ? document.body.innerText.slice(0, 1500) : 'NO BODY'" 2>/dev/null
