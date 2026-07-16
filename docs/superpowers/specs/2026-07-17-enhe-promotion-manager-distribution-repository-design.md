# ENHE Product Promo Maker Public Distribution Repository Design

**Date:** 2026-07-17
**Status:** Approved design; implementation pending written-spec review
**Target repository:** `hqwzhu/enhe-promotion-manager`
**Visibility:** Public

## Goal

Create a standalone public GitHub repository that lets a prospective customer understand, install, evaluate, and use ENHE Product Promo Maker without reading the internal development repository.

The repository serves four purposes:

1. Sell the product clearly by explaining what every user-facing capability does, which problem it solves, and the practical benefit to the user.
2. Distribute the Codex Skill and Chrome extension source code plus verified release archives.
3. Provide complete Chinese and English installation, usage, troubleshooting, security, and capability documentation.
4. Make Skill and extension release synchronization independently auditable, excluding payment and subscription behavior from the parity conclusion.

The canonical positioning is:

- Chinese: 把产品网页变成推广文案、视频脚本和发布素材。
- English: Turn product pages into promotional copy, video scripts, and publishing assets.

## Public Identity

The repository and documentation use the following public identity consistently:

| Field | Value |
| --- | --- |
| Product | ENHE Product Promo Maker / ENHE 产品推广素材生成器 |
| Brand and creator | ENHE AI |
| Business | 深圳市龙岗区恩禾网络科技工作室 |
| Official website | https://www.enhe-tech.com.cn/ |
| Product page | https://www.enhe-tech.com.cn/promotion-manager |
| Contact | huqingwei5942@gmail.com |
| GitHub | https://github.com/hqwzhu |
| Chrome Web Store | https://chromewebstore.google.com/detail/enhe-promotion-manager/dloklkbnmoigemnfigbkibogmgbieppl |

Public pages must not imply that the software guarantees viral reach, sales, conversions, platform approval, or automatic publication.

## Audience and Customer Journey

The primary audiences are independent developers, AI product operators, SaaS teams, ecommerce operators, and content marketing teams that need to turn an existing product page into reusable promotional material.

The repository homepage must support this journey in order:

1. Understand the outcome within the first screen.
2. See the product workflow and concrete deliverables.
3. Compare the Skill and extension and understand how they work together.
4. Inspect every capability through a benefit-oriented feature table.
5. Install the Skill or Chrome extension.
6. Run a first product-page generation task.
7. Understand local data, platform-risk, and manual-publishing boundaries.
8. Find detailed documentation, support, releases, creator information, and the official website.

The default `README.md` is Chinese because the initial market and support workflow are Chinese-first. `README.en.md` provides equivalent English content, not a shortened summary.

## Repository Architecture

The repository is a distribution mirror assembled from reviewed source, not a second independent development codebase. The existing development repository remains the source of truth. Public releases are generated from an explicit source commit and must never be edited only in the distribution repository without applying the same change to the source repository.

```text
enhe-promotion-manager/
├── README.md
├── README.en.md
├── LICENSE
├── NOTICE.md
├── SECURITY.md
├── CHANGELOG.md
├── release-manifest.json
├── SHA256SUMS
├── skill/
│   └── viral-product-copy-video-generator/
│       ├── SKILL.md
│       ├── scripts/
│       ├── references/
│       ├── assets/
│       ├── requirements*.txt
│       └── component-manifest.json
├── extension/
│   └── chrome/
│       ├── manifest.json
│       ├── _locales/
│       ├── icons/
│       ├── popup.html
│       ├── popup.css
│       ├── popup.js
│       ├── billing-contract.json
│       └── component-manifest.json
├── docs/
│   ├── zh-CN/
│   │   ├── features.md
│   │   ├── installation.md
│   │   ├── quick-start.md
│   │   ├── skill-guide.md
│   │   ├── extension-guide.md
│   │   ├── platform-research.md
│   │   ├── publishing-and-review.md
│   │   ├── data-and-privacy.md
│   │   ├── troubleshooting.md
│   │   └── version-sync.md
│   └── en/
│       └── matching English documents
└── scripts/
    ├── build_release.py
    ├── verify_distribution.py
    └── generate_checksums.py
```

