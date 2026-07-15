"use strict";

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const express = require("express");
const QRCode = require("qrcode");
const Stripe = require("stripe");
const {
  createStateStore,
  emptyState,
  loadJsonState,
  saveJsonState
} = require("./state-store");
const { commitUsage, startHostedWorker, startRetentionCleanup } = require("./hosted-worker");
const {
  ZPAY_PRICE_ENV_BY_PLAN,
  buildZpayPaymentRequest,
  isZpayConfigured,
  loadZpayConfig,
  normalizeZpayType,
  requestZpayPayment,
  verifyZpayNotifyPayload,
  zpayPriceForPlan
} = require("./zpay");
require("dotenv").config();

const app = express();
const port = Number(process.env.PORT || 3000);
const publicBaseUrl = trimTrailingSlash(process.env.ENHE_PUBLIC_BASE_URL || "http://localhost:3000");
const stateFile = process.env.LICENSE_SERVICE_STATE_FILE || path.join(__dirname, "..", "var", "license-service-state.json");
const store = createStateStore({ stateFile, databaseUrl: process.env.DATABASE_URL });
const stripe = process.env.STRIPE_SECRET_KEY ? new Stripe(process.env.STRIPE_SECRET_KEY) : null;

const PLAN_CREDITS = {
  free: 5,
  starter: 60,
  growth: 220,
  scale: 800
};

const WORKFLOW_CREDIT_COSTS = {
  command_only: 0,
  standard_run: 4,
  research_run: 3,
  deep_strategy_review: 15,
  hosted_mp4_render: 3,
  browser_publish_session: 2,
  launch_unlock_pack: 2,
  viral_evidence_inbox_setup: 1,
  viral_evidence_inbox: 2,
  real_evidence_inbox_setup: 1,
  real_evidence_inbox: 2,
  performance_monitor: 2,
  final_readiness_audit: 1,
  automation_config_init: 1,
  automation_due_run: 4,
  automation_windows_task: 1
};

const STRIPE_PRICE_ENV_BY_PLAN = {
  starter: "STRIPE_PRICE_STARTER",
  growth: "STRIPE_PRICE_GROWTH",
  scale: "STRIPE_PRICE_SCALE"
};

const LEGAL_PAGES = {
  privacy: "privacy-policy.md",
  terms: "terms-of-service.md",
  refund: "refund-policy.md",
  support: "support.md"
};

app.post(
  "/api/promotion-manager/webhooks/stripe",
  express.raw({ type: "application/json" }),
  asyncHandler(async (req, res) => {
    const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
    if (!stripe || !webhookSecret) {
      return res.status(500).json({ error: "missing_stripe_webhook_config" });
    }
    const signature = req.headers["stripe-signature"];
    let event;
    try {
      event = stripe.webhooks.constructEvent(req.body, signature, webhookSecret);
    } catch (error) {
      return res.status(400).send(`Webhook Error: ${error.message}`);
    }

    const result = await store.update((state) => {
      const eventResult = handleStripeEvent(state, event);
      audit(state, "stripe_webhook", { eventId: event.id, eventType: event.type, result: eventResult });
      return eventResult;
    });
    return res.json({ received: true, event: event.type, result });
  })
);

app.get("/api/promotion-manager/webhooks/zpay", asyncHandler(async (req, res) => {
  if (!isZpayConfigured()) {
    return res.status(500).send("missing-zpay-config");
  }
  const payload = zpayPayloadFromQuery(req.query);
  const state = await store.load();
  const payment = Object.values(state.payments).find(
    (item) => item.orderNo === String(payload.out_trade_no || "")
  );
  if (!payment) return res.status(404).send("order-not-found");

  const validation = verifyZpayNotifyPayload(payload, payment, loadZpayConfig());
  if (!validation.ok) return res.status(400).send(validation.reason);

  await store.update((currentState) => {
    const currentPayment = currentState.payments[payment.id];
    const license = currentState.licenses[payment.licenseId];
    if (!currentPayment || !license) throw new Error("ZPAY payment state is incomplete.");
    if (currentPayment.status !== "paid") {
      currentPayment.status = "paid";
      currentPayment.providerTradeNo = String(payload.trade_no || currentPayment.providerTradeNo || "");
      currentPayment.paidAt = nowIso();
      currentPayment.updatedAt = nowIso();
      license.status = "active";
      license.creditsRemaining = PLAN_CREDITS[license.plan];
      license.renewsAt = addDaysIso(loadZpayConfig().licenseDays);
      license.updatedAt = nowIso();
      audit(currentState, "zpay_payment_succeeded", {
        paymentId: currentPayment.id,
        licenseId: license.id,
        plan: license.plan,
        amount: currentPayment.amount,
        paymentType: currentPayment.paymentType
      });
    }
  });
  return res.type("text").send("success");
}));

app.use(express.json({ limit: "1mb" }));
app.use(express.urlencoded({ extended: false, limit: "100kb" }));

async function sendHealth(_req, res) {
  await store.init();
  return res.json({
    ok: true,
    service: "enhe-promotion-manager-license-service",
    stripeConfigured: Boolean(stripe),
    zpayConfigured: isZpayConfigured(),
    stateBackend: process.env.DATABASE_URL ? "postgres" : "json",
    workerEnabled: process.env.HOSTED_WORKER_ENABLED === "true",
    stateFile: process.env.DATABASE_URL ? "" : stateFile
  });
}

app.get("/health", asyncHandler(sendHealth));
app.get("/api/promotion-manager/health", asyncHandler(sendHealth));

app.get("/promotion-manager/checkout", asyncHandler(async (req, res) => {
  if (isZpayConfigured()) {
    const plan = normalizePlan(req.query.plan || "starter");
    if (plan === "free") {
      return res.status(400).json({ error: "free_plan_does_not_use_checkout" });
    }
    return res.type("html").send(renderZpayCheckoutPage(plan));
  }
  const error = requireStripeConfig(["STRIPE_SECRET_KEY"]);
  if (error) return res.status(500).json(error);

  const plan = normalizePlan(req.query.plan || "starter");
  if (plan === "free") {
    return res.status(400).json({ error: "free_plan_does_not_use_checkout" });
  }
  const priceId = priceIdForPlan(plan);
  if (!priceId) {
    return res.status(500).json({ error: "missing_stripe_price", env: STRIPE_PRICE_ENV_BY_PLAN[plan] });
  }

  try {
    const session = await stripe.checkout.sessions.create({
      mode: "subscription",
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: `${publicBaseUrl}/promotion-manager/checkout/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${publicBaseUrl}/promotion-manager/checkout/cancel`,
      metadata: {
        plan,
        source: String(req.query.source || "web"),
        requestedCredits: String(req.query.credits || PLAN_CREDITS[plan])
      }
    });
    return res.redirect(303, session.url);
  } catch (error) {
    return res.status(502).json({ error: "stripe_checkout_failed", message: error.message });
  }
}));

