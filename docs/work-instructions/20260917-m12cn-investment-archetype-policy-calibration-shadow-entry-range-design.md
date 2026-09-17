# Thesis Monitor — M12CN Investment Archetype Policy Calibration Shadow + WAIT Entry-Range Design

## 0. Task identity and decision boundary

Suggested work-instruction filename:

`20260917-m12cn-investment-archetype-policy-calibration-shadow-entry-range-design.md`

Suggested result bundle:

`thesis-monitor-20260917-m12cn-investment-archetype-policy-calibration-shadow-entry-range-design-report.zip`

This is a **policy-calibration shadow task** after the successful M12CM current US14/KR8 production-equivalent smoke and the subsequent blind human-vs-monitoring-AI comparison.

It is NOT:

- a production prompt/policy cutover,
- a retune to force agreement with any pre-existing per-ticker label,
- a change to Fundamental Core semantics,
- a change to Stage-2 v4 claim/source ownership,
- a new market-data smoke,
- a fresh Fundamental Core generation,
- a deployment task,
- an automated-trading/order-sizing task,
- a main merge / scheduler resume / production send task.

The purpose is to formalize and test, on the **same frozen M12CM facts and accepted Fundamental Core**, a generic investment-policy layer that cleanly separates:

1. long-term company thesis / enterprise value direction,
2. current entry attractiveness and WAIT price band,
3. existing-holder posture,
4. confidence/data-quality limitations,
5. company archetype-specific evidence weighting.

No per-ticker answer is a target. The existing independent judgment and old monitoring-AI verdicts are post-freeze comparison material only.

---

# 1. Authoritative source order and exact provenance

Use this source order:

1. this work instruction,
2. verified M12CM result and its frozen facts/Core identities,
3. current repository at the exact M12CM runtime base,
4. M12CL result for Stage-2 v4 contract closure,
5. post-freeze blind comparison artifacts only after new M12CN shadow outputs are frozen.

Exact sources supplied in the package:

- M12CM result ZIP SHA-256: `625606d6df521cf3368c8779ec7f24816ee3a374cdfcc7fac367f984983359cc`
- M12CL result ZIP SHA-256: `744f638e56436d31b6bdc8eb4aece3f68cd7daf0e4a2f02d8feabf7dbddd8024`
- M12CM human-review-only ZIP SHA-256: `93e376c5efe91664e0193f6f79c048cb4c9328befa18c182ae729616e64409fb`
- independent assistant judgment SHA-256: `745d4dd5005c7f4604f2fd5da4f5feedb0d7ec0a24e332f4c808a669cedaad01`
- prior comparison report SHA-256: `01782dfea7e21a1bf0f2d3c4afe3917e88b3d499b8a0cf3f721de65c587ed7d8`
- old sealed monitoring-AI verdict ZIP SHA-256: `0fc4761d8e8fb32870c547f8921a6d55dff00c54a072b486b752ed99d43d13ab`

Repository/runtime provenance from M12CM:

- required runtime base: `831890d1bf0dff303f67a6e0de1403ad3221b5d8`
- M12CM work-instruction commit: `c2f85e5541e902c59abd256dbd6876c98a4e5bed`
- M12CM harness commit: `5c0cb075ce8b765745039a3082235942346af225`
- runtime tree SHA-256: `c0a48acb3acdbd1dff940924f38c177bfecfd07df7cda0d3bddf86424c1f1062`
- active raw Stage-2 contract entering this task: `v2-accepted-stage2-model-output-v4`

M12CM frozen generation:

`20260917-m12cm-current-v4-smoke-20260917T062918Z-5c0cb075ce8b`

M12CM established:

- population `22` = US14 + KR8,
- Core 22/22,
- Stage-2 v4 22/22,
- materialized/finalized/readback/capture 22/22,
- maturity rows 98,
- empty supporting claims 0,
- no retry/repair/fallback/judge/selective rerun,
- production mutation/send/deploy 0.

Verify package sources and repository hashes before executing any shadow inference. Unexpected runtime divergence => STOP with `M12CN_SOURCE_OR_BASE_MISMATCH`.

---

# 2. Blindness / anti-target-leak contract

The package deliberately separates two areas:

## 2.1 Model/policy-design-eligible inputs

Before shadow outputs are frozen, the task may use only:

- `inputs/policy-principles.json`,
- `inputs/m12cm-shadow-input/` or its ZIP,
- `inputs/m12cm-human-review-only.zip`,
- repository code/history needed to understand generic owners/contracts,
- M12CL/M12CM structural reports that do **not** disclose per-ticker final verdicts.

## 2.2 Post-freeze comparison only

