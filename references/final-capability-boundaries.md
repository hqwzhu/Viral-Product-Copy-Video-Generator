# Final Capability Boundaries

Use this reference when the user asks for full automation.

## What The Skill Can Automate Locally

- Parse public product URLs, saved HTML, rendered page text, or Codex/browser structured snapshots into product profiles.
- Capture public product URLs with Playwright Chromium into structured browser-visible snapshots for product intake.
- Run `scripts/product_url_reader.py` to read one or more product URLs into per-URL structured browser snapshots, normalized product profiles, and correct next workflow commands.
- Run an end-to-end local workflow from one product source through `scripts/run_promotion_workflow.py`, producing intake, competitor discovery, generated content, video status, publish automation status, metrics recovery status, and a workflow manifest.
- Run due promotion jobs from a local JSON schedule through `scripts/automation_scheduler.py`, including state tracking and Windows Task Scheduler script generation.
- Generate platform-native copy, articles, voiceover scripts, storyboards, publish packs, result templates, and retrospective templates.
- Render deterministic MP4 videos from generated platform content with captions, optional voiceover audio files, or Windows SAPI review voiceover when `ffmpeg` is available.
- Generate platform research docs, risk matrices, reference project notes, and self-learning notes.
- Generate platform competitor discovery tasks and run official public search connectors where credentials/access allow.
- Collect YouTube competitor evidence through official search/video/channel APIs and GitHub competitor evidence through public search APIs.
- Open public platform search pages with Playwright Chromium and save browser-visible competitor search snapshots for YouTube, Zhihu, Xiaohongshu, Douyin, GitHub, TikTok, and similar platforms.
- Capture multi-result browser-visible search snapshots for YouTube, Zhihu, Xiaohongshu, Douyin, GitHub, TikTok, and similar platforms without using private endpoints or hidden browser tokens.
- Run a standalone keyword-to-viral-library discovery pass with `scripts/viral_discovery_runner.py`, chaining browser-visible platform search, normalized captures, viral material ranking, creator leaderboard generation, and optional safe follow-up queues.
- Run product-driven multi-query viral discovery with `scripts/multi_query_viral_discovery.py`, deriving multiple search queries from a product profile or workflow manifest, planning or running one public discovery pass per query, and merging/deduping ranked viral materials and creators.
- Rank captured cross-platform search results into a viral material library with top titles, hooks, creators, visible metrics, reusable patterns, and source evidence paths.
- Group ranked viral materials into a creator/account leaderboard and safe creator follow-up tasks using only observed public/browser-visible evidence.
- Run safe creator/account follow-up research through supported official/public connectors for YouTube and GitHub, while routing Zhihu, Xiaohongshu, Douyin, TikTok, and unverified platforms to browser-visible evidence requests.
- Generate follow-up capture tasks from the viral material library, routing public YouTube/GitHub URLs to safe capture candidates and routing Zhihu, Xiaohongshu, Douyin, TikTok, and unverified platforms to browser-assisted or user-export evidence.
- Execute safe public follow-up capture tasks into a deep competitor library, attempt public browser-visible snapshots for queued browser-assisted platform pages when explicitly enabled, and write manual/browser evidence requests when login, captcha, verification, draft, preview, or access-denied content appears.
- Rewrite generated platform content, video scripts, storyboards, and publish-pack content with observed viral/deep competitor structures before video rendering, while keeping competitor titles, hooks, and metrics as evidence metadata rather than product claims.
- Read user-provided competitor URLs, exported data, screenshots, or notes and turn them into deconstruction reports.
- Import real post-publish metrics from CSV, JSON, text exports, Codex/browser structured snapshots, GitHub public repository data, and YouTube official statistics when `YOUTUBE_API_KEY` is provided.
- Capture public/browser-visible post-publish metrics from registered published URLs with `scripts/post_publish_metrics_capture.py`, write a metrics export for recovery, and generate manual evidence requests when metrics are hidden behind login, captcha, private analytics, or business systems.
- Coordinate post-publish metrics recovery from workflow manifests, publish queues, published item JSON, published URLs, structured metric snapshots, GitHub repos, YouTube video IDs, and user-provided business exports without fabricating missing data.
- Execute approved official publishing actions for GitHub and YouTube when the correct environment token and explicit approval phrase are supplied.
- Build a publish execution queue that routes GitHub and YouTube into official dry-run/approved executor calls and routes Zhihu, Xiaohongshu, Douyin, and unverified platforms into manual/browser-assisted publish tasks.
- Audit publish readiness for a workflow or queue, including target information, queue state, credential presence by environment variable name, approval status, and next actions without storing secret values.
- Prepare browser-assisted/manual publishing payloads for Zhihu, Xiaohongshu, Douyin, TikTok, and similar platforms with `scripts/browser_publish_assistant.py`, including clipboard text, form-fill helper scripts, publisher entry URLs, checklists, and post-publish URL registration commands.
- Audit official platform access boundaries with `scripts/platform_access_audit.py`, mapping implemented official APIs, official app-review candidates, manual/browser-assisted fallback rules, required environment variable names, and metric evidence requirements.
- Register proven published URLs from official execution reports, publish queues, or manual/browser-assisted evidence into a standard published-items report for later metrics recovery.
- Capture browser-visible post-publish snapshots, saved HTML, copied text, or public published URLs and register them only when they resolve to a real platform URL rather than a draft, editor, preview, localhost, or unknown-platform page.
- Run a one-command local operating cycle that chains workflow generation, guarded publish queue, published URL registration, and metrics recovery while preserving approval gates and evidence requirements.
- Audit final-agent readiness with `scripts/final_capability_audit.py`, including local scripts, browser runtime, `ffmpeg`, credential presence, platform publishing limits, real metrics inputs, and self-evolution boundaries.
- Audit controlled self-evolution with `scripts/self_evolution_audit.py`, including runtime gaps, repository status, installed Codex Skill drift, safe install candidates, and approved local Skill sync.
- Run a YouTube OAuth consent flow and upload in the same process without saving OAuth tokens.

