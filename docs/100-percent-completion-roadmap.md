# 100% Completion Roadmap

This document is the operator-facing roadmap for turning ENHE Product Promo Maker from a strong local Skill into a production-ready promotion business. It separates local work Codex can finish from external gates that require the operator's real accounts, platform approvals, payment setup, server deployment, and business evidence.

## Ground Rules

- A module is not 100% until there is current evidence, not just code.
- Local code, docs, tests, packaging, and dry-run flows can be completed by Codex.
- Real publishing, real metrics, app review, store approval, Stripe live mode, payout compliance, and creator settlement need operator-owned accounts and approvals.
- Unsafe shortcuts do not count as completion: no cookie capture, simulated login, hidden token reuse, private endpoints, captcha bypass, auto-like/follow/comment, or final publish clicks.
- Manual publish packages are the primary publishing path. Official auto-publish ports stay dry-run-first until platform credentials, scopes, review, and explicit approval exist.

## Completion Summary

| Module | Current estimate | What makes it 100% |
| --- | ---: | --- |
| Codex Skill local promotion loop | 85% | A real product run proves intake, competitor research, content generation, publish pack, evidence inbox, readiness reporting, and installed Skill sync. |
| Copy, video, cover, detail image, publish pack | 85% | Every target platform has final title, copy, tags, first-batch comments, MP4 where required, cover PNG, detail PNGs, assets list, and tracking plan from a real product run. |
| Competitor research and web data | 80% | Playwright and optional Firecrawl are configured, public/official evidence is captured, and blocked platforms have imported real user evidence instead of empty search results. |
| Browser extension and commercialization infrastructure | 75% | HTTPS backend is deployed, PostgreSQL migration is run, Stripe live prices/webhooks work, hosted worker executes isolated jobs, legal/store pages are public, and Chrome/Edge approval is received. |
| True all-platform automatic publishing | 40% | Only platforms with verified official APIs, approved scopes, valid tokens, target files, account authorization, and explicit approval can be called. Platforms without official creator publishing remain manual/browser-assisted. |
| Creator tasks, settlement, and Monetize marketplace | 30% | Campaigns, creator tasks, submissions, evidence review, payout ledger, creator onboarding, payment provider, fraud review, and legal/tax process operate with real data. |

## 1. Codex Skill Local Promotion Loop

Current state: about 85%. The local workflow exists: `skill_entry.py`, `final_capability_runner.py`, `promotion_cycle_runner.py`, `final_capability_readiness.py`, `real_run_playbook.py`, evidence inbox, and readiness audits.

Missing to 100%:

- A current real product run with real input URL, not only examples.
- Proof that Playwright Chromium is installed when browser capture is needed.
- Proof that `ffmpeg` and `Pillow` are installed when MP4/PNG assets are required.
- Installed Codex Skill synced with reviewed repository files.
- A final readiness report showing each stage completed or externally gated.
- Regression tests and compile checks run after the latest changes.

Codex can complete:

- Run local audits and tests.
- Generate real-run playbooks.
- Generate readiness matrices and launch unlock packs.
- Sync the installed Skill after explicit approval.
- Add or update docs/scripts/tests.

User must do:

- Provide a real product URL or website URL.
- Approve installed Skill sync only after reviewing the repo state.
- Provide real evidence files after manual publishing.

Detailed user steps:

1. Open PowerShell.
2. Go to the project folder:

```powershell
cd "C:\Users\HU\Documents\Viral-Product-Copy-Video-Generator"
```

3. Install browser runtime if the audit says Chromium is missing:

```powershell
python scripts\final_capability_audit.py --install-safe-missing-tools --safe-install playwright_chromium --out-dir ".\promotion-output"
```

4. Run one real product through the Skill:

```powershell
python scripts\skill_entry.py `
  --link "https://your-real-product-url.example" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --out-dir ".\promotion-output"
