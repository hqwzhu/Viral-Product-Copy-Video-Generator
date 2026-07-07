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
3. Use `scripts/run_promotion_workflow.py` for the default end-to-end local workflow: intake, competitor discovery, viral material ranking, competitor-informed content rewriting, video rendering, publish automation map, and metrics recovery status.
4. Review the generated content. If `cheat-on-content` is installed, use it for a second-pass content review; otherwise use the generated scorecard. Read [references/cheat-on-content-integration.md](references/cheat-on-content-integration.md) before writing prediction logs.
5. Give the user publish packs and ask for approval before any publishing action.

Default one-command workflow:

```bash
python scripts/run_promotion_workflow.py \
  --browser-url "https://example.com/product" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --out-dir "./promotion-output"
```

For static pages or environments without Playwright Chromium, use static HTML intake:

```bash
python scripts/run_promotion_workflow.py \
  --product-url "https://example.com/product" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --out-dir "./promotion-output"
```

For dynamic pages, Codex can capture the rendered page first and pass a structured snapshot:

```bash
python scripts/browser_snapshot.py \
  --url "https://example.com/product" \
  --out-file "./rendered-product-page.json"
```

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

To have Codex read one or more product URLs into structured snapshots and product profiles:

```bash
python scripts/product_url_reader.py \
  --url "https://example.com/product" \
  --out-dir "./promotion-output"
```

To batch-run multiple product URLs through Codex-first reading and one promotion cycle per ready product:

```bash
python scripts/product_batch_runner.py \
  --urls-file "./product-urls.txt" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --out-dir "./promotion-output"
```

To also run product-driven multi-query viral discovery after each ready product cycle:

```bash
python scripts/product_batch_runner.py \
  --urls-file "./product-urls.txt" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --run-multi-query-viral-discovery \
  --multi-query-query-count 5 \
  --multi-query-top-n 20 \
  --out-dir "./promotion-output"
```

To parse a rendered page snapshot captured by Codex/browser tooling:

```bash
python scripts/product_intake.py \
  --structured-json "./rendered-product-page.json" \
  --out-dir "./promotion-output/intake"
```

If Chromium is missing, install the official Playwright browser runtime:

```bash
python -m playwright install chromium
```

Or allow the workflow to attempt the official install when `--browser-url` is used:

```bash
python scripts/run_promotion_workflow.py \
  --browser-url "https://example.com/product" \
  --install-browser-if-missing \
  --out-dir "./promotion-output"
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

To automatically open public platform search pages and create browser-visible search snapshots:

```bash
python scripts/platform_search_browser.py \
  --query "AI product copy generator" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --out-dir "./promotion-output"
```

To run the standalone viral discovery pipeline from a keyword:

```bash
python scripts/viral_discovery_runner.py \
  --query "AI product copy generator" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --top-n 20 \
  --out-dir "./promotion-output"
```

To generate multiple product-driven search queries, run discovery for each, and merge the strongest viral materials and creators:

```bash
python scripts/multi_query_viral_discovery.py \
  --workflow-manifest "./promotion-output/reports/promotion-manager/agent-run/workflow-manifest.json" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --top-n 20 \
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

To rank captured platform search results into a viral material library and follow-up capture queue:

```bash
python scripts/viral_content_library.py \
  --search-capture-dir "./promotion-output/reports/promotion-manager/competitors" \
  --top-n 20 \
  --out-dir "./promotion-output"
```

To group ranked viral materials into a creator/account leaderboard and follow-up tracking tasks:

```bash
python scripts/creator_leaderboard.py \
  --viral-library "./promotion-output/reports/promotion-manager/competitors/viral-content-library.json" \
  --top-n 20 \
  --out-dir "./promotion-output"
```

To run safe creator/account follow-up research from that leaderboard:

```bash
python scripts/creator_follow_up_runner.py \
  --tasks-json "./promotion-output/reports/promotion-manager/competitors/creator-follow-up-tasks.json" \
  --dry-run \
  --out-dir "./promotion-output"
```

To execute safe follow-up captures from that queue:

```bash
python scripts/follow_up_capture_runner.py \
  --tasks-json "./promotion-output/reports/promotion-manager/competitors/follow-up-capture-tasks.json" \
  --capture-browser-assisted \
  --out-dir "./promotion-output"
```

To rewrite generated platform content with the ranked viral/deep competitor libraries before video rendering and publish-pack preparation:

```bash
python scripts/competitor_content_enhancer.py \
  --content-json "./promotion-output/reports/promotion-manager/generated-content/ai-prompt-kit-platform-content.json" \
  --viral-library "./promotion-output/reports/promotion-manager/competitors/viral-content-library.json" \
  --deep-library "./promotion-output/reports/promotion-manager/competitors/deep-competitor-library.json" \
  --write-back \
  --out-dir "./promotion-output"
```