app.post("/api/promotion-manager/payments/zpay/checkout", asyncHandler(async (req, res) => {
  if (!isZpayConfigured()) {
    return res.status(500).json({ error: "missing_zpay_config" });
  }
  const plan = normalizePlan(req.body.plan || "starter");
  if (plan === "free") return res.status(400).json({ error: "free_plan_does_not_use_checkout" });
  const amount = zpayPriceForPlan(plan);
  if (!amount) {
    return res.status(500).json({ error: "missing_zpay_price", env: ZPAY_PRICE_ENV_BY_PLAN[plan] });
  }
  const email = String(req.body.email || "").trim().toLowerCase();
  if (!/^\S+@\S+\.\S+$/.test(email)) return res.status(400).json({ error: "invalid_email" });

  const paymentId = `pay_${crypto.randomUUID()}`;
  const orderNo = `pm_${Date.now()}_${crypto.randomBytes(5).toString("hex")}`;
  const licenseId = `lic_${crypto.randomUUID()}`;
  const licenseKey = generateLicenseKey();
  const paymentType = normalizeZpayType(req.body.type || loadZpayConfig().defaultType);
  const claimUrl = `${publicBaseUrl}/promotion-manager/checkout/success?orderNo=${encodeURIComponent(orderNo)}`;
  const request = buildZpayPaymentRequest({
    config: loadZpayConfig(),
    paymentId,
    orderNo,
    plan,
    type: paymentType,
    amount,
    clientIp: requestIp(req),
    notifyUrl: `${publicBaseUrl}/api/promotion-manager/webhooks/zpay`,
    returnUrl: claimUrl
  });
  const providerResponse = await requestZpayPayment(request);
  if (String(providerResponse.code) !== "1") {
    return res.status(502).json({
      error: "zpay_checkout_failed",
      message: String(providerResponse.msg || "ZPAY rejected the payment request.")
    });
  }
  const destination = String(
    providerResponse.payurl || providerResponse.payurl2 || providerResponse.qrcode || providerResponse.img || ""
  );
  if (!/^https?:\/\//i.test(destination)) {
    return res.status(502).json({ error: "zpay_checkout_missing_destination" });
  }

  await store.update((state) => {
    const account = accountForEmail(state, email);
    state.licenses[licenseId] = {
      id: licenseId,
      accountId: account.id,
      licenseKeyHash: hashLicenseKey(licenseKey),
      status: "pending_payment",
      plan,
      creditsRemaining: 0,
      renewsAt: "",
      paymentProvider: "zpay",
      createdAt: nowIso(),
      updatedAt: nowIso()
    };
    state.payments[paymentId] = {
      id: paymentId,
      orderNo,
      accountId: account.id,
      licenseId,
      provider: "zpay",
      providerTradeNo: String(providerResponse.trade_no || ""),
      status: "pending",
      plan,
      amount,
      currency: "CNY",
      paymentType,
      createdAt: nowIso(),
      updatedAt: nowIso()
    };
    audit(state, "zpay_checkout_created", { paymentId, licenseId, plan, amount, paymentType });
  });

  res.cookie("enhe_pm_claim", licenseKey, {
    httpOnly: true,
    secure: publicBaseUrl.startsWith("https://"),
    sameSite: "lax",
    maxAge: 24 * 60 * 60 * 1000,
    path: "/promotion-manager"
  });
  const wantsJson = String(req.get("accept") || "").toLowerCase().includes("application/json");
  if (!wantsJson) return res.redirect(303, destination);

  const qrCodeDataUrl = await QRCode.toDataURL(destination, {
    errorCorrectionLevel: "M",
    margin: 2,
    width: 280
  });
  return res.status(201).json({
    orderNo,
    plan,
    amount,
    termDays: loadZpayConfig().licenseDays,
    paymentType,
    paymentUrl: destination,
    qrCodeDataUrl,
    claimUrl
  });
}));

app.get("/api/promotion-manager/payments/zpay/status", asyncHandler(async (req, res) => {
  const orderNo = String(req.query.orderNo || "").trim();
  const state = await store.load();
  const payment = Object.values(state.payments).find((item) => item.orderNo === orderNo);
  if (!payment) return res.status(404).json({ error: "payment_not_found" });

  const license = state.licenses[payment.licenseId];
  const claim = cookieValue(req.headers.cookie, "enhe_pm_claim");
  if (!license || !claim || hashLicenseKey(claim) !== license.licenseKeyHash) {
    return res.status(403).json({ error: "payment_claim_mismatch" });
  }

  const status = payment.status === "paid"
    ? "paid"
    : payment.status === "failed" ? "failed" : "pending";
  const claimUrl = status === "paid"
    ? `${publicBaseUrl}/promotion-manager/checkout/success?orderNo=${encodeURIComponent(orderNo)}`
    : "";
  return res.json({ orderNo, status, claimUrl });
}));

app.get("/promotion-manager/checkout/success", asyncHandler(async (req, res) => {
  const state = await store.load();
  const orderNo = String(req.query.orderNo || "");
  const payment = Object.values(state.payments).find((item) => item.orderNo === orderNo);
  if (!payment) return res.status(404).type("html").send(renderCheckoutResult("paymentNotFound"));
  if (payment.status !== "paid") {
    return res.type("html").send(renderCheckoutResult("paymentPending"));
  }
  const license = state.licenses[payment.licenseId];
  const claim = cookieValue(req.headers.cookie, "enhe_pm_claim");
  if (!license || !claim || hashLicenseKey(claim) !== license.licenseKeyHash) {
    return res.status(403).type("html").send(renderCheckoutResult("claimUnavailable"));
  }
  return res.type("html").send(renderCheckoutResult("paymentConfirmed", { licenseKey: claim }));
}));

app.get("/promotion-manager/billing", asyncHandler(async (req, res) => {
  if (isZpayConfigured()) {
    return res.type("html").send(renderCheckoutResult("billing"));
  }
  const error = requireStripeConfig(["STRIPE_SECRET_KEY"]);
  if (error) return res.status(500).json(error);

  const state = await store.load();
  const customerId = String(req.query.customerId || "").trim() || customerIdFromLicense(state, req.query.licenseKey);
  if (!customerId) {
    return res.status(400).json({ error: "missing_customer", message: "Provide customerId or a valid licenseKey." });
  }

  try {
    const session = await stripe.billingPortal.sessions.create({
      customer: customerId,
      return_url: `${publicBaseUrl}/promotion-manager`
    });
    return res.redirect(303, session.url);
  } catch (error) {
    return res.status(502).json({ error: "stripe_portal_failed", message: error.message });
  }
}));

