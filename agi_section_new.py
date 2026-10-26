# ---------------------------------------------------------------------------
# AGI 日报长图(agi_news.py 用) — 四套主题按期号轮换 + 富信息卡片
# ---------------------------------------------------------------------------

# 主题色板: 每天轮换, 保持栏目 logo/版式不变但整体气质有变化
AGI_THEMES = {
    "ember": {   # 炉火橙(GitHub Dark 风)
        "bg": "#0d1117", "card_bg": "#161b22", "card_border": "#30363d",
        "hd_grad": "linear-gradient(135deg, #161b22 0%, #1c2431 55%, #26304a 100%)",
        "accent": "#ff7d29", "accent_rgb": "255,125,41",
        "title": "#f0f6fc", "text": "#e6edf3", "dim": "#8b949e",
        "glow2": "rgba(63,114,175,0.16)", "chip_bg": "#0d1117",
        "focus_badge": "#FFD700",
    },
    "ocean": {   # 深海青
        "bg": "#0a1424", "card_bg": "#101d33", "card_border": "#233b5c",
        "hd_grad": "linear-gradient(135deg, #0e1c31 0%, #12294a 55%, #16355f 100%)",
        "accent": "#38bdf8", "accent_rgb": "56,189,248",
        "title": "#f0f7ff", "text": "#dbe9f8", "dim": "#7e93b0",
        "glow2": "rgba(14,165,164,0.14)", "chip_bg": "#0a1424",
        "focus_badge": "#7dd3fc",
    },
    "violet": {  # 星云紫
        "bg": "#120f1d", "card_bg": "#1a1528", "card_border": "#342a4d",
        "hd_grad": "linear-gradient(135deg, #181227 0%, #241a3d 55%, #2f2350 100%)",
        "accent": "#b197fc", "accent_rgb": "177,151,252",
        "title": "#f5f2ff", "text": "#e6dff7", "dim": "#9a8bb5",
        "glow2": "rgba(244,114,182,0.13)", "chip_bg": "#120f1d",
        "focus_badge": "#e9d5ff",
    },
    "matrix": {  # 终端绿
        "bg": "#0a110d", "card_bg": "#0f1a13", "card_border": "#23402c",
        "hd_grad": "linear-gradient(135deg, #0c1710 0%, #10241a 55%, #14361f 100%)",
        "accent": "#4ade80", "accent_rgb": "74,222,128",
        "title": "#eefdf3", "text": "#d9f2e0", "dim": "#7fa88c",
        "glow2": "rgba(52,211,153,0.12)", "chip_bg": "#0a110d",
        "focus_badge": "#bbf7d0",
    },
}
AGI_THEME_ORDER = ["ember", "ocean", "violet", "matrix"]

CAT_ICONS = {
    "大模型": "🧠", "芯片硬件": "💾", "产品发布": "🚀", "开源项目": "📦",
    "研究突破": "🔬", "行业动态": "📈", "政策监管": "⚖️", "投融资": "💰",
}


def _agi_date_cn(date_str: str) -> str:
    """'20261008' → '2026年10月8日'"""
    try:
        return (f"{date_str[:4]}年{int(date_str[4:6])}月"
                f"{int(date_str[6:])}日")
    except (ValueError, IndexError):
        return date_str


def _agi_theme_for(date_str: str) -> str:
    """按期号轮换主题(每天换气质, 连续日期不重样)"""
    if date_str and date_str.isdigit():
        return AGI_THEME_ORDER[int(date_str) % len(AGI_THEME_ORDER)]
    return "ember"


