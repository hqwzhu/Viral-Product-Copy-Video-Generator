# ENHE 产品推广素材生成器

ENHE 产品推广素材生成器是一个 Codex Skill，用来把任意产品 URL、网站 URL、App 页面或 GitHub 仓库转成可重复执行的产品推广闭环。把产品网页变成推广文案、视频脚本和发布素材。

[English README](README.en.md)

## 能做什么

- 读取一个或多个产品 URL，并把 Codex/浏览器读取到的结构化网页证据传给产品信息解析流程。
- 在 YouTube、知乎、小红书、抖音、GitHub、TikTok 等平台搜索和排序公开可见的爆款博主、视频、帖子和仓库。
- 生成平台原生标题、知乎文章、小红书笔记、抖音/YouTube 口播脚本、分镜、README 推广文案、Release 文案和 MP4 草稿视频。
- 为支持官方 API 的平台准备受保护的发布队列；对不能安全直发的平台生成浏览器辅助或手动发布包。
- 从真实证据中回收播放量、点赞、评论、需求信号、订单和收入，并生成下一轮优化建议。
- 提供 Chrome MV3 浏览器插件，用于生成 Codex 命令、订阅计费估算、License 校验、Hosted Run Payload 和 ENHE 网站引流链接。

## 当前能力边界

| 模块 | 状态 | 说明 |
| --- | --- | --- |
| 产品 URL 读取 | 已具备 | 支持浏览器快照、结构化 JSON、静态 HTML、公开网页文本 fallback、URL 发现和批量运行。 |
| 爆款研究 | 已具备但受平台限制 | YouTube/GitHub 可走公开或官方接口；知乎、小红书、抖音、TikTok 以公开页面、浏览器可见证据或用户导出为准。 |
| 文案和视频 | 已具备 | 可生成平台文案、脚本、分镜，并用 ffmpeg 渲染 MP4。 |
| 发布 | 手动发布包优先 | 当前默认策略是先生成发布队列、浏览器辅助/手动发布包和真实证据模板；GitHub、YouTube 保留官方 API dry-run 端口，抖音默认改为浏览器辅助/手动发布，官方端口仅作为后续授权可用时的预留能力。 |
| 数据回收 | 等待真实证据 | 可运行 `real_evidence_inbox_setup.py`、`performance_monitor.py` 或 `real_evidence_inbox.py`，但不会伪造发布 URL、指标、订单或收入。 |
| 自我进化 | 受控 | 可审计工具、文档、仓库和已安装 Skill 差异；只在明确命令下同步或安装白名单运行时。 |
| 阶段进度汇报 | 已具备 | `final_capability_readiness.py` 会输出当前阶段、已实现目标、未实现目标、下一步计划和预计剩余时间。 |

## 快速开始

```powershell
python scripts\skill_entry.py `
  --link "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --out-dir ".\promotion-output"
```

当公开产品页无法被本机 Chromium 或静态 HTML 抓取读取时，`product_url_reader.py` 会保存公开网页文本 fallback，并让后续流程通过 `--text-file` 继续运行。若不希望使用第三方公开网页文本读取，可加 `--disable-web-text-fallback`；若 Codex 已经读取并保存网页文本，可传 `--web-text-fallback-file`。

如果给的是网站首页或工具站页面：

```powershell
python scripts\skill_entry.py `
  --link "https://example.com" `
  --link-mode site `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --out-dir ".\promotion-output"
```

每个主要阶段完成后，使用 `reports\promotion-manager\final-readiness\final-capability-readiness.md` 做阶段进度报告，汇报当前阶段、已实现目标、未实现目标、下一步计划和预计剩余时间。

生成发布与真实证据解锁包：

```powershell
python scripts\launch_unlock_pack.py `
  --publish-queue ".\promotion-output\reports\promotion-manager\publish-queue\publish-queue.json" `
  --publish-readiness ".\promotion-output\reports\promotion-manager\publish-readiness\publish-readiness.json" `
  --out-dir ".\promotion-output"
```

该解锁包会生成平台授权、凭证变量名、浏览器辅助发布、真实数据模板和下一步命令清单；它不会读取或保存真实密钥，也不会绕过登录、验证码、风控或最终发布确认。

`scripts\final_capability_runner.py` 现在会在存在发布队列时为每个产品 run 自动生成该解锁包。只有在你更新了凭证、目标文件或平台发布入口后，才需要单独重建。

内容审核现在也会生成 `reports\promotion-manager\cheat-review\` 桥接包：每个平台一份待评分草稿，并附带可在 Codex 中触发 `cheat-score` 的提示词。它只用于审核，不会自动创建不可逆预测日志；只有你明确启动 `cheat-on-content` 预测周期时才会写预测文件。

发布后，先登记真实 URL，再运行性能监控：

```powershell
python scripts\published_items.py `
  --platform xiaohongshu `
  --published-url "https://www.xiaohongshu.com/explore/real-note-id" `
  --evidence ".\screenshots\xhs-published.png" `
  --out-dir ".\promotion-output"

