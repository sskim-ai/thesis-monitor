# Thesis Monitor — M12CW Final Fresh Two-Pass Capability E2E Calibration Proof

## 0. Task identity

Work-instruction filename:

`20260918-m12cw-final-fresh-two-pass-capability-e2e-calibration-proof.md`

Suggested result bundle:

`thesis-monitor-20260918-m12cw-final-fresh-two-pass-capability-e2e-calibration-proof-report.zip`

This is the **final fresh end-to-end calibration proof** after Pass-B-only capability closure.

It must run:

- fresh Pass A from call 1;
- fresh deterministic materialization;
- fresh subject-specific Pass-B capability generation;
- fresh Pass B from call 1;
- final 22-subject freeze;
- one post-freeze descriptive three-way comparison.

It is NOT:

- another B-only development loop;
- a reuse of M12CV B judgments;
- a continuation of M12CU/M12CV generations;
- a policy/schema/prompt retuning task;
- a production integration/deployment task;
- a market/fundamental refresh.

No application/runtime/config source edits are authorized.

## 1. Exact repository implementation

Required execution head:

`b63726d9c1a97886a842a304a433a5fb55166288`

Working tree must be clean.

Required source base ancestor:

`0691560bb20b430c15e3c0862de679ce3c023b60`

If head differs or tree is dirty:

`M12CW_FROZEN_IMPLEMENTATION_DRIFT`

Do not patch, merge, format, fast-forward or rebase inside the execution task.

## 2. Source result binding

### M12CV

Bind exact result SHA-256:

`a59c712ac51cee00ee709e5b4c589d4a461827589acf2158cc18f36894f20673`

Required evidence:

- artifact manifest 264/264 PASS;
- B-only generation:
  `20260918-m12cv-pass-b-only-20260918T031048Z-b63726d9c1a9`;
- Pass-B 8/8 completed and semantically accepted;
- 22/22 subjects accepted;
- postrun substantive tests PASS except repo-wide Ruff-format scope.

### M12CU

Bind exact result SHA-256:

`ed8737b400ff84f77f5d8c13a365aa2d9ddee5c53f063c123c956d2c721053ea`

Use M12CU only for:
- accepted fresh Pass-A contract/live baseline;
- source/input lineage;
- failed Pass-B historical contract evidence where needed.

Do not reuse M12CU Pass-A model output in M12CW.

### M12CT-R1

Bind exact result SHA-256:

`01d39aa8f468634b20b77fdf0b5adaec9d57edd09210d1662fe29d1c8b5deab1`

Preserve:
- single-scalar directional balance;
- raw failure ordering;
- provider-wire compatibility lineage.

## 3. M12CV B-only acceptance boundary

M12CV's submitted terminal was FAIL only because postrun Ruff-format validation was scoped too broadly.

Do not rewrite its artifact.

For M12CW preflight, independently re-prove the B implementation using the correct validation scope.

### 3.1 Changed-path discovery

Compute:

`git diff --name-only 0691560bb20b430c15e3c0862de679ce3c023b60..b63726d9c1a97886a842a304a433a5fb55166288`

Classify changed files.

Expected production application/runtime/config changed paths: **0**.

If any production application/runtime/config file is changed:

`M12CW_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT`

### 3.2 Formatting gate

For all changed Python files plus the frozen shadow-contract/test source files that directly execute M12CW, run:

- `ruff check <in-scope paths>`
- `ruff format --check <in-scope paths>`

Do **not** run repo-wide `ruff format --check .` as the normative gate.

The repository already contains broad pre-existing format drift unrelated to this task.

If any in-scope changed/frozen shadow Python file fails format:

- external model calls = 0;
- stop:
  `M12CW_CHANGED_PATH_FORMAT_PRECHECK_FAILED`

Do not auto-format inside M12CW.

A repo-wide format scan may be recorded informationally, but it cannot overwrite the scoped gate.

## 4. Frozen analytical input

Use only:

`20260917-m12cm-current-v4-smoke-20260917T062918Z-5c0cb075ce8b`

Population:

### US14
CORZ, CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF

### KR8
000660, 003690, 005490, 005930, 010120, 012450, 047810, 086280

No market refresh.
No source enrichment.
No Fundamental Core model calls.