def build_agi_html(title: str, meta: Dict, items: List[Dict],
                   keywords: Optional[List[str]] = None,
                   theme_key: Optional[str] = None) -> str:
    """AGI 日报总览长图 HTML(富信息版):
    header(品牌+日期+期号) + 本期看点统计条 + 新闻卡片(TOP3焦点+分类chip
    +标语+两条要点) + 关键词标签云 + footer; 主题四选一轮换"""
    date_str = meta.get("date") or ""
    theme_key = theme_key or _agi_theme_for(date_str)
    T = AGI_THEMES[theme_key]
    issue_date = _agi_date_cn(date_str)
    today = datetime.datetime.now()
    weekday = "一二三四五六日"[today.weekday()]

    n_items = len(items or [])
    cats = [it.get("category") for it in (items or []) if it.get("category")]
    n_cats = len(set(cats)) if cats else 0
    n_facts = sum(len([p for p in (it.get("img_points") or [])
                       if str(p).strip()]) for it in (items or []))
    kws = [k for k in (keywords or []) if str(k).strip()][:5]
    kw_chips = "".join(f'<span class="kw-chip">#{_esc(k)}</span>' for k in kws)

    cards = []
    for it in items or []:
        num = int(it.get("num") or 0)
        focus = num in (1, 2, 3)
        if focus:
            badge = (f'<div class="rank-badge" style="background:'
                     f'{T["focus_badge"]};color:{T["bg"]}">TOP {num}</div>')
            card_cls = "card focus"
        else:
            badge = f'<div class="rank-badge rank-n">{num}</div>'
            card_cls = "card"
        cat = (it.get("category") or "行业动态").strip()
        chip = (f'<span class="cat-chip">{CAT_ICONS.get(cat, "📌")} '
                f'{_esc(cat)}</span>')
        headline = _esc(it.get("headline") or "")
        tagline = _esc(it.get("tagline") or "")
        facts = "".join(
            f'<div class="fact"><span class="fact-bullet"></span>'
            f'<span>{_esc(str(p))}</span></div>'
            for p in (it.get("img_points") or [])[:2] if str(p).strip())
        facts_html = f'<div class="facts">{facts}</div>' if facts else ""
        cards.append(f"""
      <div class="{card_cls}">
        <div class="card-head">
          {badge}
          <div class="news-title">{headline}</div>
          {chip}
        </div>
        <div class="tagline">{tagline}</div>
        {facts_html}
      </div>""")
    cards_html = "\n".join(cards)

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    width: 1080px;
    background: {T['bg']};
    font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
    color: {T['text']};
    padding: 40px;
  }}
  .header {{
    background: {T['hd_grad']};
    border: 1px solid {T['card_border']};
    border-radius: 24px;
    padding: 44px 48px 38px;
    position: relative;
    overflow: hidden;
    margin-bottom: 20px;
  }}
  .header::before {{
    content: "";
    position: absolute; right: -70px; top: -70px;
    width: 320px; height: 320px; border-radius: 50%;
    background: radial-gradient(circle, rgba({T['accent_rgb']},0.22) 0%, transparent 70%);
  }}
  .header::after {{
    content: "";
    position: absolute; left: -60px; bottom: -90px;
    width: 260px; height: 260px; border-radius: 50%;
    background: radial-gradient(circle, {T['glow2']} 0%, transparent 70%);
  }}
  .brand {{
    display: flex; align-items: center; gap: 16px;
    margin-bottom: 18px; position: relative;
  }}
  .brand-mark {{
    width: 58px; height: 58px; border-radius: 14px;
    background: linear-gradient(135deg, {T['accent']} 0%, rgba({T['accent_rgb']},0.62) 100%);
    display: flex; align-items: center; justify-content: center;
    font-size: 34px; font-weight: 900; color: {T['bg']};
    box-shadow: 0 6px 22px rgba({T['accent_rgb']},0.35);
  }}
  .brand-text {{ font-size: 30px; color: {T['accent']}; font-weight: 800;
    letter-spacing: 3px; }}
  .brand-theme {{ margin-left: auto; font-size: 19px; color: {T['dim']};
    letter-spacing: 1px; opacity: 0.85; }}
  .date-pill {{
    background: rgba({T['accent_rgb']},0.15); color: {T['accent']};
    border: 1px solid rgba({T['accent_rgb']},0.4); border-radius: 999px;
    padding: 6px 20px; font-size: 22px; font-weight: 600;
    align-self: flex-start; margin-bottom: 20px; display: inline-block;
  }}
  .title {{ font-size: 42px; font-weight: 800; line-height: 1.35;
    color: {T['title']}; position: relative; }}
  .subtitle {{ margin-top: 14px; font-size: 23px; color: {T['dim']};
    position: relative; }}
  .kb-bar {{
    display: flex; align-items: center; justify-content: space-between;
    gap: 16px; flex-wrap: wrap;
    background: {T['card_bg']}; border: 1px solid {T['card_border']};
    border-radius: 14px; padding: 18px 26px; margin-bottom: 20px;
  }}
  .kb-stats {{ font-size: 22px; color: {T['dim']}; }}
  .kb-stats b {{ color: {T['accent']}; font-weight: 800; font-size: 25px; }}
  .kb-stats .vsep {{ margin: 0 12px; color: {T['card_border']}; }}
  .kb-chips {{ display: flex; gap: 10px; flex-wrap: wrap; }}
  .kw-chip {{
    background: rgba({T['accent_rgb']},0.10); color: {T['accent']};
    border: 1px solid rgba({T['accent_rgb']},0.28);
    border-radius: 999px; padding: 3px 15px; font-size: 20px;
    font-weight: 600;
  }}
  .card {{
    background: {T['card_bg']}; border: 1px solid {T['card_border']};
    border-radius: 18px; padding: 28px 32px 26px;
    margin-bottom: 18px;
  }}
  .card.focus {{
    border: 2px solid transparent;
    background:
      linear-gradient({T['card_bg']}, {T['card_bg']}) padding-box,
      linear-gradient(135deg, rgba({T['accent_rgb']},0.65) 0%,
                      rgba({T['accent_rgb']},0.10) 60%,
                      rgba({T['accent_rgb']},0.35) 100%) border-box;
    box-shadow: 0 10px 34px rgba({T['accent_rgb']},0.13);
  }}
  .card-head {{ display: flex; align-items: flex-start; gap: 16px;
    margin-bottom: 12px; }}
  .rank-badge {{
    min-width: 74px; height: 40px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; font-weight: 800; flex-shrink: 0;
  }}
  .rank-n {{ background: rgba({T['accent_rgb']},0.10); color: {T['dim']};
    border: 1px solid {T['card_border']}; }}
  .news-title {{ font-size: 28px; font-weight: 700; color: {T['title']};
    line-height: 1.45; padding-top: 2px; flex: 1; }}
  .cat-chip {{
    flex-shrink: 0; margin-top: 3px;
    background: rgba({T['accent_rgb']},0.10); color: {T['accent']};
    border: 1px solid rgba({T['accent_rgb']},0.3);
    border-radius: 999px; padding: 3px 14px; font-size: 19px;
    font-weight: 600; white-space: nowrap;
  }}
  .tagline {{
    margin-left: 90px; font-size: 23px; color: {T['dim']};
    line-height: 1.5; padding: 10px 18px;
    background: {T['chip_bg']};
    border-left: 4px solid {T['accent']};
    border-radius: 0 10px 10px 0;
    margin-bottom: 12px;
  }}
  .facts {{ margin-left: 90px; display: flex; flex-direction: column;
    gap: 8px; }}
  .fact {{ display: flex; align-items: baseline; gap: 12px;
    font-size: 21px; color: {T['text']}; line-height: 1.45; }}
  .fact-bullet {{
    width: 9px; height: 9px; border-radius: 3px; flex-shrink: 0;
    background: {T['accent']}; transform: translateY(-2px);
    display: inline-block;
  }}
  .footer {{
    margin-top: 8px; padding: 26px 30px;
    background: {T['card_bg']}; border: 1px dashed {T['card_border']};
    border-radius: 16px;
    display: flex; align-items: center; justify-content: space-between;
  }}
  .footer-left {{ font-size: 22px; color: {T['dim']}; line-height: 1.6; }}
  .footer-left b {{ color: {T['text']}; }}
  .footer-right {{ font-size: 22px; color: {T['accent']}; font-weight: 700;
    white-space: nowrap; margin-left: 20px; }}
