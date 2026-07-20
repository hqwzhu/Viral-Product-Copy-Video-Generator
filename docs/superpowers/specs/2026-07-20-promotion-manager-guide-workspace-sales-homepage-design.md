# ENHE Product Promo Maker: Guide, Workspace, and Sales Distribution Design

## Status

Approved conversational design. Implementation is intentionally blocked until the user reviews this written specification.

## Goal

Complete the public distribution work by adding an in-extension bilingual usage guide, a desktop-first responsive full workspace, and a sales-oriented public GitHub homepage. Keep the existing Chrome popup workflow, Skill capabilities, payment UI, privacy boundaries, and Hosted Worker state intact.

## Product Positioning

Product name:

- English: ENHE Product Promo Maker
- Chinese: ENHE 产品推广素材生成器

Promise:

- English: Turn product pages into promotional copy, video scripts, and publishing assets.
- Chinese: 把产品网页变成推广文案、视频脚本和发布素材。

The product prepares research, copy, scripts, evidence, and publishing materials. It does not promise guaranteed viral results, bypass CAPTCHA or risk controls, or click final platform publish actions without the required user or approved official API gate.

## Workstream A: In-Extension Guide

### Entry and state

- Add a compact help button to the existing top-right header beside language and local/license status.
- Open an in-extension guide view instead of a new network page.
- Keep the existing form state when returning: product URL, platform selection, workflow depth, command type, paths, subscription plan, and generated command.
- Keep the existing Chinese/English language preference and apply it to all new labels, buttons, headings, descriptions, and accessibility text.

### Guide tabs

The guide has three accessible tabs with `aria-selected`, `aria-controls`, keyboard focus, and touch-friendly hit targets:

1. Features
   - Group capabilities by outcome: material generation, platform evidence, publishing preparation, retrospective optimization, and automation.
   - Show the core value by default.
   - Put advanced capability explanations in native disclosure sections.
   - Each capability description answers what it does, what problem it solves, and what the user receives.
2. How to use
   - Show a four-step quick start: open a product page, capture or enter the URL, choose platforms and workflow, then generate and run or copy the command.
   - Explain advanced command groups, local-first execution, evidence collection, publishing boundaries, and manual confirmation.
   - Link to the full online documentation only as a supplement, not as a replacement for the in-extension quick start.
3. Subscription
   - Read plan labels, prices, and credits from the existing extension `PLANS` data instead of duplicating pricing constants.
   - Explain the current plans: Free 5 credits, Starter CNY 19 per 30 days and 60 credits, Growth CNY 59 per 30 days and 220 credits, Scale CNY 199 per 30 days and 800 credits.
   - Explain the intended audience, included usage, hosted-run boundary, and billing/License flow for each plan without exposing secrets.
   - Keep checkout and billing portal actions pointed to the existing ENHE website.
   - State that Hosted Worker remains disabled in this release.

### Visual and interaction rules

- Preserve the existing dark workbench, green accent, 8px radius, compact controls, and 420px popup language.
- Use a view replacement for the guide rather than adding a long always-expanded panel to the main form.
- Use a short view transition only; respect `prefers-reduced-motion`.
- Do not add a network request, Chrome permission, automatic login, CAPTCHA handling, or final publish automation.

## Workstream B: Full Responsive Workspace

### Architecture

- Keep the existing popup as a fast launcher for the common product URL to command flow.
- Add a full workspace mode opened from the popup with an `Open full workspace` action.
- Reuse the same markup contracts, translation dictionary, plan data, command-generation logic, and license state. Do not fork business logic between popup and workspace.
- Use a single page/view mode switch, such as the existing document with a `view=workspace` state, unless implementation evidence requires a separate shell with shared modules.

### Responsive behavior

