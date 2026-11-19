# Reddit 免密登录管线（magic link 全流程实战笔记）

> 2026-11-19 实测打通：Playwright + urnetwork 住宅出口 + 持久 profile，
> 从触发邮件到三层落盘全程自动化。本文档是踩坑 3 轮后的完整方法论。

## 背景

- 账号为邮箱注册（无可用密码：两个变体均被应用层明确拒绝，
  判定注册时未设密码），**唯一登录路径 = 一次性邮件链接（magic link）**
- 目标：在服务器端建立并持久化 Reddit 登录态，供自动发帖管线使用

## 一、代理链路（urnetwork）

| 端口 | 协议 | 实测 |
|---|---|---|
| 7166 | HTTP | ✗ Reddit 直接 RST，不可用 |
| 7165 | SOCKS5 | ✓ |
| **7167** | **HTTPS** | ✓ **推荐：token 编在子域名，免鉴权** |

- HTTPS 代理形如 `https://<URNETWORK_TOKEN>.crisp.bringyour.com:7167`
  （token 由 `urnetwork_verify.py` 从 bringyour API 拉取，与 JWT 同周期约 30 天）
- 出口为住宅 IP，且**每隔一段时间轮换**（实测 20 分钟内见 3 个不同 IP）。
  短窗口内（分钟级）稳定，同一命令内连发 3 次请求 IP 不变
- 验证码续期：`urnetwork_authcode.py`（ur.io 邮箱验证码 → JWT，
  双层落盘 `~/.secrets/urnetwork_jwt.json` + `my-project/secrets/`）

## 二、magic link 登录全流程

### 1. 触发邮件（reddit_one_time_link.py）

```
/login/ → 填邮箱 → 点 "Email me a one-time link"
→ 二级表单 "Where should we send the link to?" → 填邮箱 → Continue
→ POST /svc/shreddit/account/login/magic_link/initialize 200
→ 页面显示 "Check your inbox"
```

- 必须走浏览器：API 式 POST 会被 Fastly 边缘 403
- reCAPTCHA enterprise 在有头模式 + 住宅 IP 下正常放行
- 邮件约 30 秒内到达；沙盒无 Gmail API，需人工把邮件里的链接
  **右键复制**（不要点击！）转发给操作者

### 2. 打开链接（同 profile！）

链接形如：
`https://www.reddit.com/magic_link/mlt:<MAGIC_TOKEN>/t2_<REDDIT_USER_ID>?$deep_link=true&otp=false`

**必须用申请邮件时的同一个持久 profile**（含 JS 挑战 cookie）。

页面加载后内部流程（全量抓包 `reddit_magic_diag.py` 才能看到）：

```
GET magic_link URL
  → (有时) JS 挑战页: 8KB 极简页, 表单自动 GET 重提交
     solution = <challenge_token> 自拼接(字符串×2), js_challenge=1, jsc_token=...
  → shreddit app 页(pageType=magic_link_handler)
  → graphql CreateCaptchaToken + update-recaptcha
  → POST /svc/shreddit/account/login/magic_link
     body: {user_id, token, recaptcha_token,
            recaptcha_action: "v1/web/login_with_magic_link", csrf_token}
```

### 3. ★ 最大的坑：首 POST 竞态 401

**页面自己的首次 POST 会返回 `401 {"error":{"message":"unauthorized"}}`，
随后 UI 降级成 "Email me a one-time link" 重发表单。**

此时千万别误判为"链接已失效/被消费"——token 是好的！

**解法（reddit_magic_diag2.py）：捕获页面发出的 POST body，
等 8 秒后在同一浏览器上下文用 fetch 原样重放 → 200，
`reddit_session` cookie 立即落地。**

```python
result = page.evaluate("""async (body) => {
    const r = await fetch('/svc/shreddit/account/login/magic_link', {
        method: 'POST', credentials: 'include',
        headers: {'content-type': 'application/json'}, body: body });
    return {status: r.status, body: (await r.text()).slice(0,300)};
}""", captured_post_body)
```

## 三、环境坑（沙盒）

| 坑 | 解法 |
|---|---|
| `xvfb-run` 缺 xauth 不可用 | 手动 `Xvfb :99 &` + `DISPLAY=:99` |
| 沙盒在工具调用间回收后台进程（Xvfb 也活不过一次调用） | **Xvfb 和脚本放同一条 bash 命令里启动** |
| Xvfb 残留死 socket 导致新进程秒退 | 先 `rm -f /tmp/.X11-unix/X99` |
| `/api/me.json` 页内 fetch 常 403（Fastly） | 用 cookie 判定（reddit_session）+ DOM（无 Log In 按钮）；登录后带头 fetch 可通 |
| curl 提交 JS 挑战 solution 被 403 | curl TLS 指纹被识别，挑战必须由真 Chrome 完成 |
| 有头模式登录输入框无 id | 选择器兜底链 `input#login-username → input[name="username"] → input[autocomplete="username"]` |

## 四、登录态固化（reddit_finalize_login.py）

登录成功的标志：cookies 中出现 **`reddit_session`**（持久 cookie，
实测有效期约 6 个月）。

落盘层级：

| 层 | 路径 | 用途 |
|---|---|---|
| storage_state ×3 | `~/.secrets/reddit_state.json` + `my-project/secrets/reddit_state.json` + 带时间戳副本 | Playwright 免profile复用 |
| 账号信息 | `my-project/secrets/reddit_account.json` | username/email/method/exit |
| Netscape cookies | `my-project/secrets/reddit_cookies.txt` | curl_cffi 等直用 |
| 整 profile | `my-project/secrets/reddit_profile_<TS>.tar.gz` | 灾备恢复 |
| 索引 | `my-project/secrets/LOGIN_STATES_INDEX.json` | 16 项登录态总审计入口 |

**以上 secrets 一律只留本地，绝不入库**（仓库内脚本均已净化为占位符）。

## 五、文件清单

| 文件 | 作用 |
|---|---|
| `urnetwork_verify.py` / `urnetwork_authcode.py` | 代理验证码→JWT→出口探测 |
| `reddit_one_time_link.py` | 触发 magic link 邮件 |
| `reddit_magic_login.py` / `reddit_magic_login2.py` | 打开链接登录（v2=cookie+DOM双判定） |
| `reddit_magic_diag.py` / `reddit_magic_diag2.py` | 全量抓包诊断；**diag2=POST捕获+重放（破局脚本）** |
| `reddit_finalize_login.py` | 登录态验证+五层固化 |
| `login_state_audit_20261119.py` | 全平台 16 项登录态审计 |
| `x_state_verify_20261119.py` | X 状态从常量重建+实测验证 |

## 六、失败模式速查

| 现象 | 真因 | 动作 |
|---|---|---|
| 页面显示重发表单 | 首 POST 竞态 401（≠token失效） | 捕获 body 重放 |
| 重放也 401 | token 真失效（被点过/超时约1h） | 重新触发邮件 |
| goto 就卡挑战页循环 | profile 丢失挑战 cookie | 用持久 profile 重来 |
| 全部 XHR 403 | 出口 IP 被边缘标记 | 换出口/等轮换 |
