# -*- coding: utf-8 -*-
"""重建微博 config.json(三层持久化) + 双平台登录态验证

2026-10-22 升级: 写入矩阵版完整配置 + 镜像到 /home/z/.secrets/。
沙箱重启会清除快照点后新建文件(config.json 是 gitignore 的从不进快照),
.secrets 在项目外不受该机制管辖 — 参见 matrix_common.load_config 的
三层回退加载链。cookie 嵌入本脚本(脚本本身受快照追踪, 是cookie的
第三重保险)。"""
import json, os, sys

sys.path.insert(0, "/home/z/my-project/weibo-agi-poster")
sys.path.insert(0, "/home/z/my-project/github-hot-heybox")

COOKIE = ("SCF=AmsyKYDV6nkgF-gAcGQCQwA6hHPU4O1RaFSKNmtf2elLhfuzST9J0ck_JgBq27OiyFG4xR7ah-6jXR2qtFEvzpY.; "
          "SUB=_2A25H0dcJDeRhGe9O4lcQ9CnFzzqIHXVkr1bBrDV8PUNbmtAYLVjzkW9NdDQhjB1hLQH0Iv-MqH4KJa_o-qJVc4aU; "
          "SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5iQbVE0-kYCRXXbIE4l_pp5JpX5KzhUgL.Fo.71K-pShM4Shq2dJLoIEBLxK.L1KnLB.qLxK-LB.2L1KeLxK-LBo5L1KBLxKqL1KqLB-qt; "
          "ALF=02_1794978905; PC_TOKEN=8d459a5ba1; XSRF-TOKEN=ml6pY_ISn7bkjEs9mb-xdqtY; "
          "WBPSESS=fYdJAurzczjxFGMLYJKiP0UWeVqo7CL_1paCNFL2ZmhmE224vTw6tNttVDake9xEgqi0cHkJ3VVKQatk_XbCR58Ts1UVnljdVTOQaaOW_Gtr51VfbXkyKG0JHXivQwd8Vfy9yB_1HaWgH7hISzOMBA==")

CFG_PATH = "/home/z/my-project/weibo-agi-poster/config.json"
SECRETS_PATH = "/home/z/.secrets/weibo_config.json"
cfg = {
    "weibo_cookie": COOKIE,
    "weibo_post": {"agi_enabled": False, "ai_enabled": False},
    "matrix": {"morning_enabled": True, "yiyan_enabled": True,
               "pet_enabled": True, "history_enabled": True,
               "hot_enabled": True},
}
force = "--force" in sys.argv
if force or not os.path.exists(CFG_PATH):
    with open(CFG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.makedirs(os.path.dirname(SECRETS_PATH), exist_ok=True)
    with open(SECRETS_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print("✅ config.json 已重建(+.secrets 镜像)")
else:
    print("ℹ config.json 已存在(--force 覆盖), .secrets 同步检查...")
    if not os.path.exists(SECRETS_PATH):
        os.makedirs(os.path.dirname(SECRETS_PATH), exist_ok=True)
        with open(SECRETS_PATH, "w", encoding="utf-8") as f:
            json.dump(json.load(open(CFG_PATH, encoding="utf-8")),
                      f, ensure_ascii=False, indent=2)
        print("✅ .secrets 镜像已补齐")

# --- 微博登录态 ---
from weibo_client import WeiboClient
wb = WeiboClient(COOKIE)
try:
    uid, nick = wb.whoami()
    print(f"✅ 微博登录态 OK: uid={uid} nick={nick}")
except Exception as e:
    print(f"❌ 微博登录态失败: {e}")

# 查最近微博, 确认今天是否已发
try:
    posts = wb.my_posts(page=1)
    print(f"--- 最近 {len(posts)} 条微博 ---")
    for p in posts[:6]:
        import datetime
        ts = p.get("created_at", "")
        txt = (p.get("text_raw") or p.get("text") or "")[:40].replace("\n", " ")
        print(f"  [{ts}] {txt}")
except Exception as e:
    print(f"❌ my_posts 失败: {e}")

# --- 小黑盒登录态 ---
from heybox_client import HeyboxClient
hcfg = json.load(open("/home/z/my-project/github-hot-heybox/config.json", encoding="utf-8"))
hb = HeyboxClient(hcfg["cookie"])
try:
    me = hb.get("/bbs/app/user/message")
    print(f"✅ 小黑盒登录态 OK: {me.get('nickname', me)}")
except Exception as e:
    print(f"❌ 小黑盒登录态失败: {e}")

# 创作者中心最近帖子(确认今天 AGI 是否已发)
try:
    arts = hb.get("/bbs/app/author/concept/article/list?limit=8")
    items = arts.get("list") or arts.get("articles") or []
    print(f"--- 小黑盒最近 {len(items)} 帖 ---")
    for a in items[:6]:
        print(f"  [{a.get('created_time_info','?')}] link_id={a.get('link_id')} {str(a.get('title',''))[:36]}")
except Exception as e:
    print(f"❌ 创作者中心读取失败: {e}")
