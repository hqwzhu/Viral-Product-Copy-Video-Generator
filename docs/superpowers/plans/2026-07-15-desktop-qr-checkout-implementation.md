# Desktop QR Checkout and Public Surface Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver desktop QR payment, mobile direct payment, protected payment polling, bilingual public payment/privacy pages, exact 30-day pricing, and a public health alias in one merged and deployed pull request.

**Architecture:** Preserve the existing ZPAY order, signed webhook, claim-cookie, and HTML redirect flow. Add an opt-in JSON response that includes a locally generated QR image, add an authenticated status endpoint, and enhance the server-rendered pages with bundled inline bilingual behavior. Keep the implementation in the existing license service and add only the `qrcode` runtime dependency.

**Tech Stack:** Node.js 20+, Express, node:test, ZPAY, `qrcode` 1.5.4, PostgreSQL/JSON state store, systemd, Nginx, Chrome CDP smoke testing.

---

## File Map

- Modify `backend/license-service/src/server.js`: shared health handler, JSON checkout, protected payment status, bilingual checkout/result/privacy rendering, and desktop/mobile browser behavior.
- Modify `backend/license-service/src/server.test.js`: all backend, security, pricing, HTML, and health regression coverage.
- Modify `backend/license-service/package.json`: add `qrcode` 1.5.4.
- Modify `backend/license-service/package-lock.json`: lock the QR dependency and its transitive dependencies.
- Create `docs/legal/privacy-policy.zh-CN.md`: approved Chinese privacy policy matching the English business rules.
- Modify `backend/license-service/README.md`: document the JSON checkout, payment-status endpoint, health alias, and UI behavior.
- Modify `deploy/promotion-manager/README.md`: document post-deployment checks for both health paths and public pages.
- Modify `docs/superpowers/plans/2026-07-15-desktop-qr-checkout-implementation.md`: mark completed steps as execution progresses.

### Task 1: Add the public health-check alias

**Files:**
- Modify: `backend/license-service/src/server.test.js`
- Modify: `backend/license-service/src/server.js`

- [x] **Step 1: Write the failing health-equivalence test**

Add this test near the top of `backend/license-service/src/server.test.js`:

```js
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
```

- [x] **Step 2: Run the focused test and verify RED**

Run:

```powershell
node --test --test-name-pattern="public health alias" src/server.test.js
```

Expected: FAIL because `/api/promotion-manager/health` returns 404.

- [x] **Step 3: Implement one shared health handler**

In `backend/license-service/src/server.js`, replace the inline `/health` callback with:

```js
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
```

- [x] **Step 4: Run the focused test and verify GREEN**

Run:

```powershell
node --test --test-name-pattern="public health alias" src/server.test.js
```

Expected: one matching test passes with exit code 0.

- [x] **Step 5: Commit the health alias**

```powershell
git add -- backend/license-service/src/server.js backend/license-service/src/server.test.js
git commit -m "feat: expose promotion manager health alias"
```

### Task 2: Return a locally generated QR code for JSON checkout clients

**Files:**
- Modify: `backend/license-service/package.json`
- Modify: `backend/license-service/package-lock.json`
- Modify: `backend/license-service/src/server.test.js`
- Modify: `backend/license-service/src/server.js`

- [x] **Step 1: Extend the ZPAY test with a failing JSON-checkout assertion**

In the existing ZPAY integration test, keep the current form POST and `303` assertion. Then create a second order with:

```js
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
assert.match(jsonCheckout.headers.get("set-cookie") || "", /enhe_pm_claim=/);
```

Also assert the provider received `money === "59.00"` for the second request while the original redirect request remains `19.00`.

- [x] **Step 2: Run the ZPAY test and verify RED**

```powershell
node --test --test-name-pattern="ZPAY checkout" src/server.test.js
```

Expected: FAIL because the endpoint returns `303` instead of JSON.

- [x] **Step 3: Install the pinned QR dependency**

```powershell
npm install qrcode@1.5.4 --save-exact
```

Confirm `package.json` contains:

```json
"qrcode": "1.5.4"
```

- [x] **Step 4: Implement content negotiation and QR generation**

At the top of `server.js`, add:

```js
const QRCode = require("qrcode");
```

After the provider destination is validated and the state/cookie operations complete, replace the unconditional redirect with:

