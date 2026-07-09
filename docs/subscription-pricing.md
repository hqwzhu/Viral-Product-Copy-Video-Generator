# Subscription Pricing

This document defines the first commercial pricing model for the browser extension and hosted promotion workflow.

The local Codex Skill can run without a paid backend. Paid subscription is required only when ENHE hosts model calls, storage, scheduling, publishing assistants, or team features.

## Source Assumptions

As of 2026-07-09, OpenAI's official API pricing page lists token prices per 1M tokens and separates input, cached input, and output pricing: https://platform.openai.com/docs/pricing. The public OpenAI model docs also describe GPT-5.5 as a higher-cost model and GPT-5.4 mini/nano as lower-cost options.

Launch pricing should be recalculated before release because token pricing changes.

Conservative planning assumptions:

| Workload | Model tier | Input USD per 1M | Output USD per 1M | Notes |
| --- | --- | ---: | ---: | --- |
| Standard copy and research | GPT-5.4 mini class | 0.40 | 2.50 | Rounded above listed mini pricing to cover variance. |
| Deep strategy review | GPT-5.5 class | 5.00 | 30.00 | Conservative long-context planning rate. |
| Local MP4 render | ffmpeg | 0.00 | 0.00 | Compute cost is local unless ENHE hosts rendering. |
| Hosted storage and queue | ENHE backend | 0.05/run | 0.05/run | Placeholder for logs, queue state, and license checks. |

## Unit Cost Formula

```text
model_cost = input_mtokens * input_price + output_mtokens * output_price
infra_cost = hosted_storage + scheduler + queue + payment_fee_buffer
gross_cost = (model_cost + infra_cost) * safety_multiplier
```

Use `safety_multiplier = 1.6` at launch until real logs are available.

## Run Types

| Run type | Included work | Token plan | Estimated gross cost |
| --- | --- | --- | ---: |
| Command only | Capture tab and build Codex command | No hosted model call | 0.00 |
| Standard run | Product intake, copy, scripts, basic platform plan | 90K input, 35K output on mini tier | About 0.20 USD |
| Research run | Standard run plus viral discovery summary | 180K input, 65K output on mini tier | About 0.45 USD |
| Deep strategy run | Research run plus high-quality strategic review | 250K input, 80K output on GPT-5.5 tier | About 5.90 USD |
| Hosted MP4 add-on | Hosted render, storage, and download | No fixed token cost | Price separately if ENHE hosts compute |
| Browser publish session | Payload preparation, visible-field form fill coordination, screenshots, and post-publish commands | Mostly local/browser automation plus hosted state | About 0.20 USD |
| Real evidence inbox | Normalize published URLs, metric exports, comments, orders, revenue, and next-round recovery commands | Low hosted model usage unless ENHE adds hosted analysis | About 0.35 USD |
| Final readiness audit | Merge generated reports into the final capability matrix | No heavy hosted model call | About 0.10 USD |

## Credit Model

Credits prevent heavy users from creating losses.

| Action | Credits |
| --- | ---: |
| Command generation | 0 |
| Standard run | 1 |
| Research run | 3 |
| Deep strategy run | 15 |
| Hosted MP4 render | 3 |
| Browser publish session | 2 |
| Real evidence inbox | 2 |
| Final readiness audit | 1 |
| Scheduled weekly automation | Same credits as the run type |

Internal planning value: `1 credit = up to 0.35 USD gross cost`.

## Plans

| Plan | Price | Included credits | Guardrail | Best for |
| --- | ---: | ---: | --- | --- |
| Free | 0 USD/month | 5 trial credits | No scheduled jobs, no hosted publish support | Testing the extension and local command flow. |
| Starter | 29 USD/month | 60 credits | Overage disabled by default | Solo product operator. |
| Growth | 99 USD/month | 220 credits | Overage billed or hard capped | Regular product launches and content calendars. |
| Scale | 299 USD/month | 800 credits | Hard quota plus optional prepaid packs | Agencies, teams, and ENHE internal operations. |

At the planning value, Starter has up to 21 USD gross cost on 29 USD revenue, Growth up to 77 USD gross cost on 99 USD revenue, and Scale up to 280 USD gross cost on 299 USD revenue. Scale is intentionally thin at full burn and should require annual prepay, fair-use limits, or lower-cost routing before public launch.

## Overage

Recommended overage:

- 1 credit pack: 0.80 USD.
- 50 credit pack: 35 USD.
- 200 credit pack: 120 USD.

Hard-stop quotas are safer than unlimited usage during the first launch.

## Billing Architecture

Do not trust the extension as the payment authority.

Production components:

1. Payment provider checkout.
2. ENHE user account.
3. License table with plan, quota, renewal, and status.
4. Server-side usage ledger.
5. Hosted promotion API that checks quota before model calls.
6. Extension license validation endpoint.
7. Admin dashboard for refunds, quota adjustments, and abuse review.

The concrete API contract is in `docs/billing-backend-contract.md` and `browser-extension/billing-contract.json`.

The local reference implementation is:

```powershell
python scripts\billing_contract_simulator.py demo --plan growth --workflow-type research_run --out-dir ".\promotion-output"
```

Use it to verify that a plan's included credits, workflow credit costs, usage reservation, usage commit, and renewal webhook behavior match the pricing model before building the production backend.

## Launch Rule

Before public release, collect real usage logs for at least 50 workflows:

- input tokens
- output tokens
- model used
- browser search count
- generated artifacts
- video rendering time
- retries
- support tickets

Then adjust credits, prices, and route selection. Do not offer unlimited usage until real cost variance is known.
