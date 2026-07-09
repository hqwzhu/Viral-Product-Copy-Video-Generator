# Usage

中文版本: [docs/zh-CN/usage.md](zh-CN/usage.md)

## One Product URL

```powershell
python scripts\skill_entry.py `
  --link "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --out-dir ".\promotion-output"
```

The entry script builds a real-run playbook, runs the final capability runner, and writes a readiness matrix. After each major stage, use `reports\promotion-manager\final-readiness\final-capability-readiness.md` as the phase progress report: current stage, completed goals, unfinished goals, next plan, and estimated remaining time.

For direct URL reading, `product_url_reader.py` tries browser structured capture first, then static HTML, then public web-text fallback for public pages that time out locally. Disable the third-party text fallback with `--disable-web-text-fallback`, or use `--web-text-fallback-file` when Codex has already saved page text.

## Website URL With Product Discovery

```powershell
python scripts\skill_entry.py `
  --link "https://example.com" `
  --link-mode site `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --discovery-top-n 25 `
  --out-dir ".\promotion-output"
```

Use this for an AI tools directory, SaaS website, ecommerce site, or docs site where the Skill should discover candidate product pages first.

## Competitor And Viral Research

```powershell
python scripts\multi_query_viral_discovery.py `
  --workflow-manifest ".\promotion-output\reports\promotion-manager\agent-run\workflow-manifest.json" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --top-n 20 `
  --out-dir ".\promotion-output"
```

The Skill ranks public or browser-visible materials. It does not scrape private endpoints or hidden media tokens.

If risk-controlled platforms do not expose enough stable public search evidence, create a fillable viral evidence inbox:

```powershell
python scripts\viral_evidence_inbox_setup.py `
  --product-url "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --inbox-dir ".\viral-evidence-inbox" `
  --out-dir ".\promotion-output"
```

Then add real competitor URLs, visible text, transcripts, exports, or screenshot OCR text and import them:

```powershell
python scripts\viral_evidence_inbox.py `
  --inbox-dir ".\viral-evidence-inbox" `
  --out-dir ".\promotion-output"
```

The inbox runner writes platform `captured-search-results-*.json` reports, rebuilds the viral content library, and rebuilds the creator leaderboard. It keeps screenshots as `manual_text_required` until OCR or copied text is provided.

## Content And Video

```powershell
python scripts\render_video.py `
  --content-json ".\promotion-output\reports\promotion-manager\generated-content\product-platform-content.json" `
  --platform douyin `
  --out ".\promotion-output\videos\product-douyin.mp4"
```

Optional voiceover:

```powershell
python scripts\render_video.py `
  --content-json ".\promotion-output\reports\promotion-manager\generated-content\product-platform-content.json" `
  --platform youtube `
  --voiceover-audio ".\voiceover.wav" `
  --out ".\promotion-output\videos\product-youtube.mp4"
```

Review packs:

```powershell
python scripts\promotion_manager.py review `
  --product-name "Product" `
  --product-url "https://example.com/product" `
  --audience "creators, founders" `
  --value-proposition "Turns product pages into launch content" `
  --out-dir ".\promotion-output"
```

The review step writes `reports\promotion-manager\cheat-review\*-cheat-review-pack.json` and one draft per platform for Codex `cheat-score`. These are review inputs only; prediction logs are created only when you explicitly start a cheat-on-content prediction cycle.

## Publishing

Build the guarded queue:

```powershell
python scripts\publish_readiness_runner.py `
  --workflow-manifest ".\promotion-output\reports\promotion-manager\agent-run\workflow-manifest.json" `
  --build-queue `
  --github-repo owner/repo `
  --youtube-video-file ".\promotion-output\videos\product-youtube.mp4" `
  --out-dir ".\promotion-output"
```

Prepare browser/manual payloads:

```powershell
python scripts\browser_publish_assistant.py `
  --publish-queue ".\promotion-output\reports\promotion-manager\publish-queue\publish-queue.json" `
  --out-dir ".\promotion-output"
```

Build one launch unlock pack for platform access, publish setup, browser-assisted publishing, and real evidence collection:

```powershell
python scripts\launch_unlock_pack.py `
  --publish-queue ".\promotion-output\reports\promotion-manager\publish-queue\publish-queue.json" `
  --publish-readiness ".\promotion-output\reports\promotion-manager\publish-readiness\publish-readiness.json" `
  --out-dir ".\promotion-output"
```

The unlock pack writes `reports/promotion-manager/launch-unlock/launch-unlock.json`, a checklist, and copy-ready next commands. It records only credential variable names and setup status, never secret values.

The final capability runner creates the same pack automatically for each product run when a publish queue exists. Pass `--platform-publish-url platform=url` to preserve browser-assisted publisher entry URLs inside the pack.

Run a browser-assisted publish session. This prepares payloads, optionally fills visible fields, writes screenshots, and stops before the final publish action:

```powershell
python scripts\browser_publish_session.py `
  --publish-queue ".\promotion-output\reports\promotion-manager\publish-queue\publish-queue.json" `
  --platform-publish-url "xiaohongshu=https://creator.xiaohongshu.com/" `
  --run-form-fill `
  --out-dir ".\promotion-output"
