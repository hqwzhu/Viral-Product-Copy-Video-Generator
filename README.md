# ENHE Promotion Manager

ENHE Promotion Manager is a Codex Skill for turning any product URL, website URL, app page, or GitHub repository into a repeatable product promotion loop.

The Skill is designed for operators who want Codex to work as a website and product promotion manager:

- Read one or many product URLs and pass structured browser evidence into product intake.
- Search and rank viral creators, posts, videos, and repositories across YouTube, Zhihu, Xiaohongshu, Douyin, GitHub, TikTok, and similar platforms.
- Generate platform-native titles, articles, notes, voiceover scripts, storyboards, README copy, release copy, and MP4 draft videos.
- Prepare guarded publish queues for official APIs where supported and browser/manual payloads where direct publishing is not safe or available.
- Recover real post-publish metrics, comments, demand signals, orders, and revenue only from real evidence.
- Run retrospective and next-round optimization without fabricating performance data.

Repository: [hqwzhu/Viral-Product-Copy-Video-Generator](https://github.com/hqwzhu/Viral-Product-Copy-Video-Generator.git)

## Current Capability

The repository implements the local Codex Skill workflow and safety gates. It does not bypass platform login, captcha, risk controls, app review, or account authorization.

| Area | Status | Notes |
| --- | --- | --- |
| Product URL reading | Ready | Browser snapshots, structured JSON intake, static fallback, URL discovery, and batch runner are included. |
| Viral research | Ready with access limits | YouTube and GitHub can use public or official paths. Zhihu, Xiaohongshu, Douyin, and TikTok use browser-visible evidence, official access, or user exports. |
| Copy and video generation | Ready | Platform-native copy and ffmpeg MP4 rendering are included. Voiceover can use an audio file or Windows review-quality TTS. |
| Publishing | Partial | GitHub, YouTube, Douyin, and TikTok require credentials, platform authorization, app scopes, and explicit approval. Zhihu and Xiaohongshu default to manual or browser-assisted flows. |
| Metrics and revenue | Waiting for real evidence | The Skill can import and recover real data, but it cannot invent published URLs, platform metrics, orders, or revenue. |
| Self-evolution | Controlled | The Skill can audit tools, docs, repo state, and installed Skill drift. It only syncs or installs allowlisted runtimes with explicit commands. |
| Browser extension | MVP included | `browser-extension/` captures the current tab, builds Codex commands, estimates subscription cost, and links to ENHE. A real paid launch still needs a backend license and payment service. |

## Install

Clone the repo:

```powershell
git clone https://github.com/hqwzhu/Viral-Product-Copy-Video-Generator.git
cd Viral-Product-Copy-Video-Generator
```

Verify Python:

```powershell
python --version
```

Optional browser runtime for rendered product pages and platform search:

```powershell
python -m pip install playwright
python -m playwright install chromium
```

Optional MP4 rendering runtime:

```powershell
winget install Gyan.FFmpeg
```

Run tests:

```powershell
python scripts\test_promotion_manager.py
python -m compileall -q scripts
```

More detail: [docs/installation.md](docs/installation.md)

## Quick Start

Run the one-link Codex Skill entry:

```powershell
python scripts\skill_entry.py `
  --link "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --out-dir ".\promotion-output"
```

Run a website URL and discover product pages from it:

```powershell
python scripts\skill_entry.py `
  --link "https://example.com" `
  --link-mode site `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --out-dir ".\promotion-output"
```

Run the final capability runner directly:

```powershell
python scripts\final_capability_runner.py `
  --discover-from-url "https://example.com" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --run-follow-up-captures `
  --sample-video-frames `
  --out-dir ".\promotion-output"
```

Review readiness:

```powershell
python scripts\final_capability_audit.py --out-dir ".\promotion-output"
python scripts\self_evolution_audit.py --out-dir ".\promotion-output"
python scripts\final_capability_readiness.py --out-dir ".\promotion-output"
```

## Browser Extension

The Chrome Manifest V3 extension lives in [browser-extension](browser-extension/). It is a lightweight operator cockpit:

- Captures the active tab URL and title.
- Lets the user select target platforms and run depth.
- Generates a Codex command for `scripts/skill_entry.py`.
- Estimates token-backed subscription usage from planned runs.
- Stores a license key locally and can call a configurable ENHE license endpoint.
- Opens ENHE checkout and customer billing portal URLs.
- Documents the backend license, usage ledger, and webhook contract needed for real paid hosted runs.
- Shows developer and website links for ENHE traffic.

Load it in Chrome:

1. Open `chrome://extensions`.
2. Enable Developer mode.
3. Click Load unpacked.
4. Select the `browser-extension` folder.

Full guide: [docs/browser-extension.md](docs/browser-extension.md)

## Subscription Model

The extension includes a pricing calculator, checkout entry, billing portal entry, license validation, and a machine-readable backend contract. Real billing must still be handled by a backend payment provider and license API. Chrome Web Store Payments is deprecated, so do not rely on the old Web Store billing API for a new paid extension.

The starter commercial model is in [docs/subscription-pricing.md](docs/subscription-pricing.md). It uses a credit quota so heavy token users cannot create a loss:

- Free: local command generation and limited trial credits.
- Starter: USD 29/month for small operators.
- Growth: USD 99/month for repeated product promotion.
- Scale: USD 299/month for agencies or teams.

The docs include the formulas, cost assumptions, and backend usage-control contract used for the initial launch model. Recalculate the numbers from real usage logs before public launch.

## Safety Gates

The Skill intentionally blocks unsafe claims and unsafe platform operations:

- No auto-login.
- No captcha or risk-control bypass.
- No cookie, token, password, or hidden credential extraction.
- No final publish click in browser-assisted flows.
- No fabricated views, likes, comments, orders, or revenue.
- Official publishing requires credentials, target data, and `I_APPROVE_PUBLISH`.
- Installed Skill sync requires `I_APPROVE_SKILL_SYNC`.

## Typical Workflow

```text
product URL or website URL
  -> Codex/browser structured intake
  -> platform and competitor discovery
  -> viral material library
  -> creator leaderboard and follow-up capture
  -> copy, script, storyboard, MP4 draft
  -> cheat-on-content style review and scorecard
  -> guarded publish queue
  -> official or browser/manual publish
  -> real metrics, comments, order, and revenue import
  -> retrospective and next-round optimization
```

## Key Commands

Product URL reader:

```powershell
python scripts\product_url_reader.py --url "https://example.com/product" --out-dir ".\promotion-output"
```

Viral discovery:

```powershell
python scripts\viral_discovery_runner.py `
  --query "AI product copy generator" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --top-n 20 `
  --out-dir ".\promotion-output"
```

Render MP4:

```powershell
python scripts\render_video.py `
  --content-json ".\promotion-output\reports\promotion-manager\generated-content\product-platform-content.json" `
  --platform douyin `
  --out ".\promotion-output\videos\product-douyin.mp4"
```

Publish readiness:

```powershell
python scripts\publish_readiness_runner.py `
  --workflow-manifest ".\promotion-output\reports\promotion-manager\agent-run\workflow-manifest.json" `
  --build-queue `
  --github-repo owner/repo `
  --out-dir ".\promotion-output"
```

Browser-assisted publishing payloads:

```powershell
python scripts\browser_publish_assistant.py `
  --publish-queue ".\promotion-output\reports\promotion-manager\publish-queue\publish-queue.json" `
  --out-dir ".\promotion-output"
```

Recover metrics:

```powershell
python scripts\metrics_recovery.py `
  --metrics-json ".\promotion-output\reports\promotion-manager\post-publish-capture\post-publish-metrics-export.json" `
  --business-csv ".\orders-and-revenue.csv" `
  --out-dir ".\promotion-output"
```

## Documentation

- [Installation](docs/installation.md)
- [Usage](docs/usage.md)
- [Browser extension](docs/browser-extension.md)
- [Subscription pricing](docs/subscription-pricing.md)
- [Billing backend contract](docs/billing-backend-contract.md)
- [Final capability map](docs/final-capability-map.md)

## License

MIT. See [LICENSE](LICENSE).
