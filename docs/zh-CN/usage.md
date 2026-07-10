# 使用说明

## 单个产品 URL

```powershell
python scripts\skill_entry.py `
  --link "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --out-dir ".\promotion-output"
```

入口脚本会生成真实运行 playbook，执行最高自动化的安全流程，并写出最终 readiness 矩阵。每个主要阶段完成后，使用 `reports\promotion-manager\final-readiness\final-capability-readiness.md` 作为阶段进度报告，汇报当前阶段、已实现目标、未实现目标、下一步计划和预计剩余时间。

直接读取 URL 时，`product_url_reader.py` 会先尝试浏览器结构化快照，再尝试静态 HTML，最后对本机访问超时的公开页面使用公开网页文本 fallback。若不希望使用第三方文本 fallback，可传 `--disable-web-text-fallback`；如果 Codex 已经保存网页文本，可传 `--web-text-fallback-file`。

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

### 动态搜索页超时处理

抖音、小红书等公开搜索页可能长期保持网络连接，等待 `networkidle` 会超时。补采公开视频证据时，建议使用有界的 `domcontentloaded` 等待：

```powershell
python scripts\final_capability_runner.py `
  --url "https://www.enhe-tech.com.cn/software/windows-ai" `
  --platforms douyin,xiaohongshu `
  --run-follow-up-captures `
  --capture-browser-assisted-follow-ups `
  --sample-video-frames `
  --timeout-ms 15000 `
  --wait-until domcontentloaded `
  --multi-query-browser-search-timeout-ms 15000 `
  --multi-query-browser-search-wait-until domcontentloaded `
  --multi-query-run-follow-up-captures `
  --multi-query-capture-browser-assisted-follow-ups `
  --multi-query-sample-video-frames `
  --out-dir ".\promotion-output\enhe-video-evidence-rerun"
```

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

如果还没有真实发布数据，只是想验证数据回收、复盘和下一轮优化链路，可以生成明确标记的 synthetic/demo 证据：

```powershell
python scripts\synthetic_evidence_generator.py `
  --product-url "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --run-recovery `
  --out-dir ".\promotion-output\synthetic-validation"
```

生成结果会带有 `SYNTHETIC_DEMO_DATA_DO_NOT_REPORT` 标记，只能用于本地流程验证，不能当作真实播放量、订单或收入数据汇报。

`final_capability_readiness.py` 会把 synthetic 验证单独显示在真实数据和下一轮优化两项里。synthetic ready 只证明本地回收链路跑通，真实表现项仍会保持 `waiting_real_data`，直到导入真实发布 URL、平台导出、评论和业务数据。

如果没有真实指标或业务证据，优化器会输出 `waiting_real_data`，不会编造表现。
## 爆款证据收件箱 fallback

当知乎、小红书、抖音等平台自动搜索不稳定，或者只能拿到浏览器可见内容时，先创建空模板：

```powershell
python scripts\viral_evidence_inbox_setup.py `
  --product-url "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --inbox-dir ".\viral-evidence-inbox" `
  --out-dir ".\promotion-output"
```

填入真实对标链接、可见正文、口播稿、平台导出或截图 OCR 文本后导入：

```powershell
python scripts\viral_evidence_inbox.py `
  --inbox-dir ".\viral-evidence-inbox" `
  --out-dir ".\promotion-output"
```

导入器会生成 `captured-search-results-*.json`、爆款内容库和博主榜单；只有截图而没有 OCR/复制文本时会标记为 `manual_text_required`。