## 5. Pass-A contract freeze

Pass A must remain exact to the accepted M12CU/M12CT lineage.

Before inference regenerate all eight Pass-A:
- prompts;
- internal semantic schemas;
- provider-wire schemas;
- subject contexts;
- ref catalogs.

Compare deterministic hashes to the accepted fresh M12CU Pass-A call/input baseline.

No actual previous Pass-A model output is reused.

If any deterministic Pass-A contract/input hash drifts without a documented package-path-only reason:

`M12CW_PASS_A_CONTRACT_DRIFT`

and external model calls remain 0.

## 6. Provider/model binding

Required model:

`gpt-5.6-sol`

Required reasoning effort:

`xhigh`

Expected transport baseline:

`OpenAI Codex v0.153.4`

Record actual values before call 1.

No fallback model.

If model differs:

`M12CW_TRANSPORT_MODEL_DRIFT`

If transport/request semantics differ materially from the proven path:

`M12CW_TRANSPORT_CONFIG_DRIFT`

## 7. Provider-wire preflight

Before external call 1 perform no-network serialization for all eight Pass-A requests.

Require:

- outbound schema is provider-wire projection;
- internal semantic schema is not sent directly;
- `uniqueItems = 0`;
- unsupported provider keyword = 0;
- all arrays have `items`;
- strict object rules PASS;
- provider limits PASS.

After fresh Pass A and deterministic materialization, regenerate all eight Pass-B capability schemas and repeat the exact provider-wire/outbound binding proof before Pass-B call 1.

No serializer/schema repair inside M12CW.

## 8. Fresh generation

Create a new generation ID.

Prohibited reuse:

- M12CU Pass-A model output;
- M12CV Pass-B model output;
- M12CT Pass-A/B output;
- any earlier model judgment cache.

No cross-generation stitching.

## 9. Pass A — fresh 8 calls

Topology:

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

Hard rules:
- one attempt per batch;
- retry 0;
- repair 0;
- judge 0;
- fallback 0;
- selective rerun 0.

Pass A remains price-blind.

### Pass-A complete gate

Require:
- 8/8 provider-completed;
- 8/8 raw-contract PASS;
- 8/8 semantic PASS;
- 22/22 subjects accepted;
- price leak 0;
- technical leak 0;
- target-label leak 0.

Freeze Pass A completely before materialization/Pass B.

## 10. Deterministic post-Pass-A materialization

Using the fresh Pass-A output and frozen policy:

materialize 22/22:
- business evidence quality;
- security valuation basis;
- archetype/tier option;
- fundamental option or exact unresolved reason.

No model-authored:
- price;
- valuation method;
- deterministic refs;
- entry status.

Security valuation basis remains a price-resolution gate, not business-thesis evidence.

## 11. Fresh subject-specific Pass-B capability generation

Use the exact M12CV capability-builder semantics at implementation head `b63726...`.

Generate a capability catalog for each fresh subject after deterministic materialization.

### New Buyer

Only offer branches whose deterministic prerequisites are satisfiable.

Examples:

- fundamental UNRESOLVED:
  `FUNDAMENTAL_RANGE_POSITION` absent.
- fundamental resolved/current above band:
  range-position WAIT may be exposed.
- unsafe security basis:
  ATTRACTIVE must be absent where frozen policy forbids it.
- execution/thesis risk:
  only exposed when eligible material evidence exists.

### Holder

Do not expose REVIEW/REDUCE branches that lack eligible nonvaluation thesis/execution/material-risk evidence.

Valuation alone, CONFIDENCE_ONLY alone and security-basis unresolved alone do not make REVIEW/REDUCE admissible.

### Overall

Preserve frozen Overall policy.

For durable/structural names, valuation/timing/security basis alone cannot be sufficient for downgrade.

Do not hardcode ticker outcomes.

## 12. Pass-B capability preflight

Before Pass-B call 1 require:

- capability catalogs: 22/22 PASS;
- empty decision surfaces: 0;
- deterministic impossible branch exposure: 0;
- capability/validator parity unresolved count: 0;
- provider-wire schema scan: 8/8 PASS;
- outbound request binding: 8/8 PASS;
- single-scalar directional balance fixtures PASS;
- target-label leak: 0.

