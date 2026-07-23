# Store Reviewer Notes

Use this text in Chrome Web Store and Microsoft Edge Add-ons reviewer notes.

```text
ENHE Product Promo Maker is a Manifest V3 extension that turns a product page selected by the user into promotional copy, video scripts, publishing assets, and guarded local commands or hosted ENHE run payloads.

The extension reads the active product URL only after user action. It uses activeTab for that user-selected page, storage for local license and endpoint settings, clipboardWrite for user-requested copies, and https://www.enhe-tech.com.cn/* for license validation, checkout and billing, credit reservation, hosted-run queue submission, and hosted-run status retrieval.

All extension logic is packaged locally. The extension does not load or execute remote code, publish to third-party platforms without user approval, bypass login, captcha, account verification, or risk-control systems, or send platform passwords, cookies, payment secrets, OAuth tokens, or webhook secrets.

The hosted worker runs server-side from a queue only after license and quota checks. It processes the user-reviewed payload and cannot send arbitrary remote code to the extension.
```

Privacy policy: https://www.enhe-tech.com.cn/promotion-manager/privacy
Support: https://www.enhe-tech.com.cn/promotion-manager/support

## Test Account Notes

If the store reviewer needs a test license, create a limited test license in the backend and provide it only inside the store dashboard reviewer notes. Do not commit test license keys to this repository.

