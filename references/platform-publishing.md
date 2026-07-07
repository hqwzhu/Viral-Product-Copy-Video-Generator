# Platform Publishing Reference

Publishing capabilities are time-sensitive. Refresh official docs before implementing or claiming direct publishing.

## Default First-Version Modes

| Platform | Default mode | Notes |
| --- | --- | --- |
| YouTube | `official_api_publish` candidate | Official YouTube Data API can upload videos with OAuth and quota constraints. Generate packs first; publish only after user approval. |
| GitHub | `official_api_publish` candidate | Official APIs can create/update repository content, releases, issues, and discussions. Do not write to repos without approval. |
| TikTok | `official_api_publish` candidate | Content Posting API requires developer access and scopes. Treat as candidate until verified. |
| Douyin | `browser_assisted_publish` | Official publishing capabilities exist but permissions and review are constrained. Do not bypass platform controls. |
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

## Reference URLs

- YouTube videos.insert: https://developers.google.com/youtube/v3/docs/videos/insert
- GitHub Contents API: https://docs.github.com/en/rest/repos/contents
- GitHub Releases API: https://docs.github.com/en/rest/releases/releases
- GitHub Discussions GraphQL: https://docs.github.com/en/graphql/guides/using-the-graphql-api-for-discussions
- TikTok Content Posting API: https://developers.tiktok.com/doc/content-posting-api-get-started/
- Douyin publishing solution: https://open.douyin.com/platform/resource/docs/ability/content-management/douyin-publish-solution

