# -*- coding: utf-8 -*-
"""发布单项目安利帖: XiaomingX/ai-money-maker-handbook(含事实修正)

干跑发现的 LLM 事实错误, 发布前确定性修正:
  ①"443+个实操案例" — 实为《程序员的副业赚钱宝典》连载到第446章
    (章号被误读成数量)
  ②"项目分三大块(含跨境出海技术栈)" — 跨境技术栈是外链的姊妹仓库
    indie-hacker-tools-plus, 非本仓库内容
"""
import datetime
import json
import os
import sys

sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
import project_post as pp
from heybox_client import HeyboxClient
from heybox_publisher import HeyboxPublisher
from image_maker import render_project_poster

REPO = "XiaomingX/ai-money-maker-handbook"
NOTE = "AI副业赚钱思路大合集"
BASE = "/home/z/my-project/github-hot-heybox"

# ---------------- 事实修正(确定性, 逐字替换) ----------------
FIX_POINTS = {
    "提供443+个AI副业实操案例，包含具体部署和盈利模式":
        "《程序员副业宝典》连载中，最新更新到第446章",
    "跨境电商全流程指南，支付合规与税务避坑":
        "31篇初创商业课连载，融资轮次到支付合规都讲",
}
FIX_BODY = {
    "项目分三大块：自媒体流量、跨境出海技术栈和AI搞钱原则手册。自媒体部分教你用AI做内容，跨境部分覆盖从融资到支付的全流程，原则手册则是搞钱心法。":
        "主体是思路合集：起步阶段的四条建议、写给0-1岁初创合伙人的三十多篇商业课、连载中的程序员副业宝典，外加自媒体、图片、文案、音频、直播几大类AI玩法清单。仓库还外链了一批姊妹项目，比如跨境出海技术栈和1000个中国独立开发者项目，作者把整套独立开发资源都串起来了。",
    # 生成变体: 禁用句式“最近发现”/拔高语“商业知识体系”微调
    "最近发现一个宝藏GitHub项目，专门收集用AI搞副业的思路和方法。这个合集已经6243颗星了，里面全是能直接上手的实操案例。":
        "GitHub上有个专门收集AI副业思路的合集，星数已经攒到6243，里面全是能直接上手的实操案例。",
    "从MAU指标、ARR、PMF基础概念，到LTV/CAC模型、股权设计、出海合规等高级话题，帮你建立完整的商业知识体系。":
        "从MAU指标、ARR、PMF基础概念，到LTV/CAC模型、股权设计、出海合规等高级话题，写得都挺细。",
}


def apply_fixes(content: dict) -> dict:
    for i, p in enumerate(content.get("points") or []):
        for bad, good in FIX_POINTS.items():
            if bad in p:
                print(f"[修正] points[{i}]: {bad[:24]}… → {good[:24]}…")
                content["points"][i] = good
    body = content.get("body") or ""
    for bad, good in FIX_BODY.items():
        if bad in body:
            print(f"[修正] body 段落: {bad[:24]}… → {good[:24]}…")
            body = body.replace(bad, good)
    content["body"] = body
    return content


def main():
    real = "--real" in sys.argv
    cfg = json.load(open(os.path.join(BASE, "config.json"), encoding="utf-8"))

    repo = pp.build_repo(REPO, NOTE)
    repo["readme_excerpt"] = pp.fetch_readme_robust(REPO)
    print(f"★{repo['stars']} {repo['language']} 协议:{repo['license'] or '未标注'} "
          f"README {len(repo.get('readme_excerpt') or '')}字")

    # 内容缓存: dry-run 审定后 --real 直接复用(所见即所发), --regen 强制重生成
    cache_path = os.path.join(BASE, "output", "ammh_content.json")
    content = None
    if real and not "--regen" in sys.argv and os.path.exists(cache_path):
        content = json.load(open(cache_path, encoding="utf-8"))
        print(f"[缓存] 复用已审定文案: {cache_path}")
    if content is None:
        content = pp.generate_content(repo)
        if not content:
            print("LLM 失败")
            return 1
        content = apply_fixes(content)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(content, f, ensure_ascii=False, indent=1)
    print("标题:", content["title"])
    print("正文", len(pp._clean(content.get("body", ""))), "字")

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    poster_path = os.path.join(BASE, "output",
                               f"project_ai-money-maker-handbook_{ts}.png")
    try:
        render_project_poster(repo, content, poster_path)
    except Exception as e:
        print(f"[warn] 海报渲染失败: {e}")
        poster_path = None

    segments = pp.build_segments(repo, content, poster_path)

    if not real:
        preview = os.path.join(BASE, "output",
                               f"project_post_ammh_{ts}.md")
        with open(preview, "w", encoding="utf-8") as f:
            f.write(f"# {content['title']}\n\n")
            for kind, val in segments:
                if kind == "text":
                    f.write(val + "\n\n")
                else:
                    f.write(f"![海报]({os.path.basename(val)})\n\n")
        print("预览:", preview)
        print("--- 最终文案 ---")
        print("标题:", content["title"])
        for kind, val in segments:
            if kind == "text":
                print(val + "\n")
        return 0

    client = HeyboxClient(cfg["cookie"])
    if not client.check_login_ok():
        print("Cookie 失效!")
        return 1
    publisher = HeyboxPublisher(client, topic_ids=str(cfg.get("topic_ids", "7214")))
    result = publisher.publish(title=content["title"], segments=segments)
    link = result.get("post_url", "")
    print("原始响应:", json.dumps(result.get("raw_resp") or {},
                                  ensure_ascii=False)[:500])
    print("✅ 发布成功:", link)

    state = pp.load_state()
    state.setdefault("project_posts", {})[REPO] = {
        "date": datetime.date.today().isoformat(),
        "url": link, "title": content["title"]}
    pp.save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
