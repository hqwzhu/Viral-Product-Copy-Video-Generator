# 100% 完成指南

这份文档回答一个问题：为什么当前每个模块还没有到 100%，还差什么，Codex 能继续做什么，哪些必须由操作者完成，以及新手应该怎么一步一步执行。

判断标准很严格：只有当前证据证明代码、运行环境、账号授权、真实输出、真实发布、真实指标或真实结算记录都存在时，模块才算 100%。代码写好了、文档写好了、dry-run 通过了，都不等于生产 100%。

## 总览

| 模块 | 当前估算 | 到 100% 还缺什么 |
| --- | ---: | --- |
| Codex Skill 本地推广闭环 | 85% | 真实产品 URL 的端到端运行证据、最终 readiness 报告、必要运行环境和已审查 Skill 同步。 |
| 文案/视频/封面/详情图/发布包 | 85% | 当前真实产品的 MP4、封面 PNG、详情图 PNG、完整发布包和每个平台的资产引用。 |
| 竞品研究与网页数据能力 | 80% | 真实产品关键词下的公开/官方/浏览器可见竞品证据，以及被限制平台的人工导入证据。 |
| 插件和商业化基础设施 | 75% | 真实 HTTPS 后端、PostgreSQL 迁移、Stripe live、hosted worker、公开法律页面、Chrome/Edge 审核通过。 |
| 真正全自动发布 | 40% | 官方 API、平台审核、OAuth/Token、账号授权、真实视频文件、发布审批、发布审计日志和真实 URL。 |
| 创作者任务/结算/Monetize 市场 | 30% | 活动/任务/提交/证据/结算数据模型、付款通道、合规流程、真实创作者试点和人工审核结算记录。 |

## 先执行这三步

1. 在本地跑一次真实产品闭环，不要先追求全平台自动发布。
2. 让发布包包含标题、正文、标签、首批互动、视频、封面、详情图和追踪字段。
3. 把平台授权、商店审核、Stripe live、服务器部署和真实结算视为外部门槛，逐项解锁。

## 1. Codex Skill 本地推广闭环

当前约 85%。还没到 100%，因为需要用你的真实产品 URL 跑出当前证据，而不是只证明示例流程可用。

Codex 可以完成：

- 运行本地审计和测试。
- 生成真实运行命令包。
- 生成最终 readiness 矩阵。
- 生成发布解锁包和证据收集模板。
- 在你明确批准后同步已审查的 Skill 文件。

必须你完成：

- 提供真实产品 URL 或网站 URL。
- 如果要同步安装版 Skill，明确批准同步。
- 发布后提供真实 URL、截图、平台导出或业务数据。

新手步骤：

1. 打开 PowerShell，进入项目目录。

```powershell
cd "C:\Users\HU\Documents\Viral-Product-Copy-Video-Generator"
```

2. 检查本地能力和缺口。

```powershell
python scripts\final_capability_audit.py --skip-runtime-checks --out-dir ".\promotion-output\verification"
```

3. 如果需要读取动态网页，安装浏览器运行时。

```powershell
python scripts\final_capability_audit.py --install-safe-missing-tools --safe-install playwright_chromium --out-dir ".\promotion-output"
```

4. 用真实产品 URL 运行 Skill。

```powershell
python scripts\skill_entry.py `
  --link "https://你的真实产品链接" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --out-dir ".\promotion-output"
```

5. 查看最终报告。

```powershell
notepad ".\promotion-output\reports\promotion-manager\final-readiness\final-capability-readiness.md"
```

验收证据：

- `promotion-output/reports/promotion-manager/skill-entry/skill-entry.json`
- `promotion-output/reports/promotion-manager/final-run/final-capability-run.json`
- `promotion-output/reports/promotion-manager/final-readiness/final-capability-readiness.json`
- `promotion-output/reports/promotion-manager/capability/final-capability-audit.json`

## 2. 文案、视频、封面、详情图、发布包

当前约 85%。还没到 100%，因为必须看到当前真实产品对应的成品资产，而不是只看到生成器存在。

Codex 可以完成：

- 生成 YouTube、知乎、小红书、抖音、GitHub 等平台文案。
- 生成爆款标题、标签、首批评论、口播脚本、分镜脚本。
- 在 `ffmpeg` 可用时生成 MP4 草稿。
- 在 `Pillow` 可用时生成封面和详情图。
- 把视频、封面、详情图写回发布包。

必须你完成：

- 安装 `ffmpeg`。
- 安装 `Pillow`。
- 如果要正式商用口播，提供真人或 AI 配音音频。
- 人工检查视频、封面和详情图是否适合发布。

新手步骤：

1. 安装 `ffmpeg`。

```powershell
winget install Gyan.FFmpeg
```

2. 安装 `Pillow`。

```powershell
python -m pip install pillow
```

3. 渲染抖音视频草稿。

```powershell
python scripts\render_video.py `
  --content-json ".\promotion-output\reports\promotion-manager\generated-content\product-platform-content.json" `
  --platform douyin `
  --out ".\promotion-output\videos\product-douyin.mp4"
```

