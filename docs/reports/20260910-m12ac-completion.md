# M12AC Financial Framework Scope and Threshold-Zone Completion

Date: 2026-09-10 KST

## Result

- Status: `M12AC_PARTIAL`
- Fresh real proof readiness: `NOT_READY_OTHER`
- Production readiness: `NOT_READY`
- Next scope: `BOUNDED_M12AC_HARD_FAILURE_REPAIR`
- Production behavior change: `0`

## Repository

- Branch: `codex/20260910-financial-framework-threshold-zone-m12ac`
- M12AB base: `f22c3cef615c665150fe5e92b45e185345782d1c`
- Work-instruction commit: `b44dd2c4b81b6145a2f26b231a72d11312d70a27`
- Architecture commit: `29d0aebc2d777488471c0b7db5d49111fcf8af82`
- Frozen model-call implementation: `6d4f8cfd4d8677e351cf9c0cbec3c250c9680e64`
- Report commit: `f8cade9fc51f9df902778700c8396d7436af1ba9`
- M12AB bundle SHA-256: `2ffe92275f7ea7b342669349fd4b2713b4c05611261bf33a33438c9220407926`
- M12AB indexed payloads: `192`; missing/extra/hash/size mismatch: `0/0/0/0`

## Frozen Experiment

- Generation: `20260910-m12ac-fictional-20260910T114423Z-c9fd32f80752`
- Source lock: `fc6d6e1943063f4437693913dabda32fa94a4942fcca0eb438674a159bd00b7e`
- Model/effort: `gpt-5.6-sol / xhigh`
- Topology: 8 fictional subjects, 2 contexts, 3 repetitions
- Calls: `6/6`; parsed/schema outputs: `24/24`
- Timeout/capacity/CLI retry/wrapper retry/orphan: `0/0/0/0/0`
- Real issuer/provider/judge calls: `0/0/0`

An earlier prepared generation was discarded before spawn because the reused runner expected a
legacy gate filename. It made zero model calls. The adapter was fixed and fully revalidated before
the frozen generation above was created.

## Scope Regression

FIC-FIN-08 passed in repetitions 1 and 2. In repetition 3 the model wrote:

> 보험사이므로 산업회사식 순부채·운전자본 틀이 아니라 인수 규율과 규제자본으로 판단한다.

This is a legitimate contrastive replacement, but the bounded parser did not accept the noun
boundary between the forbidden framework and `아니라`. It emitted two framework-level false
rejects: `net_debt_claim_without_complete_net_debt_evidence` and
`financial_sector_generic_reasoning`.

- Application-scope false rejects: `2`
- Application-scope false accepts: `0`
- Actual financial-sector industrial-framework misuse: `0`
- Objective-semantic hard failures: `2`
- Result-driven validator changes or model reruns: `0`

## Threshold Zones

FIC-FIN-05 was stable across all repetitions:

- Raw: `SELL 4.0:6.0 NOT_HOLD` x3
- Zone: `NEGATIVE_THRESHOLD_ZONE` x3
- Raw unique count: `1`; zone unique count: `1`

FIC-FIN-03 crossed the chosen deterministic boundary:

- Raw: `HOLD 5.0:5.0 NEUTRAL`, then `HOLD 5.5:4.5 BUY_LEAN` x2
- Zone: `NEUTRAL`, then `POSITIVE_THRESHOLD_ZONE` x2

Across eight subjects, raw formal stability was `7/8` and threshold-zone stability was `7/8`.
The architecture therefore did not absorb every observed adjacent HOLD variation.

## Other Stability

- New-buyer stance variance subjects: `0`
- Holder stance variance subjects: `1` (`FIC-FIN-05`: REDUCE/REVIEW/REDUCE)
- Directional-confidence variance subjects: `1` (`FIC-FIN-06`: LOW/MEDIUM/MEDIUM)
- Business-delta contract violations: `0`
- Invalid financial references: `0`
- Grounding failures: `0`

## Validation

- Local focused: `251 passed`
- Local full: `3366 passed`, 2 warnings
- M12AC target after reporting-only closeout fix: `25 passed`
- Ruff: `PASS`
- `git diff --check`: `PASS`
- Hosted CI at frozen implementation: `3360 passed`, 1 skipped, 5 known portability failures
- New M12AC hosted-CI failures: `0`

The post-canary code edit was limited to report generation: correcting a balance unique-count
lookup, distinguishing false rejects from actual misuse, and normalizing the completion stop label.
It did not alter frozen source, prompt, schema, validator behavior, threshold mapping, or outputs.

## Operating Safety

- Production sends/DB mutations/monitoring registrations/warning mutations: `0/0/0/0`
- Main merges/deployments: `0/0`
- Scheduler mutations/automatic resume: `0/0`
- Observed paused schedules at start/end: `8/8`

## Decision

M12AC cannot advance to a fresh-real financial-context proof. The bounded next repair should:

1. Recognize sector-valid Korean contrastive replacement when a bounded noun such as `틀` appears
   between the coordinated industrial framework and the exclusion marker.
2. Preserve fail-closed behavior for true industrial-framework use and ambiguous assertions.
3. Review the `NEUTRAL` versus `POSITIVE_THRESHOLD_ZONE` boundary separately, without majority
   voting, averaging, evidence-count scoring, raw-output rewriting, or ticker-specific rules.
4. Use a new generation only after the repair and exact validation are frozen.
