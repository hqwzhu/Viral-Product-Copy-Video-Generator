# Output Schema

The script writes JSON and Markdown reports under the selected output directory.

## Docs

- `docs/promotion-manager/01-platform-publishing-feasibility.md`
- `docs/promotion-manager/02-github-reference-projects.md`
- `docs/promotion-manager/03-platform-risk-matrix.md`
- `docs/promotion-manager/04-self-learning-notes.md`
- `docs/promotion-manager/05-browser-extension-roadmap.md`
- `docs/promotion-manager/06-saas-product-roadmap.md`

## Reports

- `promotion-output/intake/product-profile.{json,md}` when `scripts/product_intake.py` is run from URL, HTML, rendered text, or structured snapshot input
- `reports/promotion-manager/agent-run/workflow-manifest.{json,md}` when `scripts/run_promotion_workflow.py` is run
- `reports/promotion-manager/agent-run/competitor-collections/<platform>/...` when the workflow runner calls official/public competitor collectors
- `reports/promotion-manager/competitors/competitor-discovery.{json,md}` when `scripts/competitor_discovery.py` is run
- `reports/promotion-manager/competitors/auto-collected-competitors.{json,md}` when `scripts/competitor_collector.py` is run
- `reports/promotion-manager/competitors/imported-competitors.{json,md}` when `scripts/competitor_intake.py` is run
- `reports/promotion-manager/research/platform-publishing-feasibility.{json,md}`
- `reports/promotion-manager/research/github-reference-projects.{json,md}`
- `reports/promotion-manager/research/platform-risk-matrix.{json,md}`
- `reports/promotion-manager/research/self-learning-notes.{json,md}`
- `reports/promotion-manager/competitors/<product>-deconstruction.{json,md}`
- `reports/promotion-manager/content-plans/<product>-content-plan.{json,md}`
- `reports/promotion-manager/generated-content/<product>-platform-content.{json,md}`
- `reports/promotion-manager/generated-content/<product>-content-review.{json,md}`
- `reports/promotion-manager/publish-packs/<product>-publish-pack.{json,md}`
- `reports/promotion-manager/publish-packs/platform-publish-capability-map.{json,md}`
- `reports/promotion-manager/publish-results/<product>-publish-result-input.{json,md}`
- `reports/promotion-manager/publish-results/publish-execution.{json,md}` when `scripts/publish_executor.py` is run
- `reports/promotion-manager/publish-results/youtube-oauth-publish.{json,md}` when `scripts/youtube_oauth_publish.py` is run
- `reports/promotion-manager/metrics/imported-metrics.{json,md}` when `scripts/metrics_intake.py` is run
- `reports/promotion-manager/retrospectives/<product>-retrospective.{json,md}`
- `videos/<product>-<platform>.mp4` and matching `.json` metadata when `scripts/render_video.py` is run; metadata includes `audioMode` as `silent`, `file`, or `windows_sapi`

## Workflow Manifest

`workflow-manifest.json` is the run ledger for Codex operation. It includes:

- `product`: normalized product fields used by generation scripts
- `input`: source type, confidence, and whether rendered snapshots are supported
- `artifacts`: important output paths
- `competitorDiscovery`: search task status and official collection summaries
- `videoGeneration`: MP4 status and paths per video platform
- `publishAutomation`: platform publish mode, approval requirement, and automation status
- `metricsRecovery`: real-data recovery status and imported record count
- `selfEvolution`: controlled learning/upgrade capability status
- `guardrails`: safety rules for the run
- `steps`: command ledger with sanitized command arguments and output tails

## Publish Modes

- `official_api_publish`
- `browser_assisted_publish`
- `manual_publish_required`
- `unsupported`

## Result Data Rule

All metrics default to `null`. The user must fill real values and evidence. Retrospectives without real data must stay `waiting_real_data`.