```

5. Review the final matrix:

```powershell
notepad ".\promotion-output\reports\promotion-manager\final-readiness\final-capability-readiness.md"
```

Acceptance evidence:

- `promotion-output/reports/promotion-manager/skill-entry/skill-entry.json`
- `promotion-output/reports/promotion-manager/final-run/final-capability-run.json`
- `promotion-output/reports/promotion-manager/final-readiness/final-capability-readiness.json`
- `promotion-output/reports/promotion-manager/capability/final-capability-audit.json`

## 2. Copy, Video, Cover, Detail Image, Publish Pack

Current state: about 85%. The generator can create platform copy, scripts, first-batch comments, MP4 drafts, cover PNGs, detail PNGs, and publish-pack asset manifests.

Missing to 100%:

- `ffmpeg` installed and verified for MP4 rendering.
- `Pillow` installed and verified for PNG generation.
- Real product-specific assets generated after the latest workflow run.
- YouTube and Douyin video files attached to the publish pack when those platforms require video.
- Publish pack checked for every required field: title, copy, tags, first-batch comments, video, cover, detail images, assets, tracking plan, warnings, and manual steps.
- Optional real voiceover audio supplied if production-quality narration is required.

Codex can complete:

- Generate content drafts.
- Render silent captioned MP4 drafts when `ffmpeg` is available.
- Attach user-provided voiceover audio to MP4.
- Generate cover/detail PNGs.
- Validate publish-pack schema through tests.

Open-source references:

- Firecrawl is not needed for media generation.
- AiToEarn is a useful reference for batch creation and multi-platform content product shape.
- NarratoAI, MoneyPrinterTurbo, CosyVoice, and similar video/content repos can be studied later for more advanced video pipelines, but they should not replace the current safe publish-pack contract without tests.

User must do:

- Install `ffmpeg` if missing.
- Install `Pillow` if missing.
- Provide production voiceover audio if silent/system-TTS video is not acceptable.
- Review generated images and video before public use.

Detailed user steps:

1. Install `ffmpeg`:

```powershell
winget install Gyan.FFmpeg
```

2. Install `Pillow`:

```powershell
python -m pip install pillow
```

3. Render a platform video:

```powershell
python scripts\render_video.py `
  --content-json ".\promotion-output\reports\promotion-manager\generated-content\product-platform-content.json" `
  --platform douyin `
  --out ".\promotion-output\videos\product-douyin.mp4"
```

4. Generate the media asset pack and write paths back into the publish pack:

```powershell
python scripts\media_asset_pack.py `
  --content-json ".\promotion-output\reports\promotion-manager\generated-content\product-platform-content.json" `
  --publish-pack ".\promotion-output\reports\promotion-manager\publish-packs\product-publish-pack.json" `
  --video-file "douyin=.\promotion-output\videos\product-douyin.mp4" `
  --out-dir ".\promotion-output"
```

Acceptance evidence:

- `promotion-output/videos/*.mp4`
- `promotion-output/media-assets/*/*.png`
- `promotion-output/reports/promotion-manager/media-assets/media-asset-pack.json`
- `promotion-output/reports/promotion-manager/publish-packs/*-publish-pack.json`

## 3. Competitor Research And Web Data

Current state: about 80%. The project has browser-visible search, official/public connectors, viral evidence inbox, video frame sampling, and optional Firecrawl-style Search/Scrape/Map/Crawl/Batch Scrape.

Missing to 100%:

- Playwright Chromium installed and verified.
- Optional Firecrawl key configured, or a self-hosted Firecrawl-compatible service deployed.
- Platform searches run with real product-derived queries.
- YouTube/GitHub official or public evidence collected.
- Zhihu, Xiaohongshu, Douyin, and TikTok gaps filled by public browser-visible evidence or user-provided exports/OCR text.
- Viral material library and creator leaderboard populated with real evidence.
- Deep competitor records include hook, beat, script, structure, visible metrics, and source URLs.

Codex can complete:

- Integrate Firecrawl as an optional provider.
- Generate search queries.
- Run browser-visible public search.
- Create and import viral evidence inbox templates.
- Rank materials and creators.
- Keep blocked platform gaps explicit.

Open-source references:

- `firecrawl/firecrawl`: useful for Search, Scrape, Map, Crawl, Batch Scrape, Interact, and future MCP web data.
- Firecrawl MCP: useful for later Agent/MCP web evidence access.
- `yikart/AiToEarn`: useful for capability registry and platform separation, not for unsafe login/cookie automation.

User must do:

- Add `FIRECRAWL_API_KEY` only if using Firecrawl Cloud.
- If self-hosting Firecrawl, provide a server large enough for crawler/browser services and isolate it from the lightweight license service.
- Manually collect or export evidence when risk-controlled platforms block public automation.

Detailed user steps:

1. If using Firecrawl Cloud, add this to `.env`:

```env
WEB_DATA_PROVIDER=auto
FIRECRAWL_API_KEY=fc-your-key
FIRECRAWL_BASE_URL=https://api.firecrawl.dev/v2
```

2. Test web data provider:

```powershell
python scripts\web_data_provider.py --provider firecrawl --out-dir ".\promotion-output" scrape --url "https://your-real-product-url.example"
```

3. Run multi-query viral discovery:

```powershell
python scripts\multi_query_viral_discovery.py `
  --workflow-manifest ".\promotion-output\reports\promotion-manager\agent-run\workflow-manifest.json" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --top-n 20 `
  --out-dir ".\promotion-output"
```

4. If platform search is blocked, create an evidence inbox:

```powershell
python scripts\viral_evidence_inbox_setup.py `
  --product-url "https://your-real-product-url.example" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --inbox-dir ".\viral-evidence-inbox" `
  --out-dir ".\promotion-output"
```

5. Put real competitor URLs, copied visible text, transcripts, exports, or screenshot OCR text into `viral-evidence-inbox`.
6. Import the inbox:

```powershell
python scripts\viral_evidence_inbox.py `
  --inbox-dir ".\viral-evidence-inbox" `
  --out-dir ".\promotion-output"
```

Acceptance evidence:

- `promotion-output/reports/promotion-manager/web-data/*.json`
- `promotion-output/reports/promotion-manager/competitors/viral-content-library.json`
- `promotion-output/reports/promotion-manager/competitors/creator-leaderboard.json`
- `promotion-output/reports/promotion-manager/competitors/deep-competitor-library.json`

## 4. Browser Extension And Commercialization Infrastructure

Current state: about 75%. The extension, store package script, Stripe-oriented license service, PostgreSQL state store, hosted worker, deploy files, legal drafts, and store listing drafts exist.

Missing to 100%:

- Real HTTPS deployment on the ENHE server.
- PostgreSQL database created and migrated.
- Stripe account activated in live mode.
- Live Stripe products/prices/webhook secret configured.
- License API and hosted worker running as isolated services.
- Extension configured to call production HTTPS endpoints.
- Public privacy policy, terms, refund, and support pages published.
- Chrome Web Store and Edge Add-ons submissions approved.
- Production monitoring, backups, rate limits, and worker capacity verified.

Codex can complete:

- Maintain code, deployment templates, legal drafts, store copy, package validation, and local simulator.
- Add server config files and migration scripts.
- Help debug deployment logs after the user provides non-secret error output.

Open-source references:

- Stripe official samples: checkout, customer portal, webhook verification, and Connect marketplace patterns.
- OpenMeter, Lago, and Flexprice: references for metering, usage credits, billing events, and subscriptions.
- Unkey: reference for API key management and quota enforcement.
- ExtensionPay: reference for paid browser extension flow, but use only after reviewing whether it matches the desired Stripe/backend ownership model.

User must do:

- Own the domain/server/Stripe/store accounts.
- Enter live secrets into server environment variables.
- Submit store listings and answer reviewer questions.
- Upgrade the server if CPU/RAM is too small.

Detailed user steps:

1. Prepare server:

```powershell
ssh root@your-server-ip
```

2. Install runtime basics on the server:

```bash
sudo apt update
sudo apt install -y nodejs npm postgresql nginx git
```

3. Clone or pull the repo on the server:

```bash
git clone https://github.com/hqwzhu/Viral-Product-Copy-Video-Generator.git
cd Viral-Product-Copy-Video-Generator/backend/license-service
```

4. Install backend dependencies:

```bash
npm install
```

5. Create PostgreSQL database and user:

```bash
sudo -u postgres psql
```

Then run inside `psql`:

```sql
CREATE DATABASE enhe_promotion_manager;
CREATE USER enhe_pm WITH PASSWORD 'replace-with-a-strong-password';
GRANT ALL PRIVILEGES ON DATABASE enhe_promotion_manager TO enhe_pm;
\q
```

6. Copy production env template and fill only on the server:

```bash
cp ../../deploy/promotion-manager/.env.production.example .env
nano .env
```

7. Run migration:

```bash
npm run migrate
```

