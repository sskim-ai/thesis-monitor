# Thesis Monitor — M12CR Exhaustive Shadow Contract Parity & Deterministic Ownership Closure

## 0. Task identity

Work-instruction filename:

`20260917-m12cr-exhaustive-shadow-contract-parity-and-deterministic-ownership-closure.md`

Suggested result bundle:

`thesis-monitor-20260917-m12cr-exhaustive-shadow-contract-parity-and-deterministic-ownership-closure-report.zip`

This is a **no-model, exhaustive contract-parity and ownership closure task** after M12CQ.

It is specifically intended to stop the recent cycle of:

`one fresh shadow -> one newly discovered downstream shape mismatch -> one narrow repair -> another fresh shadow`

It is NOT:

- another fresh model run;
- a production policy deployment;
- an investment-policy redesign;
- a valuation-method redesign;
- a market/fundamental refresh;
- a per-ticker tuning task;
- a target-label fitting task.

External model calls: **0**.

Production application/runtime/config behavior changes: **0**.

## 1. Source integrity

Verify first.

### M12CQ result

- ZIP SHA-256:
  `378a3a4a9c1d65255a1baf371daa95dcf3c3f5384af4d04240685f80fc3744ca`
- Artifact manifest:
  74 declared payloads, 74/74 hash and size PASS.
- Generation:
  `20260917-m12cq-two-pass-shadow-20260917T143739Z-862c972c6e4c`
- Work-instruction commit:
  `8f75c719e5f10c50d3a57a574fe7d140d9009e14`
- Implementation commit:
  `862c972c6e4c56c30d28596e286be74b2ce55b88`
- Terminal:
  `M12CQ_PASS_A_FAILED`

Also inspect the packaged historical result bundles for M12CN, M12CN-R1, M12CN-R2, M12CO and M12CP.

Use them as contract/ownership history only, never as desired label targets.

## 2. Preserve closed policy decisions

Do not reopen these unless direct contradictory code/history evidence is found.

### Two-pass architecture

Pass A:
- price-blind business/archetype/valuation-regime classification.

Deterministic materialization:
- fundamental option from archetype + regime + M12CP policy.

Pass B:
- current price/timing + Overall/New Buyer/Holder.

### Archetypes

- DURABLE_FRANCHISE
- STRUCTURAL_CYCLICAL_LEADER
- PROFITABLE_PREMIUM_GROWTH
- EXECUTION_DEPENDENT_GROWTH
- MATURE_VALUE_DEFENSIVE
- UNRESOLVED

### Regime tiers

- CONSERVATIVE -> P25_P50
- BASE -> P50_P75
- PREMIUM -> P75_P90
- UNRESOLVED -> no option

### Three axes

- Overall: BUY / HOLD / SELL
- New Buyer: ATTRACTIVE / WAIT / AVOID
- Holder: HOLDABLE / REVIEW / REDUCE

`BUY / WAIT / HOLDABLE` remains valid.

### Valuation policy

Preserve the M12CP archetype-method matrix.

### Data-quality principle

Missing/provider-limited/unsupported information normally changes confidence/verification, not direction.

Directional data-quality effect requires exact material evidence.

Unknown alone is not bearish.

## 3. Exact M12CQ failure to reproduce offline

M12CQ Pass-A US batch 04 returned valid structured output.

SNDK and TSLA each emitted:

- `data_quality_effect = NONE`
- `data_quality_reason_class = NOT_APPLICABLE`
- `data_quality_reason = null`
- non-empty `data_quality_evidence_refs`

Semantic validator returned:

- `SNDK:none_data_quality_shape_invalid`
- `TSLA:none_data_quality_shape_invalid`

TSM in the same batch passed.

The current response schema allowed this shape.

Required first fixture:

`NONE + NOT_APPLICABLE + null reason + nonempty refs`

must reproduce the current validator failure offline.

Do not relax the validator just to accept the archived output.

## 4. Exhaustive model-output field ownership inventory

Inventory **every field** in:

- Pass-A model response;
- deterministic fundamental materialization;
- Pass-B model response;
- runtime entry-range materialization;
- final shadow 22-subject result.

Classify each field as exactly one:

- `MODEL_JUDGMENT`
- `MODEL_JUDGMENT_WITH_ENUMERATED_REF_SELECTION`
- `DETERMINISTIC_SOURCE_PROJECTION`
- `DETERMINISTIC_DERIVED_FIELD`
- `DETERMINISTIC_POLICY_MATERIALIZATION`
- `MODEL_PROSE_WITH_HARD_NONNUMERIC_LIMITS`
- `UNRESOLVED_REQUIRES_CHAT`

For every deterministic field still authored by the model, either:

A. move ownership to deterministic runtime in shadow code; or  
B. prove why true model judgment is required.

Do not change production code.

## 5. Exhaustive semantic-validator rule inventory

Parse/inspect the actual Pass-A and Pass-B semantic validators.

Enumerate every rule, including:

- enum/value rules;
- cross-field shape rules;
- ref ownership and same-subject rules;
- empty/non-empty array rules;
- nullable/non-nullable dependencies;
- premium-tier support rules;
- data-quality effect/reason/ref rules;
- archetype support rules;
- deterministic option consistency;
- tactical candidate selection;
- New Buyer consistency;
- Overall policy constraints;
- Holder policy constraints;
- security-basis gates;
- model-authored deterministic metadata prohibitions.

Create:

`semantic-validator-rule-inventory.json`

Each rule must have a stable rule ID.

## 6. Rule-to-enforcement parity matrix

For every validator rule classify its upstream enforcement:

- `SCHEMA_STRUCTURAL`
- `DETERMINISTIC_MATERIALIZER`
- `PROMPT_ONLY`
- `CROSS_REFERENCE_VALIDATOR_ONLY`
- `MISSING_UPSTREAM_ENFORCEMENT`

Target state before another model run:

### Structural shape rules

Every rule that can be expressed structurally in JSON Schema must be structurally enforced.

Examples:

- NONE data-quality shape;
- CONFIDENCE_ONLY shape;
- directional data-quality shapes;
- nullable/non-null dependencies;
- zero/nonzero arrays;
- allowed status combinations.

Do not leave these only to prompt text.

### Deterministic facts

Fields that can be derived from frozen canonical catalogs must not be model-authored merely so a validator can compare them later.

### Cross-reference rules

Rules that inherently require runtime catalogs may remain validator-owned, but must have exhaustive synthetic positive/negative fixtures.

Required artifact:

`schema-validator-materializer-parity-matrix.json`

Pass criterion:

`MISSING_UPSTREAM_ENFORCEMENT = 0`

for all structural/model-shape rules.

## 7. Data-quality ownership redesign audit

Do not assume the current model-owned shape is correct.

Audit the current canonical data-quality catalog and code/history.

Preferred hypothesis to prove or reject:

### Runtime-owned base state

Runtime can deterministically own:

- whether a canonical quality limitation exists;
- exact quality source refs;
- provider/staleness/security-basis reason class where already typed;
- NONE vs CONFIDENCE_ONLY when no discretionary business judgment is required.

### Separate directional judgment

If a material disclosure/data condition can itself be business-directional, expose a **separate** narrow model judgment only over the explicitly allowed material refs.

Do not make the model recopy normal quality refs simply to say `NONE`.

If code/history supports this split, draft/implement it in shadow only.

If model ownership must remain, create a discriminated schema:

#### NONE
- reason class = NOT_APPLICABLE
- reason = null
- refs = empty

#### CONFIDENCE_ONLY
- reason class in allowed non-directional classes
- nonempty exact refs
- nonnull bounded reason

#### DIRECTIONAL_NEGATIVE
- material-disclosure reason class
- nonempty refs from the directional allowlist only
- nonnull reason

#### DIRECTIONAL_POSITIVE
- evidenced-quality-improvement class
- nonempty refs from the positive-quality allowlist only
- nonnull reason

Do not let schema accept a shape validator rejects.

