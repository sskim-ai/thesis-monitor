# Thesis Monitor — M12CQ Two-Pass Archetype/Regime + Entry-Decision Calibration Shadow

## 0. Task identity

Work-instruction filename:

`20260917-m12cq-two-pass-archetype-regime-entry-decision-calibration-shadow.md`

Suggested result bundle:

`thesis-monitor-20260917-m12cq-two-pass-archetype-regime-entry-decision-calibration-shadow-report.zip`

This is a **fresh, shadow-only, two-pass policy calibration experiment** after M12CP.

It is NOT:

- a production Stage-2 policy change;
- a production entry-price deployment;
- a market/fundamental refresh;
- a new Fundamental Core generation;
- a per-ticker calibration task;
- a target-label fitting exercise;
- a production notification/scheduler/broker/persistence task.

Production application/runtime/config behavior changes: **0**.

## 1. Source integrity and exact frozen inputs

Verify first:

### M12CP

- Result ZIP SHA-256:
  `fe63ee201bdb0937a4936af0d89f7013adee0209b3ef01d83d210d0e93456100`
- M12CP artifact manifest: 37 declared payloads; 37/37 hash and size PASS.
- M12CP completion:
  `M12CP_SCENARIO_SOURCE_COVERAGE_INSUFFICIENT_BUT_HISTORICAL_POLICY_READY`
- M12CP implementation:
  `491eaef3172f5234d244f2627a57776528f2768d`
- Required runtime base:
  `831890d1bf0dff303f67a6e0de1403ad3221b5d8`

### Frozen analytical generation

`20260917-m12cm-current-v4-smoke-20260917T062918Z-5c0cb075ce8b`

Use the supplied immutable M12CM shadow input:

- same 22 subjects;
- same US14/KR8 batch topology;
- same accepted Fundamental Core;
- same frozen facts/context;
- no market refresh;
- no source enrichment.

## 2. Carry forward frozen policy

Keep unchanged:

### 2.1 Archetypes

- DURABLE_FRANCHISE
- STRUCTURAL_CYCLICAL_LEADER
- PROFITABLE_PREMIUM_GROWTH
- EXECUTION_DEPENDENT_GROWTH
- MATURE_VALUE_DEFENSIVE
- UNRESOLVED

No ticker/company/country rules.

### 2.2 Three independent decision axes

- Overall: BUY / HOLD / SELL
- New Buyer: ATTRACTIVE / WAIT / AVOID
- Holder: HOLDABLE / REVIEW / REDUCE

`BUY / WAIT / HOLDABLE` is explicitly valid.

Valuation/timing alone does not automatically downgrade Overall.

Valuation alone does not create Holder REVIEW.

### 2.3 Data quality

Missing/provider-limited/unsupported data defaults to confidence/verification impact.

It becomes directional-negative only when an existing canonical claim owns a material negative/disclosure failure.

Unknown itself is not bearish.

### 2.4 Archetype valuation families

- DURABLE_FRANCHISE: safe historical trailing P/E primary.
- STRUCTURAL_CYCLICAL_LEADER: safe historical P/B primary.
- PROFITABLE_PREMIUM_GROWTH: safe historical trailing P/E primary.
- EXECUTION_DEPENDENT_GROWTH: scenario methods required; current M12CP coverage = 0, therefore unresolved.
- MATURE_VALUE_DEFENSIVE: same-tier intersection when two safe methods overlap; one safe primary method may stand alone; non-overlap unresolved.
- UNRESOLVED: unresolved.

No method averaging.

### 2.5 Valuation regime

- CONSERVATIVE -> P25_P50
- BASE -> P50_P75
- PREMIUM -> P75_P90
- UNRESOLVED -> no fundamental option

PREMIUM requires non-price structural improvement evidence.

## 3. Why this shadow is two-pass

The policy must test:

`business/thesis classification independent of current entry price`
then
`current-price/timing judgment`

Therefore Pass A and Pass B are separate model calls with separate model-visible inputs.

Do not combine them back into one inference merely to reduce call count.

Fundamental Core calls remain 0.

Expected shadow calls:

- Pass A: US 5 + KR 3 = 8 calls
- Pass B: US 5 + KR 3 = 8 calls
- total planned shadow model calls = 16

Each call is single-attempt.

## 4. Pass A — price-blind archetype and valuation regime

### 4.1 Model-visible inputs

Pass A may receive only subject-local:

- accepted Fundamental Core business/earnings/cash-flow/competitive/cycle claims;
- eligible non-price canonical evidence;
- data-quality facts needed to judge evidence confidence;
- generic archetype definitions;
- generic valuation-regime definitions.

