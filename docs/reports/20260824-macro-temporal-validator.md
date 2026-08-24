# 2026-08-24 Macro Temporal Validator

## Contract

The schema-4 semantic gate reads temporal roles from market Fact fields whenever
`macro-digest-temporal-eligibility-v1` is present.

Rejected:

- reference/stale/unavailable Fact in `important_changes`;
- prior-session Fact without `직전`, `전일`, `이전`, `거래일`, or `기준` wording;
- `오늘`, `현재`, `간밤`, or current-session movement language when every linked Fact is
  non-current.

Allowed:

- genuine `CURRENT_OBSERVATION` movement;
- explicit prior-session context;
- reference facts in non-current background context;
- a new official macro release during cash-market closure.

## Fixtures

| Fixture | Expected | Result |
|---|---|---|
| reference VIX described as today's +7.5% move | reject | PASS |
| reference Fact in important changes | reject | PASS |
| prior-session VIX without a prior label | reject | PASS |
| prior-session Fact with explicit prior-session wording | allow | PASS |
| current new official release | allow | PASS |

Thresholds and existing numeric/semantic validators were not relaxed. Unknown Fact IDs, numeric
provenance, required night-futures Facts, portfolio group transmission, and runtime quality remain
independent hard gates.
