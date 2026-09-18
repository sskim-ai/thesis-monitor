# Thesis Monitor — M12CT Fresh Two-Pass Provider-Wire Calibration Shadow

## 0. Task identity

Work-instruction filename:

`20260918-m12ct-fresh-two-pass-provider-wire-calibration-shadow.md`

Suggested result bundle:

`thesis-monitor-20260918-m12ct-fresh-two-pass-provider-wire-calibration-shadow-report.zip`

This is a **fresh execution/proof of the already-closed M12CS-R1 semantic + provider-wire contracts**.

It is NOT:

- another contract-design task;
- a schema discovery task;
- a prompt retuning task;
- an investment-policy redesign;
- a valuation-method redesign;
- a data-quality/security-basis redesign;
- a market/fundamental refresh;
- a production integration/deployment task.

No application/runtime/config source edits are authorized.

Expected code diff from M12CS-R1 implementation: **0**.

## 1. Exact required source state

### M12CS-R1 result

Verify:

- ZIP SHA-256:
  `9724c1f3200d92672f3f6a7f8e4e0cd7c9af55033c07d6fde28845321fddf508`
- Artifact manifest:
  103 declared payloads, 103/103 hash and size PASS.
- Completion:
  `M12CS_R1_PROVIDER_DIALECT_COMPATIBILITY_CLOSED_READY_FOR_FRESH_TWO_PASS_SHADOW`
- Work-instruction commit:
  `392fb847fe2e163cb902addbdd6d51edcef5c967`
- Implementation commit:
  `53c603c6a257b0a093446d5dc1b0977c7f5533fa`

Repository execution head must be exactly:

`53c603c6a257b0a093446d5dc1b0977c7f5533fa`

with clean working tree before inference.

If not exact, stop:

`M12CT_FROZEN_IMPLEMENTATION_DRIFT`

Do not patch or fast-forward inside this task.

## 2. Dual contract freeze

M12CS-R1 produced two independent freeze manifests.

### Semantic contract

Exact file SHA-256:

`46761af244511ae8a2d777fd66c985fbefdb811486320f901e1939e0cbf8f1fe`

The internal semantic schema remains richer and may retain local-only constraints such as `uniqueItems`.

### Provider-wire contract

Exact file SHA-256:

`e325d7c46dba0230e19446430df71da6b4fcff9e23561bf593281ed9afeeb938`

The provider-wire projection must have:

- 16 schemas;
- `uniqueItems = 0`;
- unsupported provider keywords = 0;
- provider dialect PASS 16/16.

Both manifests are binding.

Any mismatch stops before inference:

`M12CT_FROZEN_CONTRACT_DRIFT`

## 3. Frozen analytical population and source input

Use only the immutable M12CM frozen source:

`20260917-m12cm-current-v4-smoke-20260917T062918Z-5c0cb075ce8b`

Population:

US14:
- CORZ
- CPNG
- CRCL
- GOOGL
- HUT
- IBM
- MU
- RXRX
- SKHY
- SNDK
- TSLA
- TSM
- WRD
- WULF

KR8:
- 000660
- 003690
- 005490
- 005930
- 010120
- 012450
- 047810
- 086280

No market refresh.
No source enrichment.
No Fundamental Core model calls.

## 4. Transport/model freeze

The historically provider-accepted M12CQ path and the rejected M12CS path both used:

- `OpenAI Codex v0.153.4`
- model: `gpt-5.6-sol`

M12CT must use model:

`gpt-5.6-sol`

Record the actual Codex/transport version before call 1.

If the resolved model is not exactly `gpt-5.6-sol`, stop:

`M12CT_TRANSPORT_MODEL_DRIFT`

If the Codex/transport version differs from `0.153.4`, do not silently adapt the contract. Record the difference and perform only the already-existing no-network request serialization checks. If exact provider request semantics cannot be proven unchanged, stop before inference:

`M12CT_TRANSPORT_CONFIG_DRIFT`

No model fallback.

## 5. Critical outbound-request proof

Before any provider call, exercise the exact execution path in **no-network/dry serialization mode** for all 16 planned calls.

For each outbound request capture only the locally serialized `response_format` / structured-output schema bytes.

Prove:

1. the schema sent to the provider is the **provider-wire projection**, not the internal semantic schema;
2. its normalized SHA equals the corresponding row in `provider-wire-contract-freeze-manifest.json`;
3. `uniqueItems` count = 0;
4. unsupported provider keyword count = 0;
5. all arrays have valid `items`;
6. root object / strict required / additionalProperties constraints remain valid;
7. provider-documented size limits remain within bounds.

No semantic prompt/output target material is opened by this step.

Required artifact:

`outbound-provider-request-schema-binding-16.json`

If any of 16 fails:

- external provider calls = 0;
- stop `M12CT_PROVIDER_WIRE_REQUEST_DRIFT`.

Do not repair the serializer in M12CT.

## 6. Re-run all local pre-inference gates

Before call 1 require:

- M12CS-R1 provider dialect scan: 16/16 PASS
- provider-wire uniqueItems: 0
- provider-wire unsupported keywords: 0
- semantic uniqueness positive/negative fixtures: PASS
- schema/validator/materializer missing enforcement: 0
- typed business-quality regression: PASS
- security valuation basis regression: PASS
- historical failure replay: PASS
- Pass-A semantic branch coverage: complete
- Pass-B semantic branch coverage: complete
- 22/22 no-model dry materialization: PASS
- price/technical leak into Pass A: 0
- target-label leak: 0
- sealed reference semantic open count: 0
- production diff: 0

Freeze all call inputs, prompts, semantic schemas, provider-wire schemas, subject contexts, ref catalogs and hashes before provider call 1.

## 7. Two-pass execution topology

Planned provider/model calls: **16**.

Fundamental Core calls: **0**.

### Pass A — 8 calls

US:
1. CORZ / CPNG / CRCL
2. GOOGL / HUT / IBM
3. MU / RXRX / SKHY
4. SNDK / TSLA / TSM
5. WRD / WULF

KR:
6. 000660 / 003690 / 005490
7. 005930 / 010120 / 012450
8. 047810 / 086280

Pass B must not start before all eight Pass-A calls are accepted and the complete Pass-A output is frozen.

### Pass B — 8 calls

Use the same batch topology after deterministic post-Pass-A materialization.

## 8. Pass A policy — frozen, no edits

Use the exact M12CS-R1 Pass-A semantic contract.

Pass A remains price-blind.

Model-visible Pass-A input must not contain:

- current price;
- chart/technical/tactical values;
- current valuation percentile;
- entry-price bands;
- preferred entry ranges;
- New Buyer/Holder prior labels;
- production AI judgments;
- independent assistant judgments;
- sealed comparison material.

Model judges only the frozen model-owned business/archetype/regime/directional-disclosure fields.

Runtime owns ordinary business evidence quality and security valuation basis.

## 9. Pass A execution discipline

For each call:

- single attempt;
- exact provider-wire schema;
- raw response archive;
- raw-contract validation;
- local semantic uniqueness validation;
- semantic/cross-ref validation;
- stage-specific causal failure classification.

A hard failure stops all remaining dependent work.

No:
- retry
- repair model
- schema repair
- judge
- fallback
- selective rerun
- per-ticker rerun
- prompt hotfix
- schema hotfix.

Pass-A completion gate:

- 8/8 provider-accepted completed responses;
- 8/8 raw-contract accepted;
- 8/8 semantic accepted;
- 22/22 subjects accepted;
- price leak 0;
- technical leak 0;
- target leak 0.

Then freeze Pass A with hashes.

## 10. Deterministic post-Pass-A materialization

Using the frozen Pass-A classification plus frozen M12CP/M12CR-R1 policy:

materialize 22/22:

- business evidence quality;
- security valuation basis;
- archetype/tier policy outcome;
- fundamental option or exact unresolved reason.

No model-authored fundamental price, method, status or refs.

### Security valuation basis

Frozen-snapshot generic projection should derive:

RESOLVED: 15
UNRESOLVED: 7

Expected unresolved regression set after generic derivation:
- CPNG
- SKHY
- TSM
- WRD
- 010120
- 012450
- 047810

This list is only a regression assertion, never a hardcoded derivation rule.

An unresolved security basis:

- blocks unsafe per-share fundamental option;
- may support New Buyer WAIT;
- does not lower Overall by itself;
- does not create Holder REVIEW/REDUCE by itself.