Only files required to use, inspect, document, verify, or package the public product belong in this repository. Internal planning history, production deployment configuration, private commercial operations, and generated user output remain outside it.

## Product Components

### Codex Skill

The Skill is the local execution engine. It reads product pages, structures product facts, gathers allowed research evidence, generates platform-adapted content and media assets, prepares guarded publishing packages, and supports evidence-based review after publication.

The Skill remains installable by copying the versioned Skill directory into the user's Codex skills directory. Documentation must also explain environment dependencies such as Python, Playwright, optional FFmpeg and Pillow, and optional platform integrations.

### Chrome extension

The Chrome extension is the browser entry point. It captures the active product-page URL after a user action, lets the user choose platforms and workflow depth, and generates or submits a corresponding task. It also exposes account, license, usage, and hosted-run surfaces that already exist in the verified package.

For local-first use, the extension generates commands for the installed Skill. Hosted Worker remains disabled until separately deployed and approved; public documentation must not present hosted execution as currently available.

### How they work together

The extension reduces setup friction by turning the current browser tab and user selections into a structured command. The Skill performs the actual local workflow and writes results to the local output directory. Either component may be inspected separately, but the recommended experience uses the extension as the entry point and the Skill as the execution engine.

## Sales-Oriented Feature Documentation

Every feature listed in either language must use the same four-part structure:

| Required field | Purpose |
| --- | --- |
| What it does | A factual description of the behavior and output. |
| Problem it solves | The customer pain or manual work it removes. |
| User benefit | The concrete time, consistency, control, or reuse benefit. |
| Typical use case | A specific scenario that helps a buyer recognize relevance. |

The feature catalog must cover at least the following non-payment capabilities:

| Capability | What it does | Problem solved | User benefit | Typical use case |
| --- | --- | --- | --- | --- |
| Product-page capture | Reads the active or supplied product URL and extracts structured facts. | Product information is scattered across pages and repeatedly recopied. | Creates one reusable factual source for later content. | Preparing a launch package from a SaaS pricing or product page. |
| Multi-URL and site discovery | Accepts several URLs or discovers relevant product pages from a site entry point. | A product story often spans homepage, feature, pricing, and documentation pages. | Reduces missed evidence and repetitive collection. | Building one campaign from a multi-page website. |
| Competitor and viral-content research | Organizes public or browser-visible evidence from supported platforms. | Teams guess at angles without seeing how similar content is framed. | Grounds creative decisions in inspectable evidence. | Researching hooks for Douyin, Xiaohongshu, Zhihu, YouTube, GitHub, or TikTok. |
| Local logged-in Sidecar research | Reuses a dedicated local Chrome profile for supported platform searches without uploading cookies. | Some useful public-facing evidence is visible only in a logged-in browser session. | Keeps login state local while improving research coverage. | Searching Douyin, Xiaohongshu, and Zhihu from the user's own computer. |
| Evidence and fact controls | Separates facts, inferred claims, sources, missing evidence, and risk notes. | Promotional copy can overstate unsupported product claims. | Produces reviewable material with clearer truth boundaries. | Marketing a technical or regulated product. |
| Platform-adapted copy | Generates titles, long-form copy, tags, opening comments, reply prompts, and calls to action by platform. | Reusing identical copy across platforms lowers relevance and requires manual rewriting. | Produces platform-ready drafts faster and more consistently. | Launching the same product on Zhihu, Xiaohongshu, Douyin, YouTube, and GitHub. |
| Video scripts and storyboards | Produces spoken scripts, shot plans, scenes, and timing guidance. | Turning a product page into a coherent video plan is slow. | Gives creators a shootable or renderable structure. | Creating a short product explainer or launch video. |
| Video draft generation | Produces or attaches MP4 draft assets when the required renderer is available. | Teams need a tangible first cut before investing in final editing. | Shortens the path from idea to reviewable video. | Generating a first promotional video for internal review. |
| Cover and detail images | Generates PNG cover and detail assets when image dependencies are available. | Every platform needs supporting visuals in different content packages. | Creates a more complete publishing package from the same source facts. | Preparing Xiaohongshu cover and product-detail images. |
| Publishing packages | Combines copy, tags, interactions, media paths, tracking links, risks, and review steps. | Content and assets become fragmented across files and tools. | Gives the user one auditable handoff for publication. | Handing a campaign from product marketing to an operator. |
| Guarded publishing assistance | Builds dry-run or browser-assisted publishing tasks while preserving final user review. | Fully manual posting is repetitive, but unattended posting creates account and compliance risk. | Speeds preparation without taking away final control. | Preparing posts for platforms with different API availability. |
| Post-publication evidence import | Records real published URLs, metrics, comments, orders, and revenue evidence. | Campaign results are disconnected from the content that produced them. | Makes outcomes traceable and suitable for review. | Comparing which hook produced stronger qualified interest. |
| Review and next-round optimization | Generates retrospective reports and recommendations from real evidence. | Teams repeat content without learning systematically from results. | Turns each campaign into inputs for the next one. | Improving the next set of titles, scripts, or platform choices. |
| Chrome page-to-task workflow | Converts the current tab and selected options into a local or approved hosted task. | Copying URLs and composing commands is error-prone for non-technical users. | Makes the workflow accessible from the product page itself. | Opening a product page and generating a ready-to-run local command. |
| Bilingual interface | Uses Chinese or English based on Chrome language and remembers the user's selection. | Mixed-language teams need consistent controls and documentation. | Reduces onboarding and support friction. | A Chinese operator collaborating with an English-speaking teammate. |
| Local-first privacy | Keeps local Skill output, browser profile, and cookies on the user's computer by default. | Marketing research often involves sensitive account and product context. | Gives the user clearer control over data location. | Researching from authenticated platform sessions without exporting cookies. |

