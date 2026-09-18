# Thesis Monitor — M12CU Fresh Two-Pass Single-Scalar Balance Calibration Shadow

## 0. Task identity

Work-instruction filename:

`20260918-m12cu-fresh-two-pass-single-scalar-balance-calibration-shadow.md`

Suggested result bundle:

`thesis-monitor-20260918-m12cu-fresh-two-pass-single-scalar-balance-calibration-shadow-report.zip`

This is a **fresh execution/proof task** for the already-closed M12CT-R1 two-pass contract.

It is NOT:

- a continuation of the failed M12CT generation;
- a selective Pass-B rerun;
- a schema/validator discovery task;
- a prompt retuning task;
- an archetype/valuation-policy redesign;
- a data-quality/security-basis redesign;
- a market/fundamental refresh;
- a production integration/deployment task.

No application/runtime/config source edits are authorized.

Expected repository diff before inference: **0**.

## 1. Exact required implementation

Repository execution head must be exactly:

`0691560bb20b430c15e3c0862de679ce3c023b60`

Working tree must be clean.

If not exact:

`M12CU_FROZEN_IMPLEMENTATION_DRIFT`

Do not repair, rebase, fast-forward, or patch inside this task.

## 2. Source binding

Verify M12CT-R1 result:

- result ZIP SHA-256:
  `01d39aa8f468634b20b77fdf0b5adaec9d57edd09210d1662fe29d1c8b5deab1`
- artifact manifest:
  134 declared payloads, 134/134 hash/size PASS.
- completion:
  `M12CT_R1_DIRECTIONAL_BALANCE_OWNERSHIP_CLOSED_READY_FOR_FRESH_TWO_PASS_SHADOW`

Verify prior source lineage preserved in that result:

- M12CT result:
  `cfd673b5e65d3aa6e7991f15792b093568ad94539c6b6072c3475d356ce20a4d`
- M12CS-R1 result:
  `9724c1f3200d92672f3f6a7f8e4e0cd7c9af55033c07d6fde28845321fddf508`

No historical model output may be reused.

## 3. Dual frozen-contract binding

Before any external call, bind the exact M12CT-R1 manifests.

### Semantic contract freeze

Manifest SHA-256:

`c067f1cfc7bce38580461475434d79844866daf7422ed945ee2d8542974411d9`

Required semantics include:

- Pass A unchanged from prior frozen two-pass contract;
- Pass B model owns `directional_buy_score`, not a two-number balance object;
- final downstream `directional_balance.buy/sell` semantics unchanged;
- final `PB_BALANCE_SUM` invariant preserved.

### Provider-wire contract freeze

Manifest SHA-256:

`86c098e4256dccfd6580d7d51527c1bfe55805a2030e365463c6477e943505d8`

Required:

- Pass A provider-wire hashes unchanged;
- Pass B provider-wire hashes equal the newly regenerated M12CT-R1 hashes;
- 16/16 provider dialect PASS;
- wire `uniqueItems = 0`;
- unsupported provider keyword count = 0.

Any mismatch before call 1:

`M12CU_FROZEN_CONTRACT_DRIFT`

No same-task regeneration or repair is authorized.

## 4. Frozen analytical input

Use only immutable M12CM calibration input:

`20260917-m12cm-current-v4-smoke-20260917T062918Z-5c0cb075ce8b`

Population:

### US14
CORZ, CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF

### KR8
000660, 003690, 005490, 005930, 010120, 012450, 047810, 086280

No market refresh.
No fundamental refresh.
No source enrichment.
No Fundamental Core model calls.

## 5. Transport/model binding

Required model:

`gpt-5.6-sol`

Expected historical transport baseline:

`OpenAI Codex v0.153.4`

Before call 1 record:

- actual resolved model;
- reasoning effort;
- Codex/transport version;
- command/config used.

If the model is not exactly `gpt-5.6-sol`:

`M12CU_TRANSPORT_MODEL_DRIFT`

If transport/config semantics differ materially from the proven path and exact request serialization cannot be proven unchanged:

`M12CU_TRANSPORT_CONFIG_DRIFT`

No fallback model.

## 6. Exact outbound provider-wire proof

Before any network request, use the exact execution path in no-network serialization mode for all 16 planned calls.

For each request prove:

- outbound structured-output schema is the M12CT-R1 **provider-wire** schema;
- normalized outbound schema hash equals the provider-wire freeze row;
- it is not the richer internal semantic schema;
- `uniqueItems = 0`;
- unsupported provider keywords = 0;
- all arrays contain `items`;
- strict object shape remains valid;
- provider-dialect scan PASS.

