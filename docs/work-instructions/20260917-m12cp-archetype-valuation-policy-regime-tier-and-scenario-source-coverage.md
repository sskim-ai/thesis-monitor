# Thesis Monitor — M12CP Archetype Valuation Policy, Regime Tier & Scenario Source Coverage

## 0. Task identity

Work-instruction filename:

`20260917-m12cp-archetype-valuation-policy-regime-tier-and-scenario-source-coverage.md`

Suggested result bundle:

`thesis-monitor-20260917-m12cp-archetype-valuation-policy-regime-tier-and-scenario-source-coverage-report.zip`

This is a **no-model shadow-policy contract + deterministic valuation-source coverage task** after M12CO.

It is NOT:

- a fresh policy-calibration model run;
- a production Stage-2 change;
- a production valuation-policy deployment;
- a market-data refresh;
- a per-ticker target-price task;
- a buy/sell recommendation override;
- a production notification/scheduler/broker task.

External model calls: **0**.

Production application/runtime/config behavior changes: **0**.

## 1. Source integrity

Verify first:

- M12CO result ZIP SHA-256:
  `ece5d575183a86c25c6fb0762957c07675d15914747cbbab4845ed510b82abe4`
- M12CO result manifest: 40 declared payloads, 40/40 hash/size PASS.
- M12CO completion:
  `M12CO_ENTRY_RANGE_METHOD_COVERAGE_READY_FOR_CHAT_POLICY_SELECTION`
- Required runtime base:
  `831890d1bf0dff303f67a6e0de1403ad3221b5d8`
- M12CO implementation commit:
  `59ea089b1da246dfd87b15a22b03c0312a2d0ae0`
- Frozen M12CM generation:
  `20260917-m12cm-current-v4-smoke-20260917T062918Z-5c0cb075ce8b`

Use the packaged frozen source lineage only.

No external market/fundamental refresh.

## 2. Carry forward closed M12CO findings

Freeze:

- current-price arbitrary discount count = 0;
- historical quantile arithmetic/source safety contract;
- method disagreement is never averaged away;
- model should not author deterministic entry-range numbers/refs/statuses;
- tactical support alone is not fundamental value;
- forward EPS × historical trailing P/E remains forbidden without an explicit basis contract;
- forward book × historical P/B remains forbidden without an explicit basis contract;
- execution-growth scenario methods remain unavailable unless their component facts are canonical;
- production valuation code remains unchanged.

## 3. Archetype valuation-method policy

Implement this as **shadow-only policy metadata and deterministic eligibility logic**. No ticker/company/country rule.

### 3.1 DURABLE_FRANCHISE

Primary currently allowed family:

`HISTORICAL_TRAILING_PE_QUANTILE`

when M12CO source/basis safety passes.

`HISTORICAL_PB_QUANTILE` is:

`SECONDARY_DIAGNOSTIC`

unless a deterministic `asset_relevance` contract proves that book value is economically primary for the business.

Do not average P/E and P/B.

If primary P/E is unavailable, remain unresolved rather than automatically falling back to P/B.

### 3.2 STRUCTURAL_CYCLICAL_LEADER

Primary currently allowed family:

`HISTORICAL_PB_QUANTILE`

with explicit regime/cycle caution.

Raw:

`HISTORICAL_TRAILING_PE_QUANTILE`

is not a primary fundamental-entry method until a `cycle_normalized_earnings` source contract exists.

Do not use low peak-cycle P/E as proof of cheapness.

### 3.3 PROFITABLE_PREMIUM_GROWTH

Primary currently allowed family:

`HISTORICAL_TRAILING_PE_QUANTILE`

when safe.

P/B is secondary/conditional and cannot be primary without deterministic asset relevance.

Future EV/EBITDA or FCF methods may supersede this once their canonical source contracts exist.

### 3.4 EXECUTION_DEPENDENT_GROWTH

