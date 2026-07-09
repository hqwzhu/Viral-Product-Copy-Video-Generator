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

Chinese version: [README.zh-CN.md](README.zh-CN.md)

## Current Capability

The repository implements the local Codex Skill workflow and safety gates. It does not bypass platform login, captcha, risk controls, app review, or account authorization.

| Area | Status | Notes |
| --- | --- | --- |
| Product URL reading | Ready | Browser snapshots, structured JSON intake, static fallback, public web-text fallback, URL discovery, and batch runner are included. |
| Viral research | Ready with access limits | YouTube and GitHub can use public or official paths. Zhihu, Xiaohongshu, Douyin, and TikTok use browser-visible evidence, official access, or user exports. |
| Copy and video generation | Ready | Platform-native copy and ffmpeg MP4 rendering are included. Voiceover can use an audio file or Windows review-quality TTS. |
| Publishing | Partial | GitHub, YouTube, Douyin, and TikTok require credentials, platform authorization, app scopes, and explicit approval. Zhihu and Xiaohongshu default to manual or browser-assisted flows. `launch_unlock_pack.py` builds one setup pack for platform gates, credentials, browser-assisted publish payloads, and real-evidence templates. `browser_publish_session.py` combines payload preparation, visible-field fill, screenshots, final manual publish checklist, and post-publish URL recovery commands. |
| Metrics and revenue | Waiting for real evidence | The Skill can initialize a fillable evidence inbox, run a post-publish performance monitor, import evidence files, recover real data, and optimize the next round, but it cannot invent published URLs, platform metrics, orders, or revenue. |
| Self-evolution | Controlled | The Skill can audit tools, docs, repo state, and installed Skill drift. It only syncs or installs allowlisted runtimes with explicit commands. |
| Browser extension | Store-ready package included | `browser-extension/` captures the current tab, builds Codex commands or hosted run payloads including launch unlock, periodic automation setup/run commands, estimates subscription cost, and links to ENHE. `scripts/package_browser_extension.py` validates MV3, icons, permissions, and remote-code guardrails before building a Chrome/Edge submission zip. `scripts/billing_contract_simulator.py` proves the license, quota, usage, hosted-run request, and webhook contract locally before a real payment backend is deployed. |

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
中文安装教程: [docs/zh-CN/installation.md](docs/zh-CN/installation.md)

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

Use `reports\promotion-manager\final-readiness\final-capability-readiness.md` as the phase progress report after each major stage. It should cover the current stage, completed goals, unfinished goals, next plan, and estimated remaining time.

Build one launch unlock pack for platform access, publish setup, browser-assisted publishing, and real evidence collection:

```powershell
python scripts\launch_unlock_pack.py `
  --publish-queue ".\promotion-output\reports\promotion-manager\publish-queue\publish-queue.json" `
  --publish-readiness ".\promotion-output\reports\promotion-manager\publish-readiness\publish-readiness.json" `
  --out-dir ".\promotion-output"
```

The unlock pack writes a checklist, next-action commands, credential variable-name templates, browser payload references, and real-evidence templates. It does not read or store secret values and does not bypass account authorization.

`scripts\final_capability_runner.py` now builds this unlock pack automatically for each product run when a publish queue exists. Use the standalone command when you want to rebuild the pack after changing credentials, target files, or publisher entry URLs.

Content review now also writes a cheat-on-content bridge pack under `reports\promotion-manager\cheat-review\`. It creates one draft file per platform plus Codex `cheat-score` prompts, but it does not create immutable prediction logs unless you explicitly start a prediction cycle.

After publishing, put real evidence files into a local inbox and recover the loop:

```powershell
python scripts\performance_monitor.py `
  --out-dir ".\promotion-output"
```

Use the monitor after published URLs have been registered. It captures public/browser-visible metrics, captures visible comments and demand signals, attributes optional business exports, runs metrics recovery, writes a history file, and generates next-round recommendations. Before or after publishing, create a fillable evidence inbox:

```powershell
python scripts\real_evidence_inbox_setup.py `
  --product-url "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --inbox-dir ".\promotion-evidence-inbox" `
  --out-dir ".\promotion-output"
```

For several export files, import the evidence inbox:

```powershell
python scripts\real_evidence_inbox.py `
  --inbox-dir ".\promotion-evidence-inbox" `
  --out-dir ".\promotion-output"
```

The inbox can contain files such as `published-urls.csv`, `metrics.csv`, `metrics.xlsx`, `comments.txt`, `comments.html`, `orders.csv`, `orders.xlsx`, or an optional `inbox-manifest.json` with explicit file roles. The runner registers real published URLs, imports visible/exported metrics, captures comment demand signals, attributes orders/revenue, and runs the next-round optimizer.

## Browser Extension

The Chrome Manifest V3 extension lives in [browser-extension](browser-extension/). It is a lightweight operator cockpit:

- Captures the active tab URL and title.
- Lets the user select target platforms and run depth.
- Generates Codex commands for one-link Skill runs, browser publish sessions, evidence inbox setup/recovery, post-publish performance monitoring, final readiness audits, periodic automation configs, due scheduled runs, and Windows Task Scheduler scripts.
- Estimates token-backed subscription usage from command type, run depth, hosted MP4, browser publish, and evidence-recovery options.
- Stores a license key locally, validates it against a configurable ENHE license endpoint, reserves hosted usage credits through the ENHE usage authorization endpoint, and can copy or submit a hosted run payload to the ENHE hosted run endpoint.
- Opens ENHE checkout and customer billing portal URLs.
- Documents the backend license, usage ledger, hosted run, and webhook contract needed for real paid hosted runs.
- Shows developer and website links for ENHE traffic.

Load it in Chrome:

1. Open `chrome://extensions`.
2. Enable Developer mode.
3. Click Load unpacked.
4. Select the `browser-extension` folder.