app.get("/promotion-manager/:page(privacy|terms|refund|support)", asyncHandler(async (req, res) => {
  return res.type("html").send(renderLegalPage(req.params.page));
}));

app.get("/promotion-manager/runs/:runId", asyncHandler(async (req, res) => {
  const state = await store.load();
  const run = state.hostedRuns[String(req.params.runId || "")];
  if (!run) {
    return res.status(404).send("<!doctype html><title>Run not found</title><h1>Run not found</h1>");
  }
  return res.type("html").send(renderRunPage(run));
}));

app.post("/api/promotion-manager/license", asyncHandler(async (req, res) => {
  const state = await store.load();
  const license = findLicenseByKey(state, req.body.licenseKey);
  if (!license) {
    return res.json(licenseResponse(null, false, "license_not_found"));
  }
  const active = isLicenseActive(license);
  return res.json(licenseResponse(license, active, active ? "ok" : "inactive_license"));
}));

app.post("/api/promotion-manager/usage/authorize", asyncHandler(async (req, res) => {
  const response = await store.update((state) => {
    const license = findLicenseByKey(state, req.body.licenseKey);
    if (!license || !isLicenseActive(license)) {
      return { status: 403, body: { allowed: false, reason: "inactive_license" } };
    }

    const workflowType = normalizeWorkflow(req.body.workflowType);
    const idempotencyKey = String(req.body.idempotencyKey || "").trim();
    if (!idempotencyKey) {
      return { status: 400, body: { allowed: false, reason: "missing_idempotency_key" } };
    }

    const existing = Object.values(state.usageLedger).find(
      (item) => item.licenseId === license.id && item.idempotencyKey === idempotencyKey
    );
    if (existing) {
      return { status: 200, body: usageAuthorizationResponse(existing, license, true, "ok") };
    }

    const estimatedCredits = Number(req.body.estimatedCredits || 0);
    const creditsReserved = Math.max(estimatedCredits, WORKFLOW_CREDIT_COSTS[workflowType] || 0);
    if (creditsReserved > license.creditsRemaining) {
      return {
        status: 402,
        body: {
          allowed: false,
          reason: "quota_exceeded",
          creditsReserved,
          creditsRemaining: license.creditsRemaining
        }
      };
    }

    const usage = {
      id: `usage_${crypto.randomUUID()}`,
      licenseId: license.id,
      licenseKeyHash: license.licenseKeyHash,
      workflowType,
      commandType: String(req.body.commandType || ""),
      idempotencyKey,
      creditsReserved,
      creditsUsed: 0,
      status: "reserved",
      createdAt: nowIso(),
      updatedAt: nowIso()
    };
    license.creditsRemaining -= creditsReserved;
    license.updatedAt = nowIso();
    state.usageLedger[usage.id] = usage;
    audit(state, "usage_authorized", { usageId: usage.id, workflowType, creditsReserved });
    return { status: 200, body: usageAuthorizationResponse(usage, license, true, "ok") };
  });
  return res.status(response.status).json(response.body);
}));

app.get("/api/promotion-manager/run/:runId", asyncHandler(async (req, res) => {
  const state = await store.load();
  const run = state.hostedRuns[String(req.params.runId || "")];
  if (!run) {
    return res.status(404).json({ error: "run_not_found" });
  }
  return res.json(runStatusResponse(run));
}));

app.post("/api/promotion-manager/run", asyncHandler(async (req, res) => {
  const response = await store.update((state) => {
    const license = findLicenseByKey(state, req.body.licenseKey);
    if (!license || !isLicenseActive(license)) {
      return { status: 403, body: hostedRunResponse(false, "", "blocked", "inactive_license") };
    }

    const workflowType = normalizeWorkflow(req.body.workflowType);
    const expectedCredits = WORKFLOW_CREDIT_COSTS[workflowType] || 0;
    const safetyError = validateHostedRunSafety(req.body.safety);
    if (safetyError) {
      return { status: 400, body: hostedRunResponse(false, "", "blocked", safetyError) };
    }

    const usage = state.usageLedger[String(req.body.usageId || "")];
    if (expectedCredits > 0) {
      const usageError = validateUsageForHostedRun(usage, license, workflowType, expectedCredits);
      if (usageError) {
        return { status: 402, body: hostedRunResponse(false, "", "blocked", usageError) };
      }
    }

    const idempotencyKey = String(req.body.idempotencyKey || "").trim();
    const duplicate = Object.values(state.hostedRuns).find(
      (item) => item.licenseId === license.id && idempotencyKey && item.idempotencyKey === idempotencyKey
    );
    if (duplicate) {
      return { status: 200, body: hostedRunResponse(true, duplicate.id, duplicate.status, "ok") };
    }

    const runId = `run_${crypto.randomUUID()}`;
    const run = {
      id: runId,
      usageId: usage ? usage.id : "",
      licenseId: license.id,
      workflowType,
      commandType: String(req.body.commandType || "skill_entry"),
      estimatedCredits: expectedCredits,
      productUrl: String(req.body.productUrl || ""),
      platforms: Array.isArray(req.body.platforms) ? req.body.platforms.map(String) : [],
      workflowDepth: String(req.body.workflowDepth || "full"),
      localCommand: String(req.body.localCommand || ""),
      options: req.body.options && typeof req.body.options === "object" ? req.body.options : {},
      idempotencyKey,
      requestSource: String(req.body.requestSource || ""),
      status: "queued",
      createdAt: nowIso(),
      updatedAt: nowIso()
    };
    state.hostedRuns[runId] = run;
    audit(state, "hosted_run_queued", { runId, usageId: run.usageId, workflowType, commandType: run.commandType });
    return { status: 200, body: hostedRunResponse(true, runId, "queued", "ok") };
  });
  return res.status(response.status).json(response.body);
}));

app.post("/api/promotion-manager/usage/commit", asyncHandler(async (req, res) => {
  const response = await store.update((state) => {
    const usage = state.usageLedger[String(req.body.usageId || "")];
    if (!usage) {
      return { status: 404, body: { status: "failed", reason: "usage_not_found" } };
    }
    const result = commitUsage(state, usage.id, {
      inputTokens: Number(req.body.inputTokens || 0),
      outputTokens: Number(req.body.outputTokens || 0),
      videoSecondsRendered: Number(req.body.videoSecondsRendered || 0),
      creditsUsed: Math.max(0, Number(req.body.creditsUsed || 0)),
      status: String(req.body.status || "succeeded")
    });
    audit(state, "usage_committed", result);
    return { status: 200, body: result };
  });
  return res.status(response.status).json(response.body);
}));

