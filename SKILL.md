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
3. Use `scripts/promotion_manager.py all` to generate deterministic local docs and reports.
4. Review the generated content. If `cheat-on-content` is installed, use it for a second-pass content review; otherwise use the generated scorecard. Read [references/cheat-on-content-integration.md](references/cheat-on-content-integration.md) before writing prediction logs.
5. Give the user publish packs and ask for approval before any publishing action.

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

To render a real MP4 draft video after content generation:

```bash
python scripts/render_video.py \
  --content-json "./promotion-output/reports/promotion-manager/generated-content/ai-prompt-kit-platform-content.json" \
  --platform douyin \
  --out "./promotion-output/videos/ai-prompt-kit-douyin.mp4"
```

The command writes:

- `docs/promotion-manager/01-platform-publishing-feasibility.md`
- `docs/promotion-manager/02-github-reference-projects.md`
- `docs/promotion-manager/03-platform-risk-matrix.md`
- `docs/promotion-manager/04-self-learning-notes.md`
- `docs/promotion-manager/05-browser-extension-roadmap.md`
- `docs/promotion-manager/06-saas-product-roadmap.md`
- `reports/promotion-manager/...` JSON and Markdown reports for research, deconstruction, content, review, publish packs, result input, and retrospective.
- `videos/*.mp4` only when `scripts/render_video.py` is run and `ffmpeg` is available.

## Workflows

### 1. Product URL Intake

- Extract factual product information from the page.
- Mark uncertain details as assumptions; do not invent pricing, testimonials, sales, or usage numbers.
- If a page cannot be read, ask for pasted product info.
- Use `scripts/product_intake.py` for deterministic metadata extraction from public HTML or saved product pages.

### 2. Competitor And Trend Research

- For YouTube and GitHub, prefer official/public pages and APIs when available.
- For Zhihu, Xiaohongshu, and Douyin, use manual links, browser-assisted review, or user-provided screenshots/content where automated access is risky.
- Save findings in the output reports. Do not claim a platform API exists without official evidence.
- For detailed routing, read [references/platform-publishing.md](references/platform-publishing.md).
- Use the script `research` command first when platform feasibility or self-learning notes are needed.

### 3. Content Generation

Generate platform-native material:

- YouTube: long-video titles, Shorts titles, descriptions, scripts, tags.
- Zhihu: long-form article titles, outlines, opening, CTA.
- Xiaohongshu: note titles, post bodies, cover text, tags, comment prompts.
- Douyin: 30-second hooks, voiceover scripts, storyboard, captions, hashtags.
- GitHub: README promotion copy, Release/Issue/Discussion drafts.

When the user asks for a video file, run `scripts/render_video.py` to create a draft MP4 from the generated content JSON. This creates a silent review artifact with burned-in captions; replace it with real voiceover and visuals before final publication if production quality is required.

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

## Bundled Resources

- `scripts/promotion_manager.py`: deterministic report generator.
- `scripts/product_intake.py`: public URL or saved HTML product-profile extractor.
- `scripts/render_video.py`: ffmpeg-based MP4 draft renderer.
- `scripts/test_promotion_manager.py`: regression tests for report paths, safety modes, content counts, and retrospective guardrails.
- `references/workflow.md`: full operating workflow.
- `references/platform-publishing.md`: platform publishing modes and safety rules.
- `references/final-capability-boundaries.md`: final automation, authorization, and self-evolution limits.
- `references/cheat-on-content-integration.md`: optional review integration and prediction-cycle boundary.
- `references/output-schema.md`: report and field schema.
