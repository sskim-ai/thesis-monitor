# OHLCV V2 Pipeline Repair Readiness

## Decision

`OHLCV_V2_PIPELINE_REPAIR = READY_FOR_MAIN`

`NEXT_ACTION = WAIT_FOR_NEXT_NATURAL_US_LIVE`

The repair and its complete report were promoted by clean fast-forward to main/operating code SHA
`3efe688bb7eaa41bc084061c9eb9de910d86423a`. Exact-SHA Actions run `33464969356` passed Test and
Lint, and both the thesis-monitor API and OHLCV service passed health checks. Natural `LIVE_PASS`
is still deliberately pending.

## Root cause and repair

The primary root cause is `PROCESS_NAMESPACE_MISMATCH`: the LaunchAgent OHLCV service and host
endpoint were healthy, while the restricted decision process could not open the loopback socket.
The old path duplicated a local HTTP fetch during V2 decision preparation and propagated one
connection exception across the full cohort.

The repaired path is:

```text
canonical acquisition
-> validated D/W/M features
-> packet-owned-technical-context-v1
-> immutable packet
-> V2 context preparation without fresh local HTTP
-> subject-local eligibility
-> candidate/adjudication/accepted plan
```

The client has bounded retry and health-aware recovery. Missing, stale, malformed, and partially
available technical data fail closed per subject. Price Structure and valuation calculations are
unchanged.

## Retrospective proof

- run-49 cohort: `14`
- technical context FULL/PARTIAL_SAFE/UNAVAILABLE/INVALID: `10 / 0 / 0 / 4`
- context prepared: `14 / 14`
- candidate generated: `14 / 14`
- accepted-ready: `14 / 14`
- explicit V2 decisions: `14 / 14`
- accepted distribution BUY/HOLD/SELL: `0 / 11 / 3`
- fallback: `0`
- accepted message quality: `PASS`
- current test sink: `14 / 14 exact`

CPNG, HUT, MU, and SKHY remain `INVALID` for provider OHLC integrity, not transport failure. They
do not block peers, do not receive invented low-level timing evidence, and still receive explicit
long-horizon decisions only where safe non-technical and packet-owned evidence is sufficient.

## Validator repair

The `:2000` false positive came from a word-boundary mismatch after a Korean particle. The lexer
now uses ASCII-aware numeric boundaries and validates the exact rendered span. Russell 2000
structural references pass; unsupported standalone numeric 2000 controls still fail. There is no
allowlist, ticker exception, or disabled provenance surface.

## Gates

| Gate | Result |
|---|---|
| root cause reproduced | PASS |
| service/client lifecycle | PASS |
| bounded reconnect/restart recovery | PASS |
| packet-owned technical context | PASS |
| technical numeric parity | PASS |
| subject/system failure isolation | PASS |
| run-49 accepted replay | PASS |
| KR regression | PASS |
| provenance positive/negative controls | PASS |
| exact US test sink | PASS |
| accepted ownership unchanged | PASS |
| decision calibration retuned | `0` |
| Price Structure/valuation diff | `0 / 0` |
| Public Action/schedule diff | `0 / 0` |
| full local tests and exact-SHA CI | PASS |

## Open issues

- Open P0: `0`
- Open material P1: `0`
- P2: legacy CPNG deterministic noun-phrase polish; existing typed valuation-basis caution wording
  repeats across some subjects. Neither changes evidence, OHLCV safety, or decision ownership.

This is retrospective and test-sink closure, not natural `LIVE_PASS`. No completed production run
was replayed. Main promotion is allowed; the next proof is the next naturally scheduled US cycle.
