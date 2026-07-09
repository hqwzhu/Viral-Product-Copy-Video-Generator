# Final Capability Map

This file maps the user's target requirements to the current Skill capability and the remaining external gates.

| Requirement | Current implementation | Remaining gate |
| --- | --- | --- |
| Search YouTube, Zhihu, Xiaohongshu, Douyin, GitHub for viral creators and videos | `platform_search_browser.py`, `platform_search_capture.py`, `viral_discovery_runner.py`, `multi_query_viral_discovery.py`, `browser_video_sampler.py`, and follow-up capture scripts | Platform access, browser-visible evidence, official APIs where available |
| Parse all product URLs after Codex reads pages | `browser_snapshot.py`, `product_url_discovery.py`, `product_url_reader.py`, `product_batch_runner.py`, `product_intake.py` | Playwright browser runtime for dynamic pages |
| Generate copy and real video files | `promotion_manager.py`, `competitor_content_enhancer.py`, `render_video.py` | ffmpeg for MP4 output, optional voiceover file |
| Auto-publish where possible, otherwise semi-auto | `publish_queue.py`, `publish_readiness_runner.py`, `publish_executor.py`, `youtube_oauth_publish.py`, `browser_publish_assistant.py`, `browser_publish_form_fill.py` | Credentials, app review, authorization, explicit `I_APPROVE_PUBLISH`, manual final publish for browser-assisted platforms |
| Recover real views, likes, comments, orders, revenue | `published_items.py`, `publish_url_capture.py`, `post_publish_metrics_capture.py`, `comment_evidence_capture.py`, `business_attribution.py`, `metrics_recovery.py` | Real published URLs, official metrics credentials, screenshots, exports, business-system data |
| Self-evolve | `final_capability_audit.py`, `platform_access_audit.py`, `self_evolution_audit.py` | Only allowlisted runtime installs and approved Skill sync. No silent unreviewed self-replacement |
| Sync installed Codex Skill | `self_evolution_audit.py --sync-installed-skill --approval I_APPROVE_SKILL_SYNC` | Explicit approval and reviewed clean files |
| GitHub docs, intro, usage, install tutorial | `README.md` and `docs/*.md` | Keep docs updated with each capability change |
| Browser extension with subscription and ENHE traffic | `browser-extension/` plus subscription docs | Production license API and payment backend |

## Acceptance Command

```powershell
python scripts\final_capability_audit.py --out-dir ".\promotion-output"
python scripts\self_evolution_audit.py --out-dir ".\promotion-output"
python scripts\final_capability_readiness.py --out-dir ".\promotion-output"
```

The readiness status can remain partial when the blocker is external platform authorization or missing real metrics. That is expected and safer than fabricating readiness.
