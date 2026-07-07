# Final Capability Boundaries

Use this reference when the user asks for full automation.

## What The Skill Can Automate Locally

- Parse public product URLs or saved HTML into structured product profiles.
- Generate platform-native copy, articles, voiceover scripts, storyboards, publish packs, result templates, and retrospective templates.
- Render deterministic MP4 draft videos from generated platform content when `ffmpeg` is available.
- Generate platform research docs, risk matrices, reference project notes, and self-learning notes.
- Generate platform competitor discovery tasks and run official public search connectors where credentials/access allow.
- Read user-provided competitor URLs, exported data, screenshots, or notes and turn them into deconstruction reports.
- Import real post-publish metrics from CSV, JSON, text exports, GitHub public repository data, and YouTube official statistics when `YOUTUBE_API_KEY` is provided.
- Execute approved official publishing actions for GitHub and YouTube when the correct environment token and explicit approval phrase are supplied.

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
- Do not claim revenue, orders, leads, views, likes, comments, or click data without evidence.
- Do not call unofficial endpoints "official APIs."

## Self-Evolution Rule

The Skill may research, write notes, check local tool availability, and propose upgrades. It must not silently install packages, modify itself from unreviewed network code, or upgrade dependencies without an explicit command and a clear source/risk note.
