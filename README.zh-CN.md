# ENHE Promotion Manager

ENHE Promotion Manager 是一个 Codex Skill，用来把任意产品 URL、网站 URL、App 页面或 GitHub 仓库转成可重复执行的产品推广闭环。

[English README](README.md)

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
| 产品 URL 读取 | 已具备 | 支持浏览器快照、结构化 JSON、静态 HTML、URL 发现和批量运行。 |
| 爆款研究 | 已具备但受平台限制 | YouTube/GitHub 可走公开或官方接口；知乎、小红书、抖音、TikTok 以公开页面、浏览器可见证据或用户导出为准。 |
| 文案和视频 | 已具备 | 可生成平台文案、脚本、分镜，并用 ffmpeg 渲染 MP4。 |
| 发布 | 部分具备 | GitHub、YouTube、抖音需要凭证、授权、平台权限和 `I_APPROVE_PUBLISH`；知乎和小红书默认浏览器辅助或手动发布。 |
| 数据回收 | 等待真实证据 | 可运行 `performance_monitor.py` 或 `real_evidence_inbox.py`，但不会伪造发布 URL、指标、订单或收入。 |
| 自我进化 | 受控 | 可审计工具、文档、仓库和已安装 Skill 差异；只在明确命令下同步或安装白名单运行时。 |

## 快速开始

```powershell
python scripts\skill_entry.py `
  --link "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --out-dir ".\promotion-output"
```

如果给的是网站首页或工具站页面：

```powershell
python scripts\skill_entry.py `
  --link "https://example.com" `
  --link-mode site `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --out-dir ".\promotion-output"
```

发布后，先登记真实 URL，再运行性能监控：

```powershell
python scripts\published_items.py `
  --platform xiaohongshu `
  --published-url "https://www.xiaohongshu.com/explore/real-note-id" `
  --evidence ".\screenshots\xhs-published.png" `
  --out-dir ".\promotion-output"

python scripts\performance_monitor.py --out-dir ".\promotion-output"
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
- 生成一键 Skill 运行、浏览器辅助发布、真实证据收件箱、发布后性能监控、最终 readiness 审计和周期任务命令。
- 按 token/运行成本估算订阅 credits。
- 保存本地 License key，调用 ENHE License/Usage/Hosted Run API。
- 展示开发者信息和 ENHE 网站链接，用于产品引流。

## 安全规则

- 不自动登录。
- 不绕过验证码、风控或平台审核。
- 不保存 cookie、密码、API key 或隐藏 token。
- 浏览器辅助发布不会点击最终发布按钮。
- 不伪造播放量、点赞、评论、订单或收入。
- 官方发布必须有凭证、目标信息和 `I_APPROVE_PUBLISH`。
- 同步安装版 Skill 必须有 `I_APPROVE_SKILL_SYNC`。