The Chinese feature catalog must be written naturally for Chinese buyers rather than translated word-for-word. The English catalog must make the same factual claims and preserve the same safety boundaries.

## README Content Design

Both README files use the same information hierarchy:

1. Product name, direct promise, official website, product page, store link, and language switch.
2. A concise before-and-after workflow showing product page to research, copy, video script, media, publishing package, and review.
3. Concrete deliverables users receive.
4. Skill versus extension comparison and recommended combined workflow.
5. Feature-benefit table linking to the complete catalog.
6. Three installation paths: Chrome Web Store, Skill release archive, and source installation.
7. Five-minute quick start with one safe example.
8. Supported platforms and current availability limits.
9. Local-first privacy, manual approval, and anti-fabrication commitments.
10. Current release, checksums, version synchronization, and changelog links.
11. Creator, business, website, contact, license, security, and support information.

Screenshots may be added only when they show the real extension or actual generated output. They must not include cookies, tokens, email inboxes, private account details, or fabricated campaign results.

## Installation and Usage Documentation

### Chrome extension installation

The primary path links to the published Chrome Web Store item. The manual developer-mode path is documented for source inspection and testing:

1. Download and verify the release archive.
2. Extract `extension/chrome` or use the source tree.
3. Open `chrome://extensions`.
4. Enable Developer mode.
5. Select Load unpacked and choose the Chrome extension directory.

Documentation must clearly state that Chrome Web Store version `0.5.2` is the currently published version at design time, while source and the planned repository release are `0.5.3`. After the store update is approved, the manifest and store version fields are updated together.

### Skill installation

The release provides a dedicated Skill ZIP whose root contains `viral-product-copy-video-generator`. Installation documentation covers Windows first, then macOS/Linux path differences:

1. Download and verify the Skill archive.
2. Extract it into the user's Codex skills directory.
3. Install required runtime dependencies.
4. Run the provided setup and verification commands.
5. Restart or refresh Codex skill discovery.
6. Run a documented sample against a public example page.

