# Phase 7.2 Relational Reasoning Experiment

Date: 2026-08-15

Branch: `codex/phase-7-2-relational-reasoning`

Stage A base: `7d9f59fa1b5bc6034ea5cc9620482b39e4a96f07`

Experimental policy: `daily-review-v3.10`

Output schema / structure / Pilot / renderer: `4` / `v2` / `v3` / `v3`

Status: experimental, not merged, not deployed, not sent

## Isolation

The experiment used a SQLite-consistent read-only backup of the 2026-08-15 operating data and a
copied company-profile provenance directory. Live providers were disabled. The branch generated one
new experimental packet, `2026-08-15-us-run-18-118f331178d2`, containing one market review and 13
stock reviews. It did not write to the operating database, official assessment history, operating AI
archive, Telegram, Scheduled Tasks, or Pilot state.

The preview title uses `US Pilot 2/5` because that would be the next successful US session. It is not
an earned Pilot day. The verified operating state remains KR 1/5 and US 1/5.

## V3.9 Baseline

The retained v3.9 preview was provenance-safe but repeatedly used the same stock template. The
baseline review identified seven substantive sentences repeated across all 13 stocks. Examples
included a generic statement that no new business-thesis fact existed, the same US supply-data
disclaimer, the same valuation-comparison caveat, common watch items, and common Unknowns. Headings
and mandatory safety boundaries were excluded from the seven-sentence target.

The result was safe but often read as one checklist with ticker-specific numbers inserted. New
observer and holder paragraphs also tended to restate the same price condition instead of answering
different decisions.

## Experimental Decision

The v3.10 branch changes reasoning and validation before rendering:

- Each stock selects at least one company-specific investment question.
- Related valuation facts are interpreted together without calculating an unstated spread.
- Modeled values remain modeled; provider consensus remains provider consensus.
- Industry routing supplies the interpretation frame for memory, biotech, foundry, auto/platform,
  and power-intensive compute businesses.
- New-observer text describes what would make new capital's price and fact asymmetry acceptable.
- Holder text separately names the chart review boundary and fundamental deterioration condition.
- The most material one or two next checks and Unknowns replace the common fixed checklist.
- Renderer semantic post-processing was not added.

A deterministic quality audit normalizes substantive sentences, records repetitions across at least
three stocks, measures numeric grounding by section, and counts stock-specific next checks and
Unknowns. Exact normalized equality between new-observer and holder text is a validation error. The
audit does not attempt to approve overall writing quality with fragile keyword rules.

## Representative Results

### CRCL

Before, the message displayed valuation numbers but did not clearly explain their relationship. The
experimental review connects current PER `42.41x` and forward PER `68.94x` to a weaker forward
earnings denominator and asks whether non-interest platform revenue can offset reserve-income
normalization. The packet classifies the forward value as provider consensus, so the review preserves
that identity rather than relabeling it as an internal modeled estimate. This packet truth takes
precedence over the stale example assumption that CRCL's forward value was modeled.

### MU

Current PER `19.86x` and forward PER `5.87x` are interpreted as an earnings-expansion assumption, not
as automatic cheapness. PBR `10.89x` and its historical position are connected to memory-cycle risk,
product mix, utilization, inventory, capex, and free-cash-flow confirmation.

### TSLA

Current PER `178.27x` and forward PER `145.9x` are connected to the growth, margin, and cash-flow
execution required to support a high-duration valuation. The unsafe monetary revenue amount remains
excluded because its financial-currency basis is unavailable; only safe percentage facts are used.

### TSM

Issuer revenue `NT$1.27T` and operating margin `60.3%` remain on the TWD financial-statement basis,
while the ADR price remains USD. PER `27.87x` and forward PER `21.36x` are related to process mix,
utilization, customer demand, capex, and margin durability without an ADR conversion.

### WULF

PBR `58.88x` and historical percentile `100%` are interpreted as a position above the comparable
historical observations, not a 100% overvaluation claim. The premium is tied to power economics,
utilization, expansion capital, dilution, and cash conversion.

### RXRX

The review does not force a PER conclusion on a loss-making biotechnology company. It prioritizes
clinical and regulatory milestones, partnership economics, cash runway, and dilution.

## Quality Audit

| Measure | v3.9 baseline | v3.10 experiment |
|---|---:|---:|
| Substantive sentences repeated across all 13 stocks | 7 | 0 |
| Substantive sentences repeated across 3+ stocks | At least 7 | 0 |
| Maximum substantive repeat | 13 stocks | 0 |
| Distinct new-observer / holder pairs | Inconsistent | 13/13 |
| Stock-specific next checks | Template-dominated | 13 |
| Generic next checks | Multiple | 0 |
| Stock-specific Unknowns | Template-dominated | 13 |
| Generic Unknowns | Multiple | 0 |

The reduction is not a synonym substitution result. The normalized audit still treats spacing,
bullets, and case as equivalent, and the new texts ask different company and role-specific questions.
Human review remains the approval boundary for whether the final messages read like useful investment
analysis.

## Numeric Safety

The draft contained only `{{numeric:ref_id}}` placeholders for user-visible numbers. The deterministic
binder produced 168 claims, with zero manual legacy claims, rejected bindings, removed unsafe values,
formatter failures, or unresolved placeholders. The full schema-4 validator passed with zero errors.
Each stock core judgment used two decisive canonical numbers, while the detailed earnings, price,
supply, and valuation sections retained their own occurrence-level claims.

TSM retained TWD issuer financials and USD ADR price. TSLA and WRD unsafe monetary amounts were not
rendered. No supplied US investor-flow classification was invented. Every rendered numeric occurrence
is represented in the binding artifact and final claims.

One packet-level limitation remains: several market-index facts share broad approved display labels,
which can make a non-SPY index reference select the `S&P500` label. The final experiment avoided that
unsafe ambiguity and used only SPY plus the correctly identified SOXX-relative fact. This is a
`PACKET/CANONICALIZATION` follow-up, not a renderer or reasoning fix, and was not changed in this
experiment.

## Validation And Mutations

| Item | Result |
|---|---|
| Binder | PASS |
| Full validator | PASS, 0 errors |
| Logical messages | 14 |
| Telegram chunks | 14 |
| Telegram sends | 0 |
| Operating DB mutations | 0 |
| Operating archive mutations | 0 |
| Official assessment mutations | 0 |
| Pilot count mutations | 0 |
| Scheduled Task changes | 0 |

## Artifacts

- [Full Telegram preview](20260815-us-v310-telegram-experimental-preview.md)
- [Quality and isolation audit](20260815-phase7-2-relational-reasoning-audit.json)
- [Numeric binding result](20260815-phase7-2-numeric-binding.json)
- [Validator result](20260815-phase7-2-validation.json)

## Remaining Gaps

- Work must review all 14 rendered messages for usefulness and tone before approval.
- The market-index label ambiguity needs a separate canonical packet-label fix before using affected
  non-SPY index facts in prose.
- This branch must not be merged, deployed, or assigned to Scheduled Tasks before explicit approval.
- A future live result must still satisfy validator PASS, full delivery, and archive completion before
  the Pilot count can increase.
