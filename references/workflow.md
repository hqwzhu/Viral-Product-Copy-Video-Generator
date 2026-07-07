# Workflow Reference

Use this reference when running a full promotion cycle.

## Stage 1: Intake

Required fields:

- product name
- product URL
- target audience
- pain points
- value proposition
- pricing or pricing assumption
- language
- target platforms
- primary goal: `traffic`, `leads`, `sales`, `seo`, `brand`, or `github_stars`

If the user only provides a URL, inspect the page and derive a draft profile. Label uncertain facts as assumptions.

For a full Codex-local agent run, prefer the orchestration entrypoint:

```bash
python scripts/run_promotion_workflow.py \
  --browser-url "https://example.com/product" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --out-dir "./promotion-output"
```

This opens the page with Playwright Chromium, captures browser-visible title, metadata, headings, CTA candidates, price candidates, images, links, JSON-LD, and rendered text, then feeds that snapshot into product intake.

For environments without Chromium, static HTML intake remains available:

```bash
python scripts/run_promotion_workflow.py \
  --product-url "https://example.com/product" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --out-dir "./promotion-output"
```

To capture and inspect a rendered snapshot separately:

```bash
python scripts/browser_snapshot.py \
  --url "https://example.com/product" \
  --out-file "./rendered-product-page.json"
```

Then pass the structured snapshot into the same workflow:

```bash
python scripts/run_promotion_workflow.py \
  --structured-json "./rendered-product-page.json" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --out-dir "./promotion-output"
```

The workflow writes `reports/promotion-manager/agent-run/workflow-manifest.{json,md}` as the run ledger. Check it before telling the user what was produced, what can publish through official APIs, what remains browser-assisted, and whether real metrics are still missing.

Use the deterministic extractor when possible:

```bash
python scripts/product_intake.py --url "https://example.com/product" --out-dir "./promotion-output/intake"
```

For dynamic pages, have Codex/browser tooling inspect the rendered page first, then pass a structured snapshot or rendered text into the same extractor:

```bash
python scripts/product_intake.py \
  --structured-json "./rendered-product-page.json" \
  --out-dir "./promotion-output/intake"
```

Supported intake sources are `--url`, `--html-file`, `--text-file`, and `--structured-json`. The structured snapshot can include fields such as `url`, `title`, `description`, `pricing`, `images`, `targetAudience`, `painPoints`, and rendered `text`.
The workflow runner also supports `--browser-url`, which calls `scripts/browser_snapshot.py` first and writes `browser-snapshot/product-page-snapshot.json`.
If Chromium is missing, install the official Playwright browser runtime with `python -m playwright install chromium`.
For unattended setup on a trusted machine, add `--install-browser-if-missing` to let the workflow attempt that official install before retrying the snapshot.

## Stage 2: Research

Create a competitor and trend research note before generating final content when the user wants current market positioning.

Create platform search tasks first:

```bash
python scripts/competitor_discovery.py \
  --query "AI product copy generator" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --out-dir "./promotion-output"
```

Then capture public browser-visible search pages when direct official collection is unavailable:

```bash
python scripts/platform_search_browser.py \
  --query "AI product copy generator" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --out-dir "./promotion-output"
```

The search browser writes `search-snapshots/browser-search/<platform>.json` files plus `browser-search-snapshots.{json,md}`. It captures visible DOM only. If Chromium is missing, install it with `python -m playwright install chromium` or pass `--install-browser-if-missing` on trusted machines.

Use `--live-official` only for supported official APIs. GitHub public repository search can run without credentials. YouTube live search requires `YOUTUBE_API_KEY` in the environment; do not write the key to files or chat output.

Collect supported official/public competitor evidence:

```bash
python scripts/competitor_collector.py \
  --platform youtube \
  --query "AI product copy generator" \
  --out-dir "./promotion-output"
```

The collector supports YouTube Data API search/video/channel evidence and GitHub public repository search. YouTube requires `YOUTUBE_API_KEY`. GitHub can run against public search without a token, with optional `GITHUB_TOKEN` or `GH_TOKEN` for higher rate limits. Zhihu, Xiaohongshu, and Douyin remain browser-assisted/user-export paths unless official collection access is configured and verified.

Capture rendered search result snapshots when Codex or browser tooling can see the public search page:

```bash
python scripts/platform_search_capture.py \
  --structured-json "./search-snapshots/xiaohongshu.json" \
  --platform xiaohongshu \
  --query "AI product copy generator" \
  --out-dir "./promotion-output"
```

For a full workflow, put platform files in a directory and pass it to the runner:

```bash
python scripts/run_promotion_workflow.py \
  --product-url "https://example.com/product" \
  --search-snapshot-dir "./search-snapshots" \
  --out-dir "./promotion-output"
```

Or let the workflow create those search snapshots first:

```bash
python scripts/run_promotion_workflow.py \
  --browser-url "https://example.com/product" \
  --auto-search-competitors \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --out-dir "./promotion-output"
```

Supported snapshot file names are `<platform>.json`, `<platform>.txt`, `<platform>.html`, or `<platform>.htm`. Use this for YouTube, Zhihu, Xiaohongshu, Douyin, GitHub, TikTok, or similar platforms when official API collection is unavailable. The script must not extract cookies, hidden tokens, or private endpoints; it only processes browser-visible evidence.

Start with:

```bash
python scripts/promotion_manager.py research \
  --product-name "AI Prompt Kit" \
  --product-url "https://www.enhe-tech.com.cn/validation/ai-prompt-kit" \
  --audience "AI tool operators, creators, ecommerce sellers" \
  --value-proposition "Prompt templates for product copy, SEO content, and video scripts"
```

Minimum research output:

- platform
- competitor URL
- creator/repo/account name
- title
- content format
- hook
- structure
- CTA
- visible public metrics, only if actually observed
- why it works
- reusable pattern

Use the competitor importer when you have public URLs saved as HTML, copied transcripts, screenshots converted to text, or platform exports:

```bash
python scripts/competitor_intake.py \
  --html-file "./competitor.html" \
  --platform youtube \
  --out-dir "./promotion-output"
```

Supported inputs are `--url`, `--html-file`, `--json-file`, and `--text-file`. Use `--url` only for public pages that can be fetched as static HTML. For login-only or anti-bot-protected pages, use browser-assisted review or user-provided exports instead of bypassing controls.

Use live research for platform/API claims because publishing capabilities change.
Generated self-learning docs must be written to `docs/promotion-manager/`, not only printed in chat.

## Stage 3: Generate

Generate one platform-native content pack per target platform. Content must include a CTA and compliance note.

To create a reviewable MP4 after content generation:

```bash
python scripts/render_video.py \
  --content-json "./promotion-output/reports/promotion-manager/generated-content/ai-prompt-kit-platform-content.json" \
  --platform douyin \
  --out "./promotion-output/videos/ai-prompt-kit-douyin.mp4"
```

The rendered video is a draft artifact with silent audio and burned-in text. Do not treat it as final production creative unless the user accepts that quality level.

For a stronger video artifact, provide a recorded or AI-generated voiceover file:

```bash
python scripts/render_video.py \
  --content-json "./promotion-output/reports/promotion-manager/generated-content/ai-prompt-kit-platform-content.json" \
  --platform youtube \
  --voiceover-audio "./voiceover.wav" \
  --out "./promotion-output/videos/ai-prompt-kit-youtube.mp4"
```

On Windows, `--generate-voiceover` can synthesize a review-quality voiceover through system SAPI. Use it for iteration; use a real voiceover file for publication quality.

The workflow runner renders video artifacts by default for video platforms when `ffmpeg` is available. Use `--skip-video` only for tests or dry content-only runs.

## Stage 4: Review

Use the bundled scorecard first. If `cheat-on-content` is installed, run it as a second-pass qualitative reviewer. Do not mutate real prediction logs unless the user asks.

## Stage 5: Publish Pack

Create publish packs. Every pack requires human approval before execution. Browser-assisted publishing may fill forms, but the user must click the final publish button.

Convert a completed workflow into a publish queue before doing any real write:

```bash
python scripts/publish_queue.py \
  --workflow-manifest "./promotion-output/reports/promotion-manager/agent-run/workflow-manifest.json" \
  --github-repo owner/repo \
  --youtube-video-file "./promotion-output/videos/product-youtube.mp4" \
  --out-dir "./promotion-output"
```

The queue writes platform drafts, calls GitHub/YouTube official executors in dry-run mode when enough target information exists, and keeps Zhihu, Xiaohongshu, Douyin, and similar platforms as manual/browser-assisted queue items.
It also writes `reports/promotion-manager/published-items/published-items.{json,md}`. Official dry-runs, queued manual tasks, blocked writes, and browser-assisted tasks remain pending until a real published URL exists.

Run official publishing actions through a dry run first:

```bash
python scripts/publish_executor.py \
  --platform github \
  --github-action file \
  --github-repo owner/repo \
  --path PROMOTION.md \
  --content-file "./promotion-output/reports/promotion-manager/generated-content/product-platform-content.md" \
  --out-dir "./promotion-output"
```

To execute a supported official write, the user must provide the relevant environment credential and explicit approval:

```bash
python scripts/publish_executor.py ... --execute --approval I_APPROVE_PUBLISH
```

Supported official write paths are GitHub file writes, GitHub issues, GitHub releases, and YouTube `videos.insert` upload. GitHub requires `GITHUB_TOKEN` or `GH_TOKEN`. YouTube requires `YOUTUBE_OAUTH_ACCESS_TOKEN`, not a plain API key. Zhihu, Xiaohongshu, and Douyin remain manual/browser-assisted unless official app permissions are configured and verified.

