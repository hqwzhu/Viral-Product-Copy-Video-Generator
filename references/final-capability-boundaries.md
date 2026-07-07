# Final Capability Boundaries

Use this reference when the user asks for full automation.

## What The Skill Can Automate Locally

- Parse public product URLs, saved HTML, rendered page text, or Codex/browser structured snapshots into product profiles.
- Capture public product URLs with Playwright Chromium into structured browser-visible snapshots for product intake.
- Run an end-to-end local workflow from one product source through `scripts/run_promotion_workflow.py`, producing intake, competitor discovery, generated content, video status, publish automation status, metrics recovery status, and a workflow manifest.
- Run due promotion jobs from a local JSON schedule through `scripts/automation_scheduler.py`, including state tracking and Windows Task Scheduler script generation.
- Generate platform-native copy, articles, voiceover scripts, storyboards, publish packs, result templates, and retrospective templates.
- Render deterministic MP4 videos from generated platform content with captions, optional voiceover audio files, or Windows SAPI review voiceover when `ffmpeg` is available.
- Generate platform research docs, risk matrices, reference project notes, and self-learning notes.
- Generate platform competitor discovery tasks and run official public search connectors where credentials/access allow.
- Collect YouTube competitor evidence through official search/video/channel APIs and GitHub competitor evidence through public search APIs.
- Open public platform search pages with Playwright Chromium and save browser-visible competitor search snapshots for YouTube, Zhihu, Xiaohongshu, Douyin, GitHub, TikTok, and similar platforms.
- Capture multi-result browser-visible search snapshots for YouTube, Zhihu, Xiaohongshu, Douyin, GitHub, TikTok, and similar platforms without using private endpoints or hidden browser tokens.
- Rank captured cross-platform search results into a viral material library with top titles, hooks, creators, visible metrics, reusable patterns, and source evidence paths.
- Generate follow-up capture tasks from the viral material library, routing public YouTube/GitHub URLs to safe capture candidates and routing Zhihu, Xiaohongshu, Douyin, TikTok, and unverified platforms to browser-assisted or user-export evidence.
- Execute safe public follow-up capture tasks into a deep competitor library, while writing manual/browser evidence requests for platforms that require visible user evidence or official access.
- Rewrite generated platform content, video scripts, storyboards, and publish-pack content with observed viral/deep competitor structures before video rendering, while keeping competitor titles, hooks, and metrics as evidence metadata rather than product claims.
- Read user-provided competitor URLs, exported data, screenshots, or notes and turn them into deconstruction reports.
- Import real post-publish metrics from CSV, JSON, text exports, GitHub public repository data, and YouTube official statistics when `YOUTUBE_API_KEY` is provided.
- Coordinate post-publish metrics recovery from workflow manifests, publish queues, published item JSON, published URLs, GitHub repos, YouTube video IDs, and user-provided business exports without fabricating missing data.
- Execute approved official publishing actions for GitHub and YouTube when the correct environment token and explicit approval phrase are supplied.
- Build a publish execution queue that routes GitHub and YouTube into official dry-run/approved executor calls and routes Zhihu, Xiaohongshu, Douyin, and unverified platforms into manual/browser-assisted publish tasks.
- Register proven published URLs from official execution reports, publish queues, or manual/browser-assisted evidence into a standard published-items report for later metrics recovery.
- Capture browser-visible post-publish snapshots, saved HTML, copied text, or public published URLs and register them only when they resolve to a real platform URL rather than a draft, editor, preview, localhost, or unknown-platform page.
- Run a YouTube OAuth consent flow and upload in the same process without saving OAuth tokens.

## What Requires Official Authorization

- YouTube uploads require Google/YouTube OAuth, approved scopes, quota, and explicit user approval.
- GitHub repository writes require a GitHub token or GitHub App permissions and explicit user approval.
- TikTok Direct Post requires developer app access, approved scopes, and creator authorization.
- Douyin official publishing requires open-platform app permissions, approved scopes, and user authorization.
- Platform analytics require official API access or user-exported evidence.
- Orders and revenue require business-system exports or user-provided analytics evidence; public social platforms generally cannot prove those values.

## What Must Stay Browser-Assisted Or Manual

- Zhihu and Xiaohongshu publishing should remain manual or browser-assisted unless stable official creator publishing access is verified.
- Any platform flow that triggers captcha, risk control, account verification, or login prompts must stop for user action.
- The agent must not extract, save, print, or reuse cookies, passwords, API keys, or hidden browser tokens.

## What The Skill Must Not Claim

- Do not claim auto-publishing works until code has executed through official APIs with real user authorization.
- Do not claim competitor metrics unless they were observed from public pages, official APIs, exports, or user-provided evidence.
- Do not copy competitor wording into final product copy; reuse only structure, sequence, and safe pattern labels.
- Do not claim revenue, orders, leads, views, likes, comments, or click data without evidence.
- Do not call unofficial endpoints "official APIs."

## Self-Evolution Rule

The Skill may research, write notes, check local tool availability, and propose upgrades. It must not silently install packages, modify itself from unreviewed network code, or upgrade dependencies without an explicit command and a clear source/risk note.
