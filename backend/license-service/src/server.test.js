"use strict";

const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), "enhe-pm-license-service-"));
process.env.LICENSE_PEPPER = "test-pepper";
process.env.LICENSE_SERVICE_STATE_FILE = path.join(tmpRoot, "state.json");
process.env.ENHE_PUBLIC_BASE_URL = "https://www.enhe-tech.com.cn";
process.env.HOSTED_WORKER_MODE = "simulate";

const { app, emptyState, hashLicenseKey, saveState, store } = require("./server");
const { processNextHostedRun, runRetentionCleanup } = require("./hosted-worker");

test.after(() => {
  fs.rmSync(tmpRoot, { recursive: true, force: true });
});

test("public health alias matches the canonical health endpoint", async () => {
  saveState(emptyState());
  const server = http.createServer(app);
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const baseUrl = `http://127.0.0.1:${server.address().port}`;
  try {
    const canonical = await fetch(`${baseUrl}/health`);
    const publicAlias = await fetch(`${baseUrl}/api/promotion-manager/health`);
    assert.equal(canonical.status, 200);
    assert.equal(publicAlias.status, 200);
    assert.deepEqual(await publicAlias.json(), await canonical.json());
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test("privacy page publishes the approved English and Chinese retention policy", async () => {
  const server = http.createServer(app);
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const baseUrl = `http://127.0.0.1:${server.address().port}`;
  try {
    const response = await fetch(`${baseUrl}/promotion-manager/privacy`);
    assert.equal(response.status, 200);
    const html = await response.text();
    assert.match(html, /中文 \/ EN/);
    assert.match(html, /automatically deleted 30 days/);
    assert.match(html, /retained for 180 days/);
    assert.match(html, /applicable law/);
    assert.match(html, /30 天后自动删除/);
    assert.match(html, /保留 180 天/);
    assert.match(html, /按照适用法律保留/);
    assert.match(html, /huqingwei5942@gmail\.com/);
    assert.match(html, /enhe_pm_language/);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test("license service queues and completes a hosted worker run", async () => {
  const licenseKey = "pm_test_hosted_worker_license";
  const state = emptyState();
  state.accounts.acct_test = { id: "acct_test", email: "operator@example.com", createdAt: new Date().toISOString() };
  state.licenses.lic_test = {
    id: "lic_test",
    accountId: "acct_test",
    licenseKeyHash: hashLicenseKey(licenseKey),
    status: "active",
    plan: "growth",
    creditsRemaining: 20,
    renewsAt: "2026-08-09",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };
  saveState(state);

  const server = http.createServer(app);
  await new Promise((resolve) => server.listen(0, resolve));
  const baseUrl = `http://127.0.0.1:${server.address().port}`;
  try {
    const license = await postJson(`${baseUrl}/api/promotion-manager/license`, { licenseKey });
    assert.equal(license.active, true);
    assert.equal(license.hostedRunEndpoint, "https://www.enhe-tech.com.cn/api/promotion-manager/run");

    const usage = await postJson(`${baseUrl}/api/promotion-manager/usage/authorize`, {
      licenseKey,
      workflowType: "standard_run",
      estimatedCredits: 4,
      idempotencyKey: "hosted-worker-test-usage",
      commandType: "skill_entry"
    });
    assert.equal(usage.allowed, true);
    assert.equal(usage.creditsReserved, 4);

    const queued = await postJson(`${baseUrl}/api/promotion-manager/run`, {
      licenseKey,
      usageId: usage.usageId,
      workflowType: "standard_run",
      estimatedCredits: 4,
      commandType: "skill_entry",
      extensionVersion: "0.5.0",
      requestSource: "chrome_extension",
      idempotencyKey: "hosted-worker-test-run",
      productUrl: "https://example.com/product",
      platforms: ["youtube", "github"],
      workflowDepth: "research",
      options: {},
      safety: {
        approvalRequiredForOfficialPublish: true,
        finalPublishNotClickedByExtension: true,
        noPlatformSecretsInPayload: true,
        noCaptchaBypass: true
      }
    });
    assert.equal(queued.accepted, true);
    assert.equal(queued.status, "queued");
    assert.match(queued.statusUrl, /\/api\/promotion-manager\/run\/run_/);

    await processNextHostedRun(store, { mode: "simulate", outputRoot: path.join(tmpRoot, "runs") });

    const status = await getJson(`${baseUrl}/api/promotion-manager/run/${queued.runId}`);
    assert.equal(status.status, "succeeded");
    assert.equal(status.workflowType, "standard_run");
    assert.equal(status.commandType, "skill_entry");
    assert.ok(status.artifactDirectory.includes(queued.runId));

    const privacyPage = await getText(`${baseUrl}/promotion-manager/privacy`);
    assert.match(privacyPage, /Privacy Policy/);
    assert.match(privacyPage, /Data We Do Not Collect/);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test("retention cleanup deletes hosted artifacts after 30 days and audit logs after 180 days", async () => {
  const outputRoot = path.join(tmpRoot, "retention-runs");
  const oldDirectory = path.join(outputRoot, "run_old");
  const recentDirectory = path.join(outputRoot, "run_recent");
  fs.mkdirSync(oldDirectory, { recursive: true });
  fs.mkdirSync(recentDirectory, { recursive: true });
  fs.writeFileSync(path.join(oldDirectory, "artifact.txt"), "old");
  fs.writeFileSync(path.join(recentDirectory, "artifact.txt"), "recent");

  const state = emptyState();
  state.hostedRuns.run_old = {
    id: "run_old",
    status: "succeeded",
    finishedAt: "2026-06-14T00:00:00.000Z",
    artifactDirectory: oldDirectory,
    reportPath: path.join(oldDirectory, "report.json")
  };
  state.hostedRuns.run_recent = {
    id: "run_recent",
    status: "succeeded",
    finishedAt: "2026-06-16T00:00:00.000Z",
    artifactDirectory: recentDirectory,
    reportPath: path.join(recentDirectory, "report.json")
  };
  state.auditLog = [
    { at: "2026-01-15T00:00:00.000Z", action: "old_audit", details: {} },
    { at: "2026-01-17T00:00:00.000Z", action: "recent_audit", details: {} }
  ];
  state.payments.pay_keep = { id: "pay_keep", status: "paid" };
  const retentionStore = { update: async (mutator) => mutator(state) };

  await runRetentionCleanup(retentionStore, {
    outputRoot,
    now: "2026-07-15T00:00:00.000Z",
    artifactRetentionDays: 30,
    auditRetentionDays: 180
  });

  assert.equal(fs.existsSync(oldDirectory), false);
  assert.equal(fs.existsSync(recentDirectory), true);
  assert.equal(state.hostedRuns.run_old.artifactDirectory, "");
  assert.equal(state.hostedRuns.run_recent.artifactDirectory, recentDirectory);
  assert.equal(state.auditLog.some((entry) => entry.action === "old_audit"), false);
  assert.equal(state.auditLog.some((entry) => entry.action === "recent_audit"), true);
  assert.equal(state.auditLog.some((entry) => entry.action === "hosted_artifacts_deleted"), true);
  assert.deepEqual(state.payments.pay_keep, { id: "pay_keep", status: "paid" });
});

test("ZPAY checkout activates a hashed license after a verified domestic payment", async () => {
  const providerRequests = [];
  const provider = http.createServer(async (req, res) => {
    let body = "";
    for await (const chunk of req) body += chunk;
    providerRequests.push(Object.fromEntries(new URLSearchParams(body)));
    res.writeHead(200, { "content-type": "application/json" });
    res.end(JSON.stringify({
      code: 1,
      trade_no: "zpay_trade_test",
      payurl: "https://pay.example.test/order/zpay_trade_test"
    }));
  });
  await new Promise((resolve) => provider.listen(0, "127.0.0.1", resolve));

  const providerBaseUrl = `http://127.0.0.1:${provider.address().port}`;
  Object.assign(process.env, {
    ZPAY_API_BASE: providerBaseUrl,
    ZPAY_PID: "merchant-test",
    ZPAY_KEY: "zpay-test-secret",
    ZPAY_DEFAULT_TYPE: "wxpay",
    ZPAY_CHANNEL_ID: "channel-test",
    ZPAY_PRICE_STARTER_CNY: "19",
    ZPAY_PRICE_GROWTH_CNY: "59",
    ZPAY_PRICE_SCALE_CNY: "199",
    ZPAY_LICENSE_DAYS: "30"
  });
  saveState(emptyState());

  const server = http.createServer(app);
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const baseUrl = `http://127.0.0.1:${server.address().port}`;
  try {
    const checkoutPage = await fetch(`${baseUrl}/promotion-manager/checkout?plan=growth`);
    assert.equal(checkoutPage.status, 200);
    const checkoutHtml = await checkoutPage.text();
    assert.match(checkoutHtml, /中文 \/ EN/);
    assert.match(checkoutHtml, /Starter[^<]*¥19/);
    assert.match(checkoutHtml, /Growth[^<]*¥59/);
    assert.match(checkoutHtml, /Scale[^<]*¥199/);
    assert.doesNotMatch(checkoutHtml, /¥(?:19|59|199)\.00/);
    assert.match(checkoutHtml, /data-i18n="submitPayment"/);
    assert.match(checkoutHtml, /id="paymentQr"/);
    assert.match(checkoutHtml, /id="openPaymentPage"/);
    assert.match(checkoutHtml, /application\/json/);
    assert.match(checkoutHtml, /navigator\.userAgentData/);
    assert.match(checkoutHtml, /\/api\/promotion-manager\/payments\/zpay\/status/);
    assert.match(checkoutHtml, /3_000/);
    assert.match(checkoutHtml, /10 \* 60 \* 1_000/);
    assert.match(checkoutHtml, /localStorage\.getItem\("enhe_pm_language"\)/);

    const checkout = await fetch(`${baseUrl}/api/promotion-manager/payments/zpay/checkout`, {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        plan: "starter",
        email: "buyer@example.com",
        type: "wxpay"
      }),
      redirect: "manual"
    });
    assert.equal(checkout.status, 303);
    assert.equal(checkout.headers.get("location"), "https://pay.example.test/order/zpay_trade_test");
    const setCookie = checkout.headers.get("set-cookie") || "";
    assert.match(setCookie, /enhe_pm_claim=/);
    const licenseKey = decodeURIComponent(setCookie.match(/enhe_pm_claim=([^;]+)/)[1]);
    assert.match(licenseKey, /^pm_live_/);

    const jsonCheckout = await fetch(`${baseUrl}/api/promotion-manager/payments/zpay/checkout`, {
      method: "POST",
      headers: {
        accept: "application/json",
        "content-type": "application/x-www-form-urlencoded"
      },
      body: new URLSearchParams({
        plan: "growth",
        email: "qr-buyer@example.com",
        type: "wxpay"
      }),
      redirect: "manual"
    });
    assert.equal(jsonCheckout.status, 201);
    const jsonBody = await jsonCheckout.json();
    assert.equal(jsonBody.plan, "growth");
    assert.equal(jsonBody.amount, "59.00");
    assert.equal(jsonBody.termDays, 30);
    assert.equal(jsonBody.paymentType, "wxpay");
    assert.match(jsonBody.orderNo, /^pm_/);
    assert.equal(jsonBody.paymentUrl, "https://pay.example.test/order/zpay_trade_test");
    assert.match(jsonBody.qrCodeDataUrl, /^data:image\/png;base64,/);
    assert.match(jsonBody.claimUrl, /\/promotion-manager\/checkout\/success\?orderNo=/);
    const jsonSetCookie = jsonCheckout.headers.get("set-cookie") || "";
    assert.match(jsonSetCookie, /enhe_pm_claim=/);
    const jsonClaimCookie = jsonSetCookie.split(";", 1)[0];

    const unknownStatus = await fetch(
      `${baseUrl}/api/promotion-manager/payments/zpay/status?orderNo=pm_unknown`
    );
    assert.equal(unknownStatus.status, 404);

    const anonymousStatus = await fetch(
      `${baseUrl}/api/promotion-manager/payments/zpay/status?orderNo=${encodeURIComponent(jsonBody.orderNo)}`
    );
    assert.equal(anonymousStatus.status, 403);

    const pendingStatus = await fetch(
      `${baseUrl}/api/promotion-manager/payments/zpay/status?orderNo=${encodeURIComponent(jsonBody.orderNo)}`,
      { headers: { cookie: jsonClaimCookie } }
    );
    assert.equal(pendingStatus.status, 200);
    assert.deepEqual(await pendingStatus.json(), {
      orderNo: jsonBody.orderNo,
      status: "pending",
      claimUrl: ""
    });

    assert.equal(providerRequests.length, 2);
    const providerRequest = providerRequests[0];
    assert.equal(providerRequest.type, "wxpay");
    assert.equal(providerRequest.money, "19.00");
    assert.equal(providerRequest.name, "ENHE Promotion Manager Starter");
    assert.equal(providerRequest.notify_url, "https://www.enhe-tech.com.cn/api/promotion-manager/webhooks/zpay");
    assert.match(providerRequest.return_url, /\/promotion-manager\/checkout\/success\?orderNo=/);
    assert.equal(providerRequest.sign, signZpay(providerRequest, process.env.ZPAY_KEY));
    const qrProviderRequest = providerRequests[1];
    assert.equal(qrProviderRequest.type, "wxpay");
    assert.equal(qrProviderRequest.money, "59.00");
    assert.equal(qrProviderRequest.name, "ENHE Promotion Manager Growth");
    assert.equal(qrProviderRequest.notify_url, "https://www.enhe-tech.com.cn/api/promotion-manager/webhooks/zpay");
    assert.match(qrProviderRequest.return_url, /\/promotion-manager\/checkout\/success\?orderNo=/);
    assert.equal(qrProviderRequest.sign, signZpay(qrProviderRequest, process.env.ZPAY_KEY));

    const pendingState = await store.load();
    const payment = Object.values(pendingState.payments)[0];
    const pendingLicense = pendingState.licenses[payment.licenseId];
    assert.equal(payment.status, "pending");
    assert.equal(pendingLicense.status, "pending_payment");
    assert.equal(pendingLicense.licenseKeyHash, hashLicenseKey(licenseKey));
    assert.equal(JSON.stringify(pendingState).includes(licenseKey), false);

    const notify = {
      pid: process.env.ZPAY_PID,
      out_trade_no: payment.orderNo,
      trade_no: "zpay_trade_test",
      trade_status: "TRADE_SUCCESS",
      type: "wxpay",
      money: "19.00"
    };
    notify.sign_type = "MD5";
    notify.sign = signZpay(notify, process.env.ZPAY_KEY);
    const notified = await fetch(`${baseUrl}/api/promotion-manager/webhooks/zpay?${new URLSearchParams(notify)}`);
    assert.equal(notified.status, 200);
    assert.equal(await notified.text(), "success");

    const paidState = await store.load();
    const paidLicense = paidState.licenses[payment.licenseId];
    assert.equal(paidState.payments[payment.id].status, "paid");
    assert.equal(paidLicense.status, "active");
    assert.equal(paidLicense.plan, "starter");
    assert.equal(paidLicense.creditsRemaining, 60);
    assert.match(paidLicense.renewsAt, /^\d{4}-\d{2}-\d{2}$/);

    const success = await fetch(`${baseUrl}/promotion-manager/checkout/success?orderNo=${payment.orderNo}`, {
      headers: { cookie: `enhe_pm_claim=${encodeURIComponent(licenseKey)}` }
    });
    assert.equal(success.status, 200);
    const successHtml = await success.text();
    assert.match(successHtml, new RegExp(licenseKey));
    assert.match(successHtml, /中文 \/ EN/);
    assert.match(successHtml, /Payment confirmed/);
    assert.match(successHtml, /支付已确认/);
    assert.match(successHtml, /enhe_pm_language/);

    const stateBeforeQrPayment = await store.load();
    const qrPayment = Object.values(stateBeforeQrPayment.payments)
      .find((item) => item.orderNo === jsonBody.orderNo);
    const qrNotify = {
      pid: process.env.ZPAY_PID,
      out_trade_no: qrPayment.orderNo,
      trade_no: "zpay_trade_qr_test",
      trade_status: "TRADE_SUCCESS",
      type: "wxpay",
      money: "59.00"
    };
    qrNotify.sign_type = "MD5";
    qrNotify.sign = signZpay(qrNotify, process.env.ZPAY_KEY);
    const qrNotified = await fetch(
      `${baseUrl}/api/promotion-manager/webhooks/zpay?${new URLSearchParams(qrNotify)}`
    );
    assert.equal(qrNotified.status, 200);
    assert.equal(await qrNotified.text(), "success");

    const paidStatus = await fetch(
      `${baseUrl}/api/promotion-manager/payments/zpay/status?orderNo=${encodeURIComponent(jsonBody.orderNo)}`,
      { headers: { cookie: jsonClaimCookie } }
    );
    assert.equal(paidStatus.status, 200);
    assert.deepEqual(await paidStatus.json(), {
      orderNo: jsonBody.orderNo,
      status: "paid",
      claimUrl: jsonBody.claimUrl
    });
  } finally {
    await new Promise((resolve) => server.close(resolve));
    await new Promise((resolve) => provider.close(resolve));
    for (const key of [
      "ZPAY_API_BASE",
      "ZPAY_PID",
      "ZPAY_KEY",
      "ZPAY_DEFAULT_TYPE",
      "ZPAY_CHANNEL_ID",
      "ZPAY_PRICE_STARTER_CNY",
      "ZPAY_PRICE_GROWTH_CNY",
      "ZPAY_PRICE_SCALE_CNY",
      "ZPAY_LICENSE_DAYS"
    ]) delete process.env[key];
  }
});

function signZpay(params, merchantKey) {
  const source = Object.keys(params)
    .filter((key) => key !== "sign" && key !== "sign_type" && String(params[key] ?? "") !== "")
    .sort()
    .map((key) => `${key}=${params[key]}`)
    .join("&");
  return crypto.createHash("md5").update(`${source}${merchantKey}`, "utf8").digest("hex");
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body)
  });
  const payload = await response.json();
  assert.equal(response.ok, true, JSON.stringify(payload));
  return payload;
}

async function getJson(url) {
  const response = await fetch(url);
  const payload = await response.json();
  assert.equal(response.ok, true, JSON.stringify(payload));
  return payload;
}

async function getText(url) {
  const response = await fetch(url);
  const payload = await response.text();
  assert.equal(response.ok, true, payload);
  return payload;
}
