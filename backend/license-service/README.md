# ENHE Promotion Manager License Service

This is the production reference service for commercializing the browser extension. It connects the packaged Chrome/Edge extension contract to Stripe Checkout, Stripe Customer Portal, signed Stripe webhooks, hashed license records, usage reservation, usage commit, hosted-run queue intake, hosted-run status pages, and an isolated worker process.

The service supports PostgreSQL through `DATABASE_URL`. If `DATABASE_URL` is empty, it falls back to a local JSON state file for development only.

## Run Locally

```powershell
cd backend\license-service
npm install
copy .env.example .env
npm run migrate
npm run start
```

Required environment variables are listed in `.env.example`. Keep all Stripe keys, webhook secrets, price IDs, and `LICENSE_PEPPER` on the server. Do not put them in the browser extension or repository.

Run the worker in a separate terminal for hosted task execution:

```powershell
npm run worker
```

For tests or staging without executing Python workflows, set `HOSTED_WORKER_MODE=simulate`.

## Stripe Webhook Test

Use Stripe CLI in a local test account:

```powershell
stripe listen --forward-to localhost:3000/api/promotion-manager/webhooks/stripe
```

Copy the printed webhook signing secret into `STRIPE_WEBHOOK_SECRET`, then restart the service. Webhook verification uses `stripe.webhooks.constructEvent` with the raw request body.

## Endpoints

- `GET /health`
- `GET /api/promotion-manager/health` (same payload as `/health`)
- `GET /promotion-manager/checkout`
- `GET /promotion-manager/billing`
- `GET /promotion-manager/privacy`
- `GET /promotion-manager/terms`
- `GET /promotion-manager/refund`
- `GET /promotion-manager/support`
- `POST /api/promotion-manager/license`
- `POST /api/promotion-manager/usage/authorize`
- `POST /api/promotion-manager/usage/commit`
- `POST /api/promotion-manager/run`
- `GET /api/promotion-manager/run/:runId`
- `GET /promotion-manager/runs/:runId`
- `POST /api/promotion-manager/payments/zpay/checkout`
- `GET /api/promotion-manager/payments/zpay/status?orderNo=...`
- `POST /api/promotion-manager/webhooks/stripe`
- `GET /api/promotion-manager/webhooks/zpay`

The domestic checkout endpoint keeps two response modes:

- A normal HTML form submission receives the existing `303` redirect to the payment provider.
- A request with `Accept: application/json` receives `201` JSON containing the order number, public payment URL, locally generated QR data URL, plan, amount, 30-day term, and same-origin claim URL.

The payment-status endpoint requires the matching `HttpOnly` claim cookie. It returns only the order status and, after payment, the claim URL; it never returns the License Key. The signed ZPAY webhook remains the only authority that activates a payment.

On the public checkout page, desktop browsers display the QR code and poll for up to ten minutes. Mobile browsers open WeChat Pay or Alipay directly. Chinese and English are available from the visible language control, which follows the browser language on first use and stores the user's selection locally.

Domestic public prices are 30-day licenses: Starter ¥19, Growth ¥59, and Scale ¥199. Provider requests retain two-decimal CNY amounts (`19.00`, `59.00`, and `199.00`).

## Production Launch Notes

- Deploy behind HTTPS on `www.enhe-tech.com.cn` or update `browser-extension/billing-contract.json` to the deployed host.
- Set `DATABASE_URL` and run `npm run migrate`; JSON state is only for local development.
- Run the API and hosted worker as separate systemd services and separate Linux users. See `deploy/promotion-manager/`.
- Add authenticated account pages or secure email delivery for newly issued license keys. The reference service hashes license keys at rest and does not store plaintext keys.
- Configure real Stripe prices for Starter, Growth, and Scale.
- Verify `checkout.session.completed`, `customer.subscription.*`, and invoice webhooks in Stripe test mode before switching to live mode.
- Keep `I_APPROVE_PUBLISH=false`, `PUBLISH_DRY_RUN=true`, and `REQUIRE_MANUAL_APPROVAL=true` in worker child processes unless a future official API publishing upgrade is explicitly approved.
- Chrome/Edge store approval remains external; store approval remains external to this repository and must be completed in the official store dashboards after backend deployment, privacy policy publication, screenshots, and reviewer notes are ready.
