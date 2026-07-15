# Open Source Integration Plan

This document records how ENHE Product Promo Maker uses ideas from `firecrawl/firecrawl` and `yikart/AiToEarn` without copying unsafe automation paths.

## Source Snapshot

| Project | Snapshot inspected | Applied role |
| --- | --- | --- |
| `firecrawl/firecrawl` | `b1bd74a`, 2026-07-10 | Optional public web data backend for Search, Scrape, Map, Crawl, Batch Scrape, and future Agent/MCP evidence collection. |
| `yikart/AiToEarn` | `e48981e`, 2026-07-09 | Architecture reference for platform capability registry, publish records, scheduling, MCP-facing tools, creator tasks, and settlement flow. |

## What Was Integrated

### Firecrawl-Style Web Data Layer

Implemented:

- `scripts/web_data_provider.py`
- `product_url_reader.py` Firecrawl scrape fallback before public web-text fallback
- `product_url_discovery.py` Firecrawl map support for site URL discovery
- `platform_search_browser.py` Firecrawl search support before browser-visible search fallback

Environment variables:

```env
WEB_DATA_PROVIDER=auto
FIRECRAWL_API_KEY=
FIRECRAWL_BASE_URL=https://api.firecrawl.dev/v2
```

Behavior:

- `WEB_DATA_PROVIDER=auto` uses Firecrawl only when `FIRECRAWL_API_KEY` exists.
- `WEB_DATA_PROVIDER=local` disables external web data providers and keeps existing browser/static/user-evidence paths.
- `WEB_DATA_PROVIDER=firecrawl` requires `FIRECRAWL_API_KEY` and reports a clear blocked status when the token is missing.
- API keys are read from environment variables only and are never written into reports.

Commands:

```powershell
python scripts\web_data_provider.py --provider firecrawl --out-dir ".\promotion-output" scrape --url "https://example.com/product"
python scripts\web_data_provider.py --provider firecrawl --out-dir ".\promotion-output" search --query "site:youtube.com AI product launch" --limit 5
python scripts\web_data_provider.py --provider firecrawl --out-dir ".\promotion-output" map --url "https://example.com"
python scripts\web_data_provider.py --provider firecrawl --out-dir ".\promotion-output" crawl --url "https://example.com" --limit 50
```

Self-hosting note:

Firecrawl is heavier than the current license-service/hosted-worker backend. The inspected `docker-compose.yaml` sets the Playwright service around `2 CPU / 4G` and the API service around `4 CPU / 8G`. If self-hosted, run it as an isolated service or upgrade the server before enabling it. Do not casually place it in the same small process group as the Chrome extension license backend.

### AiToEarn-Inspired Platform Registry

Implemented:

- `scripts/platform_capabilities.py`
- `final_capability_audit.py` rows for `optional_firecrawl_web_data_backend` and `platform_registry_and_monetization_blueprint`

The registry separates:

- Create: copy, image, video, script, and asset generation
- Search: public/official/browser-visible/web-data evidence
- Publish: manual package, browser-assisted, official dry-run, official execution gate
- Engage: monitoring and reply drafts, with human confirmation for final actions
- Analytics: official/public/export/screenshot/business evidence
- Monetize: creator task, evidence submission, manual settlement ledger

Rejected from AiToEarn-style automation:

- `loginCookie` storage
- simulated login
- hidden browser token reuse
- private/unverified platform endpoints
- store-version auto-like, auto-follow, auto-comment, auto-DM, or final publish clicks

## Capability Mapping

| User goal | Current implementation |
| --- | --- |
| Create AI text/video/batch content | Existing copy/video/media pipeline plus publish packs. |
| Publish to multiple platforms and schedule | Publish queue, browser/manual payloads, official dry-run ports, local scheduler. Real writes still require official credentials and approval. |
| Engage through browser extension | Store-safe brand monitoring, evidence capture, AI reply drafts, and manual confirmation path. No final social side effects in the store-safe version. |
| Monetize creator campaigns | Blueprint-ready: campaigns, creator tasks, submissions, evidence items, payout ledger. Live marketplace and payouts are not implemented yet. |
| Search/Scrape/Crawl/Map/Batch Scrape | `web_data_provider.py` plus existing Playwright/static/user-evidence fallback. |
| Interact | Not enabled as autonomous platform operation. Future use must stay public, user-approved, and stop before login/captcha/risk/final publish actions. |
| Agent/MCP | Current Skill remains Codex-operated. Firecrawl MCP and AiToEarn MCP patterns are documented as future integration paths. |

## Firecrawl Interact Solution Boundary

Firecrawl-style Interact is useful only as a planning and public-evidence helper in this project. The safe implementation is:

- Generate an `interact-plan` with the target public URL, goal, allowed visible actions, blocked actions, and stop conditions.
- Allow public navigation actions such as open, scroll, wait, click visible non-mutating navigation, and extract visible text/screenshots.
- Stop before login, captcha, platform risk prompts, account verification, private analytics, final publish, like, follow, comment, or DM actions.
- Use `browser_publish_form_fill.py` or `browser_publish_session.py` only for user-visible field filling and screenshots, not final submission.

Command:

```powershell
python scripts\web_data_provider.py `
  --out-dir ".\promotion-output" `
  interact-plan `
  --url "https://example.com/public-page" `
  --goal "collect public launch evidence" `
  --action "scroll:bottom" `
  --action "click:Pricing" `
  --action "extract:visible text"
```

This is the replacement for unsafe "automated Interact publishing": it keeps Interact as an evidence-planning layer and leaves platform-account side effects to official APIs or manual user action.

## AiToEarn Relay Boundary

Relay-style architecture can be used temporarily for early integrations if the operator explicitly accepts the third-party trust boundary. It may help with task handoff, status tracking, and non-secret orchestration.

It must not become the open-source/commercial core safety promise:

- no opaque credential custody as the default deployment model
- no browser cookie/token relay
- no hidden private endpoint publishing
- no automatic like, follow, comment, or DM actions

Migration path:

- replace relay publishing with official platform APIs where available
- self-host auditable relay-like workers when a relay is still needed
- keep manual/browser-assisted publish packages for platforms without verified official creator publishing APIs

## Next Development Steps

1. Add Firecrawl credentials only if you want the optional public web data layer:

```env
WEB_DATA_PROVIDER=auto
FIRECRAWL_API_KEY=fc-...
FIRECRAWL_BASE_URL=https://api.firecrawl.dev/v2
```

2. Run a test product URL:

```powershell
python scripts\skill_entry.py `
  --link "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --out-dir ".\promotion-output"
```

3. Inspect the capability registry:

```powershell
python scripts\platform_capabilities.py --out-dir ".\promotion-output"
```

4. Refresh final readiness:

```powershell
python scripts\final_capability_audit.py --out-dir ".\promotion-output"
python scripts\final_capability_readiness.py --out-dir ".\promotion-output"
```

5. Build the creator marketplace only after the current Skill loop is stable:

- Add database tables for `campaigns`, `creator_tasks`, `submissions`, `evidence_items`, and `payout_ledger`.
- Start with manual review settlement.
- Connect Stripe/Connect or another payout provider only after legal, tax, and account onboarding requirements are defined.
