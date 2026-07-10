# Store Reviewer Notes

Use this text in Chrome Web Store and Microsoft Edge Add-ons reviewer notes.

```text
ENHE Promotion Manager is a Manifest V3 operator extension. It captures the active product URL only after user action and generates guarded Codex commands or hosted ENHE run payloads for product promotion workflows.

The extension does not auto-publish to third-party platforms, does not bypass login, captcha, account verification, or risk-control systems, and does not package remote executable code. ENHE backend endpoints are used only for license validation, subscription checkout, customer billing portal, usage credit reservation, hosted-run queue submission, and hosted-run status retrieval.

The hosted worker runs server-side from a queue after license and quota checks. The extension cannot execute arbitrary remote code and does not send platform passwords, cookies, payment secrets, OAuth tokens, or webhook secrets.
```

## Test Account Notes

If the store reviewer needs a test license, create a limited test license in the backend and provide it only inside the store dashboard reviewer notes. Do not commit test license keys to this repository.