4. 生成封面、详情图并写入发布包。

```powershell
python scripts\media_asset_pack.py `
  --content-json ".\promotion-output\reports\promotion-manager\generated-content\product-platform-content.json" `
  --publish-pack ".\promotion-output\reports\promotion-manager\publish-packs\product-publish-pack.json" `
  --video-file "douyin=.\promotion-output\videos\product-douyin.mp4" `
  --out-dir ".\promotion-output"
```

验收证据：

- `promotion-output/videos/*.mp4`
- `promotion-output/media-assets/*/*.png`
- `promotion-output/reports/promotion-manager/media-assets/media-asset-pack.json`
- `promotion-output/reports/promotion-manager/publish-packs/*-publish-pack.json`

## 3. 竞品研究与网页数据能力

当前约 80%。接入 Firecrawl 后会增强，但 100% 仍需要真实竞品证据。

Codex 可以完成：

- 生成产品相关搜索词。
- 使用公开页面、官方 API 或浏览器可见页面收集证据。
- 调用可选 Firecrawl 风格数据层做 Search、Scrape、Map、Crawl、Batch Scrape。
- 生成竞品证据收集文件夹。
- 排名爆款素材和创作者账号。

必须你完成：

- 如果使用 Firecrawl Cloud，提供 `FIRECRAWL_API_KEY`。
- 如果自托管 Firecrawl，准备足够服务器资源，并和轻量 License 服务隔离。
- 对被限制平台，提供真实竞品链接、复制文本、字幕、导出文件或截图 OCR 文本。

新手步骤：

1. 如果使用 Firecrawl，在 `.env` 添加：

```env
WEB_DATA_PROVIDER=auto
FIRECRAWL_API_KEY=fc-your-key
FIRECRAWL_BASE_URL=https://api.firecrawl.dev/v2
```

2. 测试 Firecrawl 抓取。

```powershell
python scripts\web_data_provider.py --provider firecrawl --out-dir ".\promotion-output" scrape --url "https://你的真实产品链接"
```

3. 跑多关键词爆款发现。

```powershell
python scripts\multi_query_viral_discovery.py `
  --workflow-manifest ".\promotion-output\reports\promotion-manager\agent-run\workflow-manifest.json" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --top-n 20 `
  --out-dir ".\promotion-output"
```

4. 如果某些平台抓不到，创建人工证据文件夹。

```powershell
python scripts\viral_evidence_inbox_setup.py `
  --product-url "https://你的真实产品链接" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --inbox-dir ".\viral-evidence-inbox" `
  --out-dir ".\promotion-output"
```

5. 把真实竞品链接、复制文本、字幕、导出文件或 OCR 文本放进 `viral-evidence-inbox`。

6. 导入证据。

```powershell
python scripts\viral_evidence_inbox.py `
  --inbox-dir ".\viral-evidence-inbox" `
  --out-dir ".\promotion-output"
```

验收证据：

- `promotion-output/reports/promotion-manager/web-data/*.json`
- `promotion-output/reports/promotion-manager/competitors/viral-content-library.json`
- `promotion-output/reports/promotion-manager/competitors/creator-leaderboard.json`
- `promotion-output/reports/promotion-manager/competitors/deep-competitor-library.json`

## 4. 插件和商业化基础设施

当前约 75%。本地代码、打包、License 服务、PostgreSQL 状态存储、hosted worker、商店材料和法律页面草稿已经有基础，但生产 100% 需要真实外部服务。

Codex 可以完成：

