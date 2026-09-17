# Thesis Monitor — M12CS-R1 Provider Structured-Output Dialect Compatibility Closure

## 0. Task identity

Work-instruction filename:

`20260918-m12cs-r1-provider-structured-output-dialect-compatibility-closure.md`

Suggested result bundle:

`thesis-monitor-20260918-m12cs-r1-provider-structured-output-dialect-compatibility-closure-report.zip`

This is a **no-model, provider-wire schema compatibility repair + full offline re-proof** after M12CS.

It is NOT:

- another live/fresh two-pass shadow;
- an investment-policy redesign;
- an archetype/regime redesign;
- a data-quality/security-basis redesign;
- a valuation-method redesign;
- a prompt-content retune;
- a market/fundamental refresh;
- a production Stage-2 change.

External model calls: **0**.

Production application/runtime/config behavior changes: **0**.

## 1. Exact source state

Verify before work.

### M12CS result

- Result ZIP SHA-256:
  `3ce69abb67fac877f648780420708d2f3bdd18327be658a7e32ae2e09d31f28f`
- Artifact manifest:
  74 declared payloads, 74/74 hash and size PASS.
- Generation:
  `20260918-m12cs-fresh-two-pass-20260917T232635Z-ec0ff0569060`
- Work-instruction commit:
  `06798ddd8caf330c48fea3bf65e13670dca44f3d`
- Implementation:
  `ec0ff0569060dd10542e1942a7c25feb1dd40aa4`
- Terminal:
  `M12CS_PASS_A_FAILED`

### M12CR-R1

- Result ZIP SHA-256:
  `8d62d38c7915ddbbf77e30bffa29509e5eaa14684e507a58027da62ce51571a8`
- Completion:
  `M12CR_R1_TYPED_QUALITY_AND_SECURITY_BASIS_OWNERSHIP_CLOSED_READY_FOR_FRESH_TWO_PASS_SHADOW`
- Implementation:
  `0e96355ad9151344ee30c7e2bfc92bb70be183ec`

### Historical provider-accepted baseline

Use M12CQ result only to establish response-schema dialect compatibility, never as target investment labels.

M12CQ result SHA-256:

`378a3a4a9c1d65255a1baf371daa95dcf3c3f5384af4d04240685f80fc3744ca`

M12CQ had provider/model-successful Pass-A calls before its later local semantic failure.

## 2. Exact M12CS provider failure

Pass-A US batch 01 was the only wrapper attempt.

Raw provider response:

```text
type = invalid_request_error
code = invalid_json_schema
message = Invalid schema for response_format 'codex_output_schema':
          In context=('properties', 'classifications', 'properties', 'CORZ',
                      'anyOf', '0', 'properties',
                      'archetype_supporting_claim_refs'),
          'uniqueItems' is not permitted.
status = 400
```

Required classification:

`PROVIDER_SCHEMA_DIALECT_REJECTED_PRE_INFERENCE`

Counts:

- wrapper attempted: 1
- provider-accepted inference: 0
- completed response: 0
- evaluated subject: 0
- model semantic failure: 0

Do not describe this as a transient transport failure.

## 3. Systematic scope of the defect

Scan the exact 16 M12CS regenerated future schemas.

Expected reproduction:

- response schemas: 16
- schemas containing `uniqueItems`: 16
- total `uniqueItems` occurrences: **494**

The exact first rejected node is only the first provider-discovered instance.

Do not patch one field manually.

Find the canonical shadow schema constructor/projection that introduced `uniqueItems`.

## 4. Preserve the semantic contract

Do not broadly change:

- two-pass architecture;
- Pass-A price blindness;
- archetypes;
- valuation-regime tiers;
- typed business evidence quality;
- security valuation basis;
- directional disclosure quality;
- valuation method policy;
- Overall/New Buyer/Holder semantics;
- deterministic fundamental materialization;
- M12CR-R1 semantic-validator rules.

The provider-wire fix must be semantics-preserving.

## 5. Separate semantic contract from provider-wire schema

Introduce an explicit distinction:

### A. Internal semantic constraints

May include properties that are enforced locally even when the provider dialect cannot express them.

Examples:
- reference uniqueness, if genuinely required;
- cross-field ownership;
- same-subject refs;
- semantic duplicate prevention;
- deterministic metadata rules.

### B. Provider-wire Structured Outputs schema

Must contain only keywords accepted by the current provider Structured Outputs dialect.

The provider-wire schema is what is submitted through `response_format` / `text.format.schema`.

Do not rely on the provider for constraints it does not support.

Create a versioned projection contract:

`INTERNAL_SEMANTIC_SCHEMA -> PROVIDER_WIRE_SCHEMA`

with deterministic output.

## 6. `uniqueItems` repair

