# Final Capability Map

This file maps the user's target requirements to the current Skill capability and the remaining external gates.

| Requirement | Current implementation | Remaining gate |
| --- | --- | --- |
| Search YouTube, Zhihu, Xiaohongshu, Douyin, GitHub for viral creators and videos | `platform_search_browser.py`, `platform_search_capture.py`, `viral_discovery_runner.py`, `multi_query_viral_discovery.py`, `browser_video_sampler.py`, and follow-up capture scripts | Platform access, browser-visible evidence, official APIs where available |
| Parse all product URLs after Codex reads pages | `browser_snapshot.py`, `product_url_discovery.py`, `product_url_reader.py`, `product_batch_runner.py`, `product_intake.py` | Playwright browser runtime for dynamic pages |
| Generate copy, review packs, and real video files | `promotion_manager.py`, `competitor_content_enhancer.py`, `render_video.py` | ffmpeg for MP4 output, optional voiceover file; `promotion_manager.py review|all` also writes a cheat-on-content bridge pack for Codex `cheat-score` |
| Auto-publish where possible, otherwise semi-auto | `publish_queue.py`, `publish_readiness_runner.py`, `launch_unlock_pack.py`, `publish_executor.py`, `youtube_oauth_publish.py`, `browser_publish_assistant.py`, `browser_publish_form_fill.py`, `browser_publish_session.py` | Credentials, app review, authorization, explicit `I_APPROVE_PUBLISH`, manual final publish for browser-assisted platforms |
| Recover real views, likes, comments, orders, revenue | `launch_unlock_pack.py`, `performance_monitor.py`, `real_evidence_inbox.py`, `published_items.py`, `publish_url_capture.py`, `post_publish_metrics_capture.py`, `comment_evidence_capture.py`, `business_attribution.py`, `metrics_recovery.py` | Real published URLs, official metrics credentials, screenshots, exports, business-system data |
| Self-evolve | `final_capability_audit.py`, `platform_access_audit.py`, `self_evolution_audit.py` | Only allowlisted runtime installs and approved Skill sync. No silent unreviewed self-replacement |
| Sync installed Codex Skill | `self_evolution_audit.py --sync-installed-skill --approval I_APPROVE_SKILL_SYNC` | Explicit approval and reviewed clean files |
| GitHub docs, intro, usage, install tutorial | `README.md` and `docs/*.md` | Keep docs updated with each capability change |
| Browser extension with subscription and ENHE traffic | `browser-extension/`, `browser-extension/billing-contract.json`, `scripts/billing_contract_simulator.py`, subscription docs, checkout/portal/license UI, usage credit reservation, hosted run payload/endpoint handoff, one-link run command, browser publish session command, launch unlock pack command, evidence inbox command, performance monitor command, readiness audit command, periodic automation config/run/Windows task commands | Production license API, payment-provider integration, hosted usage enforcement, usage commit, hosted worker fleet, and admin operations |

## Acceptance Command

```powershell
python scripts\final_capability_audit.py --out-dir ".\promotion-output"
python scripts\self_evolution_audit.py --out-dir ".\promotion-output"
python scripts\final_capability_readiness.py --out-dir ".\promotion-output"
```

The readiness status can remain partial when the blocker is external platform authorization or missing real metrics. That is expected and safer than fabricating readiness.

## Browser-Assisted Publish Session

When official publishing is unavailable or not authorized, run:

```powershell
python scripts\browser_publish_session.py `
  --publish-queue ".\promotion-output\reports\promotion-manager\publish-queue\publish-queue.json" `
  --run-form-fill `
  --out-dir ".\promotion-output"
```

The session prepares browser publish payloads, fills visible form fields where possible, writes screenshots and per-platform reports, and still requires the user to review and perform the final publish action. After publishing, use the generated URL registration or evidence inbox commands.

## Post-Publish Performance Monitor

After a real publishing round and URL registration, run:

```powershell
python scripts\performance_monitor.py `
  --out-dir ".\promotion-output"
```

The monitor captures public metrics, comments, optional business attribution, metrics recovery, next-round recommendations, and `reports/promotion-manager/performance-monitor/performance-monitor-history.jsonl`.

## Real Evidence Inbox

After a real publishing round, put exported evidence into `promotion-evidence-inbox` and run:

```powershell
python scripts\real_evidence_inbox.py `
  --inbox-dir ".\promotion-evidence-inbox" `
  --out-dir ".\promotion-output"
```

The runner accepts published URL lists, platform metric exports/snapshots, visible comment evidence, and order/revenue exports. It orchestrates the existing safe recovery scripts and writes `reports/promotion-manager/real-evidence-inbox/real-evidence-inbox.json`.

## Periodic Automation

The browser extension can generate the same scheduler commands operators would otherwise type manually:

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

```powershell
python scripts\automation_scheduler.py run --config ".\promotion-automation.json" --force
python scripts\automation_scheduler.py windows-task --config ".\promotion-automation.json" --out-file ".\register-enhe-promotion-task.ps1" --time "09:00"
```

Scheduled jobs still cannot bypass credentials, `I_APPROVE_PUBLISH`, login, captcha, risk checks, or final browser publish review.
