# -*- coding: utf-8 -*-
"""通过 GitHub Git Data API 上传项目(单次干净提交)

背景: 用户的 fine-grained PAT 走 git-over-HTTPS 返回 Repository not found
(未授权 git 通道),但 Contents/Git Data API 有写权限,改走 API。

流程: 为每个文件建 blob → 建 tree → 建 commit(根提交) → 强制移动 main 指针
(覆盖之前的权限测试提交,让仓库历史只有一次干净的初始提交)
"""
import base64
import json
import os
import subprocess
import sys

import requests

TOKEN = os.environ["GH_TOKEN"]
REPO = "43aquarius/GitHub2XiaoHeiHeEveryday"
API = f"https://api.github.com/repos/{REPO}"
HEADERS = {"Authorization": f"Bearer {TOKEN}",
           "Accept": "application/vnd.github+json"}
BASE = "/home/z/my-project/github-hot-heybox"
COMMIT_MSG = """GitHub热榜→小黑盒自动发帖机器人

- 双榜单(日榜/周榜) + 老项目过滤 + 新项目优先
- 五段式去AI味文案管线(260~360字/项目)
- HTML+Playwright 榜单长图渲染
- 小黑盒API完整逆向(hkey签名/COS直传/发帖)
- 常驻调度器(容器环境) + crontab支持
- 防重发 + dry-run安全模式"""


def api(method: str, path: str, payload: dict = None) -> dict:
    r = requests.request(method, API + path, headers=HEADERS,
                         json=payload, timeout=120)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"{method} {path} -> {r.status_code}: "
                           f"{r.text[:300]}")
    return r.json()


def main():
    # git ls-files -s: 遵循 .gitignore,带文件模式
    out = subprocess.run(
        ["git", "-c", "core.quotepath=false", "ls-files", "-s"], cwd=BASE,
        capture_output=True, text=True, check=True).stdout
    entries = []
    for line in out.strip().splitlines():
        meta, path = line.split("\t", 1)
        mode = meta.split()[0]  # 100644 / 100755
        entries.append((mode, path))
    print(f"待上传 {len(entries)} 个文件:")
    for _, p in entries:
        print("  -", p)

    # 1) blobs
    tree_items = []
    for mode, path in entries:
        fp = os.path.join(BASE, path)
        with open(fp, "rb") as f:
            content = base64.b64encode(f.read()).decode()
        blob = api("POST", "/git/blobs",
                   {"content": content, "encoding": "base64"})
        tree_items.append({"path": path, "mode": mode, "type": "blob",
                           "sha": blob["sha"]})
        print(f"  blob ok: {path} ({os.path.getsize(fp)//1024} KB)")

    # 2) tree(根提交,不带 base_tree)
    tree = api("POST", "/git/trees", {"tree": tree_items})
    print("tree:", tree["sha"])

    # 3) commit(无 parent → 根提交)
    commit = api("POST", "/git/commits",
                 {"message": COMMIT_MSG, "tree": tree["sha"]})
    print("commit:", commit["sha"])

    # 4) 移动 main(强制,覆盖权限测试产生的提交)
    try:
        api("PATCH", "/git/refs/heads/main",
            {"sha": commit["sha"], "force": True})
        print("main 指针已更新(force)")
    except RuntimeError as e:
        # main 分支可能不存在(测试提交后应存在;防御性处理)
        print("PATCH ref 失败,尝试创建:", e)
        api("POST", "/git/refs",
            {"ref": "refs/heads/main", "sha": commit["sha"]})

    # 5) 验证
    info = requests.get(API, headers=HEADERS, timeout=30).json()
    print(f"\n完成 ✓  default_branch={info.get('default_branch')} "
          f"size={info.get('size')}KB")
    print(f"仓库: https://github.com/{REPO}")
    files = requests.get(API + "/contents", headers=HEADERS,
                         timeout=30).json()
    print("根目录文件:", [f["name"] for f in files])


if __name__ == "__main__":
    main()