## 11. Pass B policy — frozen, no edits

Pass B receives:

- frozen Pass-A result;
- deterministic fundamental option/unresolved state;
- current price/as-of;
- tactical catalog;
- frozen timing/market context;
- exact frozen business evidence needed for decision axes.

It outputs only the exact M12CS-R1 model-owned judgment surface.

Runtime owns all deterministic price/ref/status/method fields.

## 12. Pass B consistency rules

### Overall

For DURABLE_FRANCHISE / STRUCTURAL_CYCLICAL_LEADER:

- valuation/timing/security-basis unresolved alone cannot be sole evidence for HOLD/SELL;
- material business/thesis/cycle/competitive/earnings/cash-flow evidence is required.

No rule forces BUY.

For EXECUTION_DEPENDENT_GROWTH:
execution economics, margins, cash burn, financial resilience, dilution and realized growth may directly affect Overall.

### New Buyer

ATTRACTIVE requires the frozen resolved-fundamental-position conditions.

WAIT may be supported by:
- current price above resolved fundamental band;
- unresolved fundamental valuation;
- unresolved security valuation basis;
- unfavorable tactical timing with intact long-term thesis;
- another already frozen WAIT condition.

AVOID requires material execution/thesis risk under the frozen contract.

### Holder

Valuation alone cannot create REVIEW.

BUSINESS_EVIDENCE_QUALITY=CONFIDENCE_ONLY alone cannot create REVIEW.

SECURITY_VALUATION_BASIS=UNRESOLVED alone cannot create REVIEW/REDUCE.

REVIEW/REDUCE requires frozen structured thesis/execution/material-risk evidence.

## 13. Runtime entry-range materialization

After Pass B:

- materialize tactical selected candidate;
- combine with deterministic fundamental option using the frozen rule;
- calculate price distance;
- project exact refs/method/status/runtime fields.

Fundamental unresolved:
- preferred fundamental entry remains unresolved/null;
- tactical support remains timing context only.

No arbitrary percentage discount.

No model-authored deterministic entry metadata.

## 14. Call ledger semantics

For all 16 planned calls distinguish:

- planned
- wrapper attempted
- provider request accepted
- model inference accepted
- completed response
- raw-contract accepted
- semantic accepted

Provider schema rejection is **pre-inference**.

Use structured failure source/stage, never evidence-text keyword matching.

## 15. Complete PASS requirements

Terminal:

`M12CT_FRESH_TWO_PASS_PROVIDER_WIRE_CALIBRATION_PASS_READY_FOR_CHAT_REVIEW`

requires:

### Contract/transport
- implementation exact
- semantic freeze exact
- provider-wire freeze exact
- outbound request binding 16/16
- provider-wire dialect PASS 16/16
- unsupported keyword 0
- uniqueItems on wire 0
- model exactly gpt-5.6-sol

### Pass A
- 8/8 calls accepted and complete
- 22/22 subjects accepted
- price/technical/target leak 0
- freeze complete before Pass B

### Materialization
- 22/22 deterministic outcomes
- unsafe security-basis projection 0
- business/security-quality conflation 0
- model-authored fundamental numbers/refs/status 0

### Pass B
- 8/8 calls accepted and complete
- 22/22 subjects accepted
- Overall/New Buyer/Holder 22/22
- consistency validation PASS
- runtime entry materialization 22/22

### Final freeze
- final 22-subject result frozen/hashes complete
- sealed comparison material not opened before freeze

Agreement with historical human/AI labels is NOT a PASS condition.

## 16. Required pre-reveal analysis

Before opening the sealed reference, summarize frozen M12CT:

- archetype distribution
- regime-tier distribution
- business-quality distribution
- security-basis distribution
- Overall distribution
- New Buyer distribution
- Holder distribution
- BUY / WAIT / HOLDABLE count
- Holder REVIEW count and reason classes
- fundamental resolved/unresolved
- WAIT resolved-price count
- WAIT unresolved-fundamental count
- tactical resolved/unresolved
- directional disclosure-quality count

For every resolved WAIT price range include:

- ticker
- current price/as-of
- archetype/tier
- valuation method
- fundamental low/high
- final preferred low/high if resolved
- distance
- tactical context
- exact refs.

Tactical support alone must never be presented as fundamental fair value.

## 17. Blind post-freeze comparison

Only after complete final result freeze:

open the packaged `post-freeze-reference.zip` exactly once.

Compare descriptively:

1. original M12CM production AI;
2. independent assistant blind judgment;
3. M12CT shadow.

Report:

- 3-axis exact agreement;
- Overall agreement;
- New Buyer agreement;
- Holder agreement;
- label distributions;
- BUY/WAIT/HOLDABLE frequency;
- Holder REVIEW frequency;
- changes in overall-direction conservatism;
- resolved WAIT price coverage;
- remaining unresolved valuation coverage.

Explicitly inspect:
- large/core franchise names;
- structural cyclicals;
- execution-dependent growth names;
- security-basis-unresolved securities.

Do not treat either previous judgment set as ground truth.

No inference, threshold change, prompt edit, schema edit or policy edit after reference reveal.

## 18. Production boundary

Even on PASS:

- production Stage-2 unchanged;
- production investment policy unchanged;
- production entry-price schema unchanged;
- production sends/intents/DB writes = 0;
- scheduler changes = 0;
- broker read/order/modify/cancel = 0;
- main merge = 0;
- remote push = 0;
- deployment = 0.

Return to Chat.

## 19. Required artifacts

At minimum:

- `source-base-integrity.json`
- `m12cs-r1-dual-freeze-binding.json`
- `transport-model-binding.json`
- `outbound-provider-request-schema-binding-16.json`
- `pre-inference-provider-dialect-reproof.json`
- `pre-inference-semantic-regression-reproof.json`
- `target-price-technical-leak-proof.json`
- frozen model-input manifest
- all 8 Pass-A inputs/prompts/internal schemas/provider-wire schemas/ref catalogs/raw outputs/transport logs
- `pass-a-call-ledger.json`
- `pass-a-output-freeze-manifest.json`
- `pass-a-22-subject-classification.json`
- `fundamental-option-materialization-22.json`
- `business-quality-runtime-22.json`
- `security-valuation-basis-runtime-22.json`
- all 8 Pass-B inputs/prompts/internal schemas/provider-wire schemas/ref catalogs/raw outputs/transport logs
- `pass-b-call-ledger.json`
- `pass-b-output-freeze-manifest.json`
- `shadow-22-subject-results.json`
- `runtime-entry-range-materialization-22.json`
- `new-buyer-consistency-results.json`
- `overall-holder-policy-validation.json`
- `entry-range-coverage-and-methods.json`
- `final-shadow-freeze-manifest.json`
- pre-reveal frozen-result analysis
- post-freeze three-way comparison JSON/MD
- validation logs/JUnit
- Ruff / format / diff-check
- safety counters
- complete blocker ledger
- program completion
- REPORT.md
- artifact manifest
- result ZIP SHA sidecar.

## 20. Validation baseline

M12CS-R1 submitted:

- focused: 273 passed
- frozen-contract: 182 passed
- full: 4,394 passed / 63 skipped
- Treasury/KRX: 121 passed
- Ruff: PASS
- Ruff format: PASS
- git diff --check: PASS

No test deletion or skip inflation.

After execution, re-run the relevant focused/full/frozen/Treasury-KRX suites.

## 21. Terminal states

Use one:

- `M12CT_FRESH_TWO_PASS_PROVIDER_WIRE_CALIBRATION_PASS_READY_FOR_CHAT_REVIEW`
- `M12CT_FROZEN_IMPLEMENTATION_DRIFT`
- `M12CT_FROZEN_CONTRACT_DRIFT`
- `M12CT_TRANSPORT_MODEL_DRIFT`
- `M12CT_TRANSPORT_CONFIG_DRIFT`
- `M12CT_PROVIDER_WIRE_REQUEST_DRIFT`
- `M12CT_PASS_A_FAILED`
- `M12CT_DETERMINISTIC_MATERIALIZATION_FAILED`
- `M12CT_PASS_B_FAILED`
- `M12CT_BLINDNESS_OR_TARGET_LEAK_FAILURE`
- `M12CT_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT`

No terminal state authorizes production integration.
