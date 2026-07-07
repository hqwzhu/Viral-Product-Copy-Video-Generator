# Platform Publishing Reference

Publishing capabilities are time-sensitive. Refresh official docs before implementing or claiming direct publishing.

## Default First-Version Modes

| Platform | Default mode | Notes |
| --- | --- | --- |
| YouTube | `official_api_publish` candidate | Official YouTube Data API can upload videos with OAuth and quota constraints. Generate packs first; publish only after user approval. |
| GitHub | `official_api_publish` candidate | Official APIs can create/update repository content, releases, issues, and discussions. Do not write to repos without approval. |
| TikTok | `official_api_publish` candidate | Content Posting API requires developer access and scopes. Treat as candidate until verified. |
| Douyin | `browser_assisted_publish` | Official publishing APIs exist, but first version uses browser-assisted/manual mode until app permissions, review, and user authorization are verified. |
| Xiaohongshu | `manual_publish_required` | Default to manual/browser-assisted drafts. Do not use unverified direct publishing endpoints. |
| Zhihu | `manual_publish_required` | Default to manual/browser-assisted drafts. Do not use unofficial direct publishing endpoints. |

## Safety Rules

- No automatic login.
- No cookie/token/password storage.
- No captcha bypass.
- No final publish click by the agent.
- No fabricated published URL.
- No fabricated platform data.
- All publishing requires human approval.

## Official Executor Coverage

`scripts/publish_queue.py` converts generated publish packs into a single queue:

- GitHub and YouTube records can call `scripts/publish_executor.py` in dry-run mode by default.
- Zhihu, Xiaohongshu, Douyin, and unverified platforms are written as manual or browser-assisted tasks with copy-ready drafts.
- Real official writes still require `--execute --approval I_APPROVE_PUBLISH` and the relevant environment credential.

`scripts/publish_readiness_runner.py` audits an existing queue or builds one first with `--build-queue`. It reports per-platform readiness, missing target fields, credential presence by environment variable name, approval status, and next actions. It does not store secret values and does not bypass the explicit approval gate.

`scripts/platform_access_audit.py` creates the official access boundary report before implementation or execution decisions. It maps each platform to implemented official API paths, official app-review candidates, manual/browser-assisted fallbacks, metrics evidence sources, required environment variable names, and implementation gaps. Use `--check-live` only when you want to verify that official documentation URLs are reachable.

`scripts/publish_executor.py` supports:

- GitHub file create/update through the repository contents REST API.
- GitHub issue creation through the issues REST API.
- GitHub release creation through the releases REST API.
- YouTube video upload through `videos.insert` when an OAuth access token is available.
- YouTube OAuth consent and same-process upload through `scripts/youtube_oauth_publish.py`.

The executor defaults to dry-run. Real writes require `--execute --approval I_APPROVE_PUBLISH` plus the relevant environment credential. It must not write credentials to reports.
The YouTube OAuth helper also defaults to dry-run. Execution requires a Google OAuth client ID and client secret from environment variables, opens or prints a Google authorization URL, exchanges the authorization code for a temporary access token, uploads, and does not save the token.

## Reference URLs

- Google OAuth 2.0 for installed apps: https://developers.google.com/identity/protocols/oauth2/native-app
- YouTube videos.insert: https://developers.google.com/youtube/v3/docs/videos/insert
- GitHub Contents API: https://docs.github.com/en/rest/repos/contents
- GitHub Releases API: https://docs.github.com/en/rest/releases/releases
- GitHub Discussions GraphQL: https://docs.github.com/en/graphql/guides/using-the-graphql-api-for-discussions
- TikTok Content Posting API: https://developers.tiktok.com/doc/content-posting-api-get-started/
- Douyin publishing solution: https://open.douyin.com/platform/resource/docs/ability/content-management/douyin-publish-solution
- Douyin upload/create video APIs: https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/create/upload/ and https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/create/create-video
- Xiaohongshu open platform docs: https://open.xiaohongshu.com/document/api
