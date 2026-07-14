# ENHE Promotion Manager

[![ZH](https://img.shields.io/badge/README-ZH-blue)](README.zh-CN.md)
[![English](https://img.shields.io/badge/README-English-gray)](README.en.md)

语言切换 / Language switch: [中文](README.zh-CN.md) | [English](README.en.md)

English quick links: [Install](README.en.md#install) / [Installation](docs/installation.md) / [Quick Start](README.en.md#quick-start) / [Browser Extension](README.en.md#browser-extension) / [Subscription Model](README.en.md#subscription-model) / [Safety Gates](README.en.md#safety-gates) / `I_APPROVE_SKILL_SYNC`

100% completion roadmap: [docs/100-percent-completion-roadmap.md](docs/100-percent-completion-roadmap.md)

中文 100% 完成指南：[docs/zh-CN/100-percent-completion-guide.md](docs/zh-CN/100-percent-completion-guide.md)

ENHE Promotion Manager 是一个本地 Codex Skill，用来把任意产品 URL、网站 URL、App 页面或 GitHub 仓库，转换成可重复执行的产品推广系统。

它适合独立开发者、AI 工具站运营者、SaaS 团队和内容营销团队，让 Codex 像一个“网站及产品推广经理”一样工作：

```text
产品链接
  -> 产品信息读取
  -> 爆款竞品研究
  -> 多平台标题、文案、脚本生成
  -> 视频、封面、详情图资产生成
  -> 安全发布包
  -> 真实数据回收
  -> 下一轮复盘优化
```

仓库地址：[hqwzhu/Viral-Product-Copy-Video-Generator](https://github.com/hqwzhu/Viral-Product-Copy-Video-Generator.git)

## 这个项目是做什么的

你给它一个产品链接或网站链接，它可以帮助你完成从推广研究到发布包准备的整套流程：

- 读取一个或多个产品 URL，生成结构化产品资料。
- 在 YouTube、知乎、小红书、抖音、GitHub、TikTok 等平台上整理公开或浏览器可见的爆款素材证据。
- 拆解爆款标题、钩子、内容结构、视频结构、创作者模式和可见互动数据。
- 生成平台原生的爆款标题、正式文案、标签、首批评论/回复、口播脚本、分镜脚本。
- 生成或挂载 MP4 视频、封面图、详情图，并写入完整发布包。
- 为支持官方 API 的平台准备 dry-run 发布计划，为其他平台生成浏览器辅助/手动发布包。
- 发布后导入真实 URL、指标、评论、订单和收入证据，生成复盘和下一轮优化建议。

## 使用后能得到什么

一次正常运行会在本地 `promotion-output` 目录里生成这些产物：

- 产品资料和事实提取报告。
- 竞品搜索任务、爆款素材库、创作者榜单和补充证据请求。
- YouTube、知乎、小红书、抖音、GitHub 等平台的内容草稿。
- 完整发布包：爆款标题、正式文案、标签、首批互动内容、视频状态/路径、封面图、详情图、追踪链接、风险提示和发布步骤。
- 可选 MP4 草稿视频，依赖 `ffmpeg`。
- 可选 PNG 封面图和详情图，依赖 `Pillow`。
- 浏览器辅助/手动发布 payload 和检查清单。
- 发布后真实证据收件箱模板：发布 URL、平台指标、评论、订单、收入。
- 有真实数据后生成复盘报告和下一轮选题/标题/脚本建议。

## 它不会做什么

项目默认遵守平台安全边界：

- 不绕过登录、验证码、平台风控、账号验证或应用审核。
- 不使用 Cookie 抓包、私有接口、隐藏 token 或模拟登录。
- 浏览器辅助发布不会点击最终发布按钮。
- 不伪造播放量、点赞、评论、订单、收入或已发布 URL。
- 官方 API 发布端口默认 dry-run，真实发布必须有官方凭证、账号授权和显式批准。

## 当前能力状态

| 模块 | 状态 | 说明 |
| --- | --- | --- |
| 产品 URL 读取 | 已具备 | 支持浏览器快照、结构化 JSON、静态 HTML、公网页面文本 fallback、URL 发现和批量运行。 |
| 爆款研究 | 已具备但受平台限制 | YouTube/GitHub 可走公开或官方路径；知乎、小红书、抖音、TikTok 以公开页面、浏览器可见证据或用户导出为准。 |
| 文案和媒体生成 | 已具备 | 可生成平台文案、首批互动提示、脚本、分镜、MP4 草稿视频、PNG 封面图和详情图。 |
| 发布 | 手动发布包优先 | GitHub、YouTube 保留官方 API dry-run 端口；抖音、知乎、小红书默认浏览器辅助或手动发布，抖音官方端口仅作为后续授权可用时的预留能力。 |
| 指标和收入回收 | 等待真实证据 | 可生成证据收件箱、导入真实指标/评论/订单/收入并复盘；不会编造数据。 |
| 自我进化 | 受控 | 可审计本地工具、仓库状态和 Skill 同步差异；安装或同步需要显式命令。 |
| 浏览器插件 | 可打包，后端可部署 | 已有 Chrome MV3 插件、打包脚本、Stripe/License 服务、PostgreSQL 状态存储、hosted worker 队列、商店材料、隐私/条款/退款/支持页面草稿和同域 HTTPS 部署配置；账号注册、Stripe 实名/价格、服务器部署和商店后台提交仍需操作者完成。 |

## 插件商业化与云端任务

插件可以连接同一 HTTPS 域名下的 ENHE 后端：

- `https://www.enhe-tech.com.cn/api/promotion-manager/license`
- `https://www.enhe-tech.com.cn/api/promotion-manager/usage/authorize`
- `https://www.enhe-tech.com.cn/api/promotion-manager/run`
- `https://www.enhe-tech.com.cn/api/promotion-manager/run/{runId}`

后端位于 [backend/license-service](backend/license-service/)，部署配置位于 [deploy/promotion-manager](deploy/promotion-manager/)。生产建议使用 PostgreSQL、Stripe Checkout/Customer Portal、独立 API 进程和独立 hosted worker 进程。hosted worker 只执行白名单任务，不直接执行插件传来的任意命令，并默认保持手动发布安全边界。

## 安装

克隆仓库：

```powershell
git clone https://github.com/hqwzhu/Viral-Product-Copy-Video-Generator.git
cd Viral-Product-Copy-Video-Generator
```

检查 Python：

```powershell
python --version
```

可选：安装浏览器运行时，用于读取动态网页和公开平台搜索页：

```powershell
python -m pip install playwright
python -m playwright install chromium
```

可选：安装 MP4 渲染运行时：

```powershell
winget install Gyan.FFmpeg
```

可选：安装封面图/详情图运行时：

```powershell
python -m pip install pillow
```

Optional YouTube official API client dependencies:

```powershell
python -m pip install -r requirements-youtube.txt
```

This installs `google-api-python-client` and Google OAuth/auth helper packages for the dry-run-first YouTube official publishing port.

验证 YouTube 凭证是否已被项目识别，不会上传视频或输出密钥值：

```powershell
python scripts\youtube_credential_check.py --env-file "C:\path\to\.env" --out-dir ".\promotion-output"
```

YouTube OAuth 客户端变量支持 `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET`，也支持 `.env` 模板中的 `YOUTUBE_CLIENT_ID` / `YOUTUBE_CLIENT_SECRET`。

运行验证：

```powershell
python scripts\test_promotion_manager.py
python -m compileall -q scripts
```

更详细安装说明：[docs/installation.md](docs/installation.md)

中文安装说明：[docs/zh-CN/installation.md](docs/zh-CN/installation.md)

## 快速开始

推广单个产品链接：

```powershell
python scripts\skill_entry.py `
  --link "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --out-dir ".\promotion-output"
```

如果输入的是网站首页，让系统先发现产品页：

```powershell
python scripts\skill_entry.py `
  --link "https://example.com" `
  --link-mode site `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --out-dir ".\promotion-output"
```

在 Codex 里也可以直接这样说：

```text
执行 viral-product-copy-video-generator，推广这个链接：https://example.com/product
平台：youtube,zhihu,xiaohongshu,douyin,github
```

运行结束后重点查看：

```text
promotion-output/reports/promotion-manager/
promotion-output/media-assets/
promotion-output/videos/
```

## 生成完整发布包

如果已经生成内容和视频，可以单独生成媒体资产包，并写回发布包：

```powershell
python scripts\media_asset_pack.py `
  --content-json ".\promotion-output\reports\promotion-manager\generated-content\product-platform-content.json" `
  --publish-pack ".\promotion-output\reports\promotion-manager\publish-packs\product-publish-pack.json" `
  --video-file "youtube=.\promotion-output\videos\product-youtube.mp4" `
  --video-file "douyin=.\promotion-output\videos\product-douyin.mp4" `
  --out-dir ".\promotion-output"
```

发布包会包含：

- 爆款标题
- 正式文案
- 平台标签
- 首批评论、置顶评论、回复提示和启动动作
- 视频成品状态和路径
- 封面图
- 详情图
- 统一 `assets` 列表

完整工作流会在视频渲染后自动运行这一步。如果使用 `--skip-video`，系统会继续生成封面和详情图，并把缺失视频标记为 `missing`，不会伪造成品视频。

## 发布与复盘

生成发布准备报告：

```powershell
python scripts\publish_readiness_runner.py `
  --workflow-manifest ".\promotion-output\reports\promotion-manager\agent-run\workflow-manifest.json" `
  --build-queue `
  --github-repo owner/repo `
  --out-dir ".\promotion-output"
```

生成浏览器辅助/手动发布包：

```powershell
python scripts\browser_publish_assistant.py `
  --publish-queue ".\promotion-output\reports\promotion-manager\publish-queue\publish-queue.json" `
  --out-dir ".\promotion-output"
```

发布后登记真实 URL：

```powershell
python scripts\published_items.py `
  --platform xiaohongshu `
  --published-url "https://www.xiaohongshu.com/explore/real-note-id" `
  --evidence ".\screenshots\xhs-published.png" `
  --out-dir ".\promotion-output"
```

导入真实证据并复盘：

```powershell
python scripts\real_evidence_inbox_setup.py `
  --product-url "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --inbox-dir ".\promotion-evidence-inbox" `
  --out-dir ".\promotion-output"

python scripts\real_evidence_inbox.py `
  --inbox-dir ".\promotion-evidence-inbox" `
  --out-dir ".\promotion-output"
```

## 浏览器插件

浏览器插件位于 [browser-extension](browser-extension/)。

它可以：

- 读取当前浏览器标签页 URL。
- 选择目标平台和运行深度。
- 生成 Codex 命令、发布包命令、证据收件箱命令和周期自动化命令。
- 估算订阅积分消耗。
- 连接 ENHE License/Usage/Hosted Run API。
- 打包为 Chrome/Edge 插件提交包。

本地加载：

1. 打开 `chrome://extensions`。
2. 开启 Developer mode。
3. 点击 Load unpacked。
4. 选择 `browser-extension` 目录。

打包：

```powershell
python scripts\package_browser_extension.py --out-dir ".\dist"
```

商业化上线还需要部署后端 License 服务、配置 Stripe、准备隐私政策/截图/商店说明，并通过 Chrome Web Store 或 Microsoft Edge Add-ons 审核。

## 文档

- [英文 README](README.en.md)
- [安装说明](docs/installation.md)
- [使用说明](docs/usage.md)
- [中文安装说明](docs/zh-CN/installation.md)
- [中文使用说明](docs/zh-CN/usage.md)
- [浏览器插件说明](docs/browser-extension.md)
- [插件上架指南](docs/extension-store-submission.md)
- [中文浏览器插件说明](docs/zh-CN/browser-extension.md)
- [中文插件上架指南](docs/zh-CN/extension-store-submission.md)
- [订阅定价模型](docs/subscription-pricing.md)
- [计费后端合约](docs/billing-backend-contract.md)
- [最终能力矩阵](docs/final-capability-map.md)
- [100% 完成路线图](docs/100-percent-completion-roadmap.md)

## License

MIT. See [LICENSE](LICENSE).
