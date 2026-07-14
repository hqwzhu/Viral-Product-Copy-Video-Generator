# ENHE Promotion Manager Privacy Policy

Effective date: 2026-07-14

This policy explains how ENHE AI processes information for the ENHE Promotion Manager browser extension and optional hosted service.

## What The Product Does

ENHE Promotion Manager helps users turn product or website URLs into guarded promotion workflow commands, publish packages, and optional ENHE-hosted task runs.

## Data We Process

- Product or website URLs that the user explicitly captures or enters.
- Selected target platforms and workflow options.
- Locally stored extension settings, including license key and endpoint preferences.
- Hosted-run payloads submitted by the user, including product URL, selected platforms, workflow depth, and safe workflow options.
- Billing and subscription status from ZPAY, Stripe, or an equivalent payment provider.
- Server logs, quota events, usage reservations, hosted-run status, and audit events.

## Data We Do Not Collect

- Platform passwords.
- Browser cookies.
- Captcha answers.
- Hidden tokens.
- Payment card numbers.
- Third-party platform OAuth tokens unless a future official integration explicitly asks the user to authorize it.

## How Data Is Used

- Validate subscriptions and license status.
- Reserve and commit hosted usage credits.
- Queue and run user-requested hosted promotion tasks.
- Provide run status, support, security auditing, and abuse prevention.
- Improve reliability and product operations from aggregate, non-sensitive diagnostics.

## Local Extension Storage

The extension stores the license key, endpoint preferences, and last run metadata in `chrome.storage.local`. Users can remove this by uninstalling the extension or clearing extension storage.

## Payment Processing

Payments are handled by ZPAY, Stripe, or an equivalent provider. ENHE servers do not receive or store raw payment card numbers or users' payment-account passwords. Payment provider privacy terms apply to checkout and billing activity.

## Retention

- Hosted-run artifacts are retained for up to 30 days after a run finishes, unless the user requests earlier deletion or a longer period is required to investigate abuse, resolve a dispute, or comply with law.
- Security, usage, and audit logs are retained for up to 180 days.
- Billing, refund, tax, and license records are retained for the period required by applicable law and payment-provider obligations.
- Local extension settings remain on the user's device until the user clears extension storage or uninstalls the extension.

After the applicable period ends, information is deleted or anonymized unless continued retention is legally required.

## Security

The extension does not load remote executable code. Backend secrets, Stripe keys, webhook secrets, and worker credentials remain on the server. Hosted workers run with manual-publish safety gates and do not click final publish buttons on third-party platforms.

## Contact

Email: huqingwei5942@gmail.com

Support: https://www.enhe-tech.com.cn/promotion-manager/support

Mailing address: 深圳市龙岗区横岗街道塘坑社区宸和路51号中联展数字电商产业园C栋C305