```js
const claimUrl = `${publicBaseUrl}/promotion-manager/checkout/success?orderNo=${encodeURIComponent(orderNo)}`;
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
```

Use the same `claimUrl` variable when building the ZPAY `return_url` so the provider and JSON response cannot drift.

- [x] **Step 5: Run the focused test and verify GREEN**

Run the focused ZPAY command. Expected: the test passes, the original form submission is still `303`, and the JSON submission is `201`.

- [x] **Step 6: Commit JSON checkout and QR generation**

```powershell
git add -- backend/license-service/package.json backend/license-service/package-lock.json backend/license-service/src/server.js backend/license-service/src/server.test.js
git commit -m "feat: return QR payment checkout data"
```

### Task 3: Add claim-protected payment-status polling

**Files:**
- Modify: `backend/license-service/src/server.test.js`
- Modify: `backend/license-service/src/server.js`

- [x] **Step 1: Add failing ownership and state tests**

Continue the JSON checkout test using the JSON response and its claim cookie:

```js
const claimCookie = (jsonCheckout.headers.get("set-cookie") || "").split(";", 1)[0];
const anonymousStatus = await fetch(
  `${baseUrl}/api/promotion-manager/payments/zpay/status?orderNo=${encodeURIComponent(jsonBody.orderNo)}`
);
assert.equal(anonymousStatus.status, 403);

const pendingStatus = await fetch(
  `${baseUrl}/api/promotion-manager/payments/zpay/status?orderNo=${encodeURIComponent(jsonBody.orderNo)}`,
  { headers: { cookie: claimCookie } }
);
assert.equal(pendingStatus.status, 200);
assert.deepEqual(await pendingStatus.json(), {
  orderNo: jsonBody.orderNo,
  status: "pending",
  claimUrl: ""
});
```

After sending the existing valid signed webhook for this order, add:

```js
const paidStatus = await fetch(
  `${baseUrl}/api/promotion-manager/payments/zpay/status?orderNo=${encodeURIComponent(jsonBody.orderNo)}`,
  { headers: { cookie: claimCookie } }
);
assert.equal(paidStatus.status, 200);
assert.deepEqual(await paidStatus.json(), {
  orderNo: jsonBody.orderNo,
  status: "paid",
  claimUrl: jsonBody.claimUrl
});
```

Add a separate assertion that an unknown order returns 404.

- [x] **Step 2: Run the ZPAY test and verify RED**

Run the focused ZPAY test. Expected: FAIL because the status route does not exist.

- [x] **Step 3: Implement the protected status endpoint**

Add this route after checkout creation and before the success page:

```js
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

  const status = payment.status === "paid" ? "paid" : payment.status === "failed" ? "failed" : "pending";
  const claimUrl = status === "paid"
    ? `${publicBaseUrl}/promotion-manager/checkout/success?orderNo=${encodeURIComponent(orderNo)}`
    : "";
  return res.json({ orderNo, status, claimUrl });
}));
```

- [x] **Step 4: Run the focused test and verify GREEN**

Expected: anonymous access is 403, the owning browser sees pending, the signed webhook changes it to paid, and an unknown order is 404.

- [x] **Step 5: Commit protected polling**

```powershell
git add -- backend/license-service/src/server.js backend/license-service/src/server.test.js
git commit -m "feat: add protected payment status polling"
```

### Task 4: Build bilingual desktop QR and mobile direct-payment behavior

**Files:**
- Modify: `backend/license-service/src/server.test.js`
- Modify: `backend/license-service/src/server.js`

- [x] **Step 1: Add failing checkout-page contract assertions**

Inside the existing ZPAY integration test, after the provider and app servers are listening and before creating the first order, request `/promotion-manager/checkout?plan=growth` and assert:

```js
assert.equal(response.status, 200);
const html = await response.text();
assert.match(html, /中文 \/ EN/);
assert.match(html, /Starter[^<]*¥19/);
assert.match(html, /Growth[^<]*¥59/);
assert.match(html, /Scale[^<]*¥199/);
assert.match(html, /data-i18n="submitPayment"/);
assert.match(html, /id="paymentQr"/);
assert.match(html, /id="openPaymentPage"/);
assert.match(html, /application\/json/);
assert.match(html, /navigator\.userAgentData/);
assert.match(html, /\/api\/promotion-manager\/payments\/zpay\/status/);
assert.match(html, /3_000/);
assert.match(html, /10 \* 60 \* 1_000/);
assert.match(html, /localStorage\.getItem\("enhe_pm_language"\)/);
```