Required artifact:

`outbound-provider-request-schema-binding-16.json`

If any row fails:

- provider calls = 0;
- stop:
  `M12CU_PROVIDER_WIRE_REQUEST_DRIFT`

No serializer hotfix.

## 7. Re-run all pre-inference local gates

Before call 1 require:

- implementation exact;
- dual freeze exact;
- 16/16 provider-wire schema scan PASS;
- directional balance fixtures PASS;
- archived M12CT balance failure replay PASS;
- raw-failure-before-materialization ordering proof PASS;
- semantic uniqueness proof PASS;
- missing upstream enforcement = 0;
- typed business-quality regression PASS;
- security valuation basis regression PASS;
- all prior historical failure replays PASS;
- Pass-A branch coverage complete;
- Pass-B branch coverage complete;
- 22/22 no-model dry materialization PASS;
- final balance sum 22/22 PASS;
- model-authored sell count = 0;
- Pass-A price/technical leak = 0;
- target-label leak = 0;
- sealed post-freeze reference semantic access = 0;
- repository diff = 0.

Freeze all 16 exact prompts, contexts, internal schemas, provider-wire schemas, ref catalogs and request hashes before external call 1.

## 8. Fresh generation only

Create a wholly new generation ID.

Do not reuse:

- M12CT successful Pass-A model outputs;
- M12CT Pass-B raw output;
- any M12CN/M12CQ partial output;
- any prior generation cache containing model judgments.

No cross-generation stitching.

## 9. Execution topology

Total planned shadow model calls: **16**.

Fundamental Core model calls: **0**.

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

Pass B must not start until all Pass-A rows are accepted and the complete 22-subject Pass-A output is frozen.

### Pass B — 8 calls

Use identical batch topology after deterministic post-Pass-A materialization.

## 10. Pass A — frozen policy

Use exact frozen Pass-A prompt/schema/context.

Pass A remains price-blind.

Model-visible inputs must not contain:

- current price;
- chart/technical/tactical values;
- current valuation percentile;
- precomputed entry price bands;
- preferred entry ranges;
- prior New Buyer/Holder labels;
- original production-AI verdicts;
- independent-assistant judgments;
- post-freeze comparison material.

Pass-A model-owned surface remains the frozen 9-field surface.

Runtime owns:

- ordinary business evidence quality;
- security valuation basis;
- all deterministic identities and metadata.

### Pass-A completion gate

Require:

- 8/8 provider requests accepted;
- 8/8 completed responses;
- 8/8 raw-contract accepted;
- 8/8 semantic accepted;
- 22/22 subjects accepted;
- price leak = 0;
- technical leak = 0;
- target leak = 0.

Then freeze Pass A before any Pass-B inference.

First hard failure stops all dependent calls.

## 11. Deterministic post-Pass-A materialization

Materialize all 22 using frozen M12CP/M12CR/M12CT-R1 policy.

Runtime owns:

- business evidence quality;
- security valuation basis;
- fundamental entry option or exact unresolved reason;
- price/method/ref/status metadata.

No model-authored fundamental price/ref/status.

Frozen generic security valuation basis is expected to derive:

- RESOLVED: 15
- UNRESOLVED: 7

Regression set after generic derivation:

CPNG, SKHY, TSM, WRD, 010120, 012450, 047810

This set is an assertion only, never a ticker-based rule.

Unresolved security valuation basis:

- blocks unsafe per-share fundamental price projection;
- may support New Buyer WAIT;
- cannot by itself lower Overall;
- cannot by itself create Holder REVIEW/REDUCE.

## 12. Pass B — new frozen single-scalar balance surface

Use exact M12CT-R1 Pass-B model contract.

Model-owned raw fields include exactly the frozen 9-field judgment surface, with:

`directional_buy_score`

instead of model-authored `{buy, sell}`.

### Directional buy score

Semantics:

- number in `[0, 10]`;
- 0 = fully sell-leaning;
- 5 = balanced;
- 10 = fully buy-leaning;
- do not normalize to 0..1;
- model does not author sell.

Runtime projection:

- `buy = Decimal(str(directional_buy_score))`
- `sell = Decimal("10") - buy`

Final canonical balance must satisfy:

`PB_BALANCE_SUM`

exactly under canonical decimal semantics.

## 13. Pass-B policy consistency

All previously frozen investment semantics remain unchanged.

### Overall

For DURABLE_FRANCHISE / STRUCTURAL_CYCLICAL_LEADER:

- valuation, current price, tactical timing or security-basis unresolved alone cannot be the sole reason for HOLD/SELL;
- downgrade requires material business/thesis/cycle/competitive/earnings/cash-flow evidence.

