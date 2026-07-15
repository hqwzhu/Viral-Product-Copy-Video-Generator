# ENHE Product Promo Maker Rebrand Design

**Date:** 2026-07-15
**Status:** Naming direction approved; implementation not started

## Goal

Replace the vague user-facing name “ENHE Promotion Manager / ENHE 推广管理器” with a name that immediately explains the product’s main value: turn a product page into promotional copy, video scripts, and publishing assets.

This is a user-facing rebrand only. It must not change payment behavior, license compatibility, API routes, stored data, hosted-run contracts, or the already submitted Chrome Web Store v0.5.2 package.

## Approved Product Identity

| Surface | Approved text |
| --- | --- |
| Full Chinese name | ENHE 产品推广素材生成器 |
| Full English name | ENHE Product Promo Maker |
| Short Chinese name | ENHE 推广素材 |
| Short English name | ENHE Promo Maker |
| Chinese promise | 把产品网页变成推广文案、视频脚本和发布素材 |
| English promise | Turn product pages into promotional copy, video scripts, and publishing assets. |

The full name is the canonical product name. The short name is used only where the full name is visually constrained, such as the browser toolbar, compact popup areas, and the text label beneath the store icon.

## Positioning

The name and first sentence shown to a new user must communicate this flow:

1. Open or provide a product page.
2. Capture the page only after the user acts.
3. Generate promotional copy, video scripts, and publishing assets.
4. Optionally continue into guarded local commands or ENHE-hosted runs.

The product must not claim that it guarantees viral performance, guarantees conversion, or automatically publishes everywhere. Research, workflow generation, assisted publishing, and performance review remain supporting capabilities, not promises in the product name.

## Naming Architecture

### Browser extension

- Chrome/Edge localized extension name:
  - Chinese: ENHE 产品推广素材生成器
  - English: ENHE Product Promo Maker
- Localized short name:
  - Chinese: ENHE 推广素材
  - English: ENHE Promo Maker
- Toolbar action title uses the full localized name.
- Popup heading uses the full localized name when space permits.
- Compact navigation or status areas may use the short localized name.
- The popup’s first explanatory sentence uses the approved promise.

### Store listing

- Store name uses the full localized product name.
- Short description leads with the input and output rather than internal terms such as “Codex workflow”.
- Recommended Chinese short description:

  把产品网页变成推广文案、视频脚本和发布素材，并生成受控的本地或托管推广任务。

- Recommended English short description:

  Turn product pages into promotional copy, video scripts, publishing assets, and guarded local or hosted promotion tasks.

- Detailed descriptions may explain research, competitor evidence, publish packages, licenses, credits, and review workflows after the direct product promise.
- The store icon continues using the ENHE website logo. Because the store icon is one global asset and cannot change with locale, its bottom text uses the single short English label “ENHE Promo Maker” to preserve legibility at 128×128.
- Store screenshots, reviewer notes, privacy disclosures, and permission justifications use the new full name.

### Checkout, billing, and public pages

- Checkout, billing, payment result, run status, privacy, terms, refund, and support pages use the new full localized name.
- ZPAY’s customer-visible order name becomes “ENHE Product Promo Maker <Plan>”.
- Prices, 30-day terms, QR checkout, mobile direct payment, License Key behavior, and payment authority remain unchanged.
- The first product reference in each legal policy includes the transition alias once:
  - English: ENHE Product Promo Maker (formerly ENHE Promotion Manager)
  - Chinese: ENHE 产品推广素材生成器（原 ENHE Promotion Manager）
- Later references in the same policy use only the new full name.

### Repository documentation

- Current README files, browser-extension guides, store submission guides, capability maps, and operator-facing documentation use the new name.
- Historical design specifications, implementation plans, release records, old package reports, and previous PR evidence remain unchanged as historical records.
- The GitHub repository name is out of scope for this rebrand.

## Compatibility Boundary

The following internal identifiers remain unchanged:

- URL paths containing /promotion-manager/
- API paths containing /api/promotion-manager/
- systemd service names beginning with enhe-promotion-manager-
- server directories under /opt/enhe/promotion-manager/ and /var/lib/enhe-promotion-manager/
- database state keys and existing license/payment records
- environment variable names
- npm package identifiers
- script filenames, Python module names, report schemas, and existing report paths
- Chrome extension ID dloklkbnmoigemnfigbkibogmgbieppl

Keeping these identifiers stable makes the rebrand compatible with existing licenses, bookmarks, deployed services, stored orders, and v0.5.2 installations.

## Version and Store Rollout

1. Keep the submitted v0.5.2 ZIP and its evidence unchanged.
2. Implement the rebrand as Chrome/Edge package version 0.5.3.
3. Check the Chrome Web Store dashboard before changing the active submission.
4. Do not withdraw, overwrite, or resubmit the current store item until its actual status is known.
5. After the v0.5.3 package and store assets pass local review:
   - if v0.5.2 is still pending, decide whether to wait for the current review or replace it with v0.5.3;
   - if v0.5.2 is published, submit v0.5.3 as the normal update;
   - if v0.5.2 is rejected, address the rejection and submit the corrected v0.5.3 package.
6. Deploy the public-page rename only from a merged commit, using the existing atomic release and rollback process.

The rebrand must not create a second Chrome Web Store item or change the extension ID.

## Implementation Scope

The implementation plan will include only:

- extension locale, popup, and manifest version changes;
- store listing, reviewer note, screenshot plan, and store asset text changes;
- user-facing backend checkout, billing, result, run, and legal-page text changes;
- customer-visible ZPAY order-name changes;
- current README and operator documentation updates;
- tests and package validation for the exact bilingual name and promise;
- v0.5.3 packaging, one PR, merge, production deployment, and store-update preparation.

It will not add features, change prices, change payment providers, enable Hosted Worker, reinstall Sidecar tools, change API contracts, or refactor unrelated code.

## Validation

### Automated checks

- Extension locale tests assert the full and short Chinese/English names.
- Popup tests assert the approved promise in both languages.
- Backend tests assert the new checkout, billing, result, run, and legal-page names.
- ZPAY tests assert “ENHE Product Promo Maker <Plan>” while preserving amounts and signed payment behavior.
- A scoped old-name scan rejects user-facing occurrences of “ENHE Promotion Manager” and “ENHE 推广管理器”, with an explicit allowlist for transition aliases and historical records.
- Package validation confirms version 0.5.3, Manifest V3, existing permissions, scoped host access, and no remote executable code.
- Existing backend Node tests and the full Python regression suite remain green.

### Manual checks

- Chinese Chrome locale displays ENHE 产品推广素材生成器.
- English Chrome locale displays ENHE Product Promo Maker.
- The toolbar and compact icon label remain legible with the short name.
- Store listing text makes the page-to-copy/video-assets value understandable without opening the detailed description.
- Checkout and legal pages retain bilingual switching, exact prices, QR payment, and approved retention language.
- Existing License Keys and the current extension ID continue working.

## Acceptance Criteria

- A first-time user can understand from the name and short description that the extension turns product pages into promotional copy and video-related publishing assets.
- All current user-facing Chinese and English surfaces use the approved naming system, except the explicitly defined one-time legal transition aliases.
- Internal compatibility identifiers remain unchanged.
- The v0.5.2 package and historical evidence remain intact.
- A validated v0.5.3 package is produced from reviewed source.
- One PR contains the complete rebrand and is merged before public deployment.
- Production and store-update preparation are verified without changing pricing, payments, privacy retention, or license behavior.
