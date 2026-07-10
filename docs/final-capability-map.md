# Final Capability Map

This file maps the user's target requirements to the current Skill capability and the remaining external gates.

| Requirement | Current implementation | Remaining gate |
| --- | --- | --- |
| Search YouTube, Zhihu, Xiaohongshu, Douyin, GitHub for viral creators and videos | `platform_search_browser.py`, `platform_search_capture.py`, `viral_discovery_runner.py`, `multi_query_viral_discovery.py`, `viral_evidence_inbox_setup.py`, `viral_evidence_inbox.py`, `browser_video_sampler.py`, and follow-up capture scripts | Platform access, browser-visible evidence, official APIs where available; user-filled inbox fallback when automation is blocked |
| Parse all product URLs after Codex reads pages | `browser_snapshot.py`, `product_url_discovery.py`, `product_url_reader.py`, `product_batch_runner.py`, `product_intake.py` | Playwright browser runtime for dynamic pages; public web-text fallback when local browser/static fetch fails |
| Generate complete publish packages with viral titles, copy, tags, first-batch comments, videos, covers, and detail images | `promotion_manager.py`, `competitor_content_enhancer.py`, `render_video.py`, `media_asset_pack.py` | ffmpeg for MP4 output, Pillow for PNG cover/detail generation, optional voiceover file; `promotion_manager.py review|all` also writes a cheat-on-content bridge pack for Codex `cheat-score` |
| Generate publish packages first; keep auto-publish ports reserved | Current policy: manual publish packages are the primary path; auto-publish ports are reserved for later official API-only upgrades. `publish_queue.py`, `publish_readiness_runner.py`, `launch_unlock_pack.py`, `browser_publish_assistant.py`, `browser_publish_form_fill.py`, and `browser_publish_session.py` are the default path. `publish_executor.py` and `youtube_oauth_publish.py` remain dry-run-first official API ports for GitHub, YouTube, and Douyin. | Manual final publish or visible browser review is still required by default. Future auto-publish execution requires official credentials, app review, account authorization, explicit `I_APPROVE_PUBLISH`, and `PUBLISH_DRY_RUN=false`. |
| Recover real views, likes, comments, orders, revenue | `launch_unlock_pack.py`, `real_evidence_inbox_setup.py`, `performance_monitor.py`, `real_evidence_inbox.py`, `published_items.py`, `publish_url_capture.py`, `post_publish_metrics_capture.py`, `comment_evidence_capture.py`, `business_attribution.py`, `metrics_recovery.py` | Real published URLs, official metrics credentials, screenshots, exports, business-system data |
| Self-evolve | `final_capability_audit.py`, `platform_access_audit.py`, `self_evolution_audit.py` | Only allowlisted runtime installs and approved Skill sync. No silent unreviewed self-replacement |
| Sync installed Codex Skill | `self_evolution_audit.py --sync-installed-skill --approval I_APPROVE_SKILL_SYNC` | Explicit approval and reviewed clean files |
| GitHub docs, intro, usage, install tutorial | `README.md` and `docs/*.md` | Keep docs updated with each capability change |
| Browser extension with subscription, store package, and ENHE traffic | `browser-extension/`, packaged icons, `scripts/package_browser_extension.py`, `docs/extension-store-submission.md`, `docs/store/*.md`, `docs/legal/*.md`, `browser-extension/billing-contract.json`, `scripts/billing_contract_simulator.py`, `backend/license-service/`, PostgreSQL state backend, checkout/portal/license UI, usage credit reservation, hosted run queue/status endpoints, isolated hosted worker, one-link run command, browser publish session command, launch unlock pack command, evidence inbox setup/import commands, performance monitor command, readiness audit command, periodic automation config/run/Windows task commands, and `deploy/promotion-manager/` same-host HTTPS deployment files | User must create/register external accounts, configure Stripe live prices/webhooks, deploy to the HTTPS server, publish policy pages, prepare screenshots, and pass Chrome/Edge store review. If the current server is below 2 vCPU/4 GB RAM, upgrade before enabling hosted worker execution. |
| Phase progress reporting | `real_run_playbook.py`, `skill_entry.py`, `final_capability_runner.py`, `final_capability_readiness.py` | Estimates can change when platform review, account authorization, publishing, or real metric exports are delayed |

## Acceptance Command

```powershell
python scripts\final_capability_audit.py --out-dir ".\promotion-output"
python scripts\self_evolution_audit.py --out-dir ".\promotion-output"
python scripts\final_capability_readiness.py --out-dir ".\promotion-output"
```

The readiness status can remain partial when the blocker is external platform authorization or missing real metrics. That is expected and safer than fabricating readiness.

When a video-platform evidence gap is caused by dynamic public search pages timing out on `networkidle`, rerun the capture with bounded browser search waits:

```powershell
python scripts\final_capability_runner.py `
  --url "https://www.enhe-tech.com.cn/software/windows-ai" `
  --platforms douyin,xiaohongshu `
  --run-follow-up-captures `
  --capture-browser-assisted-follow-ups `
  --sample-video-frames `
  --timeout-ms 15000 `
  --wait-until domcontentloaded `
  --multi-query-browser-search-timeout-ms 15000 `
  --multi-query-browser-search-wait-until domcontentloaded `
  --multi-query-run-follow-up-captures `
  --multi-query-capture-browser-assisted-follow-ups `
  --multi-query-sample-video-frames `
  --out-dir ".\promotion-output\enhe-video-evidence-rerun"
```

When risk-controlled platforms still do not expose enough public/browser-visible competitor evidence, create and import a viral evidence inbox:

```powershell
python scripts\viral_evidence_inbox_setup.py `
  --product-url "https://www.enhe-tech.com.cn/software/windows-ai" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --inbox-dir ".\viral-evidence-inbox" `
  --out-dir ".\promotion-output"

python scripts\viral_evidence_inbox.py `
  --inbox-dir ".\viral-evidence-inbox" `
  --out-dir ".\promotion-output"
```

This fallback accepts real competitor URLs, visible page text, transcripts, exports, or screenshot OCR text. It does not create fake creators or metrics; screenshot files alone stay marked as `manual_text_required`.

## Phase Progress Reporting

After every major stage, report:

- Current stage
- Completed goals
- Unfinished goals
- Next plan
- Estimated remaining time

`final_capability_readiness.py` writes `phase_progress_reporting` into the JSON and Markdown readiness matrix so the operator can compare local progress against the full requested goal.

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

Before or after a real publishing round, initialize the inbox:

```powershell
python scripts\real_evidence_inbox_setup.py `
  --product-url "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --inbox-dir ".\promotion-evidence-inbox" `
  --out-dir ".\promotion-output"
```

Then put exported evidence into `promotion-evidence-inbox` and run:

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