For a full workflow, place files such as `youtube.json`, `zhihu.json`, `xiaohongshu.json`, and `douyin.json` in one directory:

```bash
python scripts/run_promotion_workflow.py \
  --product-url "https://example.com/product" \
  --search-snapshot-dir "./search-snapshots" \
  --out-dir "./promotion-output"
```

Or let the workflow create public search snapshots first:

```bash
python scripts/run_promotion_workflow.py \
  --browser-url "https://example.com/product" \
  --auto-search-competitors \
  --run-follow-up-captures \
  --capture-browser-assisted-follow-ups \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --out-dir "./promotion-output"
```

To import real post-publish metrics from a platform or business export:

```bash
python scripts/metrics_intake.py \
  --csv-file "./metrics-export.csv" \
  --out-dir "./promotion-output"
```

To import real metrics from a Codex/browser structured snapshot of a published page or analytics page:

```bash
python scripts/metrics_intake.py \
  --structured-json "./published-metrics-snapshot.json" \
  --out-dir "./promotion-output"
```

To recover metrics across a completed workflow, publish queue, published URLs, and business exports:

```bash
python scripts/metrics_recovery.py \
  --workflow-manifest "./promotion-output/reports/promotion-manager/agent-run/workflow-manifest.json" \
  --publish-queue "./promotion-output/reports/promotion-manager/publish-queue/publish-queue.json" \
  --business-csv "./orders-and-revenue.csv" \
  --out-dir "./promotion-output"
```

To attribute business orders and revenue exports that use UTM/content/referrer fields before recovery:

```bash
python scripts/business_attribution.py \
  --business-csv "./orders-and-revenue.csv" \
  --out-dir "./promotion-output"
```

Then merge the attribution export:

```bash
python scripts/metrics_recovery.py \
  --business-json "./promotion-output/reports/promotion-manager/business-attribution/business-attribution-export.json" \
  --out-dir "./promotion-output"
```

To merge structured metric snapshots with published URL evidence during recovery:

```bash
python scripts/metrics_recovery.py \
  --metrics-structured-json "./published-metrics-snapshot.json" \
  --out-dir "./promotion-output"
```

To register a manually published platform URL for later metrics recovery:

```bash
python scripts/published_items.py \
  --platform xiaohongshu \
  --published-url "https://www.xiaohongshu.com/explore/real-note-id" \
  --title "Published launch note" \
  --evidence "./screenshots/xhs-published.png" \
  --out-dir "./promotion-output"
```

To capture a browser-visible published page snapshot and register its real URL:

```bash
python scripts/publish_url_capture.py \
  --structured-json "./published-page-snapshot.json" \
  --out-dir "./promotion-output"
```

To automatically capture public/browser-visible metrics from registered published URLs:

```bash
python scripts/post_publish_metrics_capture.py \
  --out-dir "./promotion-output"
```

Then merge those captured metrics into the retrospective:

```bash
python scripts/metrics_recovery.py \
  --metrics-json "./promotion-output/reports/promotion-manager/post-publish-capture/post-publish-metrics-export.json" \
  --out-dir "./promotion-output"
```

To capture public/browser-visible comments and demand signals for the next content round:

```bash
python scripts/comment_evidence_capture.py \
  --out-dir "./promotion-output"
```

To configure periodic local automation:

```bash
python scripts/automation_scheduler.py init \
  --config "./promotion-automation.json" \
  --job-id "product-weekly" \
  --browser-url "https://example.com/product" \
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

To prepare an official Douyin Open Platform upload/create dry run, provide the rendered MP4 and post text:

```bash
python scripts/publish_executor.py \
  --platform douyin \
  --douyin-video-file "./promotion-output/videos/product-douyin.mp4" \
  --title "Product launch draft #AI" \
  --out-dir "./promotion-output"
```

To turn a completed workflow into a guarded publish queue for all target platforms:

```bash
python scripts/publish_queue.py \
  --workflow-manifest "./promotion-output/reports/promotion-manager/agent-run/workflow-manifest.json" \
  --github-repo owner/repo \
  --youtube-video-file "./promotion-output/videos/product-youtube.mp4" \
  --douyin-video-file "./promotion-output/videos/product-douyin.mp4" \
  --out-dir "./promotion-output"
```

To audit whether each queued platform is ready for dry-run review, official execution, or manual/browser-assisted publishing:

```bash
python scripts/publish_readiness_runner.py \
  --workflow-manifest "./promotion-output/reports/promotion-manager/agent-run/workflow-manifest.json" \
  --build-queue \
  --github-repo owner/repo \
  --youtube-video-file "./promotion-output/videos/product-youtube.mp4" \
  --douyin-video-file "./promotion-output/videos/product-douyin.mp4" \
  --out-dir "./promotion-output"
