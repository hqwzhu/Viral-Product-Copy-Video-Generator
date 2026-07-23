# Chrome Web Store Listing Draft

## English (default)

### Name

ENHE Product Promo Maker

### Short Description

Turn product pages into promotional copy, video scripts, publishing assets, and guarded local or hosted promotion tasks.

### Detailed Description

Turn product pages into promotional copy, video scripts, publishing assets, and guarded local or hosted promotion tasks. After the user selects the current product page, ENHE Product Promo Maker captures its URL, lets the user choose target platforms and workflow depth, and prepares local Codex commands or hosted ENHE run payloads for review.

The extension validates ENHE licenses and estimates or reserves hosted credits before submitting a selected payload to the ENHE backend worker queue. The hosted worker processes only the reviewed task payload. Generated publishing assets remain subject to user approval, and the extension does not publish to third-party platforms on the user's behalf.

All extension logic is packaged locally. Remote ENHE endpoints return data only for license validation, checkout and billing, credit reservation, hosted-run submission, and hosted-run status. The extension does not load remote executable code, bypass login or captcha checks, or collect platform credentials, cookies, payment secrets, OAuth tokens, or webhook secrets.

## Simplified Chinese

### 名称

ENHE 产品推广素材生成器

### 简短说明

把产品网页变成推广文案、视频脚本和发布素材，并生成受控的本地或托管推广任务。

### 详细说明

把产品网页变成推广文案、视频脚本和发布素材，并生成受控的本地或托管推广任务。用户选择当前产品页面后，ENHE 产品推广素材生成器会读取页面 URL，让用户选择目标平台和工作流深度，并生成供审核的本地 Codex 命令或 ENHE 托管运行载荷。

提交所选载荷前，扩展会校验 ENHE 许可证，并估算或预留托管积分。托管 worker 仅处理用户已审核的任务载荷。发布素材必须由用户确认，扩展不会代替用户向第三方平台发布。

全部扩展逻辑均随安装包提供。ENHE 远程接口只返回许可证校验、结账和账单、积分预留、托管运行提交及状态数据。扩展不会加载远程可执行代码、绕过登录或验证码检查，也不会收集平台凭据、Cookie、支付密钥、OAuth token 或 webhook secret。

## Category

Productivity

## Permission Justification

- `activeTab`: capture the current product URL only after user action.
- `storage`: store local license and endpoint settings.
- `clipboardWrite`: copy generated Codex commands and hosted-run payloads.
- Host permission for `https://www.enhe-tech.com.cn/*`: validate license, reserve credits, open checkout/billing, and submit hosted-run payloads.

## Privacy Practices

The extension processes product URLs, selected workflow settings, license validation requests, usage reservation requests, and hosted-run payloads. It does not collect passwords, cookies, payment card numbers, captcha answers, or third-party platform secrets.

Privacy policy: https://www.enhe-tech.com.cn/promotion-manager/privacy
Terms: https://www.enhe-tech.com.cn/promotion-manager/terms
Refund policy: https://www.enhe-tech.com.cn/promotion-manager/refund
Support: https://www.enhe-tech.com.cn/promotion-manager/support

