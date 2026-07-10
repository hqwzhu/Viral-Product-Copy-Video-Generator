"use strict";

const assert = require("node:assert/strict");
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
const { processNextHostedRun } = require("./hosted-worker");

test.after(() => {
  fs.rmSync(tmpRoot, { recursive: true, force: true });
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
