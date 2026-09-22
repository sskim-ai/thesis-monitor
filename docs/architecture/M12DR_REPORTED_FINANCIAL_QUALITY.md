# M12DR Reported Financial Quality

Contract: `m12dr-financial-quality-integrity-vs-corroborated-extreme-v1`.
This is an opt-in shadow extension over existing `FinancialSnapshot` and
`financial-lineage-v2` occurrences. No new persisted financial truth store,
default runtime integration, or valuation policy is introduced.

## Ownership

- `financial_observation_quality_service`: exact OpenDART formal occurrence,
  separate official preliminary corroborator, field dependencies and YoY math.
- `m12dr_financial_source_authority`: re-evaluates the frozen source inputs before
  granting comparative issuer-business authority. Absolute level, net-income
  composition, quality warnings and recurrence are not directional sources.
- `m12dr_offline_source_closure`: reads the original M12DQ database in read-only
  mode, verifies its hashes, appends comparison facts to a new shadow packet and
  re-evaluates all 22 subjects. Existing whole-row M12DK denials remain intact.
- `m12dr_fresh_blind_reproof`: source PASS -> blind ZIP/SHA -> per-subject
  authority-bound Core -> full A/future-B entitlement -> A8 -> unchanged M12DO
  raw/emitted binding and offline B8 capture -> B8 -> sealed results.

## Integrity And Caution

The original `validate_event_financials` predicates and 60% margin bound are
unchanged. The classifier does not turn an extreme observation into normal
profitability. Revenue's own source errors affect revenue and its comparisons;
unrelated net-income anomalies remain context. Operating income and net income
need same-period, same-basis corroboration to consume their owned extreme
observations. Operating margin inherits both revenue and operating income.

Identity, currency/scale, receipt, basis, source-column period, availability and
amount-lineage contradictions remain hard failures. A half-year filing envelope
may contain a verified standalone quarterly column: the exact occurrence owns
duration. Historical preliminary warnings are separately retained, never relabeled
as the selected formal source. No EPS/TTM/forward/PER/PBR taint is cleared.

## Consumption

Only exact revenue or operating-income prior-year comparisons may add
`OVERALL_DIRECTION`, `BUSINESS_CONTEXT` and `PASS_A_ARCHETYPE` permissions.
Valuation, entry and recurring-profit authority are not granted. A verified
depositary identity can project these issuer facts, but no price, ratio,
per-share denominator or valuation is transferred.

The implementation is shadow-only. Production send, DB/warning writes,
scheduler changes, merge, push and deployment remain prohibited. Model calls use
the already qualified official CLI and signed-in auth, sol/xhigh, 1,200 seconds,
one attempt; no fallback, repair, judge or automatic reveal. A failed gate never
authorizes a partial cohort to proceed.

## Proof Status

M12DR source coverage is 22/22, with original anomaly warnings retained.
Fresh Core inference is incomplete because the official CLI failed local
initialization under the launch permission boundary. A/B were not started.
See [source and runtime closeout](../reports/20260921-m12dr-source-and-runtime-closeout.md).
This implementation is not production-ready and has not been deployed.
