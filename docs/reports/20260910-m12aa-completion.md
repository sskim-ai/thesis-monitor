# M12AA Boundary-Band and Financial-Framework Scope Completion

Date: 2026-09-10 KST

## Repository

- Branch: `codex/20260910-boundary-band-canary-m12aa`
- Base: `e6e4cea878d4af93f44f299ff58791b651cc4afe`
- Work instruction: `6f783fe63a6dc727ffc19fa8d53e7cfcf84b8998`
- Contract freeze: `689624d03c2440d9f6603f2b9e140974b517ea01`
- Implementation: `d29b96a21ff2146bb1a446a2a60ce8e076f5fce9`
- Report commit: `20182366f704d0ad178d22e8b5816462679c138a`
- Production merge/deploy: `0/0`

## Contract Result

M12AA separates runtime, schema, and objective-semantic hard failures from calibration, stance,
confidence, and message-quality observations. Calibration variation no longer stops a generation.
Production Directional thresholds, half-step increments, HOLD lean, conservative tie-break,
financial source selection, Daily Delta, Price-Timing, and renderer ownership remain unchanged.

Financial framework references now use one shared field/evidence-aware role classifier. It
distinguishes asserted or applied frameworks from explicit non-application, contrastive
replacement, context-only mention, contradictory mixed use, and unresolved material use. The net
debt and financial-sector validators consume the same roles. The exact preserved FIC-FIN-08
insurance sentence now passes as contrastive replacement, while actual cross-field application,
contradiction, or unresolved material application still fails closed.

## Full Sol Canary

- Generation: `20260910-m12aa-fictional-20260910T065817Z-ba878001b3d4`
- Source lock: `bc882f77f32f2fe9a2448d71cf7ad30147a49bcfb2588a81d4013d35d7a2e37a`
- Runtime: `gpt-5.6-sol`, `xhigh`, fixed 1800-second timeout
- Scope: 8 fictional subjects, 2 contexts, 3 repetitions
- Calls: 6/6 PASS
- Rows: 24/24 schema PASS
- Timeout/retry/capacity/orphan/fallback: `0/0/0/0/0`
- Runtime median/max: `455.061229 / 540.919253` seconds
- Runtime, schema, objective-semantic hard failures: `0/0/0`
- Invalid evidence refs/grounding failures: `0/0`
- Financial exclusion false reject/false accept/true misuse: `0/0/0`
- Business-delta alias and directional failures: `0`

FIC-FIN-01, FIC-FIN-02, and FIC-FIN-04 were stable at `6.5:3.5`, `4.5:5.5`, and
`5.0:5.0`. FIC-FIN-05 produced `SELL 4.0:6.0`, `HOLD 4.5:5.5 SELL_LEAN`, and
`SELL 4.0:6.0`. FIC-FIN-08 kept `HOLD 5.0:5.0` but its holder stance varied between
`REVIEW` and `HOLDABLE`. No opposite-direction reversal occurred.

## Frozen-Band Integrity

The FIC-FIN-05 frozen minimum-SELL tuple encoded `lean=null`, while the schema-valid SELL outputs
use `hold_lean=NOT_HOLD`. The exact tuple comparator therefore classified the two `SELL 4.0:6.0`
rows as `OUT_OF_BAND_OTHER`; only the `HOLD 4.5:5.5 SELL_LEAN` row matched the frozen band.

This is retained as an exact frozen-contract shape mismatch. The band, target, outputs, and
interpretation were not changed after generation, and the two rows were not reclassified into a
PASS. M12AA therefore completes the requested observation program but does not establish a stable
FIC-FIN-05 preference.

## Stability and Readiness

- Formal stability: 6 stable, 1 boundary uncertainty, 1 unstable
- New-buyer stance variance subjects: 1
- Holder stance variance subjects: 2
- Confidence variance subjects: 1
- Business-delta variance subjects: 0
- P0 open: 0
- P1 open: 2

P1 items are the frozen minimum-SELL `lean` shape mismatch and the material FIC-FIN-05/stance
instability that remains after the complete three-repetition sample. Neither was hotfixed or
majority-voted.

## Validation

- Focused local suite: PASS
- Full local pytest: PASS
- Ruff: PASS
- `git diff --check`: PASS
- Hosted CI run `34447250960`: 3314 passed, 1 skipped, 5 failed
- New M12AA hosted-CI failures: 0

The five hosted failures are the known historical shallow-Git/local-result-ZIP portability cases.
Hosted CI is not reported as fully green.

## Safety

- Real issuer/provider/judge calls: 0
- Production DB, assessment, warning, notification, and send mutations: 0
- Main merge/deploy: 0/0
- Scheduler mutation/automatic resume: 0/0
- Approved schedules observed paused: 8

## Decision

`M12AA_STATUS = M12AA_COMPLETE`

`FINANCIAL_FRAMEWORK_ROLE_CLASSIFIER = PASS`

`FULL_SOL_FICTIONAL_CANARY = 6_OF_6_CALLS_AND_24_OF_24_ROWS_COMPLETE`

`FRESH_REAL_PROOF_READINESS = NOT_READY`

`PRODUCTION_READINESS = NOT_READY`

`NEXT_SCOPE = BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT56_SOL`

No additional model call, fresh-real proof, production integration, monitoring resume, or target
reinterpretation is authorized by this completion.
