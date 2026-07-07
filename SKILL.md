---
name: viral-product-copy-video-generator
description: Generate product promotion research, viral copy, video scripts, safe publish packs, and retrospective templates for YouTube, Zhihu, Xiaohongshu, Douyin, GitHub, and similar channels. Use when the user provides a product URL, website URL, app/tool page, GitHub repo, or asks to promote a product with multi-platform copy/video content, competitor deconstruction, publish planning, or content performance review.
---

# Viral Product Copy Video Generator

## Core Rule

Act as a product promotion manager, not a generic copywriter. Convert a product URL or product brief into a repeatable promotion loop:

`research -> deconstruct -> generate copy/scripts -> review -> publish pack -> real-data retrospective -> next round`

Never auto-publish, auto-login, save cookies/tokens/passwords, bypass captcha, or fabricate platform metrics.

## Quick Start

When the user sends a product link, do this:

1. Inspect the product page or ask for missing basics: product name, target audience, pain points, value proposition, price, target platforms, and primary goal.
2. Research platform constraints and competitors when the request depends on current information. Prefer official docs for API/publishing claims.
3. Use `scripts/run_promotion_workflow.py` for the default end-to-end local workflow: intake, competitor discovery, content generation, video rendering, publish automation map, and metrics recovery status.
4. Review the generated content. If `cheat-on-content` is installed, use it for a second-pass content review; otherwise use the generated scorecard. Read [references/cheat-on-content-integration.md](references/cheat-on-content-integration.md) before writing prediction logs.
5. Give the user publish packs and ask for approval before any publishing action.

Default one-command workflow:

```bash
python scripts/run_promotion_workflow.py \
  --product-url "https://example.com/product" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --out-dir "./promotion-output"
```

For dynamic pages, Codex should inspect the rendered page first and pass a structured snapshot:

```bash
python scripts/run_promotion_workflow.py \
  --structured-json "./rendered-product-page.json" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --out-dir "./promotion-output"
```

Example:

```bash
python scripts/promotion_manager.py all \
  --product-name "AI Prompt Kit" \
  --product-url "https://example.com/product" \
  --audience "AI tool operators, creators, ecommerce sellers" \
  --value-proposition "Prompt templates for product copy, SEO content, and video scripts" \
  --goal leads \
  --out-dir "./promotion-output"
```

To extract a product profile directly from a public page or saved HTML:

```bash
python scripts/product_intake.py --url "https://example.com/product" --out-dir "./promotion-output/intake"
```

To parse a rendered page snapshot captured by Codex/browser tooling:

```bash
python scripts/product_intake.py \
  --structured-json "./rendered-product-page.json" \
  --out-dir "./promotion-output/intake"
```

To render a real MP4 draft video after content generation:

```bash
python scripts/render_video.py \
  --content-json "./promotion-output/reports/promotion-manager/generated-content/ai-prompt-kit-platform-content.json" \
  --platform douyin \
  --out "./promotion-output/videos/ai-prompt-kit-douyin.mp4"
```

To render with a voiceover audio file:

```bash
python scripts/render_video.py \
  --content-json "./promotion-output/reports/promotion-manager/generated-content/ai-prompt-kit-platform-content.json" \
  --platform youtube \
  --voiceover-audio "./voiceover.wav" \
  --out "./promotion-output/videos/ai-prompt-kit-youtube.mp4"
```

To import competitor evidence from a public page, saved HTML, JSON export, or copied transcript:

```bash
python scripts/competitor_intake.py \
  --html-file "./competitor.html" \
  --platform youtube \
  --out-dir "./promotion-output"
```

To create platform search tasks for competitor discovery:

```bash
python scripts/competitor_discovery.py \
  --query "AI product copy generator" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --out-dir "./promotion-output"
```

To automatically collect competitor evidence through supported official/public connectors:

```bash
python scripts/competitor_collector.py \
  --platform github \
  --query "AI product copy generator" \
  --out-dir "./promotion-output"
```

To capture multi-result search pages from Codex/browser-rendered snapshots:

```bash
python scripts/platform_search_capture.py \
  --structured-json "./search-snapshots/douyin.json" \
  --platform douyin \
  --query "AI product copy generator" \
  --out-dir "./promotion-output"
```

For a full workflow, place files such as `youtube.json`, `zhihu.json`, `xiaohongshu.json`, and `douyin.json` in one directory:

```bash
python scripts/run_promotion_workflow.py \
  --product-url "https://example.com/product" \
  --search-snapshot-dir "./search-snapshots" \
  --out-dir "./promotion-output"
```

To import real post-publish metrics from a platform or business export:

```bash
python scripts/metrics_intake.py \
  --csv-file "./metrics-export.csv" \
  --out-dir "./promotion-output"
```

To configure periodic local automation:

```bash
python scripts/automation_scheduler.py init \
  --config "./promotion-automation.json" \
  --job-id "product-weekly" \
  --product-url "https://example.com/product" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --interval-days 7
```

Then run due jobs manually or from an OS scheduler:

```bash
python scripts/automation_scheduler.py run --config "./promotion-automation.json"
```

To run an official publish action, start with a dry run:

```bash
python scripts/publish_executor.py \
  --platform github \
  --github-action file \
  --github-repo owner/repo \
  --path PROMOTION.md \
  --content-file "./promotion-output/reports/promotion-manager/generated-content/product-platform-content.md" \
  --out-dir "./promotion-output"
```

To turn a completed workflow into a guarded publish queue for all target platforms:

```bash
python scripts/publish_queue.py \
  --workflow-manifest "./promotion-output/reports/promotion-manager/agent-run/workflow-manifest.json" \
  --github-repo owner/repo \
  --youtube-video-file "./promotion-output/videos/product-youtube.mp4" \
  --out-dir "./promotion-output"
```

To authorize and upload a YouTube video without saving tokens:

```bash
python scripts/youtube_oauth_publish.py \
  --video-file "./promotion-output/videos/product-youtube.mp4" \
  --title "Product launch draft" \
  --out-dir "./promotion-output"
```

The command writes:

- `docs/promotion-manager/01-platform-publishing-feasibility.md`
- `docs/promotion-manager/02-github-reference-projects.md`
- `docs/promotion-manager/03-platform-risk-matrix.md`
- `docs/promotion-manager/04-self-learning-notes.md`
- `docs/promotion-manager/05-browser-extension-roadmap.md`
- `docs/promotion-manager/06-saas-product-roadmap.md`
- `reports/promotion-manager/...` JSON and Markdown reports for research, deconstruction, content, review, publish packs, result input, and retrospective.
- `reports/promotion-manager/agent-run/workflow-manifest.{json,md}` when `scripts/run_promotion_workflow.py` is run.
- `reports/promotion-manager/competitors/captured-search-results-<platform>.{json,md}` when `scripts/platform_search_capture.py` captures search evidence.
- `reports/promotion-manager/publish-queue/publish-queue.{json,md}` and per-platform drafts when `scripts/publish_queue.py` prepares official dry-runs and manual/browser-assisted tasks.
- `promotion-output/automation/scheduler/automation-run.{json,md}` and `promotion-automation-state.json` when `scripts/automation_scheduler.py` runs scheduled jobs.
- `videos/*.mp4` only when `scripts/render_video.py` is run and `ffmpeg` is available.

## Workflows

### 1. Product URL Intake

- Extract factual product information from the page.
- Mark uncertain details as assumptions; do not invent pricing, testimonials, sales, or usage numbers.
- If a page cannot be read, ask for pasted product info.
- Use `scripts/product_intake.py` for deterministic metadata extraction from public HTML, saved product pages, rendered page text, or structured page snapshots captured by Codex/browser tooling.
- Prefer `scripts/run_promotion_workflow.py` for a full run. It calls product intake first and writes an agent workflow manifest.

### 2. Competitor And Trend Research

- For YouTube and GitHub, prefer official/public pages and APIs when available.
- For Zhihu, Xiaohongshu, and Douyin, use manual links, browser-assisted review, or user-provided screenshots/content where automated access is risky.
- Save findings in the output reports. Do not claim a platform API exists without official evidence.
- For detailed routing, read [references/platform-publishing.md](references/platform-publishing.md).
- Use the script `research` command first when platform feasibility or self-learning notes are needed.
- Use `scripts/competitor_discovery.py` to create platform search tasks and optional official API search results before importing evidence.
- Use `scripts/competitor_collector.py` to automatically collect YouTube official API evidence or GitHub public API evidence when credentials/access allow.
- Use `scripts/platform_search_capture.py` to normalize multi-result rendered search snapshots for YouTube, Zhihu, Xiaohongshu, Douyin, GitHub, TikTok, or similar platforms.
- Use `scripts/competitor_intake.py` to turn public competitor pages, saved HTML, JSON exports, or pasted transcripts into `imported-competitors` reports before deconstruction.

### 3. Content Generation

Generate platform-native material:

- YouTube: long-video titles, Shorts titles, descriptions, scripts, tags.
- Zhihu: long-form article titles, outlines, opening, CTA.
- Xiaohongshu: note titles, post bodies, cover text, tags, comment prompts.
- Douyin: 30-second hooks, voiceover scripts, storyboard, captions, hashtags.
- GitHub: README promotion copy, Release/Issue/Discussion drafts.

When the user asks for a video file, run `scripts/render_video.py` to create an MP4 from the generated content JSON. Use `--voiceover-audio` for a real recorded/AI voiceover file, or `--generate-voiceover` on Windows for review-quality system TTS. Without either option the renderer creates a silent captioned artifact.

