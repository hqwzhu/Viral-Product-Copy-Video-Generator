# 使用说明

## 单个产品 URL

```powershell
python scripts\skill_entry.py `
  --link "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --out-dir ".\promotion-output"
```

入口脚本会生成真实运行 playbook，执行最高自动化的安全流程，并写出最终 readiness 矩阵。

## 网站 URL 自动发现产品页

```powershell
python scripts\skill_entry.py `
  --link "https://example.com" `
  --link-mode site `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --discovery-top-n 25 `
  --out-dir ".\promotion-output"
```

适用于 AI 工具站、SaaS 官网、电商站或文档站。Skill 会先从公开链接和 sitemap 中发现候选产品页，再进入推广流程。

## 爆款竞品研究

```powershell
python scripts\multi_query_viral_discovery.py `
  --workflow-manifest ".\promotion-output\reports\promotion-manager\agent-run\workflow-manifest.json" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --top-n 20 `
  --out-dir ".\promotion-output"
```

该流程只使用公开或浏览器可见证据，不抓取私有接口，不提取隐藏媒体 token。

## 生成文案和视频

```powershell
python scripts\render_video.py `
  --content-json ".\promotion-output\reports\promotion-manager\generated-content\product-platform-content.json" `
  --platform douyin `
  --out ".\promotion-output\videos\product-douyin.mp4"
```

带口播音频：

```powershell
python scripts\render_video.py `
  --content-json ".\promotion-output\reports\promotion-manager\generated-content\product-platform-content.json" `
  --platform youtube `
  --voiceover-audio ".\voiceover.wav" `
  --out ".\promotion-output\videos\product-youtube.mp4"
```

内容审核桥接包：

```powershell
python scripts\promotion_manager.py review `
  --product-name "Product" `
  --product-url "https://example.com/product" `
  --audience "creators, founders" `
  --value-proposition "Turns product pages into launch content" `
  --out-dir ".\promotion-output"
```

审核步骤会写入 `reports\promotion-manager\cheat-review\*-cheat-review-pack.json`，并为每个平台生成可交给 Codex `cheat-score` 的草稿。它只准备审核输入，不会自动写预测日志。

## 发布

生成受保护发布队列：

```powershell
python scripts\publish_readiness_runner.py `
  --workflow-manifest ".\promotion-output\reports\promotion-manager\agent-run\workflow-manifest.json" `
  --build-queue `
  --github-repo owner/repo `
  --youtube-video-file ".\promotion-output\videos\product-youtube.mp4" `
  --out-dir ".\promotion-output"
```

准备浏览器/手动发布包：

```powershell
python scripts\browser_publish_assistant.py `
  --publish-queue ".\promotion-output\reports\promotion-manager\publish-queue\publish-queue.json" `
  --out-dir ".\promotion-output"
```

生成发布与真实证据解锁包：

```powershell
python scripts\launch_unlock_pack.py `
  --publish-queue ".\promotion-output\reports\promotion-manager\publish-queue\publish-queue.json" `
  --publish-readiness ".\promotion-output\reports\promotion-manager\publish-readiness\publish-readiness.json" `
  --out-dir ".\promotion-output"
```

该解锁包会输出 `reports/promotion-manager/launch-unlock/launch-unlock.json`、检查清单和下一步命令，只记录凭证变量名和准备状态，不保存真实密钥值。

最终能力 runner 会在存在发布队列时为每个产品 run 自动创建同样的解锁包。使用 `--platform-publish-url platform=url` 可以把浏览器辅助发布入口保留进解锁包。

浏览器辅助发布会准备 payload、可选填写可见字段、写截图，并在最终发布前停止：

```powershell
python scripts\browser_publish_session.py `
  --publish-queue ".\promotion-output\reports\promotion-manager\publish-queue\publish-queue.json" `
  --platform-publish-url "xiaohongshu=https://creator.xiaohongshu.com/" `
  --run-form-fill `
  --out-dir ".\promotion-output"
```

官方 API 发布只有在凭证、目标和审批都存在时才执行：

```powershell
python scripts\publish_executor.py `
  --platform github `
  --github-action file `
  --github-repo owner/repo `
  --path PROMOTION.md `
  --content-file ".\promotion-output\reports\promotion-manager\generated-content\product-platform-content.md" `
  --execute `
  --approval I_APPROVE_PUBLISH `
  --out-dir ".\promotion-output"
```

## 周期自动化

创建本地周期任务配置：

```powershell
python scripts\automation_scheduler.py init `
  --config ".\promotion-automation.json" `
  --job-id "product-weekly" `
  --browser-url "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --interval-days 7 `
  --output-root ".\promotion-output\automation" `
  --auto-search-competitors `
  --enable-multi-query-viral-discovery `
  --run-follow-up-captures `
  --capture-browser-assisted-follow-ups `
  --enable-publish-queue `
  --enable-browser-publish-assistant `
  --enable-metrics-recovery `
  --enable-next-round-optimization
```

运行到期任务或生成 Windows Task Scheduler 注册脚本：

```powershell
python scripts\automation_scheduler.py run --config ".\promotion-automation.json" --force
python scripts\automation_scheduler.py windows-task --config ".\promotion-automation.json" --out-file ".\register-enhe-promotion-task.ps1" --time "09:00"
```

周期任务仍然不会绕过凭证、平台审核、`I_APPROVE_PUBLISH`、登录、验证码、风控或最终浏览器发布确认。

## 指标回收和下一轮优化

登记真实发布 URL：

```powershell
python scripts\published_items.py `
  --platform xiaohongshu `
  --published-url "https://www.xiaohongshu.com/explore/real-note-id" `
  --evidence ".\screenshots\xhs-published.png" `
  --out-dir ".\promotion-output"
```

运行发布后性能监控：

```powershell
python scripts\performance_monitor.py --out-dir ".\promotion-output"
```

它会串联公开/浏览器可见指标抓取、评论和需求信号抓取、可选业务归因、指标合并、下一轮优化和历史快照。

发布前或发布后可以先生成本地证据收件箱模板：

```powershell
python scripts\real_evidence_inbox_setup.py `
  --product-url "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --inbox-dir ".\promotion-evidence-inbox" `
  --out-dir ".\promotion-output"
```

多个证据文件可以使用本地收件箱：

```powershell
python scripts\real_evidence_inbox.py `
  --inbox-dir ".\promotion-evidence-inbox" `
  --out-dir ".\promotion-output"
```

如果没有真实指标或业务证据，优化器会输出 `waiting_real_data`，不会编造表现。
