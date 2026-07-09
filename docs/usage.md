# Usage

## One Product URL

```powershell
python scripts\skill_entry.py `
  --link "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --out-dir ".\promotion-output"
```

The entry script builds a real-run playbook, runs the final capability runner, and writes a readiness matrix.

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

## Metrics And Next Round

Register a real published URL:

```powershell
python scripts\published_items.py `
  --platform xiaohongshu `
  --published-url "https://www.xiaohongshu.com/explore/real-note-id" `
  --evidence ".\screenshots\xhs-published.png" `
  --out-dir ".\promotion-output"
```

Recover public or browser-visible metrics:

```powershell
python scripts\post_publish_metrics_capture.py --out-dir ".\promotion-output"
python scripts\metrics_recovery.py `
  --metrics-json ".\promotion-output\reports\promotion-manager\post-publish-capture\post-publish-metrics-export.json" `
  --business-csv ".\orders-and-revenue.csv" `
  --out-dir ".\promotion-output"
```

Or recover a full local evidence inbox:

```powershell
python scripts\real_evidence_inbox.py `
  --inbox-dir ".\promotion-evidence-inbox" `
  --out-dir ".\promotion-output"
```

The inbox runner accepts exported or copied evidence such as `published-urls.csv`, `metrics.csv`, `metrics.xlsx`, `comments.txt`, `comments.html`, `orders.csv`, `orders.xlsx`, and JSON/text variants. It registers published URLs, imports metrics, captures comments, attributes orders/revenue, runs metrics recovery, and then runs `next_round_optimizer.py`. Use `--skip-post-publish-capture` when the inbox already contains platform metric exports and you do not want public URL fetch attempts.

Optimize the next round:

```powershell
python scripts\next_round_optimizer.py `
  --metrics-recovery-json ".\promotion-output\reports\promotion-manager\metrics-recovery\metrics-recovery.json" `
  --comment-evidence-json ".\promotion-output\reports\promotion-manager\comment-evidence\comment-evidence-export.json" `
  --business-attribution-json ".\promotion-output\reports\promotion-manager\business-attribution\business-attribution.json" `
  --out-dir ".\promotion-output"
```

If no real metrics or business evidence exists, the optimizer outputs `waiting_real_data`.
