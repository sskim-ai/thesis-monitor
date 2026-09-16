# M12BZ Maturity Polarity Convergence Result

## Decision

M12BZ closes the Stage-2 maturity-polarity ownership defect, but the new Full22
generation is not a complete proof. Track A stopped at model-call ordinal 7 on an
unrelated existing semantic gate:

```text
GOOGL: preconfirmation_buy_flag_missing
```

The immutable generation is
`20260916-uskr22-m12bz-20260916T003454Z-60a267c475f8`. It must not be resumed,
stitched, repaired, or selectively rerun.

## Repository

- Base: `820593cbf97e50e4e303359b4f36cc0e5b54c91f`
- Work-instruction commit: `d8d2351`
- Frozen implementation: `60a267c475f89fd39c051266b0e458c468a20184`
- Branch: `codex/20260916-m12bz-maturity-polarity-single-source-convergence`
- Origin main observed at start: `9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479`
- Main merge, deploy, and remote push: `0 / 0 / 0`

## Polarity Architecture

The historical `decision-evidence-polarity-v1` service is still present and owns
structured `BULLISH`, `BEARISH`, and `NEUTRAL` claims, but it had no stable atomic
claim identifier and Stage-2 bypassed it. The selected classification is:

```text
CANONICAL_POLARITY_SERVICE_REQUIRES_THIN_STAGE2_ADAPTER
```

`stage2-maturity-polarity-adapter-v1` projects already structured frozen-core
drivers through the historical polarity vocabulary. The deterministic identity is
`maturity-atomic-claim-identity-v1`, derived from ticker, proposition text, sorted
source refs, and logical condition. Polarity is metadata and is deliberately not
part of proposition identity.

The same atomic claim is forbidden on both sides. A mixed parent source may occur
on both sides only when different canonical child claims prove the split. No
free-form classifier, Korean sentence splitter, ticker exception, or model-based
atomization was added.

## Deterministic Gate

- Focused: `128 passed`
- Wider: `164 passed`
- Full: `4044 passed, 63 skipped, 2 warnings`
- Ruff: PASS
- `git diff --check`: PASS
- Historical polarity regressions: PASS
- Mixed-parent positive fixture: PASS
- Same-atomic negative fixture: rejected
- Single-polarity overlap fixture: rejected
- Missing-identity fixture: fail-closed
- Old M12BY CORZ output: `PASS_FAIL_CLOSED`

The prior M12BY bundle independently reverified at SHA-256
`07459f1a9e84c56b875ea91a54678e9deb70eecdf7dfbba73460a1c124005927`.
Its manifest has 141 indexed payloads and 142 ZIP entries, with zero missing,
extra, hash, size, or secret-scan failures.

## New Generation

Frozen packets remained unchanged:

- US: `2c01a21c887ca41512798199387120e8ded5afd2888f5b78a9c54ea59e975228`
- KR: `819af90aa5ff159ee77ef2be69fc115ad169631acc9cfcc101081bef4318b597`

The model was `gpt-5.6-sol` at `xhigh`. Planned/started/completed/usable calls were
`16/7/7/7`. Retry, fallback, judge, repair, and selective rerun were all zero.

All five US Fundamental Core batches passed: 14 cores, zero cardinality, ticker-set,
duplicate, missing, extra, identity, or exact-ref failures. Stage-2 returned six
schema-valid candidates. Five were semantically valid; GOOGL alone failed
`preconfirmation_buy_flag_missing`. Exact refs and typed dates remained clean.

Across those six candidates:

- Maturity atomic-identity failures: `0`
- Same-atomic-claim overlaps: `0`
- Unproven parent-source overlaps: `0`
- Valid parent-source overlaps with distinct child claims: `1`
- Frozen-core revalidation false positives: `0`

CORZ no longer reuses one undifferentiated claim on both sides. Its operating
progress and capital/risk propositions from the mixed source receive different
atomic IDs. IBM provides the direct positive fixture: one parent source appears on
both sides of a MIXED row, with disjoint BULLISH and BEARISH child claims.

## Terminal Failure

The GOOGL output passed schema, exact-ref, typed-date, atomic-identity, and
frozen-core checks. The existing Stage-2 semantic validator then returned only:

```text
preconfirmation_buy_flag_missing
```

The preflight attempted to enter its ordinary repair path, but the frozen proof's
repair guard terminated the run. No repair prompt or model call was executed. This
is `FULL22_REPROOF_NEW_HARD_FAILURE`, not a polarity regression.

## Market Context

Local Track B remains PASS. Kiwoom KOSPI200 2026-09-01 through 2026-09-03 fixture
replays pass, and a percentage is suppressed when no source-owned basis exists.
The gateway variables `KIWOOM_GATEWAY_URL` and `KIWOOM_GATEWAY_API_KEY` are not
configured; therefore no live capability or quote call was made. Read/order/modify/
cancel calls are `0/0/0/0`, and KOSDAQ150 remains unproven.

FRED DGS3, DGS5, DGS10, DGS30, DFII10, and T10YIE parsing, same-series comparison,
basis-point change, as-of ownership, rendering, and time-layer ordering pass.
Market-context leakage into BusinessDelta or holder fundamentals is zero.

## Safety And Gate

Production DB, assessment, warning, notification, Telegram, scheduler, monitoring,
main, deploy, and remote-push mutations are all zero. Production Assist and V2
production gates were not changed.

```text
TRACK_A_RESULT = FULL22_REPROOF_NEW_HARD_FAILURE
TRACK_B_RESULT = MARKET_CONTEXT_READY_KIWOOM_GATEWAY_UNAVAILABLE
TOP_LEVEL_RESULT = M12BZ_MODEL_CONTRACT_BLOCKED_MARKET_CONTEXT_READY
MESSAGE_MODEL_CONTRACT_READINESS = NO
MARKET_CONTEXT_READINESS = LOCAL_PASS_LIVE_KIWOOM_UNAVAILABLE
DEPLOYMENT_READINESS = NO
```

Open P0 is zero because the shadow proof failed closed before any production
mutation. Open P1 is one: generic preconfirmation BUY-flag contract convergence.

Next scope:

```text
BOUNDED_PRECONFIRMATION_BUY_FLAG_CONTRACT_REPAIR_AND_NEW_FULL22_REPROOF
```

Kiwoom read-only gateway configuration remains an independent final-smoke
prerequisite.