The repository must explain that the MediaCrawler Sidecar is a separate local dependency. Its checkout, browser profile, cookies, and runtime data are not included in the public release. The repository may include ENHE's adapter/bootstrap scripts, but it must direct users to the upstream project and applicable license terms for the third-party code.

### First workflow

The quick start uses a public product URL and local output directory. It explains where to find product facts, generated content, media assets, publishing packages, and workflow reports. It does not require hosted execution, a paid subscription, a production server, or final platform publication.

## Release and Version Model

The first public distribution release is `v0.5.3`. The Git tag, GitHub Release, extension manifest, component manifests, changelog entry, and release manifest must agree on that version before publication.

`release-manifest.json` records at least:

- distribution version and release date;
- source repository URL and exact source commit;
- deterministic distribution tree digest;
- Skill version and archive name;
- extension version and archive name;
- Chrome Web Store item ID and currently published store version;
- supported platforms;
- non-payment synchronization scope;
- excluded synchronization scope;
- artifact SHA-256 values;
- verification status and verification commands.

`component-manifest.json` in each component records its version, source commit, required runtime, public entry points, and capability identifiers. Stable capability identifiers are compared during release verification so translated labels do not create false synchronization results.

The non-payment synchronization report includes the 11 current extension-to-Skill command or script references and confirms that every referenced entry point exists in the shipped Skill. Payment plans, checkout providers, license purchase, subscription status, credits, and billing backend behavior are explicitly excluded from the parity conclusion.

The verified extension archive remains functionally faithful to the reviewed `0.5.3` package. Existing subscription UI and billing contract files are not removed merely because billing is excluded from the synchronization audit.

## Release Artifacts

GitHub Release `v0.5.3` contains:

- `enhe-product-promo-maker-skill-0.5.3.zip`;
- `enhe-promotion-manager-extension-0.5.3.zip` using the verified extension package contents;
- `SHA256SUMS`;
- `release-manifest.json`;
- concise Chinese and English release notes.

The extension archive must match the validated package whose current report status is `ready`. If rebuilding changes its bytes, the package is revalidated and the manifest/checksum are regenerated; an old checksum is never copied onto a new archive.

## Security, Privacy, and Licensing Boundaries

The public repository and release archives must exclude:

- `.env` files and all API keys, licenses, access tokens, refresh tokens, webhook secrets, and payment credentials;
- cookies, Chrome profiles, browser storage, authenticated session exports, and identity salts;
- Sidecar checkouts, virtual environments, runtime state, caches, backups, and generated search evidence;
- `node_modules`, `.venv`, temporary files, logs, generated promotion output, screenshots with private data, and local database files;
- production SSH keys, server inventories, deployment secrets, database connection strings, and private infrastructure configuration;
- payment backend runtime state and provider secrets.

Before each release, verification must scan both tracked files and ZIP contents for forbidden paths and common secret formats. A match blocks publication until manually resolved. No redaction is performed silently.

`NOTICE.md` identifies third-party dependencies and their licenses. The user's commercial authorization for MediaCrawler does not automatically grant public users a sublicense; therefore MediaCrawler source or an installed Sidecar checkout is not republished in this repository. Users obtain third-party dependencies from their official upstream sources under the relevant terms.

The product privacy policy remains hosted on the official website. Repository documentation summarizes local and hosted data behavior and links to the controlling policy without inventing broader promises.

## Build, Validation, and Error Handling

### Distribution build

`scripts/build_release.py` assembles a clean staging directory from an explicit reviewed source commit. It copies only allowlisted files, normalizes release metadata, builds the Skill and extension archives, and delegates checksum generation. It must not build from an unspecified dirty working tree.

### Required validation

`scripts/verify_distribution.py` fails with a non-zero exit code when any of these checks fail:

- required Chinese or English document is missing;
- a public identity field or official link is inconsistent;
- Skill or extension component version differs from the release version;
- the extension is not Manifest V3 or its permission boundary changes unexpectedly;
- a referenced non-payment Skill command or script is absent;
- a required runtime file, including `requirements-youtube.txt`, is absent;
- an archive contains a forbidden path or suspected secret;
- release manifest artifact names or SHA-256 values differ from built files;
- the extension ZIP differs from the validated package without a new validation report;
- Hosted Worker is described as enabled or available when it remains disabled;
- documentation claims guaranteed results, risk-control bypass, automatic final publication, or fabricated metrics.

