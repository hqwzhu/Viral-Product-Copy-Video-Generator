# Desktop QR Checkout and Public Surface Hardening Design

**Date:** 2026-07-15

**Status:** Approved interaction, pending written-spec review
**Base:** `origin/main` after PR #1

## Goal

Improve the existing ZPAY checkout without changing the Chrome Web Store package. Desktop users stay on the ENHE checkout page and scan a QR code; mobile users continue to open WeChat or Alipay directly. The same pull request also locks the public bilingual, pricing, privacy, and health-check behavior with regression coverage. After the pull request is merged, deploy the exact merge commit to production and verify the live service.

## Scope

The pull request will contain only the following changes:

1. Desktop QR checkout for WeChat Pay and Alipay.
2. Direct provider launch on mobile devices.
3. Same-origin payment-status polling and automatic transition to the existing License Key claim page.
4. Chinese and English checkout, payment-state, and privacy content.
5. Exact 30-day public prices: Starter ¥19, Growth ¥59, and Scale ¥199.
6. A compatibility health endpoint at `/api/promotion-manager/health` with the same payload and status as `/health`.
7. Regression tests and concise deployment documentation for all of the above.

Existing PR #1 commits remain in `main`; they will not be duplicated or rewritten. The already submitted Chrome extension v0.5.2 ZIP is out of scope because the extension only opens the remote checkout URL and needs no package change.

## Considered Approaches

### A. Same-origin JSON checkout plus server-generated QR code — selected

The existing POST endpoint keeps its redirect behavior for normal HTML forms. Requests explicitly asking for JSON receive the order number, provider destination, a locally generated QR data URL, and the claim-page URL. The page polls a protected status endpoint and navigates to the claim page after payment.

This preserves the current callback and License Key flow, does not depend on an external QR service, and gives ENHE control over the desktop experience.

### B. Display the provider's QR image directly

This has fewer code changes, but ZPAY response fields and image formats may vary by channel. It also makes the browser depend directly on a provider image URL and provides no complete status experience.

### C. Embed or redirect to the provider's hosted page

This keeps the ENHE backend simple, but it recreates the current desktop inconvenience and introduces cross-origin and mobile compatibility problems.

## Backend Design

### Checkout creation

`POST /api/promotion-manager/payments/zpay/checkout` remains the only order-creation endpoint.

- Existing form submissions receive the current `303` redirect.
- Requests with `Accept: application/json` receive JSON instead.
- The response contains only the order identifier, payment type, public payment destination, locally generated QR data URL, public plan/price, and claim URL.
- The existing `HttpOnly`, `Secure`, `SameSite=Lax` claim cookie remains the proof that the browser owns the pending License Key.
- Merchant credentials and the License Key never appear in the JSON response or persisted payment record.

The QR code is generated inside the service from the provider payment destination using a pinned npm dependency. No remote JavaScript or third-party QR-generation URL is used.

### Payment status

Add `GET /api/promotion-manager/payments/zpay/status?orderNo=...`.

- Look up the payment by order number.
- Require the claim cookie to hash to the License record associated with that payment.
- Return only `pending`, `paid`, or `failed`, plus the same-origin claim URL when appropriate.
- Return `404` for unknown orders and `403` when the claim cookie does not match.
- Never return the License Key from the status endpoint.

The existing signed ZPAY webhook remains the only authority that changes a payment to `paid` and activates the License.

### Health checks

Use one health handler for both:

- `GET /health`
- `GET /api/promotion-manager/health`

Both paths must return the same status code and JSON payload. No secret configuration values are included.

## Browser Experience

### Desktop

Submitting the checkout form with JavaScript:

1. Disables the submit button and shows a creating-order state.
2. Requests JSON from the same-origin checkout endpoint.
3. Shows a payment panel containing the provider name, plan, exact price, QR code, order number, and a fallback link to open the provider page.
4. Polls the protected status endpoint every three seconds for at most ten minutes, pausing while the page is hidden and resuming when it becomes visible.
5. On `paid`, stops polling and navigates to the existing claim page.
6. On failure or timeout, keeps the order details visible and offers retry or direct provider launch.