```

To prepare browser-assisted publishing payloads for Zhihu, Xiaohongshu, Douyin, TikTok, or other non-official direct-publish platforms:

```bash
python scripts/browser_publish_assistant.py \
  --publish-queue "./promotion-output/reports/promotion-manager/publish-queue/publish-queue.json" \
  --out-dir "./promotion-output"
```

To fill visible publisher form fields from one prepared payload and stop before final publish:

```bash
python scripts/browser_publish_form_fill.py \
  --payload-json "./promotion-output/reports/promotion-manager/browser-publish/payloads/xiaohongshu.payload.json" \
  --out-dir "./promotion-output"
```

After the user publishes manually or in a user-visible browser session, register the real URL through the same assistant:

```bash
python scripts/browser_publish_assistant.py \
  --publish-queue "./promotion-output/reports/promotion-manager/publish-queue/publish-queue.json" \
  --published-url "xiaohongshu=https://www.xiaohongshu.com/explore/real-note-id" \
  --evidence "./screenshots/xhs-published.png" \
  --out-dir "./promotion-output"
```

To audit official publishing and metrics access paths before claiming full automation:

```bash
python scripts/platform_access_audit.py --out-dir "./promotion-output"
```

To run one full local promotion cycle from product intake through publish queue, published URL registration, and real metrics recovery:

```bash
python scripts/promotion_cycle_runner.py \
  --browser-url "https://example.com/product" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --github-repo owner/repo \
  --business-csv "./orders-and-revenue.csv" \
  --out-dir "./promotion-output"
```

To include public post-publish metric capture, comment evidence capture, and business attribution in that same cycle:

```bash
python scripts/promotion_cycle_runner.py \
  --browser-url "https://example.com/product" \
  --published-url "xiaohongshu=https://www.xiaohongshu.com/explore/real-note-id" \
  --run-post-publish-metrics-capture \
  --run-comment-evidence-capture \
  --run-business-attribution \
  --business-csv "./orders-and-revenue.csv" \
  --out-dir "./promotion-output"
```

To audit final-agent readiness before a real run:

```bash
python scripts/final_capability_audit.py --out-dir "./promotion-output"
```

To audit controlled self-evolution, local tool gaps, repository state, and installed Skill drift:

```bash
python scripts/self_evolution_audit.py --out-dir "./promotion-output"
```

To explicitly install the allowlisted browser runtime if missing:

```bash
python scripts/final_capability_audit.py \
  --install-safe-missing-tools \
  --safe-install playwright_chromium \
  --out-dir "./promotion-output"