## What Requires Official Authorization

- YouTube uploads require Google/YouTube OAuth, approved scopes, quota, and explicit user approval.
- GitHub repository writes require a GitHub token or GitHub App permissions and explicit user approval.
- TikTok Direct Post requires developer app access, approved scopes, and creator authorization.
- Douyin official publishing requires open-platform app permissions, approved scopes, and user authorization.
- Platform analytics require official API access or user-exported evidence.
- Orders and revenue require business-system exports or user-provided analytics evidence; public social platforms generally cannot prove those values.
- Public post pages may expose views, likes, comments, saves, shares, or similar counters, but hidden analytics, order attribution, and revenue still require official exports, screenshots, or business-system evidence.

## What Must Stay Browser-Assisted Or Manual

- Zhihu and Xiaohongshu publishing should remain manual or browser-assisted unless stable official creator publishing access is verified.
- Browser-assisted publish preparation may open a user-visible creator page and prepare field payloads, but it must not auto-login, solve challenges, or click the final publish/submit button.
- Any platform flow that triggers captcha, risk control, account verification, or login prompts must stop for user action.
- The agent must not extract, save, print, or reuse cookies, passwords, API keys, or hidden browser tokens.

## What The Skill Must Not Claim

- Do not claim auto-publishing works until code has executed through official APIs with real user authorization.
- Do not claim competitor metrics unless they were observed from public pages, official APIs, exports, or user-provided evidence.
- Do not infer hidden follower counts, private analytics, creator income, orders, or conversion performance from public creator ranking.
- Do not treat creator follow-up dry-runs, queued evidence requests, or search plans as captured creator performance data.
- Do not treat a promotion cycle as fully published unless the publish queue or published-items report contains proven published URLs.
- Do not copy competitor wording into final product copy; reuse only structure, sequence, and safe pattern labels.
- Do not claim revenue, orders, leads, views, likes, comments, or click data without evidence.
- Do not treat `post_publish_metrics_capture.py` manual evidence requests as recovered data; only captured metric records, official APIs, exports, screenshots, or user-provided evidence count.
- Do not call unofficial endpoints "official APIs."

## Self-Evolution Rule

The Skill may research, write notes, check local tool availability, detect installed Skill drift, and propose upgrades. `scripts/final_capability_audit.py` and `scripts/self_evolution_audit.py` may install only explicit allowlisted runtime dependencies, such as Playwright Chromium, when the command includes `--install-safe-missing-tools`. `scripts/self_evolution_audit.py` may sync reviewed local Skill files into the installed Codex Skill directory only when the command includes `--sync-installed-skill --approval I_APPROVE_SKILL_SYNC`. It must not silently install arbitrary packages, modify itself from unreviewed network code, delete installed Skill files during sync, or upgrade dependencies without an explicit command and a clear source/risk note.
