# Extension bilingual UI and branded icon design

Date: 2026-07-15
Status: Approved
Target version: 0.5.2

## Goal

Make the Chrome extension popup fully usable in Chinese and English, with a visible language switch and a branded store icon based on the official ENHE website logo. The pending 0.5.1 store submission remains unchanged; these changes are prepared as the next 0.5.2 package.

## Scope

- Add a compact `中文 / EN` switch in the popup's upper-right area beside the license status.
- On first launch, select Chinese when `chrome.i18n.getUILanguage()` starts with `zh`; otherwise select English.
- Persist the selected language in `chrome.storage.local.uiLanguage` and restore it on later launches.
- Localize all user-visible popup labels, options, placeholders, hints, validation messages, transient button states, license/usage/hosted-run status messages, and pricing summaries.
- Keep CLI commands, file paths, API fields, plan keys, platform identifiers, URLs, and product brand names unchanged.
- Add Chrome manifest locales for English and Simplified Chinese so the extension name, description, and action title follow Chrome's language.
- Replace the 128px store icon with an ENHE-branded composition and retain text-free 16px and 48px toolbar icons.
- Update extension documentation and build a version 0.5.2 store package.

## Popup architecture

Static text in `popup.html` will use `data-i18n` attributes. Placeholders will use `data-i18n-placeholder`; option labels and accessibility labels will use the same dictionary through explicit keys. `popup.js` will own one flat English/Chinese dictionary and expose small helpers to resolve a key and apply the active language.

The top bar will contain a right-side control group with the existing license status and a two-button segmented language switch. The active button uses `aria-pressed="true"`; the document `lang` attribute changes between `zh-CN` and `en`.

Initialization order:

1. Read `uiLanguage` with the existing extension settings.
2. If absent, derive `zh-CN` or `en` from `chrome.i18n.getUILanguage()` and persist it.
3. Apply translations before requesting the active tab or calculating estimates.
4. Restore existing license and form state.

Switching language updates the current DOM in place. It does not reload the popup, clear form values, regenerate commands, or alter stored license data.

## Dynamic messages

Dynamic UI messages will use translation keys with named parameters, including tab capture results, validation errors, copied/saved states, API progress and failure messages, license status, usage reservation results, hosted-run results, and pricing estimates. Generated CLI commands remain identical in both languages.

Unknown translation keys fall back to English. Missing or unsupported stored language values are normalized to the Chrome-language default.

## Chrome locale metadata

`manifest.json` will set `default_locale` to `en` and replace the extension name, short name, description, and action title with `__MSG_*__` references. Matching message files will be added under `_locales/en/messages.json` and `_locales/zh_CN/messages.json`.

The popup's manual language selection affects popup content only. Chrome-controlled surfaces such as the Extensions page continue to follow Chrome's own locale, as required by the platform.

## Icon design

The source asset is `enhe_icon_gradient_transparent.png`, a 569x365 PNG with a real alpha channel. The 128x128 store icon will follow Chrome's guidance:

- transparent 128x128 canvas;
- approximately 16px transparent padding on each side;
- a front-facing dark rounded 96x96 tile for contrast on light and dark backgrounds;
- the original ENHE gradient mark centered in the upper area without changing its colors or proportions;
- the application name split into `ENHE` and `PROMOTION MANAGER` beneath the mark;
- no outer border, large shadow, perspective, or watermark.

The 16px and 48px runtime icons will use simplified, text-free ENHE mark variants because the full name is not legible at toolbar sizes. Original source files will not be overwritten; project deliverables will use versioned intermediate names before the approved files are wired into the extension package.

## Testing and acceptance

Tests will be written before implementation and must initially fail for the missing behavior. They will verify:

- language controls and translation markers exist;
- English and Chinese dictionaries cover every referenced popup key;
- Chrome-language detection and stored preference behavior are present;
- all dynamic user-visible messages use translation keys;
- manifest locale references and both locale message files are valid;
- icon files are PNGs with the required dimensions and alpha channel;
- version is 0.5.2 and the generated ZIP contains locale and icon assets;
- existing browser-extension package, billing, and full regression tests still pass.

Visual acceptance will inspect the 128px icon at native size and the popup in both languages. The implementation will not submit or replace the currently pending 0.5.1 store review without a separate explicit publishing instruction.