Historical P/E/P/B arithmetic candidates are **not selectable as final preferred fundamental entry** merely because arithmetic is possible.

Required future families:

- EV/Sales scenario
- EV/Gross Profit scenario
- EV/EBITDA scenario
- FCF/cash-runway/dilution scenario

Until at least one safe scenario method exists:

`fundamental_choice = UNRESOLVED`

Tactical support may still be materialized separately.

### 3.5 MATURE_VALUE_DEFENSIVE

P/E and P/B may both be primary when safe and economically applicable.

Never average methods.

For the same valuation-regime tier:

- if both method bands overlap, build a deterministic `METHOD_INTERSECTION` candidate using:
  - low = max(method lows)
  - high = min(method highs)
  - refs = union of both canonical method refs
- if they do not overlap:
  - no composite candidate;
  - status = `METHODS_DIVERGE_REQUIRES_RESOLUTION`
  - no preferred fundamental range unless a separately proven business-model owner selects one method.

### 3.6 UNRESOLVED

No selectable fundamental candidate.

## 4. Valuation regime tier contract

Create shadow-only:

`valuation_regime_tier`

with:

- `CONSERVATIVE`
- `BASE`
- `PREMIUM`
- `UNRESOLVED`

Deterministic mapping:

- CONSERVATIVE -> P25_P50
- BASE -> P50_P75
- PREMIUM -> P75_P90
- UNRESOLVED -> no quantile candidate selection

The future model will judge the tier; M12CP itself uses no model.

### 4.1 Tier evidence contract

A later model's tier choice must cite only eligible non-price fundamental/competitive/cycle refs.

Forbidden tier evidence:

- current price;
- current valuation percentile itself;
- chart support/resistance;
- tactical price rules;
- desired New Buyer label;
- prior human/AI label.

`PREMIUM` requires explicit evidence of durable structural improvement/rerating, such as:

- sustained competitive-position improvement;
- structurally stronger earnings/cash-flow economics;
- durable growth/margin/ROIC improvement;
- structurally higher-value business mix;
- another canonical structural change owned by evidence.

High current multiple alone is never evidence for PREMIUM.

`CONSERVATIVE` may be supported by material thesis/cycle weakening that does not yet invalidate the long-term thesis.

If evidence is conflicting or insufficient:

`UNRESOLVED`.

## 5. Candidate option materialization

Create a deterministic shadow-only option builder.

Given:

- archetype;
- valuation_regime_tier;
- M12CO safe candidate catalog;

runtime returns either:

- exactly one eligible fundamental option;
- a deterministic same-tier METHOD_INTERSECTION option;
- or UNRESOLVED.

No model-authored prices.

### 5.1 Examples of intended generic behavior

- DURABLE_FRANCHISE + BASE + safe P/E:
  select the P50_P75 historical trailing-P/E candidate.
- DURABLE_FRANCHISE + safe P/B but unsafe P/E:
  unresolved unless asset relevance is independently proven.
- STRUCTURAL_CYCLICAL_LEADER + PREMIUM + safe P/B:
  select P75_P90 P/B candidate.
- STRUCTURAL_CYCLICAL_LEADER + only trailing P/E:
  unresolved until normalized earnings contract.
- EXECUTION_DEPENDENT_GROWTH:
  historical P/B/PE candidates are not selectable.
- MATURE_VALUE_DEFENSIVE + BASE + safe P/E and P/B with overlap:
  deterministic intersection of their P50_P75 bands.
- MATURE_VALUE_DEFENSIVE + BASE + non-overlap:
  unresolved.

No ticker-specific code.

## 6. New Buyer consistency contract — draft only

Do not change production.

Draft the later shadow constraints:

- `ATTRACTIVE` requires:
  - a resolved fundamental entry option;
  - current price at/below the permitted fundamental band high;
  - no incompatible severe execution/tactical condition.