Pass A must not receive:

- current market price;
- chart/technical values;
- tactical candidate ranges;
- current valuation percentile;
- current P/E/P/B level if it directly reveals the present valuation state;
- precomputed historical candidate price bands;
- distance-to-band;
- New Buyer/Holder prior labels;
- production AI output;
- independent-assistant judgment;
- any target/reference comparison.

Historical valuation *method availability* may be known to the deterministic runtime but must not be model-visible if it exposes price-band values.

### 4.2 Pass-A outputs

For every subject:

- ticker/subject identity;
- `archetype`;
- `archetype_supporting_claim_refs`;
- `valuation_regime_tier`;
- `tier_supporting_claim_refs`;
- `data_quality_effect` under the existing generic shadow policy;
- bounded nonnumeric classification rationale if already supported.

No price, multiple, band, target, tactical, New Buyer or Holder value may appear.

### 4.3 Archetype support

Supporting refs must:

- belong to the same subject/generation;
- be exact registered claim/evidence refs;
- be non-price/non-technical;
- support business quality, profitability, competitive position, cycle/execution characteristics, or maturity.

No identity-name reasoning.

### 4.4 Tier support

Tier supporting refs must come from a deterministic eligible non-price set.

Forbidden:

- current price;
- current multiple/percentile;
- technical support;
- desired New Buyer state;
- prior labels.

`PREMIUM` requires at least one eligible structural-improvement claim/ref.

High valuation itself is not PREMIUM evidence.

If conflicting/insufficient:

`valuation_regime_tier = UNRESOLVED`.

### 4.5 Pass-A schema and validator

Create a new shadow-only versioned contract.

Before any model call:

- recursive response-format schema completeness PASS;
- generic renamed-identity controls PASS;
- current-price leakage scan PASS;
- forbidden target/reference material absent from model input;
- evidence-ref ownership validator PASS on fixtures.

First hard failure stops Pass A. Pass B must not begin unless Pass A is complete 22/22 and frozen.

## 5. Freeze Pass A

After all 8 Pass-A calls:

- validate 22/22;
- freeze raw responses and normalized Pass-A output;
- record whole-batch hashes;
- record archetype/tier distributions;
- record eligible supporting refs;
- prove current-price/technical leakage count = 0.

No post-freeze reference labels may be opened yet.

## 6. Deterministic fundamental-option materialization

Use M12CP's exact shadow-only policy/candidate artifacts.

Inputs:

- frozen Pass-A archetype;
- frozen Pass-A valuation regime tier;
- M12CP safe candidate catalog/policy matrix.

The model does not select or author the fundamental candidate ID.

Runtime returns:

- resolved policy option; or
- UNRESOLVED with canonical reason.

### 6.1 Required generic outcomes

- Durable + tier + safe P/E -> corresponding P/E quantile option.
- Structural cyclical + tier + safe P/B -> corresponding P/B option.
- Profitable growth + tier + safe P/E -> corresponding P/E option.
- Execution-dependent growth -> UNRESOLVED while scenario coverage remains 0.
- Mature value + two safe same-tier methods -> exact intersection if overlapping.
- Mature value + one safe method -> that safe method.
- Mature value + non-overlap -> UNRESOLVED.
- Unresolved archetype/tier -> UNRESOLVED.

No model-authored low/high/refs/status.

### 6.2 Security-basis gate

Preserve M12CP fail-closed results.

For unresolved depositary/security basis such as any subject meeting that generic condition:

- do not materialize per-share historical option from underlying-company metrics;
- do not infer conversion ratio;
- unresolved remains valid.

No hardcoded ticker allowlist.

## 7. Pass B — decision axes and entry timing

Pass B starts only after Pass A + deterministic fundamental materialization is frozen.

### 7.1 Model-visible input

For each subject, Pass B receives:

- original frozen subject evidence required by the existing decision policy;
- frozen Pass-A archetype/tier/data-quality classification;
- deterministic fundamental option or exact unresolved reason;
- current price and as-of;
- exact tactical candidate catalog;
- market/timing context already present in frozen M12CM;
- generic three-axis policy.

Do not show prior production AI or independent-assistant judgments.

### 7.2 Pass-B model outputs

Preserve the existing shadow decision fields required for:

- Overall;
- New Buyer;
- Holder;
- directional balance/reasons;
- tactical candidate choice `candidate_id | UNRESOLVED` where applicable;
- bounded nonnumeric re-evaluation conditions.

Do not let the model author:

- fundamental option ID;
- fundamental low/high;
- preferred low/high;
- distance to band;
- valuation refs;
- technical refs copied from candidate;
- deterministic status/method/combination fields.

For AVOID, no entry price needs to be invented.

## 8. Runtime entry-range materialization after Pass B

Runtime combines:

- deterministic fundamental option;
- model tactical choice;
- canonical tactical catalog;
- current price.

Use the already reviewed M12CN/M12CO combination semantics.

### Fundamental unresolved

- parent entry range remains UNRESOLVED;
- preferred numeric band remains null;
- resolved tactical support may be rendered only as tactical/watch context.

### Fundamental resolved + tactical resolved

Use the existing reviewed overlap/no-overlap rule. Do not average unrelated bands.

### Fundamental resolved + tactical unresolved

Use the reviewed FUNDAMENTAL_ONLY behavior where already allowed.

No arbitrary percentage discount.

## 9. New Buyer consistency hard validation

The model still owns New Buyer judgment, but it must be consistent with the materialized data.

### ATTRACTIVE

Requires:

- resolved fundamental option;
- current price at or below the permitted fundamental high;
- no incompatible severe execution/tactical condition under the existing shadow policy.

If these are not true, ATTRACTIVE fails validation.

### WAIT

Valid when at least one evidence-backed condition holds:

- price above preferred fundamental range;
- fundamental range unresolved;
- tactical timing unfavorable despite intact long-term thesis;
- another existing structured WAIT condition already authorized.

WAIT with a resolved fundamental band must expose the runtime-materialized band.

WAIT with unresolved fundamental valuation must say unresolved rather than invent a price.

### AVOID

May be used for material execution/thesis risk and does not require a resolved fundamental band.

## 10. Overall and Holder policy validation

### Overall

For DURABLE_FRANCHISE and STRUCTURAL_CYCLICAL_LEADER:

- current valuation/tactical timing alone cannot be the sole structured reason for HOLD/SELL;
- HOLD/SELL must cite material thesis/cycle/competitive/earnings/cash-flow evidence.

This does not force BUY.

For EXECUTION_DEPENDENT_GROWTH:

- execution, cash burn, margin, dilution, financial resilience and realized-growth evidence may directly affect Overall.

### Holder

`REVIEW` requires a structured non-valuation reason such as:

- material thesis uncertainty;
- evidence contradiction;
- execution deterioration/risk;
- material disclosure/data condition that is itself business-relevant.

Valuation-expensive alone is insufficient.

Data-quality `CONFIDENCE_ONLY` alone is insufficient.

`REDUCE` requires stronger material negative evidence under the existing generic policy.

No natural-language keyword regex should be the primary owner; use structured reason/evidence classes already present or shadow-only typed additions if required.

## 11. Failure classification

Use structured stage/exception ownership.

Do not infer quota/rate limit/schema errors from arbitrary source-text keywords.

Required categories distinguish:

- schema preflight;
- provider schema rejection;
- transport/network/timeout/quota;
- model raw-contract failure;
- Pass-A semantic failure;
- fundamental materialization failure;
- Pass-B semantic failure;
- decision consistency failure.

No retry.

## 12. Fresh execution rules

Create a new generation ID.

### Pass A

8 calls from call 1.

Only if 8/8 complete and 22/22 valid:

### Pass B

8 calls from call 1 using the frozen Pass-A result.

Hard:

- retry = 0
- repair model = 0
- judge = 0
- fallback model = 0
- schema repair model = 0
- selective rerun = 0
- per-ticker rerun = 0
- prior M12CN partial output reuse = 0
- cross-generation stitching = 0
- post-call hotfix = 0

A hard failure freezes the generation and stops dependent later calls.

## 13. PASS requirements

`M12CQ_TWO_PASS_POLICY_CALIBRATION_SHADOW_PASS_READY_FOR_CHAT_REVIEW`

requires:

### Pass A
- 8/8 calls complete;
- 22/22 valid;
- price/technical leakage = 0;
- target-label leakage = 0;
- evidence ownership PASS.

### Materialization
- 22/22 deterministic fundamental outcomes;
- model-authored fundamental prices = 0;
- arbitrary current-price discount = 0;
- security-basis violations = 0.

### Pass B
- 8/8 calls complete;
- 22/22 valid;
- all three decision axes present;
- New Buyer consistency PASS 22/22;
- holder/overall policy validation PASS;
- runtime entry materialization PASS;
- model-authored deterministic entry metadata = 0.

### Freeze
- complete 22-subject shadow hash freeze before opening references.

