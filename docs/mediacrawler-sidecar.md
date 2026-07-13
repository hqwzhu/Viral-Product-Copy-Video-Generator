# MediaCrawler 本机 Sidecar 使用指南

本功能在用户电脑上运行固定版本的 MediaCrawler，为 Promotion Manager 补充小红书、抖音、知乎的公开内容、评论和页面可见指标。Chrome 登录态保留在本机；Cookie、授权头、签名参数和原始用户 ID 不进入命令行、不进入标准化输出，也不上传到 ENHE 或 GitHub。

## 适用范围

- 平台：小红书、抖音、知乎。
- 模式：关键词搜索、内容详情、创作者作品。
- 数据：正文、标题、脱敏作者、发布时间、标签、页面可见互动指标、一级评论；二级评论需显式开启。
- 不提供：验证码绕过、滑块求解、代理池、多账号轮换、自动登录、媒体下载。

项目所有者已确认取得当前商业产品所需的作者商业授权。授权凭证应保存在项目仓库之外；如果授权范围发生变化，必须先收窄产品使用范围。

## 固定版本

- 上游仓库：[NanmiCoder/MediaCrawler](https://github.com/NanmiCoder/MediaCrawler)
- 固定提交：`3bde9e2015f912f2e19ee63b615a0f48b9a90315`
- 环境：仓库外的独立 `uv`/Python 3.11 环境。
- 正常运行不会执行 `git pull`、依赖升级或自动切换提交。

ENHE 通过独立子进程调用固定 checkout，不把上游源码复制进主仓库，也不在主 Promotion Manager 进程中导入 MediaCrawler。一个轻量 bootstrap 只在 Sidecar 子进程中运行，用于补齐该固定提交的知乎 creator 参数映射，并在连接已有 Chrome 时避免主动关闭浏览器 context 或 Chrome 进程；固定 checkout 本身保持不变。

## 安装前只读检查

在项目根目录运行：

```powershell
python scripts\promotion_manager.py platform-data setup --check
```

该命令只读取并报告以下状态：

- Git、`uv` 和本机 Chrome 是否可用。
- Sidecar checkout、独立 Python、安装清单和本机身份脱敏盐是否存在。
- checkout 是否严格位于固定提交。
- CDP、连接已有浏览器、禁止媒体下载、最小 2 秒间隔等安全默认值是否仍然有效。

它不会克隆、下载、创建环境、修改 Chrome 或写入检查文件。`status=provider_unavailable` 表示尚未安装或检查未通过，不影响原有 Firecrawl、浏览器可见证据和人工证据流程。

## 显式安装

只有以下命令允许执行 Sidecar 网络安装：

```powershell
python scripts\promotion_manager.py platform-data setup --install
```

安装过程会：

1. 在仓库外的 ENHE 本机数据目录创建临时 staging checkout。
2. checkout 固定提交，不跟随 `main`。
3. 运行 `uv sync --python 3.11` 创建隔离环境。
4. 校验提交、安全配置和独立 Python。
5. 校验成功后才把 staging 原子移动为正式 checkout。
6. 在本机生成安装级身份脱敏盐和安装清单。

失败时 staging 会清理，未完成安装不会替换正式 checkout。若已存在但版本不匹配，安装命令会停止并要求显式维护更新，不会自动覆盖。

## Chrome 与登录

MediaCrawler 固定版本默认使用 Chrome CDP 和可见浏览器。推荐步骤：

1. 保持本机 Chrome 的调试端口可用。
2. 执行一次 `setup --check`，确认 `chrome`、`cdpMode` 和 `connectExisting` 为 `true`。
3. 运行最小采集命令。
4. 如果浏览器显示登录页面，由你亲自在该浏览器完成扫码、账号登录或确认。
5. 如果输出为 `waiting_login`，登录完成后重新执行原命令。
6. 如果出现验证码、滑块或账号验证，状态会变为 `manual_verification_required`；必须手动完成，程序不会自动求解。

不要在命令行传 Cookie。CLI 不提供 `--cookies` 参数。

## 采集命令

### 小红书

```powershell
python scripts\promotion_manager.py platform-data collect --platform xiaohongshu --mode search --query "AI 工具" --out-dir .\promotion-output
python scripts\promotion_manager.py platform-data collect --platform xiaohongshu --mode detail --target "https://www.xiaohongshu.com/explore/内容ID" --out-dir .\promotion-output
python scripts\promotion_manager.py platform-data collect --platform xiaohongshu --mode creator --target "https://www.xiaohongshu.com/user/profile/创作者ID" --out-dir .\promotion-output
```

### 抖音

```powershell
python scripts\promotion_manager.py platform-data collect --platform douyin --mode search --query "产品短视频" --out-dir .\promotion-output
python scripts\promotion_manager.py platform-data collect --platform douyin --mode detail --target "https://www.douyin.com/video/内容ID" --out-dir .\promotion-output
python scripts\promotion_manager.py platform-data collect --platform douyin --mode creator --target "https://www.douyin.com/user/创作者ID" --out-dir .\promotion-output
```

### 知乎

```powershell
python scripts\promotion_manager.py platform-data collect --platform zhihu --mode search --query "AI 内容生产" --out-dir .\promotion-output
python scripts\promotion_manager.py platform-data collect --platform zhihu --mode detail --target "https://www.zhihu.com/question/问题ID/answer/回答ID" --out-dir .\promotion-output
python scripts\promotion_manager.py platform-data collect --platform zhihu --mode creator --target "https://www.zhihu.com/people/创作者ID" --out-dir .\promotion-output
```

### 二级评论

默认最多读取每条内容 30 条一级评论，二级评论关闭。只有确实需要时显式开启：

```powershell
python scripts\promotion_manager.py platform-data collect --platform xiaohongshu --mode search --query "AI 工具" --include-sub-comments --out-dir .\promotion-output
```

## 安全默认值

| 项目 | 默认值或硬上限 |
|---|---|
| 同时运行任务 | 1 |
| 每次内容数 | 默认且最高 20 |
| 每条内容一级评论 | 默认且最高 30 |
| 二级评论 | 默认关闭 |
| 并发 | 1 |
| 页面间隔 | 上游固定配置至少 2 秒 |
| 单任务超时 | 默认 900 秒，最高 3600 秒 |
| 瞬时网络重试 | 最多 1 次 |
| 代理、媒体下载、多账号 | 关闭 |

可以把内容数、评论数和超时调低，不能通过普通 CLI 参数突破硬上限。

## 状态说明

| 状态 | 处理方式 |
|---|---|
| `ready` | 请求数据已标准化并写入下游证据 |
| `partial_ready` | 部分数据可用，查看清单中的计数和原因 |
| `waiting_login` | 在本机可见 Chrome 中手动登录后重试 |
| `manual_verification_required` | 手动完成验证码、滑块、扫码或账号确认 |
| `blocked_by_platform` | 停止任务，等待平台风控解除，不循环重试 |
| `no_results` | 请求完成但没有可用结果，人工检查关键词或目标 |
| `provider_unavailable` | 运行只读检查；原有 Provider 流程仍可使用 |
| `normalization_error` | 上游字段变化或数据无法安全映射，禁止直接导入原始数据 |
| `cancelled` | 用户取消，锁和本次临时数据已清理 |
| `error` | 查看脱敏原因和退出码 |

## 输出

每次运行位于：

```text
promotion-output/reports/promotion-manager/platform-data/mediacrawler/<run-id>/
```

主要文件：

- `run-manifest.json`：固定提交、平台、模式、限制、状态、计数、耗时、重试、脱敏和原始数据清理状态。
- `contents.jsonl`：标准化内容。
- `comments.jsonl`：标准化评论和父子关系。
- `creators.jsonl`：由本次标准化内容派生的脱敏创作者聚合。
- `owned-metrics.json`：只包含与真实发布登记精确匹配的自有内容指标。

同时更新现有：

- 爆款内容库。
- 创作者榜单。
- 评论证据和需求信号。

竞品数据不能进入自有效果恢复。匹配顺序为：

1. 精确 `platform + contentId`。
2. 只有发布登记没有 `contentId` 时，才允许精确规范化公开 URL。

标题、作者、关键词和文本相似度永远不能证明内容归属。

## 原始数据与 `--keep-raw`

原始 JSONL 默认只在任务运行期间存在，标准化完成后删除。调试时可以显式保留：

```powershell
python scripts\promotion_manager.py platform-data collect --platform douyin --mode search --query "AI 工具" --keep-raw --out-dir .\promotion-output
```

`--keep-raw` 会显示安全警告。原始文件可能包含 Token、签名参数或其他敏感字段：

- 只在本机短期排错。
- 不提交 Git。
- 不上传 ENHE、云盘、工单或聊天。
- 排错结束后手动删除对应 `raw` 目录。

整个 `promotion-output/` 已被 Git 忽略。

## 取消

在终端按 `Ctrl+C`。运行器会把状态转换为 `cancelled`，释放本次单任务锁并删除本次临时原始目录。它不枚举、终止或关闭 Chrome 进程；连接已有 Chrome 时，bootstrap 也不会主动关闭 browser context。

## 排错

### `uv` 不可用

先安装官方 `uv`，重新打开终端，再运行 `setup --check`。Promotion Manager 不会在只读检查中自动安装它。

### Chrome/CDP 不可用

确认 Chrome 已启动并开放本机调试端口，然后重新运行检查。不要把调试端口暴露到公网。

### 一直要求登录

确认登录发生在 Sidecar 连接的可见 Chrome 中。不要复制 Cookie 到 `.env` 或命令行。登录后重新执行最小命令。

### 验证码、滑块或账号确认

手动完成。程序不会自动识别、点击、绕过或循环重试。

### `blocked_by_platform`

立即停止采集。不要提高并发、启用代理或连续重试。等待平台限制解除后再使用更小数据量人工验证。

### `normalization_error`

不要直接把原始 JSONL导入下游。维护者应使用脱敏字段样本更新三平台映射，先让离线夹具和回归测试通过。

### 任务锁存在

先确认没有另一个 Sidecar 任务。若上一次进程已完全退出但锁仍存在，检查对应 `run-manifest.json` 和进程状态后再处理锁；不要在任务仍运行时删除锁。

## 固定提交更新

更新不是日常用户操作。维护者必须：

1. 选择一个完整的 40 位上游提交哈希。
2. 复核授权范围和安全默认值。
3. 更新固定提交常量和脱敏离线夹具。
4. 运行全部 `scripts/test_mediacrawler_sidecar.py` 测试。
5. 运行 Promotion Manager 聚焦回归测试。
6. 在隔离安装目录执行三平台最小人工冒烟测试。
7. 扫描标准化输出和日志，确认无 Cookie、Token、签名值和原始用户 ID。
8. 所有检查通过后才替换正式 checkout；失败时保留旧版本。

正常启动和 `setup --check` 都不会更新版本。

## 发布前人工冒烟

发布 V1 前，用户需在本机完成：

1. 三个平台各搜索最多 3 条内容。
2. 三个平台各采集一个内容详情。
3. 三个平台各采集最多 5 条一级评论。
4. 只在一个平台显式开启二级评论。
5. 验证爆款库、创作者榜单、评论证据和严格匹配的自有效果输入。
6. 扫描全部输出和日志中的敏感值。
7. 确认完成、取消和失败后 Chrome 仍保持打开。
8. 停止 Sidecar 后确认原有 Firecrawl、浏览器证据和人工证据流程仍能工作。
