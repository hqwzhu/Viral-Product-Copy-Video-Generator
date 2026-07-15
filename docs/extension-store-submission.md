# ENHE Product Promo Maker Extension Store Submission

Version: 0.5.3

This guide turns `browser-extension/` into the Chrome Web Store and Microsoft Edge Add-ons submission package for ENHE Product Promo Maker.

Localized store names:

- English (default): `ENHE Product Promo Maker`
- Simplified Chinese: `ENHE 产品推广素材生成器`

Official references:

- Chrome Web Store publishing: https://developer.chrome.com/docs/webstore/publish
- Microsoft Edge Add-ons publishing: https://learn.microsoft.com/en-us/microsoft-edge/extensions-chromium/publish/publish-extension
- Chrome remote code migration notes: https://developer.chrome.com/docs/extensions/develop/migrate/remote-hosted-code

## Build The Package

From the repository root:

```powershell
python scripts\package_browser_extension.py --out-dir ".\dist\v0.5.3"
```

The command writes:

- `dist\v0.5.3\enhe-promotion-manager-0.5.3.zip`
- `dist\v0.5.3\browser-extension-package-report.json`
- `dist\v0.5.3\browser-extension-package-report.md`

Place reviewed store artwork in:

- `dist\v0.5.3\store-assets\enhe-product-promo-maker-en-1280x800.png`
- `dist\v0.5.3\store-assets\enhe-product-promo-maker-zh-1280x800.png`

Upload the zip file to the existing store item. Keep the reports as release evidence; the compatible package slug remains `enhe-promotion-manager-0.5.3.zip`.

## Pre-Submission Checklist

- Version and package output are 0.5.3 under `dist\v0.5.3`.
- Manifest is MV3.
- Popup code and CSS are packaged locally.
- No remote code is loaded by `<script src="https://...">`, dynamic imports, `importScripts`, `eval`, or `new Function`.
- Remote ENHE endpoints are used for data only: license validation, usage authorization, hosted run requests, checkout, and billing portal.
- No platform secrets, payment provider secrets, cookies, OAuth tokens, or webhook secrets are bundled.
- The package contains `icons/icon16.png`, `icons/icon48.png`, and `icons/icon128.png`.
- The package contains English and Simplified Chinese `_locales` metadata, and the popup follows the browser language on first launch while remembering a manual `中文 / EN` choice.
- The extension links to the ENHE website, product page, and GitHub repository as product references.
- Privacy policy: `https://www.enhe-tech.com.cn/promotion-manager/privacy`.
- Support URL: `https://www.enhe-tech.com.cn/promotion-manager/support`.
- Product website: `https://www.enhe-tech.com.cn/`.
- Publication-ready policy pages are in `docs/legal/`.
- Store listing and reviewer copy are in `docs/store/`.
- The existing Chrome Web Store item ID is `dloklkbnmoigemnfigbkibogmgbieppl`; update this item and do not create another item.

## Permission Justifications

- `activeTab`: capture the current product URL only after the user acts on the extension.
- `storage`: store local license and endpoint settings.
- `clipboardWrite`: copy generated local commands and hosted-run payloads only when requested by the user.
- `https://www.enhe-tech.com.cn/*`: validate licenses, open checkout and billing, reserve credits, submit hosted-run payloads, and retrieve hosted-run status.

All extension logic stays inside the package. Remote services return data only and do not provide executable extension code.

## Commercial Launch Gate

Before submitting a paid extension listing:

- Deploy `backend/license-service/` or an equivalent production license service behind HTTPS.
- Set `DATABASE_URL`, run `npm run migrate`, and deploy the API and hosted worker as isolated services. See `deploy/promotion-manager/`.
- Configure real Stripe Checkout prices, Customer Portal, and signed webhooks.
- Verify `checkout.session.completed`, `customer.subscription.updated`, `invoice.payment_succeeded`, and `invoice.payment_failed` in Stripe test mode.
- Confirm the extension can validate a real test license, reserve hosted usage credits, start a hosted run, and view the run status URL through the deployed API.
- Publish the privacy policy, support, refund/contact, and product pages.
- Prepare screenshots that show local command generation, license validation, credit reservation, and hosted-run payload review without exposing secrets.
- Keep all extension logic packaged locally; remote endpoints must return data only.
- Treat Chrome Web Store and Microsoft Edge Add-ons review as an external gate. Packaging can be automated, but store approval remains external.