- [x] **Step 2: Run the checkout-page test and verify RED**

Expected: FAIL because the current page is Chinese-only and has no QR panel or browser script.

- [x] **Step 3: Replace `renderZpayCheckoutPage` with the minimal bilingual page**

Keep one form and one payment panel. The server-rendered option labels must use:

```js
const displayPrice = String(price || "").replace(/\.00$/, "");
const label = `${labelPlan(plan)}${price ? ` - ¥${displayPrice}` : " - unavailable"}`;
```

Embed a local message object with these keys in both languages:

```js
const messages = {
  "zh-CN": {
    title: "ENHE Promotion Manager 国内支付",
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
    privacyHint: "支付由 ENHE AI 的 ZPAY 商户通道处理。"
  },
  en: {
    title: "ENHE Promotion Manager Checkout",
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
    privacyHint: "Payment is processed through ENHE AI's ZPAY merchant channel."
  }
};
```

The inline browser code must:

```js
const languageKey = "enhe_pm_language";
const storedLanguage = localStorage.getItem(languageKey);
let language = storedLanguage || (navigator.language.toLowerCase().startsWith("zh") ? "zh-CN" : "en");
const mobile = navigator.userAgentData && typeof navigator.userAgentData.mobile === "boolean"
  ? navigator.userAgentData.mobile
  : /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);
```

On submit, call `fetch` with `Accept: application/json`. If `mobile` is true, call `location.assign(body.paymentUrl)`. Otherwise populate `paymentQr.src`, show the panel, expose `openPaymentPage.href`, and poll the protected status route every `3_000` milliseconds. Pause while `document.hidden`, stop after `10 * 60 * 1_000`, clear on `beforeunload`, and navigate to `status.claimUrl` only when the response says `paid`.

All translated text must be assigned with `textContent`; provider and claim links must be assigned through validated `href` values returned by the same-origin backend.

- [x] **Step 4: Run the checkout-page and ZPAY tests and verify GREEN**

```powershell
node --test --test-name-pattern="checkout|ZPAY" src/server.test.js
```

Expected: all matching tests pass, including redirect compatibility, JSON checkout, protected polling, prices, and HTML contract assertions.

- [x] **Step 5: Commit the browser experience**

```powershell
git add -- backend/license-service/src/server.js backend/license-service/src/server.test.js
git commit -m "feat: add bilingual desktop QR checkout"
```

### Task 5: Make payment results and privacy policy bilingual

**Files:**
- Create: `docs/legal/privacy-policy.zh-CN.md`
- Modify: `backend/license-service/src/server.test.js`
- Modify: `backend/license-service/src/server.js`

- [x] **Step 1: Add failing result-page and privacy assertions**

Add tests that assert the payment result renderer and `/promotion-manager/privacy` HTML include:

```js
assert.match(html, /中文 \/ EN/);
assert.match(html, /Payment confirmed/);
assert.match(html, /支付已确认/);
assert.match(html, /enhe_pm_language/);
```

For privacy, assert both approved language versions contain the exact invariants:

```js
assert.match(html, /automatically deleted 30 days/);
assert.match(html, /retained for 180 days/);
assert.match(html, /applicable law/);
assert.match(html, /30 天后自动删除/);
assert.match(html, /保留 180 天/);
assert.match(html, /按照适用法律保留/);
assert.match(html, /huqingwei5942@gmail\.com/);
```

- [x] **Step 2: Run the new tests and verify RED**

Expected: FAIL because the result page has no language toggle and the privacy page has no Chinese policy source.

- [x] **Step 3: Create the approved Chinese privacy source**

Create `docs/legal/privacy-policy.zh-CN.md` with this complete content:

```markdown
# ENHE Promotion Manager 隐私政策

生效日期：2026-07-15

本政策说明 ENHE AI 如何处理 ENHE Promotion Manager 浏览器扩展程序及其可选托管服务中的信息。

## 产品功能

ENHE Promotion Manager 帮助用户将产品或网站 URL 转换为受控的推广工作流命令、发布素材包以及可选的 ENHE 托管任务。

## 我们处理的数据

- 用户明确采集或输入的产品或网站 URL。
- 用户选择的目标平台和工作流选项。
- 扩展程序在本机保存的设置，包括许可证密钥和服务端点偏好。
- 用户提交的托管任务载荷，包括产品 URL、所选平台、工作流深度和安全工作流选项。
- 来自 ZPAY、Stripe 或同等支付服务商的账单及订阅状态。
- 服务器日志、配额事件、用量预留、托管任务状态和审计事件。

## 我们不收集的数据

- 第三方平台密码。
- 浏览器 Cookie。
- 验证码答案。
- 隐藏令牌。
- 支付卡号。
- 第三方平台 OAuth 令牌，除非未来的官方集成明确请求用户授权。

## 数据用途

- 验证订阅和许可证状态。
- 预留并结算托管服务用量点数。
- 排队并执行用户请求的托管推广任务。
- 提供任务状态、客户支持、安全审计和滥用防护。
- 通过汇总且不含敏感信息的诊断数据提升可靠性和产品运营质量。

## 扩展程序本机存储

扩展程序会在 `chrome.storage.local` 中保存许可证密钥、服务端点偏好和最近一次任务元数据。用户可以通过卸载扩展程序或清除扩展程序存储来删除这些数据。

## 支付处理

支付由 ZPAY、Stripe 或同等支付服务商处理。ENHE 服务器不会接收或存储原始支付卡号或用户的支付账户密码。结算和账单活动同时适用支付服务商的隐私条款。

## 保留期限

- Hosted Task 产物将在任务完成 30 天后自动删除。
- 安全及审计日志保留 180 天。
- 支付、退款和依法需要的账务记录按照适用法律保留。
- 扩展程序本机设置将保留在用户设备上，直到用户清除扩展程序存储或卸载扩展程序。

用户可以发送邮件至 huqingwei5942@gmail.com，申请查询或删除不受强制保留要求约束的数据。

## 安全

扩展程序不会加载远程可执行代码。后端密钥、Stripe 密钥、Webhook 密钥和 Worker 凭据保留在服务器端。托管 Worker 使用人工发布安全门，不会在第三方平台上点击最终发布按钮。

## 联系方式

邮箱：huqingwei5942@gmail.com

支持：https://www.enhe-tech.com.cn/promotion-manager/support

邮寄地址：深圳市龙岗区横岗街道塘坑社区宸和路51号中联展数字电商产业园C栋C305
```

- [x] **Step 4: Implement bilingual result and privacy rendering**

Change checkout-result call sites to pass a stable result key and optional License Key rather than arbitrary user-facing prose. Support these keys in both languages:

```js
const checkoutResultMessages = {
  paymentNotFound: { en: "Payment not found", zh: "未找到支付订单" },
  paymentPending: { en: "Payment is being confirmed", zh: "正在确认支付" },
  paymentConfirmed: { en: "Payment confirmed", zh: "支付已确认" },
  claimUnavailable: {
    en: "The license claim is unavailable in this browser. Contact support with your order number.",
    zh: "当前浏览器无法领取许可证，请携带订单号联系支持。"
  },
  billing: {
    en: "Domestic plans use one-time 30-day payments. Renew or change plans from checkout.",
    zh: "国内套餐采用一次性购买 30 天许可证，请在结算页续购或更换套餐。"
  }
};
```

For `privacy`, load `privacy-policy.md` and `privacy-policy.zh-CN.md`, render each through the existing safe Markdown converter into separate language panels, and add a `中文 / EN` control using the same `enhe_pm_language` local-storage key. Keep the existing single-file behavior for terms, refund, and support.

- [x] **Step 5: Run focused tests and verify GREEN**

Run:

```powershell
node --test --test-name-pattern="privacy|result|ZPAY" src/server.test.js
```

Expected: all matching tests pass and the License Key appears only on the authorized paid claim page.

- [x] **Step 6: Commit bilingual public content**

```powershell
git add -- docs/legal/privacy-policy.zh-CN.md backend/license-service/src/server.js backend/license-service/src/server.test.js
git commit -m "feat: localize payment and privacy pages"
```

### Task 6: Document and verify the complete change

**Files:**
- Modify: `backend/license-service/README.md`
- Modify: `deploy/promotion-manager/README.md`
- Modify: `docs/superpowers/plans/2026-07-15-desktop-qr-checkout-implementation.md`

