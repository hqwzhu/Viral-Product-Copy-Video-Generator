# Output Schema

The script writes JSON and Markdown reports under the selected output directory.

## Files

- `platform-publish-capability-map.json`
- `platform-publish-capability-map.md`
- `content-plan.json`
- `content-plan.md`
- `platform-content.json`
- `platform-content.md`
- `content-review.json`
- `content-review.md`
- `publish-pack.json`
- `publish-pack.md`
- `publish-result-input.json`
- `publish-result-input.md`
- `retrospective.json`
- `retrospective.md`

## Publish Modes

- `official_api_publish`
- `browser_assisted_publish`
- `manual_publish_required`
- `unsupported`

## Result Data Rule

All metrics default to `null`. The user must fill real values and evidence. Retrospectives without real data must stay `waiting_real_data`.

