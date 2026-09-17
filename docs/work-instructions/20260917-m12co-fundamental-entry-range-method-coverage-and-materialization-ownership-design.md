# Thesis Monitor — M12CO Fundamental Entry Range Method Coverage & Materialization Ownership Design

## 0. Task identity

Work-instruction filename:

`20260917-m12co-fundamental-entry-range-method-coverage-and-materialization-ownership-design.md`

Suggested result bundle:

`thesis-monitor-20260917-m12co-fundamental-entry-range-method-coverage-and-materialization-ownership-design-report.zip`

This is a **no-model, shadow-policy design + deterministic candidate-builder coverage task** following M12CN-R2.

It is NOT:

- another policy-calibration model run;
- a production Stage-2 change;
- a production valuation-policy cutover;
- a market refresh;
- a per-ticker target-price task;
- an order/stop/position-sizing task;
- a deployment/scheduler/notification task.

External model calls: **0**.

Production application/runtime/config behavior changes: **0**.

## 1. Exact source state

Verify before work.

### M12CN-R2 result

- ZIP SHA-256:
  `5f26ad263cf29ef5a3b18c856c6eafc7b74894367e6444e868014dff304c8b37`
- Artifact manifest:
  94 declared payloads, 94/94 hash and size PASS.
- Required runtime base:
  `831890d1bf0dff303f67a6e0de1403ad3221b5d8`
- R2 harness commit:
  `c4cfb0f2c1ed4326587fac0c493a463beeb2bd0b`
- R2 terminal:
  `M12CN_R2_POLICY_CALIBRATION_SHADOW_FAILED`
- Frozen M12CM generation:
  `20260917-m12cm-current-v4-smoke-20260917T062918Z-5c0cb075ce8b`

Use only the frozen R2/M12CM subject contexts and canonical evidence in the source package.

Do not refresh market or fundamental data.

## 2. Carry forward closed shadow findings

Freeze:

1. archetype taxonomy and evidence-based, identity-generic classification principles;
2. independence of Overall / New Buyer / Holder;
3. `BUY / WAIT / HOLDABLE` as a valid combination;
4. valuation alone does not force Holder REVIEW;
5. data-quality limitation defaults to confidence-only unless the underlying missing/disclosure condition is itself material negative evidence;
6. WAIT means entry-price/timing analysis is applicable;
7. tactical support alone cannot become fundamental fair-entry value;
8. arbitrary current-price discounts are forbidden;
9. response-format schema completeness repair is closed at R2: 8/8 repaired schemas passed; provider schema rejection = 0.

Do not rerun the model to re-prove these in M12CO.

## 3. Exact R2 semantic mismatch to close by ownership, not validator relaxation

R2 US batch 03 generated valid provider output but failed semantic validation for:

- MU: `unresolved_fundamental_metadata_present`
- SKHY: `unresolved_fundamental_metadata_present`

Observed R2 combination:

- parent `ENTRY_RANGE_UNRESOLVED`
- fundamental band `UNRESOLVED`
- fundamental candidate ID/numeric/evidence refs empty
- tactical band `RESOLVED`
- preferred entry numeric fields null
- `valuation_basis_refs` populated
- explanatory `assumptions` populated

Passing unresolved-fundamental R2 rows used empty `valuation_basis_refs` and empty `assumptions`, while unresolved reasons remained in `unresolved_inputs` / `re_evaluate_conditions`.

Do not weaken `unresolved_fundamental_metadata_present`.

Instead audit semantic ownership of every entry-range field.

## 4. Entry-range semantic ownership audit

Classify every current entry-range output field as exactly one of:

- `MODEL_JUDGMENT`
- `DETERMINISTIC_CATALOG_PROJECTION`
- `DETERMINISTIC_DERIVED_FIELD`
- `MODEL_PROSE_WITH_HARD_NONNUMERIC_LIMITS`
- `UNRESOLVED_REQUIRES_CHAT`

The audit must use the current catalog builder, semantic validator, prompt/schema, downstream consumers and existing tests.

Expected hypothesis to prove or reject:

### 4.1 Model-owned choices