```

To sync reviewed local Skill files into the installed Codex Skill after verification:

```bash
python scripts/self_evolution_audit.py \
  --sync-installed-skill \
  --approval I_APPROVE_SKILL_SYNC \
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
- `browser-snapshot/product-page-snapshot.json` when `scripts/browser_snapshot.py` or `--browser-url` captures a rendered product page.
- `reports/promotion-manager/intake/product-url-reader.{json,md}` and `product-url-reader/<id>/structured-product-page.json` when `scripts/product_url_reader.py` reads product URLs into browser-visible structured snapshots and product profiles.
- `reports/promotion-manager/batch/product-batch-runner.{json,md}` and `product-batch-runs/<id>/...` when `scripts/product_batch_runner.py` reads multiple product URLs first, runs one promotion cycle per ready product, and optionally runs multi-query viral discovery per product.
- `search-snapshots/browser-search/<platform>.json` and `reports/promotion-manager/competitors/browser-search-snapshots.{json,md}` when `scripts/platform_search_browser.py` or `--auto-search-competitors` captures public search pages.
- `reports/promotion-manager/competitors/viral-discovery-run.{json,md}` when `scripts/viral_discovery_runner.py` runs keyword search, browser-visible capture, viral library creation, creator leaderboard generation, and optional follow-up queues as one standalone discovery pass.
- `reports/promotion-manager/competitors/multi-query-viral-discovery.{json,md}`, `multi-query-viral-content-library.{json,md}`, and `multi-query-creator-leaderboard.{json,md}` when `scripts/multi_query_viral_discovery.py` runs product-driven multi-query discovery and merges ranked materials and creators.
- `reports/promotion-manager/competitors/captured-search-results-<platform>.{json,md}` when `scripts/platform_search_capture.py` captures search evidence.
- `reports/promotion-manager/competitors/viral-content-library.{json,md}` and `follow-up-capture-tasks.{json,md}` when `scripts/viral_content_library.py` ranks captured search evidence.
- `reports/promotion-manager/competitors/creator-leaderboard.{json,md}` and `creator-follow-up-tasks.{json,md}` when `scripts/creator_leaderboard.py` groups viral materials by creator/account and creates safe tracking tasks.
- `reports/promotion-manager/competitors/creator-follow-up-results.{json,md}` and `creator-deep-library.{json,md}` when `scripts/creator_follow_up_runner.py` runs safe public creator/account follow-up research or queues manual evidence.
- `reports/promotion-manager/competitors/follow-up-capture-results.{json,md}` and `deep-competitor-library.{json,md}` when `scripts/follow_up_capture_runner.py` executes safe follow-up captures.
- `reports/promotion-manager/competitors/follow-up-captures/<task>/browser-visible-snapshot.json` when browser-assisted follow-up capture opens a public platform URL and imports browser-visible page evidence.
- `reports/promotion-manager/generated-content/<product>-competitor-informed-content.{json,md}` and `<product>-competitor-informed-strategy.json` when `scripts/competitor_content_enhancer.py` rewrites generated content from observed viral patterns. The workflow writes this back to `<product>-platform-content.json` before video rendering unless `--skip-competitor-informed-content` is supplied.
- `reports/promotion-manager/publish-queue/publish-queue.{json,md}` and per-platform drafts when `scripts/publish_queue.py` prepares official dry-runs and manual/browser-assisted tasks.
- `reports/promotion-manager/publish-readiness/publish-readiness.{json,md}` when `scripts/publish_readiness_runner.py` audits queue status, credential presence by environment variable name, target readiness, approval status, and next actions.
- `reports/promotion-manager/browser-publish/browser-publish-assistant.{json,md}` and `payloads/*` when `scripts/browser_publish_assistant.py` prepares user-visible publish payloads, form-fill helpers, browser form-fill commands, checklists, and optional real URL registration for manual/browser-assisted platforms.
- `reports/promotion-manager/browser-publish/browser-form-fill.{json,md}` and `browser-form-fill.png` when `scripts/browser_publish_form_fill.py` fills visible publisher fields from one prepared payload and stops before final publish.
- `reports/promotion-manager/platform-access/platform-access-audit.{json,md}` when `scripts/platform_access_audit.py` maps official API, app-review, manual/browser-assisted, and metrics access boundaries.
- `reports/promotion-manager/publish-capture/publish-url-capture.{json,md}` when `scripts/publish_url_capture.py` captures a browser-visible published page and registers the real URL.
- `reports/promotion-manager/published-items/published-items.{json,md}` when `scripts/published_items.py` registers proven published URLs from queue execution reports or manual evidence.
- `reports/promotion-manager/post-publish-capture/post-publish-metrics-capture.{json,md}`, `post-publish-metrics-export.json`, and `post-publish-metrics-snapshot.json` when `scripts/post_publish_metrics_capture.py` captures public/browser-visible metrics from registered published URLs.
- `reports/promotion-manager/comment-evidence/comment-evidence-capture.{json,md}` and `comment-evidence-export.json` when `scripts/comment_evidence_capture.py` captures public/browser-visible comments and demand signals.
- `reports/promotion-manager/business-attribution/business-attribution.{json,md}` and `business-attribution-export.json` when `scripts/business_attribution.py` attributes real business exports to proven published content using URL, UTM content, referrer, or title/campaign evidence.
- `reports/promotion-manager/metrics-recovery/metrics-recovery.{json,md}` when `scripts/metrics_recovery.py` coordinates official metrics connectors and business exports.
- `reports/promotion-manager/cycle/promotion-cycle.{json,md}` when `scripts/promotion_cycle_runner.py` runs the workflow, publish queue, published item registration, optional post-publish metrics capture, optional comment evidence capture, optional business attribution, and metrics recovery as one local operating cycle.
- `reports/promotion-manager/capability/final-capability-audit.{json,md}` when `scripts/final_capability_audit.py` checks scripts, tools, credential presence, platform limits, and final requirement gaps.
- `reports/promotion-manager/self-evolution/self-evolution-audit.{json,md}` when `scripts/self_evolution_audit.py` checks local tools, repository state, installed Skill drift, safe install candidates, and approved Skill sync actions.
- `promotion-output/automation/scheduler/automation-run.{json,md}` and `promotion-automation-state.json` when `scripts/automation_scheduler.py` runs scheduled jobs.
- `videos/*.mp4` only when `scripts/render_video.py` is run and `ffmpeg` is available.

## Workflows

### 1. Product URL Intake