If this fails, do not call Pass B.

## 13. Pass B — fresh 8 calls

Same batch topology as Pass A.

Model owns only the frozen judgment surface, including:

`directional_buy_score ∈ [0,10]`

Runtime owns:

`directional_balance.sell = 10 - buy`

using Decimal-safe arithmetic.

Hard:
- retry 0;
- repair 0;
- judge 0;
- fallback 0;
- selective rerun 0;
- per-ticker rerun 0;
- prompt/schema/capability hotfix 0.

First hard failure stops remaining work.

## 14. Pass-B validation order

For each batch:

1. persist raw provider output;
2. raw/provider contract validation;
3. raw semantic/capability validation;
4. persist exact rule IDs;
5. stop immediately on raw failure;
6. normalize;
7. project directional balance;
8. materialize entry/tactical runtime fields;
9. final policy/cross-reference validation.

Downstream envelope errors must not mask raw root causes.

## 15. Final E2E PASS requirements

Terminal:

`M12CW_FINAL_FRESH_TWO_PASS_E2E_CALIBRATION_PASS_READY_FOR_CHAT_INTEGRATION_REVIEW`

requires all:

### Preflight
- exact implementation head;
- clean worktree;
- production application/runtime/config changed paths = 0;
- in-scope Ruff check PASS;
- in-scope Ruff format PASS;
- Pass-A deterministic contract/input binding PASS;
- provider/model binding PASS.

### Pass A
- 8/8 calls complete/accepted;
- 22/22 subjects accepted;
- price/technical/target leak = 0;
- complete freeze before Pass B.

### Materialization
- 22/22 deterministic outcomes;
- unsafe security valuation projection = 0;
- business/security-quality conflation = 0.

### Capability generation
- 22/22 catalogs;
- deterministic impossible branch exposure = 0;
- provider-wire Pass-B schemas 8/8;
- outbound Pass-B request binding 8/8.

### Pass B
- 8/8 calls complete/accepted;
- 22/22 raw/final semantic PASS;
- model-authored sell = 0;
- PB_BALANCE_SUM = 22/22;
- New Buyer consistency = 22/22;
- Overall/Holder policy validation = 22/22;
- runtime entry materialization = 22/22.

### Final freeze
- final 22-subject result hashed/frozen;
- historical comparison archive semantic access before freeze = 0.

Agreement with old judgments is not a PASS criterion.

## 16. Pre-reveal result analysis

Before opening prior judgments, report the fresh M12CW result alone:

- archetype distribution;
- valuation regime distribution;
- business-quality distribution;
- security-basis distribution;
- Overall distribution;
- New Buyer distribution;
- Holder distribution;
- directional buy scores;
- BUY/WAIT/HOLDABLE count;
- Holder REVIEW/REDUCE counts and reasons;
- fundamental resolved/unresolved;
- WAIT resolved-price count;
- WAIT unresolved count;
- tactical resolved/unresolved;
- resolved preferred ranges.

For each WAIT with a resolved fundamental/preferred range include:
- ticker;
- current price/as-of;
- archetype/tier;
- valuation method;
- fundamental low/high;
- preferred low/high;
- distance;
- tactical component;
- canonical refs.

Do not call tactical support fundamental fair value.

## 17. One post-freeze three-way comparison

Only after complete final freeze open the sealed historical comparison package exactly once.

Compare descriptively:

1. original M12CM production AI;
2. independent assistant blind judgment;
3. fresh M12CW result.

Report:
- exact 3-axis agreement;
- Overall agreement;
- New Buyer agreement;
- Holder agreement;
- label distributions;
- directional-balance differences;
- BUY/WAIT/HOLDABLE frequency;
- Holder REVIEW frequency;
- resolved WAIT price coverage;
- remaining unresolved price coverage.

Explicitly discuss:
- durable/core names;
- structural cyclicals;
- execution-dependent growth names;
- security-basis-unresolved securities.

Do not treat prior human or AI judgment as ground truth.

After reveal:
- external model calls = 0;
- policy/schema/prompt edits = 0;
- threshold tuning = 0.

## 18. Postrun validation — correct scope

Run:

### Focused
current M12CV/M12CT/M12CS/M12CR/M12CQ shadow-contract tests.

