# thesis-monitor — 2026-09-02 KR Natural Live Post-Close Review

## Purpose
Read-only review of the ordinary KR close cycle. Do not repair during observation.

Prove:
1. correct KR session/cutoff cohort
2. natural scheduler + Codex runtime-state path
3. source/technical readiness
4. model → candidate → adjudication → accepted → renderer
5. decision consistency versus prior accepted state/evidence fingerprints
6. message quality, valuation, Price Structure, numeric provenance
7. exactly-once delivery
8. next bounded repair plan

## Reference KR cohort
000660, 003690, 005490, 005930, 010120, 012450, 047810, 086280.
Reference count 8. Use actual immutable cutoff cohort if different.
If all 8 eligible: expected 1 market + 8 stock = 9 messages.

## Hard read-only rules
No manual source-monitor/primary/backup/dispatcher run.
No resend/requeue.
No production DB/packet/claim/accepted/assessment mutation.
No repair/merge/scheduler change during proof.
Production Assist remains OFF.

Required:
MANUAL_KR_PRODUCTION_TRIGGER = 0
MANUAL_KR_PRODUCTION_SEND = 0
KR_PRODUCTION_STATE_MUTATION = 0
KR_REPAIR_DURING_REVIEW = 0

## A. Exact natural run / lineage
Capture:
- source-monitor / primary / backup / dispatcher runs
- run ID / packet ID / claim ID / owner
- evidence cutoff / frozen cohort time / delivery time
- origin/main / operating / runtime SHA
- V2 feature selector
- Codex runtime-state contract/version

Require:
KR_CANONICAL_SESSION_DATE = 2026-09-02
KR_RUNTIME_LINEAGE = PASS/FAIL
MULTIPLE_KR_PRODUCERS_OWNED_PACKET = 0
KR_UNOWNED_RETRY = 0
KR_PACKET_COHORT_MUTATED_AFTER_CUTOFF = 0

## B. Source / market / supply
For each cutoff-eligible ticker:
- close / price_as_of
- supply available/as_of
- earnings checkpoint
- valuation availability
- event/thesis evidence
- OHLCV acquisition

Set KR_SOURCE_READY_COUNT.

Audit KR market message:
- KOSPI/KOSDAQ/KOSPI200/KOSDAQ150 where configured
- breadth/participation
- sector/industry selection
- market flows
- source/as_of/semantic type for every rendered number

Set KR_MARKET_MESSAGE_STATUS.

Supply is positioning only.
SUPPLY_ALONE_CHANGED_BUSINESS_DECISION = 0.

## C. Packet-owned technical context
For all cutoff-eligible stocks:
- technical_context_id
- aggregate state
- D/W/M state
- safe and blocked feature counts
- source/fingerprint

Set:
KR_TECHNICAL_FULL_COUNT
KR_TECHNICAL_PARTIAL_SAFE_COUNT
KR_TECHNICAL_UNAVAILABLE_COUNT
KR_TECHNICAL_INVALID_COUNT

Require:
ONE_KR_TECHNICAL_FAILURE_BLOCKS_COHORT = 0
KR_DECISION_STAGE_LOCAL_OHLCV_HTTP = 0

## D. Natural Codex runtime proof
Capture:
- runtime-state preflight
- state-home resolution
- app-server initialization
- model call reached

Require:
KR_CODEX_RUNTIME_STATE_PREFLIGHT = PASS
KR_CODEX_APP_SERVER_INITIALIZATION = PASS

## E. V2 context / candidate / validation
Per ticker:
- prepare_context
- model/batch membership
- candidate BUY/HOLD/SELL
- confidence/evidence maturity
- pricing requirement/asymmetry
- candidate validation

Set:
KR_V2_CONTEXT_READY_COUNT
KR_V2_MODEL_CALL_REACHED
KR_V2_MODEL_COVERED_COUNT
KR_V2_CANDIDATE_GENERATED_COUNT
KR_CANDIDATE_VALIDATION_PASS_COUNT
KR_PHANTOM_NUMERIC_ERRORS

Validator controls:
- 047810: KF-21 / FA-50 phantom numeric = 0
- 010120/012450: large numeric provenance PASS
- 000660: valuation-quality guard remains PASS
- 005930: unsupported risk/reward guard remains PASS
Do not weaken validators.