</style></head>
<body>
  <div class="header">
    <div class="brand">
      <div class="brand-mark">⚡</div>
      <div class="brand-text">AGI 日报</div>
      <div class="brand-theme">{issue_date} · 周{weekday}</div>
    </div>
    <div class="date-pill">📰 {issue_date} · 周{weekday} · 第 {date_str} 期</div>
    <div class="title">{_esc(title)}</div>
    <div class="subtitle">今日 AI 圈 {n_items} 条大事速览 · 数据来源于网络整理</div>
  </div>
  <div class="kb-bar">
    <div class="kb-stats">
      <b>{n_items}</b> 条大事<span class="vsep">|</span><b>{n_cats}</b> 个领域<span class="vsep">|</span><b>{n_facts}</b> 个看点
    </div>
    <div class="kb-chips">{kw_chips}</div>
  </div>
  {cards_html}
  <div class="footer">
    <div class="footer-left"><b>AGI 日报</b> · 每天帮你看完 AI 圈新动态<br>数据来源于网络整理, 详情以官方消息为准</div>
    <div class="footer-right">关注不迷路 →</div>
  </div>
</body></html>"""


def render_agi_image(title: str, meta: Dict, items: List[Dict],
                     out_path: str, width: int = 1080,
                     keywords: Optional[List[str]] = None,
                     theme_key: Optional[str] = None) -> str:
    """渲染 AGI 日报总览长图(Playwright 2x 截图, 主题默认按期号轮换)"""
    from playwright.sync_api import sync_playwright

    if not theme_key:
        theme_key = _agi_theme_for(meta.get("date") or "")
    html = build_agi_html(title, meta, items, keywords=keywords,
                          theme_key=theme_key)
    tmp_html = out_path + ".html"
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(html)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": width, "height": 800},
                                    device_scale_factor=2)
            page.goto("file://" + os.path.abspath(tmp_html))
            page.wait_for_timeout(500)
            page.screenshot(path=out_path, full_page=True)
            browser.close()
    finally:
        try:
            os.unlink(tmp_html)
        except OSError:
            pass
    print(f"[image] AGI 日报长图已生成(主题:{theme_key}): {out_path}")
    return out_path