Agreement with prior labels is not a PASS criterion.

## 14. Required coverage report

For the frozen 22-subject output report:

- archetype distribution;
- valuation tier distribution;
- archetype × tier matrix;
- overall/new-buyer/holder distributions;
- BUY/WAIT/HOLDABLE count;
- WAIT count;
- fundamental resolved/unresolved;
- resolved price bands by method;
- execution-growth unresolved count;
- tactical resolved/unresolved;
- WAIT with resolved preferred entry count;
- WAIT with unresolved fundamental count;
- ATTRACTIVE consistency cases;
- Holder REVIEW reason classes;
- data-quality effect distribution;
- depositary/security-basis unresolved cases;
- premium-tier support refs and evidence class;
- method-intersection cases.

For each resolved WAIT entry range, export exact:

- current price/as-of;
- preferred low/high;
- distance;
- fundamental method/tier;
- tactical component;
- canonical refs.

## 15. Blind post-freeze comparison

A packaged post-freeze reference archive is supplied.

Before the complete M12CQ shadow output freeze:

- do not extract it;
- do not read its content;
- do not use it in prompts, tests, validators or policy thresholds;
- hash verification only.

After freeze, open it **once** and compare descriptively:

1. M12CM production AI;
2. independent assistant blind judgment;
3. M12CQ shadow.

Report:

- exact 3-axis agreement counts;
- per-axis agreement;
- label distributions;
- differences on the previously highlighted large-cap/core names and execution-growth names;
- whether overall-direction conservatism changed;
- whether Holder REVIEW frequency changed;
- whether New Buyer remains appropriately price-sensitive;
- resolved WAIT price examples;
- remaining unresolved price coverage.

Do not rank one judgment set as ground truth.

No second model call after reveal.

## 16. Production integration remains forbidden

Even after shadow PASS:

- production policy unchanged;
- production Stage-2 v4 unchanged;
- production entry-range schema unchanged;
- no main merge;
- no deployment;
- no scheduler changes;
- no production send/intent/DB mutation;
- no broker read/order/modify/cancel;
- no market refresh.

Return to Chat for policy review.

## 17. Required artifacts

At minimum:

- `source-base-integrity.json`
- `m12cp-policy-input-binding.json`
- `pass-a-price-blind-input-contract.json`
- `pass-a-schema-and-validator.json`
- all 8 Pass-A prompts/schemas/ref catalogs/raw outputs
- `pass-a-call-ledger.json`
- `pass-a-output-freeze-manifest.json`
- `pass-a-22-subject-classification.json`
- `price-technical-target-leak-proof.json`
- `fundamental-option-materialization-22.json`
- `security-basis-gate-results.json`
- `pass-b-input-contract.json`
- `pass-b-schema-and-validator.json`
- all 8 Pass-B prompts/schemas/ref catalogs/raw outputs
- `pass-b-call-ledger.json`
- `pass-b-output-freeze-manifest.json`
- `shadow-22-subject-results.json`
- `runtime-entry-range-materialization-22.json`
- `new-buyer-consistency-results.json`
- `overall-holder-policy-validation.json`
- `entry-range-coverage-and-methods.json`
- `premium-tier-evidence-audit.json`
- `data-quality-effect-analysis.json`
- `post-freeze-three-way-comparison.json`
- `post-freeze-three-way-comparison.md`
- test/JUnit/logs
- Ruff / git diff --check
- `safety-counters.json`
- `complete-blocker-ledger.json`
- `program-completion.json`
- `REPORT.md`
- artifact manifest + external ZIP SHA sidecar.

## 18. Validation

Before model calls run:

- focused no-model contract tests;
- recursive schema completeness for every Pass-A and Pass-B schema template;
- renamed-identity controls;
- materializer tests over all M12CP archetype/tier options;
- New Buyer consistency controls;
- holder/overall generic controls;
- post-freeze reference nonaccess control.

After model execution run relevant:

- focused;
- full;
- frozen contracts;
- Treasury/KRX;
- Ruff;
- `git diff --check`.

No test deletion or skip inflation.

## 19. Terminal states

Use one:

- `M12CQ_TWO_PASS_POLICY_CALIBRATION_SHADOW_PASS_READY_FOR_CHAT_REVIEW`
- `M12CQ_PASS_A_FAILED`
- `M12CQ_FUNDAMENTAL_MATERIALIZATION_FAILED`
- `M12CQ_PASS_B_FAILED`
- `M12CQ_BLINDNESS_OR_TARGET_LEAK_FAILURE`
- `M12CQ_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT`

No result authorizes production integration automatically.
