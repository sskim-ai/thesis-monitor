# Thesis Monitor — M12CV Frozen Pass-A Fixture / Pass-B Capability Contract Closure

## 0. Task identity

Work-instruction filename:

`20260918-m12cv-frozen-pass-a-pass-b-capability-contract-closure.md`

Suggested result bundle:

`thesis-monitor-20260918-m12cv-frozen-pass-a-pass-b-capability-contract-closure-report.zip`

This is a **Pass-B-only contract closure + bounded 8-call shadow execution task**.

It deliberately reuses one previously accepted Pass-A result as an immutable upstream fixture so that Pass-B can be stabilized without paying for or rediscovering Pass-A on every iteration.

It is NOT:

- a final end-to-end proof;
- a fresh Pass-A run;
- a production policy integration;
- a market/fundamental refresh;
- a target-label fitting task;
- a selective replay of only CRCL;
- a same-generation repair of M12CU;
- a deployment/scheduler/notification/broker task.

Planned external model calls: **8 maximum**.

Pass-A model calls: **0**.

Production application/runtime/config behavior changes: **0**.

## 1. Exact source state

### M12CU result

Verify:

- result ZIP SHA-256:
  `ed8737b400ff84f77f5d8c13a365aa2d9ddee5c53f063c123c956d2c721053ea`
- artifact manifest:
  347 declared payloads, 347/347 hash and size PASS.
- generation:
  `20260918-m12cs-fresh-two-pass-20260918T020719Z-0691560bb20b`
- execution head:
  `0691560bb20b430c15e3c0862de679ce3c023b60`
- terminal:
  `M12CU_PASS_B_FAILED`

### M12CT-R1 result

Verify:

- result ZIP SHA-256:
  `01d39aa8f468634b20b77fdf0b5adaec9d57edd09210d1662fe29d1c8b5deab1`
- artifact manifest:
  134 declared payloads, 134/134 hash and size PASS.
- implementation head:
  `0691560bb20b430c15e3c0862de679ce3c023b60`
- completion:
  `M12CT_R1_DIRECTIONAL_BALANCE_OWNERSHIP_CLOSED_READY_FOR_FRESH_TWO_PASS_SHADOW`

The repository repair branch must start from the exact implementation head above.

Shadow-only changes are allowed. Production application/runtime/config changes are not.

## 2. Immutable Pass-A fixture

M12CV is explicitly allowed to reuse the **accepted M12CU Pass-A result**.

This is the only upstream model output that may be reused.

Required Pass-A fixture:

- calls: 8/8 PASS
- subjects: 22/22 PASS
- price leak: 0
- technical leak: 0
- target-label leak: 0
- Pass-A classification aggregate SHA-256:
  `9d5e1f8a5580cef553222d33ba341fc2c216d2ff536e562d487a5f150308e132`
- Pass-A freeze manifest file SHA-256:
  `16886fe09f6e12d69c1190a7cd2fb95685010e9637554b0d8279461ec2d24aa4`

Deterministic upstream artifacts must also be reused exactly:

- fundamental-option-materialization-22:
  `c74f138e26f8e3672c14af947c8d2b02f793019a29cc12c59fbd9635d8460552`
- business-quality-runtime-22:
  `c111b63410fc734935760a25b8432cc03920c051930b95bba8c74a9fd72cac60`
- security-valuation-basis-runtime-22:
  `db583a58be65f1396b556dbb23a3a555c931c0c3296fd591402979e3e2156716`

Before modifying Pass B:

1. extract the packaged fixture;
2. verify every file and aggregate hash;
3. prove subject order/cardinality = US14 + KR8 = 22;
4. prove no Pass-A model inference will occur in M12CV.

If fixture binding fails:

`M12CV_PASS_A_FIXTURE_BINDING_FAILED`

and external model calls remain 0.

## 3. Frozen Pass-A meaning

M12CV must not alter:

- Pass-A archetypes;
- Pass-A valuation regime tiers;
- Pass-A evidence refs;
- Pass-A business-evidence-quality state;
- security-valuation-basis state;
- deterministic fundamental-option result.

These are test fixtures for closing Pass B.

Do not reinterpret them to obtain preferred outcomes.

No Pass-A schema/prompt/model call.

## 4. Exact current Pass-B failure

M12CU Pass-B US batch 01 returned a complete model response.

Directional balance repair was successful:

- CORZ: buy score 5.8 -> buy 5.8 / sell 4.2
- CPNG: buy score 5.0 -> buy 5.0 / sell 5.0
- CRCL: buy score 4.3 -> buy 4.3 / sell 5.7
- `PB_BALANCE_SUM`: 3/3 PASS

