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
3. Use `scripts/promotion_manager.py all` to generate deterministic local reports.
4. Review the generated content. If `cheat-on-content` is installed, use it for a second-pass content review; otherwise use the generated scorecard.
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

## Workflows

### 1. Product URL Intake

- Extract factual product information from the page.
- Mark uncertain details as assumptions; do not invent pricing, testimonials, sales, or usage numbers.
- If a page cannot be read, ask for pasted product info.

### 2. Competitor And Trend Research

- For YouTube and GitHub, prefer official/public pages and APIs when available.
- For Zhihu, Xiaohongshu, and Douyin, use manual links, browser-assisted review, or user-provided screenshots/content where automated access is risky.
- Save findings in the output reports. Do not claim a platform API exists without official evidence.
- For detailed routing, read [references/platform-publishing.md](references/platform-publishing.md).

### 3. Content Generation

Generate platform-native material:

- YouTube: long-video titles, Shorts titles, descriptions, scripts, tags.
- Zhihu: long-form article titles, outlines, opening, CTA.
- Xiaohongshu: note titles, post bodies, cover text, tags, comment prompts.
- Douyin: 30-second hooks, voiceover scripts, storyboard, captions, hashtags.
- GitHub: README promotion copy, Release/Issue/Discussion drafts.

### 4. Review And Score

Score every platform draft for:

- viral potential
- title/hook strength
- clarity
- conversion CTA
- platform fit
- SEO/GEO value
- compliance risk

If `cheat-on-content` is available, run a qualitative review through that skill. Do not write immutable prediction logs unless the user explicitly asks to start a real `cheat-on-content` prediction cycle.

### 5. Publish Pack

Every publish pack must include:

- `publishMode`: `official_api_publish`, `browser_assisted_publish`, `manual_publish_required`, or `unsupported`
- `approvalRequired: true`
- manual steps
- warnings
- tracking fields
- schedule suggestion

YouTube and GitHub may be official API candidates. Zhihu, Xiaohongshu, and Douyin default to manual or browser-assisted publishing unless current official evidence proves otherwise.

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
- `references/workflow.md`: full operating workflow.
- `references/platform-publishing.md`: platform publishing modes and safety rules.
- `references/output-schema.md`: report and field schema.