## 8. Replay every recent failure class offline

Create immutable negative fixtures from archived outputs/contracts for at least:

### M12CN
- WAIT + tactical NOT_APPLICABLE

### M12CN-R1
- array schema missing `items`

### M12CN-R2
- unresolved fundamental + forbidden model-authored metadata

### M12CQ
- data-quality NONE + nonempty refs

For each historical failure, prove:

1. the new no-model preflight catches it **before provider inference**; or
2. deterministic ownership makes that malformed model shape impossible.

Create:

`historical-failure-replay-matrix.json`

No historical desired direction labels may be used.

## 9. Pass-A branch coverage

Build synthetic positive and negative fixtures covering every semantic branch, not just happy paths.

At minimum cover all combinations that are semantically meaningful for:

- all archetype enum values;
- all valuation-regime tiers;
- PREMIUM with valid structural support;
- PREMIUM without structural support;
- UNRESOLVED tier support shape;
- all data-quality effect branches;
- confidence values;
- valid/invalid claim ownership;
- same-subject/cross-subject refs;
- empty/nonempty supporting refs;
- exact ticker/order/identity.

Do not require combinatorial explosion of irrelevant independent fields.

Use **rule/branch coverage**, not brute-force Cartesian multiplication.

Required artifact:

`pass-a-semantic-branch-coverage.json`

All validator rules must be hit by at least one positive or negative fixture as appropriate.

## 10. Pass-B preemptive branch coverage

Pass B has not executed in M12CQ. Do not wait for live model calls to discover its first structural mismatch.

Before any future inference, exhaustively exercise the Pass-B validator and schema using synthetic fixtures for:

- Overall BUY/HOLD/SELL;
- New Buyer ATTRACTIVE/WAIT/AVOID;
- Holder HOLDABLE/REVIEW/REDUCE;
- resolved/unresolved fundamental option;
- resolved/unresolved tactical choice;
- ATTRACTIVE eligibility;
- WAIT with price above band;
- WAIT with unresolved fundamental;
- WAIT with tactical timing condition;
- AVOID without price band;
- holder REVIEW with valid thesis-relevant reason;
- holder REVIEW with valuation-only reason -> fail;
- durable/structural Overall downgrade with valuation-only reason -> fail;
- execution-growth Overall deterioration with valid execution evidence;
- data-quality CONFIDENCE_ONLY not used as sole holder/overall negative;
- security-basis unresolved;
- cross-ticker candidate/ref failures;
- model-authored deterministic price/ref/status failures.

Required:

`pass-b-semantic-branch-coverage.json`

No provider call.

## 11. Generate and scan all 16 future response schemas offline

Using the exact frozen 22-subject topology and future shadow contract:

- generate 8 Pass-A schemas;
- generate 8 Pass-B schemas.

For every schema recursively check:

- arrays all have valid `items`;
- strict object property/required consistency;
- discriminated union branch completeness;
- no branch permits an explicitly validator-invalid structural state;
- dynamic per-batch enum/ref injection preserves all constraints.

Required:

`all-16-schema-completeness-and-parity-scan.json`

All 16 must PASS before a future shadow is authorized.

## 12. Model-vs-deterministic boundary minimization

Review the full new shadow contract with a bias toward minimizing model-authored deterministic metadata.

Especially inspect:

- data-quality refs/reason classes;
- fundamental option IDs;
- price/low/high/distance;
- valuation method;
- tactical candidate metadata;
- entry statuses;
- exact source refs that can be projected from selected IDs;
- identity/generation/date fields.

The model should preferably author only:

- true business/archetype/regime judgment;
- genuine decision axes;
- small enumerated choices where judgment is necessary;
- bounded rationale/re-evaluation prose;
- exact supporting claim selections where semantic judgment matters.

Required:

`model-output-surface-reduction-analysis.json`

Report before/after model-owned field counts.

## 13. No-model 22-subject dry materialization

Using the frozen 22 contexts and synthetic valid model choices, exercise the full deterministic pipeline without calling a model:

Pass A normalized choice  
-> fundamental option materialization  
-> synthetic Pass-B valid branch  
-> runtime entry-range materialization  
-> final semantic validation.

Use multiple generic branch scenarios sufficient to hit all rules.

Do not synthesize or record desired investment labels per ticker.

This is contract mechanics only.

## 14. No target leakage

Prior production AI, independent assistant judgment and post-freeze three-way comparison remain forbidden as preflight targets.

They are unnecessary in M12CR.

Do not open sealed verdict material.

Historical failed model outputs may be read only for **shape/contract failure replay**, not their investment labels.

Required leak count: 0.

## 15. Production boundary

Expected application/runtime/config source changes: 0.

Allowed:
- shadow scripts;
- shadow schemas;
- shadow validators/materializers;
- tests;
- audit tooling;
- documentation.

If the repair requires a production application file, stop and return:

`M12CR_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT`

Do not proceed silently.

## 16. Validation

Run:

- new exhaustive parity tests;
- focused M12CN/M12CO/M12CP/M12CQ shadow-contract tests;
- full suite;
- frozen-contract suite;
- Treasury/KRX;
- Ruff;
- Ruff format check;
- `git diff --check`.

No test deletion.

No skip inflation.

Report rule/branch coverage separately from ordinary pytest counts.

## 17. Fresh-shadow authorization gate

Do **not** run a model in this task.

A later fresh shadow may be recommended only if all are true:

- structural validator rules missing upstream enforcement = 0;
- all recent historical failure fixtures caught offline;
- Pass-A semantic rule coverage complete;
- Pass-B semantic rule coverage complete;
- all 16 generated schemas pass completeness/parity;
- deterministic ownership audit has no unresolved P0/P1;
- target leakage = 0;
- production changes = 0.

If so return:

`M12CR_SHADOW_CONTRACT_PARITY_CLOSED_READY_FOR_FRESH_TWO_PASS_SHADOW`

Otherwise return the exact unresolved contract gap.

## 18. Required artifacts

At minimum:

- `source-base-integrity.json`
- `m12cq-failure-reproducer.json`
- `semantic-validator-rule-inventory.json`
- `entry-and-decision-field-ownership-inventory.json`
- `schema-validator-materializer-parity-matrix.json`
- `data-quality-ownership-audit.json`
- `data-quality-shadow-contract.json`
- `historical-failure-replay-matrix.json`
- `pass-a-semantic-branch-coverage.json`
- `pass-b-semantic-branch-coverage.json`
- `all-16-schema-completeness-and-parity-scan.json`
- `model-output-surface-reduction-analysis.json`
- `no-model-22-subject-dry-materialization.json`
- exact future Pass-A and Pass-B schema/prompt/materializer draft sources and hashes
- generic fixtures
- target-leak proof
- test/JUnit/logs
- rule coverage summary
- Ruff / format / diff-check
- `safety-counters.json`
- `complete-blocker-ledger.json`
- `program-completion.json`
- `REPORT.md`
- artifact manifest
- external result ZIP SHA sidecar.

## 19. Terminal states

Use one:

- `M12CR_SHADOW_CONTRACT_PARITY_CLOSED_READY_FOR_FRESH_TWO_PASS_SHADOW`
- `M12CR_MODEL_DETERMINISTIC_OWNERSHIP_GAP_REQUIRES_CHAT`
- `M12CR_PASS_A_CONTRACT_PARITY_NOT_CLOSED`
- `M12CR_PASS_B_CONTRACT_PARITY_NOT_CLOSED`
- `M12CR_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT`
- `M12CR_OFFLINE_CONTRACT_AUDIT_FAILED`

No state authorizes production integration.

## 20. Hard safety

- external model calls = 0;
- market refresh = 0;
- production runtime/config changes = 0;
- production sends/intents/DB writes = 0;
- broker read/order/modify/cancel = 0;
- scheduler changes = 0;
- main merge = 0;
- remote push = 0;
- deployment = 0.

Return to Chat. Do not automatically run the next fresh shadow.
