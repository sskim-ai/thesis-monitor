# Thesis Monitor — M12CR-R1 Typed Data Quality & Security Valuation Basis Ownership Repair

## 0. Task identity

Work-instruction filename:

`20260918-m12cr-r1-typed-data-quality-and-security-valuation-basis-ownership-repair.md`

Suggested result bundle:

`thesis-monitor-20260918-m12cr-r1-typed-data-quality-and-security-valuation-basis-ownership-repair-report.zip`

This is a **no-model, bounded correction to M12CR's deterministic quality/basis ownership layer plus full offline re-proof**.

It is NOT:

- another live/fresh model shadow;
- a re-design of the approved archetype/valuation policy;
- a re-design of the two-pass architecture;
- a market/fundamental refresh;
- a production Stage-2 modification;
- a ticker-specific investment retune;
- a target-label fitting task.

External model calls: **0**.

Production application/runtime/config behavior changes: **0**.

## 1. Exact source state

Verify before work.

### M12CR result

- ZIP SHA-256:
  `f6ca17a87988885bba8cfa6964ac54d026d2296adc536216b7dd64f4012b8acb`
- Artifact manifest:
  84 declared payloads, 84/84 hash and size PASS.
- Work-instruction commit:
  `acb9cfdc`
- Implementation commit:
  `4fbd510d9c9d4c30400d1cd80c3333bc27148555`
- Submitted terminal:
  `M12CR_SHADOW_CONTRACT_PARITY_CLOSED_READY_FOR_FRESH_TWO_PASS_SHADOW`

### M12CP result

- ZIP SHA-256:
  `fe63ee201bdb0937a4936af0d89f7013adee0209b3ef01d83d210d0e93456100`
- Accepted source/basis design includes:
  - depositary basis unresolved count = 3
  - unresolved subjects = SKHY, TSM, WRD
  - underlying metrics copied without verified ratio = 0

### M12CQ result

- ZIP SHA-256:
  `378a3a4a9c1d65255a1baf371daa95dcf3c3f5384af4d04240685f80fc3744ca`

Use the same frozen M12CM generation:

`20260917-m12cm-current-v4-smoke-20260917T062918Z-5c0cb075ce8b`

No source refresh.

## 2. Preserve closed M12CR work

Do not broadly reopen:

- two-pass Pass A / deterministic materialization / Pass B architecture;
- archetype definitions;
- regime tiers;
- archetype valuation-method matrix;
- Overall / New Buyer / Holder independence;
- M12CR's 103-rule inventory structure;
- 16-schema completeness framework;
- historical-failure replay framework;
- model-output surface reduction direction;
- target-leak isolation.

The repair scope is typed quality/basis ownership and all rules directly affected by it.

## 3. Reproduce the Chat-found deterministic overclassification

Using only frozen typed sources, reproduce M12CR's submitted distribution:

- CONFIDENCE_ONLY = 21
- NONE = 1

Then prove why presence of `data_quality_catalog.evidence_refs` is insufficient to infer a limitation.

Required snapshot controls include, but are not limited to:

### SNDK

- financial_quality state = verified_usable
- security identity = verified_non_depositary / verified
- no material disclosure-failure ref

Submitted M12CR runtime effect:
`CONFIDENCE_ONLY`

### TSLA

- financial_quality state = verified_usable
- security identity = verified_non_depositary / verified
- no material disclosure-failure ref

Submitted M12CR runtime effect:
`CONFIDENCE_ONLY`

The repaired deterministic projection must derive the result from typed state/reason semantics, not from ref cardinality.

These ticker controls are **snapshot regression fixtures only**, never production/policy conditions.

## 4. Audit canonical typed quality semantics before coding

Inspect the canonical source owners/history for at least:

- `financial_quality.state`
- `financial_quality.reason_codes`
- source freshness/cadence semantics
- taint/denial semantics
- security_identity identity/verification state
- security_basis eligibility/denial state

Create an explicit mapping table with:

- source field/state
- semantic meaning
- BUSINESS_EVIDENCE_QUALITY impact
- SECURITY_VALUATION_BASIS impact
- whether directional use is allowed
- exact source/code/history evidence

Do not invent mappings based on the current 22 desired outcomes.

Examples to resolve from the actual contracts:

- `verified_usable`
- `caution_usable`
- `denied`
- `unknown`
- `reporting_cadence_exceeded`
- `official_financial_period_unresolved`
- `verified_non_depositary`
- `provider_native_multiple_may_be_eligible`
- `security_share_basis_dependent_valuation_denied`
- `unverified_depositary_evidence_requires_authoritative_resolution`

If a state's semantics are not owned clearly enough, mark it unresolved rather than guessing.

## 5. Split quality ownership into three typed layers

### 5.1 BUSINESS_EVIDENCE_QUALITY

Shadow-only deterministic state.

Purpose:
confidence in operating/financial/business evidence used for business thesis.

At minimum:

