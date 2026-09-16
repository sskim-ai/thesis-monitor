# M12CE Frozen Deterministic `as_of` Full22 Reproof Result

## Result

```text
M12CE_RESULT = FULL22_REPROOF_BLOCKED_BY_NEW_HARD_FAILURE
MESSAGE_MODEL_CONTRACT_READINESS = NOT_READY
DEPLOYMENT_READINESS = NO
NEXT_SCOPE = M12CF_SYMBOLIC_ONLY_MATURITY_PROVENANCE_OWNERSHIP_REVIEW
```

M12CE started a wholly new US14/KR8 generation under the frozen M12CD contract. It stopped at
call 8 exactly as required by the no-repair policy. Calls 9-16 were not run, and there was no
retry, fallback, judge, repair, selective rerun, output stitch, or prior-output reuse.

## Repository

```text
branch = codex/20260916-m12ce-deterministic-asof-full22-reproof
M12CD runtime implementation = 9a9bda729afcb0777d7228ee7151d31f0b2f84f8
M12CD final local = 6f87e8723cae359054335ee8fa92f5efca40047b
M12CE work instruction = 96a562d5cafc138a38a9592914e789e1159159e1
runtime/source changes = 0
main merge / deploy / remote push = 0 / 0 / 0
```

The corrected M12CD implementation/final-local distinction is preserved. The M12CD source ZIP
passed the frozen SHA and `89/89` manifest integrity check before model execution.

## Generation

```text
generation id = 20260916-uskr22-m12ce-20260916T080425Z-96a562d5cafc
model / effort = gpt-5.6-sol / xhigh
planned / started / completed / usable calls = 16 / 8 / 8 / 8
Fundamental Core accepted = 14
Stage-2 raw contract accepted = 9
Stage-2 materialized and semantically accepted = 6
raw maturity rows observed = 42
accepted materialized maturity rows = 27
```

US Fundamental Core calls 1-5 all passed exact subject identity and exact-ref validation. US
Stage-2 calls 6-7 passed raw contract, deterministic materialization, and semantic validation.
Call 8 produced a schema-valid, exact-ref-valid raw output for MU, RXRX, and SKHY, then failed
closed during deterministic materialization.

## Hard Failure

```text
ordinal = 8
market / stage / batch = US / PRICE_TIMING / 3
batch subjects = MU / RXRX / SKHY
ticker / row = SKHY / driver_maturity[2]
error = stage2_materialization_no_concrete_owned_date:SKHY:2
phase = after raw contract acceptance, before typed materialization
raw output SHA-256 = 6c8e80898904b44a710c00fdb3d918bf00a6edf757f1e2cc987d8d2fcb79455f
```

The row evaluated the quality limitation of the latest financial data and cited only
`canonical:financial_quality:latest`. That ref is ticker-local and canonical, but its source
`as_of` is the symbolic token `latest`; its deterministic date catalog is empty. The row's
`what_remains_unproven` also cited `canonical:earnings:latest`, which is likewise symbolic, but
that nested field is not part of the frozen scalar owner set. No concrete same-row owned date
exists, so the M12CD materializer correctly refused assessment-date, current-date, or global-date
fallback.

Across the 42 raw maturity rows, 39 had one concrete date, two had multiple concrete dates, and
one was symbolic-only. Raw model-authored `as_of`, future dates, unknown refs, cross-ticker refs,
and exact-ref violations were all zero. The harness's raw aggregate no-concrete counter remained
zero because the exception occurred before its final aggregate update; the immutable failure
record and row audit establish the actual failure count as one.

## Frozen Regressions

GOOGL remained representable as independent axes: overall BUY, pre-confirmation true, new-buyer
WAIT, holder HOLDABLE, and timing UNFAVORABLE. The fresh SNDK/TSLA/TSM Stage-2 batch and fresh
`010120` calls were not run after the first hard failure; their frozen offline regressions remain
passing, and the historical invalid `010120` fixture remains rejected.

```text
focused = 198 passed, 1 skipped
full pytest = 4064 passed, 63 skipped, 2 existing warnings
Treasury = 69 passed
Kiwoom local = 32 passed
Ruff = PASS
git diff --check = PASS
```

## Safety

```text
raw model-authored maturity as_of = 0
retry / wrapper retry / fallback / judge = 0 / 0 / 0 / 0
repair / schema repair / candidate repair = 0 / 0 / 0
selective rerun / per-ticker retry / hotfix = 0 / 0 / 0
output stitch / prior-output reuse = 0 / 0
production DB / warning / notification mutations = 0 / 0 / 0
production sends / scheduler mutations / resumes = 0 / 0 / 0
main merges / deployments / remote pushes = 0 / 0 / 0
```

## Next Scope

M12CE is terminal and must not be resumed or stitched. The next task must be a separately
authorized bounded architecture review of symbolic-only maturity provenance ownership. It must
not introduce assessment/system/global date fallbacks, ticker/date exceptions, same-generation
retry, or validator weakening. No deployment or message-model readiness is granted.