- Extract factual product information from the page.
- Mark uncertain details as assumptions; do not invent pricing, testimonials, sales, or usage numbers.
- If a page cannot be read, ask for pasted product info.
- Use `scripts/product_intake.py` for deterministic metadata extraction from public HTML, saved product pages, rendered page text, or structured page snapshots captured by Codex/browser tooling.
- Use `scripts/browser_snapshot.py` or `scripts/run_promotion_workflow.py --browser-url` when the product page is dynamic or Codex needs rendered DOM evidence before intake.
- Use `scripts/product_url_reader.py` when the user sends one or more product URLs and wants Codex to read the rendered page first, write a structured snapshot, pass it into `product_intake.py`, and return a product profile plus the correct next workflow command.
- Use `scripts/product_batch_runner.py` when the user sends multiple product URLs and wants the Skill to read each URL first, then run a guarded promotion cycle for every ready product. Add `--run-multi-query-viral-discovery` when each product should also derive multiple search queries and merge viral materials/creators after the cycle.
- Use `scripts/final_capability_audit.py` before claiming final-agent readiness. The audit checks local scripts, browser runtime, `ffmpeg`, credential presence, publish constraints, metrics inputs, and self-evolution limits without writing credential values. It also runs `scripts/self_evolution_audit.py` and records the self-evolution report path.
- Use `scripts/self_evolution_audit.py` when the Skill needs to inspect local tool gaps, repo/installed-Skill drift, safe runtime install candidates, or approved local Skill sync actions.
- Prefer `scripts/run_promotion_workflow.py` for a full run. It calls product intake first and writes an agent workflow manifest.

### 2. Competitor And Trend Research

- For YouTube and GitHub, prefer official/public pages and APIs when available.
- For Zhihu, Xiaohongshu, and Douyin, use manual links, browser-assisted review, or user-provided screenshots/content where automated access is risky.
- Save findings in the output reports. Do not claim a platform API exists without official evidence.
- For detailed routing, read [references/platform-publishing.md](references/platform-publishing.md).
- Use the script `research` command first when platform feasibility or self-learning notes are needed.
- Use `scripts/competitor_discovery.py` to create platform search tasks and optional official API search results before importing evidence.
- Use `scripts/competitor_collector.py` to automatically collect YouTube official API evidence or GitHub public API evidence when credentials/access allow.
- Use `scripts/platform_search_browser.py` or `scripts/run_promotion_workflow.py --auto-search-competitors` to create browser-visible public search snapshots for YouTube, Zhihu, Xiaohongshu, Douyin, GitHub, TikTok, and similar platforms.
- Use `scripts/viral_discovery_runner.py` when the user specifically asks to automatically find viral creators, posts, videos, or repositories from a keyword before product copy generation. It chains browser-visible platform search, normalized capture, ranked viral library creation, creator leaderboard generation, and optional follow-up queues.
- Use `scripts/multi_query_viral_discovery.py` when one keyword is too narrow. It derives queries from the product profile, value proposition, keywords, audience, and pain points; runs or plans one discovery pass per query; then dedupes and ranks the merged viral materials and creator leaderboard.
- Use `scripts/platform_search_capture.py` to normalize multi-result rendered search snapshots for YouTube, Zhihu, Xiaohongshu, Douyin, GitHub, TikTok, or similar platforms.
- Use `scripts/viral_content_library.py` after search capture to rank top viral materials across platforms and create follow-up capture tasks. Public YouTube/GitHub URLs become safe capture candidates; Zhihu, Xiaohongshu, Douyin, and TikTok stay browser-assisted/user-export tasks unless official access is verified.
- Use `scripts/creator_leaderboard.py` after the viral library exists to identify high-signal creators/accounts, aggregate their observed public metrics, and create creator follow-up tasks. The full workflow does this automatically unless `--skip-creator-leaderboard` is supplied.
- Use `scripts/creator_follow_up_runner.py` after the creator leaderboard exists to run safe YouTube/GitHub creator follow-up through official/public connectors and queue manual/browser evidence requests for Zhihu, Xiaohongshu, Douyin, TikTok, and unverified platforms. In the full workflow, add `--run-creator-follow-up`; use `--creator-follow-up-dry-run` for planning-only runs.
- Use `scripts/follow_up_capture_runner.py` to execute only safe public follow-up capture tasks and generate manual evidence request files for browser-assisted platforms. In the full workflow, add `--run-follow-up-captures` when you want this stage to run.
- Add `--capture-browser-assisted` to `scripts/follow_up_capture_runner.py`, or `--capture-browser-assisted-follow-ups` to the full workflow, when queued Zhihu, Xiaohongshu, Douyin, TikTok, or similar follow-up tasks should attempt public browser-visible snapshots before falling back to manual evidence requests.
- Use `scripts/competitor_content_enhancer.py` after the viral/deep libraries exist to apply observed hooks, reusable patterns, and safe structure summaries to the generated platform content. The full workflow does this automatically when a library exists; use `--skip-competitor-informed-content` to disable it.
- Use `scripts/competitor_intake.py` to turn public competitor pages, saved HTML, JSON exports, or pasted transcripts into `imported-competitors` reports before deconstruction.

