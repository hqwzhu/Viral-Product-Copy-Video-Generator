# Professional media pipeline design

Date: 2026-07-22
Status: Approved
Target: `viral-product-copy-video-generator`

## Goal

Upgrade the current deterministic promotion media generator into a local-first professional media pipeline that can produce:

- voiced MP4 videos built from real product captures, multiple scenes, motion graphics, subtitles, B-roll, and optional digital presenters;
- commercial covers and detail images that combine exact product screenshots and brand assets with photographic AI-generated scenes;
- new run artifacts under bilingual Chinese/English directory names;
- truthful, machine-verifiable media quality reports that never present a degraded template as a professional result.

The pipeline must preserve the existing Skill, extension, publish-pack, and evidence workflows. Hosted Worker remains disabled. This design does not add automatic platform publishing, payment behavior, or performance-data collection.

## Current state and problem

The current `scripts/render_video.py` creates an MP4 from a solid background, burned-in text, and optional audio. It does not automatically capture the product, construct varied scenes, add B-roll, or render advanced motion. `scripts/media_asset_pack.py` creates readable local PNG cards, but the images are primarily text layouts without real product screenshots, brand-led composition, or photographic product scenes.

These outputs are useful drafts but do not satisfy the requested commercial standard. A new media-specific quality status is required so that generation quality is not confused with the existing overall workflow status, which also covers publishing approval, live URLs, metrics, comments, orders, and revenue evidence.

The most recent real workflow output directories were removed before this design was approved. Source code, prior verification fixtures, and MediaCrawler Sidecar smoke evidence were deliberately retained.

## Approved decisions

### Hybrid, local-first architecture

The default path is entirely local:

- Playwright captures real product pages and interaction sequences.
- Kokoro ONNX creates Chinese or English voiceovers.
- HyperFrames creates motion, highlights, pointer paths, transitions, subtitles, and branded sequences.
- FFmpeg performs final encoding, audio mixing, loudness normalization, and media inspection.
- exact product screenshots, logos, Chinese text, and brand elements are composited locally.

The provider layer uses local ComfyUI/FLUX as the default photographic AI-scene path for the professional target. Pexels B-roll, local MuseTalk presenters, cloud image generation, and HeyGen presenters remain optional adapters. The core pipeline can still produce an honest lower-grade result when optional runtimes are absent. Cloud providers are disabled by default. Browser cookies, profiles, login tokens, and unselected private-page captures must never be uploaded.

### Product demonstration first

The default professional video is a product demonstration, not a talking-head video. A digital presenter is an optional scene type selected explicitly for a run. Presenter failure must not prevent a complete product-demonstration video when the other professional quality requirements are met.

### Exact product, generated environment

AI generation is used for backgrounds, environments, lighting concepts, and supporting photography. It must not redraw a product UI, logo, legal label, price, or Chinese marketing text when an exact source asset is available. Those elements are composited locally after scene generation.

### Honest quality levels

The media pipeline records one of these values in a separate `mediaQuality.status` field:

- `draft_ready`: deterministic review assets exist but rely mainly on simple layouts or fallback media.
- `standard_ready`: voiced, usable media exists with real product content, but one or more professional composition requirements are missing.
- `professional_ready`: every mandatory professional video and commercial-visual check passes.
- `partial_ready`: one or more required artifact families are missing or failed.

These values do not replace or weaken existing publication/evidence statuses. A run can have `mediaQuality.status=professional_ready` while the overall workflow correctly remains `waiting_real_data` or another pre-publication state.

## Research and capability selection

The design was informed by the installed `brainstorming`, `find-skills`, `product-hyperframes-video`, `imagegen`, `web-access`, and project Skill instructions. The official `heygen-video` and `heygen-avatar` skills from `heygen-com/skills` were installed for an optional cloud adapter. Because those skills can run shell commands, contact remote APIs, upload media, and expose optional feedback behavior, the pipeline must not invoke them implicitly, install their CLI automatically, or enable telemetry.

Selected technology and license boundaries:

- HyperFrames, Playwright, Diffusers, Kokoro models, and FLUX.1-schnell have commercial-compatible Apache-2.0 paths.
- `kokoro-onnx`, MuseTalk code and models, and LivePortrait code have permissive paths, subject to dependency and model checks.
- LivePortrait's default InsightFace detection model is not acceptable for the commercial default and must be replaced before a LivePortrait adapter can be enabled.
- ComfyUI is GPL-3.0 and must remain an independent local sidecar rather than linked application code.
- FLUX.1-dev is not a commercial default because of its nonstandard license; FLUX.1-schnell is the default local FLUX option.
- Remotion is not selected for the default implementation because its customized license can require a commercial company license.
- Pexels assets may be used and modified, but source metadata must be retained and assets must not be redistributed as a standalone stock library.
- The reviewed `inference-sh` photography skill is not adopted because its repository had no clear license and depended on an additional `belt` CLI.