For WAIT, the model should decide only meaningful choices such as:

- whether a supplied **fundamental candidate/option ID** is appropriate, or unresolved;
- which supplied tactical candidate ID is most relevant, or tactical unresolved;
- concise nonnumeric re-evaluation prose;
- archetype/axes/thesis/data-quality judgments already in the shadow policy.

### 4.2 Runtime-owned projection

Once IDs/status choices are known, runtime should materialize from the canonical catalog:

- parent entry status;
- fundamental/tactical component status;
- current price/date/ref;
- low/high/currency;
- preferred low/high;
- signed distance;
- method;
- combination rule;
- valuation refs;
- technical refs;
- option/candidate IDs;
- exact catalog assumptions;
- exact unresolved reason strings.

The model must not recopy or invent those deterministic fields.

For a WAIT row with no usable fundamental candidate:

- fundamental component becomes runtime-owned UNRESOLVED;
- valuation refs and option assumptions are empty unless an actual catalog option owns them;
- exact catalog unresolved reason is injected deterministically;
- tactical candidate may still be separately selected/materialized;
- preferred/fair-entry numeric fields remain null.

For non-WAIT:

- entry-range NOT_APPLICABLE structure is materialized deterministically;
- the model should not author a parallel zero-filled object if an existing internal adapter can own it safely.

Do not implement this hypothesis until code/history confirms it. If a field has genuine model-owned semantics, document why.

## 5. Fix R2 failure-category reporting

The R2 ledger incorrectly labels batch 03 `RATE_LIMIT_OR_QUOTA` although a full model output exists and the actual failure is local semantic validation.

Repair **shadow harness/reporting only** so failure classification comes from structured execution stage/exception, not keyword matches in full transport text.

Required replay control:

- R1 provider 400 invalid schema -> `SCHEMA_REJECTED_PRE_INFERENCE`
- R2 batch 03 -> `SEMANTIC_VALIDATION_FAILED`
- unrelated source text containing `rate limit`, `quota`, or numeric `429` -> must not alter failure category.

No production transport taxonomy change.

## 6. Fundamental entry candidate coverage: current baseline

R2 catalog coverage is:

- subject count: 22
- tactical candidate subject count: 22
- fundamental candidate subject count: **0**
- resolved option subject count: **0**

This means current WAIT price output cannot provide evidence-backed fundamental ranges regardless of prompt quality.

M12CO must address **candidate construction coverage**, not force a final target price.

## 7. Candidate method families to audit

Use only existing canonical facts. No new external source.

For every method, export:

- exact formula;
- exact required refs;
- denominator/share/currency/basis constraints;
- history-quality thresholds;
- profitability constraints;
- allowed/forbidden archetype considerations;
- low/high derivation;
- reason the result is an **entry candidate**, not a price target;
- whether method is arithmetically feasible;
- whether method is economically suitable or still requires Chat policy selection.

### 7.1 Historical trailing-PE quantile bands

Candidate arithmetic where all required conditions hold:

`candidate_price = positive TTM EPS × historical trailing-PE quantile`

Evaluate, separately:

- P25–P50
- P50–P75
- P75–P90

Requirements include:

- TTM EPS > 0;
- same-security/share/currency basis;
- historical PE `history_quality = high`;
- sufficient observation/coverage;
- exact P25/P50/P75/P90 values present.

Do not use PE when earnings are zero/negative or source basis is unsafe.

These bands are diagnostic candidates. M12CO does not decide which percentile band is the final archetype policy.

### 7.2 Historical P/B quantile bands

Where book basis is directly comparable and BVPS > 0:

`candidate_price = BVPS × historical P/B quantile`

Evaluate:

- P25–P50
- P50–P75
- P75–P90

Require exact current-security/share/currency basis, high-quality history and source refs.

Do not assume P/B is economically suitable merely because arithmetic is possible.

### 7.3 Forward book variants

Audit whether `modeled_forward_book` can safely pair with the historical P/B distribution.

If forward book/share/currency basis and source semantics are not demonstrably comparable, classify:

`FORWARD_BOOK_HISTORICAL_PB_BASIS_UNRESOLVED`

and do not emit a candidate.

### 7.4 Forward EPS × historical trailing PE

Do **not** silently combine forward EPS with a historical trailing-PE distribution.

Allow only if an explicit existing source/contract establishes the metric-basis comparability.

Otherwise classify:

`FORWARD_EPS_HISTORICAL_TRAILING_PE_BASIS_MISMATCH`

and emit no candidate.

### 7.5 Execution-dependent growth methods

Audit existing frozen facts for safe availability of:

- EV/Sales;
- EV/Gross Profit;
- EV/EBITDA;
- revenue/gross-profit scenario inputs;
- normalized future EBITDA;
- FCF scenario/cash-runway/diluted-share inputs.

If absent, record method coverage gaps.

Do not substitute P/B merely because the company is loss-making.

Do not invent future revenue/margins.

## 8. Archetype-policy applicability matrix — design only

Create a generic matrix, not ticker rules.

At minimum examine:

- `DURABLE_FRANCHISE`
- `STRUCTURAL_CYCLICAL_LEADER`
- `PROFITABLE_PREMIUM_GROWTH`
- `EXECUTION_DEPENDENT_GROWTH`
- `MATURE_VALUE_DEFENSIVE`
- `UNRESOLVED`

For each candidate method family state:

- arithmetically possible?
- generally economically meaningful?
- conditionally meaningful?
- forbidden?
- what additional evidence is required?

Do not hardcode company names.

Do not decide one final method merely because it agrees with prior human judgment.

## 9. Method disagreement is evidence, not something to average away

For each subject with more than one safe candidate family:

- export every candidate band;
- calculate overlap/non-overlap;
- classify disagreement magnitude;
- show current price only as context;
- never average PE and P/B bands into one target;
- never choose the band closest to current price;
- never choose the band closest to prior human/AI judgment.

Required status examples:

- `METHODS_OVERLAP`
- `METHODS_DIVERGE`
- `SINGLE_METHOD_ONLY`
- `NO_SAFE_FUNDAMENTAL_METHOD`

This is crucial for structural rerating cases where PE and P/B may imply very different entry ranges.

## 10. Historical-regime / structural-rerating caution

Historical multiple distributions are descriptive, not automatically normative.

For high-quality franchises or structural cyclical leaders, current business economics may differ materially from the old regime.

Therefore M12CO must not convert:

`historical percentile band`

into:

`true fair value`

without a later explicit policy decision.

Export diagnostics for:

- current percentile;
- historical P25/P50/P75/P90;
- current profitability/earnings state;
- evidence of structural thesis change;
- whether a premium-band candidate exists;
- whether PE/PB methods conflict.

This lets Chat decide whether durable/cyclical leaders should use mid or premium bands.

## 11. Current-price discount prohibition

Candidate generation may **never** use:

- current price × 0.9;
- current price × 0.8;
- arbitrary “10–20% pullback”;
- chart support as a fundamental fair-value range;
- a band reverse-engineered to match a desired label.

Current price is used only for:

- signed distance after candidate generation;
- descriptive positioning;
- no-arbitrage sanity checks if already canonical.

Required:

`ARBITRARY_CURRENT_PRICE_DISCOUNT_COUNT = 0`

## 12. Shadow-only deterministic catalog builder

After the audit, implement a **shadow-only** deterministic candidate builder if and only if each method's arithmetic/source contract is proven.

It may create multiple candidate objects per subject.

Each candidate must include:

- candidate ID derived from canonical inputs/method;
- method family/version;
- low/high/currency;
- exact source refs;
- exact quantiles/denominator values;
- allowed/conditional archetypes;
- quality state;
- assumptions owned by the method;
- disqualifying reasons if not eligible.

Do not choose the final preferred option in M12CO.

Do not alter production valuation or Stage-2 code.

Expected application source changes: 0.

## 13. Entry-selection/materialization draft contract

Produce a versioned **draft shadow contract** for the next model phase, but do not call a model.

Preferred shape, subject to the ownership audit:

For WAIT model output:

- `fundamental_choice = candidate_id | UNRESOLVED`
- `tactical_choice = candidate_id | UNRESOLVED`
- nonnumeric `re_evaluate_conditions` only if still model-owned

Runtime materializer then builds the complete EntryRange object.

For non-WAIT:

- no entry-range selection required;
- runtime owns the NOT_APPLICABLE object.

Required generic tests:

1. unresolved fundamental cannot carry model-authored valuation refs;
2. selected candidate ID materializes exact numbers/refs;
3. altered copied price/ref cannot be introduced because the model no longer authors it;
4. nonexistent candidate ID fails closed;
5. cross-ticker candidate ID fails closed;
6. tactical selection cannot become fundamental price;
7. non-WAIT cannot inject an entry candidate;
8. renamed generic identities behave identically.

Do not replace current shadow contract yet; this is the reviewed next-version draft.

## 14. No-model 22-subject coverage proof

Using the frozen 22 contexts:

Produce per subject:

- available valuation facts;
- feasible method families;
- rejected method families and reasons;
- every deterministic candidate band;
- tactical candidate count;
- method disagreement status;
- current price and distance to each candidate for context only.

Report aggregate counts:

- any safe fundamental candidate;
- PE candidate;
- P/B candidate;
- forward-book candidate;
- execution-growth candidate;
- no-safe-method;
- multi-method disagreement;
- by prospective archetype applicability.

The task does not require 22/22 candidate coverage.

Honest unresolved is preferable to fabricated coverage.

## 15. Validation

Add no-model tests for:

- PE arithmetic;
- PB arithmetic;
- exact quantile refs;
- negative earnings exclusion;
- bad book basis exclusion;
- low-quality/insufficient history exclusion;
- forward/trailing metric mismatch exclusion;
- method disagreement preservation;
- arbitrary-discount prohibition;
- candidate-ID deterministic stability;
- cross-subject isolation;
- failure-category classification.

Run:

- focused;
- full;
- frozen contracts;
- Treasury/KRX;
- Ruff;
- `git diff --check`.

No test deletion or skip inflation.

## 16. Required artifacts

At minimum:

- `source-base-integrity.json`
- `m12cn-r2-chat-scope-reconciliation.json`
- `r2-semantic-failure-reproducer.json`
- `r2-failure-category-correction.json`
- `entry-range-field-ownership-audit.json`
- `entry-range-selection-materialization-draft-contract.json`
- `valuation-method-source-contracts.json`
- `valuation-method-feasibility-matrix.json`
- `archetype-method-applicability-matrix.json`
- `execution-growth-method-input-coverage.json`
- `fundamental-entry-candidate-builder-contract.json`
- `fundamental-entry-candidate-coverage.json`
- `fundamental-entry-candidates-22.json`
- `method-disagreement-analysis.json`
- `current-price-discount-prohibition-proof.json`
- generic negative/positive fixtures
- exact shadow-only builder/materializer sources and hashes
- test commands/logs/JUnit
- `safety-counters.json`
- `complete-blocker-ledger.json`
- `program-completion.json`
- `REPORT.md`
- `artifact-manifest.json`
- external result ZIP SHA sidecar.

## 17. Terminal outcomes

Use one:

- `M12CO_ENTRY_RANGE_METHOD_COVERAGE_READY_FOR_CHAT_POLICY_SELECTION`
- `M12CO_ENTRY_RANGE_OWNERSHIP_DESIGN_GAP`
- `M12CO_SAFE_FUNDAMENTAL_METHOD_COVERAGE_INSUFFICIENT`
- `M12CO_OFFLINE_DESIGN_FAILED`

A PASS means only that Chat now has enough evidence to choose the method policy and authorize a later fresh shadow.

## 18. Hard safety

Throughout:

- external model calls = 0;
- market refresh = 0;
- production policy/runtime/config changes = 0;
- production sends/intents/DB writes = 0;
- broker read/order/modify/cancel = 0;
- scheduler changes = 0;
- main merge = 0;
- remote push = 0;
- deployment = 0.

Return to Chat. Do not automatically start M12CN-R3.
