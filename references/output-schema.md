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

- `promotion-output/intake/product-profile.{json,md}` when `scripts/product_intake.py` is run
- `reports/promotion-manager/competitors/competitor-discovery.{json,md}` when `scripts/competitor_discovery.py` is run
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
- `reports/promotion-manager/metrics/imported-metrics.{json,md}` when `scripts/metrics_intake.py` is run
- `reports/promotion-manager/retrospectives/<product>-retrospective.{json,md}`
- `videos/<product>-<platform>.mp4` and matching `.json` metadata when `scripts/render_video.py` is run

## Publish Modes

- `official_api_publish`
- `browser_assisted_publish`
- `manual_publish_required`
- `unsupported`

## Result Data Rule

All metrics default to `null`. The user must fill real values and evidence. Retrospectives without real data must stay `waiting_real_data`.
