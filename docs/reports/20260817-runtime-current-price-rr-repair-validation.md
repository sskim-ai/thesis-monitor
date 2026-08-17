# Runtime Current-Price RR Repair Validation

## Repository And Scope

- Branch: `codex/phase-8-5-1-runtime-current-price-rr-repair`
- Base: `f32bbe7837dc75333915812fa3e84607dffa3d51`
- Implementation commit: `ce5f3c6`
- Main merge: no
- Operating deployment: no
- DB migration: none
- Production Assist: OFF
- AI mode: shadow
- Telegram sends: 0
- Pilot mutation: 0; runtime remains KR 3/5 and US 3/5
- Scheduled Task execution/configuration change: 0

## Repair

The repair makes market-session freshness exchange-calendar-aware. It does not expose stale chart
Facts. A new read-only packet preflight distinguishes `UNAVAILABLE_BY_CONTRACT` from calculated RR
lost at the Fact or numeric-registry layer.

The current-price contract remains:

```text
nearest valid Strong/Medium resistance lower bound
minus current adjusted chart close
divided by
current adjusted chart close minus current chart invalidation
```

Current-price RR and support-entry scenario RR remain separate semantics.

## Run-23 Reconstruction

The immutable packet, first rejection artifact, prior validated bound output, and operating DB were
opened read-only. The replay made an in-memory copy and wrote only Git documentation artifacts.

| Ticker | Before | After | Canonical display | Numeric path |
|---|---|---|---:|---|
| 005490 | `BUG_MISSING_FACT` | `READY` | 0.17배 | exact |
| 010120 | `BUG_MISSING_FACT` | `READY` | 0.32배 | exact |
| 012450 | `BUG_MISSING_FACT` | `READY` | 0.15배 | exact |
| 086280 | `BUG_MISSING_FACT` | `READY` | 0.47배 | exact |
| 005930 | `UNAVAILABLE_BY_CONTRACT` | unchanged | N/A | not required |
| 003690 | `UNAVAILABLE_BY_CONTRACT` | unchanged | N/A | not required |
| 000660 | `UNAVAILABLE_BY_CONTRACT` | unchanged | N/A | not required |

The immutable original validation contains eight RR missing-path errors. The repaired packet has
zero RR missing-path errors and zero unresolved preflight rows. A prior bound output replay under
the current validator still reports 63 unrelated contract-drift errors because that message
predates later schema-4 semantic hardening. Those errors are not hidden or counted as a full natural
message PASS. The targeted result is that no rejection remains attributable to the run-23 RR packet
loss.

## Numeric Path

All four available RR rows resolve exactly:

```text
fact_id: chart:structure:risk_reward:current_price
field_path: fields.ratio
unit: x
semantic_type: current_price_risk_reward_ratio
canonical display: deterministic multiple formatter
```

Scenario RR cannot satisfy this path. Missing Fact, mismatched value, absent registry row, wrong
semantic, wrong unit, or absent canonical display remains a fail-closed bug state.

## Tests

- Focused RR/session/packet suite: 234 passed
- Full pytest: 1026 passed, 1 third-party deprecation warning
- Ruff: PASS
- `git diff --check`: PASS
- Investment Knowledge SHA/parity: `559ad45e...a9d18`, PASS
- Chart Knowledge SHA/parity: `beee6455...e19b`, PASS
- Public Action 0.4.5 and operationId 20/20 unique: PASS

Fixtures cover XKRX holiday handling, same-day close, US session continuity, calculated Fact
canonicalization, exact registry semantic/unit/display, support scenario separation, missing Fact,
missing registry, wrong semantic, missing resistance, undefined invalidation, non-positive upside,
non-positive downside, the four affected tickers, and three unavailable controls.

## Regression Boundary

Phase 8.4 delta-first rendering, valuation context, observer/holder, Unknown/next-check behavior and
Phase 8.5 industry routing/causal validation were not changed. Existing numeric, financial,
security-identity, OHLCV, supply, receipt, fallback, and exactly-once tests remain green.

## Persistent Status

| Gap | Status |
|---|---|
| Current-Price RR Packet/Numeric Path | PARTIAL |
| Natural Live Validation | OPEN |
| Industry-Specific Reasoning | STRONG PARTIAL |
| KRX approval | PENDING/UNKNOWN from repository evidence |

Retrospective reconstruction is complete. The RR gap remains PARTIAL until the next natural KR
session independently passes packet completeness, full validation, runtime receipt, archive, and
exactly-once checks.