CRCL failed only final New Buyer consistency:

`wait_without_authorized_structured_condition`

Model output:

- New Buyer: WAIT
- reason class: `FUNDAMENTAL_RANGE_POSITION`

Deterministic upstream state:

- fundamental option: UNRESOLVED
- unresolved reason:
  `EXECUTION_GROWTH_SCENARIO_METHOD_UNAVAILABLE`

Therefore there was no resolved fundamental range that could authorize `FUNDAMENTAL_RANGE_POSITION`.

The archived M12CU model output remains immutable and failed.

Do not rewrite its reason class.

## 5. Root design problem

The current Pass-B provider schema exposes branches that are syntactically valid but deterministically impossible for the specific subject.

Example current WAIT enum:

- FUNDAMENTAL_RANGE_POSITION
- FUNDAMENTAL_UNRESOLVED
- TACTICAL_TIMING
- EXECUTION_OR_THESIS_RISK

That same enum is offered even when:

- fundamental is unresolved;
- security valuation basis blocks safe per-share valuation;
- no eligible execution-risk evidence exists;
- other frozen preconditions make a reason class impossible.

The downstream validator then discovers the mismatch after inference.

M12CV must move deterministic impossibility **upstream of the model**.

## 6. Pass-B capability catalog

Create a deterministic, subject-specific, versioned:

`pass_b_capability_catalog`

for all 22 subjects.

It is constructed **after frozen Pass-A materialization and before Pass-B inference**.

The catalog must not decide the investment judgment itself.

It defines the set of choices that the frozen policy says are structurally admissible.

At minimum inventory capabilities for:

- Overall Direction;
- New Buyer stance + reason class;
- Holder stance + reason class;
- tactical choice availability;
- evidence-class availability needed by those branches.

Every capability must contain:

- subject/ticker binding;
- deterministic prerequisite facts;
- exact source/ref catalogs that make the branch admissible;
- allowed model enums/branches;
- reason why excluded branches are impossible;
- contract version.

No current or historical target label may determine capability membership.

## 7. New Buyer capability contract

Audit the actual frozen validator first. Do not invent new investment semantics.

Then upstream-enforce every deterministic precondition that can be known before inference.

### 7.1 ATTRACTIVE

The ATTRACTIVE branch may be model-visible only when the existing frozen policy's deterministic prerequisites can possibly be satisfied.

At minimum audit:

- resolved fundamental option;
- current-price position relative to permitted fundamental band;
- security valuation basis;
- any frozen severe execution/thesis exclusion condition.

If deterministic prerequisites make ATTRACTIVE impossible, omit the ATTRACTIVE branch from that subject's provider schema.

Do not force ATTRACTIVE when prerequisites are present; the model still chooses among valid stances.

### 7.2 WAIT

Build the WAIT reason-class enum per subject.

`FUNDAMENTAL_RANGE_POSITION`

may be offered only when a resolved fundamental range exists and the frozen policy recognizes the current deterministic range position as a possible WAIT condition.

If fundamental status is UNRESOLVED:

`FUNDAMENTAL_RANGE_POSITION` must be absent.

`FUNDAMENTAL_UNRESOLVED`

may be offered when the frozen policy recognizes unresolved fundamental price/value state, including already-authorized security-basis-driven inability to resolve the fundamental price.

`TACTICAL_TIMING`

may be offered only when an eligible timing/tactical decision surface exists under the frozen policy.

`EXECUTION_OR_THESIS_RISK`

may be offered only when the subject has eligible material execution/thesis risk evidence under the frozen catalogs.

Do not add a new reason class merely to fix CRCL unless the existing policy genuinely lacks a necessary semantic category and Chat review is required.

### 7.3 AVOID

Expose AVOID only under the frozen policy's deterministic eligibility surface.

Material execution/thesis-risk evidence requirements must remain enforced.

Do not make AVOID available solely because valuation is expensive, business-quality confidence is low, or security valuation basis is unresolved.

## 8. Holder capability contract

Pass B has not yet been exercised across all 22 live subjects, so preempt the next validator-only surprise.

Audit all frozen Holder consistency rules.

Build subject-specific capability branches where deterministic eligibility can be known before inference.

Preserve:

- valuation-expensive alone cannot create REVIEW;
- BUSINESS_EVIDENCE_QUALITY=CONFIDENCE_ONLY alone cannot create REVIEW;
- SECURITY_VALUATION_BASIS=UNRESOLVED alone cannot create REVIEW/REDUCE;
- REVIEW/REDUCE requires eligible structured thesis/execution/material-risk evidence.

