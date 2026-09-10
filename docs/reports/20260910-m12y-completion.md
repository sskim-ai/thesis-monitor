# M12Y Leverage Target, Business Delta, and Contrastive Exclusion Completion

Date: 2026-09-10 KST

## Repository

- Branch: `codex/20260910-sol-leverage-target-delta-m12y`
- Base: `0651fe2387049c27b81e273260b99e8cfe7e9b5d`
- Work instruction: `68d00f9d413565a44ddb3e3306f6cfe036ce85c7`
- Root-cause freeze: `8295f0db873148c74383e8137964673d9e204fbc`
- Implementation/runtime identity: `ab4da46266299b3ac1b2c32cc10e20a15036f1f2`
- Report commit: `PENDING_FINAL_COMMIT`
- Production merge/deploy: `0/0`

## Contract Changes

The shared financial-framework classifier now recognizes bounded contrastive exclusions such as
`X instead of Y` while retaining fail-closed handling for conditionals, contradictions, double
negatives, cross-field application, and material-anchor misuse. Exact FIC-FIN-08 offline replay
passed with no source-output modification. Positive and negative exclusion fixtures recorded zero
false accepts and zero false rejects.

FIC-FIN-05 was frozen at `BUY 4.0 / SELL 6.0`. The source establishes current resilience pressure
through complete debt and thin cash, while unknown refinancing terms and stable operating profit
cap stronger negative strength. No leverage prompt or market-expectation contract changed.

One generic Stage 1 paragraph separates `business_thesis_change` from absolute quality. It requires
supplied prior or baseline change evidence for `STRENGTHENED` or `WEAKENED`; an absolute current
state alone maps to `UNCHANGED`.

## Canary Result

- Generation: `20260910-m12y-fictional-20260910T043154Z-2761aab01862`
- Source lock: `725ed6a67ab441a9b16904702c21ebe0df3f8c86fc606e296b24a5891b5fe01d`
- Runtime: `gpt-5.6-sol`, `xhigh`, 1800-second fixed timeout
- Planned: 8 fictional subjects, 2 contexts, 3 repetitions, 6 calls
- Completed: 1/6 calls, 4 rows, 4 schema-valid outputs
- Transport: PASS in 445.399 seconds, 0 timeout, 0 retry, 0 orphan
- Unattempted: run-1 context-02 and all run-2/run-3 calls

Run-1 context-01 stopped the whole generation. FIC-FIN-01 emitted `BUY 6.0 / SELL 4.0`, below the
frozen exact target `BUY 6.5 / SELL 3.5`. FIC-FIN-02 and FIC-FIN-04 matched their frozen targets.
FIC-FIN-05 and FIC-FIN-08 were not reached, so their full-canary acceptance remains unmeasured.

The business-delta validator also marked FIC-FIN-01, FIC-FIN-02, and FIC-FIN-03 as failures, but
forensic replay shows these are validator false rejects. The audit compared alias-resolved
canonical references from the candidate with an alias-keyed source context, producing empty linked
evidence. The untouched raw outputs cite explicit comparable improvement, lower comparable OCF,
and a recent operating rebound respectively. Model business-delta semantic violations after raw
alias replay are therefore zero; validator false rejects are three.

No selective rerun, hotfix, fallback model, candidate modification, timeout change, or generation
stitching occurred.

## Validation

- Focused local: 217 passed
- Full local: 3293 passed, 2 warnings
- Ruff: PASS
- `git diff --check`: PASS
- Hosted CI run 34437248164: 3288 passed, 5 known portability failures, 0 new M12Y failures

Hosted CI is not reported as PASS. The five remaining failures are the existing shallow Git-object
and local-result-ZIP portability backlog.

## Safety

- Real issuer/provider/judge calls: 0
- Production DB, assessment, warning, notification, and send mutations: 0
- Main merge/deploy: 0/0
- Scheduler mutation/resume: 0/0
- Approved schedules observed paused at start/end: 8/8

## Decision

`M12Y_STATUS = PARTIAL_STOPPED`

`CONTRASTIVE_EXCLUSION_REPAIR = PASS_OFFLINE_FULL_CANARY_NOT_REACHED`

`FIC_FIN_01_EXACT_TARGET = FAIL_6_0_VS_FROZEN_6_5`

`BUSINESS_DELTA_VALIDATOR = FAIL_ALIAS_RESOLUTION_GAP`

`FRESH_REAL_PROOF_READINESS = NOT_READY`

`PRODUCTION_READINESS = NOT_READY`

`NEXT_SCOPE = M12Y_DELTA_AUDIT_ALIAS_RESOLUTION_AND_POSITIVE_BUCKET_STABILITY_REPAIR`

The next work must first repair the validator's canonical-ref to alias-context join and replay the
preserved output offline. It must then review the FIC-FIN-01 6.0 versus 6.5 stability boundary before
authorizing any new generation.