python scripts\performance_monitor.py --out-dir ".\promotion-output"
```

如果还没有真实发布数据，只是想验证数据回收、复盘和下一轮优化链路，可以生成明确标记的 synthetic/demo 证据：

```powershell
python scripts\synthetic_evidence_generator.py `
  --product-url "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --run-recovery `
  --out-dir ".\promotion-output\synthetic-validation"
```

生成结果会带有 `SYNTHETIC_DEMO_DATA_DO_NOT_REPORT` 标记，只能用于本地流程验证，不能当作真实播放量、订单或收入数据汇报。

发布前或发布后可以先生成证据收件箱模板：

```powershell
python scripts\real_evidence_inbox_setup.py `
  --product-url "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --inbox-dir ".\promotion-evidence-inbox" `
  --out-dir ".\promotion-output"
```

多个导出文件可以放到证据收件箱：

```powershell
python scripts\real_evidence_inbox.py `
  --inbox-dir ".\promotion-evidence-inbox" `
  --out-dir ".\promotion-output"
```

## 安装和使用

- [中文安装教程](docs/zh-CN/installation.md)
- [中文使用说明](docs/zh-CN/usage.md)
- [English installation](docs/installation.md)
- [English usage](docs/usage.md)

## 浏览器插件

插件位于 `browser-extension/`，可作为 Chrome Manifest V3 未打包扩展加载。它可以：

- 读取当前产品页 URL。
- 生成一键 Skill 运行、浏览器辅助发布、真实证据收件箱初始化/导入、发布后性能监控、最终 readiness 审计和周期任务命令。
- 按 token/运行成本估算订阅 credits。
- 保存本地 License key，调用 ENHE License/Usage/Hosted Run API。
- 展示开发者信息和 ENHE 网站链接，用于产品引流。

商业化后端参考实现位于 `backend/license-service/`，包含 Stripe Checkout、Webhook 签名校验、License 校验、usage credit 预留、usage commit 和 hosted run 队列入口。正式上线前仍需要部署 HTTPS 后端、配置 Stripe live price/webhook、替换数据库、发布隐私/支持页面，并通过 Chrome/Edge 商店审核。

## 安全规则

- 不自动登录。
- 不绕过验证码、风控或平台审核。
- 不保存 cookie、密码、API key 或隐藏 token。
- 浏览器辅助发布不会点击最终发布按钮。
- 不伪造播放量、点赞、评论、订单或收入。
- 官方发布必须有凭证、目标信息和 `I_APPROVE_PUBLISH`。
- 同步安装版 Skill 必须有 `I_APPROVE_SKILL_SYNC`。

## 浏览器插件成品与上架

插件位于 `browser-extension/`，现在包含 MV3 manifest、本地图标、订阅估算、license 校验、usage credits 预留、hosted run payload、ENHE 网站引流链接和开发者信息。

打包 Chrome Web Store / Microsoft Edge Add-ons 提交包：

```powershell
python scripts\package_browser_extension.py --out-dir ".\dist\v0.5.4"
```

输出：

- `dist\v0.5.4\enhe-promotion-manager-0.5.4.zip`
- `dist\v0.5.4\browser-extension-package-report.json`
- `dist\v0.5.4\browser-extension-package-report.md`

提交前确认 package report 的 `status` 为 `ready`。上架步骤、privacy policy、remote code 审核说明和收费订阅话术见：

- [中文浏览器插件说明](docs/zh-CN/browser-extension.md)
- [中文插件上架指南](docs/zh-CN/extension-store-submission.md)
- [English browser extension guide](docs/browser-extension.md)
- [English extension store submission guide](docs/extension-store-submission.md)

## 爆款证据收件箱 fallback

当知乎、小红书、抖音等平台自动搜索不稳定，或者只能拿到浏览器可见内容时，先创建空模板：

```powershell
python scripts\viral_evidence_inbox_setup.py `
  --product-url "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --inbox-dir ".\viral-evidence-inbox" `
  --out-dir ".\promotion-output"
```

填入真实对标链接、可见正文、口播稿、平台导出或截图 OCR 文本后导入：

```powershell
python scripts\viral_evidence_inbox.py `
  --inbox-dir ".\viral-evidence-inbox" `
  --out-dir ".\promotion-output"
```

该收件箱不会预置虚假博主、播放量或点赞数；截图文件必须补充 OCR/复制文本后才会进入爆款库。