- `NONE`
- `CONFIDENCE_ONLY`

The exact mapping comes from section 4.

Rules:

- a normal verified security identity is not a business-quality limitation;
- unresolved security/share conversion alone is not a business-quality limitation;
- ref existence alone is not a limitation;
- genuinely denied/caution/stale/incomplete business evidence may be CONFIDENCE_ONLY according to the canonical contract.

If no applicable business-quality record exists, distinguish:
- legitimately not applicable/clean;
- expected quality evidence absent.

Do not automatically equate absence with NONE or CONFIDENCE_ONLY without proving the source contract.

### 5.2 SECURITY_VALUATION_BASIS

Shadow-only deterministic state.

Purpose:
whether per-share/current-security valuation and preferred-entry materialization are safe.

At minimum:

- `RESOLVED`
- `UNRESOLVED`

Audit generically over all 22, including:
- depositary securities;
- share-basis-dependent valuation denials;
- unknown current-security denominator;
- reporting/trading currency mismatch;
- underlying-security identity gaps.

No ticker allowlist in code.

Rules:

- unresolved basis blocks unsafe per-share candidate materialization;
- unresolved basis may cause fundamental entry range to remain unresolved;
- it may support New Buyer WAIT due unresolved price basis;
- it is **not**, by itself, evidence for Overall HOLD/SELL;
- it is **not**, by itself, evidence for Holder REVIEW/REDUCE;
- it is not directional-negative data quality.

### 5.3 DIRECTIONAL_DISCLOSURE_QUALITY

Keep M12CR's narrow model judgment over explicit material allowlists.

Do not let the model:
- recopy ordinary quality metadata;
- recopy security-basis metadata;
- turn ordinary missing/unknown into directional negative.

## 6. Reconcile M12CP security-basis coverage

M12CP's accepted artifact owns this frozen-snapshot fact:

- depositary affected/unresolved: SKHY, TSM, WRD
- resolved: 0/3

M12CR submitted:

`security-basis-gate-results.json`
with
`depositary_subjects = []`.

Explain the exact reason for the discrepancy.

Then build a generic 22-subject `security_valuation_basis_state` directly from frozen typed facts plus already-authorized deterministic M12CP basis contracts.

Required:

- known unresolved depositary/share-basis conditions cannot silently disappear;
- no underlying per-share metric can be projected without verified conversion/basis;
- source provenance is explicit;
- snapshot-specific expected subject lists may be used only as regression assertions after generic derivation.

If M12CP itself used any ticker-specific heuristic rather than generic evidence, expose that and stop for Chat rather than carrying it forward.

## 7. Rebuild the Pass-A runtime quality projection

Pass A model output remains reduced.

The model must not author ordinary quality metadata.

The Pass-A runtime context should expose only what is semantically needed.

Recommended separation:

- `business_evidence_quality_state`:
  runtime-owned
- `directional_quality_eligible_refs`:
  narrow model-visible allowlist
- `security_valuation_basis_state`:
  not used as business/archetype/regime degradation evidence

Do not leak current price/technical information into Pass A.

For `directional_data_quality_judgment`, preserve the narrow enum/allowlist contract.

## 8. Rebuild Pass-B quality/basis policy validation

Pass B receives deterministic states needed for decision consistency.

Required negative controls:

1. security valuation basis UNRESOLVED as the sole reason for Overall HOLD/SELL -> FAIL.
2. security valuation basis UNRESOLVED as the sole reason for Holder REVIEW/REDUCE -> FAIL.
3. security valuation basis UNRESOLVED + unresolved fundamental price basis -> New Buyer WAIT may PASS.
4. business evidence CONFIDENCE_ONLY as the sole reason for Overall downgrade -> FAIL unless another authorized material thesis reason exists.
5. business evidence CONFIDENCE_ONLY as the sole reason for Holder REVIEW -> FAIL.
6. directional material disclosure condition with eligible refs may affect Overall/Holder under existing policy.

No natural-language keyword heuristic as owner.

## 9. Current-snapshot quality/basis audit

Produce all 22 rows with:

- ticker
- financial-quality typed state/reason codes
- business evidence quality state
- business-quality source refs
- security identity typed state
- security basis typed state
- security valuation basis state
- exact unresolved basis reasons
- directional quality eligible ref counts
- final runtime quality effect used by Pass A/B

Report aggregate distributions separately.

Do **not** collapse business evidence quality and security valuation basis into a single `data_quality_effect`.

Required snapshot sanity controls:

- SNDK and TSLA must not become CONFIDENCE_ONLY solely because verified-clean refs exist.
- M12CP's unresolved depositary basis cannot disappear silently.
- any additional current-security/share-basis unresolved subjects must be surfaced generically.

If these controls conflict with canonical source semantics, report the conflict instead of forcing the expected snapshot result.

## 10. Re-run exhaustive parity closure

Update the M12CR inventory/parity framework only where the split changes rules.

Required:

