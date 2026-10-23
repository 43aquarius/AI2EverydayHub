# AI2EverydayHub · 多平台自动内容矩阵 · 总控交接文档

> **这是整个矩阵的入口文档。** 新 Agent 从这里开始，按需跳转到各平台仓库。
> 维护者：Super Z（GLM）· 最近全量更新：2026-10-23

## 0. 矩阵总览

| 平台 | 代码目录（沙箱） | GitHub 仓库 | 内容与节奏 | 状态 |
|------|------|------|------|------|
| 小黑盒 | `/home/z/my-project/github-hot-heybox/` | [AI2HeyboxEveryday](https://github.com/43aquarius/AI2HeyboxEveryday) | AGI 日报 每日 09:30；GitHub 周榜 周一 10:00 | 运行中 |
| 微博 | `/home/z/my-project/weibo-agi-poster/` | [AI2WeiboEveryday](https://github.com/43aquarius/AI2WeiboEveryday) | 五栏目：早报 07:30 / 一言 12:00 / 萌宠 15:00 / 历史 18:30 / 热榜 21:30 | 运行中 |
| 网易云音乐 | `/home/z/my-project/netease-music-poster/` | [AI2NeteaseEveryday](https://github.com/43aquarius/AI2NeteaseEveryday) | 每日一歌 08:00；评论自动回复 08–23 每 2h；周歌单 周日 19:30 | 运行中 |
| 小红书 | `/home/z/my-project/xhs-draft-poster/` | [AI2XhsDraft](https://github.com/43aquarius/AI2XhsDraft) | 图文笔记 2~3 天一期（低频红线）；默认存草稿，发布需用户授权 | 运行中 |
| 时讯视频 | `/home/z/my-project/news-video-gen/` | [NewsVideoEveryday](https://github.com/43aquarius/NewsVideoEveryday) | AGI 时讯 1080p 视频（同小黑盒数据源）；手动/半自动 | 首期制作中 |

各平台的**完整**交接文档（安装/凭据/发布流程/调度/防重/排雷/命令速查）在各自仓库 README，**接管任何一个平台前必读对应文档**。

## 1. 沙箱环境拓扑（必读，所有坑的根源）

- 工作目录：`/home/z/my-project/`；所有产出物放 `download/`；生成脚本放 `scripts/`。
- **沙箱会不定期重启**，重启会带走：各项目 `.git/`、项目内 `config.json`（.gitignore 凭据）、
  nohup 后台进程、`/tmp`。**项目外 `/home/z/.secrets/` 是唯一可靠的凭据持久层**。
- **时区**：系统时钟是 UTC，实际按北京时间（UTC+8）排程；各调度器已内置换算，勿重复换算。
- **Bash 工具调用结束会清理 nohup 后台子进程**：一次性长任务必须用
  `/home/z/my-project/scripts/detached_run.py <工作目录> <日志> <命令...>`（双 fork 脱离，实测常驻）。
- 网络间歇抖动：git clone / GitHub API 阵发 404/TLS 失败，重试即可（推送脚本已内置 8 次耐心重试）。

## 2. 一键自愈（重启后第一件事）

```bash
python3 /home/z/my-project/scripts/boot_heal.py
```

自动完成：① 三平台凭据三层回写（config.json ← `/home/z/.secrets/` ← secrets_backup.json）
② 调度器拉起（小黑盒/微博/网易云）③ 输出待办清单（缺凭据平台等 cookie）。

各平台专用重建脚本（boot_heal 报「缺失」时用）：

| 平台 | 脚本 | 说明 |
|------|------|------|
| 网易云 | `netease-music-poster/rebuild_config.py --env` | 从 `MUSIC_U_COOKIE` 环境变量重建 |
| 微博 | `scripts/rebuild_weibo_config.py` | cookie 内嵌，运行即恢复 |
| 小红书 | `scripts/save_xhs_cookie.py` | 完整 cookie 内嵌，恢复三层 |
| 小黑盒 | boot_heal 自愈（cookie 在 heybox_config） | 全缺时需用户重新抓 cookie |

## 3. 统一日志：worklog.md

`/home/z/my-project/worklog.md` 是唯一共享工作日志，**每个 Agent 完成任务后必须追加**：

```markdown
---
Task ID: <任务号>
Agent: <agent 名>
Task: <任务描述>

Work Log:
- <具体步骤>

Stage Summary:
- <关键结论/产物/待用户决策>
```

接手任何平台前：读 worklog **最新两节** + 对应仓库 README。

## 4. GitHub 备份协议

- 组织账号：`43aquarius`；推送走 **Git Data API**（fine-grained PAT 只开了 Contents 权限，
  git-over-HTTPS 不通），token 内嵌于 `scripts/push_github_v2.py`（**永远不要**把 token 写进任何仓库文件或日志）。
- 快照式全量推送工具：`scripts/push_snapshot.py <项目目录> <repo名> "<commit message>"`
  （本地 git init 尊重 .gitignore → blobs → tree → commit → 移动 main）。
- ⚠️ 沙箱重启会清 `.git/`：推送脚本每次本地重新 init，无需担心；但**同一次会话内勿依赖 .git 历史**。
- 间歇 404 是常态：脚本已内置 curl 单发 + 12s×8 次重试。

## 5. 内容策略速记

- 小黑盒 AGI 日报数据源：微信合集页（腾讯研究院 AI 速递，T-1 日 16:01 发次日刊）。
  **红线：帖子中不标明来源为腾讯研究院/ima，只说"数据来源于网络整理"**。
- 小红书：低频（2~3 天一期）、拟人化、默认草稿、发布需用户当次授权（安全设计，勿破坏）。
- 网易云评论回复：按 uid 过滤只回复他人，防误回复留底测试评论。
- 时讯视频：与小黑盒 AGI 日报同一数据源双形态分发；TTS 用 z-ai 免费引擎（限流时退避）。

## 6. 常见故障处置

| 症状 | 处置 |
|------|------|
| 调度器全灭 | `boot_heal.py`（第一反应，永远先跑这个） |
| 某平台凭据缺失 | boot_heal 输出会指出；按 §2 表用对应 rebuild 脚本 |
| 今日帖疑似重复/漏发 | 先查各平台 state 防重标记 + 平台个人主页对账，再决定补发或补写标记（勿盲目 --force） |
| GitHub 推送 404 | 正常抖动，重试；连续失败检查 token（`push_github_v2.py` 内嵌 PAT 可能过期，需用户更新） |
| z-ai TTS 429 | 退避重试；长窗口用 `news-video-gen/scripts/topup_daemon.py` 挂后台 |
| LLM 无响应 | `z-ai chat` CLI 阵发抖动，重试；`summarizer.py` 已内置 JSON 修复容错 |

## 7. 新 Agent 接管总流程

1. 读本文档全文 → 读 `/home/z/my-project/worklog.md` 最新两节
2. `python3 /home/z/my-project/scripts/boot_heal.py` → 三平台恢复
3. 按需读各平台仓库 README（每个都有独立接管 checklist）
4. 干活，每个任务完成写 worklog，代码改动推对应 GitHub 仓库
5. 拿不准的事情问用户，尤其是：**任何平台的真实发布授权、频率变更、新栏目上线**
