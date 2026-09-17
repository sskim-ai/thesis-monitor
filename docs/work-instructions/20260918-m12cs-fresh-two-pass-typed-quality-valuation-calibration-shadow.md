# Thesis Monitor — M12CS Fresh Two-Pass Typed-Quality / Valuation Calibration Shadow

## 0. Task identity

Work-instruction filename:

`20260918-m12cs-fresh-two-pass-typed-quality-valuation-calibration-shadow.md`

Suggested result bundle:

`thesis-monitor-20260918-m12cs-fresh-two-pass-typed-quality-valuation-calibration-shadow-report.zip`

This is a **fresh shadow execution/proof task** after M12CR-R1.

It is NOT:

- another shadow-policy design task;
- a schema/validator discovery task;
- a prompt retuning task;
- a production Stage-2 integration;
- a production valuation-policy cutover;
- a market/fundamental refresh;
- a per-ticker calibration task;
- a target-label fitting task;
- a deployment/scheduler/notification/broker/persistence task.

The purpose is to execute the already-closed M12CR-R1 contract without changing it.

Production application/runtime/config behavior changes: **0**.

## 1. Exact source state

Verify first.

### M12CR-R1 result

- ZIP SHA-256:
  `8d62d38c7915ddbbf77e30bffa29509e5eaa14684e507a58027da62ce51571a8`
- Artifact manifest:
  89 declared payloads, 89/89 hash/size PASS.
- Completion:
  `M12CR_R1_TYPED_QUALITY_AND_SECURITY_BASIS_OWNERSHIP_CLOSED_READY_FOR_FRESH_TWO_PASS_SHADOW`
- Generation:
  `20260918-m12cr-r1-offline-0e96355ad915`
- Work-instruction commit:
  `45d7a5be1d76b4f7ad4c60994d79b5dbdf5202c3`
- Implementation commit:
  `0e96355ad9151344ee30c7e2bfc92bb70be183ec`

### Frozen analytical input

Use only:

`20260917-m12cm-current-v4-smoke-20260917T062918Z-5c0cb075ce8b`

Population remains the frozen 22-subject calibration population:

US14:
CORZ, CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF

KR8:
000660, 003690, 005490, 005930, 010120, 012450, 047810, 086280

No market refresh. No source enrichment.

## 2. Exact-contract freeze before inference

M12CR-R1 produced the reviewed future contract under:

- `future-contract-draft-source-hashes.json`
- `future-drafts/pass-a/...`
- `future-drafts/pass-b/...`

Before any model call:

1. regenerate/locate the exact future Pass-A and Pass-B drafts from the M12CR-R1 implementation;
2. compare every prompt/schema/context/materializer-relevant hash against the M12CR-R1 report;
3. require exact equality for all frozen contract artifacts;
4. re-run the M12CR-R1 16-schema completeness/parity scan;
5. re-run the M12CR-R1 quality/basis regression suite;
6. re-run target/price leakage preflight.

If any frozen contract hash differs:

- model calls = 0;
- stop as `M12CS_FROZEN_CONTRACT_DRIFT`;
- do not repair inside M12CS.

No prompt/schema/validator/materializer policy edits are authorized.

## 3. Carry forward closed typed ownership

### 3.1 BUSINESS_EVIDENCE_QUALITY

Runtime-owned.

States:
- NONE
- CONFIDENCE_ONLY

It comes only from typed financial/business quality state/reason semantics.

Ref cardinality is not the owner.

Normal verified security identity does not lower business-evidence confidence.

Security/share-basis reason codes are excluded from this layer.

This state is not directional by itself.

### 3.2 SECURITY_VALUATION_BASIS

Runtime-owned.

States:
- RESOLVED
- UNRESOLVED

It gates:
- per-share valuation eligibility;
- fundamental entry option materialization;
- price-resolution availability.

It may support New Buyer WAIT due unresolved price basis.

By itself it cannot:
- downgrade Overall;
- create Holder REVIEW;
- create Holder REDUCE;
- become directional-negative business evidence.

Expected frozen-snapshot unresolved set from the generic projection:

CPNG, SKHY, TSM, WRD, 010120, 012450, 047810

This list is a post-derivation regression assertion only. Do not hardcode it into logic.

### 3.3 DIRECTIONAL_DISCLOSURE_QUALITY

Model-owned only as the narrow M12CR-R1 judgment over explicitly eligible material-disclosure refs.

Ordinary quality refs and security-basis refs are not model-authored.

## 4. Two-pass architecture

Fundamental Core model calls: **0**.

Planned shadow calls:

- Pass A: 8 calls
- Pass B: 8 calls
- Total: 16 calls

Use the same frozen batch topology.

### US batches

1. CORZ / CPNG / CRCL
2. GOOGL / HUT / IBM
3. MU / RXRX / SKHY
4. SNDK / TSLA / TSM
5. WRD / WULF

### KR batches

1. 000660 / 003690 / 005490
2. 005930 / 010120 / 012450
3. 047810 / 086280

## 5. Pass A — price-blind business/archetype/regime judgment

Use the exact M12CR-R1 Pass-A contract.

Model-visible input may contain:

- accepted business/fundamental claims;
- eligible non-price evidence;
- deterministic business-evidence-quality state;
- narrow directional-quality eligible refs;
- generic archetype definitions;
- generic valuation-regime definitions.

It must not contain:

- current price;
- technical/chart/tactical values;
- current valuation level/percentile;
- precomputed entry-price bands;
- preferred entry ranges;
- security valuation basis as business-thesis degradation evidence;
- prior production-AI labels;
- independent-assistant judgments;
- post-freeze comparison material.

### Pass-A model-owned fields

Use the exact 9-or-fewer M12CR-R1 model-owned surface.

Do not reintroduce runtime-owned fields.

The key semantic judgments remain:

- archetype;
- archetype support;
- valuation regime tier;
- tier support;
- narrow directional disclosure-quality judgment;
- bounded rationale fields already frozen by M12CR-R1.

### Pass-A execution

Run 8 calls, one attempt each.

After every call:
- raw contract validation;
- semantic validation;
- same-subject/ref ownership validation;
- no-price/no-technical leak confirmation.

A hard failure stops Pass A immediately.

No repair/rerun.

Pass B cannot start until:

- 8/8 Pass-A calls completed;
- 22/22 subjects accepted;
- complete Pass-A output frozen and hashed.

## 6. Deterministic post-Pass-A materialization

After Pass A freeze, runtime materializes:

- business-evidence-quality state;
- security-valuation-basis state;
- archetype/tier policy option;
- fundamental entry option or exact unresolved reason.

Use M12CP + M12CR-R1 exact policy/materializer contracts.

No model-authored price.

No model-authored valuation refs/status/method.

### Security-basis gate

If `SECURITY_VALUATION_BASIS = UNRESOLVED`:

- unsafe per-share fundamental option must not materialize;
- fundamental price basis remains unresolved;
- no underlying-security per-share metric conversion is inferred;
- Overall and Holder remain unaffected unless separate business/thesis evidence says otherwise.

## 7. Pass B — decision axes / entry timing

Use the exact M12CR-R1 Pass-B contract.

Model-visible input includes:

- frozen original decision evidence;
- frozen Pass-A archetype/tier;
- deterministic business-evidence-quality state;
- deterministic security-valuation-basis state;
- deterministic fundamental option or unresolved reason;
- current price;
- tactical catalog;
- frozen market/timing context;
- generic three-axis policy.

It still must not contain prior human/production-AI target labels.

### Pass-B model-owned fields

Use the exact M12CR-R1 9-or-fewer field surface.

The model owns only genuine judgment fields such as:

- Overall;
- directional balance;
- thesis state / supporting and contradicting claim choices where frozen;
- New Buyer;
- Holder;
- tactical choice where frozen;
- bounded rationale/re-evaluation prose.

The model does not author deterministic entry metadata.

## 8. Required consistency

### 8.1 Long-term Overall

For DURABLE_FRANCHISE / STRUCTURAL_CYCLICAL_LEADER:

current valuation, current price, tactical state, or security-basis unresolved alone cannot be the sole reason for HOLD/SELL.

A downgrade requires material business/thesis/cycle/competitive/earnings/cash-flow evidence.

This does not force BUY.

### 8.2 Execution-dependent growth

Execution, realized economics, margin, cash burn, financial resilience and dilution may affect Overall.

### 8.3 Holder

Valuation-expensive alone cannot create REVIEW.

`BUSINESS_EVIDENCE_QUALITY=CONFIDENCE_ONLY` alone cannot create REVIEW.

`SECURITY_VALUATION_BASIS=UNRESOLVED` alone cannot create REVIEW/REDUCE.

REVIEW/REDUCE requires the frozen structured thesis/execution/material-risk evidence contract.

### 8.4 New Buyer

ATTRACTIVE requires the frozen resolved fundamental-position conditions.

WAIT is valid for any already-authorized structured condition including:

- current price above resolved fundamental entry range;
- fundamental valuation unresolved;
- security valuation basis unresolved;
- tactical timing unfavorable with intact long-term thesis.

AVOID requires material execution/thesis risk under the frozen contract.

No arbitrary current-price percentage discount.

## 9. Runtime entry-range materialization

After Pass B:

- materialize tactical selected candidate from exact catalog;
- combine with deterministic fundamental option using the frozen reviewed rule;
- calculate current-price distance deterministically;
- materialize refs/status/method/runtime fields.

### Fundamental unresolved

- preferred fundamental entry remains unresolved/null;
- tactical support may remain timing/watch context only.

### Fundamental resolved + tactical resolved

Use the existing frozen overlap/no-overlap semantics.

### Fundamental resolved + tactical unresolved

Use the frozen FUNDAMENTAL_ONLY path where authorized.

Model-authored deterministic price/ref/status count must remain 0.

## 10. Failure and execution discipline

Hard execution rules:

- one attempt per call
- retry = 0
- repair model = 0
- schema repair = 0
- judge = 0
- fallback = 0
- selective rerun = 0
- per-ticker rerun = 0
- prior M12CN/M12CQ output reuse = 0
- cross-generation stitching = 0
- post-call hotfix = 0

Use structured stage/exception failure classification only.

Do not classify failures from keyword scans of evidence text.

A hard failure freezes the generation and stops dependent work.

## 11. Fresh generation and call ledger

Create a new generation ID.

Required ledger distinguishes:

- planned
- wrapper attempted
- provider accepted inference
- completed response
- raw-contract accepted
- semantic accepted

Do not call a pre-inference schema rejection an inference.

## 12. PASS requirements

Terminal:

`M12CS_FRESH_TWO_PASS_CALIBRATION_SHADOW_PASS_READY_FOR_CHAT_REVIEW`

requires all of:

### Frozen contract
- exact M12CR-R1 contract hash parity
- 16/16 schema completeness/parity PASS
- missing upstream enforcement = 0
- quality/basis regression replay PASS
- target leak = 0

### Pass A
- 8/8 accepted calls
- 22/22 subjects accepted
- price leak = 0
- technical leak = 0
- target-label leak = 0
- Pass-A freeze before any Pass-B inference

### Deterministic materialization
- 22/22 outcomes
- unsafe security-basis projection = 0
- business/security-quality conflation = 0
- model-authored fundamental price/ref/status = 0

### Pass B
- 8/8 accepted calls
- 22/22 subjects accepted
- Overall/New Buyer/Holder present 22/22
- all policy consistency validators PASS
- runtime entry materialization PASS 22/22

### Final freeze
- all 22 final shadow rows frozen and hashed
- no reference archive semantic access before freeze

Agreement with prior judgments is not a PASS condition.

## 13. Required result analysis before reference reveal

For the frozen M12CS result, report:

- archetype distribution
- valuation-regime distribution
- archetype × tier
- business-quality distribution
- security-valuation-basis distribution
- Overall distribution
- New Buyer distribution
- Holder distribution
- BUY / WAIT / HOLDABLE count
- Holder REVIEW count and structured reason classes
- security-basis-unresolved cases and their New Buyer outcomes
- fundamental resolved/unresolved counts
- WAIT with resolved entry range
- WAIT with unresolved fundamental range
- resolved preferred entry bands/methods
- tactical resolved/unresolved
- data-quality directional-judgment counts

For each resolved WAIT price output include:

- ticker
- current price/as-of
- fundamental method/tier
- preferred low/high
- distance to band
- tactical context
- exact canonical refs

Do not present tactical support alone as fundamental fair value.

## 14. Blind post-freeze comparison

The work package includes a sealed post-freeze reference archive.

Before final M12CS freeze:

- hash verification only;
- do not extract/read;
- do not use it in tests/prompts/validators/thresholds.

After final 22-subject freeze:

open it exactly once and compare descriptively:

1. original M12CM production AI;
2. independent assistant blind judgment;
3. M12CS two-pass shadow.

Report:

- exact three-axis agreement
- Overall agreement
- New Buyer agreement
- Holder agreement
- label distributions
- changes in prior AI conservatism
- BUY/WAIT/HOLDABLE frequency
- Holder REVIEW frequency
- large interpretive disagreements
- resolved WAIT price coverage

Explicitly inspect, descriptively rather than as target fitting:

- large/core/high-business-value cases
- structural cyclicals
- execution-dependent growth names
- security-basis-unresolved names

No model call or contract edit after reference reveal.

## 15. Production integration remains forbidden

Even if PASS:

- production Stage-2 unchanged
- production investment policy unchanged
- production entry-price schema unchanged
- production sends/intents/DB writes = 0
- scheduler changes = 0
- broker read/order/modify/cancel = 0
- main merge = 0
- remote push = 0
- deployment = 0

Return to Chat for review.

## 16. Required artifacts

At minimum:

- `source-base-integrity.json`
- `m12cr-r1-frozen-contract-binding.json`
- `pre-inference-16-schema-reproof.json`
- `quality-basis-regression-reproof.json`
- `target-and-price-leak-proof.json`
- all 8 Pass-A inputs/prompts/schemas/raw outputs/transport logs
- `pass-a-call-ledger.json`
- `pass-a-output-freeze-manifest.json`
- `pass-a-22-subject-classification.json`
- `fundamental-option-materialization-22.json`
- `business-quality-runtime-22.json`
- `security-valuation-basis-runtime-22.json`
- all 8 Pass-B inputs/prompts/schemas/raw outputs/transport logs
- `pass-b-call-ledger.json`
- `pass-b-output-freeze-manifest.json`
- `shadow-22-subject-results.json`
- `runtime-entry-range-materialization-22.json`
- `new-buyer-consistency-results.json`
- `overall-holder-policy-validation.json`
- `entry-range-coverage-and-methods.json`
- `quality-basis-policy-results.json`
- `final-shadow-freeze-manifest.json`
- post-freeze comparison JSON/MD
- test/JUnit/logs
- Ruff / format / diff-check
- `safety-counters.json`
- `complete-blocker-ledger.json`
- `program-completion.json`
- `REPORT.md`
- artifact manifest
- external result ZIP SHA sidecar

## 17. Validation baseline

M12CR-R1 submitted:

- focused: 254 passed
- frozen-contract: 163 passed
- full: 4,375 passed / 63 skipped
- Treasury/KRX: 121 passed
- Ruff: PASS
- Ruff format: PASS
- git diff --check: PASS

No test deletion or skip inflation.

## 18. Terminal states

Use one:

- `M12CS_FRESH_TWO_PASS_CALIBRATION_SHADOW_PASS_READY_FOR_CHAT_REVIEW`
- `M12CS_FROZEN_CONTRACT_DRIFT`
- `M12CS_PASS_A_FAILED`
- `M12CS_DETERMINISTIC_MATERIALIZATION_FAILED`
- `M12CS_PASS_B_FAILED`
- `M12CS_BLINDNESS_OR_TARGET_LEAK_FAILURE`
- `M12CS_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT`

No terminal state authorizes production integration.