Full guide: [docs/browser-extension.md](docs/browser-extension.md)

Build the Chrome/Edge store submission package:

```powershell
python scripts\package_browser_extension.py --out-dir ".\dist"
```

Store listing and submission guide: [docs/extension-store-submission.md](docs/extension-store-submission.md)

## Subscription Model

The extension includes a pricing calculator, checkout entry, billing portal entry, license validation, usage credit reservation, hosted-run payload handoff, a machine-readable backend contract, and a local reference simulator for license, usage, hosted-run, and webhook flows. Real billing must still be handled by a backend payment provider and license API. Chrome Web Store Payments is deprecated, so do not rely on the old Web Store billing API for a new paid extension.

The starter commercial model is in [docs/subscription-pricing.md](docs/subscription-pricing.md). It uses a credit quota so heavy token users cannot create a loss:

- Free: local command generation and limited trial credits.
- Starter: USD 29/month for small operators.
- Growth: USD 99/month for repeated product promotion.
- Scale: USD 299/month for agencies or teams.

Run the local billing contract simulator:

```powershell
python scripts\billing_contract_simulator.py demo `
  --plan growth `
  --workflow-type research_run `
  --out-dir ".\promotion-output"
```

The simulator writes `promotion-output\reports\promotion-manager\billing-simulator\billing-simulator.json` and keeps only hashed license keys in its state file.

Validate the hosted-run handoff used by the extension after reserving credits:

```powershell
python scripts\billing_contract_simulator.py demo-hosted-run `
  --plan growth `
  --workflow-type standard_run `
  --product-url "https://example.com/product" `
  --out-dir ".\promotion-output"
```

Validate the periodic automation credit path:

```powershell
python scripts\billing_contract_simulator.py demo `
  --plan growth `
  --workflow-type automation_due_run `
  --out-dir ".\promotion-output"
```

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
  -> cheat-on-content review pack and scorecard
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

When a public product page cannot be reached by local Chromium or static HTML fetch, the reader saves a web-text fallback file and routes the next workflow through `--text-file`. Use `--disable-web-text-fallback` when you do not want the public third-party reader fallback, or `--web-text-fallback-file` when Codex has already captured page text.

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

Launch unlock pack for publish and evidence gates:

```powershell
python scripts\launch_unlock_pack.py `
  --publish-queue ".\promotion-output\reports\promotion-manager\publish-queue\publish-queue.json" `
  --publish-readiness ".\promotion-output\reports\promotion-manager\publish-readiness\publish-readiness.json" `
  --out-dir ".\promotion-output"
```

Browser-assisted publish session with visible-field fill and no final publish click:

```powershell
python scripts\browser_publish_session.py `
  --publish-queue ".\promotion-output\reports\promotion-manager\publish-queue\publish-queue.json" `
  --platform-publish-url "xiaohongshu=https://creator.xiaohongshu.com/" `
  --run-form-fill `
  --out-dir ".\promotion-output"
```

Periodic automation config:

```powershell
python scripts\automation_scheduler.py init `
  --config ".\promotion-automation.json" `
  --job-id "product-weekly" `
  --browser-url "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --interval-days 7 `
  --output-root ".\promotion-output\automation" `
  --auto-search-competitors `
  --enable-multi-query-viral-discovery `
  --run-follow-up-captures `
  --capture-browser-assisted-follow-ups `
  --enable-publish-queue `
  --enable-browser-publish-assistant `
  --enable-metrics-recovery `
  --enable-next-round-optimization
```

Run due scheduled jobs or write a Windows Task Scheduler registration script:

```powershell
python scripts\automation_scheduler.py run --config ".\promotion-automation.json" --force
python scripts\automation_scheduler.py windows-task --config ".\promotion-automation.json" --out-file ".\register-enhe-promotion-task.ps1" --time "09:00"
```

Recover metrics:

```powershell
python scripts\performance_monitor.py `
  --out-dir ".\promotion-output"
```

Recover metrics manually:

```powershell
python scripts\metrics_recovery.py `
  --metrics-json ".\promotion-output\reports\promotion-manager\post-publish-capture\post-publish-metrics-export.json" `
  --business-csv ".\orders-and-revenue.csv" `
  --out-dir ".\promotion-output"
```

Set up and recover a whole real-evidence inbox:

```powershell
python scripts\real_evidence_inbox_setup.py `
  --product-url "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --inbox-dir ".\promotion-evidence-inbox" `
  --out-dir ".\promotion-output"

python scripts\real_evidence_inbox.py `
  --inbox-dir ".\promotion-evidence-inbox" `
  --skip-post-publish-capture `
  --out-dir ".\promotion-output"
```

## Documentation

- [Installation](docs/installation.md)
- [Usage](docs/usage.md)
- [中文安装教程](docs/zh-CN/installation.md)
- [中文使用说明](docs/zh-CN/usage.md)
- [Browser extension](docs/browser-extension.md)
- [Extension store submission](docs/extension-store-submission.md)
- [中文浏览器插件说明](docs/zh-CN/browser-extension.md)
- [中文插件上架指南](docs/zh-CN/extension-store-submission.md)
- [Subscription pricing](docs/subscription-pricing.md)
- [Billing backend contract](docs/billing-backend-contract.md)
- [Final capability map](docs/final-capability-map.md)

## License

MIT. See [LICENSE](LICENSE).