No rule forces BUY.

For EXECUTION_DEPENDENT_GROWTH:

execution economics, realized growth, margins, cash burn, financial resilience and dilution may directly affect Overall.

### New Buyer

ATTRACTIVE requires frozen resolved fundamental-position conditions.

WAIT may be supported by:

- current price above resolved fundamental band;
- unresolved fundamental valuation;
- unresolved security valuation basis;
- unfavorable tactical timing with intact long-term thesis;
- another frozen authorized WAIT condition.

AVOID requires material execution/thesis risk.

### Holder

Valuation-expensive alone cannot create REVIEW.

BUSINESS_EVIDENCE_QUALITY=CONFIDENCE_ONLY alone cannot create REVIEW.

SECURITY_VALUATION_BASIS=UNRESOLVED alone cannot create REVIEW/REDUCE.

REVIEW/REDUCE requires frozen structured material thesis/execution/risk evidence.

## 14. Raw failure surface ordering

For every Pass-B call:

1. persist raw provider output;
2. validate provider/raw contract;
3. validate raw model semantics;
4. persist raw semantic result;
5. if raw semantic fails, stop immediately with exact rule IDs;
6. only on raw semantic PASS, normalize and deterministically project directional balance;
7. materialize remaining runtime fields;
8. run final semantic validation.

A raw semantic failure must never be replaced by a downstream empty-envelope/Pydantic error.

## 15. Runtime entry materialization

After valid Pass B:

- project `directional_balance`;
- project tactical selected candidate;
- combine tactical and deterministic fundamental option using frozen semantics;
- calculate distance to band;
- project exact refs/method/status/runtime fields.

Fundamental unresolved:

- fundamental/preferred price remains unresolved/null;
- tactical support is timing context only.

No arbitrary current-price discount.

Model-authored deterministic sell/entry metadata count = 0.

## 16. Execution discipline

For all 16 model calls:

- one attempt;
- retry = 0;
- repair model = 0;
- schema repair = 0;
- judge = 0;
- fallback = 0;
- selective rerun = 0;
- per-ticker rerun = 0;
- prompt hotfix = 0;
- schema hotfix = 0;
- post-call contract edit = 0.

Hard failure freezes the generation and stops subsequent dependent work.

## 17. Call-ledger semantics

For each planned call distinguish:

- planned;
- wrapper attempted;
- provider request accepted;
- model inference accepted;
- completed response;
- raw-contract accepted;
- raw-semantic accepted;
- materialized;
- final-semantic accepted.

Do not count pre-inference schema rejection as inference.

Use structured execution stage for causal classification, never keyword scans of model-visible evidence.

## 18. Complete PASS gate

Terminal:

`M12CU_FRESH_TWO_PASS_SINGLE_SCALAR_CALIBRATION_PASS_READY_FOR_CHAT_REVIEW`

requires all:

### Frozen contract / transport
- exact implementation head;
- semantic freeze exact;
- provider-wire freeze exact;
- outbound provider request binding 16/16;
- provider dialect 16/16;
- model exactly `gpt-5.6-sol`;
- repository diff 0.

### Pass A
- 8/8 calls fully accepted;
- 22/22 subjects accepted;
- price/technical/target leak 0;
- Pass-A freeze before Pass B.

### Deterministic materialization
- 22/22 outcomes;
- unsafe security-basis projection 0;
- business/security quality conflation 0;
- model-authored fundamental metadata 0.

### Pass B
- 8/8 calls fully accepted;
- 22/22 subjects accepted;
- raw semantic PASS 22/22;
- model-authored sell count 0;
- final `PB_BALANCE_SUM` PASS 22/22;
- Overall/New Buyer/Holder present 22/22;
- frozen policy-consistency validators PASS;
- runtime entry materialization PASS 22/22.

### Final freeze
- complete final 22-subject output frozen and hashed;
- sealed comparison material not semantically opened before freeze.

Agreement with previous human/AI judgments is not a PASS criterion.

## 19. Pre-reveal frozen-result analysis

Before opening any prior-judgment reference, report the M12CU result itself:

- archetype distribution;
- valuation regime distribution;
- business evidence quality distribution;
- security valuation basis distribution;
- Overall distribution;
- New Buyer distribution;
- Holder distribution;
- directional buy-score distribution/range;
- BUY / WAIT / HOLDABLE count;
- Holder REVIEW count and structured reasons;
- fundamental resolved/unresolved;
- WAIT with resolved entry band;
- WAIT with unresolved fundamental range;
- tactical resolved/unresolved;
- resolved preferred entry ranges;
- directional disclosure-quality count.

