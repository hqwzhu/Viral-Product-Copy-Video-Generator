# ENHE Product Promo Maker Privacy Policy

Effective date: 2026-07-15

This policy explains how ENHE AI processes information for ENHE Product Promo Maker (formerly ENHE Promotion Manager), including its browser extension and optional hosted service.

## What The Product Does

ENHE Product Promo Maker helps users turn product or website URLs into guarded promotion workflow commands, publish packages, and optional ENHE-hosted task runs.

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

- Hosted Task artifacts are automatically deleted 30 days after the task finishes.
- Security and audit logs are retained for 180 days.
- Payment, refund, and legally required accounting records are retained as required by applicable law.
- Local extension settings remain on the user's device until the user clears extension storage or uninstalls the extension.

Users may email huqingwei5942@gmail.com to request access to or deletion of data that is not subject to mandatory retention.

## Security

The extension does not load remote executable code. Backend secrets, Stripe keys, webhook secrets, and worker credentials remain on the server. Hosted workers run with manual-publish safety gates and do not click final publish buttons on third-party platforms.

## Contact

Email: huqingwei5942@gmail.com

Support: https://www.enhe-tech.com.cn/promotion-manager/support

Mailing address: 深圳市龙岗区横岗街道塘坑社区宸和路51号中联展数字电商产业园C栋C305