function asyncHandler(handler) {
  return (req, res, next) => Promise.resolve(handler(req, res, next)).catch(next);
}

function requireStripeConfig(keys) {
  const missing = keys.filter((key) => !process.env[key]);
  if (missing.length > 0 || !stripe) {
    return { error: "missing_stripe_config", missing };
  }
  return null;
}

function loadState(file = stateFile) {
  return loadJsonState(file);
}

function saveState(state, file = stateFile) {
  saveJsonState(file, state);
}

function handleStripeEvent(state, event) {
  const object = event.data.object;
  if (event.type === "checkout.session.completed") {
    return handleCheckoutCompleted(state, object);
  }
  if (event.type === "customer.subscription.created" || event.type === "customer.subscription.updated") {
    return handleSubscriptionUpsert(state, object);
  }
  if (event.type === "customer.subscription.deleted") {
    return handleSubscriptionDeleted(state, object);
  }
  if (event.type === "invoice.payment_succeeded") {
    return handleInvoicePaymentSucceeded(state, object);
  }
  if (event.type === "invoice.payment_failed") {
    return handleInvoicePaymentFailed(state, object);
  }
  if (event.type === "entitlements.active_entitlement_summary.updated") {
    return { status: "recorded_entitlement_refresh" };
  }
  return { status: "ignored" };
}

function handleCheckoutCompleted(state, session) {
  const plan = normalizePlan(session.metadata && session.metadata.plan);
  const account = accountForCustomer(state, session.customer, session.customer_details && session.customer_details.email);
  const licenseKey = generateLicenseKey();
  const licenseId = `lic_${crypto.randomUUID()}`;
  state.licenses[licenseId] = {
    id: licenseId,
    accountId: account.id,
    licenseKeyHash: hashLicenseKey(licenseKey),
    status: "active",
    plan,
    creditsRemaining: PLAN_CREDITS[plan],
    renewsAt: dateFromUnix(session.expires_at) || "",
    stripeCustomerId: String(session.customer || ""),
    stripeSubscriptionId: String(session.subscription || ""),
    createdAt: nowIso(),
    updatedAt: nowIso()
  };
  state.stripeCustomers[String(session.customer || "")] = account.id;
  return { status: "license_issued_hashed", plan, licenseId };
}

function handleSubscriptionUpsert(state, subscription) {
  const plan = planFromSubscription(subscription);
  const record = {
    id: String(subscription.id || ""),
    provider: "stripe",
    providerCustomerId: String(subscription.customer || ""),
    providerSubscriptionId: String(subscription.id || ""),
    status: String(subscription.status || ""),
    plan,
    priceId: priceIdFromSubscription(subscription),
    currentPeriodEnd: dateFromUnix(subscription.current_period_end),
    updatedAt: nowIso()
  };
  state.subscriptions[record.providerSubscriptionId] = record;
  for (const license of Object.values(state.licenses)) {
    if (license.stripeSubscriptionId === record.providerSubscriptionId) {
      license.plan = plan;
      license.status = subscriptionStatusToLicenseStatus(record.status);
      license.renewsAt = record.currentPeriodEnd;
      license.updatedAt = nowIso();
    }
  }
  return { status: "subscription_upserted", subscriptionId: record.providerSubscriptionId, plan };
}

function handleSubscriptionDeleted(state, subscription) {
  const subscriptionId = String(subscription.id || "");
  if (state.subscriptions[subscriptionId]) {
    state.subscriptions[subscriptionId].status = "deleted";
    state.subscriptions[subscriptionId].updatedAt = nowIso();
  }
  for (const license of Object.values(state.licenses)) {
    if (license.stripeSubscriptionId === subscriptionId) {
      license.status = "inactive";
      license.updatedAt = nowIso();
    }
  }
  return { status: "subscription_deleted", subscriptionId };
}

function handleInvoicePaymentSucceeded(state, invoice) {
  const subscriptionId = String(invoice.subscription || "");
  let renewed = 0;
  for (const license of Object.values(state.licenses)) {
    if (license.stripeSubscriptionId === subscriptionId) {
      license.status = "active";
      license.creditsRemaining = PLAN_CREDITS[license.plan] || license.creditsRemaining;
      license.renewsAt = dateFromUnix(
        invoice.lines && invoice.lines.data && invoice.lines.data[0] && invoice.lines.data[0].period && invoice.lines.data[0].period.end
      ) || license.renewsAt;
      license.updatedAt = nowIso();
      renewed += 1;
    }
  }
  return { status: "invoice_payment_succeeded", subscriptionId, renewedLicenses: renewed };
}

function handleInvoicePaymentFailed(state, invoice) {
  const subscriptionId = String(invoice.subscription || "");
  for (const license of Object.values(state.licenses)) {
    if (license.stripeSubscriptionId === subscriptionId) {
      license.status = "past_due";
      license.updatedAt = nowIso();
    }
  }
  return { status: "invoice_payment_failed", subscriptionId };
}

function accountForCustomer(state, customerId, email) {
  const key = String(customerId || "");
  if (key && state.stripeCustomers[key] && state.accounts[state.stripeCustomers[key]]) {
    return state.accounts[state.stripeCustomers[key]];
  }
  const account = {
    id: `acct_${crypto.randomUUID()}`,
    email: String(email || ""),
    stripeCustomerId: key,
    createdAt: nowIso()
  };
  state.accounts[account.id] = account;
  if (key) state.stripeCustomers[key] = account.id;
  return account;
}

function accountForEmail(state, email) {
  const normalizedEmail = String(email || "").trim().toLowerCase();
  const existing = Object.values(state.accounts).find(
    (account) => String(account.email || "").trim().toLowerCase() === normalizedEmail
  );
  if (existing) return existing;
  const account = {
    id: `acct_${crypto.randomUUID()}`,
    email: normalizedEmail,
    createdAt: nowIso()
  };
  state.accounts[account.id] = account;
  return account;
}

function findLicenseByKey(state, licenseKey) {
  if (!licenseKey) return null;
  const licenseKeyHash = hashLicenseKey(String(licenseKey));
  return Object.values(state.licenses).find((license) => license.licenseKeyHash === licenseKeyHash) || null;
}

function hashLicenseKey(licenseKey) {
  const pepper = process.env.LICENSE_PEPPER;
  if (!pepper) {
    throw new Error("LICENSE_PEPPER is required before handling license keys.");
  }
  return crypto.createHash("sha256").update(`${pepper}:${licenseKey}`).digest("hex");
}