Failures report the exact file and violated rule. Build and release scripts stop before tagging or uploading. They do not auto-delete source files, rewrite secrets, publish partial releases, or continue after an ambiguous package mismatch.

### Test set

Before GitHub publication:

1. Run the existing scoped extension tests and package validator.
2. Run the Skill regression and compile checks relevant to shipped scripts.
3. Verify all 11 non-payment extension-to-Skill references.
4. Validate Chinese and English internal links.
5. Extract both ZIP files into clean temporary directories and run smoke checks from the extracted copies.
6. Verify every `SHA256SUMS` entry against the final release bytes.
7. Run secret and forbidden-path scans against the Git index and archives.
8. Review rendered README files on desktop and mobile widths for readable tables, links, and code blocks.

The already validated extension evidence at design time is version `0.5.3`, package-report status `ready`, and SHA-256 `D01BCCD2D1D8F2AC25B44BF615F4B9F4F3CD4C9E4461C9BF26AA3DCB849CA7B0`. This value is retained only if the final artifact is byte-identical.

## GitHub Publishing Flow

1. Converge and commit the current reviewed source changes in the source repository without mixing unrelated work.
2. Restore the missing `requirements-youtube.txt` in the installed/distributed Skill and run synchronization checks.
3. Build a clean public repository staging tree from the selected source commit.
4. Run the full distribution validator and inspect the generated manifest and checksums.
5. Create public repository `hqwzhu/enhe-promotion-manager` with no auto-generated README, license, or `.gitignore` that could conflict with the prepared tree.
6. Push the prepared default branch and confirm the public repository renders both README files correctly.
7. Tag the exact verified commit as `v0.5.3`, record that commit in the GitHub Release body, and create the release with both archives, manifest, checksums, and bilingual notes. The manifest uses a distribution tree digest instead of attempting to contain its own Git commit hash.
8. Download the public release assets once and re-verify checksums from the downloaded copies.
9. Upload extension `v0.5.3` as an update to the existing Chrome Web Store item `dloklkbnmoigemnfigbkibogmgbieppl`; do not create a second item.
10. Record the store submission state in the release manifest or changelog. The public repository release does not wait for store approval, but documentation must continue showing the actual published store version.

No production deployment, Hosted Worker enablement, payment-provider mutation, or final platform publication is authorized by this repository release flow.

## Acceptance Criteria

- `hqwzhu/enhe-promotion-manager` is public and contains the approved Skill and Chrome extension source distributions.
- Chinese and English documentation are complete, linked, and equivalent in factual scope.
- A prospective customer can understand what each feature does, the problem it solves, the resulting benefit, and a typical use case.
- Creator, business, website, product page, contact, GitHub, and store information are visible and consistent.
- Skill and extension installation and first-use instructions work from clean extracted release archives.
- `v0.5.3` release assets, manifests, tags, and checksums agree.
- The non-payment synchronization audit passes for all current extension-to-Skill entry points.
- Billing remains excluded from the parity conclusion without altering the verified extension package.
- No secrets, cookies, browser profiles, Sidecar runtime state, generated user data, or production infrastructure credentials are published.
- Hosted Worker remains disabled and is not presented as available.
- The existing Chrome Web Store item receives the `0.5.3` update package after repository verification.

## Out of Scope

- Enabling or deploying Hosted Worker.
- Changing Starter, Growth, or Scale pricing.
- Redesigning checkout, QR payment, licenses, subscriptions, or refunds.
- Claiming payment/subscription parity between the Skill and extension.
- Publishing MediaCrawler source, login sessions, or runtime state.
- Bypassing CAPTCHA, platform risk controls, login checks, or application review.
- Automatically clicking final publish buttons on content platforms.
- Refactoring unrelated Skill, Sidecar, website, or backend code.