- Popup mode remains constrained to a practical 380-480px width.
- Workspace mode uses a two-column desktop layout: configuration on the left, command/subscription summary and guide access on the right.
- Collapse to a single column at tablet widths.
- Use full-width controls and touch-safe spacing at 360px mobile width.
- Avoid hover-only actions, horizontal overflow, and fixed-height content traps.
- Treat mobile browser support as responsive layout compatibility. Do not claim that Chrome Android can install or run a desktop Chrome extension when the platform does not support it.

## Workstream C: Sales-Oriented Public GitHub Homepage

### Homepage structure

The public `README.md` and equivalent `README.en.md` lead with product value, not installation commands:

1. Product promise and primary download CTAs for Skill and Chrome extension.
2. The customer problems: fragmented product messaging, platform-specific content uncertainty, and disconnected evidence/review loops.
3. Customer outcomes: product-page intake, copy and script generation, multi-platform publishing preparation, and evidence-backed iteration.
4. Outcome-oriented capability sections explaining what the feature does, the problem it solves, the user benefit, and a typical use case.
5. The end-to-end workflow from product page to research, copy, script, publishing pack, manual confirmation, and retrospective optimization.
6. Free, Starter, Growth, and Scale audience fit, current CNY 30-day prices, and included credits.
7. Trust and boundaries: local-first behavior, no cookie upload, manual CAPTCHA/risk-control handling, final publish confirmation, and Hosted Worker disabled.
8. Five-minute installation and first-run path, with links to bilingual detailed documentation.
9. Creator, contact email, official website, product page, Chrome Web Store, privacy, terms, and support links.

The Chinese README remains the primary landing page. The English README mirrors the same factual fields, capability set, pricing, safety boundaries, creator information, and download destinations.

### Homepage visual language

- Use the existing ENHE dark/green product language and the approved extension screenshot or a repository-local equivalent.
- Keep the first viewport sales-oriented: promise, audience, outcome, and download choices must appear before long technical sections.
- Use short sections, clear CTA hierarchy, and an outcome table or capability grid without making the page read like an API reference.
- Keep installation, privacy, platform research, publishing, troubleshooting, and version-sync documents available below the sales entry point.

## Data and Safety Boundaries

- Payment, checkout, subscription authorization, credits, and license purchase remain outside Skill/extension capability parity conclusions, while the existing extension billing UI remains packaged.
- Hosted Worker remains disabled.
- No secrets, browser profiles, cookies, tokens, generated output directories, backend runtime, or Sidecar checkout/runtime data enter the public repository.
- Existing extension permissions remain unchanged: `activeTab`, `storage`, `clipboardWrite`, and the approved ENHE host permission.
- Published extension bytes remain byte-faithful to the validated store ZIP and traceable to the exact merged Git commit.

## Verification and Acceptance

### Extension tests

- Verify the help entry, guide tabs, new translation keys, and accessibility attributes in both locales.
- Verify popup-to-workspace navigation and restoration of form state.
- Verify shared command generation and subscription plan data in both modes.
- Verify responsive layout at 360px, 768px, and 1280px widths without horizontal overflow.
- Verify no permission expansion and no Hosted Worker activation.

### Distribution tests

- Run the existing Sidecar, Skill synchronization, distribution-contract, and promotion-manager regression suites.
- Build the standalone public repository from a clean exact source commit.
- Run the public validator, release builder, public tests, checksum generation, and forbidden-content/security scans.
- Verify both Skill and extension ZIPs, release manifest, SHA-256 sums, bilingual parity, safe sales claims, and README links.
- Push one source PR, squash-merge it, rebuild from merged `main`, create the public repository and `v0.5.3` Release, and upload the same extension ZIP to the existing Chrome Web Store item.

## Explicit Non-Goals

- No new backend or Hosted Worker implementation.
- No Chrome permission expansion.
- No new payment provider or checkout flow.
- No automatic CAPTCHA solving, risk-control bypass, login, or final platform publishing.
- No claim that the extension itself runs on unsupported mobile Chrome installations.
- No unrelated refactor of the Skill runtime or payment backend.