### 4. Review And Score

Score every platform draft for:

- viral potential
- title/hook strength
- clarity
- conversion CTA
- platform fit
- SEO/GEO value
- compliance risk

If `cheat-on-content` is available, run a qualitative review through that skill. Do not write immutable prediction logs unless the user explicitly asks to start a real `cheat-on-content` prediction cycle. For details, read [references/cheat-on-content-integration.md](references/cheat-on-content-integration.md).

### 5. Publish Pack

Every publish pack must include:

- `publishMode`: `official_api_publish`, `browser_assisted_publish`, `manual_publish_required`, or `unsupported`
- `approvalRequired: true`
- manual steps
- warnings
- tracking fields
- schedule suggestion

YouTube and GitHub may be official API candidates. Zhihu, Xiaohongshu, and Douyin default to manual or browser-assisted publishing unless current official evidence proves otherwise.
For full-automation boundaries, read [references/final-capability-boundaries.md](references/final-capability-boundaries.md).
Use `scripts/publish_executor.py` for supported official publishing actions. It defaults to dry-run and only writes when `--execute --approval I_APPROVE_PUBLISH` is supplied with the required environment token.
Use `scripts/youtube_oauth_publish.py` when the user needs the full YouTube OAuth consent flow before upload. It requires `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` for execution and does not save OAuth tokens.
Use `scripts/publish_queue.py` after a workflow run to convert publish packs into executable GitHub/YouTube dry-runs plus manual/browser-assisted queue records for Zhihu, Xiaohongshu, Douyin, and other unsupported direct-publish platforms.

### 6. Retrospective

Use only real data supplied by the user or exported from platforms:

- views
- likes
- favorites
- comments
- shares
- clicks
- messages
- leads
- orders
- revenue
- evidence URLs/screenshots/exports

If no real data exists, output `waiting_real_data`. Never estimate or fabricate performance.
Use `scripts/metrics_intake.py` to import real CSV, JSON, text, GitHub, or YouTube metrics before doing a retrospective. YouTube live metrics require `YOUTUBE_API_KEY`; GitHub public repository metrics can use the public REST API.

### 7. Periodic Automation

Use `scripts/automation_scheduler.py` to run one or more product promotion jobs on a local schedule. The scheduler reads a JSON config, decides which jobs are due, calls `scripts/run_promotion_workflow.py`, writes a state file, and writes an automation run report. It can also generate a PowerShell script for Windows Task Scheduler.

The scheduler may generate content, videos, publish packs, official dry-run publish plans, and metrics import attempts. It must not bypass the publish approval gate. Official writes still require the publish executor, environment credentials, and `--approval I_APPROVE_PUBLISH`.
If a scheduled job has `publish.enabled: true`, the scheduler runs `scripts/publish_queue.py` after a successful workflow and records the queue report path in state. This still defaults to dry-run unless the job explicitly enables execution and supplies the approval phrase.

## Bundled Resources

- `scripts/promotion_manager.py`: deterministic report generator.
- `scripts/run_promotion_workflow.py`: end-to-end local agent workflow runner.
- `scripts/automation_scheduler.py`: JSON-configured periodic runner and Windows Task Scheduler script generator.
- `scripts/product_intake.py`: public URL, saved HTML, rendered text, or structured snapshot product-profile extractor.
- `scripts/competitor_discovery.py`: platform competitor search task generator with optional official API connectors.
- `scripts/competitor_collector.py`: official/public competitor evidence collector for YouTube and GitHub.
- `scripts/platform_search_capture.py`: multi-result search snapshot capture for rendered browser pages, HTML, text, and public URLs.
- `scripts/competitor_intake.py`: competitor evidence importer for public pages and user-provided exports.
- `scripts/metrics_intake.py`: real metrics importer for exports and supported official API reads.
- `scripts/publish_queue.py`: publish queue builder that creates platform drafts, GitHub/YouTube official dry-runs, and manual/browser-assisted publish tasks.
- `scripts/publish_executor.py`: approved official publish executor for GitHub and YouTube.
- `scripts/youtube_oauth_publish.py`: YouTube OAuth consent and same-process upload helper.
- `scripts/render_video.py`: ffmpeg-based MP4 renderer with caption, voiceover-audio, and Windows TTS support.
- `scripts/test_promotion_manager.py`: regression tests for report paths, safety modes, content counts, and retrospective guardrails.
- `references/workflow.md`: full operating workflow.
- `references/platform-publishing.md`: platform publishing modes and safety rules.
- `references/final-capability-boundaries.md`: final automation, authorization, and self-evolution limits.
- `references/cheat-on-content-integration.md`: optional review integration and prediction-cycle boundary.
- `references/output-schema.md`: report and field schema.