MuseTalk, ComfyUI, and their models are not installed merely by approving this design. They are installed only when the implementation plan reaches their adapter and their exact dependencies and licenses have passed a fresh check.

## Output layout and migration

All new default runs write only to this tree:

```text
promotion-output_推广输出/
└─ runs_运行记录/
   └─ <timestamp-product>/
      ├─ source-assets_源素材/
      ├─ product-captures_产品录屏/
      ├─ generated-content_生成内容/
      ├─ voiceovers_配音/
      ├─ b-roll_辅助镜头/
      ├─ ai-scenes_AI场景图/
      ├─ videos_视频/
      ├─ covers_封面/
      ├─ detail-images_详情图/
      ├─ publish-packs_发布包/
      └─ reports_报告/
```

The implementation adds a single path module that owns directory creation and resolution. Existing explicit `--out-dir` arguments remain authoritative. With no explicit output directory, the CLI uses `promotion-output_推广输出`. Readers look in the new layout first and can fall back to the old `promotion-output` layout. The migration does not copy artifacts into duplicate English and bilingual trees.

The old directories remain readable but receive no new default runs. Existing publish-pack field names remain unchanged so the Chrome extension and downstream publishing tools do not require a parallel media schema.

## Architecture and data flow

```text
product URL/content
        │
        ▼
media job + capture plan
        │
        ├── Playwright product captures
        ├── Kokoro voiceover
        ├── user/local/AI/Pexels supporting scenes
        └── optional MuseTalk or HeyGen presenter
        │
        ▼
HyperFrames scene composition
        │
        ▼
FFmpeg encode, mix, normalize, inspect
        │
        ├── commercial cover/detail composition
        ├── media manifest and provenance
        ├── media quality report
        └── compatible publish-pack update
```

Python remains the main orchestrator. HyperFrames, FFmpeg, ComfyUI, and optional presenter runtimes are called through narrow process or HTTP adapter boundaries. The core pipeline must not import ComfyUI or MuseTalk dependencies into the existing Skill runtime.

## Data contracts

### Media job

Each run writes `reports_报告/media-job.json` before expensive generation starts. It contains:

- run ID, product name, source URL, language, target platforms, and target quality;
- requested aspect ratios and duration range;
- selected local and optional cloud providers;
- whether cloud media upload was explicitly allowed;
- paths to product data, brand assets, generated content, and `capture-plan.json`;
- requested presenter mode, which defaults to `none`.

### Capture plan

`capture-plan.json` is declarative data, not executable code. Each shot contains a same-site URL, viewport, stable selector, optional click/scroll action, wait condition, capture duration, highlight selector, and human-readable purpose. Account, billing, checkout, admin, and editable form regions are denied by default.

### Stage result

Every provider stage returns the same minimum contract:

```json
{
  "status": "ready",
  "provider": "playwright",
  "artifacts": [],
  "warnings": [],
  "errorCode": "",
  "diagnostics": {}
}
```

Allowed stage statuses are `ready`, `degraded`, `failed`, and `skipped`. An artifact records its type, local path, SHA-256 hash, source category, source URL when applicable, license identifier, generation provider, and whether it contains user-provided data. Secrets are never included.

### Media manifest and quality report

`reports_报告/media-manifest.json` is the authoritative inventory and provenance record. `reports_报告/media-quality-report.json` records the requested level, achieved level, each evaluated check, blockers, fallbacks, and media inspection results. Existing publish packs receive only compatible `video`, `cover`, `detailImages`, and `assets` references plus the new nested `mediaQuality` summary.

## Components

### Path manager

The path manager creates one `RunPaths` value for the run and is the only module that knows bilingual folder names. All new media components receive resolved `Path` values rather than constructing folder strings. Legacy lookup is isolated in this module.

### Product capture adapter

Playwright executes the approved capture plan against public product pages or a local authorized Chrome session. It captures still images and short interaction clips at target viewports. The adapter records the final URL, viewport, selector outcome, timestamps, and file hashes. A failed product capture is never replaced with a fabricated UI.

### Voiceover adapter

Kokoro ONNX is the professional default for Chinese and English. It produces a WAV file and timing segments derived from the final narration. An existing user-supplied WAV remains valid input. Windows SAPI may create a review fallback, but an SAPI fallback cannot pass `professional_ready`.

### Supporting media adapters

Supporting scenes are selected in this order:

1. authorized user-supplied product and lifestyle media;
2. real product captures;
3. local ComfyUI with a commercially allowed FLUX.1-schnell workflow;
4. Pexels B-roll with retained provenance;
5. an explicitly enabled cloud image provider.

