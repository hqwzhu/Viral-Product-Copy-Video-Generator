# 安装指南

本文面向 Windows PowerShell，也给出跨平台提示。公开发行包含本地 Codex Skill、Chrome Manifest V3 扩展和校验脚本；Hosted Worker 保持关闭，不需要为本地工作流部署服务端。

## Windows 首选安装检查

克隆公开仓库并进入 `skill\viral-product-copy-video-generator` 后，先运行这组 Windows PowerShell 命令：

```powershell
python --version
python -m pip install playwright pillow
python -m playwright install chromium
python scripts\self_evolution_audit.py --skip-runtime-checks --out-dir ".\promotion-output\install-audit"
```

这组命令安装浏览器与图片依赖并执行只读安装审计。FFmpeg 和 YouTube 官方 API 客户端按需单独安装，见下文。

## 路径一：Chrome Web Store

适合只需要当前页面转任务和命令生成的用户。

1. 打开 [ENHE Promotion Manager](https://chromewebstore.google.com/detail/enhe-promotion-manager/dloklkbnmoigemnfigbkibogmgbieppl)。
2. 点击“添加至 Chrome”，确认浏览器安装提示。
3. 打开一个公开产品页面，完成你的登录或页面准备后，主动点击扩展图标。
4. 点击“使用当前标签页”，选择平台、工作流深度和命令类型，再复制命令到本地仓库运行。

商店当前公开版本（发布前）为 `0.5.2`；公开仓库源码和待发行包为 `0.5.3`。安装后请以扩展界面显示的版本和 [版本同步说明](version-sync.md) 为准。

## 路径二：未打包扩展

适合需要审阅源码、参与测试或使用尚未提交商店的版本。

```powershell
git clone https://github.com/hqwzhu/enhe-promotion-manager.git
cd .\enhe-promotion-manager
```

1. 在 Chrome 地址栏打开 `chrome://extensions`。
2. 打开右上角“开发者模式”。
3. 点击“加载已解压的扩展程序”。
4. 选择仓库里的 `extension\chrome` 文件夹。
5. 打开产品页面并在用户主动操作后使用“使用当前标签页”。

扩展只读取当前标签页的可见入口并生成本地命令；它不会把 Cookies、Chrome 登录配置或页面登录态上传到本公开仓库或公开发行包。

## 路径三：Skill ZIP 或源码

适合需要完整本地流程、脚本输出、媒体草稿、发布包和真实证据复盘的用户。先安装 Python 3.10 或更高版本（推荐 Python 3.11），并确认 PowerShell 中可调用：

```powershell
python --version
```

### 使用公开仓库源码

```powershell
git clone https://github.com/hqwzhu/enhe-promotion-manager.git
cd .\enhe-promotion-manager\skill\viral-product-copy-video-generator
python -m pip install --upgrade pip
```

公开仓库把 Skill 放在 `skill\viral-product-copy-video-generator`；进入该目录后，`SKILL.md` 和 `scripts\skill_entry.py` 位于当前目录。无需订阅，不要求 Hosted Worker。

### 使用 Skill ZIP

从 [GitHub Releases](https://github.com/hqwzhu/enhe-promotion-manager/releases) 下载 `enhe-product-promo-maker-skill-0.5.3.zip`，在 PowerShell 中解压到你管理 Codex Skill 的目录：

```powershell
$skillHome = "$HOME\.codex\skills"
New-Item -ItemType Directory -Force $skillHome | Out-Null
Expand-Archive -Path ".\enhe-product-promo-maker-skill-0.5.3.zip" `
  -DestinationPath $skillHome -Force
```

解压后确认 `$skillHome\viral-product-copy-video-generator\SKILL.md` 和 `$skillHome\viral-product-copy-video-generator\scripts\skill_entry.py` 存在。

安装或替换 Skill 后，完全退出并重新打开 Codex，或在客户端中刷新 Skill 发现并新建任务，确保新版本被重新加载。

如需把已审核源码同步到 Codex Skill 目录，只能从一个独立克隆的公开仓库 Skill 目录运行 `--sync-installed-skill`。不要从 `$skillHome\viral-product-copy-video-generator` 目标目录运行同步命令；源文件与目标文件相同时会发生同文件复制错误。

## 校验发行包 SHA-256

从同一 GitHub Release 下载 `SHA256SUMS`、`enhe-product-promo-maker-skill-0.5.3.zip` 和 `enhe-promotion-manager-extension-0.5.3.zip`，放在同一目录，然后同时校验 Skill 与扩展包：

```powershell
$releaseFiles = @(
  "enhe-product-promo-maker-skill-0.5.3.zip",
  "enhe-promotion-manager-extension-0.5.3.zip"
)
$sumLines = Get-Content ".\SHA256SUMS"
foreach ($name in $releaseFiles) {
  $record = $sumLines | Where-Object { $_.EndsWith($name) } | Select-Object -First 1
  if (-not $record) { throw "SHA256SUMS 中缺少 $name" }
  $expected = ($record -split "\s+")[0]
  $actual = (Get-FileHash -LiteralPath ".\$name" -Algorithm SHA256).Hash
  if ($actual -ne $expected) { throw "$name SHA-256 校验失败" }
  Write-Host "$name SHA-256 OK"
}
```

任一哈希不一致时不要安装，重新从正式发行页下载并再次校验。

## 可选依赖

### Playwright、Chromium 与 Pillow

用于动态产品页、浏览器可见平台页面和浏览器辅助表单：

```powershell
python -m pip install playwright pillow
python -m playwright install chromium
```

也可以在明确参数下让运行命令尝试安装 Chromium：

```powershell
python scripts\skill_entry.py `
  --link "https://example.com/product" `
  --install-browser-if-missing `
  --out-dir ".\promotion-output"
```

### FFmpeg

用于 MP4 视频草稿。Windows 可使用：

```powershell
winget install Gyan.FFmpeg
ffmpeg -version
```

### YouTube 官方 API（可选）

仅在你拥有自己的 OAuth 凭据、账号授权并需要官方 API 路径时安装：

```powershell
python -m pip install -r requirements-youtube.txt
```

凭据只通过本机环境变量或本机 `.env` 管理；不要提交或复制到公开仓库。

## MediaCrawler Sidecar（独立上游依赖）

知乎、小红书、抖音的本机登录态研究可以使用 MediaCrawler Sidecar。它不是本仓库内置组件，需要你按 [MediaCrawler 上游项目](https://github.com/NanmiCoder/MediaCrawler) 的许可证、安装说明和平台条款单独取得授权与安装。Sidecar 代码、checkout、虚拟环境、Cookies、Chrome profile、原始 JSONL 输出和身份盐应位于本公开仓库之外；本仓库只保留受控边界脚本和归一化结果。

Sidecar 默认数据根目录为 Windows 的 `%LOCALAPPDATA%\ENHE\promotion-manager\mediacrawler`。安装后应固定到文档和脚本要求的上游提交，并在本机完成登录。若未就绪，平台结果会标记为 `provider_unavailable`，不会伪造内容。

## 安装边界

- Hosted Worker 保持关闭，不需要部署、配置或购买托管运行。
- Cookies 与 Chrome 登录配置只留在本机，不上传到本公开仓库或公开发行包。
- 最终发布需要用户审核和操作；官方 API 还需要用户凭据与明确批准。
- 工具不会规避 CAPTCHA、平台风险控制、登录检查或账号授权。
- 真实 URL、指标、评论、订单和收入才可进入真实证据；不会虚构证据。
- 支付、订阅、许可证、点数和账单后端仅排除在同步结论之外；扩展原有 billing UI 和 `billing-contract.json` 保留。

更多运行说明见 [快速开始](quick-start.md) 和 [Skill 指南](skill-guide.md)。
