# 安装教程

本项目是一个本地 Codex Skill 加脚本工具集。它可以不依赖 SaaS 后端运行；浏览器插件的商业化订阅、License 和 Hosted Run 需要你额外部署支付和授权后端。

## 环境要求

- Windows PowerShell、macOS shell 或 Linux shell。
- Python 3.10 或更高版本。
- Git。
- 可选：Playwright Chromium，用于读取动态网页和抓取浏览器可见平台搜索页。
- 可选：ffmpeg，用于渲染 MP4 视频文件。
- 可选：Pillow，用于生成发布包里的 PNG 封面图和详情图。

## 克隆仓库

```powershell
git clone https://github.com/hqwzhu/Viral-Product-Copy-Video-Generator.git
cd Viral-Product-Copy-Video-Generator
```

## 检查 Python

```powershell
python --version
```

## 安装可选浏览器运行时

当你希望 Codex 读取动态产品页、搜索公开平台页面或浏览器可见证据时安装：

```powershell
python -m pip install playwright
python -m playwright install chromium
```

也可以让工作流在明确参数下尝试安装官方 Playwright Chromium：

```powershell
python scripts\skill_entry.py `
  --link "https://example.com/product" `
  --install-browser-if-missing `
  --out-dir ".\promotion-output"
```

## 安装可选视频运行时

Windows:

```powershell
winget install Gyan.FFmpeg
```

验证：

```powershell
ffmpeg -version
```

## 安装可选图片运行时

当需要让 `media_asset_pack.py` 生成封面图和详情图时安装：

```powershell
python -m pip install pillow
```

## 安装为 Codex Skill

先验证本地文件，再同步到 Codex Skill 目录：

```powershell
python scripts\self_evolution_audit.py `
  --sync-installed-skill `
  --approval I_APPROVE_SKILL_SYNC `
  --out-dir ".\promotion-output"
```

同步只覆盖受管理文件，例如 `SKILL.md`、`references/`、`scripts/`、`docs/`、`README.md`、`README.en.md`、`README.zh-CN.md` 和 `browser-extension/`。

## 验证安装

```powershell
python scripts\test_promotion_manager.py
python -m compileall -q scripts
python scripts\final_capability_audit.py --out-dir ".\promotion-output"
python scripts\final_capability_readiness.py --out-dir ".\promotion-output"
```

## 安全注意事项

- 不要把 API key 写入仓库文件。
- 平台凭证使用环境变量。
- 官方发布必须提供 `I_APPROVE_PUBLISH`。
- Skill 不会绕过登录、验证码、平台风控或最终发布动作。