```

Official publishing only runs when credentials, targets, and approval are present:

```powershell
python scripts\publish_executor.py `
  --platform github `
  --github-action file `
  --github-repo owner/repo `
  --path PROMOTION.md `
  --content-file ".\promotion-output\reports\promotion-manager\generated-content\product-platform-content.md" `
  --execute `
  --approval I_APPROVE_PUBLISH `
  --out-dir ".\promotion-output"
```

## Periodic Automation

Create a recurring local job:

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

Run due jobs manually or generate a Windows Task Scheduler registration script:

```powershell
python scripts\automation_scheduler.py run --config ".\promotion-automation.json" --force
python scripts\automation_scheduler.py windows-task --config ".\promotion-automation.json" --out-file ".\register-enhe-promotion-task.ps1" --time "09:00"
```

Scheduled jobs can prepare content, MP4s, publish queues, browser-assisted publish payloads, evidence recovery, and next-round optimization. They still cannot bypass credentials, platform review, `I_APPROVE_PUBLISH`, login, captcha, risk checks, or final browser publish review.

## Dynamic Search Pages

Some platform search pages keep network connections open and can time out if Playwright waits for `networkidle`. For Douyin, Xiaohongshu, or similar public search pages, use a bounded `domcontentloaded` wait in the multi-query discovery stage:

```powershell
python scripts\final_capability_runner.py `
  --url "https://example.com/product" `
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
  --out-dir ".\promotion-output"
```

## Metrics And Next Round

Register a real published URL:

```powershell
python scripts\published_items.py `
  --platform xiaohongshu `
  --published-url "https://www.xiaohongshu.com/explore/real-note-id" `
  --evidence ".\screenshots\xhs-published.png" `
  --out-dir ".\promotion-output"
```

Run the post-publish monitor after real URLs are registered:

```powershell
python scripts\performance_monitor.py --out-dir ".\promotion-output"
```

The monitor captures public/browser-visible metrics, visible comments and demand signals, optional business exports, metrics recovery, next-round optimization, and a history file. For manual step-by-step recovery:

```powershell
python scripts\post_publish_metrics_capture.py --out-dir ".\promotion-output"
python scripts\metrics_recovery.py `
  --metrics-json ".\promotion-output\reports\promotion-manager\post-publish-capture\post-publish-metrics-export.json" `
  --business-csv ".\orders-and-revenue.csv" `
  --out-dir ".\promotion-output"
```

Create a fillable evidence inbox before or after publishing:

```powershell
python scripts\real_evidence_inbox_setup.py `
  --product-url "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --inbox-dir ".\promotion-evidence-inbox" `
  --out-dir ".\promotion-output"
```

Then recover a full local evidence inbox:

```powershell
python scripts\real_evidence_inbox.py `
  --inbox-dir ".\promotion-evidence-inbox" `
  --out-dir ".\promotion-output"
```

The setup command writes `inbox-manifest.json`, `published-urls.csv`, `metrics.csv`, `comments.txt`, `orders.csv`, `structured-metrics-snapshot.example.json`, `README.md`, and an import command file. The inbox runner accepts exported or copied evidence such as `published-urls.csv`, `metrics.csv`, `metrics.xlsx`, `comments.txt`, `comments.html`, `orders.csv`, `orders.xlsx`, and JSON/text variants. It registers published URLs, imports metrics, captures comments, attributes orders/revenue, runs metrics recovery, and then runs `next_round_optimizer.py`. Use `--skip-post-publish-capture` when the inbox already contains platform metric exports and you do not want public URL fetch attempts.

To validate the recovery and next-round loop before real data exists, generate synthetic/demo evidence:

```powershell
python scripts\synthetic_evidence_generator.py `
  --product-url "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --run-recovery `
  --out-dir ".\promotion-output\synthetic-validation"
```

The synthetic inbox and report are marked `SYNTHETIC_DEMO_DATA_DO_NOT_REPORT`. Use them only to validate local wiring; replace them with real published URLs, platform exports, comments, and business exports before any live retrospective.

Optimize the next round:

```powershell
python scripts\next_round_optimizer.py `
  --metrics-recovery-json ".\promotion-output\reports\promotion-manager\metrics-recovery\metrics-recovery.json" `
  --comment-evidence-json ".\promotion-output\reports\promotion-manager\comment-evidence\comment-evidence-export.json" `
  --business-attribution-json ".\promotion-output\reports\promotion-manager\business-attribution\business-attribution.json" `
  --out-dir ".\promotion-output"
```

If no real metrics or business evidence exists, the optimizer outputs `waiting_real_data`.