If no eligible REVIEW reason/evidence class exists for a subject, the schema must not offer that impossible REVIEW branch.

If no eligible REDUCE reason/evidence class exists, omit REDUCE.

The model still selects among all actually admissible Holder states.

## 9. Overall capability contract

Audit the frozen Overall validator.

For DURABLE_FRANCHISE / STRUCTURAL_CYCLICAL_LEADER:

- valuation/timing/security-basis alone cannot support HOLD/SELL;
- non-BUY outcomes require eligible material business/thesis/cycle/competitive/earnings/cash-flow evidence.

Where the deterministic evidence catalog contains no evidence that could satisfy such a downgrade branch, do not offer an impossible branch merely for symmetry.

For EXECUTION_DEPENDENT_GROWTH, preserve the broader execution-risk policy already frozen.

Do not hardcode tickers or desired outcomes.

## 10. Schema generation from capabilities

Generate the Pass-B internal semantic schema and provider-wire schema **from the subject-specific capability catalog**.

The provider must not be able to emit a reason class or stance that deterministic preconditions already make impossible.

Use discriminated/subject-keyed branches as needed.

Preserve M12CS-R1 provider-wire compatibility:

- wire `uniqueItems = 0`;
- unsupported provider keywords = 0;
- every array has `items`;
- strict object shape;
- provider documented limits remain within bounds.

Preserve M12CT-R1 single-scalar directional balance:

`directional_buy_score ∈ [0,10]`

with runtime sell complement.

## 11. Cross-reference validators remain

Do not delete downstream validators.

They become defense-in-depth for:

- evidence ref eligibility;
- selected tactical candidate ownership;
- genuinely model-dependent cross-reference meaning;
- final policy consistency.

Target:

Every deterministic branch-impossibility rule should be impossible at provider-schema level or materialized deterministically before the model.

Rules that inherently depend on the model's selected evidence may remain runtime cross-reference validators.

Create:

`pass-b-capability-validator-parity-matrix.json`

Required classification per rule:

- `CAPABILITY_SCHEMA_ENFORCED`
- `DETERMINISTIC_MATERIALIZER`
- `MODEL_DEPENDENT_CROSS_REFERENCE`
- `UNRESOLVED_REQUIRES_CHAT`

For deterministic branch-impossibility rules:

`MODEL_DEPENDENT_CROSS_REFERENCE` is not acceptable.

## 12. Exhaustive no-model Pass-B preflight

Before external calls, use the frozen 22-subject upstream fixture to generate all capability catalogs and schemas.

Required checks:

- 22/22 capability catalogs generated;
- no subject has an empty total decision surface;
- current M12CU CRCL branch:
  `WAIT/FUNDAMENTAL_RANGE_POSITION`
  is absent;
- CRCL valid unresolved/tactical/risk branches remain only if independently eligible;
- all resolved-fundamental subjects expose only frozen-policy-compatible range-position branches;
- all security-basis-unresolved subjects cannot emit unsafe ATTRACTIVE branches;
- holder impossible branches removed;
- overall impossible branches removed where deterministic evidence eligibility is absent;
- provider dialect 8/8 Pass-B schemas PASS;
- outbound dry request binding 8/8 PASS;
- single-scalar balance fixtures PASS;
- target-label leak = 0.

## 13. Generic capability fixtures

Do not test only CRCL.

Create renamed/generic positive and negative fixtures covering at least:

1. fundamental UNRESOLVED + WAIT:
   FUNDAMENTAL_RANGE_POSITION absent.
2. fundamental UNRESOLVED:
   FUNDAMENTAL_UNRESOLVED available when authorized.
3. resolved fundamental with range-position WAIT condition:
   FUNDAMENTAL_RANGE_POSITION available.
4. security basis UNRESOLVED:
   unsafe ATTRACTIVE absent.
5. tactical surface unavailable:
   TACTICAL_TIMING absent.
6. material execution-risk evidence absent:
   EXECUTION_OR_THESIS_RISK / AVOID branch absent where required.
7. material execution-risk evidence present:
   corresponding branch available.
8. Holder REVIEW with no eligible thesis/execution reason:
   REVIEW absent.
9. Holder REVIEW with eligible material reason:
   REVIEW available.
10. Holder REDUCE without material negative eligibility:
    REDUCE absent.
11. durable/structural subject with no material downgrade evidence:
    impossible non-BUY branch excluded according to the frozen validator semantics.
