# KR Fresh Macro Temporal Rehearsal

## Result

`MACRO_TEMPORAL_REHEARSAL = FAIL`

The 2026-08-24 morning `MacroBriefing` was created before the temporal repair was promoted. Its
serialized `market_summary` has no `macro-digest-temporal-eligibility-v1` context and no per-item
`temporal` field. The normal KR path reuses that morning briefing. Both `daily_digest._temporal_role`
and `market_intelligence_service._observation_fact` default missing temporal metadata to
`CURRENT_OBSERVATION`, so legacy persisted evidence fails open.

## Unsafe Output

| Evidence | Actual date | Required role | Rehearsal wording/result |
|---|---|---|---|
| SOXX vs SPY | 2026-08-21 | prior completed US session | important change without prior-session label |
| VIX | 2026-08-20 | reference lagging | `VIX가 +7.5% 움직여` as current change |
| WTI | 2026-08-18 | reference lagging | `WTI가 +2.0% 움직여` as current change |

The three direct errors also propagated into the current one-line and two `현재 신호` assumption
blocks. Current KR-close FX dated 2026-08-24 remained safe. Packet audit incorrectly reported 14
current Fact IDs, prior 0, reference 0, and an empty temporal contract.

## Classification

- Unsafe direct temporal claims: 3
- Derived current-signal contaminations: 3
- Prior-session mislabeled current: 1
- Reference-lagging reused as today signal: 2
- Severity: P0 under this rehearsal instruction

The bounded repair is a legacy-briefing compatibility gate: when the temporal contract is absent,
digest and market-intelligence consumers must fail closed or deterministically rehydrate roles from
stored observations and the prior briefing. A regression must cover a pre-contract morning briefing
consumed after code promotion. No macro configuration or runtime code was changed in this task.
