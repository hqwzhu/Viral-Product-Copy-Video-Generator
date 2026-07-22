# Browser Extension

The `browser-extension` folder contains a Chrome Manifest V3 operator popup for ENHE Product Promo Maker.

Version 0.5.4 is the source/release candidate and provides a complete Chinese/English popup. On first launch it follows Chrome's UI language, then remembers the operator's explicit `中文 / EN` selection in local extension storage. Store metadata is also localized through Chrome `_locales` resources. Chrome Web Store v0.5.3 remains published; v0.5.4 has not yet been submitted for review.

## What It Does

- Reads the active tab URL and title after the user opens the extension.
- Lets the operator select target platforms.
- Builds safe Codex commands for `scripts/skill_entry.py`, `scripts/browser_publish_session.py`, `scripts/launch_unlock_pack.py`, `scripts/real_evidence_inbox_setup.py`, `scripts/real_evidence_inbox.py`, `scripts/performance_monitor.py`, `scripts/final_capability_readiness.py`, and `scripts/automation_scheduler.py`.
- Shows whether the operator is running a one-link product cycle, a browser-assisted publishing session, a real evidence recovery pass, or a readiness audit.
- Lets the operator provide the output directory, publish queue path, publisher URL overrides, evidence inbox path, automation config path, scheduler output root, job ID, interval, and Windows Task Scheduler script settings.
- Estimates token-backed subscription usage before the operator starts a hosted run.
- Stores a license key locally.
- Can validate the license against a configurable ENHE license endpoint when a backend is deployed.
- Can reserve hosted usage credits against the ENHE usage authorization endpoint before a hosted run.
- Can copy or submit a hosted run payload with the product URL, platforms, workflow type, estimated credits, local command, selected options, and safety constraints.
- Shows the hosted run ID and status URL returned by the backend after queue submission.
- Opens the ENHE checkout URL with the selected plan and estimated monthly credits.
- Opens the ENHE customer billing portal.
- Links to ENHE website and project documentation for traffic.
- Uses ENHE-branded text-free 16/48 px toolbar icons and a 128 px store icon optimized for Chrome's required transparent safe area.

## What It Does Not Do

- It does not execute Codex from the browser.
- It does not send arbitrary local commands for server execution. The hosted worker rebuilds commands from whitelisted structured payload fields.
- It does not bypass platform login, captcha, review, or risk controls.
- It does not click final publish.
- It does not securely enforce payment by itself. A real paid launch needs a server-side license API and payment provider.

## Load Unpacked In Chrome

1. Open `chrome://extensions`.
2. Enable Developer mode.
3. Click Load unpacked.
4. Select the repository folder `browser-extension`.
5. Pin ENHE Product Promo Maker in the toolbar.

## Build Store Submission Package

Build a Chrome/Edge submission zip from the repository root:

```powershell
python scripts\package_browser_extension.py --out-dir ".\dist\v0.5.4"
```

The command writes:

- `dist\v0.5.4\enhe-promotion-manager-0.5.4.zip`
- `dist\v0.5.4\browser-extension-package-report.json`
- `dist\v0.5.4\browser-extension-package-report.md`

Only submit the v0.5.4 zip when `dist\v0.5.4\browser-extension-package-report.json` reports `status: ready`; this task does not submit it. The package check verifies MV3, bundled icons, local popup code, scoped permissions, and no remote code execution patterns.

For Chrome Web Store and Microsoft Edge Add-ons listing steps, reviewer notes, privacy policy fields, and paid-subscription wording, see `docs/extension-store-submission.md`.

## Operator Flow

1. Open a product page in Chrome.
2. Click the extension.
3. Click Use current tab.
4. Select platforms, workflow depth, and command type.
5. Generate command.
6. Copy the command.
7. Run it from the repository root in Codex or PowerShell.

Command types:

- One-link Skill run: reads the product URL, runs research, content generation, publish-pack setup, and readiness refresh.
- Browser publish session: reads a generated `publish-queue.json`, prepares browser/manual publish payloads, optionally fills visible fields, and stops before final publish.
- Launch unlock pack: reads a generated `publish-queue.json`, combines platform access audit, publish setup, browser-assisted publish payloads, and real-evidence templates into one launch checklist. Publisher URL overrides from the popup are passed through as `--platform-publish-url`.
- Evidence inbox setup: creates `published-urls.csv`, `metrics.csv`, `comments.txt`, `orders.csv`, `inbox-manifest.json`, and import commands before or immediately after publishing.
- Real evidence inbox: imports published URLs, platform metrics, comments, orders, and revenue evidence from a local folder.
- Performance monitor: reruns post-publish public metrics capture, visible comment capture, optional business attribution, metrics recovery, next-round optimization, and history snapshots from registered published URLs.
- Final readiness audit: refreshes the matrix that compares the current run against the requested final Agent scope.
- Schedule init: writes a `promotion-automation.json` job that can run recurring product promotion cycles with competitor search, follow-up capture, publish queue preparation, browser-assisted publish payloads, metrics recovery, and next-round optimization toggles.
- Run scheduled jobs: runs due automation jobs from the selected config, optionally forced by the generated command.
- Windows task script: writes a PowerShell script that registers `automation_scheduler.py run` with Windows Task Scheduler.