Do not simply delete uniqueness semantics.

First inventory every logical model-output field whose expanded per-subject/per-branch schema currently carries `uniqueItems`.

Collapse 494 expanded occurrences into logical field paths.

For each logical field classify:

- `UNIQUENESS_SEMANTICALLY_REQUIRED`
- `UNIQUENESS_NOT_REQUIRED`
- `DETERMINISTIC_OR_NON_MODEL_FIELD`

For fields where uniqueness is required:

- provider-wire schema omits `uniqueItems`;
- local raw/semantic validator rejects exact duplicate elements before downstream use;
- duplicate checking must work for scalar refs and structured values as appropriate.

For fields where uniqueness is not semantically required:

- remove the unsupported keyword with no replacement constraint.

Do not invent a blanket rule if a field's semantic contract does not require uniqueness.

Required negative controls include duplicate:
- archetype supporting claim refs;
- tier supporting claim refs;
- directional quality evidence refs where applicable;
- Pass-B support/contradiction refs;
- tactical/ref choice arrays;
- any other actual set-like model-owned array discovered by inventory.

## 7. Provider dialect compatibility audit

Build a new recursive preflight separate from the existing semantic/schema parity scan.

It must validate every provider-wire schema against the effective OpenAI Structured Outputs subset used by this project.

Reference sources:

1. current official OpenAI Structured Outputs guide;
2. actual M12CS provider error;
3. historically provider-accepted M12CQ schema constructs.

The current official guide states that Structured Outputs supports only a subset of JSON Schema and unsupported strict schemas cause errors.

At minimum enforce:

### Allowed/required structural families used here

- `type`
- `properties`
- `required`
- `additionalProperties: false`
- `items`
- `enum`
- `anyOf`
- `$defs`
- `$ref`
- supported string/number/array constraints actually documented/empirically accepted by the current non-fine-tuned model path.

### Explicitly reject

- `uniqueItems`
- `allOf`
- `not`
- `dependentRequired`
- `dependentSchemas`
- `if`
- `then`
- `else`
- any other keyword outside the project's proven provider dialect.

Do not infer support merely because generic JSON Schema permits a keyword.

Create:

`provider-structured-output-dialect-contract.json`

and:

`all-16-provider-wire-schema-dialect-scan.json`

## 8. Empirical compatibility baseline

Compare the new provider-wire schemas against M12CQ's provider-accepted Pass-A schemas.

Document constructs that were empirically accepted there, including as applicable:

- `const`
- `anyOf`
- `minLength`
- `maxLength`
- `minItems`
- `maxItems`
- `$defs`
- `$ref`
- `additionalProperties: false`

Do not use M12CQ investment labels or outputs as targets.

Required artifact:

`historical-provider-schema-compatibility-baseline.json`

## 9. M12CS failure replay

Feed the exact archived M12CS Pass-A batch-01 schema to the new provider-dialect checker.

Required result:

- FAIL before inference
- rejected keyword includes `uniqueItems`
- all offending paths are enumerated, not just the first provider-reported path

Then feed the projected provider-wire schema.

Required result:

- PASS
- `uniqueItems` count = 0
- unsupported-keyword count = 0

Create:

`m12cs-provider-schema-failure-replay.json`

## 10. All 16 future schemas

Regenerate all:

- Pass A: 8
- Pass B: 8

under the repaired provider-wire projection.

For every schema require:

- provider-dialect scan PASS;
- existing M12CR-R1 structural completeness scan PASS;
- all arrays have `items`;
- strict object property/required consistency PASS;
- semantic branch parity PASS;
- deterministic field leak count = 0.

Required:

`ALL_16_PROVIDER_WIRE_SCHEMA_PASS = true`

No provider/model call.

## 11. Semantic uniqueness re-proof

After removing `uniqueItems` from provider wire format:

- replay valid model-shaped payloads with unique refs -> PASS;
- replay exact duplicate entries in every set-like logical output field -> FAIL locally;
- ensure local duplicate failure is deterministic and has a stable rule ID;
- ensure duplicates cannot alter runtime materialization or evidence weighting.

Update the semantic-validator inventory/parity matrix only where needed.

Required:

`provider_keyword_removed_semantic_uniqueness_preserved = true`

## 12. M12CR-R1 full contract preservation

Re-run the closed offline proof:

- typed business-quality mapping;
- security valuation basis mapping;
- directional quality allowlist;
- M12CP basis regression;
- historical M12CN/R1/R2/M12CQ failure replay;
- quality/basis failure replay;
- Pass-A branch coverage;
- Pass-B branch coverage;
- 22/22 no-model dry materialization;
- target/price leak proof.

Required:
- missing upstream semantic enforcement = 0
- uncovered rule count = 0
- business/security conflation = 0
- unsafe security valuation projection = 0

