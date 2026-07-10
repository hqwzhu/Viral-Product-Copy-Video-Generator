# Microsoft Edge Add-ons Listing Draft

## Product Name

ENHE Promotion Manager

## Short Description

Create safe product promotion workflows and hosted ENHE run payloads from the current product page.

## Full Description

ENHE Promotion Manager helps product operators create promotion workflows from any product or website URL. The extension captures a URL after user action, generates Codex commands, estimates hosted credits, validates ENHE licenses, reserves usage credits, and can submit hosted-run payloads to ENHE's backend worker queue.

All extension logic is packaged locally. Remote ENHE endpoints return data only for license validation, billing, usage reservation, and hosted-run status. The extension does not auto-publish content, does not bypass login/captcha/risk-control checks, and does not package remote executable code.

## Certification Notes

This Manifest V3 extension uses `activeTab`, `storage`, and `clipboardWrite`. It connects only to `https://www.enhe-tech.com.cn/*` for ENHE account, billing, license, usage, and hosted-run APIs. It does not collect platform credentials, cookies, payment secrets, or third-party API tokens.

Privacy policy: https://www.enhe-tech.com.cn/promotion-manager/privacy
Support: https://www.enhe-tech.com.cn/promotion-manager/support