### Frozen-contract
all applicable frozen shadow-contract tests.

### Full
entire pytest suite.

### Treasury/KRX
existing frozen market-context suite.

### Ruff check and Ruff format
Gate only:
- Python files changed from source base through current implementation;
- exact shadow/test Python files involved in M12CW execution.

Do not use repository-wide formatting debt as this task's gate.

Record a repo-wide format scan, if desired, only as:
`INFORMATIONAL_PREEXISTING_FORMAT_DEBT`.

### git diff --check
PASS.

No test deletion or skip inflation.

## 19. M12CV validation-scope regression control

Create a regression proving:

- the old repo-wide M12CV format command would flag unrelated legacy files;
- the scoped changed-path/frozen-shadow format gate is PASS;
- no production file was formatted/mutated;
- no mass-format commit was created.

Required status:

`M12CV_POSTRUN_FORMAT_SCOPE_FALSE_NEGATIVE_CLOSED`

## 20. Production boundary

Even on full M12CW PASS:

- production Stage-2 unchanged;
- production investment policy unchanged;
- production entry-price schema unchanged;
- production send/intents/DB writes = 0;
- scheduler changes = 0;
- broker read/order/modify/cancel = 0;
- main merge = 0;
- remote push = 0;
- deployment = 0.

Return to Chat.

Chat will review:
- final fresh three-way calibration;
- resolved/unresolved entry-price coverage;
- whether the new philosophy is acceptable;
- whether a separate production-integration task should be authorized.

## 21. Required artifacts

At minimum:

- `source-base-integrity.json`
- `m12cv-chat-acceptance-reconciliation.json`
- `m12cv-format-scope-diagnostic.json`
- `changed-path-format-precheck.json`
- `pass-a-fresh-contract-binding.json`
- `transport-model-binding.json`
- Pass-A outbound provider binding 8
- all Pass-A inputs/schemas/outputs/logs
- Pass-A call ledger/freeze
- fresh Pass-A 22 classification
- fresh business/security quality 22
- fresh fundamental materialization 22
- `fresh-pass-b-capability-catalog-22.json`
- capability-validator parity
- capability exclusion analysis
- Pass-B provider dialect scan 8
- Pass-B outbound binding 8
- all Pass-B inputs/schemas/outputs/logs
- Pass-B call ledger/freeze
- directional balance runtime 22
- New Buyer consistency 22
- Overall/Holder policy validation
- runtime entry-range materialization 22
- final fresh 22 results
- final freeze manifest
- pre-reveal analysis
- post-freeze 3-way comparison JSON/MD
- validation logs/JUnit
- scoped Ruff/format evidence
- optional repo-wide-format informational log
- diff-check
- safety counters
- complete blocker ledger
- program completion
- REPORT.md
- artifact manifest
- external ZIP SHA sidecar.

## 22. Terminal states

Use one:

- `M12CW_FINAL_FRESH_TWO_PASS_E2E_CALIBRATION_PASS_READY_FOR_CHAT_INTEGRATION_REVIEW`
- `M12CW_FROZEN_IMPLEMENTATION_DRIFT`
- `M12CW_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT`
- `M12CW_CHANGED_PATH_FORMAT_PRECHECK_FAILED`
- `M12CW_PASS_A_CONTRACT_DRIFT`
- `M12CW_TRANSPORT_MODEL_DRIFT`
- `M12CW_TRANSPORT_CONFIG_DRIFT`
- `M12CW_PASS_A_FAILED`
- `M12CW_DETERMINISTIC_MATERIALIZATION_FAILED`
- `M12CW_PASS_B_CAPABILITY_PREFLIGHT_FAILED`
- `M12CW_PASS_B_FAILED`
- `M12CW_BLINDNESS_OR_TARGET_LEAK_FAILURE`
- `M12CW_POSTRUN_VALIDATION_FAILED`

No state authorizes production integration automatically.

## 23. Hard safety

- total external model calls <= 16
- Fundamental Core model calls = 0
- market refresh = 0
- production application/runtime/config behavior changes = 0
- production sends/intents/DB writes = 0
- broker read/order/modify/cancel = 0
- scheduler changes = 0
- main merge = 0
- remote push = 0
- deployment = 0.
