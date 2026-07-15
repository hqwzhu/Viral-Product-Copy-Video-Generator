"use strict";

const crypto = require("node:crypto");

const ZPAY_PRICE_ENV_BY_PLAN = {
  starter: "ZPAY_PRICE_STARTER_CNY",
  growth: "ZPAY_PRICE_GROWTH_CNY",
  scale: "ZPAY_PRICE_SCALE_CNY"
};

function loadZpayConfig() {
  return {
    apiBase: trimTrailingSlash(process.env.ZPAY_API_BASE || "https://zpayz.cn"),
    pid: String(process.env.ZPAY_PID || "").trim(),
    key: String(process.env.ZPAY_KEY || "").trim(),
    defaultType: normalizeZpayType(process.env.ZPAY_DEFAULT_TYPE || "wxpay"),
    channelId: String(process.env.ZPAY_CHANNEL_ID || "").trim(),
    licenseDays: Math.max(1, Number(process.env.ZPAY_LICENSE_DAYS || 30))
  };
}

function isZpayConfigured() {
  const config = loadZpayConfig();
  return Boolean(config.apiBase && config.pid && config.key);
}

function zpayPriceForPlan(plan) {
  const envName = ZPAY_PRICE_ENV_BY_PLAN[plan];
  const value = envName ? process.env[envName] : "";
  if (!value) return null;
  return formatZpayAmount(value);
}

function buildZpaySignSource(params, merchantKey) {
  const query = Object.keys(params)
    .filter((key) => key !== "sign" && key !== "sign_type" && String(params[key] ?? "") !== "")
    .sort()
    .map((key) => `${key}=${params[key]}`)
    .join("&");
  return `${query}${merchantKey}`;
}

function createZpaySign(params, merchantKey) {
  return crypto.createHash("md5").update(buildZpaySignSource(params, merchantKey), "utf8").digest("hex");
}

function buildZpaySignedParams(params, merchantKey) {
  const payload = { ...params, sign_type: "MD5" };
  return { ...payload, sign: createZpaySign(payload, merchantKey) };
}

function buildZpayPaymentRequest(input) {
  const params = buildZpaySignedParams({
    pid: input.config.pid,
    cid: input.config.channelId,
    type: normalizeZpayType(input.type || input.config.defaultType),
    out_trade_no: input.orderNo,
    notify_url: input.notifyUrl,
    return_url: input.returnUrl,
    name: `ENHE Product Promo Maker ${labelPlan(input.plan)}`,
    money: formatZpayAmount(input.amount),
    clientip: input.clientIp || "127.0.0.1",
    param: input.paymentId
  }, input.config.key);
  return {
    endpoint: `${input.config.apiBase}/mapi.php`,
    params
  };
}

async function requestZpayPayment(request) {
  const body = new URLSearchParams();
  for (const [key, value] of Object.entries(request.params)) {
    if (String(value ?? "") !== "") body.set(key, String(value));
  }
  const response = await fetch(request.endpoint, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body
  });
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`ZPAY returned non-JSON response: ${text.slice(0, 160)}`);
  }
}

function verifyZpayNotifyPayload(payload, payment, config) {
  const receivedSign = String(payload.sign || "");
  if (!receivedSign) return { ok: false, reason: "missing_signature" };
  const expectedSign = createZpaySign(payload, config.key);
  if (expectedSign.toLowerCase() !== receivedSign.toLowerCase()) {
    return { ok: false, reason: "invalid_signature" };
  }
  if (String(payload.pid || "") !== config.pid) return { ok: false, reason: "merchant_mismatch" };
  if (String(payload.out_trade_no || "") !== payment.orderNo) return { ok: false, reason: "order_mismatch" };
  if (String(payload.trade_status || "") !== "TRADE_SUCCESS") return { ok: false, reason: "status_not_success" };
  if (formatZpayAmount(payload.money || 0) !== formatZpayAmount(payment.amount)) {
    return { ok: false, reason: "amount_mismatch" };
  }
  return { ok: true, reason: null };
}

function formatZpayAmount(value) {
  const amount = Number(value);
  if (!Number.isFinite(amount) || amount <= 0) throw new Error("Invalid ZPAY amount.");
  return amount.toFixed(2);
}

function normalizeZpayType(value) {
  return String(value || "").toLowerCase() === "alipay" ? "alipay" : "wxpay";
}

function labelPlan(plan) {
  return String(plan).charAt(0).toUpperCase() + String(plan).slice(1);
}

function trimTrailingSlash(value) {
  return String(value).replace(/\/+$/, "");
}

module.exports = {
  ZPAY_PRICE_ENV_BY_PLAN,
  buildZpayPaymentRequest,
  buildZpaySignSource,
  createZpaySign,
  formatZpayAmount,
  isZpayConfigured,
  loadZpayConfig,
  normalizeZpayType,
  requestZpayPayment,
  verifyZpayNotifyPayload,
  zpayPriceForPlan
};