The pipeline does not require every provider. It asks each selected adapter for a health check before generation and records a skip or fallback when unavailable.

### Optional presenter adapters

MuseTalk is the preferred local presenter/lip-sync adapter. HeyGen is the optional cloud adapter. Both consume only a selected, authorized portrait or avatar asset plus the generated voiceover. Presenter output is treated as one possible scene source, not as the entire video. HeyGen requires both configured credentials and explicit cloud-media permission.

### Video compositor

The video compositor converts the storyboard into a HyperFrames project with real captures, supporting scenes, presenter clips when selected, animated product highlights, pointer paths, typography, captions, transitions, and branded intro/outro frames. FFmpeg then encodes H.264/AAC MP4, mixes audio, applies loudness normalization, and produces ffprobe evidence.

### Commercial visual compositor

Cover and detail-image generation uses two layers:

1. photographic background or scene imagery from user assets, local AI, Pexels, or an explicitly enabled cloud source;
2. exact local composition of product captures, logos, brand shapes, pricing or calls to action, and Chinese/English text.

The compositor uses platform-specific dimensions and safe areas. It creates a review contact sheet in addition to individual images. A plain text card without a real product or commercial scene is a draft, not a professional visual.

### Quality evaluator

The evaluator reads artifacts and technical probe results rather than trusting provider success messages. It assigns the media quality level, emits explicit blockers, and controls whether the publish pack may claim professional media readiness.

## Professional video rules

A `professional_ready` video must satisfy all of these requirements:

- contain a valid, non-silent voice track;
- contain at least five distinct shots;
- contain at least three distinct real product captures;
- contain at least two distinct B-roll or AI scene shots;
- use at least three motion categories: zoom/pan, product highlight or pointer motion, and a scene transition;
- have captions whose timing stays within the video duration and corresponds to narration segments;
- use the requested platform aspect ratio with a short edge of at least 1080 pixels;
- use H.264 video and AAC audio in a playable MP4 container;
- apply speech-oriented loudness normalization and record measured audio values;
- include branded opening or closing treatment without replacing the product demonstration with title cards.

The default storyboard target is a concise 20-to-60-second promotion video. Platform-specific content may override the exact duration while retaining the shot and quality requirements.

## Commercial cover and detail-image rules

For `professional_ready` commercial visuals:

- every cover includes an exact product screenshot or product asset, a brand identifier, and a commercial scene or intentional photographic background;
- the cover/detail set includes at least one AI-generated photographic product scene, with the exact product composited locally rather than redrawn by the model;
- every detail image contains product or lifestyle imagery and cannot be a pure text card;
- the product, logo, price, legal labels, and Chinese/English text are locally composited and remain exact;
- platform dimensions, safe margins, readable contrast, and export format checks pass;
- generated backgrounds do not falsely depict unavailable product capabilities;
- provenance is present for every external or generated base image;
- the contact sheet is generated for final human review before publication.

Automated checks establish technical and composition readiness. They do not replace final human review of claims, copyright, likeness permission, or brand taste.

## Error handling and recovery

Failures are classified by their effect on the requested quality target:

- Product capture failure blocks `professional_ready` and normally produces `partial_ready`; no synthetic UI is substituted.
- Kokoro failure may fall back to SAPI for review, but the result is at most `standard_ready`.
- AI scene failure falls back through authorized user media, product captures, and Pexels. Missing the required supporting-scene count lowers the quality level.
- If no AI-generated photographic product scene succeeds, the cover/detail set is at most `standard_ready` even when Pexels or user photography provides a usable fallback.
- Pexels or cloud failure never exposes credentials and falls back locally.
- HyperFrames failure may use a simple FFmpeg composition for a reviewable artifact, but the result is at most `standard_ready`.
- Presenter failure is non-blocking when a complete product-demonstration storyboard remains possible.
- Missing commercial covers or detail images yields `partial_ready` for the complete media request even if the MP4 is valid.

Each stage writes its result atomically after successful artifact creation. A rerun reads artifact hashes and stage results, resumes at the first failed or invalid stage, and does not repeat valid expensive work. Failed or temporary files are not attached to publish packs.

## Security and privacy boundaries

- Chrome cookies, browser profiles, login tokens, local-storage values, and request headers are never exported or placed in reports.
- Public pages are the default capture source. A logged-in capture requires an already authorized local session and remains local.
- Capture plans deny account, billing, payment, checkout, admin, and editable form regions unless a future explicit policy change approves them.
- Cross-origin navigation, downloads, and arbitrary JavaScript from capture-plan data are not allowed.
- Browser and model inputs are passed as argument arrays or structured data, never concatenated into shell commands.
- Cloud adapters receive only files selected in the job allowlist and the minimum prompt or narration data required for the request.
- Cloud media use requires configured credentials and the explicit `--allow-cloud-media` flag. Provider configuration alone is insufficient.
- Logs record whether a credential is configured and whether a call succeeded, never the credential value.
- User-provided portraits and voice assets require an affirmative authorization field before a presenter adapter can use them.
- Source URLs, licenses, provider names, hashes, and user-data classification are retained in the local manifest.

