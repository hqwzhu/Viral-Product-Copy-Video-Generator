# 浏览器插件上架指南

本文用于把 `browser-extension/` 打包成 Chrome Web Store 或 Microsoft Edge Add-ons 可提交的插件包。

官方参考：

- Chrome Web Store 发布文档: https://developer.chrome.com/docs/webstore/publish
- Microsoft Edge 插件发布文档: https://learn.microsoft.com/en-us/microsoft-edge/extensions-chromium/publish/publish-extension
- Chrome remote code 迁移说明: https://developer.chrome.com/docs/extensions/develop/migrate/remote-hosted-code

## 打包

在仓库根目录运行：

```powershell
python scripts\package_browser_extension.py --out-dir ".\dist"
```

输出文件：

- `dist\enhe-promotion-manager-<version>.zip`
- `dist\browser-extension-package-report.json`
- `dist\browser-extension-package-report.md`

上传 zip 文件到商店；保留 `browser-extension-package-report.json` 作为上架前检查证据。

## 上架前检查

- Manifest 使用 MV3。
- popup、CSS、JS 都在插件包本地。
- 不加载 remote code：没有远程 `<script src="https://...">`、动态 import、`importScripts`、`eval` 或 `new Function`。
- ENHE 远程接口只作为数据接口：license 校验、usage 授权、hosted run、checkout、billing portal。
- 不打包平台密钥、支付密钥、cookie、OAuth token 或 webhook secret。
- 插件包包含 `icons/icon16.png`、`icons/icon48.png`、`icons/icon128.png`。
- 插件内带 ENHE 网站、产品页和 GitHub 链接，用于网站引流。
- 准备公开 privacy policy，建议使用 `https://www.enhe-tech.com.cn/privacy`。
- 准备支持网址，建议使用 `https://www.enhe-tech.com.cn/`。

## Chrome Web Store 上架步骤

1. 创建或登录 Chrome Web Store Developer Dashboard。
2. 按后台要求完成开发者注册和费用支付。
3. 创建新商品。
4. 上传 `dist\enhe-promotion-manager-<version>.zip`。
5. 填写商店资料：
   - 名称：`ENHE Promotion Manager`
   - 简短描述：`Generate guarded Codex promotion workflows from any product URL.`
   - 分类：按后台可选项选择 productivity 或 marketing。
   - 网站：`https://www.enhe-tech.com.cn/`
   - 支持网址：`https://www.enhe-tech.com.cn/`
   - privacy policy：`https://www.enhe-tech.com.cn/privacy`
6. 填写隐私实践。插件使用 `activeTab`、`storage`、`clipboardWrite` 和 ENHE 数据接口，不收集平台密码、cookie、支付密钥或 API token。
7. 说明收费订阅：托管运行消耗 ENHE 订阅积分，本地命令生成可作为免费或试用能力。
8. 提交审核。

## Microsoft Edge Add-ons 上架步骤

1. 创建或登录 Microsoft Partner Center。
2. 创建 Microsoft Edge extension 提交。
3. 上传同一个 `dist\enhe-promotion-manager-<version>.zip`。
4. 填写产品说明、分类、截图、privacy policy、支持网址和认证说明。
5. 在审核备注中说明：远程服务只返回数据，所有插件逻辑都在包内。
6. 提交认证。

## 审核备注模板

```text
ENHE Promotion Manager is a Manifest V3 operator extension. It captures the active product URL after user action and generates guarded Codex commands or hosted ENHE run payloads for product promotion workflows. The extension does not auto-publish to third-party platforms, does not bypass login/captcha/risk controls, and does not package remote executable code. ENHE backend endpoints are used only for license validation, subscription credit reservation, checkout, billing portal, and hosted run data exchange.
```

## 收费订阅说明

不要把支付能力只放在插件本地执行；生产版必须由 ENHE 后端强制控制：

- 托管运行前校验 license。
- 运行前预留 usage credits。
- 运行完成后按实际消耗扣减。
- 失败时退回未使用的预留积分。
- 支付平台密钥和 webhook secret 只放在后端。

订阅价格和积分模型见 `docs/subscription-pricing.md`、`docs/billing-backend-contract.md` 和 `browser-extension/billing-contract.json`。
