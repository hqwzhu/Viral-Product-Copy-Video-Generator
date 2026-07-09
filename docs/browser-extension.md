# Browser Extension

The `browser-extension` folder contains a Chrome Manifest V3 operator popup for ENHE Promotion Manager.

## What It Does

- Reads the active tab URL and title after the user opens the extension.
- Lets the operator select target platforms.
- Builds safe Codex commands for `scripts/skill_entry.py`, `scripts/browser_publish_session.py`, `scripts/real_evidence_inbox.py`, and `scripts/final_capability_readiness.py`.
- Shows whether the operator is running a one-link product cycle, a browser-assisted publishing session, a real evidence recovery pass, or a readiness audit.
- Lets the operator provide the output directory, publish queue path, publisher URL overrides, and evidence inbox path.
- Estimates token-backed subscription usage before the operator starts a hosted run.
- Stores a license key locally.
- Can validate the license against a configurable ENHE license endpoint when a backend is deployed.
- Opens the ENHE checkout URL with the selected plan and estimated monthly credits.
- Opens the ENHE customer billing portal.
- Links to ENHE website and project documentation for traffic.

## What It Does Not Do

- It does not execute Codex from the browser.
- It does not bypass platform login, captcha, review, or risk controls.
- It does not click final publish.
- It does not securely enforce payment by itself. A real paid launch needs a server-side license API and payment provider.

## Load Unpacked In Chrome

1. Open `chrome://extensions`.
2. Enable Developer mode.
3. Click Load unpacked.
4. Select the repository folder `browser-extension`.
5. Pin ENHE Promotion Manager in the toolbar.

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
- Real evidence inbox: imports published URLs, platform metrics, comments, orders, and revenue evidence from a local folder.
- Final readiness audit: refreshes the matrix that compares the current run against the requested final Agent scope.

## Subscription Flow

Chrome Web Store Payments is deprecated, so use a third-party payment provider and a backend license API for production.

Recommended flow:

1. User clicks Open checkout.
2. ENHE website handles checkout and account login.
3. Backend creates a license key with plan, quota, renewal date, and status.
4. Extension stores the license key in `chrome.storage.local`.
5. Extension calls the license API to check status and remaining credits.
6. Hosted API refuses runs that exceed credits.
7. Local Codex command generation remains free or trial-limited.

Customer self-service billing uses the Billing portal button. The extension opens:

```text
https://www.enhe-tech.com.cn/promotion-manager/billing?source=extension
```

The full server contract is in `docs/billing-backend-contract.md`; the extension copy is in `browser-extension/billing-contract.json`.

Default planned endpoint:

```text
https://www.enhe-tech.com.cn/api/promotion-manager/license
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

The simulator writes:

- `promotion-output\reports\promotion-manager\billing-simulator\billing-simulator.json`
- `promotion-output\reports\promotion-manager\billing-simulator\billing-simulator.md`
- `promotion-output\reports\promotion-manager\billing-simulator\billing-simulator-state.json`

The state file stores a license hash, subscription status, remaining credits, usage reservations, usage commits, and handled webhook event IDs. It does not store plaintext license keys or payment provider secrets.

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