## Resource management

The target machine has an RTX 3070 Laptop GPU with 8 GB VRAM and limited free system memory during prior inspection. GPU-heavy providers declare a health check and minimum available resources. ComfyUI and MuseTalk jobs run serially and are never resident together. If a selected optional local provider lacks memory, the pipeline records a resource diagnostic and uses the approved fallback chain instead of crashing the main workflow.

Docker is not required for the default local path. Independent sidecars may use their own Python environments. The core Skill remains runnable without ComfyUI, MuseTalk, HeyGen, or a cloud image account.

## CLI and compatibility behavior

`scripts/skill_entry.py` remains the primary one-link entry point. Existing flags and explicit output paths continue to work. The implementation adds only the controls required by this design, including target media quality, provider selection where needed, presenter mode, and explicit cloud-media permission.

`scripts/render_video.py` and `scripts/media_asset_pack.py` remain callable compatibility wrappers. Their professional path delegates to focused media-pipeline modules; explicit draft behavior remains available for tests and low-resource review runs.

For a single product test, `--link-mode product` is used. `--link-mode auto` retains its existing site-discovery behavior and must not be used for a one-product acceptance run because it can expand into multiple product batches.

## Testing strategy

Tests follow the repository's existing Python test style and cover four levels.

### Unit tests

- bilingual path creation, explicit output overrides, and legacy read fallback;
- media job, capture plan, stage result, manifest, and quality report validation;
- provider selection and fallback order;
- exact media-quality classification for every mandatory check;
- cloud permission, file allowlist, forbidden capture regions, and secret redaction;
- publish-pack compatibility and separation of media quality from publication evidence.

### Integration tests

- Playwright captures a deterministic local product fixture at multiple viewports;
- Kokoro produces a non-empty voice WAV and timing data;
- HyperFrames and FFmpeg create an MP4 that ffprobe confirms contains expected video and audio streams;
- local visual composition creates correctly sized covers and detail images with real fixture screenshots;
- failure injection proves that SAPI, missing B-roll, failed presenter, and failed HyperFrames produce the specified honest downgrade.

Tests requiring optional models or network providers are explicitly marked and do not make the core offline suite depend on cloud services.

### End-to-end fixture

A deterministic local product site generates the full bilingual run tree, media job, captures, voiceover, supporting scenes, MP4, covers, detail images, publish pack, manifest, and quality report. With cloud providers disabled, the test verifies that no cloud upload occurs.

### Real product smoke test

After local tests pass, the implementation runs the ENHE public product page with `--link-mode product`. The acceptance evidence includes:

- absolute output and report paths;
- ffprobe stream, codec, duration, resolution, and audio measurements;
- captured-shot and supporting-scene counts;
- a contact sheet for cover and detail-image review;
- the complete media quality report;
- confirmation that no platform publishing occurred.

## Acceptance criteria

The upgrade is complete only when current evidence proves all of the following:

1. A real product run creates a voiced professional MP4 with the required real product captures, supporting scenes, motion categories, captions, and technical media checks.
2. The same run creates at least one platform-ready cover and the configured detail-image set using exact product/brand composition, including at least one AI-generated photographic product scene, rather than pure information cards.
3. The new default run exists only under `promotion-output_推广输出/runs_运行记录/...`; no new default artifacts are written to the legacy tree.
4. Old output paths remain readable where downstream tools need them, and publish-pack consumers remain compatible.
5. `media-quality-report.json` proves `professional_ready` from artifact inspection rather than provider claims, while publication/evidence readiness remains independently truthful.
6. Cloud providers are disabled by default and security tests prove that cookies, profiles, tokens, and non-allowlisted files are not uploaded or logged.
7. Required local dependencies are installed and checked; optional provider absence produces the designed downgrade instead of a false success.
8. Unit, integration, end-to-end, and real product smoke evidence all pass without changing Hosted Worker or publishing content.

## Implementation boundaries

In scope:

- bilingual path migration and compatibility reads;
- local product capture and voice generation;
- professional motion/video composition;
- supporting-scene and optional presenter adapters;
- commercial cover/detail composition;
- provenance, resumability, quality evaluation, tests, and a real sample run.

Out of scope:

- automatic live publishing or bypassing platform confirmation;
- enabling Hosted Worker;
- changes to Chrome extension payment or subscription behavior;
- automated advertising spend;
- claims that generated media produced real traffic, orders, or revenue without external evidence.
