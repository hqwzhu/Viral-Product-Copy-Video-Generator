# ENHE 产品推广素材生成器浏览器扩展上架指南

版本：0.5.3

本文用于把 `browser-extension/` 打包为可提交到 Chrome Web Store 和 Microsoft Edge Add-ons 的 ENHE Product Promo Maker 扩展包。

## 当前已发布版本

Chrome Web Store 条目 `dloklkbnmoigemnfigbkibogmgbieppl` 的 v0.5.3 已发布。其已验证归档为 `dist\v0.5.3\enhe-promotion-manager-0.5.3.zip`；它只是不可修改的历史验证资产，不是再次上传的操作指令。其商店图片、校验和与发行证据也均不可更改；不得重新打包、重新上传或替换 v0.5.3。下一版升级时，先提高扩展版本号，创建新的发行目录和证据集，再作为同一条目的更新提交。

商店本地化名称：

- 简体中文：`ENHE 产品推广素材生成器`
- 英文（默认）：`ENHE Product Promo Maker`

官方参考：

- Chrome Web Store 发布文档：https://developer.chrome.com/docs/webstore/publish
- Microsoft Edge 扩展发布文档：https://learn.microsoft.com/en-us/microsoft-edge/extensions-chromium/publish/publish-extension
- Chrome remote code 迁移说明：https://developer.chrome.com/docs/extensions/develop/migrate/remote-hosted-code

## 打包

在仓库根目录运行：

仅在提高版本号后，为下一版运行：

```powershell
python scripts\package_browser_extension.py --out-dir ".\dist\v<NEXT_VERSION>"
```

输出文件：

- `dist\v<NEXT_VERSION>\enhe-promotion-manager-<NEXT_VERSION>.zip`
- `dist\v<NEXT_VERSION>\browser-extension-package-report.json`
- `dist\v<NEXT_VERSION>\browser-extension-package-report.md`

把审核通过的商店图片放在：

- `dist\v<NEXT_VERSION>\store-assets\enhe-product-promo-maker-en-1280x800.png`
- `dist\v<NEXT_VERSION>\store-assets\enhe-product-promo-maker-zh-1280x800.png`

向现有商店条目上传下一版 ZIP，并保留其报告作为发行证据。

## 上架前检查

- 当前已发布版本保持 v0.5.3 不变；下一版与打包输出使用新的 `dist\v<NEXT_VERSION>` 目录。
- Manifest 使用 MV3。
- popup、CSS 和 JavaScript 均随扩展包本地提供。
- 不加载 remote code：没有远程 `<script src="https://...">`、动态 import、`importScripts`、`eval` 或 `new Function`。
- ENHE 远程接口只返回许可证校验、使用授权、托管运行请求、结账和账单门户所需的数据。
- 不打包平台密钥、支付密钥、Cookie、OAuth token 或 webhook secret。
- 扩展包包含 `icons/icon16.png`、`icons/icon48.png` 和 `icons/icon128.png`。
- 扩展包包含英文和简体中文 `_locales` 元数据；popup 首次启动时跟随浏览器语言，并记住用户手动选择的 `中文 / EN`。
- Privacy policy：`https://www.enhe-tech.com.cn/promotion-manager/privacy`。
- 支持网址：`https://www.enhe-tech.com.cn/promotion-manager/support`。
- 产品网站：`https://www.enhe-tech.com.cn/`。
- 法律页面位于 `docs/legal/`，商店 listing 和审核文案位于 `docs/store/`。
- 现有 Chrome Web Store 条目 ID 为 `dloklkbnmoigemnfigbkibogmgbieppl`；只更新该条目，不创建第二个条目。

## 权限说明

- `activeTab`：仅在用户操作扩展后读取当前产品页面 URL。
- `storage`：保存本地许可证和 endpoint 设置。
- `clipboardWrite`：仅按用户请求复制生成的本地命令和托管运行载荷。
- `https://www.enhe-tech.com.cn/*`：校验许可证、打开结账和账单页面、预留积分、提交托管运行载荷及查询状态。

所有扩展逻辑都在安装包内。远程服务仅返回数据，不向扩展提供可执行代码。

## 商业发布门槛

提交收费扩展前：

