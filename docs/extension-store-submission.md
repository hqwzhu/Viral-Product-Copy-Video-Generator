# Extension Store Submission

This guide turns `browser-extension/` into a Chrome or Edge store submission package.

Official references:

- Chrome Web Store publishing: https://developer.chrome.com/docs/webstore/publish
- Microsoft Edge Add-ons publishing: https://learn.microsoft.com/en-us/microsoft-edge/extensions-chromium/publish/publish-extension
- Chrome remote code migration notes: https://developer.chrome.com/docs/extensions/develop/migrate/remote-hosted-code

## Build The Package

From the repository root:

```powershell
python scripts\package_browser_extension.py --out-dir ".\dist"
```

The command writes:

- `dist\enhe-promotion-manager-<version>.zip`
- `dist\browser-extension-package-report.json`
- `dist\browser-extension-package-report.md`

Upload the zip file to the store. Keep the report as release evidence.

## Pre-Submission Checklist

- Manifest is MV3.
- Popup code and CSS are packaged locally.
- No remote code is loaded by `<script src="https://...">`, dynamic imports, `importScripts`, `eval`, or `new Function`.
- Remote ENHE endpoints are used for data only: license validation, usage authorization, hosted run requests, checkout, and billing portal.
- No platform secrets, payment provider secrets, cookies, OAuth tokens, or webhook secrets are bundled.
- The package contains `icons/icon16.png`, `icons/icon48.png`, and `icons/icon128.png`.
- The extension links to the ENHE website, product page, and GitHub repository for traffic.
- A public privacy policy URL is ready, recommended: `https://www.enhe-tech.com.cn/privacy`.
- A support URL is ready, recommended: `https://www.enhe-tech.com.cn/`.
- Publication-ready policy pages are drafted in `docs/legal/`.
- Store listing and reviewer copy are drafted in `docs/store/`.

## Commercial Launch Gate

Before submitting a paid extension listing:

- Deploy `backend/license-service/` or an equivalent production License service behind HTTPS.
- Set `DATABASE_URL`, run `npm run migrate`, and deploy the API and hosted worker as isolated services. See `deploy/promotion-manager/`.
- Configure real Stripe Checkout prices, Customer Portal, and signed webhooks.
- Verify `checkout.session.completed`, `customer.subscription.updated`, `invoice.payment_succeeded`, and `invoice.payment_failed` in Stripe test mode.
- Confirm the extension can validate a real test license, reserve hosted usage credits, start a hosted run, and view the run status URL through the deployed API.
- Publish privacy policy, support, refund/contact, and product pages.
- Prepare screenshots that show local command generation, license validation, credit reservation, and hosted-run payload review.
- Keep all extension logic packaged locally; remote endpoints must return data only.
- Treat Chrome Web Store and Microsoft Edge Add-ons review as an external gate. Packaging can be automated, but store approval remains external.

## Chrome Web Store Steps

1. Create or open a Chrome Web Store Developer Dashboard account.
2. Pay any required developer registration fee in the dashboard.
3. Create a new item.
4. Upload `dist\enhe-promotion-manager-<version>.zip`.
5. Fill listing assets:
   - Name: `ENHE Promotion Manager`
   - Short description: `Generate guarded Codex promotion workflows from any product URL.`
   - Category: productivity or marketing, depending on the store options available at submission time.
   - Website: `https://www.enhe-tech.com.cn/`
   - Support URL: `https://www.enhe-tech.com.cn/`
   - Privacy policy: `https://www.enhe-tech.com.cn/promotion-manager/privacy`
   - Support URL: `https://www.enhe-tech.com.cn/promotion-manager/support`
6. Fill privacy practices. The extension uses `activeTab`, `storage`, `clipboardWrite`, and ENHE-hosted data endpoints. It does not collect platform passwords, cookies, payment secrets, or API tokens.
7. Explain paid features: hosted runs require ENHE subscription credits; local command generation can remain free or trial-limited.
8. Submit for review.

## Microsoft Edge Add-ons Steps

1. Create or open a Microsoft Partner Center account.
2. Create a new Microsoft Edge extension submission.
3. Upload the same `dist\enhe-promotion-manager-<version>.zip`.
4. Fill product description, category, screenshots, privacy policy, support URL, and certification notes.
5. In notes to reviewers, state that remote services return data only and that all extension logic is inside the package.
6. Submit for certification.

## Reviewer Notes Template

```text
ENHE Promotion Manager is a Manifest V3 operator extension. It captures the active product URL after user action and generates guarded Codex commands or hosted ENHE run payloads for product promotion workflows. The extension does not auto-publish to third-party platforms, does not bypass login/captcha/risk controls, and does not package remote executable code. ENHE backend endpoints are used only for license validation, subscription credit reservation, checkout, billing portal, hosted-run queue submission, and hosted-run status retrieval.
```

## Paid Subscription Notes

Use ENHE website billing rather than in-extension payment processing. Production enforcement must happen server-side:

- Validate license before hosted runs.
- Reserve credits before the run.
- Commit actual credits after the run.
- Refund unused reserved credits on failure.
- Keep payment provider keys and webhook secrets on the backend.

See `docs/subscription-pricing.md`, `docs/billing-backend-contract.md`, and `browser-extension/billing-contract.json`.
