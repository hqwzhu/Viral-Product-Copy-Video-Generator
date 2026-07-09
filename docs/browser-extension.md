# Browser Extension

The `browser-extension` folder contains a Chrome Manifest V3 operator popup for ENHE Promotion Manager.

## What It Does

- Reads the active tab URL and title after the user opens the extension.
- Lets the operator select target platforms.
- Builds a safe Codex command for `scripts/skill_entry.py`.
- Shows whether the run will create a playbook only, a full workflow, or a full workflow with browser-assisted follow-up.
- Estimates token-backed subscription usage before the operator starts a hosted run.
- Stores a license key locally.
- Can validate the license against a configurable ENHE license endpoint when a backend is deployed.
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
4. Select platforms and workflow depth.
5. Generate command.
6. Copy the command.
7. Run it from the repository root in Codex or PowerShell.

## Subscription Flow

Chrome Web Store Payments is deprecated, so use a third-party payment provider and a backend license API for production.

Recommended flow:

1. User clicks Manage subscription.
2. ENHE website handles checkout and account login.
3. Backend creates a license key with plan, quota, renewal date, and status.
4. Extension stores the license key in `chrome.storage.local`.
5. Extension calls the license API to check status and remaining credits.
6. Hosted API refuses runs that exceed credits.
7. Local Codex command generation remains free or trial-limited.

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

## Security Notes

The extension follows MV3 constraints:

- `manifest_version` is 3.
- Extension pages use `script-src 'self'`.
- JavaScript and CSS are bundled inside the extension.
- Remote services are used for data only, not remote code.
- No API secrets are stored in the extension.

Google's Manifest V3 docs require extension logic to be part of the extension package and not remotely hosted. The implementation keeps local code in `popup.js` and `popup.css`.

## Developer Info

- Developer: ENHE AI
- Website: https://www.enhe-tech.com.cn/
- Product page: https://www.enhe-tech.com.cn/promotion-manager
- Repository: https://github.com/hqwzhu/Viral-Product-Copy-Video-Generator.git