12. execution-dependent-growth subject with eligible execution evidence:
    broader directional branch remains available.
13. renamed identities produce identical capabilities.

Do not use prior human/AI labels in fixture design.

## 14. Archived M12CU failure replay

Use M12CU Pass-B batch 01 only as a failure-shape fixture.

Required:

- old static schema admits CRCL's invalid branch;
- new capability schema rejects that exact raw branch before semantic materialization;
- archived model output remains immutable;
- no automatic rewrite to FUNDAMENTAL_UNRESOLVED or TACTICAL_TIMING.

Status:

`M12CU_WAIT_REASON_CAPABILITY_FAILURE_CAUGHT_PRE_INFERENCE`

## 15. Frozen Pass-A B-only execution mode

After all offline checks pass, create a **new B-only diagnostic generation**.

Generation metadata must explicitly include:

- `mode = PASS_B_ONLY_CONTRACT_CLOSURE`
- upstream Pass-A fixture generation ID;
- Pass-A aggregate SHA;
- fundamental materialization SHA;
- business quality SHA;
- security basis SHA;
- B contract implementation commit.

No Pass-A provider/model calls.

Pass-B inputs are reconstructed from:

- immutable M12CU Pass-A fixture;
- immutable M12CM source evidence already bound by that fixture/run;
- immutable deterministic materialization artifacts;
- new capability catalog/schema.

Do not use M12CU Pass-B model output as an input.

## 16. Pass-B-only live topology

Maximum external model calls: **8**.

Run from B batch 1:

### US
1. CORZ / CPNG / CRCL
2. GOOGL / HUT / IBM
3. MU / RXRX / SKHY
4. SNDK / TSLA / TSM
5. WRD / WULF

### KR
6. 000660 / 003690 / 005490
7. 005930 / 010120 / 012450
8. 047810 / 086280

Hard rules:

- one attempt per batch;
- retry 0;
- repair model 0;
- schema-repair model 0;
- judge 0;
- fallback 0;
- selective rerun 0;
- per-ticker rerun 0;
- post-call hotfix 0.

The first hard B failure stops the remaining B calls.

Do **not** rerun A.

## 17. Raw/final validation order

Preserve M12CT-R1 failure ordering:

1. persist raw provider output;
2. raw provider-contract validation;
3. raw semantic validation;
4. persist raw semantic rule IDs;
5. stop on raw semantic failure;
6. normalize;
7. deterministic directional-balance projection;
8. deterministic entry/tactical materialization;
9. final policy/cross-reference validation.

Do not allow a downstream envelope error to mask a primary raw failure.

## 18. B-only PASS requirements

Terminal:

`M12CV_PASS_B_ONLY_CONTRACT_CLOSURE_PASS_READY_FOR_FINAL_FRESH_E2E`

requires:

### Upstream fixture
- Pass-A external calls = 0
- fixture hashes exact
- 22/22 fixture subjects bound
- upstream deterministic materialization exact

### Capability closure
- capability catalogs 22/22
- deterministic impossible branch exposure count = 0
- CRCL archived invalid WAIT branch blocked pre-inference
- provider-wire schemas 8/8 PASS
- outbound request binding 8/8 PASS
- target-label leak 0

### Live Pass B
- 8/8 provider responses complete
- 8/8 raw-contract PASS
- 8/8 raw-semantic PASS
- 22/22 subjects normalized/materialized/final-semantic PASS
- model-authored sell count 0
- PB_BALANCE_SUM 22/22 PASS
- impossible New Buyer reason-class count 0
- impossible Holder branch count 0
- impossible Overall branch count 0
- runtime entry materialization 22/22 PASS

### Safety
- production changes 0
- production sends/intents/DB writes 0
- scheduler/broker/deploy/merge/push 0

A B-only PASS is **not** final end-to-end readiness.

## 19. B-only result analysis

Before returning to Chat report:

- Overall distribution
- New Buyer distribution
- Holder distribution
- directional buy-score distribution
- New Buyer reason-class distribution
- Holder reason-class distribution
- capability-excluded branch counts by class
- WAIT count
- WAIT fundamental resolved/unresolved
- WAIT tactical resolved/unresolved
- WAIT with resolved preferred entry band
- WAIT with unresolved fundamental range
- security-basis-unresolved New Buyer outcomes
- execution-dependent-growth outcomes
- Holder REVIEW/REDUCE reason classes
- final entry-range materialization status

For every resolved WAIT price range include exact current price, method/tier, fundamental range, final preferred range if resolved, distance and refs.

