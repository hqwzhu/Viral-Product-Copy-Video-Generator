# ENHE Promotion Manager Deployment

This deploys the browser-extension backend on the same HTTPS host as the ENHE website while isolating it from the main site process.

## Target Layout

```text
https://www.enhe-tech.com.cn/api/promotion-manager/*  -> localhost:3030 API
https://www.enhe-tech.com.cn/promotion-manager/*      -> checkout, billing, legal pages, run status
/opt/enhe/promotion-manager/current                   -> repository checkout
/var/lib/enhe-promotion-manager                       -> private hosted-run artifacts and fallback state
/etc/enhe-promotion-manager/api.env                   -> production secrets
```

Use a separate Linux user for the API and worker. Keep the worker as a separate process from the website and the API process. Do not run it as root.

## Server Requirement

Minimum for a small launch:

- 2 vCPU, 4 GB RAM, 40 GB disk
- Node.js 20+
- Python 3.10+
- PostgreSQL 14+
- Nginx with a valid HTTPS certificate

Recommended if hosted runs generate videos or run many browser captures:

- 4 vCPU, 8 GB RAM, 80 GB disk
- Dedicated worker user
- Queue output cleanup/backup policy

The API process runs retention cleanup independently of hosted task execution. By default it automatically deletes completed Hosted Task artifact directories after 30 days and removes security and audit events after 180 days. Configure `HOSTED_ARTIFACT_RETENTION_DAYS`, `SECURITY_AUDIT_LOG_RETENTION_DAYS`, and `RETENTION_CLEANUP_INTERVAL_MS` in `api.env`. Payment, refund, subscription, license, and legally required accounting records are not removed by this cleanup job.

If the current ENHE website server has less than 2 vCPU or 4 GB RAM, upgrade before enabling hosted worker execution. You can still deploy the API/license service without the worker.

## Install

```bash
sudo useradd --system --home /var/lib/enhe-promotion-manager --shell /usr/sbin/nologin enhe-promotion
sudo useradd --system --home /var/lib/enhe-promotion-manager --shell /usr/sbin/nologin enhe-promotion-worker
sudo mkdir -p /opt/enhe/promotion-manager /var/lib/enhe-promotion-manager /etc/enhe-promotion-manager
sudo chown -R enhe-promotion:enhe-promotion /opt/enhe/promotion-manager /var/lib/enhe-promotion-manager
```

Clone or deploy the repository to `/opt/enhe/promotion-manager/current`, then:

```bash
cd /opt/enhe/promotion-manager/current/backend/license-service
npm ci --omit=dev
cp /opt/enhe/promotion-manager/current/deploy/promotion-manager/.env.production.example /etc/enhe-promotion-manager/api.env
```

Edit `/etc/enhe-promotion-manager/api.env` and fill PostgreSQL and `LICENSE_PEPPER` values. For domestic checkout, copy the existing ENHE website ZPAY merchant values into the server-only `ZPAY_*` variables and set the three CNY plan prices. Stripe remains optional for international subscriptions.

The domestic flow is isolated from the website order database:

```text
Promotion Manager checkout -> shared ZPAY merchant -> signed ZPAY callback
-> Promotion Manager payment record -> hashed license activation
```

`ZPAY_KEY` stays on the server. The extension never receives merchant credentials. Domestic payments are one-time 30-day licenses by default; change `ZPAY_LICENSE_DAYS` if the commercial term changes.

## Database

Create a PostgreSQL database and user:

```sql
CREATE USER enhe_promotion_manager WITH PASSWORD 'CHANGE_ME';
CREATE DATABASE enhe_promotion_manager OWNER enhe_promotion_manager;
```

Run migration:

```bash
cd /opt/enhe/promotion-manager/current/backend/license-service
npm run migrate
```

The service also supports local JSON fallback when `DATABASE_URL` is empty, but production should use PostgreSQL.

## Reverse Proxy

Copy `nginx-promotion-manager.conf` into the existing `www.enhe-tech.com.cn` HTTPS server block. It only proxies:

- `/api/promotion-manager/`
- `/promotion-manager/checkout`
- `/promotion-manager/billing`
- `/promotion-manager/privacy`
- `/promotion-manager/terms`
- `/promotion-manager/refund`
- `/promotion-manager/support`
- `/promotion-manager/runs/`

This prevents the plugin backend from taking over unrelated website routes.

## Services

```bash
sudo cp deploy/promotion-manager/enhe-promotion-manager-api.service /etc/systemd/system/
sudo cp deploy/promotion-manager/enhe-promotion-manager-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now enhe-promotion-manager-api
sudo systemctl enable --now enhe-promotion-manager-worker
```

For API-only launch, start only `enhe-promotion-manager-api` and leave worker disabled.

## Smoke Test

```bash
curl https://www.enhe-tech.com.cn/health
curl https://www.enhe-tech.com.cn/api/promotion-manager/run/not-real
```

The second command should return `{"error":"run_not_found"}` with HTTP 404, proving the API route is isolated and reachable.

## Rollback

Disable the Nginx include and stop the two systemd services:

```bash
sudo systemctl stop enhe-promotion-manager-worker enhe-promotion-manager-api
sudo systemctl disable enhe-promotion-manager-worker enhe-promotion-manager-api
sudo nginx -t && sudo systemctl reload nginx
```
