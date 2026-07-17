# ENHE 产品推广素材生成器

把产品网页变成推广文案、视频脚本和发布素材。

[English](README.en.md) | [官方网站](https://www.enhe-tech.com.cn/) | [产品页面](https://www.enhe-tech.com.cn/promotion-manager) | [Chrome 商店](https://chromewebstore.google.com/detail/enhe-promotion-manager/dloklkbnmoigemnfigbkibogmgbieppl)

```text
产品网页 -> 产品事实 -> 爆款/竞品证据 -> 平台文案 -> 视频脚本与素材 -> 发布包 -> 真实数据复盘
```

给它一个公开产品网页，ENHE 产品推广素材生成器会在本机整理可核查的产品事实与公开证据，为 YouTube、知乎、小红书、抖音、GitHub 等渠道生成适配草稿，并把视频、图片、发布检查项和后续复盘入口组织成一套可执行文件。它面向独立开发者、产品团队、内容运营者和服务商；不承诺固定流量或转化结果，也不会替代账号所有者完成最终发布。

## 你提供一个产品网页，我们交付什么

一次标准运行会在本地输出：

- 产品事实与证据：产品定位、功能、目标用户、页面原文引用、来源链接、证据状态与风险提示。
- 平台文案草稿：标题、正文、标签、简介、首批评论或回复提示，并针对不同平台调整结构。
- 视频脚本与分镜：口播稿、镜头节奏、画面建议、字幕重点和素材清单。
- 媒体草稿：依赖可用时渲染 MP4 视频草稿；安装 Pillow 后生成 PNG 封面图与详情图。
- 发布包：平台文案、视频与图片路径、跟踪链接、缺失项、风险提示、人工步骤和发布前清单。
- 证据收件箱：用于导入真实发布 URL、指标、评论、订单与收入导出，不把演示数据当成真实结果。
- 复盘报告：基于真实数据比较内容表现、受众反馈与业务证据，形成下一轮优化建议。

如果页面无法完整读取、媒体依赖缺失或平台访问受限，结果会标记为 `partial_ready`、`missing` 或相应阻塞状态，便于你继续补采或人工处理。

## 它解决的不是“写一篇文案”，而是整套推广准备

普通文案工具常把产品链接压缩成一段泛化文字，后续仍需人工核对事实、寻找参考内容、重写平台格式、制作视频与图片、整理发布字段、记录链接并复盘数据。本项目把这些步骤连成同一个本地工作流：

1. 读取一个产品页、多个链接或整站产品入口。
2. 保留可追溯事实，区分页面证据、公开平台证据、用户导入证据和缺失信息。
3. 研究公开或浏览器可见的竞品、创作者与高表现内容结构。
4. 生成平台原生草稿，而不是把同一段文字复制到所有渠道。
5. 产出口播稿、分镜、可选 MP4、封面图、详情图和完整发布包。
6. 在用户审核后辅助发布，并在发布后接收真实数据。
7. 用真实数据完成复盘，形成下一轮选题、钩子和素材建议。

这样，交付物不仅能看，还能被审核、补全、发布、登记和迭代。

## Skill 与 Chrome 插件如何配合

Chrome 插件是轻量入口，Codex Skill 是本地执行引擎。

| 组件 | 主要作用 | 适合什么时候用 |
| --- | --- | --- |
| Chrome 插件 | 在用户点击后读取当前标签页 URL 和标题，选择平台、工作流深度与命令类型，生成可复制的本地命令 | 正浏览产品页面，希望快速建立任务时 |
| Codex Skill | 读取产品、研究证据、生成内容和媒体草稿、组织发布包、导入真实数据并复盘 | 需要完整执行、文件交付和审计记录时 |

典型路径是：打开产品页面 → 点击插件“使用当前标签页” → 选择目标平台 → 复制生成的 PowerShell 命令 → 在公开仓库的 Skill 目录运行 → 审核 `promotion-output`。插件可以单独生成命令，Skill 也可以不依赖插件直接运行。

扩展原有支付、订阅、许可证、点数和账单界面仍保留，但这些能力不纳入本次“扩展非支付命令与随包 Skill 同步”的结论。Hosted Worker 关闭；公开版不把托管执行描述为可用能力。

## 核心功能与用户收益

- 从网页到事实档案：减少手工摘录，降低把推测写成产品能力的风险。
- 从公开证据到内容方向：保留来源和状态，让钩子、结构与平台选择更容易复核。
- 从一个产品到多平台草稿：减少重复改写，同时保留各平台的表达差异。
- 从脚本到媒体草稿：在本机依赖可用时生成 MP4、PNG 封面图和详情图，缩短制作准备时间。
- 从散落文件到发布包：把文案、标签、视频、图片、警告和操作步骤放在同一交付结构中。
- 从发布到真实复盘：接收真实 URL、指标、评论、订单和收入导出，用证据推动下一轮优化。
- 从网页入口到本地任务：Chrome 插件把当前页面快速转换为可审计命令，无需复制多段参数。
- 中英文界面：插件可切换中文与英文，便于不同成员使用同一工作流。

完整能力表见 [功能目录](docs/zh-CN/features.md)。

## 五分钟开始使用

Windows PowerShell：

```powershell
git clone https://github.com/hqwzhu/enhe-promotion-manager.git
cd .\enhe-promotion-manager\skill\viral-product-copy-video-generator

python scripts\skill_entry.py `
  --link "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --out-dir ".\promotion-output"
```

先打开批次报告：

```text
promotion-output\reports\promotion-manager\batch\product-batch-runner.json
```

报告的 `promotionRuns` 数组会给出每个产品的 `outputDir`、`workflowManifest` 和 `publishQueue`。产品内容、视频、图片、发布包与复盘位于对应的 `promotion-output\product-batch-runs\<run>`；`<run>` 由运行时生成，不应手工猜测。MP4、浏览器动态读取和 PNG 图片属于可选增强能力；缺少对应依赖时，文本交付仍可继续，并明确标记媒体缺失。

你也可以直接从 [Chrome Web Store](https://chromewebstore.google.com/detail/enhe-promotion-manager/dloklkbnmoigemnfigbkibogmgbieppl) 安装插件，或按 [安装指南](docs/zh-CN/installation.md) 使用 `extension\chrome` 未打包扩展和 Skill ZIP。运行本地工作流不需要订阅，也不要求 Hosted Worker。

## 支持的平台和当前边界

| 平台/来源 | 当前可用路径 | 主要边界 |
| --- | --- | --- |
| 产品网页与网站 | 静态读取、Playwright 浏览器快照、站点链接发现、站点地图或用户保存的 HTML | 动态页面可能需要 Chromium；登录后私有页面不作为公共默认来源 |
| YouTube | 公开页面、公开/官方数据路径、内容草稿、官方 API dry-run 与凭据检查 | 真实上传需要用户凭据、平台授权和明确批准 |
| GitHub | 公开仓库证据、README/Issue/Release 等发布草稿与受控官方路径 | 写入真实仓库前必须确认目标、权限与批准 |
| 知乎 | 公开或浏览器可见页面、用户导出、可选本机 Sidecar 登录态 | 登录、平台验证或风控出现时由用户处理，证据可能为部分就绪 |
| 小红书 | 公开或浏览器可见页面、用户导出、可选本机 Sidecar 登录态 | 页面结构、登录与风控会影响采集；发布通常走手动或浏览器辅助 |
| 抖音 | 公开或浏览器可见页面、用户导出、可选本机 Sidecar 登录态 | 平台验证、登录和官方发布权限属于外部门槛 |

研究只使用公开、浏览器可见、官方授权或用户主动提供的数据。系统不会规避平台验证、登录检查或风险控制。最终发布由用户确认；浏览器辅助流程在最终提交前停止。

## 本地优先、安全可审计

- 输出默认写入你指定的本地目录；公开仓库和发布包不包含运行态输出。
- Cookies 与 Chrome 登录配置只留在本机，不上传到本公开仓库或公开发行包。
- MediaCrawler Sidecar 是单独安装的上游依赖，使用本机 Chrome 登录态时，其 checkout、虚拟环境、配置和原始输出均位于公开仓库之外。
- Hosted Worker：关闭。公开版不要求、也不提供托管执行。
- 平台发布需要用户审核与操作；官方 API 路径还需要用户自己的凭据、账号授权和明确批准。
- 只登记真实发布 URL、真实指标、真实评论、真实订单和真实收入；不会虚构证据。
- 支付、订阅、许可证、点数和账单后端仅排除在功能同步结论之外，扩展既有 billing UI 和 `billing-contract.json` 继续保留。

隐私说明见 [数据与隐私](docs/zh-CN/data-and-privacy.md) 和 [隐私政策](https://www.enhe-tech.com.cn/promotion-manager/privacy)。

## 当前版本与下载

- 公开仓库、Skill 和扩展源码：`0.5.3`
- Chrome 商店当前公开版本（发布前）：`0.5.2`
- 公开发行页：[GitHub Releases](https://github.com/hqwzhu/enhe-promotion-manager/releases)
- Skill 包：`enhe-product-promo-maker-skill-0.5.3.zip`
- 扩展包：`enhe-promotion-manager-extension-0.5.3.zip`
- Chrome 商店现有条目：[ENHE Promotion Manager](https://chromewebstore.google.com/detail/enhe-promotion-manager/dloklkbnmoigemnfigbkibogmgbieppl)

版本关系、11 项非支付命令同步结果和商店更新边界见 [版本同步说明](docs/zh-CN/version-sync.md)。

## 创作者与联系信息

- 品牌与创作者：ENHE AI
- 运营主体：深圳市龙岗区恩禾网络科技工作室
- 网站：https://www.enhe-tech.com.cn/
- 产品页面：https://www.enhe-tech.com.cn/promotion-manager
- 联系邮箱：huqingwei5942@gmail.com
- GitHub：https://github.com/hqwzhu

安全问题请按 [安全政策](SECURITY.md) 私下报告。产品使用问题可先查阅 [故障排查](docs/zh-CN/troubleshooting.md)。

## 开源许可与第三方组件

`LICENSE` 当前记录 `Copyright (c) 2026 HU`；`HU` 是该许可文件显示的代码版权标识/权利人。`ENHE AI` 是产品品牌与创作者身份，`深圳市龙岗区恩禾网络科技工作室` 是公开运营与支持主体。授权范围与条件以 `LICENSE` 为准，本说明不修改该许可，也不推断运营主体拥有代码版权。

第三方运行时和上游依赖遵循各自许可证。

MediaCrawler 是独立上游项目，不属于本仓库的 MIT 授权范围。任何面向 ENHE 的商业授权都不会自动把 MediaCrawler 源码再授权给公开用户；使用者需要自行遵守其上游许可证、平台条款和适用法律。更多信息见 [NOTICE](NOTICE.md)。
