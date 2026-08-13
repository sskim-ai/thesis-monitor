# Codex AI Review Hardening Validation

## Repository State

- Repository: `sskim-ai/thesis-monitor`
- Branch: `main`
- Base: `186317e5bfcc127c0ba62d0781c848b508899051`
- DB migration: none
- Public Action schema: unchanged (`0.4.5`, 20 operationIds)
- AI review mode: `shadow`
- GitHub Actions: pending at report creation

## Claim Schedule

Before, the 30-minute lease outlived the 20-minute primary-to-backup delay, so an interrupted primary could make the only backup skip the packet.

| Market | Primary | Backup before | Backup after | Lease | Margin |
| --- | --- | --- | --- | --- | --- |
| US | 08:50 | 09:10 | 09:30 | 30m | 10m |
| KR | 16:15 | 16:35 | 16:55 | 30m | 10m |

The repository validates `backup_delay > claim_lease + safety_margin`; defaults are 40m, 30m, and 5m. All four local-project Scheduled Tasks are ACTIVE with `gpt-5.6-sol`, high reasoning, and the live `/Users/sskim/Codex/thesis-monitor` project.

## Full Investment Knowledge

- Source: `docs/custom_gpt_knowledge_ko.md`
- Runtime mirror: `.agents/skills/thesis-monitor-daily-review/references/investment-thesis-analysis-monitoring-knowledge.md`
- Knowledge version: `2026-08-13`
- SHA-256: `4af4e4f41ef65e1a1b5c7d8dece08a72a89f06f1774493947718fddb3d762c8c`
- Source and mirror byte comparison: identical
- Custom GPT Instructions and uploaded Knowledge: unchanged

`knowledge-index.md` routes the full guide's core, earnings, price, macro, basis-safety, and industry sections. Every packet and output records the Knowledge version and checksum. The analysis policy is `daily-review-v2`, so older shadow history is not overwritten or presented as the same policy result.

## Industry Routing

Fixtures verified:

| Fixture | Routed framework | Safety expectation |
| --- | --- | --- |
| Memory | `memory_valuation` | Low peak-cycle PER alone cannot establish undervaluation. |
| Insurance | `insurance_reinsurance_valuation` | SaaS NRR and Rule of 40 are rejected as incompatible. |
| SaaS | `saas_recurring_revenue_valuation` | ARR/NRR changes remain unsupported when absent. |
| EPC | `epc_construction_valuation` | Contract margin and cash collection remain Unknown unless packet facts support them. |
| Biotech/pre-profit | `biotech_valuation` / `pre_profit_valuation` | PER is not forced onto an unsupported basis. |

Preliminary earnings route `provisional_earnings`; ADR/share uncertainty routes `adr_share_basis`. Shadow comparison flags unsupported FCF/inventory/ROIC/NRR/ARR/project-margin assertions and price-only thesis changes for review.

## Canonical Evidence

Before, a material event was reduced mostly to date, type, title, direction, materiality, and fingerprint.

After, the packet uses user-safe structured facts with stable `fact_id` values. Verified fields include:

- Earnings period, preliminary/full status, revenue, operating income, margin, and verified growth fields.
- Contract name, amount and currency, counterparty, period, region, and recent-sales ratio.
- Treasury transaction shares, denominator provenance, share ratio, amount, market-cap ratio, purpose, and materiality.
- Current and forward valuation with modeled/consensus/provider-only provenance and fail-closed historical comparability.

Raw OpenDART/parser/provider fields remain absent. The Telegram and packet paths share the same safe event extraction and KRW amount formatter.

## Numeric Provenance

Every numeric source is registered as `fact_id + field_path + value + unit + semantic_type`. AI prose numbers require a matching `numeric_claims` item.

Valid fixture:

```json
{
  "fact_id": "earnings:2026-06-30",
  "field_path": "fields.operating_margin_pct",
  "value": 10.0,
  "unit": "pct",
  "usage": "영업이익률 10%"
}
```

Formatter-compatible `318964597910 KRW -> 3,190억원` and approved `0.1095% -> 0.11%` rounding pass. Reusing current price `100 USD` as `매출 성장률 100%`, changing a field/unit, or writing an unsupported derived number fails validation.

## Claim Fencing

Claims now carry UUID `claim_id` values and use isolated paths:

```text
outbox/<packet-policy-knowledge>--<claim_id>.json.tmp
```

Validated scenario:

```text
08:50 primary claim A
09:10 active lease -> backup cannot claim
09:30 backup claim B -> reclaim succeeds
B finalizes
A resumes -> stale_claim_output rejected
```

If A's lease expires but nobody reclaims, A may still finalize because it remains the active claim. Finalization re-reads the active claim immediately before atomic promotion. B's completed output is preserved when A returns.

## Shadow Isolation

- Official `ThesisAssessment` mutation: none
- `NotificationDelivery` or Telegram mutation: none
- External web/API use: none
- OpenAI API integration or API key use: none
- Database migration: none

Comparison history now includes frameworks, facts, numeric claims, unknowns, deterministic warnings, and guardrail flags.

## Validation

- `pytest -q`: 473 passed, 1 existing dependency deprecation warning
- `ruff check .`: passed
- `git diff --check`: passed
- Skill validation: passed
- Knowledge source/mirror checksum: matched
- GitHub Actions: pending at report creation

## Remaining Gap

Production assist remains disabled. Actual 5-10 trading-day US/KR shadow quality and runtime timing still require observation before explicit assist-mode approval.