8. Start API and worker with the provided service files under `deploy/promotion-manager/`.
9. Configure Nginx from `deploy/promotion-manager/nginx-promotion-manager.conf`.
10. Enable HTTPS certificate for `www.enhe-tech.com.cn`.
11. Build the extension package:

```powershell
python scripts\package_browser_extension.py --out-dir ".\dist"
```

12. Submit the generated ZIP to Chrome Web Store and Microsoft Edge Add-ons.

Acceptance evidence:

- Production HTTPS health check returns success.
- `backend/license-service` migration has run.
- Stripe webhook events create/update licenses.
- Extension validates license against production endpoint.
- Hosted run endpoint accepts a job and worker completes it.
- Chrome/Edge store listing status is approved.

## 5. True All-Platform Automatic Publishing

Current state: about 40%. GitHub and YouTube official API ports exist and default to dry-run. Douyin has been moved to browser-assisted/manual publishing because operator authorization is unavailable; its official port is reserved for future verified authorization. Zhihu and Xiaohongshu remain manual/browser-assisted unless official creator publishing access is verified.

Missing to 100%:

- GitHub fine-grained token or GitHub App with minimal repo permissions.
- YouTube Data API OAuth client, approved scopes, working consent, quota, and video file.
- Douyin browser-assisted/manual publishing evidence; official Open Platform publishing is future reserved work only.
- TikTok Content Posting API app review if TikTok is added.
- Verified official publishing API for Zhihu/Xiaohongshu, or acceptance that they cannot be true auto-publish.
- `I_APPROVE_PUBLISH=true`, `PUBLISH_DRY_RUN=false`, exact command approval, and audit log for every real write.
- Real published URL captured after execution.

Codex can complete:

- Keep dry-run plans and publish readiness checks accurate.
- Execute official API calls only when all gates are present.
- Generate manual/browser-assisted payloads for unsupported platforms.
- Record audit logs and clear errors.

Open-source references:

- AiToEarn has useful publish queue, OAuth/Relay, and multi-platform product patterns.
- Do not copy cookie, simulated login, private endpoint, or hidden-token approaches.
- Official SDKs/docs must override open-source examples for live publishing.

User must do:

- Create and verify developer apps.
- Complete OAuth consent/app review.
- Put tokens/secrets into environment variables.
- Manually approve each real publish.
- For Douyin/Zhihu/Xiaohongshu, either provide verified official creator publishing documentation and approved credentials in a future iteration, or accept manual/browser-assisted publishing.

Detailed user steps:

1. GitHub token:
   - Open GitHub.
   - Go to Settings -> Developer settings -> Personal access tokens -> Fine-grained tokens.
   - Create a token for the target repo only.
   - Give Contents read/write and Pull requests read/write if PR publishing is needed.
   - Put it in `.env` or current PowerShell environment:

```powershell
$env:GITHUB_TOKEN="github_pat_xxx"
```

2. YouTube:
   - Open Google Cloud Console.
   - Create/select a project.
   - Enable YouTube Data API v3.
   - Configure OAuth consent screen.
   - Create OAuth Client ID for desktop or web callback.
   - Put credentials in environment variables:

```powershell
$env:YOUTUBE_CLIENT_ID="your-client-id"
$env:YOUTUBE_CLIENT_SECRET="your-client-secret"
# GOOGLE_OAUTH_CLIENT_ID / GOOGLE_OAUTH_CLIENT_SECRET are also accepted aliases.
```

3. Douyin:
   - Use the generated Douyin title, copy, hashtags, MP4, cover, and detail images in a visible creator workflow.
   - Do not use cookies, simulated login, private APIs, captcha bypass, or scripted final publish clicks.
   - After the account owner publishes, register the real Douyin URL and evidence for metrics recovery.

4. Run dry-run first:

```powershell
python scripts\publish_readiness_runner.py `
  --workflow-manifest ".\promotion-output\reports\promotion-manager\agent-run\workflow-manifest.json" `
  --build-queue `
  --github-repo hqwzhu/Viral-Product-Copy-Video-Generator `
  --youtube-video-file ".\promotion-output\videos\product-youtube.mp4" `
  --douyin-video-file ".\promotion-output\videos\product-douyin.mp4" `
  --out-dir ".\promotion-output"
```

5. Execute official GitHub/YouTube writes only after reviewing the dry-run; keep Douyin browser-assisted/manual:

```powershell
$env:I_APPROVE_PUBLISH="true"
$env:PUBLISH_DRY_RUN="false"

python scripts\final_capability_runner.py `
  --url "https://your-real-product-url.example" `
  --platforms youtube,douyin,github `
  --github-repo hqwzhu/Viral-Product-Copy-Video-Generator `
  --youtube-video-file ".\promotion-output\videos\product-youtube.mp4" `
  --douyin-video-file ".\promotion-output\videos\product-douyin.mp4" `
  --execute-publish `
  --approval I_APPROVE_PUBLISH `
  --out-dir ".\promotion-output"
```

Acceptance evidence:

- `publish-readiness.json` says the platform is ready.
- Official execution report has status success.
- Published URL exists and is registered.
- Audit log records platform, status, content ID, URL, time, and errors.

## 6. Creator Tasks, Settlement, And Monetize Marketplace

Current state: about 30%. The project has a platform capability registry and monetization blueprint, but not a live marketplace.

Missing to 100%:

- Database tables for campaigns, creator tasks, submissions, evidence items, payout ledger, creator profiles, advertiser profiles, and review decisions.
- Admin/operator UI or CLI to create campaigns.
- Creator flow to accept tasks and submit published URLs/evidence.
- Evidence review workflow with fraud checks.
- CPS/CPE/CPM formulas backed by real platform/business evidence.
- Payout provider setup, ideally Stripe Connect or a local compliant payout flow.
- Legal/tax process: KYC/KYB, invoices, refunds/disputes, tax forms, and regional compliance.
- Support process for creators and advertisers.

Codex can complete:

- Build an MVP database schema and API.
- Generate CLI/admin commands for manual task creation and review.
- Connect evidence inbox outputs to payout proposals.
- Add tests for settlement formulas.
- Keep payouts manual-review-first.

Open-source references:

- AiToEarn is the closest product reference for Monetize, Publish, Engage, Create.
- Stripe Connect marketplace samples are the right reference for split payouts and onboarding.
- OpenMeter/Lago/Flexprice can inform usage events, billing ledger, and audit logs.

User must do:

- Decide the legal business entity.
- Open Stripe/Connect or another payout provider.
- Define creator terms, advertiser terms, refund/dispute policy, and tax process.
- Recruit pilot creators and advertisers.
- Approve payouts manually until fraud and compliance controls are proven.

Detailed user steps:

1. Decide the first MVP scope:
   - Start with manual settlement.
   - Start with flat-fee or manually verified CPE/CPM.
   - Do not start with automatic CPS payouts until order attribution is proven.

2. Prepare pilot campaign information:
   - Product URL.
   - Target platforms.
   - Required deliverables.
   - Payout model.
   - Budget cap.
   - Deadline.
   - Evidence required.

3. Let Codex create the MVP schema/API after you confirm the scope.

4. Run a manual pilot:
   - Create one campaign.
   - Let one creator publish manually.
   - Creator submits URL and screenshots/exports.
   - Import evidence through `real_evidence_inbox.py`.
   - Generate payout proposal.
   - Operator approves payout manually.

Acceptance evidence:

- Real campaign exists.
- Real creator submission exists.
- Real published URL and evidence are imported.
- Payout proposal is generated from evidence.
- Manual payout decision is recorded.
- No payout is made from fabricated or unverified metrics.

## Priority Order

1. Finish a real Codex Skill run and publish-pack proof.
2. Configure Playwright, `ffmpeg`, and `Pillow`.
3. Add Firecrawl key or prepare manual viral evidence inbox workflow.
4. Deploy license backend and hosted worker behind HTTPS.
5. Submit extension to Chrome/Edge stores.
6. Enable official API publishing only for platforms with approved credentials.
7. Build Monetize marketplace MVP after the local promotion loop and plugin backend are stable.

## Verification Commands

Run these before claiming progress:

```powershell
python scripts\completion_roadmap.py --out-dir ".\promotion-output"
python scripts\platform_capabilities.py --out-dir ".\promotion-output"
python scripts\final_capability_audit.py --skip-runtime-checks --out-dir ".\promotion-output\verification"
python -m compileall -q scripts
python scripts\test_promotion_manager.py
```

The local project can reach 100% for code, docs, packaging, dry-run flows, and repeatable evidence templates. Production operation reaches 100% only after the operator supplies real accounts, approvals, deployed services, published URLs, metrics exports, and settlement records.
