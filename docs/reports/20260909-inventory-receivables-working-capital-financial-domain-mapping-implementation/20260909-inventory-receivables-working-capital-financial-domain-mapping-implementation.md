# M10 Inventory, Receivables and Working-Capital Mapping

## Result

- Status: `M10_COMPLETE`
- Production readiness: `NOT_READY`
- Base: `2e93eb9dcfab7594007af0139d6e2bd7c15a5009`
- Work-instruction commit: `584876a091fbf3ad10b833fe3706c7c2daf5a3c2`
- Implementation commit: `c898343db3d416243183c2c62746b08dc461b6a2`
- Contract: `inventory-receivables-working-capital-v1`

## Frozen accounting policy

- Exact aggregate inventory takes precedence over child components; no reconstructed total is made.
- Trade and broad receivables/payables remain distinct, and net/gross balances never compare.
- Contract assets and liabilities are `SEPARATE_WORKING_CAPITAL_CONTEXT`.
- Current assets minus current liabilities is not operating working capital.
- The only M10 derivation is `balance_absolute_delta` with exact input lineage.
- `prior_year_comparable` and `prior_year_end` stay separate; year-end to interim is not YoY.
- DSO, DIO, DPO, CCC, scores and directional interpretations remain disabled.

## Measured archive coverage

The preserved US archive still contains no reusable balance-sheet payload. Real US inventory,
trade receivable/payable and comparison coverage is therefore `0`; exact SEC capability is a
labeled synthetic contract proof only.

The seven preserved KR official filings contain six non-financial issuers and one insurer.
Inventory is direct for `6 / 6`, trade receivables for
`5 / 6`, trade payables for
`5 / 6`, with broad receivable/payable context for
the remaining issuer. Exact current and prior-year-end XBRL contexts produce
`38` safe absolute deltas. All are
`prior_year_end`; real prior-year comparable counts are `0`. Insurance generic emissions are
`0`.

## Safety and validation

- Ticker-specific, SEC fuzzy and OpenDART fuzzy mappings: `0`
- Universal OWC/NWC formulas and DSO/DIO/DPO/CCC derivations: `0`
- Compact AI, Directional, Timing, renderer, sufficiency, Daily Delta and warning changes: `0`
- Model/provider/production/scheduler mutations: `0`
- Monitoring paths observed paused or disabled: `8 / 8`
- Focused tests: `339 passed`
- Full tests: `2970 passed` with `1` existing deprecation warning
- Ruff and `git diff --check`: `PASS`

## Next scope

`NON_OPERATING_FINANCIAL_INCOME_EFFECTS_MAPPING_IMPLEMENTATION`

Directional financial-context consumption, model proof, production activation and schedule
resume remain out of scope.