function generateLicenseKey() {
  return `pm_live_${crypto.randomBytes(24).toString("hex")}`;
}

function isLicenseActive(license) {
  return ["active", "trialing"].includes(String(license.status || "")) && Number(license.creditsRemaining || 0) >= 0;
}

function licenseResponse(license, active, reason) {
  const plan = normalizePlan(license && license.plan);
  return {
    active,
    reason,
    plan: labelPlan(plan),
    creditsRemaining: license ? Number(license.creditsRemaining || 0) : 0,
    renewsAt: license ? String(license.renewsAt || "") : "",
    checkoutUrl: `${publicBaseUrl}/promotion-manager/checkout`,
    customerPortalUrl: `${publicBaseUrl}/promotion-manager/billing`,
    hostedRunEndpoint: `${publicBaseUrl}/api/promotion-manager/run`
  };
}

function usageAuthorizationResponse(usage, license, allowed, reason) {
  return {
    allowed,
    usageId: usage.id,
    creditsReserved: usage.creditsReserved,
    creditsRemainingAfterReservation: license.creditsRemaining,
    reason
  };
}

function hostedRunResponse(accepted, runId, status, reason) {
  return {
    accepted,
    runId,
    status,
    dashboardUrl: runId ? `${publicBaseUrl}/promotion-manager/runs/${runId}` : "",
    statusUrl: runId ? `${publicBaseUrl}/api/promotion-manager/run/${runId}` : "",
    reportUrl: "",
    reason
  };
}

function runStatusResponse(run) {
  return {
    runId: run.id,
    workflowType: run.workflowType,
    commandType: run.commandType,
    status: run.status,
    reason: run.reason || "",
    productUrl: run.productUrl || "",
    platforms: run.platforms || [],
    createdAt: run.createdAt || "",
    startedAt: run.startedAt || "",
    finishedAt: run.finishedAt || "",
    dashboardUrl: `${publicBaseUrl}/promotion-manager/runs/${run.id}`,
    reportUrl: run.reportUrl || "",
    artifactDirectory: run.artifactDirectory || ""
  };
}

