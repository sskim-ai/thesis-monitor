# M12AD Financial Framework Negation and Holder Stability Completion

Date: 2026-09-11 KST

## Result

- Status: `M12AD_PARTIAL`
- Fresh real proof readiness: `NOT_READY`
- Production readiness: `NOT_READY`
- Next scope: `PRIMARY_DIRECTION_BOUNDARY_STABILITY_REVIEW_GPT56_SOL`
- Production behavior change: `0`

## Repository

- Branch: `codex/20260911-financial-framework-negation-holder-stability-m12ad`
- M12AC base: `6fc68f6bb8a7f88b375338cefc357670f617d575`
- Work-instruction commit: `ee61646c5c0e7516bbf318d2c75232bb9f2c60bf`
- Architecture commit: `d09894116a05ce9043f19d9cc0e79f5bd9f9670c`
- Frozen model-call implementation: `c52b852c515e08c5123534810fd33c4768f67060`
- M12AC bundle SHA-256: `2b5dd84efcaf207e31e5fec15521c0879022fdb9fb411fb0b7cd2cedd80801fe`
- M12AC bundle integrity: `PASS`

## Frozen Experiment

- Generation: `20260911-m12ad-fictional-20260910T225211Z-4dc83d2d03b5`
- Source lock: `67f46e42cd933584af58f590f6a012d842dbd4ca276f29be28dcc9264cf08328`
- Model/effort: `gpt-5.6-sol / xhigh`
- Topology: 8 fictional subjects, 2 contexts, 3 repetitions
- Calls: `6/6`; parsed/schema outputs: `24/24`
- Timeout/capacity/CLI retry/wrapper retry/orphan: `0/0/0/0/0`
- Real issuer/provider/judge calls: `0/0/0`

All six calls used the same frozen source packet, prompt, schema, validator, and renderer contract.
There was no selective rerun, hotfix, majority vote, score averaging, or result-driven threshold
change.

## Financial-Framework Negation

The exact M12AC FIC-FIN-08 sentence failed because the replacement judgment predicate
`판단한다` was outside the bounded contrast classifier. M12AD added bounded handling for the
replacement predicates, Korean adnominal negation `아닌`, and replacement particles `으로/로`.

- Exact M12AC reproduction after repair: `PASS`
- Application-scope false rejects: `0`
- Application-scope false accepts: `0`
- Actual financial-sector industrial-framework misuse: `0`
- Contradictory or ambiguous framework use remains hard-failed.

## Holder Contract

Before any model call, FIC-FIN-05's generic target was frozen as `REVIEW`. High debt and thin cash
are material enough to require active review, but debt maturity, refinancing severity, and risk
persistence are unresolved while operating profit remains positive. Those facts do not uniquely
justify an immediate `REDUCE` action.

- Offline holder fixtures: `7/7 PASS`
- FIC-FIN-05 holder output: `REVIEW / REVIEW / REVIEW`
- Holder-stance unstable subjects: `0`
- New-buyer output: `WAIT / WAIT / WAIT`
- Business delta: `UNCHANGED / UNCHANGED / UNCHANGED`

## Decision-Material Stability

The new classifier keeps exact raw state and the legacy formal projection as separate diagnostics.
It treats same-direction half-point movement as calibration variance, while direction, business
delta, new-buyer stance, and holder stance remain material.

FIC-FIN-03 produced `HOLD 5.0:5.0`, `HOLD 5.5:4.5`, and `HOLD 5.0:5.0`. Direction, new-buyer,
and holder decisions stayed HOLD/WAIT/REVIEW, so it is classified as
`CALIBRATION_VARIANCE_SAME_DIRECTION` and is nonblocking.

FIC-FIN-05 produced `SELL 4.0:6.0`, `HOLD 4.5:5.5`, and `HOLD 4.5:5.5`. Its holder contract is
stable, but the primary direction crosses the HOLD/SELL boundary. It is therefore classified as
`PRIMARY_DIRECTION_UNSTABLE` and blocks fresh-real readiness.

- Decision-stable subjects: `6`
- Same-direction calibration variance: `1`
- Primary-direction unstable: `1`
- Business-delta unstable: `0`
- New-buyer unstable: `0`
- Holder unstable: `0`

## Semantic Safety

- Objective-semantic hard failures: `0`
- Invalid financial references: `0`
- Material financial grounding failures: `0`
- Working-capital grounding failures: `0`
- Business-delta contract violations: `0`
- Financial-sector framework leaks: `0`
- Fixed score/evidence-count rules: `0/0`

## Validation

- Local focused: `273 passed`
- Local full: `3388 passed`, 2 warnings
- Ruff: `PASS`
- `git diff --check`: `PASS`
- Hosted CI at frozen implementation: `3382 passed`, 1 skipped, 5 known portability failures
- New M12AD hosted-CI failures: `0`

The hosted failures are the same three historical Git-object lookups and two local-only report ZIP
dependencies already carried by the previous phase. They are not labeled CI PASS.

## Operating Safety

- Production sends/DB mutations/monitoring registrations/warning mutations: `0/0/0/0`
- Main merges/deployments: `0/0`
- Scheduler mutations/automatic resume: `0/0`
- Observed paused schedules at start/end: `8/8`

## Open Issues

- P0: `0`
- P1: `1` - FIC-FIN-05 primary direction crossed SELL/HOLD across identical frozen inputs.
- P2: historical hosted-CI portability remains an explicit backlog and is not reported as PASS.

## Decision

M12AD closes the structural Korean contrastive-negation false reject and the holder REVIEW/REDUCE
ambiguity, but it cannot advance to a fresh-real financial-context proof. The bounded next review
must use the preserved outputs to determine whether the FIC-FIN-05 SELL/HOLD crossing reflects an
underspecified evidence-severity boundary or a remaining generic decision contract gap. It must not
retrofit the finished generation, average balances, use majority voting, add ticker-specific rules,
or initiate another model generation without a separate instruction and approval.