- [x] **Step 1: Update service documentation**

Document these exact endpoint contracts in `backend/license-service/README.md`:

```text
POST /api/promotion-manager/payments/zpay/checkout
  HTML form: 303 redirect
  Accept: application/json: 201 JSON with QR data and claim URL
GET /api/promotion-manager/payments/zpay/status?orderNo=...
  Requires the matching HttpOnly claim cookie
GET /health
GET /api/promotion-manager/health
  Equivalent health responses
```

Also document desktop QR, mobile direct launch, the ten-minute polling limit, and the exact 30-day prices.

- [x] **Step 2: Update deployment verification documentation**

Add these commands to `deploy/promotion-manager/README.md`:

```bash
curl -fsS http://127.0.0.1:3030/health
curl -fsS http://127.0.0.1:3030/api/promotion-manager/health
curl -fsS https://www.enhe-tech.com.cn/api/promotion-manager/health
curl -fsS https://www.enhe-tech.com.cn/promotion-manager/checkout
curl -fsS https://www.enhe-tech.com.cn/promotion-manager/privacy
```

- [x] **Step 3: Run backend tests**

```powershell
npm test
```

Expected: exit code 0, no failed Node tests.

- [x] **Step 4: Run the full Python regression suite**

From repository root:

```powershell
python -m unittest discover -s scripts -p 'test_*.py'
```

Expected: exit code 0 and `OK` with no failures.

- [x] **Step 5: Run static and dependency checks**

```powershell
git diff --check origin/main...HEAD
npm audit --omit=dev
git status --short
```

Expected: no whitespace errors, zero production vulnerabilities, and only intended branch files plus the preserved user-owned `dist` changes in the original checkout.

- [x] **Step 6: Commit documentation and completed plan state**

Mark completed plan checkboxes, then commit only the plan and documentation:

```powershell
git add -- backend/license-service/README.md deploy/promotion-manager/README.md docs/superpowers/plans/2026-07-15-desktop-qr-checkout-implementation.md
git commit -m "docs: document QR checkout operations"
```

### Task 7: Push one PR, merge it, deploy the merge commit, and verify production

**Files:**
- No new source files; this task operates on the verified branch and production release directories.

- [ ] **Step 1: Verify PR scope before publishing**

```powershell
git status -sb
git diff --stat origin/main...HEAD
git log --oneline origin/main..HEAD
gh auth status
```

Expected: the branch contains the design, plan, checkout, tests, privacy translation, dependency lock, and documentation only. The user's `dist/enhe-promotion-manager-0.5.0.zip` and `dist/store-assets/` do not appear in the branch diff.

- [ ] **Step 2: Push the feature branch**

```powershell
git push -u origin agent/desktop-qr-checkout
```

- [ ] **Step 3: Create a ready-for-review pull request**

Create the PR with a PowerShell multiline body and run:

```powershell
$body = @'
## Summary
- show a locally generated payment QR code on desktop while preserving direct provider launch on mobile
- add protected payment polling, bilingual checkout/result/privacy pages, exact 30-day prices, and a public health alias
- document and test the complete production behavior without changing the Chrome Web Store v0.5.2 package

## Root cause and security
The original checkout always returned a 303 provider redirect, which forced desktop users toward the WeChat client. JSON checkout remains opt-in, the signed webhook remains the only payment authority, and the status endpoint requires the matching HttpOnly claim cookie.

## Verification
- `npm test`
- `python -m unittest discover -s scripts -p 'test_*.py'`
- `npm audit --omit=dev`
- browser smoke checks for language switching, QR rendering contract, prices, privacy, and both health paths

## Deployment
After merge, deploy an archive built from the merge commit, retain the previous release, and verify the internal and public health endpoints before declaring success.
'@
gh pr create --base main --head agent/desktop-qr-checkout --title "feat: add desktop QR checkout and public surface hardening" --body $body
```

The PR must be ready for review, not draft, because the user explicitly approved merging after verification.

- [ ] **Step 4: Confirm mergeability and merge**

```powershell
gh pr view --json state,isDraft,mergeable,url,headRefName,baseRefName
gh pr merge --merge
```

Expected: PR state becomes `MERGED` and `origin/main` advances to the merge commit.

