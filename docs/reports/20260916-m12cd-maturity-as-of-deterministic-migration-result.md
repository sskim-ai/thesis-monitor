# M12CD Deterministic Maturity `as_of` Migration Result

## Result

```text
M12CD_RESULT = MATURITY_AS_OF_DETERMINISTIC_OWNERSHIP_MIGRATION_OFFLINE_PASS
MESSAGE_MODEL_CONTRACT_READINESS = NOT_REPROVEN_MODEL_CALL_REQUIRED
DEPLOYMENT_READINESS = NO_BY_PHASE_BOUNDARY
NEXT_SCOPE = M12CE_NEW_FULL22_REPROOF_UNDER_FROZEN_DETERMINISTIC_AS_OF_CONTRACT
```

M12CD removes model authorship of `driver_maturity[].as_of` at the Stage-2 model boundary and
materializes the internal required field from ticker-local, same-row cited canonical evidence.
No model call, production mutation, send, scheduler change, main merge, deploy, or remote push
occurred.

## Repository

```text
branch = codex/20260916-m12cd-maturity-as-of-deterministic-migration
base = b26022916f0bd2dea58dde71a9fddb41a844a9d4
origin/main observed = 9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479
work-instruction commit = dbe40f4c9b5564660dab509d6534c8f9acbeb1b2
implementation commit = 9a9bda729afcb0777d7228ee7151d31f0b2f84f8
main merge / deploy / remote push = 0 / 0 / 0
```

The supplied M12CC bundle passed SHA-256 and manifest verification: `114/114` artifacts, `115`
ZIP entries, and zero missing, extra, hash, or size mismatches. Its SHA-256 is
`7b4a09d651fc47d400831ddff603d4ce8b8cd2310674a31e07cd0b2b2fa728fd`.

## Contract

The model-facing contract is now `v2-accepted-stage2-model-output-v2`. It does not expose or
require `driver_maturity[].as_of`. The internal candidate contract remains
`v2-accepted-production-output-v1`, where `as_of` is still required for compatibility.

The normalization contract is `stage2-maturity-as-of-deterministic-v1`:

```text
semantics = LATEST_KNOWN_CONCRETE_SAME_ROW_PROVENANCE_DATE
aggregation = MAX_CONCRETE_OWNED_DATES
owner = materialize_accepted_v2_stage2_output
```

The materializer uses only concrete dates owned by refs cited in the same maturity row and visible
to the same ticker. It rejects model-emitted dates, unknown or cross-ticker refs, no-concrete-owner
rows, future dates, and post-materialization tampering. It has no assessment-date, current-date,
global-latest, ticker, or date fallback. The existing hard same-row validator remains active.

## Historical Compatibility

The authoritative historical set contains 20 candidates and 62 maturity rows:

```text
single concrete date rows = 37
multiple concrete date rows = 25
symbolic-only rows = 0
symbolic plus concrete rows = 2
old value equals deterministic MAX = 60 / 62
old value differs = 2 / 62
```

The two differences are WULF and the designated invalid historical `010120` output. WULF moves
from `2026-09-14` to the same-row latest concrete date `2026-09-15`; only candidate and accepted
plan hashes change. The immutable `010120` source still fails the old same-row validator because
it emitted `2026-09-15` for a ref owning `2026-08-12`; an ephemeral new-contract copy safely
materializes `2026-08-12`.

Across all rows:

```text
accepted-plan semantic changes = 0
renderer changes = 0
continuity churn events = 0
candidate hash changes = 2
accepted-plan hash changes = 2
historical source bytes modified = 0
historical bad output reinterpreted = 0
```

The hash impact is `HASH_CHANGE_EXPECTED_BUT_SEMANTICALLY_NEUTRAL`. Old artifacts remain readable
under their existing internal contract and are not silently relabeled as the new model contract.

## Schema Guard

Seven historical Stage-2 batches were measured. The largest model-facing schema shrank from
`60,934` to `60,207` bytes, and the largest combined prompt plus schema shrank from `235,225` to
`234,298` bytes. `oneOf`, `anyOf`, and total branch maxima remain `0`, `5`, and `10`; no ref/date
cross product or ticker-specific schema branch was added. The post-migration schema contains zero
model-facing `as_of` properties and remains strict with `additionalProperties=false`.

## Fixtures And Regression

Eight positive migration fixtures pass. Ten hard-negative fixtures are rejected as expected, and
two semantic negative controls pass their expected invariant. Historical candidates materialize
and validate `20/20`; maturity atomic identity is `20/20`. GOOGL pre-confirmation,
SNDK/TSLA/TSM frozen-core scope, exact-ref, typed contract, maturity polarity, persistence,
Treasury, and local Kiwoom regressions pass.

```text
focused pytest = 188 passed, 1 skipped
full pytest = 4064 passed, 63 skipped, 2 existing warnings
Treasury focused = 69 passed
Kiwoom focused = 32 passed
Ruff = PASS
git diff --check = PASS
```

The Kiwoom gateway remains unconfigured. Authorized capability is read-only and live
read/order/modify/cancel counts are `0/0/0/0`.

## Operating Safety

```text
planned / started / completed / usable model calls = 0 / 0 / 0 / 0
retry / fallback / judge / repair / selective / per-ticker retry = 0 / 0 / 0 / 0 / 0 / 0
production DB mutations / sends = 0 / 0
scheduler mutations / resumes = 0 / 0
main merges / deployments / remote pushes = 0 / 0 / 0
```

## Final Gate

The deterministic migration is complete offline, but the changed model-facing contract has not
been exercised by a model. M12CE must start a wholly new US14/KR8 Full22 generation from call 1
with no prior-output reuse, stitching, retry, fallback, judge, repair, or selective rerun. A clean
M12CE result remains a proof gate and does not authorize deployment.
