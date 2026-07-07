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

Use the deterministic extractor when possible:

```bash
python scripts/product_intake.py --url "https://example.com/product" --out-dir "./promotion-output/intake"
```

## Stage 2: Research

Create a competitor and trend research note before generating final content when the user wants current market positioning.

Create platform search tasks first:

```bash
python scripts/competitor_discovery.py \
  --query "AI product copy generator" \
  --platforms youtube,zhihu,xiaohongshu,douyin,github \
  --out-dir "./promotion-output"
```

Use `--live-official` only for supported official APIs. GitHub public repository search can run without credentials. YouTube live search requires `YOUTUBE_API_KEY` in the environment; do not write the key to files or chat output.

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

## Stage 4: Review

Use the bundled scorecard first. If `cheat-on-content` is installed, run it as a second-pass qualitative reviewer. Do not mutate real prediction logs unless the user asks.

## Stage 5: Publish Pack

Create publish packs. Every pack requires human approval before execution. Browser-assisted publishing may fill forms, but the user must click the final publish button.

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

## Stage 6: Retrospective

Generate a retrospective only from real data and evidence. If data is missing, return `waiting_real_data`.

Import real metrics first:

```bash
python scripts/metrics_intake.py \
  --csv-file "./metrics-export.csv" \
  --out-dir "./promotion-output"
```

Supported sources are `--csv-file`, `--json-file`, `--text-file`, `--published-url`, `--github-repo`, and `--youtube-video-id`. GitHub public repository metrics use the official REST API. YouTube video statistics require `YOUTUBE_API_KEY` in the environment and the key must not be written to files or chat output. Orders and revenue must come from user-provided business exports or analytics evidence.

## Phase 2 And Phase 3 Boundaries

The script may generate roadmap documents for a browser extension and SaaS product, but do not implement either until the user explicitly approves that phase.