## F. Adjudication / accepted
Per ticker:
- prior accepted decision
- fresh candidate
- material disagreement?
- adjudication required/invoked/completed
- accepted decision
- accepted evidence fingerprint

Set:
KR_ADJUDICATION_REQUIRED_COUNT
KR_ADJUDICATION_COMPLETED_COUNT
KR_REQUIRED_ADJUDICATION_MISSING = 0
KR_ACCEPTED_READY_COUNT
KR_RAW_CANDIDATE_USED_AS_FINAL = 0

Record actual BUY/HOLD/SELL/NOT_READY distribution.

## G. Decision-consistency audit — mandatory
Because US run-51 produced different replay distributions, compare for each KR ticker:
- prior evidence fingerprint
- current evidence fingerprint
- prior accepted
- current candidate
- current accepted

Classify evidence:
EVIDENCE_CHANGED_MATERIALLY
EVIDENCE_CHANGED_NONMATERIALLY
EVIDENCE_UNCHANGED
FINGERPRINT_NOT_COMPARABLE

For every accepted decision change provide:
ticker / old / new / exact material evidence delta / adjudication / why value-relevant.

Require:
KR_DECISION_CHANGE_WITHOUT_MATERIAL_EVIDENCE_OR_ADJUDICATION = 0

If evidence unchanged but candidate changes:
classify MODEL_STOCHASTIC_CANDIDATE_VARIANCE.
Do not call it a business-thesis change.

Set:
KR_UNEXPLAINED_ACCEPTED_DECISION_DRIFT = 0/NONZERO

Also separate:
- business thesis
- earnings estimate
- market expectations
- valuation
- price/timing
so BUY→HOLD due price/expectations is not mislabeled as thesis weakening.

## H. Renderer / message quality
Per stock identify:
V2_ACCEPTED_RENDERER / DETERMINISTIC_FALLBACK / LEGACY_V1 / OTHER.

Require explicit top-level:
🧠 AI 분석 판단: BUY/HOLD/SELL

Set:
KR_RENDERER_ROUTE_IDENTIFIED_COUNT
KR_FALLBACK_STOCK_COUNT
KR_EXPLICIT_V2_DECISION_COUNT
ACCEPTED_READY_WITHOUT_EXPLICIT_DECISION = 0

Audit consistency across:
- AI decision
- core judgment
- re-evaluation conditions
- thesis-status/body
- market expectation
- Price Structure
- Valuation
- next checks

Set:
NO_INTERNAL_CONTRADICTION = PASS/FAIL

Classify V2 block vs old thesis-body duplication:
LOW / MODERATE / HIGH.

## I. Pending common disclaimer cleanup inventory
The user has decided to remove:
`※ 분석 분류이며 주문·자동매매·의무 매매 지시가 아닙니다.`

Do NOT patch it during this review.
Record:
- KR occurrence count
- exact renderer/component owner
- whether US/KR share same component

Set:
KR_DISCLAIMER_OCCURRENCE_COUNT
COMMON_DISCLAIMER_OWNER

## J. Price Structure / valuation / language
Price Structure:
- current close
- support/resistance
- weekly/monthly Bollinger if available
- registered price rules
- no invented levels
- in-progress monthly correctly labeled

Set KR_PRICE_STRUCTURE_VALIDATION = PASS/FAIL.

Valuation:
- PER/PBR/fPER/fPBR only where appropriate
- correct period/security/currency basis
- historical percentile semantics
- no denominator reconstruction from unsafe facts

Set KR_VALUATION_SEMANTIC_VALIDATION = PASS/FAIL.

Message quality:
- company/ticker identity
- grammar
- character count
- substantive repeats
- TOO_LONG/GOOD/TOO_SHORT
- re-evaluation conditions GOOD/TOO_GENERIC/UNSUPPORTED

Set KR_IDENTITY_LANGUAGE_QUALITY.

## K. Final validation / delivery
Per message terminal:
PASS / REPAIRED_PASS / REJECTED / FALLBACK.

Set:
KR_FINAL_VALIDATION_PASS_COUNT
KR_FINAL_VALIDATION_REJECT_COUNT

Delivery:
expected / intent / sent / acknowledged / duplicate / orphan / unowned retry.

Require:
KR_EXACTLY_ONCE_DELIVERY = PASS
KR_LIVE_EXACT_PAYLOAD = PASS

