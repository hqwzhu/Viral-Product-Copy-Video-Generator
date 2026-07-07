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

`scripts/publish_executor.py` supports:

- GitHub file create/update through the repository contents REST API.
- GitHub issue creation through the issues REST API.
- GitHub release creation through the releases REST API.
- YouTube video upload through `videos.insert` when an OAuth access token is available.

The executor defaults to dry-run. Real writes require `--execute --approval I_APPROVE_PUBLISH` plus the relevant environment credential. It must not write credentials to reports.

## Reference URLs

- YouTube videos.insert: https://developers.google.com/youtube/v3/docs/videos/insert
- GitHub Contents API: https://docs.github.com/en/rest/repos/contents
- GitHub Releases API: https://docs.github.com/en/rest/releases/releases
- GitHub Discussions GraphQL: https://docs.github.com/en/graphql/guides/using-the-graphql-api-for-discussions
- TikTok Content Posting API: https://developers.tiktok.com/doc/content-posting-api-get-started/
- Douyin publishing solution: https://open.douyin.com/platform/resource/docs/ability/content-management/douyin-publish-solution
- Douyin upload/create video APIs: https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/create/upload/ and https://open.douyin.com/platform/resource/docs/openapi/video-management/douyin/create/create-video
- Xiaohongshu open platform docs: https://open.xiaohongshu.com/document/api
