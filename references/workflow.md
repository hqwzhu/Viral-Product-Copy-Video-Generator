# Workflow Reference

Use this reference when running a full promotion cycle.

Before claiming the Skill has final Agent readiness, run the capability audit:

```bash
python scripts/final_capability_audit.py --out-dir "./promotion-output"
```

The audit writes `reports/promotion-manager/capability/final-capability-audit.{json,md}` and checks the exact requested end-state: product URL parsing, viral creator/content search, copy/video generation, publishing, metrics/orders/revenue recovery, periodic Codex operation, and self-evolution. It also runs `scripts/self_evolution_audit.py` and records the self-evolution report path. It records credential presence only by environment variable name and must not write secret values.

Run the self-evolution audit directly when the Skill needs to inspect local tool gaps, repository state, installed Skill drift, and safe upgrade actions:

```bash
python scripts/self_evolution_audit.py --out-dir "./promotion-output"
```

If the machine is trusted and browser runtime installation is explicitly acceptable, the audit can install only the allowlisted Chromium runtime:

```bash
python scripts/final_capability_audit.py \
  --install-safe-missing-tools \
  --safe-install playwright_chromium \
  --out-dir "./promotion-output"
```

After a reviewed local Skill change passes tests and secret scanning, sync it into the installed Codex Skill directory only with the explicit sync approval phrase:

```bash
python scripts/self_evolution_audit.py \
  --sync-installed-skill \
  --approval I_APPROVE_SKILL_SYNC \
  --out-dir "./promotion-output"
```

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

To run Codex-first product URL reading as a standalone intake pass:

```bash
python scripts/product_url_reader.py \
  --url "https://example.com/product" \
  --out-dir "./promotion-output"
```

This writes `reports/promotion-manager/intake/product-url-reader.{json,md}`, a per-URL structured page snapshot, and a per-URL product profile. When browser rendering succeeds, each record includes a `nextWorkflowCommand` that uses `--structured-json`; if only static fallback succeeds, it uses `--product-url` and marks the record as `partial_ready`.

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

For a direct keyword-to-viral-library pass, run the standalone viral discovery runner:

```bash
python scripts/viral_discovery_runner.py \
  --query "AI product copy generator" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --top-n 20 \
  --out-dir "./promotion-output"
```

This writes `reports/promotion-manager/competitors/viral-discovery-run.{json,md}` and chains platform search snapshots, normalized captures, `viral-content-library`, `creator-leaderboard`, and follow-up task generation. Use `--live-official` to also run supported YouTube/GitHub official/public collectors where credentials allow. Use `--html-snapshot-dir` when Codex or the user has saved browser-visible platform search pages.

Use `--live-official` only for supported official APIs. GitHub public repository search can run without credentials. YouTube live search requires `YOUTUBE_API_KEY` in the environment; do not write the key to files or chat output.

When the product category is broad or one keyword is likely too narrow, run product-driven multi-query discovery from the workflow manifest:

```bash
python scripts/multi_query_viral_discovery.py \
  --workflow-manifest "./promotion-output/reports/promotion-manager/agent-run/workflow-manifest.json" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --top-n 20 \
  --out-dir "./promotion-output"
```

This writes `multi-query-viral-discovery.{json,md}`, `multi-query-viral-content-library.{json,md}`, and `multi-query-creator-leaderboard.{json,md}`. It derives queries from product name, value proposition, keywords, pain points, audience, and optional `--query` values. Use `--dry-run` to inspect planned platform searches before opening public search pages.

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

After search capture, build the cross-platform viral material library:

```bash
python scripts/viral_content_library.py \
  --search-capture-dir "./promotion-output/reports/promotion-manager/competitors" \
  --top-n 20 \
  --out-dir "./promotion-output"
```

This writes `viral-content-library.{json,md}` and `follow-up-capture-tasks.{json,md}`. The library ranks captured records by observed viral score and preserves title, creator, hook, CTA, visible metrics, reusable patterns, and source report paths. The follow-up queue marks YouTube/GitHub public URLs as capture candidates and keeps Zhihu, Xiaohongshu, Douyin, TikTok, and unknown platforms as browser-assisted/manual evidence tasks unless official access is verified.