Before shadow outputs are frozen, DO NOT open/read/search/import/model-input any file under:

`post-freeze-reference/`

including:

- `m12cm-independent-assistant-judgment.json`,
- `m12cm-independent-vs-monitoring-ai-comparison.md`,
- `m12cm-sealed-ai-verdicts.zip`.

No per-ticker old monitoring verdict, independent judgment, label distribution, expected class or desired entry band may appear in model-facing prompts, schemas, ref catalogs or test expectations.

After the M12CN shadow output is byte-frozen, the comparison layer may open these references for **descriptive evaluation only**. No same-run retuning or second inference is authorized.

Required proof:

- enumerate every model-facing file SHA before call 1;
- scan all model-facing inputs for post-freeze-reference paths/hashes/verdict keys;
- record `target_label_leak_count = 0`;
- freeze all shadow outputs before opening comparison references;
- record timestamps/order proving this sequence.

Any leak => `M12CN_BLINDNESS_FAILURE`, stop before inference if detected pre-call or invalidate the run if detected later.

---

# 3. User-approved policy principles to formalize

The following are generic policy principles, not ticker-specific target answers.

## 3.1 Long-term thesis and current entry must be independent

`overall_direction` answers:

> Is the long-term enterprise/business investment thesis strengthening, intact, impaired or invalidated?

`new_buyer` answers:

> Given that thesis, is the current market price attractive for a new position now?

Therefore the following is a normal, intended state:

`BUY / WAIT / HOLDABLE`

A high valuation or overheated price alone must not automatically convert a strong long-term thesis from BUY to HOLD/SELL.

## 3.2 Holder REVIEW is not a synonym for expensive valuation

A holder stance of REVIEW requires a material thesis question, evidence contradiction, execution deterioration, balance-sheet concern, or genuinely unresolved risk relevant to ownership.

`valuation_expensive` or `entry_not_attractive` alone is insufficient to force REVIEW when the underlying thesis remains intact.

## 3.3 Data-quality uncertainty defaults to confidence, not bearish polarity

Missing, stale, unsupported, provider-limited or otherwise unreliable data normally means:

- confidence down,
- verification requirement up,
- directional weight unchanged unless another valid negative fact exists.

Do not convert `UNKNOWN` or `DATA_QUALITY_LIMITATION` into bearish evidence by default.

A distinct `MATERIAL_DISCLOSURE_FAILURE` may itself be negative evidence only if the absence/non-disclosure is economically meaningful and the source establishes that condition. Do not infer this merely because a provider field is missing.

## 3.4 WAIT requires an actionable price-band result

Every `new_buyer = WAIT` must return exactly one of:

- `ENTRY_RANGE_RESOLVED`, with an evidence-backed preferred entry band; or
- `ENTRY_RANGE_UNRESOLVED`, with the exact missing inputs/method dependency.

Never manufacture a price simply because WAIT requires one.

---

# 4. Evidence-based company archetype contract

Do not hardcode tickers, names, countries or sectors into production logic. Classify from evidence.

The shadow policy must support these archetypes:

1. `DURABLE_FRANCHISE`
2. `STRUCTURAL_CYCLICAL_LEADER`
3. `PROFITABLE_PREMIUM_GROWTH`
4. `EXECUTION_DEPENDENT_GROWTH`
5. `MATURE_VALUE_DEFENSIVE`
6. `UNRESOLVED`

Archetype selection must cite structured evidence dimensions, at minimum where available:

- scale / market position / competitive durability,
- multi-period profitability and cash generation,
- structural versus cyclical demand exposure,
- capital intensity and cycle sensitivity,
- growth execution dependence,
- unit-economics / margin proof,
- balance-sheet and financing/dilution dependence,
- earnings/FCF visibility,
- valuation method suitability.

No ticker map such as `{GOOGL: DURABLE_FRANCHISE}` is permitted. No symbol allowlist/denylist. Generic fixtures with renamed identities must reach the same classification when economic evidence is unchanged.

If evidence cannot support a class, use `UNRESOLVED`; do not guess.

---

# 5. Archetype-specific weighting semantics

## 5.1 DURABLE_FRANCHISE

Long-term direction is primarily driven by:

- durable competitive advantage,
- structural earnings/FCF power,
- business quality and reinvestment economics,
- market position / product moat,
- material thesis impairments.

Valuation and current price predominantly affect `new_buyer`, not long-term direction.

Examples of potential direction-changing evidence, only when actually evidenced:

- structural customer loss,
- durable competitive-position deterioration,
- core product/technology thesis failure,
- persistent earnings/FCF impairment,
- balance-sheet deterioration threatening the thesis.