The automation commands still honor the same safety gates. They can prepare queues, browser payloads, screenshots, evidence requests, and next-round reports, but official writes still need credentials and `I_APPROVE_PUBLISH`, and browser-assisted flows still stop before final publish.

## Subscription Flow

Chrome Web Store Payments is deprecated, so use a third-party payment provider and a backend license API for production.

Recommended flow:

1. User clicks Open checkout.
2. ENHE website handles checkout and account login.
3. Backend creates a license key with plan, quota, renewal date, and status.
4. Extension stores the license key in `chrome.storage.local`.
5. Extension calls the license API to check status and remaining credits.
6. Extension can call the usage authorization API to reserve credits for the selected workflow.
7. Extension copies or posts a hosted run payload to the ENHE hosted run API.
8. Hosted API refuses runs without an active license and matching usage reservation, then queues accepted runs.
9. The isolated hosted worker consumes queued runs, writes artifacts under a server-owned hosted-run directory, updates run status, and commits actual usage after completion.
10. Local Codex command generation remains free or trial-limited.

Customer self-service billing uses the Billing portal button. The extension opens:

```text
https://www.enhe-tech.com.cn/promotion-manager/billing?source=extension
```

The full server contract is in `docs/billing-backend-contract.md`; the extension copy is in `browser-extension/billing-contract.json`.

Default planned endpoint:

```text
https://www.enhe-tech.com.cn/api/promotion-manager/license
```

Default usage authorization endpoint:

```text
https://www.enhe-tech.com.cn/api/promotion-manager/usage/authorize
```

Default hosted run endpoint:

```text
https://www.enhe-tech.com.cn/api/promotion-manager/run
```

Default hosted run status endpoint:

```text
https://www.enhe-tech.com.cn/api/promotion-manager/run/{runId}
```

Expected response:

```json
{
  "active": true,
  "plan": "Growth",
  "creditsRemaining": 120,
  "renewsAt": "2026-08-09"
}
```

## Reference Simulator

Before deploying a real payment backend, run the local contract simulator to verify the license, quota, usage, and webhook flow:

```powershell
python scripts\billing_contract_simulator.py demo `
  --plan growth `
  --workflow-type research_run `
  --out-dir ".\promotion-output"
```

Use `--workflow-type automation_due_run` to validate the scheduled-run credit path:

```powershell
python scripts\billing_contract_simulator.py demo `
  --plan growth `
  --workflow-type automation_due_run `
  --out-dir ".\promotion-output"
```

Use `demo-hosted-run` to validate the extension's hosted payload handoff after usage reservation:

```powershell
python scripts\billing_contract_simulator.py demo-hosted-run `
  --plan growth `
  --workflow-type standard_run `
  --product-url "https://example.com/product" `
  --out-dir ".\promotion-output"
```

The simulator writes:

- `promotion-output\reports\promotion-manager\billing-simulator\billing-simulator.json`
- `promotion-output\reports\promotion-manager\billing-simulator\billing-simulator.md`
- `promotion-output\reports\promotion-manager\billing-simulator\billing-simulator-state.json`

The state file stores a license hash, subscription status, remaining credits, usage reservations, hosted run records, usage commits, and handled webhook event IDs. It does not store plaintext license keys or payment provider secrets.

The extension's Reserve credits button sends the selected workflow type, estimated credits, and an idempotency key to the usage authorization endpoint. The Copy hosted payload and Start hosted run buttons then package the active product URL, selected platforms, command type, workflow depth, local Codex command, options, usage ID, and explicit safety flags for the hosted run endpoint. Production hosted runs should commit actual usage server-side after completion; local Codex command generation does not need a hosted usage reservation.

## Production Deployment

Deploy `backend/license-service/` behind the same HTTPS host as the ENHE website, isolated under `/api/promotion-manager/` and `/promotion-manager/runs/`. Use `deploy/promotion-manager/` for Nginx, systemd, PostgreSQL, and worker configuration. Start with API-only deployment if the server is small; enable the hosted worker only after Stripe test mode, license validation, usage reservation, and run status checks pass.

## Security Notes

The extension follows MV3 constraints:

- `manifest_version` is 3.
- Extension pages use `script-src 'self'`.
- JavaScript and CSS are bundled inside the extension.
- Remote services are used for data only, not remote code.
- No API secrets are stored in the extension.
- Payment provider secret keys, webhook signing secrets, price IDs, and usage-ledger writes stay on the backend.

Google's Manifest V3 docs require extension logic to be part of the extension package and not remotely hosted. The implementation keeps local code in `popup.js` and `popup.css`.

## Developer Info

- Developer: ENHE AI
- Website: https://www.enhe-tech.com.cn/
- Product page: https://www.enhe-tech.com.cn/promotion-manager
- Repository: https://github.com/hqwzhu/Viral-Product-Copy-Video-Generator.git
