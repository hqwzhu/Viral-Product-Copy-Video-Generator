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
- `POST /api/promotion-manager/webhooks/stripe`

## Production Launch Notes

- Deploy behind HTTPS on `www.enhe-tech.com.cn` or update `browser-extension/billing-contract.json` to the deployed host.
- Set `DATABASE_URL` and run `npm run migrate`; JSON state is only for local development.
- Run the API and hosted worker as separate systemd services and separate Linux users. See `deploy/promotion-manager/`.
- Add authenticated account pages or secure email delivery for newly issued license keys. The reference service hashes license keys at rest and does not store plaintext keys.
- Configure real Stripe prices for Starter, Growth, and Scale.
- Verify `checkout.session.completed`, `customer.subscription.*`, and invoice webhooks in Stripe test mode before switching to live mode.
- Keep `I_APPROVE_PUBLISH=false`, `PUBLISH_DRY_RUN=true`, and `REQUIRE_MANUAL_APPROVAL=true` in worker child processes unless a future official API publishing upgrade is explicitly approved.
- Chrome/Edge store approval remains external; store approval remains external to this repository and must be completed in the official store dashboards after backend deployment, privacy policy publication, screenshots, and reviewer notes are ready.
