# ENHE Promotion Manager License Service

This is the production reference service for commercializing the browser extension. It connects the packaged Chrome/Edge extension contract to Stripe Checkout, Stripe Customer Portal, signed Stripe webhooks, hashed license records, usage reservation, usage commit, and hosted-run queue intake.

The service is intentionally small and deployable, but the default state store is a local JSON file. Replace it with a transactional database before production scale.

## Run Locally

```powershell
cd backend\license-service
npm install
copy .env.example .env
npm run start
```

Required environment variables are listed in `.env.example`. Keep all Stripe keys, webhook secrets, price IDs, and `LICENSE_PEPPER` on the server. Do not put them in the browser extension or repository.

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
- `POST /api/promotion-manager/license`
- `POST /api/promotion-manager/usage/authorize`
- `POST /api/promotion-manager/usage/commit`
- `POST /api/promotion-manager/run`
- `POST /api/promotion-manager/webhooks/stripe`

## Production Launch Notes

- Deploy behind HTTPS on `www.enhe-tech.com.cn` or update `browser-extension/billing-contract.json` to the deployed host.
- Replace the JSON state file with database tables and transactions for accounts, licenses, subscriptions, usage ledger, hosted runs, and audit logs.
- Add authenticated account pages or secure email delivery for newly issued license keys. The reference service hashes license keys at rest and does not store plaintext keys.
- Configure real Stripe prices for Starter, Growth, and Scale.
- Verify `checkout.session.completed`, `customer.subscription.*`, and invoice webhooks in Stripe test mode before switching to live mode.
- Connect the hosted-run queue to a worker only after usage reservation and safety flags are enforced.
- Chrome/Edge store approval remains external; store approval remains external to this repository and must be completed in the official store dashboards after backend deployment, privacy policy publication, screenshots, and reviewer notes are ready.