### 3. Content Generation

Generate platform-native material:

- YouTube: long-video titles, Shorts titles, descriptions, scripts, tags.
- Zhihu: long-form article titles, outlines, opening, CTA.
- Xiaohongshu: note titles, post bodies, cover text, tags, comment prompts.
- Douyin: 30-second hooks, voiceover scripts, storyboard, captions, hashtags.
- GitHub: README promotion copy, Release/Issue/Discussion drafts.

When competitor search evidence exists, generated drafts should include `competitorInformed` metadata and should preserve source titles/hooks as evidence metadata only. Reuse structure; do not copy competitor wording or transfer competitor metrics into product claims.

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

YouTube, GitHub, and Douyin have official API executor paths, but execution still requires platform credentials, user authorization, and explicit approval. Zhihu and Xiaohongshu remain manual or browser-assisted unless current official creator-publishing evidence proves otherwise.
For full-automation boundaries, read [references/final-capability-boundaries.md](references/final-capability-boundaries.md).
Use `scripts/publish_executor.py` for supported official publishing actions. It defaults to dry-run and only writes when `--execute --approval I_APPROVE_PUBLISH` is supplied with the required environment token.
For Douyin, `scripts/publish_executor.py --platform douyin` uses the official upload/create flow with `--douyin-video-file` and requires `DOUYIN_ACCESS_TOKEN` plus `DOUYIN_OPEN_ID` for execution. App approval, `video.create.bind`-style publishing permission, user authorization, and platform review remain external requirements.
Use `scripts/youtube_oauth_publish.py` when the user needs the full YouTube OAuth consent flow before upload. It requires `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` for execution and does not save OAuth tokens.
Use `scripts/publish_queue.py` after a workflow run to convert publish packs into executable GitHub/YouTube dry-runs, Douyin official dry-runs when `--douyin-video-file` is supplied, plus manual/browser-assisted queue records for Zhihu, Xiaohongshu, and other unsupported direct-publish platforms.
Use `scripts/publish_readiness_runner.py` after a workflow run or existing publish queue to produce a machine-checkable readiness report before execution. It may build the guarded queue first with `--build-queue`; it records credential presence only by environment variable name and still requires `--execute-publish --approval I_APPROVE_PUBLISH` before official writes.
Use `scripts/browser_publish_assistant.py` after `publish_queue.py` to prepare browser-assisted payload files, platform entry URLs, generic form-fill helper scripts, browser form-fill commands, and post-publish URL registration commands for Zhihu, Xiaohongshu, Douyin, TikTok, or similar platforms. It may open publisher entry URLs in the user's default browser with `--open-browser`, but it must not auto-login, solve captcha, or click the final publish button.
Use `scripts/browser_publish_form_fill.py` only on a prepared payload JSON when the user wants Codex to fill visible publisher fields. It writes a screenshot and report, does not submit the form, and must stop for login, captcha, risk control, account verification, or final publish.
Use `scripts/platform_access_audit.py` when you need a machine-readable official access boundary report for YouTube, Zhihu, Xiaohongshu, Douyin, GitHub, and TikTok before deciding whether a platform can be automated or must remain manual/browser-assisted.
Use `scripts/published_items.py` after a manual/browser-assisted publish to register the real published URL and evidence. `scripts/publish_queue.py` also writes a `published-items` report automatically; dry-runs and queued tasks remain pending, not published.
Use `scripts/publish_url_capture.py` when Codex or the user has a post-publish browser snapshot, saved HTML, or copied page text. It extracts the real platform URL/title, blocks draft or preview URLs, and updates `published-items` for metrics recovery.
Use `scripts/post_publish_metrics_capture.py` after real published URLs are registered. It fetches public pages or browser-visible snapshots, extracts visible views/likes/comments/saves/shares/clicks/leads/orders/revenue when present, writes a `post-publish-metrics-export.json` file for `metrics_recovery.py`, and queues manual evidence when login/captcha/private analytics are required.
Use `scripts/promotion_cycle_runner.py` when the user wants one command to run generation, guarded publish queue, published URL registration, optional public metrics capture, optional comment evidence capture, optional business attribution, and metrics recovery. Official GitHub/YouTube/Douyin writes still require `--execute-publish --approval I_APPROVE_PUBLISH` plus credentials; dry-runs and manual/browser-assisted tasks remain pending rather than published.

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
Use `scripts/metrics_intake.py` to import real CSV, JSON, text, Codex/browser structured snapshots, GitHub, or YouTube metrics before doing a retrospective. YouTube live metrics require `YOUTUBE_API_KEY`; GitHub public repository metrics can use the public REST API.
Use `scripts/metrics_recovery.py` when the run has a workflow manifest, publish queue, `published-items` report, published URL list, structured metric snapshot, or business export. It merges official GitHub/YouTube metrics with user-provided platform snapshots and orders/revenue exports, and marks Zhihu, Xiaohongshu, Douyin, TikTok, or unpublished queue items as `manual_export_required` or `publish_pending` instead of inventing data.
Before a retrospective, run `scripts/post_publish_metrics_capture.py` when `published-items.json` contains real URLs. It captures only public/browser-visible metrics and produces `post-publish-metrics-export.json`; pass that file to `metrics_recovery.py --metrics-json`. If metrics are hidden behind platform analytics, login, captcha, or risk checks, use the generated manual evidence request and import a real export or screenshot-derived text.
Run `scripts/comment_evidence_capture.py` after real published URLs or visible comment exports exist. It extracts public/browser-visible comments, likes/replies per comment when visible, and demand signals such as questions, pricing objections, integrations, feature requests, pain points, and CTA intent. Treat its manual evidence requests as missing evidence, not recovered comments.
Run `scripts/business_attribution.py` when orders or revenue are exported from a business system with UTM fields, referrers, content IDs, or campaign/title fields. It attributes only rows that match proven published content and leaves weak platform-only rows unmatched.