For each resolved WAIT range include:

- ticker;
- current price/as-of;
- archetype/tier;
- fundamental method;
- fundamental low/high;
- final preferred low/high if resolved;
- distance to band;
- tactical context;
- exact canonical refs.

Do not call tactical support alone fundamental fair value.

## 20. Blind post-freeze comparison

Only after the final 22-subject M12CU freeze:

open the packaged `post-freeze-reference.zip` exactly once.

Compare descriptively:

1. original M12CM production AI;
2. independent assistant blind judgment;
3. M12CU two-pass shadow.

Report:

- exact 3-axis agreement;
- Overall agreement;
- New Buyer agreement;
- Holder agreement;
- label distributions;
- BUY/WAIT/HOLDABLE frequency;
- Holder REVIEW frequency;
- directional balance differences;
- resolved WAIT price coverage;
- remaining unresolved fundamental-price coverage;
- large/core franchise cases;
- structural cyclical cases;
- execution-dependent growth cases;
- security-basis-unresolved cases.

Do not treat either historical judgment set as ground truth.

After reference reveal:

- model calls = 0;
- policy edits = 0;
- threshold edits = 0;
- prompt/schema edits = 0.

## 21. Production boundary

Even on PASS:

- production Stage-2 unchanged;
- production investment policy unchanged;
- production entry-price schema unchanged;
- production sends/intents/DB writes = 0;
- broker read/order/modify/cancel = 0;
- scheduler changes = 0;
- main merge = 0;
- remote push = 0;
- deployment = 0.

Return to Chat for system-level review.

## 22. Required artifacts

At minimum:

- `source-base-integrity.json`
- `m12ct-r1-dual-freeze-binding.json`
- `transport-model-binding.json`
- `outbound-provider-request-schema-binding-16.json`
- `pre-inference-provider-dialect-reproof.json`
- `pre-inference-semantic-regression-reproof.json`
- `directional-balance-ownership-reproof.json`
- `m12ct-balance-failure-replay-reproof.json`
- `pass-b-failure-surface-order-reproof.json`
- `target-price-technical-leak-proof.json`
- frozen model-input manifest
- all 8 Pass-A inputs/prompts/internal/provider schemas/ref catalogs/raw outputs/transport logs
- `pass-a-call-ledger.json`
- `pass-a-output-freeze-manifest.json`
- `pass-a-22-subject-classification.json`
- deterministic fundamental materialization 22
- business quality runtime 22
- security valuation basis runtime 22
- all 8 Pass-B inputs/prompts/internal/provider schemas/ref catalogs/raw outputs/transport logs
- `pass-b-call-ledger.json`
- all raw semantic validation artifacts
- `pass-b-output-freeze-manifest.json`
- `shadow-22-subject-results.json`
- `runtime-entry-range-materialization-22.json`
- `directional-balance-runtime-22.json`
- `new-buyer-consistency-results.json`
- `overall-holder-policy-validation.json`
- `entry-range-coverage-and-methods.json`
- final shadow freeze manifest
- pre-reveal analysis
- post-freeze 3-way comparison JSON/MD
- test/JUnit/logs
- Ruff / format / diff-check
- safety counters
- blocker ledger
- program completion
- REPORT.md
- artifact manifest
- result ZIP SHA sidecar.

## 23. Validation baseline

M12CT-R1 submitted:

- focused: 291 passed
- frozen-contract: 200 passed
- full: 4,412 passed / 63 skipped
- Treasury/KRX: 121 passed
- Ruff: PASS
- Ruff format: PASS
- git diff --check: PASS

After execution, rerun the applicable focused/frozen/full/Treasury-KRX suites.

No test deletion or skip inflation.

## 24. Terminal states

Use one:

- `M12CU_FRESH_TWO_PASS_SINGLE_SCALAR_CALIBRATION_PASS_READY_FOR_CHAT_REVIEW`
- `M12CU_FROZEN_IMPLEMENTATION_DRIFT`
- `M12CU_FROZEN_CONTRACT_DRIFT`
- `M12CU_TRANSPORT_MODEL_DRIFT`
- `M12CU_TRANSPORT_CONFIG_DRIFT`
- `M12CU_PROVIDER_WIRE_REQUEST_DRIFT`
- `M12CU_PASS_A_FAILED`
- `M12CU_DETERMINISTIC_MATERIALIZATION_FAILED`
- `M12CU_PASS_B_FAILED`
- `M12CU_BLINDNESS_OR_TARGET_LEAK_FAILURE`
- `M12CU_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT`

No terminal state authorizes production integration.
