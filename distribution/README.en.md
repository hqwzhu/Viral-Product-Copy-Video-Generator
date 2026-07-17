# ENHE Product Promo Maker

Turn product pages into promotional copy, video scripts, and publishing assets.

[中文](README.md) | [Official website](https://www.enhe-tech.com.cn/) | [Product page](https://www.enhe-tech.com.cn/promotion-manager) | [Chrome Web Store](https://chromewebstore.google.com/detail/enhe-promotion-manager/dloklkbnmoigemnfigbkibogmgbieppl)

```text
Product page -> product facts -> high-performing/competitor evidence -> platform copy -> video scripts and assets -> publishing packs -> real-data review
```

Give it a public product page and ENHE Product Promo Maker organizes verifiable product facts and public evidence on your computer, creates channel-specific drafts for YouTube, Zhihu, Xiaohongshu, Douyin, GitHub, and other destinations, then packages video, images, publishing checks, and follow-up review entry points into an actionable set of files. It is designed for independent developers, product teams, content operators, and service providers. It does not promise fixed traffic or conversion results, and it does not replace the account owner for the final publishing action.

## What you provide and what the product delivers

A standard local run produces:

- Product facts and evidence: positioning, capabilities, target users, quoted page text, source links, evidence status, and risk notes.
- Platform copy drafts: titles, body copy, tags, descriptions, and initial comment or reply prompts, structured for each platform.
- Video scripts and storyboards: spoken scripts, shot pacing, visual guidance, subtitle emphasis, and an asset list.
- Media drafts: MP4 video drafts when the required tools are available, plus PNG cover and detail images when Pillow is installed.
- Publishing packs: platform copy, video and image paths, tracking links, missing items, risk notes, manual steps, and pre-publish checklists.
- Evidence inboxes: entry points for real published URLs, metrics, comments, order exports, and revenue exports, with demonstration data kept separate from real results.
- Retrospective reports: comparisons of content performance, audience feedback, and business evidence, followed by recommendations for the next iteration.

If a page cannot be read completely, a media dependency is absent, or platform access is limited, the output records `partial_ready`, `missing`, or the relevant blocked status so that you can collect the missing evidence or finish the step manually.

## More than one piece of copy: a complete promotion-preparation workflow

Basic copy tools often compress a product link into generic prose. You still have to verify facts, find relevant examples, rewrite for each platform, make video and images, assemble publishing fields, record links, and review the real results. This project connects those steps in one local workflow:

1. Read one product page, multiple links, or a website entry point.
2. Preserve traceable facts and distinguish page evidence, public platform evidence, user-imported evidence, and missing information.
3. Research publicly available or browser-visible competitors, creators, and structures used by high-performing content.
4. Create platform-native drafts instead of copying the same paragraph to every channel.
5. Produce spoken scripts, storyboards, optional MP4 files, cover images, detail images, and complete publishing packs.
6. Assist with publishing after user review, then accept real post-publication data.
7. Review real data and turn it into recommendations for the next topic, hook, and asset set.

The result is not merely readable. It is organized to be reviewed, completed, published, recorded, and improved.

## How the Skill and Chrome extension work together

The Chrome extension is a lightweight entry point. The Codex Skill is the local execution engine.

| Component | Primary role | Best used when |
| --- | --- | --- |
| Chrome extension | After a user click, reads the current tab URL and title, lets the user choose platforms, workflow depth, and command type, then creates a local command that can be reviewed and copied | You are viewing a product page and want to create a task quickly |
| Codex Skill | Reads the product, researches evidence, creates content and media drafts, organizes publishing packs, imports real data, and runs retrospectives | You need full execution, file deliverables, and an audit trail |

A typical path is: open a product page -> click "Use current tab" in the extension -> select target platforms -> copy the generated PowerShell command -> run it from the Skill directory in the public repository -> review `promotion-output`. The extension can generate commands on its own, and the Skill can run directly without the extension.

The extension's existing payment, subscription, license, credits, and billing UI remains included, but those capabilities are outside the conclusion that its non-payment commands match the bundled Skill. Hosted Worker is disabled; the public edition does not describe hosted execution as available.

## Capabilities and customer benefits

- From webpage to fact file: reduce manual extraction and the risk of presenting assumptions as product capabilities.
- From public evidence to content direction: keep sources and status visible so hooks, structures, and platform choices are easier to review.
- From one product to platform-specific drafts: reduce repeated rewriting while preserving how each platform communicates.
- From script to media draft: create MP4, PNG cover, and detail-image drafts locally when their dependencies are available, shortening production preparation.
- From scattered files to publishing packs: keep copy, tags, video, images, warnings, and operating steps in one delivery structure.
- From publication to real-data review: accept real URLs, metrics, comments, order exports, and revenue exports, then use that evidence to guide the next iteration.
- From a webpage entry point to a local task: turn the current browser page into a reviewable command without manually copying many parameters.
- Chinese and English UI: let Chinese-language operators and English-language collaborators use the same workflow.

See the complete [feature catalog](docs/en/features.md).

## Start in five minutes

In Windows PowerShell:

```powershell
git clone https://github.com/hqwzhu/enhe-promotion-manager.git
cd .\enhe-promotion-manager\skill\viral-product-copy-video-generator

python scripts\skill_entry.py `
  --link "https://example.com/product" `
  --platforms youtube,zhihu,xiaohongshu,douyin,github `
  --out-dir ".\promotion-output"
```

Open the batch report first:

```text
promotion-output\reports\promotion-manager\batch\product-batch-runner.json
```

Its `promotionRuns` array gives each product's actual `outputDir`, `workflowManifest`, and `publishQueue`. Product content, video, images, publishing packs, and retrospectives live under the corresponding `promotion-output\product-batch-runs\<run>` directory. The runtime creates `<run>`; do not guess it manually. MP4 rendering, dynamic browser reads, and PNG generation are optional enhancements. If a related dependency is absent, text deliverables continue and the missing media is marked explicitly.

You can also install the extension from the [Chrome Web Store](https://chromewebstore.google.com/detail/enhe-promotion-manager/dloklkbnmoigemnfigbkibogmgbieppl), or follow the [installation guide](docs/en/installation.md) to use the unpacked `extension\chrome` directory and Skill ZIP. The local workflow does not require a subscription or Hosted Worker.

## Supported platforms and current boundaries

| Platform or source | Current path | Primary boundary |
| --- | --- | --- |
| Product pages and websites | Static reads, Playwright browser snapshots, site-link discovery, sitemaps, or HTML saved by the user | Dynamic pages may require Chromium; private pages behind login are not default public sources |
| YouTube | Public pages, public or official data paths, content drafts, official API dry-run, and credential checks | A real upload requires user credentials, platform authorization, and explicit approval |
| GitHub | Public repository evidence, README/Issue/Release drafts, and controlled official paths | Confirm the target, permission, and approval before writing to a real repository |
| Zhihu | Public or browser-visible pages, user exports, and an optional local Sidecar using local login state | The user handles login, platform verification, or risk controls; evidence may remain partially ready |
| Xiaohongshu | Public or browser-visible pages, user exports, and an optional local Sidecar using local login state | Page structure, login, and risk controls affect collection; publishing normally uses a manual or browser-assisted path |
| Douyin | Public or browser-visible pages, user exports, and an optional local Sidecar using local login state | Platform verification, login, and official publishing permissions are external requirements |

Research uses only public, browser-visible, officially authorized, or user-provided data. The system does not evade platform verification, login checks, or risk controls. The user confirms the final publishing action; browser-assisted flows stop before final submission.

## Local-first and auditable by design

- Output is written to the local directory you choose by default; the public repository and release packages do not contain runtime output.
- Cookies and Chrome login profiles stay on the local computer and are not uploaded to this public repository or its public release packages.
- MediaCrawler Sidecar is a separately installed upstream dependency. When it uses local Chrome login state, its checkout, virtual environment, configuration, and raw output remain outside the public repository.
- Hosted Worker: disabled. The public edition neither requires nor provides hosted execution.
- Platform publishing requires user review and action. Official API paths also require the user's own credentials, account authorization, and explicit approval.
- Only real published URLs, metrics, comments, orders, and revenue are recorded as real evidence; evidence is not fabricated.
- Payment, subscription, license, credits, and billing backends are excluded only from the feature parity conclusion. The extension's existing billing UI and `billing-contract.json` remain included.

See [data and privacy](docs/en/data-and-privacy.md) and the official [privacy policy](https://www.enhe-tech.com.cn/promotion-manager/privacy).

## Current version and downloads

- Public repository, Skill, and extension source: `0.5.3`
- Current public Chrome Web Store version before update: `0.5.2`
- Public releases: [GitHub Releases](https://github.com/hqwzhu/enhe-promotion-manager/releases)
- Skill package: `enhe-product-promo-maker-skill-0.5.3.zip`
- Extension package: `enhe-promotion-manager-extension-0.5.3.zip`
- Existing store listing: [ENHE Promotion Manager](https://chromewebstore.google.com/detail/enhe-promotion-manager/dloklkbnmoigemnfigbkibogmgbieppl)

See [version synchronization](docs/en/version-sync.md) for the version relationship, the 11-command non-payment parity result, and the store update boundary.

## Creator and contact

- Brand and creator: ENHE AI
- Operating and support entity: Shenzhen Longgang District Enhe Network Technology Studio, legally registered in Chinese as 深圳市龙岗区恩禾网络科技工作室
- Website: https://www.enhe-tech.com.cn/
- Product page: https://www.enhe-tech.com.cn/promotion-manager
- Contact: huqingwei5942@gmail.com
- GitHub: https://github.com/hqwzhu

Report security issues privately under the [security policy](SECURITY.md). For product questions, begin with [troubleshooting](docs/en/troubleshooting.md).

## License and third-party components

`LICENSE` records `Copyright (c) 2026 HU`. `HU` is the code copyright identifier/rightsholder shown in the MIT license. `ENHE AI` is the product brand and creator identity. Shenzhen Longgang District Enhe Network Technology Studio (深圳市龙岗区恩禾网络科技工作室) is the public operating and support entity. The scope and terms of the grant are controlled by `LICENSE`; this explanation does not change the license or infer that the operating entity owns the code copyright.

Third-party runtimes and upstream dependencies remain subject to their own licenses.

MediaCrawler is a separate upstream project and is not covered by this repository's MIT grant. Any commercial license offered for ENHE does not automatically relicense MediaCrawler source code to public users. Users must follow the upstream license, platform terms, and applicable law. See [NOTICE](NOTICE.md) for details.