### 7. Periodic Automation

Use `scripts/automation_scheduler.py` to run one or more product promotion jobs on a local schedule. The scheduler reads a JSON config, decides which jobs are due, calls `scripts/run_promotion_workflow.py`, writes a state file, and writes an automation run report. It can also generate a PowerShell script for Windows Task Scheduler.

The scheduler may generate content, videos, publish packs, official dry-run publish plans, and metrics import attempts. It must not bypass the publish approval gate. Official writes still require the publish executor, environment credentials, and `--approval I_APPROVE_PUBLISH`.
If a scheduled job has `publish.enabled: true`, the scheduler runs `scripts/publish_queue.py` after a successful workflow and records the queue report path in state. This still defaults to dry-run unless the job explicitly enables execution and supplies the approval phrase.
Scheduled jobs can set `publish.douyin.videoFile` to pass a rendered MP4 into the Douyin official dry-run queue; execution still requires approved open-platform credentials and `I_APPROVE_PUBLISH`.
If a scheduled job has `browserPublishAssistant.enabled: true`, the scheduler runs `scripts/browser_publish_assistant.py` after publish queue generation and records the browser/manual payload report path in state.
If a scheduled job has `postPublishMetricsCapture.enabled: true`, the scheduler runs `scripts/post_publish_metrics_capture.py` after published URL registration and before metrics recovery. Captured metrics are passed into `scripts/metrics_recovery.py` as a JSON metrics source when `metricsRecovery.enabled` is also true.
If a scheduled job has `commentEvidenceCapture.enabled: true`, the scheduler runs `scripts/comment_evidence_capture.py` after the workflow and records the public/browser-visible comment evidence report path in state.
If a scheduled job has `businessAttribution.enabled: true`, the scheduler runs `scripts/business_attribution.py` before metrics recovery and passes `business-attribution-export.json` into `scripts/metrics_recovery.py` when recovery is enabled.
If a scheduled job has `metricsRecovery.enabled: true`, the scheduler runs `scripts/metrics_recovery.py` after the workflow and optional publish queue, then records the metrics recovery report path in state.
If a scheduled job has `multiQueryViralDiscovery.enabled: true`, the scheduler runs `scripts/multi_query_viral_discovery.py` after the workflow manifest is created and records the merged discovery report path in state. Use `multiQueryViralDiscovery.dryRun: true` for planning-only recurring research.
Scheduled jobs can set `skipCreatorLeaderboard: true` to skip creator/account aggregation after the viral material library.
Scheduled jobs can set `followUpCapture.captureBrowserAssisted: true` to attempt public browser-visible snapshots for queued browser-assisted follow-up tasks.
Scheduled jobs can set `creatorFollowUp.enabled: true` to run safe creator/account follow-up research after the creator leaderboard. Use `creatorFollowUp.dryRun: true` for planning-only runs.
Scheduled jobs can set `competitorInformedContent.enabled: false` to disable rewriting with viral/deep competitor libraries, or `true` to pass the explicit `--use-competitor-informed-content` flag.

## Bundled Resources

