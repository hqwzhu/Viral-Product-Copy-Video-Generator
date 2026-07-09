# Billing Backend Contract

This contract turns the browser extension subscription UI into a real payment and usage-control flow without putting payment secrets in the extension.

The extension remains a Chrome MV3 static package. It can open checkout, open a customer billing portal, store a license key locally, validate that license, and estimate credits. The backend is the source of truth for subscription status, quota, usage reservation, and payment webhooks.

## Provider

Use Stripe Checkout, Stripe Customer Portal, and Stripe webhooks, or an equivalent subscription provider with the same capabilities.

Current Stripe documentation describes:

- `Subscription` as the recurring billing agreement with statuses such as `trialing`, `active`, `past_due`, `canceled`, `unpaid`, and `paused`.
- Checkout Sessions with `mode=subscription` for hosted subscription checkout.
- Billing Portal Sessions for customer self-service billing management.
- Webhook handling for `checkout.session.completed`, `customer.subscription.*`, invoice payment events, and entitlement updates.

Do not put `STRIPE_SECRET_KEY`, webhook signing secrets, or price IDs that allow privilege escalation inside the extension.

## Extension Endpoints

Machine-readable version: `browser-extension/billing-contract.json`.

### Checkout

```http
GET https://www.enhe-tech.com.cn/promotion-manager/checkout?plan=growth&source=extension&credits=220
```

The ENHE website should create a hosted checkout session and redirect the user to the payment provider. The extension only opens this page.

### Customer Portal

```http
GET https://www.enhe-tech.com.cn/promotion-manager/billing?source=extension
```

The ENHE website should authenticate the user and create a provider customer portal session.

### License Validation

```http
POST https://www.enhe-tech.com.cn/api/promotion-manager/license
content-type: application/json
```

Request:

```json
{
  "licenseKey": "pm_live_xxx",
  "requestedPlan": "growth",
  "extensionVersion": "0.4.0",
  "website": "https://www.enhe-tech.com.cn/",
  "commandType": "skill_entry",
  "estimatedMonthlyCredits": 120
}
```

Response:

```json
{
  "active": true,
  "plan": "Growth",
  "creditsRemaining": 120,
  "renewsAt": "2026-08-09",
  "checkoutUrl": "https://www.enhe-tech.com.cn/promotion-manager/checkout",
  "customerPortalUrl": "https://www.enhe-tech.com.cn/promotion-manager/billing",
  "hostedRunEndpoint": "https://www.enhe-tech.com.cn/api/promotion-manager/run"
}
```

### Supported Workflow Types

The backend should keep these credit costs in sync with `browser-extension/billing-contract.json` and the popup estimator.

| Workflow type | Credits | Notes |
| --- | ---: | --- |
| `command_only` | 0 | Local command generation only. |
| `standard_run` | 1 | Product intake, copy, scripts, and basic platform plan. |
| `research_run` | 3 | Standard run plus viral discovery summary. |
| `deep_strategy_review` | 15 | Higher-cost strategy review. |
| `hosted_mp4_render` | 3 | Hosted render/storage add-on. |
| `browser_publish_session` | 2 | Browser/manual publish payloads, optional visible-field fill coordination, screenshots, and follow-up commands. |
| `real_evidence_inbox` | 2 | Published URL, metric, comment, order, and revenue evidence recovery. |
| `final_readiness_audit` | 1 | Final capability matrix refresh. |
| `automation_config_init` | 1 | Create a recurring automation config with safe job toggles. |
| `automation_due_run` | 4 | Run one due scheduled promotion job. |
| `automation_windows_task` | 1 | Generate a local Windows Task Scheduler registration script. |

### Usage Authorization

Before a hosted run, the backend must reserve credits.

```http
POST https://www.enhe-tech.com.cn/api/promotion-manager/usage/authorize
content-type: application/json
```

Request:

```json
{
  "licenseKey": "pm_live_xxx",
  "workflowType": "research_run",
  "estimatedCredits": 3,
  "idempotencyKey": "uuid",
  "commandType": "skill_entry",
  "extensionVersion": "0.4.0",
  "website": "https://www.enhe-tech.com.cn/"
}
```