## Localized Listing Values

### English (default)

- Name: `ENHE Product Promo Maker`
- Short description: `Turn product pages into promotional copy, video scripts, publishing assets, and guarded local or hosted promotion tasks.`

### Simplified Chinese

- Name: `ENHE 产品推广素材生成器`
- Short description: `把产品网页变成推广文案、视频脚本和发布素材，并生成受控的本地或托管推广任务。`

Use the detailed localized descriptions from `docs/store/chrome-listing.md` and `docs/store/edge-listing.md`.

## Chrome Web Store Steps

1. Create or open a Chrome Web Store Developer Dashboard account.
2. Pay any required developer registration fee in the dashboard.
3. Open item `dloklkbnmoigemnfigbkibogmgbieppl`; do not create a new item.
4. Check the dashboard status of the current v0.5.2 submission before uploading v0.5.3:
5. If v0.5.2 is pending review, do not replace it; wait for the review result.
6. If v0.5.2 is published, continue with the v0.5.3 upload as an update.
7. If v0.5.2 is rejected, record the rejection reason, fix any required issue, then upload v0.5.3.
8. Upload `dist\v0.5.3\enhe-promotion-manager-0.5.3.zip`.
9. Upload the v0.5.3 icon and both reviewed localized screenshots from `dist\v0.5.3\store-assets`.
10. Fill the localized name, short description, detailed description, category, product website, support URL, and privacy policy fields from the committed documents.
11. Fill privacy practices using the permission justifications above. State that the extension does not collect platform passwords, cookies, payment secrets, or API tokens.
12. Explain paid features: hosted runs require ENHE subscription credits; local command generation can remain free or trial-limited.
13. Paste `docs/store/reviewer-notes.md`, confirm the item ID again, and submit for review. If login, account verification, or captcha is required, pause for the account owner to complete it.

## Microsoft Edge Add-ons Steps

1. Create or open a Microsoft Partner Center account.
2. Open the existing Microsoft Edge extension submission when applicable; do not create a replacement for an existing item.
3. Check the dashboard status of the current v0.5.2 submission before uploading v0.5.3:
4. If v0.5.2 is pending review, do not replace it; wait for the review result.
5. If v0.5.2 is published, continue with the v0.5.3 upload as an update.
6. If v0.5.2 is rejected, record the rejection reason, fix any required issue, then upload v0.5.3.
7. Upload `dist\v0.5.3\enhe-promotion-manager-0.5.3.zip`.
8. Upload the v0.5.3 icon and both reviewed localized screenshots from `dist\v0.5.3\store-assets`.
9. Fill the localized product descriptions, category, privacy policy, support URL, permission justifications, and certification notes.
10. In reviewer notes, state that remote services return data only and that all extension logic is inside the package.
11. Confirm the generated publishing assets require user approval, then submit for certification. If login, account verification, or captcha is required, pause for the account owner to complete it.

## Reviewer Notes Template

```text
ENHE Product Promo Maker is a Manifest V3 extension that turns a product page selected by the user into promotional copy, video scripts, publishing assets, and guarded local commands or hosted ENHE run payloads. It reads the active product URL only after user action. All extension logic is packaged locally; ENHE endpoints return data only for license validation, checkout and billing, credit reservation, hosted-run queue submission, and hosted-run status. The extension does not publish to third-party platforms without user approval, bypass login/captcha/risk controls, or load remote executable code.
```

## Paid Subscription Notes

Use ENHE website billing rather than in-extension payment processing. Production enforcement must happen server-side:

- Validate the license before hosted runs.
- Reserve credits before the run.
- Commit actual credits after the run.
- Refund unused reserved credits on failure.
- Keep payment provider keys and webhook secrets on the backend.

See `docs/subscription-pricing.md`, `docs/billing-backend-contract.md`, and `browser-extension/billing-contract.json`.
