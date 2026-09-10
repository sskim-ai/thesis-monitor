# M12AB Completion Report

Date: 2026-09-10 KST

## Decision

- Phase status: `M12AB_PARTIAL`
- Fresh real proof readiness: `NOT_READY`
- Production readiness: `NOT_READY`
- Next scope: `FINANCIAL_SECTOR_EXCLUSION_VALIDATOR_REGRESSION_REPAIR_GPT56_SOL`
- Selective rerun or hotfix after generation start: `0`

## Repository

- Branch: `codex/20260910-leverage-hold-sell-boundary-m12ab`
- Base: `95addf0a6a484e7ea307a7b8cb63c175e71332e2`
- Work-instruction commit: `96377fedd6f575f10b97a30db564fa71cde8e766`
- Architecture freeze commit: `6436227b4bef7b61f9afca2970852101bcba4df2`
- Implementation commit: `e59431d741de38f89109c00af5ce5a7ce767bb14`

## Architecture

M12AA comparator normalization was corrected without modifying the authoritative M12AA ZIP:

- FIC-FIN-05 minimum SELL: `2`
- FIC-FIN-05 HOLD 4.5:5.5 SELL_LEAN: `1`
- Out of band: `0`
- Stable preference: `MIXED_BOUNDARY`

Option F was selected exactly once. The AI owns raw core interpretation and explicit adjacent-boundary
declaration. A versioned experimental resolver may only choose the declared endpoint closer to 5.0.
Raw and resolved core states remain separately auditable. No majority vote, averaging, fixed score,
evidence-count rule, or ticker-specific exception was added.

## Validation Gate

- Focused tests: `246 passed`
- Full local tests: `3341 passed, 2 warnings`
- Ruff: `PASS`
- Diff check: `PASS`
- Exact-head CI: `3335 passed, 1 skipped, 5 historical portability failures`
- New M12AB CI failures: `0`
- Model target: `gpt-5.6-sol / xhigh`
- Frozen source hash: `1018dd3213e9514f2ebe38f2b0223a3e3a88d096bbef31e2edf90d30edbe0adb`

## Canary Result

Generation: `20260910-m12ab-fictional-20260910T092640Z-741ca9a40148`

- Requested plan: 8 fictional subjects, 2 contexts, 3 repetitions, 6 calls, 24 rows
- Completed: `2/6 calls`, `8/24 rows`
- Transport success: `2/2`
- Parsed/schema-valid observed rows: `8/8`
- Wrapper retries, timeouts, capacity failures, orphan processes: `0`
- Observed schema failures: `0`
- Rows not run after the mandatory stop: `16`

Run 1 context 1 passed 4/4. Run 1 context 2 returned a complete, schema-valid model output. Its
FIC-FIN-08 sector sentence explicitly said to use underwriting discipline and regulatory capital
*instead of* industrial-company net debt and working-capital frameworks. The existing validator
misclassified that legitimate exclusion as two hard failures:

- `net_debt_claim_without_complete_net_debt_evidence`
- `financial_sector_generic_reasoning`

These are validator false rejects, not model financial-sector misuse and not transport or schema
failures. The current runner nevertheless classifies them as objective-semantic hard failures, so the
canary stopped immediately. No selective rerun, prompt adjustment, validator change, or new generation
followed.

## Boundary Observation

FIC-FIN-05 was observed once as raw and resolved `HOLD 4.5:5.5 SELL_LEAN`; it did not declare the
adjacent 4.5:5.5 / 4.0:6.0 boundary in that output. The required three declarations and three resolved
observations therefore remain unmeasured. Stable controls FIC-FIN-01, FIC-FIN-04, and FIC-FIN-07 did
not invent a boundary.

## Safety

- Real issuer/provider/judge calls: `0`
- Production sends and notification writes: `0`
- DB, assessment, warning, registration mutations: `0`
- Main merge and deployment: `0`
- Scheduler mutations and automatic resume: `0`
- Paused schedules at start/end: `8/8`

The experimental architecture remains non-production and is not eligible for real-issuer proof until
the financial-sector legitimate-exclusion validator regression is repaired and a separately approved,
newly frozen generation completes the boundary proof.
