# ENHE Product Promo Maker Extension Store Submission

Version: 0.5.3

This guide turns `browser-extension/` into the Chrome Web Store and Microsoft Edge Add-ons submission package for ENHE Product Promo Maker.

## Current Published Release

Chrome Web Store item `dloklkbnmoigemnfigbkibogmgbieppl` has version `0.5.3` published. Its archived ZIP, artwork, checksums, and release evidence are immutable. Do not repackage, re-upload, or replace v0.5.3. For the next version, first increment the extension version, create a new release directory and evidence set, then submit that new version as an update to the same item.

Localized store names:

- English (default): `ENHE Product Promo Maker`
- Simplified Chinese: `ENHE 产品推广素材生成器`

Official references:

- Chrome Web Store publishing: https://developer.chrome.com/docs/webstore/publish
- Microsoft Edge Add-ons publishing: https://learn.microsoft.com/en-us/microsoft-edge/extensions-chromium/publish/publish-extension
- Chrome remote code migration notes: https://developer.chrome.com/docs/extensions/develop/migrate/remote-hosted-code

## Build The Package

From the repository root:

For the next version only, after incrementing the version:

```powershell
python scripts\package_browser_extension.py --out-dir ".\dist\v<NEXT_VERSION>"
```

The command writes:

- `dist\v<NEXT_VERSION>\enhe-promotion-manager-<NEXT_VERSION>.zip`
- `dist\v<NEXT_VERSION>\browser-extension-package-report.json`
- `dist\v<NEXT_VERSION>\browser-extension-package-report.md`

Place reviewed store artwork in:

- `dist\v<NEXT_VERSION>\store-assets\enhe-product-promo-maker-en-1280x800.png`
- `dist\v<NEXT_VERSION>\store-assets\enhe-product-promo-maker-zh-1280x800.png`

Upload the next-version ZIP to the existing store item. Keep its reports as release evidence.

## Pre-Submission Checklist

- The current published release remains v0.5.3 and unchanged; the next version and package output use a new `dist\v<NEXT_VERSION>` directory.
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
4. Confirm that v0.5.3 is published, then increment the manifest version for the next version; do not change the v0.5.3 archive or listing history.
5. Package the next version and upload `dist\v<NEXT_VERSION>\enhe-promotion-manager-<NEXT_VERSION>.zip` as an update to this item.
6. Upload next-version icons and both reviewed localized screenshots from `dist\v<NEXT_VERSION>\store-assets`.
7. Fill the localized name, short description, detailed description, category, product website, support URL, and privacy policy fields from the committed documents.
8. Fill privacy practices using the permission justifications above. State that the extension does not collect platform passwords, cookies, payment secrets, or API tokens.
9. Explain paid features: hosted runs require ENHE subscription credits; local command generation can remain free or trial-limited.
10. Paste `docs/store/reviewer-notes.md`, confirm the item ID again, and submit the next version for review. If login, account verification, or captcha is required, pause for the account owner to complete it.

## Microsoft Edge Add-ons Steps

1. Create or open a Microsoft Partner Center account.
2. Open the existing Microsoft Edge extension submission when applicable; do not create a replacement for an existing item.
3. Verify the current Edge listing status independently. If v0.5.3 is published for that Edge item, increment the manifest version for the next version; if v0.5.3 is not published, follow the applicable Edge submission flow without treating the Chrome publication as Edge publication.
4. Package and upload `dist\v<NEXT_VERSION>\enhe-promotion-manager-<NEXT_VERSION>.zip` as the next-version update.
5. Upload next-version icons and both reviewed localized screenshots from `dist\v<NEXT_VERSION>\store-assets`.
6. Fill the localized product descriptions, category, privacy policy, support URL, permission justifications, and certification notes.
7. In reviewer notes, state that remote services return data only and that all extension logic is inside the package.
8. Confirm the generated publishing assets require user approval, then submit the next version for certification. If login, account verification, or captcha is required, pause for the account owner to complete it.

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