- semantic-validator rule inventory regenerated;
- every structural rule has upstream enforcement;
- `MISSING_UPSTREAM_ENFORCEMENT = 0`;
- uncovered rule count = 0;
- Pass-A branch coverage complete;
- Pass-B branch coverage complete;
- all 16 future schemas complete and parity-safe;
- recent historical failure replay remains 4/4 caught before inference;
- new quality/basis regression fixtures all caught offline.

Add explicit new failure replay classes:

- clean verified quality ref misclassified solely due ref presence;
- security basis unresolved used as Overall downgrade evidence;
- security basis unresolved used as Holder REVIEW evidence;
- known frozen security-basis gate silently omitted.

## 11. Re-run no-model 22-subject dry materialization

Run the complete future mechanics:

Pass A synthetic valid choices
-> runtime typed quality projection
-> archetype/tier
-> fundamental option materialization with security-basis gate
-> synthetic Pass B branch
-> runtime entry materialization
-> final semantic validation.

No desired per-ticker investment labels.

Required:

- 22/22 mechanical PASS;
- unsafe security-basis valuation projection = 0;
- business/security quality conflation count = 0;
- arbitrary current-price discount = 0;
- production changes = 0.

## 12. Model-output surface

Preserve or further reduce M12CR's model-owned surface:

- Pass A model-owned fields: 9 or fewer
- Pass B model-owned fields: 9 or fewer

Do not reintroduce:
- identity;
- ordinary data-quality metadata;
- security-basis metadata;
- fundamental option numbers/refs;
- entry metadata;
- rule trace;
- valuation-affects metadata

into model ownership.

## 13. Fresh-shadow authorization gate

No model calls in this task.

A fresh two-pass shadow is authorized for recommendation only if:

- typed business quality mapping has no unresolved P0/P1;
- security valuation basis mapping has no unresolved P0/P1;
- M12CP/M12CR basis discrepancy reconciled;
- business/security quality conflation count = 0;
- missing upstream enforcement = 0;
- uncovered semantic rule count = 0;
- all 16 schemas PASS;
- historical failure replay PASS;
- new quality/basis replay PASS;
- 22/22 dry materialization PASS;
- target leak = 0;
- production changes = 0.

## 14. Required artifacts

At minimum:

- `source-base-integrity.json`
- `m12cr-chat-review-reconciliation.json`
- `typed-quality-source-semantics-audit.json`
- `business-evidence-quality-contract.json`
- `security-valuation-basis-contract.json`
- `directional-disclosure-quality-contract.json`
- `m12cp-m12cr-security-basis-discrepancy-analysis.json`
- `quality-and-security-basis-audit-22.json`
- `business-quality-distribution.json`
- `security-valuation-basis-distribution.json`
- `pass-a-quality-projection-contract.json`
- `pass-b-quality-basis-policy-contract.json`
- `semantic-validator-rule-inventory.json`
- `schema-validator-materializer-parity-matrix.json`
- `historical-failure-replay-matrix.json`
- `quality-basis-failure-replay-matrix.json`
- `pass-a-semantic-branch-coverage.json`
- `pass-b-semantic-branch-coverage.json`
- `all-16-schema-completeness-and-parity-scan.json`
- `model-output-surface-reduction-analysis.json`
- `no-model-22-subject-dry-materialization.json`
- exact future schema/prompt/materializer draft hashes
- target-leak proof
- safety counters
- full/focused/frozen/Treasury-KRX test logs and JUnit
- Ruff / format / diff-check
- `complete-blocker-ledger.json`
- `program-completion.json`
- `REPORT.md`
- artifact manifest
- result ZIP SHA sidecar

## 15. Validation baseline

M12CR submitted:

- focused: 230 passed
- frozen-contract: 139 passed
- full: 4,351 passed / 63 skipped
- Treasury/KRX: 121 passed
- Ruff: PASS
- git diff --check: PASS

No test deletion or skip inflation.

## 16. Terminal states

Use one:

- `M12CR_R1_TYPED_QUALITY_AND_SECURITY_BASIS_OWNERSHIP_CLOSED_READY_FOR_FRESH_TWO_PASS_SHADOW`
- `M12CR_R1_TYPED_QUALITY_SEMANTICS_REQUIRE_CHAT`
- `M12CR_R1_SECURITY_BASIS_OWNERSHIP_REQUIRE_CHAT`
- `M12CR_R1_CONTRACT_PARITY_NOT_CLOSED`
- `M12CR_R1_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT`
- `M12CR_R1_OFFLINE_REPAIR_FAILED`

No terminal state authorizes production integration.

## 17. Hard safety

- external model calls = 0
- market refresh = 0
- production runtime/config behavior changes = 0
- production sends/intents/DB writes = 0
- broker read/order/modify/cancel = 0
- scheduler changes = 0
- main merge = 0
- remote push = 0
- deployment = 0

Return to Chat. Do not automatically execute the fresh shadow.
