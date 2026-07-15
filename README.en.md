# ENHE Product Promo Maker

[![ZH](https://img.shields.io/badge/README-ZH-blue)](README.md)
[![English](https://img.shields.io/badge/README-English-gray)](README.en.md)

ENHE Product Promo Maker is a local Codex Skill that turns any product URL, website URL, app page, or GitHub repository into a repeatable product promotion system. Turn product pages into promotional copy, video scripts, and publishing assets.

It is built for founders, indie hackers, AI tool operators, and marketing teams who want Codex to act like a practical website and product promotion manager:

```text
product URL
  -> product intake
  -> viral competitor research
  -> platform-native copy and scripts
  -> video, cover, and detail-image assets
  -> safe publish packages
  -> real evidence recovery
  -> next-round optimization
```

Repository: [hqwzhu/Viral-Product-Copy-Video-Generator](https://github.com/hqwzhu/Viral-Product-Copy-Video-Generator.git)

Chinese version: [README.md](README.md)

Open-source integration notes: [Firecrawl + AiToEarn Integration](docs/open-source-integration.md)

100% completion roadmap: [Module-by-module roadmap](docs/100-percent-completion-roadmap.md) / [Chinese beginner guide](docs/zh-CN/100-percent-completion-guide.md)

## What This Project Does

Give the Skill a product link or website link. It can then:

- Read one or many product URLs and convert them into structured product profiles.
- Search public or browser-visible platform evidence for viral creators, posts, videos, and repositories across YouTube, Zhihu, Xiaohongshu, Douyin, GitHub, TikTok, and similar platforms.
- Deconstruct viral hooks, content structure, creator patterns, visible metrics, and video/storyboard patterns.
- Generate platform-native viral titles, copy, tags, first-batch comments/replies, voiceover scripts, storyboards, MP4 draft videos, covers, and detail images.
- Build guarded publish packages for manual/browser-assisted publishing and dry-run official API publishing where supported.
- Register real published URLs, import real metrics/comments/orders/revenue evidence, and create next-round optimization recommendations.

## What You Get After Running It

A normal run writes a local `promotion-output` folder with manager-ready assets:

- Product profile and factual intake report.
- Competitor search tasks, viral material library, creator leaderboard, and follow-up capture requests.
- Multi-platform content drafts for YouTube, Zhihu, Xiaohongshu, Douyin, GitHub, and similar channels.
- Complete publish packages containing viral title, final copy, tags, first-batch engagement prompts, video status/path, cover image, detail images, tracking URLs, warnings, and manual steps.
- Optional MP4 draft videos generated with `ffmpeg`.
- Optional PNG cover/detail images generated with `Pillow`.
- Browser/manual publish payloads and checklists.
- Evidence inbox templates for published URLs, metrics, comments, orders, and revenue.
- Retrospective and next-round optimization reports once real performance evidence exists.

## What It Does Not Do

The project intentionally keeps publishing safe:

- It does not bypass login, captcha, platform risk control, app review, or account authorization.
- It does not scrape private APIs, save cookies, or extract hidden tokens.
- It does not click the final publish button in browser-assisted publishing.
- It does not fabricate platform metrics, comments, orders, revenue, or published URLs.
- Official publishing remains dry-run-first and requires platform credentials plus explicit approval.

## Current Capability

The repository implements the local Codex Skill workflow and safety gates. It does not bypass platform login, captcha, risk controls, app review, or account authorization.

| Area | Status | Notes |
| --- | --- | --- |
| Product URL reading | Ready | Browser snapshots, structured JSON intake, static fallback, public web-text fallback, URL discovery, and batch runner are included. |
| Viral research | Ready with access limits | YouTube and GitHub can use public or official paths. Zhihu, Xiaohongshu, Douyin, and TikTok use browser-visible evidence, official access, user exports, or the optional Firecrawl-style web data backend. |
| Optional web data backend | Ready | `scripts/web_data_provider.py` supports Firecrawl-style Search, Scrape, Map, Crawl, and Batch Scrape through environment variables, and is integrated into product URL reading, site URL discovery, and platform search capture. |
| Platform capability registry | Ready | `scripts/platform_capabilities.py` documents platform Create/Publish/Engage/Monetize/Search capability boundaries inspired by AiToEarn while rejecting cookie/simulated-login automation. |
| Copy and media generation | Ready | Platform-native copy, first-batch engagement prompts, ffmpeg MP4 rendering, PNG cover images, and detail images are included. Voiceover can use an audio file or Windows review-quality TTS. |
| Publishing | Partial | GitHub and YouTube keep official API dry-run-first publish ports. Douyin, Zhihu, Xiaohongshu, and TikTok default to manual or browser-assisted flows unless verified official creator publishing access is available. `launch_unlock_pack.py` builds one setup pack for platform gates, credentials, browser-assisted publish payloads, and real-evidence templates. `browser_publish_session.py` combines payload preparation, visible-field fill, screenshots, final manual publish checklist, and post-publish URL recovery commands. |
| Metrics and revenue | Waiting for real evidence | The Skill can initialize a fillable evidence inbox, run a post-publish performance monitor, import evidence files, recover real data, and optimize the next round, but it cannot invent published URLs, platform metrics, orders, or revenue. |
| Self-evolution | Controlled | The Skill can audit tools, docs, repo state, and installed Skill drift. It only syncs or installs allowlisted runtimes with explicit commands. |
| Browser extension | Store package and deployable backend included | `browser-extension/` captures the current tab, builds Codex commands or hosted run payloads, estimates subscription cost, and links to ENHE. `scripts/package_browser_extension.py` validates MV3 and remote-code guardrails. `backend/license-service/` now provides Stripe Checkout, signed webhooks, license validation, PostgreSQL-backed quota state, usage reservation/commit, hosted-run queue/status endpoints, and an isolated hosted worker. `deploy/promotion-manager/`, `docs/store/`, and `docs/legal/` prepare deployment, review copy, privacy, terms, refund, and support materials. External account setup, live Stripe configuration, server deployment, and store approval remain operator gates. |

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

Optional PNG cover/detail image runtime:

```powershell
python -m pip install pillow
```

Optional official YouTube Data API publishing client:

```powershell
python -m pip install -r requirements-youtube.txt
```

This installs `google-api-python-client` plus the Google OAuth/auth helper packages used by `scripts\publish_executor.py --platform youtube` and `scripts\youtube_oauth_publish.py`.

Check whether YouTube credentials are visible to the project without uploading or printing secret values:

```powershell
python scripts\youtube_credential_check.py --env-file "C:\path\to\.env" --out-dir ".\promotion-output"
```

The YouTube OAuth helpers accept `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET` and the template aliases `YOUTUBE_CLIENT_ID` / `YOUTUBE_CLIENT_SECRET`.

Run tests:

```powershell
python scripts\test_promotion_manager.py
python -m compileall -q scripts
```

More detail: [docs/installation.md](docs/installation.md)
Chinese installation guide: [docs/zh-CN/installation.md](docs/zh-CN/installation.md)

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
python scripts\completion_roadmap.py --out-dir ".\promotion-output"
python scripts\operator_action_checklist.py --out-dir ".\promotion-output"
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

If no real data exists yet and you only want to validate the recovery loop, generate a clearly marked synthetic/demo inbox:

```powershell
python scripts\synthetic_evidence_generator.py `
  --product-url "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --run-recovery `
  --out-dir ".\promotion-output\synthetic-validation"
```

Synthetic reports carry `SYNTHETIC_DEMO_DATA_DO_NOT_REPORT`. They are only for local pipeline validation and must not be reported as real platform, order, or revenue performance.

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

The extension includes a pricing calculator, checkout entry, billing portal entry, license validation, usage credit reservation, hosted-run payload handoff, a machine-readable backend contract, a local reference simulator for license, usage, hosted-run, and webhook flows, and a production reference License service under `backend/license-service/`. Chrome Web Store Payments is deprecated, so use the ENHE backend payment provider and License API rather than the old Web Store billing API for a new paid extension.

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

Run the production reference License service locally:

```powershell
cd backend\license-service
npm install
copy .env.example .env
npm run start
```

Before public launch, deploy it behind HTTPS, configure Stripe live prices and signed webhooks, set `DATABASE_URL`, run `npm run migrate`, start the API and worker services from `deploy/promotion-manager/`, publish privacy/terms/refund/support pages, and pass Chrome/Edge store review.

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

Viral evidence inbox fallback for risk-controlled platforms:

```powershell
python scripts\viral_evidence_inbox_setup.py `
  --product-url "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --inbox-dir ".\viral-evidence-inbox" `
  --out-dir ".\promotion-output"
```

After adding real competitor URLs, visible page text, transcripts, exports, or screenshot OCR text:

```powershell
python scripts\viral_evidence_inbox.py `
  --inbox-dir ".\viral-evidence-inbox" `
  --out-dir ".\promotion-output"
```

This inbox is for real competitor evidence only. It does not seed fake creators or metrics; screenshots are recorded as needing OCR/copied text before import.

Render MP4:

```powershell
python scripts\render_video.py `
  --content-json ".\promotion-output\reports\promotion-manager\generated-content\product-platform-content.json" `
  --platform douyin `
  --out ".\promotion-output\videos\product-douyin.mp4"
```

Generate the complete publish media asset pack and write it back into the publish package:

```powershell
python scripts\media_asset_pack.py `
  --content-json ".\promotion-output\reports\promotion-manager\generated-content\product-platform-content.json" `
  --publish-pack ".\promotion-output\reports\promotion-manager\publish-packs\product-publish-pack.json" `
  --video-file "douyin=.\promotion-output\videos\product-douyin.mp4" `
  --out-dir ".\promotion-output"
```

After this step each publish package item includes viral title, copy, tags, first-batch comments/replies, video path/status, cover image, detail images, and an `assets` list for manual/browser-assisted publishing.

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

Validate the recovery loop with synthetic/demo evidence only:

```powershell
python scripts\synthetic_evidence_generator.py `
  --product-url "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --run-recovery `
  --out-dir ".\promotion-output\synthetic-validation"
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
- [Chinese installation guide](docs/zh-CN/installation.md)
- [Chinese usage guide](docs/zh-CN/usage.md)
- [Browser extension](docs/browser-extension.md)
- [Extension store submission](docs/extension-store-submission.md)
- [Chinese browser extension guide](docs/zh-CN/browser-extension.md)
- [Chinese extension submission guide](docs/zh-CN/extension-store-submission.md)
- [Subscription pricing](docs/subscription-pricing.md)
- [Billing backend contract](docs/billing-backend-contract.md)
- [Final capability map](docs/final-capability-map.md)
- [100% completion roadmap](docs/100-percent-completion-roadmap.md)
- [Chinese 100% completion guide](docs/zh-CN/100-percent-completion-guide.md)

## License

MIT. See [LICENSE](LICENSE).