- `scripts/promotion_manager.py`: deterministic report generator.
- `scripts/run_promotion_workflow.py`: end-to-end local agent workflow runner.
- `scripts/automation_scheduler.py`: JSON-configured periodic runner and Windows Task Scheduler script generator.
- `scripts/browser_snapshot.py`: Playwright/HTML structured snapshot capturer for rendered product pages.
- `scripts/product_url_reader.py`: URL-to-structured-snapshot/product-profile runner for Codex-first product page reading.
- `scripts/product_batch_runner.py`: batch URL runner that invokes Codex-first reading, one promotion cycle per ready product, and optional per-product multi-query viral discovery.
- `scripts/product_intake.py`: public URL, saved HTML, rendered text, or structured snapshot product-profile extractor.
- `scripts/competitor_discovery.py`: platform competitor search task generator with optional official API connectors.
- `scripts/competitor_collector.py`: official/public competitor evidence collector for YouTube and GitHub.
- `scripts/platform_search_browser.py`: public search page browser snapshot generator for platform competitor discovery.
- `scripts/platform_search_capture.py`: multi-result search snapshot capture for rendered browser pages, HTML, text, and public URLs.
- `scripts/viral_discovery_runner.py`: standalone keyword-to-viral-library runner for platform search, content capture, creator leaderboard, and follow-up queues.
- `scripts/multi_query_viral_discovery.py`: product-driven multi-query viral discovery planner/runner and merged material/creator aggregator.
- `scripts/viral_content_library.py`: ranked multi-platform viral material library and follow-up capture task generator.
- `scripts/creator_leaderboard.py`: creator/account leaderboard and follow-up tracking task generator from ranked viral materials.
- `scripts/creator_follow_up_runner.py`: safe creator/account follow-up runner that uses public/official connectors where available and queues manual evidence elsewhere.
- `scripts/follow_up_capture_runner.py`: safe public and browser-visible follow-up capture executor and deep competitor library builder.
- `scripts/competitor_content_enhancer.py`: rewrites generated platform content and publish packs using observed viral/deep competitor patterns before videos are rendered.
- `scripts/competitor_intake.py`: competitor evidence importer for public pages and user-provided exports.
- `scripts/metrics_intake.py`: real metrics importer for exports and supported official API reads.
- `scripts/metrics_recovery.py`: metrics recovery coordinator for workflow manifests, publish queues, published URL evidence, and business exports.
- `scripts/published_items.py`: published URL registrar for official execution reports, publish queues, and manual/browser-assisted publish evidence.
- `scripts/publish_url_capture.py`: post-publish browser snapshot/HTML/text capturer that registers real published URLs.
- `scripts/post_publish_metrics_capture.py`: public/browser-visible post-publish metrics capturer for registered URLs; writes a metrics export for recovery and manual evidence requests when metrics are hidden.
- `scripts/comment_evidence_capture.py`: public/browser-visible comment and demand-signal capturer for post-publish retrospectives and next-round content optimization.
- `scripts/business_attribution.py`: order/revenue export attribution to proven published content using URL, UTM content, referrer, content ID, or title/campaign evidence.
- `scripts/publish_queue.py`: publish queue builder that creates platform drafts, GitHub/YouTube official dry-runs, Douyin official dry-runs when a video file is supplied, and manual/browser-assisted publish tasks.
- `scripts/publish_readiness_runner.py`: publish readiness auditor for queue status, target info, credentials, approval, and per-platform next actions without storing secret values.
- `scripts/browser_publish_assistant.py`: user-visible browser-assisted publishing payload preparer and real published URL registrar for platforms without verified direct API publishing.
- `scripts/browser_publish_form_fill.py`: controlled Playwright helper that fills visible publisher fields from a prepared payload, screenshots the result, and stops before final publish.
- `scripts/platform_access_audit.py`: official access boundary auditor for platform publishing, metrics recovery, app-review requirements, and manual/browser-assisted fallback rules.
- `scripts/publish_executor.py`: approved official publish executor for GitHub, YouTube, and Douyin Open Platform video upload/create.
- `scripts/youtube_oauth_publish.py`: YouTube OAuth consent and same-process upload helper.
- `scripts/promotion_cycle_runner.py`: one-command local operating cycle for workflow generation, guarded publish queue, published item registration, post-publish metric/comment evidence capture, business attribution, and metrics recovery.
- `scripts/final_capability_audit.py`: final readiness auditor for requested end-state requirements, local tools, credential presence, platform limits, and controlled self-evolution actions.
- `scripts/self_evolution_audit.py`: controlled self-evolution auditor for runtime gaps, repository status, installed Skill drift, safe install candidates, and approved local Skill sync.
- `scripts/render_video.py`: ffmpeg-based MP4 renderer with caption, voiceover-audio, and Windows TTS support.
- `scripts/test_promotion_manager.py`: regression tests for report paths, safety modes, content counts, and retrospective guardrails.
- `references/workflow.md`: full operating workflow.
- `references/platform-publishing.md`: platform publishing modes and safety rules.
- `references/final-capability-boundaries.md`: final automation, authorization, and self-evolution limits.
- `references/cheat-on-content-integration.md`: optional review integration and prediction-cycle boundary.
- `references/output-schema.md`: report and field schema.
