# M12Z Business-Delta Alias and Balance-Confidence Completion

Date: 2026-09-10 KST

## Repository

- Branch: `codex/20260910-business-delta-alias-resolution-m12z`
- Base: `89bee202be8a4ae2f0eac7ce2fdca1a095c7818e`
- Work instruction: `55bb3e92e7f40455ff547340c7e876b36292e88b`
- Root-cause freeze: `9bcba40e4ef67fa025ff72d9badcbc0bf92da7a7`
- Implementation/runtime identity: `ca63b25894b53f17c4b89f2ecb3dfff79227448c`
- Report commit: `e54d75eec5761f3e1616caceef950a96ed25920d`
- Production merge/deploy: `0/0`

## Offline Contract Result

The business-delta failure was confirmed as a validator identity-join defect:
`CANONICAL_REFS_COMPARED_TO_ALIAS_KEYED_CONTEXT`. The M12Z audit resolves a selected alias or
canonical reference through the per-ticker alias catalog before comparing the selected evidence.
Missing, ambiguous, colliding, and cross-ticker references fail closed.

All four positive and eight negative alias fixtures passed with false reject/accept `0/0`. The
preserved M12Y run-1/context-01 output replayed with all four business deltas accepted and model
semantic violations `0`. The new canary's observed eight rows also had alias-resolution failures,
business-delta contract violations, and unsupported absolute-state-to-delta errors of `0/0/0`.
Formal full-canary success remains unmeasured because the generation stopped after two calls.

The positive-bucket review selected the generic root cause
`PERSISTENCE_LIMIT_PRIORITY_UNDERSPECIFIED`, with secondary
`BALANCE_CONFIDENCE_SEMANTIC_ENTANGLEMENT`. One generic prompt paragraph now separates supplied
directional evidence strength from epistemic confidence. Future durability merely not proven can
lower confidence without automatically lowering current evidence balance; direct evidence against
causality, persistence, reversibility, or validity can create genuine adjacent-bucket ambiguity.
Threshold, half-step, HOLD lean, tie-break direction, source selection, financial validators, and
renderer contracts did not change. Fixed-score and evidence-count bucket rules remain zero.

## Canary Result

- Generation: `20260910-m12z-fictional-20260910T053337Z-5ce67bcf509e`
- Source lock: `0cbd7d68cec8b9edead07b96199b4c3b25c8f35ef2d679662f89d83aaddd6e36`
- Runtime: `gpt-5.6-sol`, `xhigh`, 1800-second fixed timeout
- Planned: 8 fictional subjects, 2 contexts, 3 repetitions, 6 calls
- Completed: 2/6 calls, 8 rows, 8 schema-valid outputs
- Runtime: 2/2 transport PASS, median 419.387 seconds, max 507.663 seconds
- Transport failures: timeout/retry/capacity/orphan/fallback `0/0/0/0/0`
- Unattempted: all run-2 and run-3 calls

Run-1/context-01 passed 4/4. FIC-FIN-01 reproduced the frozen `BUY 6.5 / SELL 3.5`; FIC-FIN-02
and FIC-FIN-04 also matched their frozen targets. This is one observation only, so FIC-FIN-01
three-repetition stability remains `NOT_MEASURED`.

Run-1/context-02 returned a complete transport-valid output but failed postprocessing. FIC-FIN-05
kept business delta `UNCHANGED` yet emitted `BUY 4.5 / SELL 5.5`, below the frozen minimum SELL
target `BUY 4.0 / SELL 6.0`. FIC-FIN-08 used explicit insurance exclusion language but was rejected
as `net_debt_claim_without_complete_net_debt_evidence` and
`financial_sector_generic_reasoning`. These are two separate unresolved semantic boundaries; the
generation stopped immediately and no output was altered.

No selective rerun, whole-generation retry, hotfix, fallback model, candidate modification,
threshold relaxation, timeout change, or generation stitching occurred.

## Validation

- Focused local: 220 passed
- Full local: 3308 passed, 2 warnings
- Ruff: PASS
- `git diff --check`: PASS
- Hosted CI run 34441240996: 3303 passed, 5 known portability failures
- New M12Z hosted-CI failures: 0

The earlier implementation run exposed two new shallow-checkout assertions. They were repaired
before generation by comparing against frozen hashes, then the exact portability SHA was rerun.
The remaining five hosted failures are the pre-existing shallow Git-object and local-result-ZIP
portability backlog; hosted CI is not reported as fully passing.

## Safety

- Real issuer/provider/judge calls: 0
- Production DB, assessment, warning, notification, and send mutations: 0
- Main merge/deploy: 0/0
- Scheduler mutation/resume: 0/0
- Approved schedules observed paused at start/end: 8/8

## Decision

`M12Z_STATUS = PARTIAL_STOPPED`

`DELTA_ALIAS_RESOLUTION = PASS_OFFLINE_AND_OBSERVED_8_OF_8_FULL_PROOF_INCOMPLETE`

`FIC_FIN_01_FROZEN_TARGET = PASS_ONCE_STABILITY_NOT_MEASURED`

`FIC_FIN_05_FROZEN_TARGET = FAIL_4_5_VS_REQUIRED_4_0`

`FIC_FIN_08_CONTRASTIVE_EXCLUSION = FAIL_FULL_CANARY_REGRESSION`

`FRESH_REAL_PROOF_READINESS = NOT_READY`

`PRODUCTION_READINESS = NOT_READY`

`NEXT_SCOPE = LEVERAGE_DIRECTIONAL_CONTRACT_REVIEW_GPT56_SOL`

The next review must start from the preserved M12Z outputs. It should determine why the supplied
complete-debt/thin-cash evidence still produced only a SELL lean for FIC-FIN-05, while separately
classifying the FIC-FIN-08 exclusion failure. It must not rerun this generation, invoke a model,
change the frozen target from the observed output, or resume monitoring without a new instruction.