- `WAIT` is valid when:
  - current price is above the preferred fundamental range; or
  - the fundamental range is unresolved; or
  - tactical timing is unfavorable despite long-term thesis remaining positive.
- `AVOID` may be used for material execution/thesis risk and does not require a resolved price band.

Overall Direction remains separate:
- valuation/timing alone must not automatically turn a durable/structural thesis from BUY into HOLD/SELL.

Holder remains separate:
- valuation alone does not create REVIEW.

This is a contract draft and generic test surface only; no model call in M12CP.

## 7. Deterministic scenario-input component audit

M12CO searched for preassembled keys such as `enterprise_value` and `revenue_scenario`.

M12CP must go one level deeper and inspect the **actual existing frozen canonical/source facts** for components from which safe scenario inputs might be constructed.

For each subject inventory exact refs/values/basis for:

- current market capitalization;
- cash and cash equivalents;
- total debt / net debt;
- diluted share count / basic share count and basis;
- LTM revenue;
- LTM gross profit;
- EBITDA / operating income;
- OCF;
- FCF;
- current gross margin;
- company guidance / consensus revenue growth if already canonical;
- company guidance / consensus margins if already canonical;
- capex;
- share dilution/change;
- cash runway components.

Do not infer from prose if no typed/canonical owner exists.

## 8. Enterprise-value derivation contract

If and only if canonical components exist and are same-subject/same-basis/currency-compatible:

`enterprise_value = market_cap + total_debt - cash_and_equivalents`

Materialize a shadow-only canonical derived candidate input with source refs.

If preferred stock/minority interest or other material EV components are required but unavailable, classify:

`ENTERPRISE_VALUE_COMPONENTS_INCOMPLETE`

Do not silently approximate.

## 9. Scenario valuation method source coverage

For execution-dependent/profitable-growth archetypes audit whether a safe method can be built **without fabricating forecasts**.

### EV/Sales

Requires:
- safe EV;
- canonical revenue base;
- canonical future revenue scenario or explicit company/consensus guidance;
- justified EV/Sales multiple source contract.

### EV/Gross Profit

Requires:
- safe EV;
- canonical gross-profit base/scenario;
- justified EV/GP multiple source contract.

### EV/EBITDA

Requires:
- safe EV;
- normalized future EBITDA or explicit guidance/consensus;
- justified EV/EBITDA multiple contract.

### FCF

Requires:
- canonical FCF scenario;
- safe diluted shares/security basis;
- explicit discount/multiple methodology.

Do not let the model invent scenario numbers.

If the frozen facts lack the required multiple/scenario source, report the exact minimal source-contract gap.

## 10. Historical-multiple source expansion audit

Audit whether M12CO's 13 no-safe-method subjects are blocked because:

A. the data truly does not exist; or
B. the raw/fact source exists but was not projected into the canonical valuation catalog; or
C. security/share/currency basis is unresolved.

For category B, shadow-only projection is allowed if the source contract already owns the metric and no new semantics are invented.

For category C, do not guess.

## 11. Depositary / ADR / current-security basis audit

Specifically audit all affected securities generically, not by a hardcoded allowlist.

Determine whether the frozen source already owns:

- depositary ratio / shares-per-ADR;
- underlying-security identity;
- reporting currency;
- trading currency;
- per-share denominator basis;
- current-security conversion basis.

If enough canonical evidence exists, define a generic shadow-only basis-conversion contract.

If not, emit:

`DEPOSITARY_SECURITY_BASIS_UNRESOLVED`

with exact missing fields.

Do not copy underlying-company per-share metrics into an ADR without a verified ratio.

## 12. Updated candidate coverage

After applying:

- archetype method eligibility;
- regime-tier mapping;
- any safe existing-source projection;
- any safe derived EV inputs;

produce updated no-model coverage for all 22:

- arithmetic candidates;
- policy-selectable candidates;
- options by archetype/tier;
- method-intersection candidates;
- scenario method readiness;
- unresolved reasons;
- security-basis gaps.