Response:

```json
{
  "allowed": true,
  "usageId": "usage_123",
  "creditsReserved": 3,
  "creditsRemainingAfterReservation": 117,
  "reason": "ok"
}
```

### Usage Commit

After the run, commit actual usage.

```http
POST https://www.enhe-tech.com.cn/api/promotion-manager/usage/commit
content-type: application/json
```

Request:

```json
{
  "usageId": "usage_123",
  "inputTokens": 180000,
  "outputTokens": 65000,
  "videoSecondsRendered": 30,
  "creditsUsed": 3,
  "status": "succeeded"
}
```

## Reference Simulator

The repository includes a local, non-production simulator for this contract:

```powershell
python scripts\billing_contract_simulator.py demo `
  --plan growth `
  --workflow-type research_run `
  --out-dir ".\promotion-output"
```

It validates `browser-extension/billing-contract.json`, creates a local hashed license record, validates that license, reserves credits before a run, commits actual token usage, and applies a simulated `invoice.payment_succeeded` webhook. Reports are written to:

```text
promotion-output\reports\promotion-manager\billing-simulator\
```

Use it as an implementation reference for endpoint behavior and loss-control checks. It is not a production backend: a deployed service still needs authentication, database transactions, salted or peppered license-key hashing, webhook signature verification, audit logging, admin controls, and real payment-provider SDK integration.

## Webhooks

Backend endpoint:

```http
POST https://www.enhe-tech.com.cn/api/promotion-manager/webhooks/stripe
```

Required event handling:

| Event | Backend action |
| --- | --- |
| `checkout.session.completed` | Link customer, subscription, and license. Activate trial or paid entitlement. |
| `customer.subscription.created` | Create subscription record and plan quota. |
| `customer.subscription.updated` | Update plan, status, renewal, and quota. |
| `customer.subscription.deleted` | Disable hosted runs and mark license inactive. |
| `invoice.payment_succeeded` | Renew quota and clear delinquency. |
| `invoice.payment_failed` | Mark account past due and block new hosted runs after grace policy. |
| `entitlements.active_entitlement_summary.updated` | Sync provider entitlements into local license flags. |

Webhook signatures must be verified by the backend.

## Data Model

Minimum tables:

| Table | Key fields |
| --- | --- |
| `accounts` | `id`, `email`, `created_at` |
| `licenses` | `id`, `account_id`, `license_key_hash`, `status`, `plan`, `credits_remaining`, `renews_at` |
| `subscriptions` | `id`, `account_id`, `provider`, `provider_customer_id`, `provider_subscription_id`, `status`, `price_id` |
| `usage_ledger` | `id`, `license_id`, `workflow_type`, `credits_reserved`, `credits_used`, `input_tokens`, `output_tokens`, `status`, `idempotency_key` |

## Loss-Control Rules

- Hosted model calls must fail closed when the license API is unavailable.
- Hard-stop quota is the default for Free and Starter.
- Growth and Scale can use prepaid overage only after explicit backend enablement.
- A hosted run must reserve credits before model calls and commit actual usage after completion.
- Refunds, chargebacks, canceled subscriptions, and payment failures must stop hosted runs.
- Local command generation can remain free because it does not consume ENHE-hosted model tokens.

## Extension Responsibilities

- Open checkout and customer portal URLs.
- Store license key in `chrome.storage.local`.
- Call the license validation endpoint.
- Show current plan, credits, and renewal date.
- Estimate credits before the operator starts a hosted run.
- Reserve hosted credits by calling the usage authorization endpoint with workflow type, estimated credits, and an idempotency key.
- Never store provider secret keys or webhook secrets.

## Backend Responsibilities

- Create checkout sessions and customer portal sessions.
- Verify payment webhooks.
- Issue and hash license keys.
- Track credits, usage reservations, and usage commits.
- Block hosted runs when quota or subscription state is invalid.
- Keep Stripe price IDs, secret keys, webhook secrets, and tax/payment rules on the server.