- [ ] **Step 5: Build the deployment archive from the merge commit**

Fetch `origin/main`, record the merge SHA, and create an archive from that Git object rather than from a dirty working tree:

```powershell
git fetch origin main
$mergeSha = (git rev-parse origin/main).Trim()
git archive --format=tar.gz --output="$env:TEMP\promotion-manager-$($mergeSha.Substring(0,12)).tar.gz" $mergeSha
```

- [ ] **Step 6: Deploy atomically and preserve rollback**

Set exact local variables and upload the merge archive:

```powershell
$mergeSha = (git rev-parse origin/main).Trim()
$releaseName = "$(Get-Date -Format yyyyMMddHHmmss)-$($mergeSha.Substring(0,12))"
$archive = Join-Path $env:TEMP "promotion-manager-$($mergeSha.Substring(0,12)).tar.gz"
$deployScript = Join-Path (git rev-parse --show-toplevel) ".codex-deploy-promotion-manager.sh"
scp -i 'C:\Users\HU\.ssh\enhe-ai-tools-tencent.pem' $archive ubuntu@111.229.135.3:/tmp/promotion-manager-release.tar.gz
scp -i 'C:\Users\HU\.ssh\enhe-ai-tools-tencent.pem' $deployScript ubuntu@111.229.135.3:/tmp/deploy-promotion-manager.sh
ssh -i 'C:\Users\HU\.ssh\enhe-ai-tools-tencent.pem' ubuntu@111.229.135.3 "bash /tmp/deploy-promotion-manager.sh '$releaseName'"
```

Create `.codex-deploy-promotion-manager.sh` with `apply_patch`, do not commit it, and use this exact content:

```bash
#!/usr/bin/env bash
set -euo pipefail

release_name="$1"
release_dir="/opt/enhe/promotion-manager/releases/$release_name"
current_link="/opt/enhe/promotion-manager/current"
previous_release="$(readlink -f "$current_link")"
env_file="/etc/enhe-promotion-manager/api.env"
env_backup="${env_file}.before-${release_name}"

rollback() {
  if [[ -f "$env_backup" ]]; then
    sudo cp "$env_backup" "$env_file"
  fi
  if [[ -n "$previous_release" && -d "$previous_release" ]]; then
    sudo ln -sfn "$previous_release" "$current_link"
    sudo systemctl restart enhe-promotion-manager-api
  fi
}
trap rollback ERR

sudo cp "$env_file" "$env_backup"
sudo install -d -o enhe-promotion -g enhe-promotion "$release_dir"
sudo tar -xzf /tmp/promotion-manager-release.tar.gz -C "$release_dir"
sudo chown -R enhe-promotion:enhe-promotion "$release_dir"
sudo -u enhe-promotion bash -lc "cd '$release_dir/backend/license-service' && npm ci --omit=dev && npm test"
sudo ln -sfn "$release_dir" "$current_link"
sudo systemctl restart enhe-promotion-manager-api
sudo systemctl is-active --quiet enhe-promotion-manager-api
curl -fsS http://127.0.0.1:3030/health >/dev/null
curl -fsS http://127.0.0.1:3030/api/promotion-manager/health >/dev/null
trap - ERR
printf '%s\n' "$release_dir"
```

Use service user/group `enhe-promotion`. The script never prints the environment file or secrets and retains the prior release and environment backup for rollback.

- [ ] **Step 7: Verify production health and public content**

Verify on the host:

```bash
systemctl is-active enhe-promotion-manager-api
systemctl is-enabled enhe-promotion-manager-api
curl -fsS http://127.0.0.1:3030/health
curl -fsS http://127.0.0.1:3030/api/promotion-manager/health
```

Then verify through the public site that:

- Both public health paths are healthy and equivalent.
- Checkout contains `中文 / EN`, Starter ¥19, Growth ¥59, Scale ¥199, the QR panel, and the mobile direct-launch branch.
- Privacy contains the approved English and Chinese 30-day, 180-day, legal-accounting, and contact-email statements.
- The Chrome Web Store item remains v0.5.2 and `待审核`; no store package is changed by this deployment.

- [ ] **Step 8: Clean only owned temporary artifacts**

Remove the local deployment archive, remote upload, temporary PR body, and browser tabs created for verification. Preserve the prior production release for rollback and preserve all user-owned working-tree changes.