Do not force 22/22.

Required counts:

- safe arithmetic;
- policy selectable;
- durable-primary-PE coverage;
- structural-cyclical-primary-PB coverage;
- mature-value intersection coverage;
- execution-growth scenario-ready coverage;
- depositary-basis-resolved/unresolved;
- no-safe-policy-method.

## 13. Generic controls

At minimum:

1. Durable franchise cannot select P/B as primary without asset relevance.
2. Structural cyclical cannot select raw historical P/E as primary.
3. Execution growth cannot select historical P/B merely because arithmetic is safe.
4. Mature value same-tier intersection is exact and never averaged.
5. Non-overlap remains unresolved.
6. Regime tier maps to the exact quantile band.
7. PREMIUM cannot be justified by current price/multiple alone.
8. Current price is not used to generate the band.
9. Scenario inputs cannot be fabricated.
10. Unsafe ADR/share basis rejects.
11. Cross-ticker/source refs reject.
12. Candidate IDs remain deterministic.
13. Renamed identities preserve generic behavior.
14. No production file changes.

## 14. Next-shadow draft

Produce the exact reviewed draft contract for a later fresh shadow.

Preferred later model outputs for WAIT:

- archetype;
- valuation_regime_tier;
- tier_supporting_refs;
- tactical_choice `candidate_id | UNRESOLVED`;
- bounded nonnumeric re-evaluation prose.

Do **not** require the model to author the fundamental candidate ID if archetype+tier+policy resolve exactly one candidate deterministically.

If multiple policy-eligible fundamental choices remain after archetype+tier, return UNRESOLVED rather than asking the model to choose a price method without an explicit policy owner.

Runtime materializes the entire EntryRange object.

No model call in M12CP.

## 15. Validation

Run no-model:

- focused;
- full;
- frozen-contract;
- Treasury/KRX;
- Ruff;
- `git diff --check`.

No test deletion or skip inflation.

## 16. Required artifacts

At minimum:

- `source-base-integrity.json`
- `m12co-chat-policy-selection.json`
- `archetype-primary-method-policy.json`
- `valuation-regime-tier-contract.json`
- `entry-option-policy-materializer-contract.json`
- `new-buyer-consistency-draft-contract.json`
- `frozen-source-component-inventory-22.json`
- `enterprise-value-derived-input-coverage.json`
- `scenario-method-source-coverage.json`
- `historical-method-projection-gap-analysis.json`
- `depositary-security-basis-coverage.json`
- `updated-fundamental-entry-candidate-coverage.json`
- `policy-selectable-entry-options-22.json`
- `method-intersection-analysis.json`
- `next-shadow-output-contract-draft.json`
- generic fixture/control matrix
- exact shadow-only code and source hashes
- test/JUnit/logs
- `safety-counters.json`
- `complete-blocker-ledger.json`
- `program-completion.json`
- `REPORT.md`
- `artifact-manifest.json`
- external result ZIP SHA sidecar.

## 17. Completion states

Use one:

- `M12CP_ARCHETYPE_VALUATION_POLICY_AND_SOURCE_COVERAGE_READY_FOR_FRESH_SHADOW`
- `M12CP_POLICY_MATERIALIZATION_GAP_REQUIRES_CHAT`
- `M12CP_SCENARIO_SOURCE_COVERAGE_INSUFFICIENT_BUT_HISTORICAL_POLICY_READY`
- `M12CP_OFFLINE_POLICY_DESIGN_FAILED`

A PASS does not authorize the fresh model shadow automatically. Return to Chat.

## 18. Hard safety

- External model calls: 0
- Market refresh: 0
- Production runtime/config behavior changes: 0
- Production sends/intents/DB writes: 0
- Broker read/order/modify/cancel: 0
- Scheduler changes: 0
- Main merge: 0
- Remote push: 0
- Deployment: 0