Build a creator/account leaderboard from the ranked viral library:

```bash
python scripts/creator_leaderboard.py \
  --viral-library "./promotion-output/reports/promotion-manager/competitors/viral-content-library.json" \
  --top-n 20 \
  --out-dir "./promotion-output"
```

This writes `creator-leaderboard.{json,md}` and `creator-follow-up-tasks.{json,md}`. Use it to identify high-signal creators, group repeated viral materials by account, and queue safe public/browser-assisted creator tracking. It must not infer hidden follower counts, private analytics, orders, or revenue.

Run safe creator/account follow-up research when you want account-level evidence:

```bash
python scripts/creator_follow_up_runner.py \
  --tasks-json "./promotion-output/reports/promotion-manager/competitors/creator-follow-up-tasks.json" \
  --dry-run \
  --out-dir "./promotion-output"
```

This writes `creator-follow-up-results.{json,md}` and `creator-deep-library.{json,md}`. YouTube and GitHub creator tasks can use supported official/public connectors; Zhihu, Xiaohongshu, Douyin, TikTok, and unknown platforms stay browser-assisted or user-export evidence tasks unless verified official access exists.

Execute safe public follow-up capture tasks when you want deeper competitor evidence:

```bash
python scripts/follow_up_capture_runner.py \
  --tasks-json "./promotion-output/reports/promotion-manager/competitors/follow-up-capture-tasks.json" \
  --capture-browser-assisted \
  --out-dir "./promotion-output"
```

By default the runner fetches only `public_url_capture_candidate` tasks. With `--capture-browser-assisted`, it also attempts public Playwright snapshots for queued browser-assisted tasks, writes `follow-up-captures/<task>/browser-visible-snapshot.json`, imports visible page evidence into `deep-competitor-library.json`, and falls back to evidence request files when login, captcha, verification, draft, preview, or access-denied content is detected.

Use the competitor-informed enhancer when ranked search materials or deep competitor records should shape the final drafts:

```bash
python scripts/competitor_content_enhancer.py \
  --content-json "./promotion-output/reports/promotion-manager/generated-content/product-platform-content.json" \
  --viral-library "./promotion-output/reports/promotion-manager/competitors/viral-content-library.json" \
  --deep-library "./promotion-output/reports/promotion-manager/competitors/deep-competitor-library.json" \
  --write-back \
  --out-dir "./promotion-output"
```

The full workflow runs this step automatically after viral/deep libraries are available and before video rendering. It writes `<product>-competitor-informed-content.{json,md}`, `<product>-competitor-informed-strategy.json`, backs up the base content as `<product>-platform-content.base.json`, and updates the publish pack when present. Use `--skip-competitor-informed-content` only when you need untouched baseline drafts.

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
  --run-follow-up-captures \
  --capture-browser-assisted-follow-ups \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --out-dir "./promotion-output"
```

Supported snapshot file names are `<platform>.json`, `<platform>.txt`, `<platform>.html`, or `<platform>.htm`. Use this for YouTube, Zhihu, Xiaohongshu, Douyin, GitHub, TikTok, or similar platforms when official API collection is unavailable. The script must not extract cookies, hidden tokens, or private endpoints; it only processes browser-visible evidence.
The workflow runner builds the viral material library automatically after at least one search capture succeeds. Use `--skip-viral-library` only when you want raw capture reports without cross-platform ranking.
The workflow runner builds the creator leaderboard automatically after the viral material library succeeds. Use `--skip-creator-leaderboard` only when you want to skip account-level aggregation.
The workflow runner runs creator/account follow-up only when `--run-creator-follow-up` is supplied. Use `--creator-follow-up-dry-run` to plan the stage without fetching public APIs.
The workflow runner executes follow-up captures only when `--run-follow-up-captures` is supplied. Use `--capture-browser-assisted-follow-ups` to attempt safe browser-visible snapshots for queued Zhihu, Xiaohongshu, Douyin, TikTok, or similar follow-up tasks; use `--follow-up-dry-run` to plan the stage without fetching public URLs.
The workflow runner rewrites generated content with available viral/deep competitor libraries before rendering videos and building final publish queues. Use `--skip-competitor-informed-content` to disable that rewrite.

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
When a viral material library exists, use competitor-informed content as the default final draft source. The enhancer may adapt titles, descriptions, video scripts, voiceover, storyboard, and platform-specific formats, but it must keep competitor metrics as evidence metadata only and must not copy competitor wording into product claims.

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

Before execution, audit publish readiness:

```bash
python scripts/publish_readiness_runner.py \
  --workflow-manifest "./promotion-output/reports/promotion-manager/agent-run/workflow-manifest.json" \
  --build-queue \
  --github-repo owner/repo \
  --youtube-video-file "./promotion-output/videos/product-youtube.mp4" \
  --out-dir "./promotion-output"