- 通过 HTTPS 部署 `backend/license-service/` 或等效的生产许可证服务。
- 设置 `DATABASE_URL`，执行 `npm run migrate`，并把 API 和托管 worker 作为隔离服务部署。参见 `deploy/promotion-manager/`。
- 配置真实的 Stripe Checkout prices、Customer Portal 和签名 webhook。
- 在 Stripe 测试模式验证 `checkout.session.completed`、`customer.subscription.updated`、`invoice.payment_succeeded` 和 `invoice.payment_failed`。
- 确认扩展可以校验真实测试许可证、预留托管积分、启动托管运行并通过已部署 API 查看状态 URL。
- 发布隐私政策、支持、退款/联系和产品页面。
- 准备展示本地命令生成、许可证校验、积分预留和托管运行载荷审核且不暴露秘密的截图。
- 所有扩展逻辑必须随安装包提供，远程接口只返回数据。
- Chrome Web Store 和 Microsoft Edge Add-ons 审核属于外部门槛；打包可自动完成，商店批准仍由商店决定。

## 本地化商店资料

### 简体中文

- 名称：`ENHE 产品推广素材生成器`
- 简短说明：`把产品网页变成推广文案、视频脚本和发布素材，并生成受控的本地或托管推广任务。`

### 英文（默认）

- 名称：`ENHE Product Promo Maker`
- 简短说明：`Turn product pages into promotional copy, video scripts, publishing assets, and guarded local or hosted promotion tasks.`

详细本地化说明使用 `docs/store/chrome-listing.md` 和 `docs/store/edge-listing.md` 中的已提交文案。

## Chrome Web Store 上架步骤

1. 创建或登录 Chrome Web Store Developer Dashboard 账号。
2. 按后台要求完成开发者注册和费用支付。
3. 打开条目 `dloklkbnmoigemnfigbkibogmgbieppl`，不要创建新条目。
4. 确认 v0.5.3 已发布后，再提高 manifest 的版本号；不要改动 v0.5.3 归档或条目历史。
5. 打包下一版，并将 `dist\v<NEXT_VERSION>\enhe-promotion-manager-<NEXT_VERSION>.zip` 作为该条目的更新上传。
6. 上传 `dist\v<NEXT_VERSION>\store-assets` 中下一版图标和两张已审核的本地化截图。
7. 按已提交文档填写本地化名称、简短说明、详细说明、分类、产品网站、支持网址和隐私政策字段。
8. 使用上面的权限说明填写 privacy practices，并说明扩展不收集平台密码、Cookie、支付密钥或 API token。
9. 说明收费功能：托管运行消耗 ENHE 订阅积分；本地命令生成可以保持免费或受试用限制。
10. 粘贴 `docs/store/reviewer-notes.md`，再次确认条目 ID 后提交下一版审核。若需要登录、账号验证或 captcha，由账号所有者完成后再继续。

## Microsoft Edge Add-ons 上架步骤

1. 创建或登录 Microsoft Partner Center 账号。
2. 如果已有 Microsoft Edge 扩展条目，打开现有提交，不为同一扩展创建替代条目。
3. 独立核验当前 Edge 条目状态。若 v0.5.3 已在该 Edge 条目发布，再提高 manifest 的版本号；若 v0.5.3 尚未发布，则按适用的 Edge 提交流程处理，不得把 Chrome 的发布状态当作 Edge 已发布。
4. 打包并上传 `dist\v<NEXT_VERSION>\enhe-promotion-manager-<NEXT_VERSION>.zip` 作为下一版更新。
5. 上传 `dist\v<NEXT_VERSION>\store-assets` 中下一版图标和两张已审核的本地化截图。
6. 填写本地化产品说明、分类、隐私政策、支持网址、权限说明和认证说明。
7. 在审核备注中说明远程服务只返回数据，全部扩展逻辑都在安装包内。
8. 确认生成的发布素材需要用户批准后提交下一版认证。若需要登录、账号验证或 captcha，由账号所有者完成后再继续。

## 审核备注模板

```text
ENHE Product Promo Maker is a Manifest V3 extension that turns a product page selected by the user into promotional copy, video scripts, publishing assets, and guarded local commands or hosted ENHE run payloads. It reads the active product URL only after user action. All extension logic is packaged locally; ENHE endpoints return data only for license validation, checkout and billing, credit reservation, hosted-run queue submission, and hosted-run status. The extension does not publish to third-party platforms without user approval, bypass login/captcha/risk controls, or load remote executable code.
```

## 收费订阅说明

使用 ENHE 网站账单页面，不在扩展内处理支付。生产环境必须由后端强制执行：

- 托管运行前校验许可证。
- 运行前预留积分。
- 运行完成后按实际消耗结算积分。
- 失败时退回未使用的预留积分。
- 支付平台密钥和 webhook secret 只保存在后端。

订阅价格和积分模型见 `docs/subscription-pricing.md`、`docs/billing-backend-contract.md` 和 `browser-extension/billing-contract.json`。