- 维护插件代码和打包脚本。
- 维护 License 后端、数据库迁移、hosted worker。
- 维护隐私政策、服务条款、退款政策、支持页面和商店文案。
- 根据你的服务器日志或商店审核反馈继续修复。

必须你完成：

- 购买或准备服务器。
- 准备域名和 HTTPS。
- 注册并激活 Stripe live。
- 注册 Chrome Web Store 和 Microsoft Edge Add-ons 开发者账号。
- 在服务器环境变量里填写真实密钥。
- 提交商店审核并处理审核问题。

新手步骤：

1. 连接服务器。

```bash
ssh root@your-server-ip
```

2. 安装基础服务。

```bash
sudo apt update
sudo apt install -y nodejs npm postgresql nginx git
```

3. 克隆仓库。

```bash
git clone https://github.com/hqwzhu/Viral-Product-Copy-Video-Generator.git
cd Viral-Product-Copy-Video-Generator/backend/license-service
```

4. 安装依赖。

```bash
npm install
```

5. 创建 PostgreSQL 数据库和用户。

```bash
sudo -u postgres psql
```

进入 `psql` 后执行：

```sql
CREATE DATABASE enhe_promotion_manager;
CREATE USER enhe_pm WITH PASSWORD '请替换成强密码';
GRANT ALL PRIVILEGES ON DATABASE enhe_promotion_manager TO enhe_pm;
\q
```

6. 复制生产环境变量模板，在服务器上填写真实值。

```bash
cp ../../deploy/promotion-manager/.env.production.example .env
nano .env
```

7. 运行数据库迁移。

```bash
npm run migrate
```

8. 按 `deploy/promotion-manager/README.md` 配置 systemd 服务、Nginx 和 HTTPS。

9. 在本地打包插件。

```powershell
python scripts\package_browser_extension.py --out-dir ".\dist\v0.5.3"
```

10. 把生成的 ZIP 提交到 Chrome Web Store 和 Microsoft Edge Add-ons。

验收证据：

- HTTPS health check 成功。
- 数据库迁移完成。
- Stripe webhook 能更新 License 状态。
- 插件能连接生产 License endpoint。
- hosted run 能从插件提交并由 worker 完成。
- Chrome/Edge 商店状态为 approved。

## 5. 真正全自动发布

当前约 40%。这不是简单开发问题，而是平台授权和政策问题。没有官方 API、没有审核通过、没有用户授权，就不能自动发布。

Codex 可以完成：

- 生成发布队列和 dry-run。
- 检查 Token、视频文件、账号授权、审批变量是否齐全。
- 对 GitHub、YouTube 这类已有官方授权路径的平台，在全部门槛满足后调用官方 API。
- 对抖音、知乎、小红书等当前无法确认或无法获取官方创作者发布授权的平台生成手动或浏览器辅助发布包。
- 写审计日志和明确错误。

必须你完成：

- 创建 GitHub fine-grained token 或 GitHub App。
- 创建 Google Cloud OAuth 应用并启用 YouTube Data API v3。
- 完成平台审核、OAuth 授权和账号绑定。
- 每次真实发布前手动确认。

新手步骤：

1. 设置 GitHub token。

```powershell
$env:GITHUB_TOKEN="github_pat_xxx"
```

2. 设置 YouTube OAuth。

```powershell
$env:GOOGLE_OAUTH_CLIENT_ID="your-client-id"
$env:GOOGLE_OAUTH_CLIENT_SECRET="your-client-secret"
```

3. 抖音改为半自动发布。

- 使用生成的标题、文案、标签、MP4、封面图和详情图。
- 在抖音创作者页面中可见操作，Codex 只能辅助填表，不能自动登录、绕过验证码或点击最终发布。
- 发布后登记真实 URL 和截图/导出证据。

4. 先 dry-run。

```powershell
python scripts\publish_readiness_runner.py `
  --workflow-manifest ".\promotion-output\reports\promotion-manager\agent-run\workflow-manifest.json" `
  --build-queue `
  --github-repo hqwzhu/Viral-Product-Copy-Video-Generator `
  --youtube-video-file ".\promotion-output\videos\product-youtube.mp4" `
  --douyin-video-file ".\promotion-output\videos\product-douyin.mp4" `
  --out-dir ".\promotion-output"
```