Do not open the historical sealed comparison archive.

## 20. No historical judgment reveal in M12CV

The purpose of M12CV is B contract closure, not score fitting.

Do not open/use:

- M12CM production AI verdicts;
- independent assistant blind judgments;
- prior three-way comparison;
- sealed post-freeze reference archive.

M12CU Pass-A output is allowed because it is the explicit upstream fixture.

M12CU failed Pass-B output is allowed only for failure-shape replay.

Target-label leak count must remain 0.

## 21. What happens after B-only PASS

Return to Chat.

Do not automatically run the final full generation.

Chat will then authorize one final:

`fresh Pass A 8 + fresh Pass B 8`

end-to-end generation under the frozen B contract.

That final fresh A+B run, not M12CV, is where:

- end-to-end calibration is proven;
- output is frozen;
- historical comparison archive may be opened;
- production integration can later be discussed.

## 22. Production boundary

Even on M12CV PASS:

- production Stage-2 unchanged;
- production investment policy unchanged;
- production entry-price schema unchanged;
- application/runtime/config behavior changes = 0;
- production sends/intents/DB writes = 0;
- broker read/order/modify/cancel = 0;
- scheduler changes = 0;
- main merge = 0;
- remote push = 0;
- deployment = 0.

## 23. Validation

Before B-only live execution run:

- new capability catalog tests;
- New Buyer capability branch fixtures;
- Holder capability branch fixtures;
- Overall capability branch fixtures;
- archived M12CU failure replay;
- provider-wire dialect 8/8;
- outbound dry binding 8/8;
- focused shadow suite;
- frozen-contract suite.

After B-only execution run:

- focused;
- frozen-contract;
- full suite;
- Treasury/KRX;
- Ruff;
- Ruff format;
- `git diff --check`.

No test deletion or skip inflation.

M12CU baseline:

- focused: 291 passed
- frozen-contract: 200 passed
- full: 4,412 passed / 63 skipped
- Treasury/KRX: 121 passed
- Ruff: PASS
- Ruff format: PASS
- git diff --check: PASS

## 24. Required artifacts

At minimum:

- `source-base-integrity.json`
- `m12cu-pass-a-fixture-binding.json`
- `m12cu-pass-b-failure-reproducer.json`
- `pass-b-capability-contract.json`
- `pass-b-capability-catalog-22.json`
- `pass-b-capability-validator-parity-matrix.json`
- `new-buyer-capability-analysis-22.json`
- `holder-capability-analysis-22.json`
- `overall-capability-analysis-22.json`
- generic capability positive/negative fixtures
- `m12cu-wait-reason-failure-replay.json`
- all 8 regenerated Pass-B internal schemas
- all 8 regenerated Pass-B provider-wire schemas
- all 8 Pass-B prompts/ref catalogs/subject contexts
- `pass-b-provider-dialect-scan-8.json`
- `outbound-pass-b-request-binding-8.json`
- B-only generation binding manifest
- all 8 raw outputs/transport logs where executed
- raw semantic validation artifacts
- `pass-b-call-ledger.json`
- `directional-balance-runtime-22.json`
- `runtime-entry-range-materialization-22.json`
- `new-buyer-consistency-results.json`
- `overall-holder-policy-validation.json`
- `pass-b-only-22-subject-results.json`
- `pass-b-only-output-freeze-manifest.json`
- B-only pre-reference analysis
- target-leak proof
- test/JUnit/logs
- Ruff / format / diff-check
- safety counters
- blocker ledger
- program completion
- REPORT.md
- artifact manifest
- external ZIP SHA sidecar

## 25. Terminal states

Use one:

- `M12CV_PASS_B_ONLY_CONTRACT_CLOSURE_PASS_READY_FOR_FINAL_FRESH_E2E`
- `M12CV_PASS_A_FIXTURE_BINDING_FAILED`
- `M12CV_PASS_B_CAPABILITY_CONTRACT_NOT_CLOSED`
- `M12CV_PROVIDER_WIRE_REQUEST_DRIFT`
- `M12CV_PASS_B_EXECUTION_FAILED`
- `M12CV_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT`

No terminal state authorizes production integration.

## 26. Hard safety

- Pass-A external model calls = 0
- Pass-B external model calls <= 8
- market refresh = 0
- production application/runtime/config behavior changes = 0
- production sends/intents/DB writes = 0
- broker read/order/modify/cancel = 0
- scheduler changes = 0
- main merge = 0
- remote push = 0
- deployment = 0

Return to Chat. Do not automatically execute the final fresh A+B run.