## 5.2 STRUCTURAL_CYCLICAL_LEADER

Long-term direction combines competitive position with cycle structure.

Required distinction:

- enterprise/technology leadership can remain BUY,
- entry can still be WAIT when the cycle/valuation is stretched.

Use structural demand, supply/capacity, pricing, utilization, CAPEX discipline and normalized/mid-cycle earnings where available. A normal cyclical slowdown is not automatically a destroyed structural thesis; a genuine supply/technology/customer thesis break can be.

## 5.3 PROFITABLE_PREMIUM_GROWTH

Evaluate:

- validated growth,
- backlog/order conversion,
- margins,
- ROIC/FCF trajectory,
- reinvestment quality,
- valuation relative to demonstrated growth.

Valuation matters more to overall direction than in a durable franchise when the premium requires continued execution, but valuation alone should not mechanically produce SELL while execution remains strong unless the downside asymmetry is evidence-backed.

## 5.4 EXECUTION_DEPENDENT_GROWTH

Overall direction may be materially affected by:

- realized revenue conversion,
- utilization/unit economics,
- gross/operating margin path,
- OCF/FCF and cash burn,
- CAPEX efficiency,
- financing/dilution/debt dependence,
- concentration risk,
- valuation relative to still-unproven economics.

Large TAM, contracts, fleet capacity or announced pipelines alone are insufficient.

## 5.5 MATURE_VALUE_DEFENSIVE

Weight:

- earnings durability,
- capital strength,
- cash distribution / capital return,
- balance sheet,
- underwriting/operating quality where applicable,
- valuation and downside protection.

## 5.6 UNRESOLVED

Do not silently choose another archetype. Lower confidence and state the missing evidence.

---

# 6. Three-axis decision contract

Shadow output must keep the current independent axes and preserve existing decision labels:

### Overall direction

- `BUY`
- `HOLD`
- `SELL`

### New buyer

- `ATTRACTIVE`
- `WAIT`
- `AVOID`

### Holder

- `HOLDABLE`
- `REVIEW`
- `REDUCE`

Rules:

1. `BUY + WAIT + HOLDABLE` is valid and expected when thesis is strong but price is unattractive.
2. `HOLDABLE` must remain possible even when `new_buyer = AVOID`, if the reason is primarily entry valuation and the holder thesis remains intact.
3. `REVIEW` needs a material thesis-relevant reason. Record the exact reason class.
4. `REDUCE` needs actual impairment/asymmetry/risk evidence, not generic uncertainty.
5. No mechanical mapping from directional balance alone to final labels unless the existing contract explicitly owns that mapping.

Do not change existing preconfirmation/postconfirmation or claim/evidence ownership contracts in this task.

---

# 7. Entry-range design for WAIT

This is a **buy-entry band**, not a price target or guaranteed fair value.

For every WAIT output, return:

- `entry_range_status`
- `current_price` and as-of/source ref when safely available
- `preferred_entry_low`
- `preferred_entry_high`
- `distance_to_band_pct`
- `fundamental_entry_band`
- `tactical_entry_band`
- `method`
- `valuation_basis_refs`
- `technical_basis_refs`
- `assumptions`
- `unresolved_inputs`
- `re_evaluate_conditions`

Numeric fields must be null when unresolved.

## 7.1 Allowed fundamental methods

Use only methods supported by existing evidence and company archetype, for example:

- `FORWARD_EARNINGS_MULTIPLE`
- `NORMALIZED_CYCLE_EARNINGS`
- `FCF_YIELD_OR_MULTIPLE`
- `EV_EBITDA`
- `EV_SALES_SCENARIO`
- `EV_GROSS_PROFIT_SCENARIO`
- `SOTP_EXISTING_EVIDENCE`

Do not use a PE method for a company without meaningful positive earnings. Do not use EV/Sales merely because a company is a growth stock if revenue economics are not comparable or source inputs are absent.

## 7.2 Tactical band

May use existing price-structure evidence such as:

- daily/weekly support,
- validated pivots,
- current price structure,
- moving-average or volume structure only where the existing evidence owns it.

Do not invent chart levels from prose or use unsupported indicators.

## 7.3 Preferred band combination

Prefer overlap/intersection of a defensible fundamental band and a defensible tactical support region.

If the two do not overlap, report both and classify the preferred range conservatively with an explicit rule. Do not silently average unrelated bands.

If no defensible fundamental valuation input exists, return `ENTRY_RANGE_UNRESOLVED`; a technical support level alone must not masquerade as fundamental fair entry.

Forbidden shortcuts:

- current price minus an arbitrary 5/10/20%,
- old analyst target copied without basis,
- prior human/AI desired label used to choose a range,
- ticker-specific hardcoded price,
- unreferenced multiple,
- cross-ticker multiple transfer without an explicit comparable-evidence contract.

---

# 8. Shadow implementation boundary

This task must NOT modify current production decision behavior.

Preferred implementation:

- shadow-only prompt/schema/policy adapter and evaluator under scripts/tests or explicitly shadow-owned modules;
- application/runtime production path change count `0`.

If a reusable production-neutral type is absolutely required, STOP and propose it rather than silently changing live owners.

Do not change:

- M12CM accepted artifacts,
- Stage-2 v4 production prompt/schema,
- Fundamental Core prompt/schema,
- numeric ownership,
- maturity claim/source projection,
- as_of/provenance ownership,
- entry/holder labels in current production,
- delivery/receipt/state logic,
- KRX/Treasury/market-data policy.

---

# 9. Shadow model execution

After the generic policy contract and schema are frozen, run exactly **8 shadow Stage-2-style calls** using the existing M12CM batch topology:

US 5 batches + KR 3 batches.

Inputs:

- exact frozen M12CM facts/context,
- exact independently frozen M12CM accepted Fundamental Core for the same generation,
- new generic shadow policy only.

Do NOT rerun Fundamental Core. This is intentional: the task measures policy/decision-layer effect on identical evidence.

Configured model/effort:

- use the same existing project configuration as M12CM (`gpt-5.6-sol`, `xhigh`) if still available through the approved signed-in transport;
- do not substitute another model/effort silently.

Hard execution rules:

- one attempt per call,
- no retry,
- no repair model,
- no judge model,
- no fallback model,
- no selective ticker rerun,
- no old Stage-2 output reuse as a new answer,
- no post-call prompt/schema hotfix,
- no reading post-freeze references before all 8 outputs are frozen.

A first hard contract failure stops subsequent dependent calls, preserves completed outputs and returns to Chat. Independent static tests may finish.

This 8-call shadow is not a Full22 production proof and must never be labeled as such.

---

# 10. Shadow output schema

Each subject must include at least:

- ticker/market identity,
- `company_archetype`,
- `archetype_confidence`,
- archetype evidence refs,
- `overall_direction`,
- `new_buyer`,
- `holder`,
- decision confidence,
- decisive supporting and contradicting claim refs under existing ownership rules,
- `thesis_state` = `STRENGTHENING | INTACT | MIXED | IMPAIRED | INVALIDATED | UNRESOLVED`,
- `data_quality_effect` = `CONFIDENCE_ONLY | DIRECTIONAL_NEGATIVE | DIRECTIONAL_POSITIVE | NONE`,
- exact reason when data quality is directional,
- holder review reason class when REVIEW,
- entry-range object from section 7,
- explicit `valuation_affects` set drawn from `OVERALL | NEW_BUYER | HOLDER`,
- rule trace indicating which generic policy clauses were applied.

No user/assistant reference labels may appear in this schema or prompt.

---

# 11. Required generic controls before inference

Build generic/synthetic or source-faithful controls that establish:

1. strong durable thesis + expensive valuation can produce `BUY/WAIT/HOLDABLE`;
2. expensive valuation alone does not force holder REVIEW;
3. provider/data-quality limitation alone lowers confidence without bearish direction;
4. material disclosure failure can be bearish only with evidence that the failure itself is material;
5. execution-growth company with cash burn/dilution/poor unit economics can receive HOLD/SELL even with strong TAM;
6. structural cyclical leader can remain BUY while entry is WAIT at an expensive cycle point;
7. WAIT without valuation inputs returns `ENTRY_RANGE_UNRESOLVED`, not a fabricated number;
8. profitable company uses an appropriate valuation method; loss-making company is not assigned PE mechanically;
9. identity-renamed equivalent fixtures preserve policy behavior;
10. no ticker/name/sector literal controls production behavior.

These controls test semantics, not desired 22-stock labels.

---

# 12. Post-freeze comparison

Only after all available shadow outputs and their hashes are frozen may the evaluator open `post-freeze-reference/`.

Then compare three sets:

A. M12CM original monitoring AI
B. pre-existing independent assistant judgment
C. M12CN shadow policy output

For every ticker report:

- old vs shadow overall/new-buyer/holder,
- independent-reference vs shadow differences,
- archetype,
- WAIT entry-range status/method,
- whether the change is explained by an explicit generic policy clause,
- whether any difference appears target-driven or unsupported.

Aggregate at least:

- label distributions,
- exact 3-axis agreement counts,
- per-axis agreement counts,
- WAIT count,
- WAIT with resolved entry range,
- WAIT unresolved count + reasons,
- holder REVIEW count and reason classes,
- data-quality directional-negative count,
- archetype distribution,
- overall-direction changes attributable solely to valuation,
- identity-generic control results.

**Agreement with the independent reference is NOT a PASS criterion.** It is descriptive calibration evidence. A shadow result that matches more labels but violates generic rules is a failure.

No second inference or tuning pass after comparison.

---

# 13. Special audit questions

The result must answer these directly from evidence:

1. Does the current policy conflate company-thesis quality with entry valuation?
2. Under the shadow policy, how often does valuation change only new-buyer vs overall direction?
3. How many holder REVIEW outcomes are driven by actual thesis uncertainty versus valuation alone?
4. Does any provider/data-quality limitation become SELL evidence without a material-negative fact?
5. Which archetypes can produce resolved entry bands with current evidence, and which lack required valuation inputs?
6. Are entry bands dominated by fundamentals, tactical structure, or both?
7. Does any entry band rely on arbitrary discounting from current price?
8. Are the policy changes generic under renamed-identity controls?
9. What production fields/prompt sections would need changing if Chat later authorizes integration?
10. Can production integration be bounded to the decision/policy layer without reopening Core, maturity, delivery or market-data contracts?

---

# 14. Validation and safety

Run:

- shadow schema tests,
- generic policy controls,
- exact Stage-2 v4 compatibility tests where reused,
- full existing repository suite,
- Treasury/KRX frozen regressions as appropriate,
- Ruff,
- `git diff --check`.

No test deletion or skip inflation.

Safety counters must show:

- production send = 0,
- production intent = 0,
- production DB mutation = 0,
- broker read/order/modify/cancel = 0 unless a read is strictly required for repository preflight; no market provider refresh is needed for this frozen-facts task,
- scheduler change = 0,
- main merge = 0,
- remote push = 0,
- deployment = 0,
- Fundamental Core model calls = 0,
- Stage-2 shadow model calls <= 8 exactly as executed,
- retries/repair/fallback/judge/selective rerun = 0.

---

# 15. Required artifacts

Include at minimum:

- `source-base-integrity.json`
- `blindness-and-target-leak-proof.json`
- `policy-principles-normalized.json`
- `archetype-contract.json`
- `archetype-classification-evidence.json`
- `three-axis-policy-contract.json`
- `data-quality-directionality-contract.json`
- `entry-range-method-contract.json`
- `generic-policy-control-matrix.json`
- `shadow-model-input-manifest.json`
- all 8 shadow prompts/schemas/ref catalogs/raw outputs where executed
- `shadow-output-freeze-manifest.json`
- `shadow-22-subject-results.json`
- `entry-range-coverage-and-methods.json`
- `holder-review-reason-analysis.json`
- `valuation-vs-overall-direction-analysis.json`
- `post-freeze-three-way-comparison.json`
- `post-freeze-three-way-comparison.md`
- `production-integration-impact-map.md`
- `test-results.json`, JUnit/logs, Ruff/diff outputs
- `safety-counters.json`
- `complete-blocker-ledger.json`
- `program-completion.json`
- `REPORT.md`
- `artifact-manifest.json` and external ZIP SHA sidecar.

Export enough exact prompt/schema source to prove there are no hidden per-ticker rules.

---

# 16. Completion states

Use one of:

`M12CN_POLICY_CALIBRATION_SHADOW_PASS_READY_FOR_CHAT_REVIEW`

Requires:

- generic archetype contract closed,
- 8-call shadow completed for all 22 subjects,
- target leakage 0,
- generic controls PASS,
- entry-range contract enforced without fabricated prices,
- data-quality/confidence separation enforced,
- no production runtime behavior change,
- post-freeze comparison completed once, without retuning.

`M12CN_POLICY_DESIGN_PASS_SHADOW_EXECUTION_BLOCKED`

Use when static policy/schema/control work is valid but approved model transport or a required frozen input is unavailable. No invented shadow results.

`M12CN_POLICY_CONTRACT_GAP_REQUIRES_CHAT_DECISION`

Use when a generic rule cannot be implemented without changing Fundamental Core/evidence ownership/valuation source semantics or another frozen architecture contract.

`M12CN_POLICY_CALIBRATION_SHADOW_FAILED`

Use for executed semantic/contract/blindness failures.

Even after PASS:

- production policy is unchanged,
- deployment readiness = NO,
- scheduler/real send remain untouched,
- no automatic next generation is authorized.

Return the complete result to Chat. Chat then decides whether the generic policy should be integrated into production, revised, or rejected.
