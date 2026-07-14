# Chrome Web Store Listing Draft

## Name

ENHE Promotion Manager

## Short Description

Generate guarded Codex promotion workflows, copy, video scripts, and publish packages from any product URL.

## Detailed Description

ENHE Promotion Manager is an operator extension for founders, AI tool builders, and product marketers. Capture the current product page, choose target platforms, estimate hosted credits, and generate safe Codex workflows for product promotion research, viral copy, video scripts, publish packages, and next-round optimization.

The extension can also connect to ENHE hosted runs after license validation and server-side credit reservation. Hosted runs are processed by the ENHE backend and worker queue. The extension does not auto-publish to third-party platforms, does not bypass login or captcha, and does not include remote executable code.

## Category

Productivity

## Permission Justification

- `activeTab`: capture the current product URL only after user action.
- `storage`: store local license and endpoint settings.
- `clipboardWrite`: copy generated Codex commands and hosted-run payloads.
- Host permission for `https://www.enhe-tech.com.cn/*`: validate license, reserve credits, open checkout/billing, and submit hosted-run payloads.

## Privacy Practices

The extension processes product URLs, selected workflow settings, license validation requests, usage reservation requests, and hosted-run payloads. It does not collect passwords, cookies, payment card numbers, captcha answers, or third-party platform secrets.

Privacy policy: https://www.enhe-tech.com.cn/promotion-manager/privacy
Terms: https://www.enhe-tech.com.cn/promotion-manager/terms
Refund policy: https://www.enhe-tech.com.cn/promotion-manager/refund
Support: https://www.enhe-tech.com.cn/promotion-manager/support

