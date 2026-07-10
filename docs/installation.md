# Installation

中文版本: [docs/zh-CN/installation.md](zh-CN/installation.md)

This project is a local Codex Skill plus scripts. It can run without a SaaS backend. Browser extension monetization needs a separate backend payment and license service.

## Requirements

- Windows PowerShell, macOS shell, or Linux shell.
- Python 3.10 or newer.
- Git.
- Optional: Playwright Chromium for rendered page reading and platform search snapshots.
- Optional: ffmpeg for MP4 rendering.
- Optional: Pillow for PNG cover and detail image generation.

## Clone

```powershell
git clone https://github.com/hqwzhu/Viral-Product-Copy-Video-Generator.git
cd Viral-Product-Copy-Video-Generator
```

## Python Check

```powershell
python --version
```

## Optional Browser Runtime

Use this when you want Codex to read dynamic product pages or capture browser-visible platform search pages:

```powershell
python -m pip install playwright
python -m playwright install chromium
```

You can also let the workflow attempt the official Playwright browser install:

```powershell
python scripts\skill_entry.py `
  --link "https://example.com/product" `
  --install-browser-if-missing `
  --out-dir ".\promotion-output"
```

## Optional Video Runtime

```powershell
winget install Gyan.FFmpeg
```

Verify:

```powershell
ffmpeg -version
```

## Optional Image Runtime

Use this when you want `media_asset_pack.py` to generate PNG covers and detail images:

```powershell
python -m pip install pillow
```

## Install As A Codex Skill

Copy or sync the reviewed files into the installed Skill directory only after verification:

```powershell
python scripts\self_evolution_audit.py `
  --sync-installed-skill `
  --approval I_APPROVE_SKILL_SYNC `
  --out-dir ".\promotion-output"
```

This copies only managed files such as `SKILL.md`, `references`, `scripts`, `docs`, `README.md`, `README.en.md`, `README.zh-CN.md`, and `browser-extension`.

## Verify

```powershell
python scripts\test_promotion_manager.py
python -m compileall -q scripts
python scripts\final_capability_audit.py --out-dir ".\promotion-output"
python scripts\final_capability_readiness.py --out-dir ".\promotion-output"
```

## Safety Notes

- Do not put API keys in committed files.
- Use environment variables for platform credentials.
- Publishing still needs explicit `I_APPROVE_PUBLISH`.
- The Skill will not bypass login, captcha, platform risk controls, or final publish actions.