function renderRunPage(run) {
  const status = escapeHtml(run.status || "unknown");
  const runId = escapeHtml(run.id || "");
  const productUrl = escapeHtml(run.productUrl || "");
  const reason = escapeHtml(run.reason || "");
  const artifacts = escapeHtml(run.artifactDirectory || "");
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ENHE Product Promo Maker Run ${runId}</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 760px; margin: 40px auto; padding: 0 20px; line-height: 1.5; }
    code { background: #f4f4f5; padding: 2px 4px; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>Hosted Run ${runId}</h1>
  <p>Status: <strong>${status}</strong></p>
  <p>Product URL: <code>${productUrl}</code></p>
  <p>Reason: ${reason || "ok"}</p>
  <p>Artifacts: <code>${artifacts}</code></p>
  <p>JSON status: <a href="/api/promotion-manager/run/${runId}">/api/promotion-manager/run/${runId}</a></p>
</body>
</html>`;
}

function renderZpayCheckoutPage(selectedPlan) {
  const planOptions = ["starter", "growth", "scale"]
    .map((plan) => {
      const price = zpayPriceForPlan(plan);
      const displayPrice = String(price || "").replace(/\.00$/, "");
      const label = `${labelPlan(plan)}${price ? ` - ¥${displayPrice}` : " - unavailable"}`;
      return `<option value="${plan}"${plan === selectedPlan ? " selected" : ""}${price ? "" : " disabled"}>${escapeHtml(label)}</option>`;
    })
    .join("");
  const messages = {
    "zh-CN": {
      title: "ENHE 产品推广素材生成器 国内支付",
      intro: "使用微信支付或支付宝购买 30 天许可证。",
      plan: "套餐",
      email: "接收与找回许可证的邮箱",
      paymentMethod: "支付方式",
      wechat: "微信支付",
      alipay: "支付宝",
      submitPayment: "前往支付",
      creatingOrder: "正在创建订单…",
      scanToPay: "请使用手机扫码支付",
      waitingForPayment: "等待支付确认…",
      paymentConfirmed: "支付成功，正在领取许可证…",
      paymentFailed: "支付未完成，请重试或直接打开支付页面。",
      openPaymentPage: "直接打开支付页面",
      orderNumber: "订单号",
      privacyHint: "支付由 ENHE AI 的 ZPAY 商户通道处理。许可证密钥不会以明文存储在服务器。"
    },
    en: {
      title: "ENHE Product Promo Maker Checkout",
      intro: "Buy a 30-day license with WeChat Pay or Alipay.",
      plan: "Plan",
      email: "Email for license delivery and recovery",
      paymentMethod: "Payment method",
      wechat: "WeChat Pay",
      alipay: "Alipay",
      submitPayment: "Continue to payment",
      creatingOrder: "Creating order…",
      scanToPay: "Scan with your phone to pay",
      waitingForPayment: "Waiting for payment confirmation…",
      paymentConfirmed: "Payment confirmed. Opening your license…",
      paymentFailed: "Payment was not completed. Retry or open the payment page directly.",
      openPaymentPage: "Open payment page",
      orderNumber: "Order number",
      privacyHint: "Payment is processed through ENHE AI's ZPAY merchant channel. License Keys are not stored in plaintext."
    }
  };
  return `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ENHE 产品推广素材生成器 国内支付</title>
  <style>
    :root { color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, sans-serif; color: #18181b; background: #f6f7fb; }
    * { box-sizing: border-box; }
    body { max-width: 760px; margin: 0 auto; padding: 32px 20px 64px; line-height: 1.6; }
    main { display: grid; gap: 22px; }
    .toolbar { display: flex; justify-content: flex-end; align-items: center; gap: 8px; color: #52525b; font-size: 14px; }
    .language-button { padding: 5px 10px; border: 1px solid #d4d4d8; border-radius: 999px; background: white; color: #27272a; }
    .language-button[aria-pressed="true"] { border-color: #111827; background: #111827; color: white; }
    .card { padding: 28px; border: 1px solid #e4e4e7; border-radius: 18px; background: white; box-shadow: 0 16px 50px rgba(15, 23, 42, 0.08); }
    h1, h2, p { margin-top: 0; }
    form { display: grid; gap: 16px; }
    label { display: grid; gap: 6px; font-weight: 600; }
    input, select, button, a { font: inherit; }
    input, select { width: 100%; padding: 11px 12px; border: 1px solid #d4d4d8; border-radius: 9px; background: white; }
    button { cursor: pointer; border: 0; }
    .primary { padding: 12px 16px; border-radius: 9px; background: #111827; color: white; font-weight: 700; }
    .primary:disabled { cursor: wait; opacity: 0.65; }
    .payment-panel { text-align: center; }
    .payment-panel img { display: block; width: 280px; height: 280px; max-width: 100%; margin: 18px auto; border: 1px solid #e4e4e7; border-radius: 12px; }
    .payment-summary { font-weight: 700; }
    .direct-link { display: inline-flex; margin-top: 12px; color: #0f766e; font-weight: 700; }
    .hint { color: #52525b; font-size: 14px; }
    code { word-break: break-all; }
    [hidden] { display: none !important; }
    @media (max-width: 560px) { body { padding: 20px 14px 48px; } .card { padding: 20px; } }
  </style>
</head>
<body>
  <main>
    <div class="toolbar" aria-label="Language">
      <span>中文 / EN</span>
      <button class="language-button" type="button" data-language="zh-CN">中文</button>
      <button class="language-button" type="button" data-language="en">EN</button>
    </div>
    <section class="card">
      <h1 data-i18n="title">ENHE 产品推广素材生成器 国内支付</h1>
      <p data-i18n="intro">使用微信支付或支付宝购买 30 天许可证。</p>
      <form id="checkoutForm" method="post" action="/api/promotion-manager/payments/zpay/checkout">
        <label><span data-i18n="plan">套餐</span><select name="plan" required>${planOptions}</select></label>
        <label><span data-i18n="email">接收与找回许可证的邮箱</span><input type="email" name="email" autocomplete="email" required></label>
        <label><span data-i18n="paymentMethod">支付方式</span>
          <select name="type" required>
            <option value="wxpay" data-i18n="wechat">微信支付</option>
            <option value="alipay" data-i18n="alipay">支付宝</option>
          </select>
        </label>
        <button id="submitButton" class="primary" type="submit" data-i18n="submitPayment">前往支付</button>
      </form>
      <p class="hint" data-i18n="privacyHint">支付由 ENHE AI 的 ZPAY 商户通道处理。许可证密钥不会以明文存储在服务器。</p>
    </section>
    <section id="paymentPanel" class="card payment-panel" hidden aria-live="polite">
      <h2 data-i18n="scanToPay">请使用手机扫码支付</h2>
      <p id="paymentSummary" class="payment-summary"></p>
      <img id="paymentQr" alt="Payment QR code" width="280" height="280">
      <p id="paymentStatus" data-i18n="waitingForPayment">等待支付确认…</p>
      <p><span data-i18n="orderNumber">订单号</span>：<code id="orderNumber"></code></p>
      <a id="openPaymentPage" class="direct-link" target="_blank" rel="noopener noreferrer" data-i18n="openPaymentPage">直接打开支付页面</a>
    </section>
  </main>
  <script>
    (() => {
      const messages = ${JSON.stringify(messages).replace(/</g, "\\u003c")};
      const languageKey = "enhe_pm_language";
      const form = document.getElementById("checkoutForm");
      const submitButton = document.getElementById("submitButton");
      const paymentPanel = document.getElementById("paymentPanel");
      const paymentQr = document.getElementById("paymentQr");
      const paymentSummary = document.getElementById("paymentSummary");
      const paymentStatus = document.getElementById("paymentStatus");
      const orderNumber = document.getElementById("orderNumber");
      const openPaymentPage = document.getElementById("openPaymentPage");
      const storedLanguage = localStorage.getItem("enhe_pm_language");
      let language = storedLanguage || (navigator.language.toLowerCase().startsWith("zh") ? "zh-CN" : "en");
      let statusKey = "waitingForPayment";
      let pollTimer = 0;
      let pollDeadline = 0;
      const mobile = navigator.userAgentData && typeof navigator.userAgentData.mobile === "boolean"
        ? navigator.userAgentData.mobile
        : /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);

      function applyLanguage(nextLanguage) {
        language = nextLanguage === "zh-CN" ? "zh-CN" : "en";
        localStorage.setItem(languageKey, language);
        document.documentElement.lang = language;
        document.querySelectorAll("[data-i18n]").forEach((element) => {
          const key = element.dataset.i18n;
          if (messages[language][key]) element.textContent = messages[language][key];
        });
        document.querySelectorAll("[data-language]").forEach((button) => {
          button.setAttribute("aria-pressed", String(button.dataset.language === language));
        });
        paymentStatus.textContent = messages[language][statusKey];
      }

      function setStatus(key) {
        statusKey = key;
        paymentStatus.textContent = messages[language][key];
      }

      function stopPolling() {
        if (pollTimer) window.clearInterval(pollTimer);
        pollTimer = 0;
      }

      async function checkPayment(orderNoValue) {
        if (document.hidden) return;
        if (Date.now() >= pollDeadline) {
          stopPolling();
          setStatus("paymentFailed");
          return;
        }
        const response = await fetch(
          "/api/promotion-manager/payments/zpay/status?orderNo=" + encodeURIComponent(orderNoValue),
          { credentials: "same-origin" }
        );
        if (!response.ok) return;
        const body = await response.json();
        if (body.status === "paid" && body.claimUrl) {
          stopPolling();
          setStatus("paymentConfirmed");
          location.assign(body.claimUrl);
        } else if (body.status === "failed") {
          stopPolling();
          setStatus("paymentFailed");
        }
      }

      document.querySelectorAll("[data-language]").forEach((button) => {
        button.addEventListener("click", () => applyLanguage(button.dataset.language));
      });
      window.addEventListener("beforeunload", stopPolling);
      document.addEventListener("visibilitychange", () => {
        if (!document.hidden && orderNumber.textContent && pollTimer) checkPayment(orderNumber.textContent);
      });

      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        stopPolling();
        submitButton.disabled = true;
        submitButton.textContent = messages[language].creatingOrder;
        try {
          const response = await fetch(form.action, {
            method: "POST",
            headers: { accept: "application/json" },
            body: new URLSearchParams(new FormData(form)),
            credentials: "same-origin"
          });
          const body = await response.json();
          if (!response.ok) throw new Error(body.message || body.error || "checkout_failed");
          if (mobile) {
            location.assign(body.paymentUrl);
            return;
          }
          paymentQr.src = body.qrCodeDataUrl;
          paymentSummary.textContent = labelPlan(body.plan) + " · ¥" + String(body.amount).replace(/\\.00$/, "") + " · 30 days";
          orderNumber.textContent = body.orderNo;
          openPaymentPage.href = body.paymentUrl;
          paymentPanel.hidden = false;
          setStatus("waitingForPayment");
          pollDeadline = Date.now() + 10 * 60 * 1_000;
          await checkPayment(body.orderNo);
          pollTimer = window.setInterval(() => checkPayment(body.orderNo), 3_000);
        } catch (_error) {
          paymentPanel.hidden = false;
          setStatus("paymentFailed");
        } finally {
          submitButton.disabled = false;
          submitButton.textContent = messages[language].submitPayment;
        }
      });

      function labelPlan(plan) {
        const value = String(plan || "");
        return value.charAt(0).toUpperCase() + value.slice(1);
      }

      applyLanguage(language);
    })();
  </script>
</body>
</html>`;
}

function renderCheckoutResult(resultKey, options = {}) {
  const messages = {
    paymentNotFound: {
      en: { title: "Payment not found", message: "Check the order link or return to checkout." },
      zh: { title: "未找到支付订单", message: "请检查订单链接或返回结算页。" }
    },
    paymentPending: {
      en: { title: "Payment is being confirmed", message: "Refresh this page in a moment." },
      zh: { title: "正在确认支付", message: "请稍后刷新此页面。" }
    },
    paymentConfirmed: {
      en: { title: "Payment confirmed", message: "" },
      zh: { title: "支付已确认", message: "" }
    },
    claimUnavailable: {
      en: {
        title: "Payment confirmed",
        message: "The license claim is unavailable in this browser. Contact support with your order number."
      },
      zh: { title: "支付已确认", message: "当前浏览器无法领取许可证，请携带订单号联系支持。" }
    },
    billing: {
      en: {
        title: "ENHE Product Promo Maker billing",
        message: "Domestic plans use one-time 30-day payments. Renew or change plans from checkout."
      },
      zh: {
        title: "ENHE 产品推广素材生成器 账单",
        message: "国内套餐采用一次性购买 30 天许可证，请在结算页续购或更换套餐。"
      }
    }
  };
  const content = messages[resultKey] || messages.paymentNotFound;
  const licenseKey = String(options.licenseKey || "");
  const resultPanel = (language, productName, title, message, backLabel, licenseLabel, hidden) => `
    <section data-language-panel="${language}"${hidden ? " hidden" : ""}>
      <p class="product-name">${escapeHtml(productName)}</p>
      <h1>${escapeHtml(title)}</h1>
      ${licenseKey
        ? `<p>${escapeHtml(licenseLabel)}</p><p><code>${escapeHtml(licenseKey)}</code></p>`
        : `<p>${escapeHtml(message)}</p>`}
      <p><a href="/promotion-manager/checkout">${escapeHtml(backLabel)}</a></p>
    </section>`;
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(content.en.title)}</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 680px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #18181b; }
    .toolbar { display: flex; justify-content: flex-end; align-items: center; gap: 8px; margin-bottom: 24px; color: #52525b; font-size: 14px; }
    button { padding: 5px 10px; border: 1px solid #d4d4d8; border-radius: 999px; background: white; cursor: pointer; }
    button[aria-pressed="true"] { border-color: #111827; background: #111827; color: white; }
    code { word-break: break-all; }
    a { color: #0f766e; }
    [hidden] { display: none !important; }
  </style>
</head>
<body>
  <div class="toolbar"><span>中文 / EN</span><button type="button" data-language="zh-CN">中文</button><button type="button" data-language="en">EN</button></div>
  ${resultPanel("en", "ENHE Product Promo Maker", content.en.title, content.en.message, "Return to checkout", "License key", false)}
  ${resultPanel("zh-CN", "ENHE 产品推广素材生成器", content.zh.title, content.zh.message, "返回结算页", "许可证密钥", true)}
  ${renderLanguageToggleScript()}
</body>
</html>`;
}

function renderLegalPage(page) {
  const filename = LEGAL_PAGES[page];
  const pagePath = path.join(__dirname, "..", "..", "..", "docs", "legal", filename);
  if (!filename || !fs.existsSync(pagePath)) {
    return "<!doctype html><title>Page not found</title><h1>Page not found</h1>";
  }
  const markdown = fs.readFileSync(pagePath, "utf8");
  const title = firstHeading(markdown) || "ENHE Product Promo Maker";
  if (page === "privacy") {
    const chinesePath = path.join(__dirname, "..", "..", "..", "docs", "legal", "privacy-policy.zh-CN.md");
    const chineseMarkdown = fs.readFileSync(chinesePath, "utf8");
    return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(title)}</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 820px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #18181b; }
    .toolbar { position: sticky; top: 0; display: flex; justify-content: flex-end; align-items: center; gap: 8px; padding: 12px 0; background: rgba(255, 255, 255, 0.95); color: #52525b; font-size: 14px; }
    button { padding: 5px 10px; border: 1px solid #d4d4d8; border-radius: 999px; background: white; cursor: pointer; }
    button[aria-pressed="true"] { border-color: #111827; background: #111827; color: white; }
    h1, h2 { line-height: 1.2; }
    a { color: #0f766e; }
    code { background: #f4f4f5; padding: 2px 4px; border-radius: 4px; }
    [hidden] { display: none !important; }
  </style>
</head>
<body>
  <div class="toolbar"><span>中文 / EN</span><button type="button" data-language="zh-CN">中文</button><button type="button" data-language="en">EN</button></div>
  <article data-language-panel="en">${markdownToHtml(markdown)}</article>
  <article data-language-panel="zh-CN" hidden>${markdownToHtml(chineseMarkdown)}</article>
  ${renderLanguageToggleScript()}
</body>
</html>`;
  }
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(title)}</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 820px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #18181b; }
    h1, h2 { line-height: 1.2; }
    a { color: #0f766e; }
    code { background: #f4f4f5; padding: 2px 4px; border-radius: 4px; }
  </style>
</head>
<body>
${markdownToHtml(markdown)}
</body>
</html>`;
}

function renderLanguageToggleScript() {
  return `<script>
    (() => {
      const languageKey = "enhe_pm_language";
      const storedLanguage = localStorage.getItem(languageKey);
      let language = storedLanguage || (navigator.language.toLowerCase().startsWith("zh") ? "zh-CN" : "en");
      function applyLanguage(nextLanguage) {
        language = nextLanguage === "zh-CN" ? "zh-CN" : "en";
        localStorage.setItem(languageKey, language);
        document.documentElement.lang = language;
        document.querySelectorAll("[data-language-panel]").forEach((panel) => {
          panel.hidden = panel.dataset.languagePanel !== language;
        });
        document.querySelectorAll("[data-language]").forEach((button) => {
          button.setAttribute("aria-pressed", String(button.dataset.language === language));
        });
      }
      document.querySelectorAll("[data-language]").forEach((button) => {
        button.addEventListener("click", () => applyLanguage(button.dataset.language));
      });
      applyLanguage(language);
    })();
  </script>`;
}

function firstHeading(markdown) {
  const line = String(markdown).split(/\r?\n/).find((item) => item.startsWith("# "));
  return line ? line.replace(/^#\s+/, "").trim() : "";
}

function markdownToHtml(markdown) {
  const html = [];
  let inList = false;
  for (const rawLine of String(markdown).split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) {
      if (inList) {
        html.push("</ul>");
        inList = false;
      }
      continue;
    }
    if (line.startsWith("## ")) {
      if (inList) {
        html.push("</ul>");
        inList = false;
      }
      html.push(`<h2>${escapeHtml(line.slice(3))}</h2>`);
      continue;
    }
    if (line.startsWith("# ")) {
      if (inList) {
        html.push("</ul>");
        inList = false;
      }
      html.push(`<h1>${escapeHtml(line.slice(2))}</h1>`);
      continue;
    }
    if (line.startsWith("- ")) {
      if (!inList) {
        html.push("<ul>");
        inList = true;
      }
      html.push(`<li>${linkify(escapeHtml(line.slice(2)))}</li>`);
      continue;
    }
    if (inList) {
      html.push("</ul>");
      inList = false;
    }
    html.push(`<p>${linkify(escapeHtml(line))}</p>`);
  }
  if (inList) html.push("</ul>");
  return html.join("\n");
}

function linkify(value) {
  return value.replace(/https:\/\/[^\s<]+/g, (url) => `<a href="${url}">${url}</a>`);
}

function validateUsageForHostedRun(usage, license, workflowType, expectedCredits) {
  if (!usage) return "missing_usage_reservation";
  if (usage.licenseId !== license.id) return "usage_license_mismatch";
  if (usage.workflowType !== workflowType) return "usage_workflow_mismatch";
  if (usage.status !== "reserved") return "usage_not_reserved";
  if (Number(usage.creditsReserved || 0) < expectedCredits) return "reserved_credits_too_low";
  return "";
}

function validateHostedRunSafety(safety) {
  const required = [
    "approvalRequiredForOfficialPublish",
    "finalPublishNotClickedByExtension",
    "noPlatformSecretsInPayload",
    "noCaptchaBypass"
  ];
  if (!safety || typeof safety !== "object") return "missing_safety_flags";
  const missing = required.filter((key) => safety[key] !== true);
  return missing.length ? `missing_safety_flags:${missing.join(",")}` : "";
}

function customerIdFromLicense(state, licenseKey) {
  try {
    const license = findLicenseByKey(state, licenseKey);
    return license ? String(license.stripeCustomerId || "") : "";
  } catch (_error) {
    return "";
  }
}

function normalizePlan(value) {
  const plan = String(value || "").trim().toLowerCase();
  return Object.prototype.hasOwnProperty.call(PLAN_CREDITS, plan) ? plan : "starter";
}

function normalizeWorkflow(value) {
  const workflowType = String(value || "").trim();
  return Object.prototype.hasOwnProperty.call(WORKFLOW_CREDIT_COSTS, workflowType) ? workflowType : "standard_run";
}

function priceIdForPlan(plan) {
  return process.env[STRIPE_PRICE_ENV_BY_PLAN[plan] || ""];
}

function planFromSubscription(subscription) {
  const priceId = priceIdFromSubscription(subscription);
  for (const [plan, envName] of Object.entries(STRIPE_PRICE_ENV_BY_PLAN)) {
    if (process.env[envName] && process.env[envName] === priceId) return plan;
  }
  return normalizePlan(subscription.metadata && subscription.metadata.plan);
}

function priceIdFromSubscription(subscription) {
  return String(
    subscription &&
      subscription.items &&
      subscription.items.data &&
      subscription.items.data[0] &&
      subscription.items.data[0].price &&
      subscription.items.data[0].price.id || ""
  );
}

function subscriptionStatusToLicenseStatus(status) {
  if (["active", "trialing"].includes(status)) return status;
  if (["past_due", "unpaid", "paused"].includes(status)) return "past_due";
  return "inactive";
}

function labelPlan(plan) {
  return plan.charAt(0).toUpperCase() + plan.slice(1);
}

function dateFromUnix(value) {
  const seconds = Number(value || 0);
  if (!seconds) return "";
  return new Date(seconds * 1000).toISOString().slice(0, 10);
}

function nowIso() {
  return new Date().toISOString();
}

function addDaysIso(days) {
  const value = new Date();
  value.setUTCDate(value.getUTCDate() + Number(days || 0));
  return value.toISOString().slice(0, 10);
}

function requestIp(req) {
  const forwarded = String(req.headers["x-forwarded-for"] || "").split(",")[0].trim();
  return forwarded || req.socket.remoteAddress || "127.0.0.1";
}

function zpayPayloadFromQuery(query) {
  return Object.fromEntries(
    Object.entries(query || {}).map(([key, value]) => [key, Array.isArray(value) ? String(value[0] || "") : String(value || "")])
  );
}

function cookieValue(header, name) {
  for (const part of String(header || "").split(";")) {
    const index = part.indexOf("=");
    if (index < 0 || part.slice(0, index).trim() !== name) continue;
    try {
      return decodeURIComponent(part.slice(index + 1).trim());
    } catch (_error) {
      return "";
    }
  }
  return "";
}

function trimTrailingSlash(value) {
  return String(value).replace(/\/+$/, "");
}

function audit(state, action, details) {
  state.auditLog.push({ at: nowIso(), action, details });
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

app.use((error, _req, res, _next) => {
  console.error(error.stack || error.message);
  res.status(500).json({ error: "internal_server_error", message: error.message });
});

if (require.main === module) {
  store.init().then(() => {
    app.listen(port, () => {
      console.log(`ENHE Product Promo Maker license service listening on ${port}`);
    });
    startRetentionCleanup(store).then(() => {
      console.log("ENHE Product Promo Maker retention cleanup enabled");
    }).catch((error) => {
      console.error(`retention cleanup failed: ${error.stack || error.message}`);
    });
    if (process.env.HOSTED_WORKER_ENABLED === "true") {
      startHostedWorker(store).then(() => {
        console.log("ENHE Product Promo Maker hosted worker enabled in API process");
      });
    }
  }).catch((error) => {
    console.error(error.stack || error.message);
    process.exitCode = 1;
  });
}

module.exports = {
  WORKFLOW_CREDIT_COSTS,
  app,
  emptyState,
  hashLicenseKey,
  loadState,
  saveState,
  store
};
