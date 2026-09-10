# M12X Positive Stronger-Bucket Contract Review Completion

Date: 2026-09-10 KST

## Repository

- Branch: `codex/20260910-positive-stronger-bucket-m12x`
- Base: `079213d7ff730c1d9eb60fca3b06b404ff34f0e5`
- Work instruction: `239b799a1361b8ad8168aef2310f03eaf8fc641e`
- Root-cause freeze: `6aa35700448539cde45e440f7082f329a78d9e68`
- Implementation/runtime identity: `7b1407eab18182defc3bafc261064008a65e20c1`
- Production merge/deploy: `0/0`

## Contract Decision

`root_cause = EXACT_FIXTURE_TARGET_OVERCONSTRAINED`.

FIC-FIN-01 contains distinct current operating improvement, reported QTD OCF/cash-conversion
improvement, and net-cash balance-sheet resilience. OCF less PPE is not counted as another
independent support axis. Missing safe valuation and unproven longer-term persistence limit
confidence but do not make exact 6.0 and 6.5 genuinely adjacent. The frozen target is therefore
`BUY 6.5 / SELL 3.5`.

Only the fictional exact target changed. Directional prompt, threshold, increment, HOLD lean,
tie-break, source values, financial context selection, typed projection, and all financial
validators remained unchanged. Fixed score and evidence-count bucket rules remain zero.

## Canary Result

- Generation: `20260910-m12x-fictional-20260910T031958Z-a6c5d77c56d5`
- Source lock: `9b66dd9ac8eca70fc7cb9e7912f575d9014b3430fb725917269837f17136c2a8`
- Runtime: `gpt-5.6-sol`, `xhigh`, 1800-second fixed timeout
- Planned: 8 fictional subjects, 2 contexts, 3 repetitions, 6 calls
- Completed: 2/6 calls, 8 rows, 8 schema-valid outputs
- Transport: 2 success, 0 timeout, 0 wrapper retry, 0 orphan
- Unattempted: run-2 and run-3 context-01/02, 4 calls

Run-1 context-01 passed 4/4. FIC-FIN-01 produced `BUY 6.5 / SELL 3.5` and passed grounding,
financial semantics, ownership, and the corrected target contract.

Run-1 context-02 returned a complete transport-valid output but failed the frozen canary gate:

1. FIC-FIN-05 produced `BUY 4.0 / SELL 6.0`, below the frozen exact BUY target 4.5.
2. FIC-FIN-08 used an explicit insurance exclusion sentence but received
   `net_debt_claim_without_complete_net_debt_evidence` and `financial_sector_generic_reasoning`.

The whole generation stopped immediately. There was no selective rerun, hotfix, timeout change,
fallback model, candidate modification, or generation stitching. Formal stability, core-only
stability, business-delta variance, and holder/new-buyer stance variance are `NOT_MEASURED`.

## Validation

- Focused local: 152 passed
- Full local: 3266 passed, 2 warnings
- Ruff: PASS
- `git diff --check`: PASS
- Hosted CI run 34432634778: 3261 passed, 5 known historical portability failures, 0 new M12X failures

Hosted CI is not reported as PASS. Its five failures are the existing shallow Git-object and
local-result-ZIP portability backlog.

## Safety

- Real issuer model exposure: 0
- Provider fetches: 0
- Judge calls: 0
- Production DB/assessment/warning/queue mutations: 0
- Production sends: 0
- Main merges/deployments: 0
- Scheduler mutations/resume: 0/0
- Approved schedules observed PAUSED at start/end: 8/8

## Decision

`M12X_STATUS = PARTIAL_STOPPED`

`FIC_FIN_01_POSITIVE_STRONGER_BUCKET = PASS_6_5`

`FULL_SOL_FICTIONAL_CANARY = FAIL_IN_RUN_1_CONTEXT_02`

`FRESH_REAL_PROOF_READINESS = NOT_READY`

`PRODUCTION_READINESS = NOT_READY`

`NEXT_SCOPE = SOL_RUNTIME_REGRESSION_REVIEW`

The next work must use preserved outputs to separate FIC-FIN-05 exact-target calibration from the
FIC-FIN-08 exclusion-language validator boundary. It is not authorization for another model call.