```

This writes `reports/promotion-manager/publish-readiness/publish-readiness.{json,md}`. The report checks queue state, target information, credential presence by environment variable name, approval status, and next actions. It does not write credential values and does not execute final platform writes unless the publish queue is explicitly run with execution and the required approval phrase.

Prepare browser-assisted publishing materials for non-official direct-publish platforms:

```bash
python scripts/browser_publish_assistant.py \
  --publish-queue "./promotion-output/reports/promotion-manager/publish-queue/publish-queue.json" \
  --out-dir "./promotion-output"
```

This writes `reports/promotion-manager/browser-publish/browser-publish-assistant.{json,md}` plus per-platform payload JSON, clipboard text, form-fill helper scripts, and checklists. It can open user-visible publisher entry URLs with `--open-browser`, but the user must complete login, account checks, media review, and the final publish action. Override moved creator pages with `--platform-publish-url platform=url`.

After the user publishes manually or in a user-visible browser session, register the real published URL:

```bash
python scripts/browser_publish_assistant.py \
  --publish-queue "./promotion-output/reports/promotion-manager/publish-queue/publish-queue.json" \
  --published-url "xiaohongshu=https://www.xiaohongshu.com/explore/real-note-id" \
  --evidence "./screenshots/xhs-published.png" \
  --out-dir "./promotion-output"
```

The assistant calls `scripts/published_items.py` for supplied real URLs, so metrics recovery can start from the standard `published-items` report.

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

Before claiming a platform can be fully automated, generate the official access boundary report:

```bash
python scripts/platform_access_audit.py --out-dir "./promotion-output"
```

This writes `reports/promotion-manager/platform-access/platform-access-audit.{json,md}`. The report maps each platform to implemented official API paths, official app-review candidates, manual/browser-assisted fallbacks, required environment variable names, and metrics recovery evidence rules. It records only environment variable names, never credential values.

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

If Codex or the user has a browser-visible post-publish page snapshot, saved HTML, or copied page text, capture and register it directly:

```bash
python scripts/publish_url_capture.py \
  --structured-json "./published-page-snapshot.json" \
  --out-dir "./promotion-output"
```

The capture script extracts the real platform URL, title, content id, and evidence, then updates `reports/promotion-manager/published-items/published-items.{json,md}`. It must block draft, editor, preview, localhost, and unknown-platform URLs instead of registering them as published content.

After real published URLs are registered, capture public/browser-visible metrics before recovery:

```bash
python scripts/post_publish_metrics_capture.py \
  --out-dir "./promotion-output"
```

This writes `reports/promotion-manager/post-publish-capture/post-publish-metrics-capture.{json,md}`, a structured snapshot, and `post-publish-metrics-export.json`. It captures visible public metrics only. If the page requires login, captcha, account verification, private analytics, or a business system, it writes a manual evidence request instead of bypassing the platform.

After real published URLs or visible comment exports exist, capture public/browser-visible comment evidence and demand signals:

```bash
python scripts/comment_evidence_capture.py \
  --out-dir "./promotion-output"