Do not weaken semantic validators to accommodate provider limitations.

## 13. Frozen-contract versioning for the next run

The M12CR-R1 **semantic policy** remains frozen, but the provider-wire schema hashes necessarily change.

Produce two independent freeze manifests:

### Semantic contract freeze

Must prove policy/validator/materializer semantics are unchanged except explicit local duplicate enforcement replacing provider `uniqueItems`.

### Provider-wire contract freeze

Contains new hashes for:
- all 8 Pass-A provider schemas;
- all 8 Pass-B provider schemas;
- provider dialect checker/projection code.

Future live shadow must bind to both manifests.

Do not pretend the old provider-schema hashes are still identical.

## 14. Reporting repair

Fix shadow-only reporting so:

- call ledger causal category:
  `PROVIDER_SCHEMA_DIALECT_REJECTED_PRE_INFERENCE`
- top-level blocker ledger uses the same causal category;
- underlying safe wrapper error may remain recorded separately as `OTHER_TRANSPORT_FAILURE`.

Fix REPORT boilerplate:
if final freeze/reference reveal was not reached, say:

`post-freeze reference semantic access = 0 / NOT_REACHED`

Do not state that prior judgments "were opened after freeze" when no final freeze occurred.

No production transport taxonomy change.

## 15. No model/provider calls

This task must make:

- external model calls = 0
- provider schema submission attempts = 0

A static compatibility closure is required before another paid/remote inference run.

## 16. Fresh-shadow authorization gate

Return ready for a later fresh two-pass run only if:

- archived M12CS schema fails the new provider dialect scan offline;
- repaired 16/16 provider-wire schemas PASS;
- unsupported provider keyword count = 0;
- `uniqueItems` provider-wire count = 0;
- required semantic uniqueness is locally enforced;
- M12CR-R1 full semantic proof remains closed;
- 22/22 dry materialization PASS;
- target/price leak = 0;
- production changes = 0.

## 17. Required artifacts

At minimum:

- `source-base-integrity.json`
- `m12cs-chat-review-reconciliation.json`
- `provider-structured-output-dialect-contract.json`
- `provider-schema-keyword-inventory.json`
- `unique-items-logical-field-inventory.json`
- `provider-wire-schema-projection-contract.json`
- `historical-provider-schema-compatibility-baseline.json`
- `m12cs-provider-schema-failure-replay.json`
- `all-16-provider-wire-schema-dialect-scan.json`
- all 16 projected provider-wire schemas
- `semantic-uniqueness-local-enforcement.json`
- duplicate positive/negative fixtures
- updated semantic-validator rule inventory
- updated schema/validator/materializer parity matrix
- M12CR-R1 quality/basis regression reproof
- historical failure replay reproof
- Pass-A branch coverage
- Pass-B branch coverage
- 22-subject dry materialization
- semantic contract freeze manifest
- provider-wire contract freeze manifest
- exact projector/checker source hashes
- test/JUnit/logs
- Ruff / format / diff-check
- safety counters
- complete blocker ledger
- program completion
- REPORT.md
- artifact manifest
- result ZIP SHA sidecar

## 18. Validation baseline

M12CS pre-call baseline:

- focused: 261 passed
- frozen-contract: 170 passed
- Ruff: PASS
- Ruff format: PASS
- git diff --check: PASS

M12CR-R1 prior full baseline:

- full: 4,375 passed / 63 skipped
- Treasury/KRX: 121 passed

Run:
- new provider-dialect focused tests;
- full focused shadow-contract tests;
- full suite;
- frozen-contract;
- Treasury/KRX;
- Ruff;
- Ruff format;
- git diff --check.

No test deletion or skip inflation.

## 19. Terminal states

Use one:

- `M12CS_R1_PROVIDER_DIALECT_COMPATIBILITY_CLOSED_READY_FOR_FRESH_TWO_PASS_SHADOW`
- `M12CS_R1_PROVIDER_DIALECT_GAP_REQUIRES_CHAT`
- `M12CS_R1_SEMANTIC_UNIQUENESS_GAP_REQUIRES_CHAT`
- `M12CS_R1_CONTRACT_PARITY_NOT_CLOSED`
- `M12CS_R1_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT`
- `M12CS_R1_OFFLINE_REPAIR_FAILED`

No terminal state authorizes production integration.

## 20. Hard safety

- external model calls = 0
- provider schema submission attempts = 0
- market refresh = 0
- production runtime/config behavior changes = 0
- production sends/intents/DB writes = 0
- broker read/order/modify/cancel = 0
- scheduler changes = 0
- main merge = 0
- remote push = 0
- deployment = 0

Return to Chat. Do not automatically execute the next fresh shadow.
