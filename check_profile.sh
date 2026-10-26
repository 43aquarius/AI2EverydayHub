#!/bin/bash
# 注入小黑盒 cookie 并打开个人主页, 检查发帖记录
set -e
CFG=/home/z/my-project/github-hot-heybox/config.json

agent-browser open https://www.xiaoheihe.cn/ >/dev/null
agent-browser wait --load networkidle >/dev/null 2>&1 || true

# 从 config.json 解析 cookie 并逐个注入
python3 - "$CFG" <<'EOF' > /tmp/cookie_cmds.sh
import json, sys, shlex
cookie = json.load(open(sys.argv[1]))["cookie"]
for pair in cookie.split("; "):
    if "=" in pair:
        name, val = pair.split("=", 1)
        if name.startswith("."):
            continue  # 缓存类 cookie 跳过
        print(f'agent-browser cookies set {shlex.quote(name)} {shlex.quote(val)}')
EOF
bash /tmp/cookie_cmds.sh

# 重新加载使 cookie 生效
agent-browser open https://www.xiaoheihe.cn/user/74691929 >/dev/null
agent-browser wait --load networkidle >/dev/null 2>&1 || true
agent-browser get url
agent-browser get title