For a YouTube upload when no access token exists yet, use the OAuth helper:

```bash
python scripts/youtube_oauth_publish.py \
  --video-file "./promotion-output/videos/product-youtube.mp4" \
  --title "Product launch draft" \
  --out-dir "./promotion-output"
```

Dry-run writes the Google authorization URL. Execution requires `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, and `--execute --approval I_APPROVE_PUBLISH`. The helper exchanges the authorization code for an access token and uploads in the same process without saving the token.

After manual or browser-assisted publishing, register the real URL before metrics recovery:

```bash
python scripts/published_items.py \
  --platform xiaohongshu \
  --published-url "https://www.xiaohongshu.com/explore/real-note-id" \
  --title "Published launch note" \
  --evidence "./screenshots/xhs-published.png" \
  --out-dir "./promotion-output"
```

## Stage 6: Retrospective

Generate a retrospective only from real data and evidence. If data is missing, return `waiting_real_data`.

Import real metrics first:

```bash
python scripts/metrics_intake.py \
  --csv-file "./metrics-export.csv" \
  --out-dir "./promotion-output"
```

Supported sources are `--csv-file`, `--json-file`, `--text-file`, `--published-url`, `--github-repo`, and `--youtube-video-id`. GitHub public repository metrics use the official REST API. YouTube video statistics require `YOUTUBE_API_KEY` in the environment and the key must not be written to files or chat output. Orders and revenue must come from user-provided business exports or analytics evidence.

The workflow runner can call metrics intake in the same run with `--metrics-csv`, `--metrics-json`, `--metrics-text`, `--published-url`, `--github-repo`, or `--youtube-video-id`. If no real evidence is supplied, its manifest must report `waiting_real_data`.

For a full post-publish recovery pass, use the metrics recovery coordinator after a workflow or publish queue exists:

```bash
python scripts/metrics_recovery.py \
  --workflow-manifest "./promotion-output/reports/promotion-manager/agent-run/workflow-manifest.json" \
  --publish-queue "./promotion-output/reports/promotion-manager/publish-queue/publish-queue.json" \
  --business-csv "./orders-and-revenue.csv" \
  --out-dir "./promotion-output"
```

The coordinator reads proven published URLs from the default `published-items` report, direct `--published-url` inputs, `--github-repo`, `--youtube-video-id`, and optional `--published-items-json` files. It automatically attempts only safe official/public connectors for GitHub and YouTube. It merges those records with CSV, JSON, or text exports that contain clicks, leads, orders, revenue, or platform metrics. Zhihu, Xiaohongshu, Douyin, TikTok, and unpublished queue items must be reported as `manual_export_required` or `publish_pending` until real platform exports, screenshots, or official access are provided.

## Stage 7: Periodic Automation

Create a local automation config:

```bash
python scripts/automation_scheduler.py init \
  --config "./promotion-automation.json" \
  --job-id "product-weekly" \
  --browser-url "https://example.com/product" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --interval-days 7
```

Run due jobs:

```bash
python scripts/automation_scheduler.py run --config "./promotion-automation.json"
```

Generate a Windows Task Scheduler registration script:

```bash
python scripts/automation_scheduler.py windows-task \
  --config "./promotion-automation.json" \
  --out-file "./register-promotion-task.ps1" \
  --task-name "ENHE Promotion Manager" \
  --time "09:00"
```

The scheduler writes `promotion-automation-state.json` next to the config unless `--state-file` is provided. It also writes `automation-run.{json,md}` under the configured output root. Treat that report as the scheduler ledger.

Scheduled runs can generate new content, videos, publish packs, and metrics import reports. They still must not perform final publishing unless an official executor path has credentials and explicit approval. Browser-assisted and manual platforms remain queued for user-visible action.

To enable queue generation after a scheduled workflow, set `jobs[].publish.enabled` to `true`. The scheduler then runs `scripts/publish_queue.py` and records `lastPublishQueue` in the state file. Keep `jobs[].publish.execute` false unless the environment has official credentials and the user has explicitly approved `I_APPROVE_PUBLISH`.
Scheduled jobs can set `installBrowserIfMissing: true` when browser-runtime installation is acceptable for that machine.
Scheduled jobs can set `autoSearchCompetitors: true` to run browser-visible competitor search before content generation reports are finalized.
Scheduled jobs can set `metricsRecovery.enabled: true` to run `scripts/metrics_recovery.py` after the workflow and optional publish queue. Use `metricsRecovery.businessCsv`, `businessJson`, `businessText`, `publishedItemsJson`, `publishedUrls`, `githubRepos`, or `youtubeVideoIds` to pass evidence for automatic recovery.

## Phase 2 And Phase 3 Boundaries

The script may generate roadmap documents for a browser extension and SaaS product, but do not implement either until the user explicitly approves that phase.
