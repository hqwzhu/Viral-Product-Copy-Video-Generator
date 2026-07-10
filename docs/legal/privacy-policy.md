# ENHE Promotion Manager Privacy Policy

Effective date: 2026-07-10

This policy is a publication-ready draft for the ENHE Promotion Manager browser extension and hosted service. Review it with counsel before public launch.

## What The Product Does

ENHE Promotion Manager helps users turn product or website URLs into guarded promotion workflow commands, publish packages, and optional ENHE-hosted task runs.

## Data We Process

- Product or website URLs that the user explicitly captures or enters.
- Selected target platforms and workflow options.
- Locally stored extension settings, including license key and endpoint preferences.
- Hosted-run payloads submitted by the user, including product URL, selected platforms, workflow depth, and safe workflow options.
- Billing and subscription status from Stripe or an equivalent payment provider.
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

Payments are handled by Stripe or an equivalent provider. ENHE servers do not receive or store raw card numbers. Payment provider privacy terms apply to checkout and billing portal activity.

## Retention

Hosted-run artifacts and audit logs are retained only as long as needed for service delivery, troubleshooting, billing records, abuse prevention, and legal compliance. Operators should configure an artifact cleanup policy before production launch.

## Security

The extension does not load remote executable code. Backend secrets, Stripe keys, webhook secrets, and worker credentials remain on the server. Hosted workers run with manual-publish safety gates and do not click final publish buttons on third-party platforms.

## Contact

Support: https://www.enhe-tech.com.cn/promotion-manager/support