5. 检查 dry-run 报告，确认没有 missing，再允许真实发布。

```powershell
$env:I_APPROVE_PUBLISH="true"
$env:PUBLISH_DRY_RUN="false"
```

6. 执行官方 API 发布，只针对已授权平台；抖音仍走半自动发布包。

```powershell
python scripts\final_capability_runner.py `
  --url "https://你的真实产品链接" `
  --platforms youtube,douyin,github `
  --github-repo hqwzhu/Viral-Product-Copy-Video-Generator `
  --youtube-video-file ".\promotion-output\videos\product-youtube.mp4" `
  --douyin-video-file ".\promotion-output\videos\product-douyin.mp4" `
  --execute-publish `
  --approval I_APPROVE_PUBLISH `
  --out-dir ".\promotion-output"
```

验收证据：

- `publish-readiness.json` 显示目标平台 ready。
- 官方执行报告 status 为 success。
- 真实 published URL 已登记。
- 审计日志包含平台、状态、内容 ID、URL、时间和错误信息。

## 6. 创作者任务、结算和 Monetize 市场

当前约 30%。现在是蓝图，不是可运营市场。建议先做人工结算 MVP。

Codex 可以完成：

- 创建数据库模型和 API。
- 创建运营 CLI 或管理后台流程。
- 把真实发布 URL、平台导出、订单/收入导出接入证据审核。
- 生成 CPS/CPE/CPM 结算建议。
- 添加结算公式测试。

必须你完成：

- 决定法律主体。
- 开通 Stripe Connect 或其他付款渠道。
- 制定创作者条款、广告主条款、退款/争议/税务流程。
- 招募试点创作者和广告主。
- 真实付款前人工审核。

新手步骤：

1. 先定义一个试点活动，不要先做全自动市场。
2. 准备产品 URL、目标平台、交付物、预算、结算方式、截止日期、证据要求。
3. 让 Codex 根据你确认的范围创建 MVP 数据库和 API。
4. 找一个创作者手动发布内容。
5. 让创作者提交真实 URL 和截图/导出。
6. 用 `real_evidence_inbox.py` 导入证据。
7. 生成结算建议。
8. 由你人工确认是否付款。

验收证据：

- 真实 campaign 存在。
- 真实 creator submission 存在。
- 真实 published URL 和证据已导入。
- 结算建议来自真实证据。
- 人工付款决策已记录。
- 没有用虚构指标付款。

## 可参考的开源项目

- `firecrawl/firecrawl`：用于 Search、Scrape、Map、Crawl、Batch Scrape、Interact 和未来 MCP 网页证据层。
- `yikart/AiToEarn`：用于参考 Create、Publish、Engage、Monetize 的产品架构和任务流。
- `stripe-samples`：用于参考 Checkout、Customer Portal、Webhook、Stripe Connect。
- `openmeterio/openmeter`、`getlago/lago`、`unkeyed/unkey`：用于参考计量、账单、API key、额度和限流。

不能照搬的做法：

- Cookie 抓包。
- 模拟登录。
- 私有或未验证接口。
- 隐藏 token 复用。
- 绕过验证码或风控。
- 自动点赞、关注、评论、私信。
- 浏览器自动点击最终发布。
- 虚构播放量、订单、收入或发布 URL。

## 生成最新中文操作清单

每次代码或策略变化后，运行：

```powershell
python scripts\operator_action_checklist.py --out-dir ".\promotion-output"
```

输出文件：

- `promotion-output/reports/promotion-manager/capability/operator-action-checklist.zh-CN.json`
- `promotion-output/reports/promotion-manager/capability/operator-action-checklist.zh-CN.md`

## 最终验收命令

```powershell
python scripts\completion_roadmap.py --out-dir ".\promotion-output"
python scripts\operator_action_checklist.py --out-dir ".\promotion-output"
python scripts\platform_capabilities.py --out-dir ".\promotion-output"
python scripts\final_capability_audit.py --skip-runtime-checks --out-dir ".\promotion-output\verification"
python -m compileall -q scripts
python scripts\test_promotion_manager.py
```

如果这些命令通过，只能说明本地代码、文档、生成器和 dry-run 能力达标。生产 100% 仍必须以真实账号、真实授权、真实服务、真实发布 URL、真实指标和真实结算记录为准。
