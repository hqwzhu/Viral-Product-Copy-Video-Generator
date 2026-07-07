# Workflow Reference

Use this reference when running a full promotion cycle.

## Stage 1: Intake

Required fields:

- product name
- product URL
- target audience
- pain points
- value proposition
- pricing or pricing assumption
- language
- target platforms
- primary goal: `traffic`, `leads`, `sales`, `seo`, `brand`, or `github_stars`

If the user only provides a URL, inspect the page and derive a draft profile. Label uncertain facts as assumptions.

## Stage 2: Research

Create a competitor and trend research note before generating final content when the user wants current market positioning.

Minimum research output:

- platform
- competitor URL
- creator/repo/account name
- title
- content format
- hook
- structure
- CTA
- visible public metrics, only if actually observed
- why it works
- reusable pattern

Use live research for platform/API claims because publishing capabilities change.

## Stage 3: Generate

Generate one platform-native content pack per target platform. Content must include a CTA and compliance note.

## Stage 4: Review

Use the bundled scorecard first. If `cheat-on-content` is installed, run it as a second-pass qualitative reviewer. Do not mutate real prediction logs unless the user asks.

## Stage 5: Publish Pack

Create publish packs. Every pack requires human approval before execution. Browser-assisted publishing may fill forms, but the user must click the final publish button.

## Stage 6: Retrospective

Generate a retrospective only from real data and evidence. If data is missing, return `waiting_real_data`.

