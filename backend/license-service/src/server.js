"use strict";

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");
const express = require("express");
const Stripe = require("stripe");
require("dotenv").config();

const app = express();
const port = Number(process.env.PORT || 3000);
const publicBaseUrl = trimTrailingSlash(process.env.ENHE_PUBLIC_BASE_URL || "http://localhost:3000");
const stateFile = process.env.LICENSE_SERVICE_STATE_FILE || path.join(__dirname, "..", "var", "license-service-state.json");
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

app.post(
  "/api/promotion-manager/webhooks/stripe",
  express.raw({ type: "application/json" }),
  (req, res) => {
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

    const state = loadState();
    const result = handleStripeEvent(state, event);
    audit(state, "stripe_webhook", { eventId: event.id, eventType: event.type, result });
    saveState(state);
    return res.json({ received: true, event: event.type, result });
  }
);

app.use(express.json({ limit: "1mb" }));

app.get("/health", (_req, res) => {
  res.json({
    ok: true,
    service: "enhe-promotion-manager-license-service",
    stripeConfigured: Boolean(stripe),
    stateFile
  });
});

app.get("/promotion-manager/checkout", async (req, res) => {
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
});

app.get("/promotion-manager/billing", async (req, res) => {
  const error = requireStripeConfig(["STRIPE_SECRET_KEY"]);
  if (error) return res.status(500).json(error);

  const state = loadState();
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
});

app.post("/api/promotion-manager/license", (req, res) => {
  const state = loadState();
  const license = findLicenseByKey(state, req.body.licenseKey);
  if (!license) {
    return res.json(licenseResponse(null, false, "license_not_found"));
  }
  const active = isLicenseActive(license);
  return res.json(licenseResponse(license, active, active ? "ok" : "inactive_license"));
});

app.post("/api/promotion-manager/usage/authorize", (req, res) => {
  const state = loadState();
  const license = findLicenseByKey(state, req.body.licenseKey);
  if (!license || !isLicenseActive(license)) {
    return res.status(403).json({ allowed: false, reason: "inactive_license" });
  }

  const workflowType = normalizeWorkflow(req.body.workflowType);
  const idempotencyKey = String(req.body.idempotencyKey || "").trim();
  if (!idempotencyKey) {
    return res.status(400).json({ allowed: false, reason: "missing_idempotency_key" });
  }

  const existing = Object.values(state.usageLedger).find(
    (item) => item.licenseId === license.id && item.idempotencyKey === idempotencyKey
  );
  if (existing) {
    return res.json(usageAuthorizationResponse(existing, license, true, "ok"));
  }

  const estimatedCredits = Number(req.body.estimatedCredits || 0);
  const creditsReserved = Math.max(estimatedCredits, WORKFLOW_CREDIT_COSTS[workflowType] || 0);
  if (creditsReserved > license.creditsRemaining) {
    return res.status(402).json({
      allowed: false,
      reason: "quota_exceeded",
      creditsReserved,
      creditsRemaining: license.creditsRemaining
    });
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
  state.usageLedger[usage.id] = usage;
  audit(state, "usage_authorized", { usageId: usage.id, workflowType, creditsReserved });
  saveState(state);
  return res.json(usageAuthorizationResponse(usage, license, true, "ok"));
});

app.post("/api/promotion-manager/run", (req, res) => {
  const state = loadState();
  const license = findLicenseByKey(state, req.body.licenseKey);
  if (!license || !isLicenseActive(license)) {
    return res.status(403).json(hostedRunResponse(false, "", "blocked", "inactive_license"));
  }

  const workflowType = normalizeWorkflow(req.body.workflowType);
  const expectedCredits = WORKFLOW_CREDIT_COSTS[workflowType] || 0;
  const safetyError = validateHostedRunSafety(req.body.safety);
  if (safetyError) {
    return res.status(400).json(hostedRunResponse(false, "", "blocked", safetyError));
  }

  const usage = state.usageLedger[String(req.body.usageId || "")];
  if (expectedCredits > 0) {
    const usageError = validateUsageForHostedRun(usage, license, workflowType, expectedCredits);
    if (usageError) {
      return res.status(402).json(hostedRunResponse(false, "", "blocked", usageError));
    }
  }

  const runId = `run_${crypto.randomUUID()}`;
  const run = {
    id: runId,
    usageId: usage ? usage.id : "",
    licenseId: license.id,
    workflowType,
    productUrl: String(req.body.productUrl || ""),
    platforms: Array.isArray(req.body.platforms) ? req.body.platforms : [],
    localCommand: String(req.body.localCommand || ""),
    idempotencyKey: String(req.body.idempotencyKey || ""),
    status: "queued",
    createdAt: nowIso(),
    updatedAt: nowIso()
  };
  state.hostedRuns[runId] = run;
  audit(state, "hosted_run_queued", { runId, usageId: run.usageId, workflowType });
  saveState(state);
  return res.json(hostedRunResponse(true, runId, "queued", "ok"));
});

app.post("/api/promotion-manager/usage/commit", (req, res) => {
  const state = loadState();
  const usage = state.usageLedger[String(req.body.usageId || "")];
  if (!usage) {
    return res.status(404).json({ status: "failed", reason: "usage_not_found" });
  }
  const license = state.licenses[usage.licenseId];
  const creditsUsed = Math.max(0, Number(req.body.creditsUsed || 0));
  const refundable = Math.max(0, usage.creditsReserved - creditsUsed);
  usage.inputTokens = Number(req.body.inputTokens || 0);
  usage.outputTokens = Number(req.body.outputTokens || 0);
  usage.videoSecondsRendered = Number(req.body.videoSecondsRendered || 0);
  usage.creditsUsed = creditsUsed;
  usage.status = String(req.body.status || "succeeded");
  usage.updatedAt = nowIso();
  if (license && refundable > 0) {
    license.creditsRemaining += refundable;
  }
  audit(state, "usage_committed", { usageId: usage.id, creditsUsed, refunded: refundable, status: usage.status });
  saveState(state);
  return res.json({ status: usage.status, usageId: usage.id, creditsUsed, creditsRefunded: refundable });
});

function requireStripeConfig(keys) {
  const missing = keys.filter((key) => !process.env[key]);
  if (missing.length > 0 || !stripe) {
    return { error: "missing_stripe_config", missing };
  }
  return null;
}

function loadState() {
  if (!fs.existsSync(stateFile)) {
    return emptyState();
  }
  try {
    const parsed = JSON.parse(fs.readFileSync(stateFile, "utf8"));
    return { ...emptyState(), ...parsed };
  } catch (_error) {
    return emptyState();
  }
}

function saveState(state) {
  fs.mkdirSync(path.dirname(stateFile), { recursive: true });
  fs.writeFileSync(stateFile, `${JSON.stringify(state, null, 2)}\n`);
}

function emptyState() {
  return {
    accounts: {},
    licenses: {},
    subscriptions: {},
    usageLedger: {},
    hostedRuns: {},
    stripeCustomers: {},
    auditLog: []
  };
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
      license.renewsAt = dateFromUnix(invoice.lines && invoice.lines.data && invoice.lines.data[0] && invoice.lines.data[0].period && invoice.lines.data[0].period.end) || license.renewsAt;
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
    reportUrl: "",
    reason
  };
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

function trimTrailingSlash(value) {
  return String(value).replace(/\/+$/, "");
}

function audit(state, action, details) {
  state.auditLog.push({ at: nowIso(), action, details });
}

if (require.main === module) {
  app.listen(port, () => {
    console.log(`ENHE Promotion Manager license service listening on ${port}`);
  });
}

module.exports = { app, loadState, saveState, hashLicenseKey };
