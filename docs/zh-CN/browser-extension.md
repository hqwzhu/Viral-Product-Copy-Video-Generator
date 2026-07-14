# 浏览器插件

`browser-extension/` 是 ENHE Promotion Manager 的 Chrome Manifest V3 插件成品目录。它用于从当前产品页面生成 Codex Skill 命令、浏览器辅助发布命令、证据回收命令、定期自动化命令，也可以对接 ENHE 托管运行、license 和 usage credits。

## 能力

- 读取用户当前打开的产品页 URL 和标题。
- 选择 YouTube、知乎、小红书、抖音、GitHub 等目标平台。
- 生成 `scripts/skill_entry.py`、`scripts/browser_publish_session.py`、`scripts/launch_unlock_pack.py`、`scripts/real_evidence_inbox_setup.py`、`scripts/real_evidence_inbox.py`、`scripts/performance_monitor.py`、`scripts/final_capability_readiness.py` 和 `scripts/automation_scheduler.py` 命令。
- 估算收费订阅积分消耗，避免 token 和视频渲染成本造成亏损。
- 本地保存 license key，并支持调用 ENHE license endpoint 校验订阅。
- 在托管运行前调用 usage authorization endpoint 预留 credits。
- 生成 hosted run payload，提交给 ENHE hosted run endpoint。
- 打开 ENHE checkout 和 billing portal。
- 在页脚展示开发者信息、网站网址、产品页和 GitHub，用于网站引流。

## 安全边界

- 插件不直接执行 Codex。
- 插件不自动登录任何第三方平台。
- 插件不绕过验证码、风控、平台审核或账号授权。
- 插件不点击最终发布按钮。
- 插件不存储平台密钥、支付密钥、cookie、OAuth token 或 webhook secret。
- 收费订阅必须由 ENHE 后端做 license、usage、webhook 和扣费控制。

## 本地加载

1. 打开 `chrome://extensions`。
2. 打开 Developer mode。
3. 点击 Load unpacked。
4. 选择仓库内的 `browser-extension` 目录。
5. 固定 ENHE Promotion Manager 到浏览器工具栏。

## 打包成上架包

```powershell
python scripts\package_browser_extension.py --out-dir ".\dist"
```

输出：

- `dist\enhe-promotion-manager-<version>.zip`
- `dist\browser-extension-package-report.json`
- `dist\browser-extension-package-report.md`

上架步骤见 `docs/zh-CN/extension-store-submission.md`。提交前确认 `browser-extension-package-report.json` 的 `status` 为 `ready`。

## 收费订阅

默认积分模型：

- Playbook command：0 credits。
- Research run：3 credits。
- Full Skill run：4 credits。
- Browser publish session：2 credits。
- Launch unlock pack：2 credits。
- Real evidence inbox setup：1 credit。
- Real evidence inbox：2 credits。
- Performance monitor：2 credits。
- Final readiness audit：1 credit。
- Automation due run：4 credits。
- Deep strategy review：额外 15 credits。
- Hosted MP4 add-on：额外 3 credits。

订阅建议：

- Free：5 credits，用于体验。
- Starter：60 credits / USD 29 月。
- Growth：220 credits / USD 99 月。
- Scale：800 credits / USD 299 月。

后端必须在 hosted run 前校验 license 并预留 credits，在任务完成后按实际 token、视频秒数和工作流类型扣减。具体契约见 `docs/billing-backend-contract.md`。

## 开发者信息

- Developer: ENHE AI
- Website: https://www.enhe-tech.com.cn/
- Product page: https://www.enhe-tech.com.cn/promotion-manager
- Repository: https://github.com/hqwzhu/Viral-Product-Copy-Video-Generator.git

## 0.5.2 中英文界面

- 插件首次打开时自动跟随 Chrome 界面语言：中文环境使用中文，其他环境使用英文。
- 右上角提供 `中文 / EN` 切换，用户选择会保存在插件本地存储中，后续打开继续使用该语言。
- 静态标签、动态状态、校验提示、套餐与点数估算均支持中英文。
- 商店名称、简介和工具栏标题通过 Chrome `_locales` 资源提供中英文版本。
- 16/48 像素工具栏图标保持无文字，128 像素商店图标采用 ENHE 品牌标识和透明安全边距。