```

This writes `reports/promotion-manager/comment-evidence/comment-evidence-capture.{json,md}` and `comment-evidence-export.json`. It captures visible comments, visible likes/replies per comment, and recurring demand signals such as questions, pricing concerns, integrations, feature requests, pain points, objections, and CTA intent. If comments are behind login, captcha, risk checks, or private analytics, it writes a manual evidence request instead of bypassing the platform.

When the business export contains UTM/source/referrer/order rows instead of direct published URLs, attribute it before recovery:

```bash
python scripts/business_attribution.py \
  --business-csv "./orders-and-revenue.csv" \
  --out-dir "./promotion-output"
```

This writes `reports/promotion-manager/business-attribution/business-attribution.{json,md}` and `business-attribution-export.json`. It matches rows to proven published items by exact URL, referrer URL, landing page URL, UTM content/content ID, or title/campaign evidence. Platform-only rows remain unmatched so orders and revenue are not overclaimed.

Run one full local operating cycle when you want workflow generation, guarded publishing, published URL registration, and metrics recovery in one command:

```bash
python scripts/promotion_cycle_runner.py \
  --browser-url "https://example.com/product" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --github-repo owner/repo \
  --business-csv "./orders-and-revenue.csv" \
  --out-dir "./promotion-output"
```

This writes `reports/promotion-manager/cycle/promotion-cycle.{json,md}`. The cycle runner calls the existing workflow, publish queue, published-items registrar, and metrics recovery scripts. It can pass official GitHub/YouTube execution through `--execute-publish --approval I_APPROVE_PUBLISH`, but queued manual/browser-assisted tasks remain pending until a real published URL or export is registered.

## Stage 6: Retrospective

Generate a retrospective only from real data and evidence. If data is missing, return `waiting_real_data`.

Import real metrics first:

```bash
python scripts/metrics_intake.py \
  --csv-file "./metrics-export.csv" \
  --out-dir "./promotion-output"
```

For a browser-visible published page or analytics page that Codex has already read into structured JSON:

```bash
python scripts/metrics_intake.py \
  --structured-json "./published-metrics-snapshot.json" \
  --out-dir "./promotion-output"
```

Supported sources are `--csv-file`, `--json-file`, `--text-file`, `--structured-json`, `--published-url`, `--github-repo`, and `--youtube-video-id`. GitHub public repository metrics use the official REST API. YouTube video statistics require `YOUTUBE_API_KEY` in the environment and the key must not be written to files or chat output. Orders and revenue must come from user-provided business exports or analytics evidence.

The workflow runner can call metrics intake in the same run with `--metrics-csv`, `--metrics-json`, `--metrics-text`, `--published-url`, `--github-repo`, or `--youtube-video-id`. If no real evidence is supplied, its manifest must report `waiting_real_data`.

For a full post-publish recovery pass, use the metrics recovery coordinator after a workflow or publish queue exists:

```bash
python scripts/metrics_recovery.py \
  --workflow-manifest "./promotion-output/reports/promotion-manager/agent-run/workflow-manifest.json" \
  --publish-queue "./promotion-output/reports/promotion-manager/publish-queue/publish-queue.json" \
  --business-csv "./orders-and-revenue.csv" \
  --out-dir "./promotion-output"
```

The coordinator reads proven published URLs from the default `published-items` report, direct `--published-url` inputs, `--github-repo`, `--youtube-video-id`, and optional `--published-items-json` files. It automatically attempts only safe official/public connectors for GitHub and YouTube. It merges those records with CSV, JSON, text, or structured browser snapshots that contain clicks, leads, orders, revenue, or platform metrics:

```bash
python scripts/metrics_recovery.py \
  --metrics-structured-json "./published-metrics-snapshot.json" \
  --out-dir "./promotion-output"
```

When `scripts/business_attribution.py` has produced a matched order/revenue export, merge that attribution output:

```bash
python scripts/metrics_recovery.py \
  --business-json "./promotion-output/reports/promotion-manager/business-attribution/business-attribution-export.json" \
  --out-dir "./promotion-output"
```

When `scripts/post_publish_metrics_capture.py` has already captured public page metrics, merge its export:

```bash
python scripts/metrics_recovery.py \
  --metrics-json "./promotion-output/reports/promotion-manager/post-publish-capture/post-publish-metrics-export.json" \
  --out-dir "./promotion-output"