### Mobile

The same JSON order-creation flow is used so the claim cookie is set consistently. When the device reports a mobile browser, the page navigates directly to the provider destination instead of showing the QR panel. A user can return to the ENHE claim URL after completing payment.

If JavaScript is unavailable, the existing HTML form and `303` redirect continue to work on all devices.

## Internationalization

The checkout page uses a small inline Chinese/English message dictionary; it does not load remote code.

- The initial language follows the browser language.
- A visible `中文 / EN` control changes the language immediately.
- The choice is stored in local storage.
- Plan names remain Starter, Growth, and Scale; surrounding labels, instructions, errors, buttons, and payment states are translated.
- The payment result page and public privacy page provide equivalent Chinese and English content.

## Pricing and Privacy Invariants

The service continues to read production prices from server-side environment variables, but the regression suite and deployment check require:

- Starter: CNY 19 for 30 days.
- Growth: CNY 59 for 30 days.
- Scale: CNY 199 for 30 days.

The public UI omits unnecessary `.00`; the signed provider request continues to use two-decimal amounts.

The bilingual privacy page must preserve these business rules exactly:

- Hosted Task artifacts are automatically deleted after 30 days.
- Security and audit logs are retained for 180 days.
- Payment, refund, and legally required accounting records are retained under applicable law.
- Users can email `huqingwei5942@gmail.com` to request access to or deletion of data that is not subject to mandatory retention.

## Error Handling and Security

- Reject unsupported plans, invalid email addresses, missing prices, invalid provider responses, and non-public payment destinations.
- Do not mark payments paid from browser polling or return URLs.
- Do not expose merchant secrets, License Keys, raw claim-cookie values, or internal state records.
- Pause polling while the page is hidden, stop after ten minutes, and stop immediately when the user leaves the page.
- Escape all server-rendered text and place dynamic browser content through text-safe DOM APIs.
- Keep the direct provider link available as a controlled fallback.

## Test Strategy

Implementation follows red-green-refactor. Tests are written and observed failing before production code changes.

Backend integration tests will cover:

- Existing form submission still returns `303`.
- JSON checkout returns a QR payload and sets the claim cookie.
- Exact plan prices and 30-day term.
- Status polling returns pending and paid states for the owning browser.
- Missing or mismatched claim cookies are rejected.
- Webhook verification remains the only activation path.
- `/health` and `/api/promotion-manager/health` are equivalent.
- Checkout and privacy HTML contain both language dictionaries and the approved retention text.

The full Python regression suite and backend Node test suite must pass before the branch is pushed. A browser smoke test will validate desktop QR rendering, language switching, and the mobile direct-launch branch without completing another real payment.

## Delivery and Deployment

1. Work from an isolated branch based on current `origin/main`.
2. Keep all intended code, tests, documentation, and dependency-lock changes in one pull request.
3. Do not stage the user's modified `dist/enhe-promotion-manager-0.5.0.zip` or untracked `dist/store-assets/` files.
4. Push the branch, create a ready-for-review pull request, and merge only after all checks pass.
5. Build a release archive from the merge commit, deploy it atomically to the existing production service, and retain the previous release for rollback.
6. Verify the systemd service, both health URLs, bilingual checkout/privacy pages, exact prices, and desktop QR rendering against production.
7. Roll back the symlink and environment file if service startup or health verification fails.

## Acceptance Criteria

- A desktop checkout displays a scannable QR code without forcing a WeChat desktop-client launch.
- A mobile checkout directly opens the selected provider.
- A paid order automatically reaches the License Key claim page, while an unauthorized browser cannot poll or claim it.
- Chinese and English checkout, result, and privacy content are available and persistent.
- The live prices are ¥19, ¥59, and ¥199 for 30 days.
- Both health paths return the same healthy response.
- One pull request contains the complete incremental change and is merged.
- Production runs the merge commit and passes the post-deployment checks.