Archive sanitized exact KR market + stock messages.

## L. Mandatory per-stock matrix
Columns:
ticker | source_ready | technical | context | model | candidate | candidate_validation | prior_accepted | evidence_delta | adjudication | accepted | renderer | explicit_decision | price_structure | valuation | message_quality | delivery | earliest_failure

Also one separate KR market row.

## M. Natural-live classification
Preferred healthy result if cohort remains 8:
source 8 / context 8 / model reached / candidate 8 / accepted 8 / explicit V2 8 / fallback 0 / delivery 9/9 / exact payload PASS.

Set:
KR_V2_NATURAL_LIVE = PASS / PARTIAL_SAFE / FAIL

## N. Pending user-decided common changes
Do not implement during review. Carry into next bounded repair:
1. Remove common stock-message disclaimer in KR+US.
2. US night futures compact display:
   Daily = open / close / gap% / return%
   Weekly = open / close / weekly%
   Monthly = open / close / monthly%
3. US nominal Treasury curve:
   3Y / 5Y / 10Y / 30Y
   current yield + previous valid observation delta in bp.
4. Replace the current standalone 10Y real-yield user-facing primary block.

These UI changes do not determine KR functional LIVE_PASS.

## O. Next repair class
After evidence is complete choose:
NO_ACTION
FUNCTIONAL_P1_REPAIR
DECISION_CONSISTENCY_REPAIR
MESSAGE_RENDERER_CLEANUP
MARKET_MESSAGE_ENRICHMENT
COMBINED_BOUNDED_REPAIR
ROLLBACK_REVIEW

Do not perform the repair.

## Required reports
Create:
- 20260902-kr-natural-run-identity.md
- 20260902-kr-runtime-lineage.md
- 20260902-kr-scheduler-ownership.md
- 20260902-kr-frozen-cohort.md
- 20260902-kr-source-readiness.md
- 20260902-kr-market-message-proof.md
- 20260902-kr-supply-positioning-proof.md
- 20260902-kr-technical-context.md
- 20260902-kr-codex-runtime-natural-proof.md
- 20260902-kr-v2-candidate-generation.md
- 20260902-kr-candidate-validation.md
- 20260902-kr-adjudication-accepted.md
- 20260902-kr-decision-consistency-audit.md
- 20260902-kr-decision-drift-controls.md
- 20260902-047810-identifier-control.md
- 20260902-000660-valuation-quality-control.md
- 20260902-005930-risk-reward-control.md
- 20260902-010120-012450-numeric-control.md
- 20260902-kr-renderer-route.md
- 20260902-kr-message-block-consistency.md
- 20260902-kr-message-duplication-density.md
- 20260902-kr-price-structure-validation.md
- 20260902-kr-valuation-semantic-validation.md
- 20260902-kr-disclaimer-cleanup-inventory.md
- 20260902-kr-exact-messages.md
- 20260902-kr-delivery-proof.md
- 20260902-kr-live-stage-matrix.md
- 20260902-kr-next-repair-plan.md
- 20260902-kr-natural-live-artifact-index.md

Machine-readable:
- 20260902-kr-live-stage-matrix.json
- 20260902-kr-decisions.json
- 20260902-kr-decision-delta.json
- 20260902-kr-message-quality.json
- 20260902-kr-delivery.json
- 20260902-kr-live-proof.json

## Completion response
Return compactly:
RUN_ID / PACKET_ID / session / runtime SHA
source ready
technical states
model/candidate/adjudication/accepted
8 ticker decisions
BUY/HOLD/SELL distribution
decision changes with evidence delta
unexplained decision drift
message quality/duplication/disclaimer owner
price-structure/valuation validation
delivery/exact payload
P0/P1/P2
KR_V2_NATURAL_LIVE
NEXT_REPAIR_CLASS

## Mandatory completion ZIP
Create:
`20260902-kr-natural-live-postclose-review-and-next-repair-planning-bundle.zip`

Include all reports/JSON and exact sanitized messages.
Exclude recipient IDs, tokens, credentials, account identifiers, secrets, hidden chain-of-thought.

## Final principle
First prove the natural production path and decision ownership.
Then judge message quality.

A changed model candidate is not automatically a changed investment logic.
If evidence is unchanged, call it model variance and verify adjudication controls it.

Do not let already-decided US UI changes contaminate the KR functional live-pass judgment.