```

When `scripts/comment_evidence_capture.py` has captured public comments, use `comment-evidence-export.json` as qualitative evidence for the next content round. Do not convert comment counts, likes, replies, objections, or purchase intent into performance claims unless the report includes visible evidence for them.

Zhihu, Xiaohongshu, Douyin, TikTok, and unpublished queue items must be reported as `manual_export_required` or `publish_pending` until real platform exports, screenshots, browser-visible structured snapshots, or official access are provided.

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
Set `jobs[].browserPublishAssistant.enabled` to `true` to run `scripts/browser_publish_assistant.py` after publish queue generation. This prepares browser/manual payloads for queued platforms and records `lastBrowserPublishAssistant` in state. Use `browserPublishAssistant.platformPublishUrls`, `publishedUrls`, and `evidence` to override creator entry URLs or register real URLs after user-visible publishing.
Set `jobs[].postPublishMetricsCapture.enabled` to `true` to run `scripts/post_publish_metrics_capture.py` after published URL registration and before metrics recovery. Use `publishedItemsJson`, `publishedUrls`, `captureBrowserAssisted`, and `allowLocalhost` for explicit evidence sources and tests. Captured metrics are passed to metrics recovery as a JSON metrics source when `metricsRecovery.enabled` is also true.
Set `jobs[].commentEvidenceCapture.enabled` to `true` to run `scripts/comment_evidence_capture.py` after the workflow. Use `publishedItemsJson`, `publishedUrls`, `structuredJson`, `htmlFile`, `textFile`, `captureBrowserAssisted`, and `allowLocalhost` for explicit public/browser-visible comment evidence sources. The scheduler records `lastCommentEvidenceCapture` in state.
Set `jobs[].businessAttribution.enabled` to `true` to run `scripts/business_attribution.py` before metrics recovery. Use `businessCsv`, `businessJson`, `publishedItemsJson`, and `publishedUrls` to pass order/revenue exports and content evidence. The scheduler records `lastBusinessAttribution` in state and passes the attribution export to metrics recovery when `metricsRecovery.enabled` is true.
Scheduled jobs can set `installBrowserIfMissing: true` when browser-runtime installation is acceptable for that machine.
Scheduled jobs can set `autoSearchCompetitors: true` to run browser-visible competitor search before content generation reports are finalized.
Scheduled jobs can set `multiQueryViralDiscovery.enabled: true` to run product-driven multi-query viral discovery after the workflow manifest is created. Useful fields include `dryRun`, `queryCount`, `queries`, `platforms`, `topN`, `htmlSnapshotRoot`, `liveOfficial`, `runCreatorFollowUp`, `runFollowUpCaptures`, and `captureBrowserAssistedFollowUps`.
Scheduled jobs can set `followUpCapture.enabled: true` to run safe public follow-up captures after the viral material library is built. Use `followUpCapture.dryRun: true` for planning-only runs.
Scheduled jobs can set `followUpCapture.captureBrowserAssisted: true` to attempt public browser-visible snapshots for queued browser-assisted platform follow-up tasks.
Scheduled jobs can set `skipCreatorLeaderboard: true` to skip creator/account aggregation after viral material ranking.
Scheduled jobs can set `creatorFollowUp.enabled: true` to run safe creator/account follow-up after the creator leaderboard is built. Use `creatorFollowUp.dryRun: true` for planning-only runs.
Scheduled jobs can set `competitorInformedContent.enabled: true` to pass the explicit workflow flag or `false` to add `--skip-competitor-informed-content`.
Scheduled jobs can set `metricsRecovery.enabled: true` to run `scripts/metrics_recovery.py` after the workflow and optional publish queue. Use `metricsRecovery.businessCsv`, `businessJson`, `businessText`, `publishedItemsJson`, `publishedUrls`, `githubRepos`, or `youtubeVideoIds` to pass evidence for automatic recovery.

## Phase 2 And Phase 3 Boundaries

The script may generate roadmap documents for a browser extension and SaaS product, but do not implement either until the user explicitly approves that phase.
