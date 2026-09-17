# Thesis Monitor — M12CN-R1 WAIT Entry Tactical Applicability Contract Repair + Fresh Policy Calibration Shadow

## 0. Task identity

Work-instruction filename:

`20260917-m12cn-r1-wait-entry-tactical-applicability-contract-repair-fresh-shadow.md`

Suggested result bundle:

`thesis-monitor-20260917-m12cn-r1-wait-entry-tactical-applicability-contract-repair-fresh-shadow-report.zip`

This is a **shadow-only contract repair + wholly fresh 8-call calibration rerun** after M12CN.

It is NOT:

- a production investment-policy cutover;
- a production Stage-2 v4 change;
- a Fundamental Core change;
- a market-data refresh/smoke;
- a per-ticker retune;
- a repair to force agreement with prior human/AI labels;
- a deployment, scheduler, notification, broker, or persistence task.

Production runtime behavior change count must remain **0**.

## 1. Source of truth and exact prior result

Verify first:

- M12CN result ZIP SHA-256:
  `2fb44910ea8f1545da6e8e6f40bfffe95a44fc614b5c41b7755f576cd2ab16ed`
- M12CN artifact manifest: 83 payloads, no missing/hash/size mismatch.
- Required runtime base:
  `831890d1bf0dff303f67a6e0de1403ad3221b5d8`
- Prior shadow harness commit:
  `dba107ca8948a4adaae972bc3d1f1f15658b303c`
- Frozen M12CM generation:
  `20260917-m12cm-current-v4-smoke-20260917T062918Z-5c0cb075ce8b`

Use the packaged frozen M12CM shadow input as the only semantic input for the new model run.

Do not use M12CN partial output as an expected answer or model-visible few-shot/reference.

## 2. Carry forward closed M12CN design findings

Freeze these shadow-policy decisions:

### 2.1 Archetypes

- `DURABLE_FRANCHISE`
- `STRUCTURAL_CYCLICAL_LEADER`
- `PROFITABLE_PREMIUM_GROWTH`
- `EXECUTION_DEPENDENT_GROWTH`
- `MATURE_VALUE_DEFENSIVE`
- `UNRESOLVED`

Classification remains evidence-based. Ticker, company name and country remain forbidden as production logic.

### 2.2 Three axes

Keep independent:

- Overall: `BUY | HOLD | SELL`
- New buyer: `ATTRACTIVE | WAIT | AVOID`
- Holder: `HOLDABLE | REVIEW | REDUCE`

`BUY / WAIT / HOLDABLE` remains explicitly valid.

Valuation alone must not force holder REVIEW.

### 2.3 Data quality

Default:

`provider/missing/unsupported limitation -> CONFIDENCE_ONLY`

Directional-negative use requires existing material-negative/disclosure evidence. Unknown/missing alone is not bearish.

### 2.4 Entry-price principles

Every WAIT must have either:

- evidence-backed resolved preferred entry range; or
- `ENTRY_RANGE_UNRESOLVED` with exact missing dependency.

Never create an arbitrary discount from current price.

Technical support alone cannot masquerade as fundamental fair entry.

## 3. Exact M12CN failure

M12CN fresh shadow generation:

`20260917-m12cn-policy-shadow-20260917T085353Z-dba107ca8948`

Call 3:

- market: US
- batch: 03
- subjects: MU / RXRX / SKHY

MU and SKHY emitted the following structural combination:

- `new_buyer = WAIT`
- `entry_range_status = ENTRY_RANGE_UNRESOLVED`
- `fundamental_entry_band.status = UNRESOLVED`
- `tactical_entry_band.status = NOT_APPLICABLE`
- preferred entry low/high = null

The input catalogs actually contained:

- MU: 2 tactical candidates
- SKHY: 1 tactical candidate

The validator rejected exactly:

- `unresolved_tactical_band_status_invalid`

The prior run correctly stopped. Do not relabel it PASS and do not replay only MU/SKHY.

## 4. Chat decision — component applicability semantics

The next frozen shadow contract shall use these semantics.

### 4.1 WAIT branch

For `new_buyer = WAIT`:

#### Parent

`entry_range_status` may be only:

- `ENTRY_RANGE_RESOLVED`
- `ENTRY_RANGE_UNRESOLVED`

`NOT_APPLICABLE` is invalid.

#### Fundamental component

`fundamental_entry_band.status` may be only:

- `RESOLVED`
- `UNRESOLVED`

`NOT_APPLICABLE` is invalid.

#### Tactical component

`tactical_entry_band.status` may be only:

- `RESOLVED`
- `UNRESOLVED`

`NOT_APPLICABLE` is invalid.

Rationale: WAIT explicitly means entry timing/price is under evaluation. Tactical assessment therefore remains applicable even if no safe tactical band can be resolved.

If no safe tactical band can be selected, use `UNRESOLVED`, null band numbers/candidate ID, empty evidence refs, and record the exact unresolved dependency/reason in the existing unresolved/re-evaluation fields.

If supplied tactical candidates are safely usable, `RESOLVED` must copy one supplied candidate exactly. Never synthesize or adjust a support band.

### 4.2 Fundamental unresolved dominates parent resolution

If:

`fundamental_entry_band.status = UNRESOLVED`

then:

- parent `entry_range_status = ENTRY_RANGE_UNRESOLVED`;
- `preferred_entry_low/high = null`;
- `distance_to_band_pct = null`;
- `method = UNRESOLVED`;
- `combination_rule = UNRESOLVED`.

A resolved tactical band may still be reported as a **watch/support context**, but must not become preferred/fair entry by itself.

### 4.3 Fundamental resolved

If the fundamental band is RESOLVED:

- tactical RESOLVED:
  use the existing approved overlap/no-overlap combination rule;
- tactical UNRESOLVED:
  parent may remain RESOLVED using the evidence-backed fundamental band alone with `FUNDAMENTAL_ONLY`, if the existing option contract supports that exact result.

No averaging of unrelated bands.

### 4.4 Non-WAIT branch

For `new_buyer in {ATTRACTIVE, AVOID}`:

- parent status = `NOT_APPLICABLE`;
- fundamental status = `NOT_APPLICABLE`;
- tactical status = `NOT_APPLICABLE`;
- preferred numeric fields = null;
- method/combination rule = `NOT_APPLICABLE`.

Do not add price targets to non-WAIT outputs in this task.

## 5. Structural schema requirement

Do not rely only on prompt prose.

Create a **shadow-only versioned schema branch** that structurally distinguishes:

1. WAIT candidate/output branch;
2. non-WAIT candidate/output branch.

Preferred implementation is a discriminated/conditional schema or equivalent typed union such that structurally valid output cannot express:

`WAIT + tactical NOT_APPLICABLE`.

Bump the shadow contract/schema version because this changes shadow-output admissibility. Do not change production Stage-2 v4.

Keep the hard semantic validator as an independent second gate.

## 6. Required red/green controls before model call

Before any inference, execute explicit generic fixtures:

1. WAIT + fundamental UNRESOLVED + tactical NOT_APPLICABLE -> **FAIL**.
2. WAIT + fundamental UNRESOLVED + exact tactical candidate RESOLVED -> **PASS**, parent remains UNRESOLVED.
3. WAIT + fundamental UNRESOLVED + tactical UNRESOLVED -> **PASS** when unresolved reason is supplied.
4. WAIT + no safe tactical resolution -> tactical `UNRESOLVED`, never NOT_APPLICABLE.
5. WAIT + fundamental RESOLVED + tactical RESOLVED overlap -> parent RESOLVED.
6. WAIT + fundamental RESOLVED + tactical RESOLVED no overlap -> existing conservative no-overlap rule.
7. WAIT + fundamental RESOLVED + tactical UNRESOLVED -> `FUNDAMENTAL_ONLY` where supported.
8. Technical-only band + fundamental UNRESOLVED -> preferred price numbers remain null.
9. Non-WAIT + all entry components NOT_APPLICABLE -> PASS.
10. Non-WAIT + resolved preferred entry output -> FAIL.
11. Renamed generic identity controls preserve identical policy behavior.
12. No ticker/company/country condition exists.

Old M12CN MU/SKHY failure may be used only as a **structural negative fixture**, never as a target label.

## 7. Entry-range catalog preservation

Do not alter M12CM facts or create new valuation facts.

Do not broaden valuation inputs in this task.

Keep the currently implemented evidence-backed valuation methods exactly as provided by the existing catalog builder.

If many WAIT subjects remain `ENTRY_RANGE_UNRESOLVED` because fundamental valuation inputs are absent, that is **coverage evidence**, not permission to manufacture prices.

The complete fresh result must report:

- WAIT count;
- parent resolved/unresolved count;
- fundamental resolved/unresolved count;
- tactical resolved/unresolved count;
- tactical candidate availability vs selection;
- unresolved reasons by archetype/method;
- price-band methods used;
- arbitrary-discount count (must be 0).

This data will inform a later Chat decision about whether more deterministic valuation-source methods are needed.

## 8. Blindness and no target tuning

Until all 8 new shadow outputs are frozen:

Do not semantically open or use as prompt material:

- independent assistant judgment;
- prior monitoring-AI verdicts;
- prior three-way comparison;
- M12CN partial shadow labels/outcomes beyond the redacted structural failure described in section 3.

Cryptographic verification is allowed.

The model receives only:

- exact frozen M12CM facts/context;
- exact independently frozen accepted Fundamental Core;
- approved generic policy principles;
- new shadow schema/prompt/ref catalog.

Target-label leak count must be 0.

## 9. Fresh shadow execution

After schema/prompt/contracts/tests are frozen, create a **new generation ID** and run all 8 Stage-2-style shadow calls from call 1:

- US: 5 batches
- KR: 3 batches

Use the exact M12CM batch topology and accepted Fundamental Core.

Fundamental Core model calls = 0.

Hard execution rules:

- one attempt per call;
- retry 0;
- repair model 0;
- judge 0;
- fallback model 0;
- selective rerun 0;
- per-ticker rerun 0;
- previous M12CN output reuse 0;
- cross-generation stitching 0;
- post-call hotfix 0.

First unexpected hard failure stops subsequent dependent calls and preserves the generation as failed.

No same-generation relaxation.

## 10. PASS requirements

`M12CN_R1_POLICY_CALIBRATION_SHADOW_PASS_READY_FOR_CHAT_REVIEW`

requires all of:

- generic static controls PASS;
- schema structurally forbids WAIT + NOT_APPLICABLE component state;
- all 8 calls complete;
- all 22 subjects semantically accepted;
- no fabricated entry price;
- target-label leak count 0;
- data-quality/confidence policy preserved;
- archetype classification remains identity-generic;
- production runtime behavior change count 0;
- output freeze complete before reference opening;
- exactly one post-freeze descriptive comparison;
- no retuning after comparison.

Agreement with any prior human/AI labels is descriptive only and is NOT a PASS criterion.

## 11. Post-freeze comparison

Only after all 22 fresh shadow outputs are frozen, open the packaged post-freeze reference material once and compare:

- M12CM production AI;
- independent assistant judgment;
- M12CN-R1 shadow.

Report:

- per-axis agreement counts;
- 3-axis exact agreement;
- label distributions;
- archetype distribution;
- BUY/WAIT/HOLDABLE frequency;
- holder REVIEW reasons;
- data-quality directional effects;
- WAIT entry-range resolved/unresolved coverage;
- key qualitative disagreements.

Do not run a second inference or tune after seeing the comparison.

## 12. Production integration remains forbidden

Even after PASS:

- production policy unchanged;
- production Stage-2 v4 unchanged;
- deployment readiness = NO;
- scheduler unchanged;
- production sends/intents/DB writes = 0;
- broker read/order/modify/cancel = 0;
- no main merge or remote push.

Return to Chat. Chat decides whether to:
- integrate the generic policy;
- expand deterministic valuation-input coverage first;
- revise/reject the shadow policy.

## 13. Required artifacts

At minimum:

- `source-base-integrity.json`
- `m12cn-failure-reproducer.json`
- `wait-entry-component-applicability-contract.json`
- `shadow-schema-version-and-diff.json`
- exact prompt/schema source
- `generic-policy-control-matrix.json`
- `entry-range-catalog-coverage.json`
- `blindness-and-target-leak-proof.json`
- `shadow-call-ledger.json`
- all 8 inputs/raw outputs where executed
- `shadow-output-freeze-manifest.json`
- `shadow-22-subject-results.json`
- `entry-range-coverage-and-methods.json`
- `holder-review-reason-analysis.json`
- `valuation-vs-overall-direction-analysis.json`
- `post-freeze-three-way-comparison.json`
- `post-freeze-three-way-comparison.md`
- `production-integration-impact-map.md`
- full/focused/frozen test results/JUnit/logs
- Ruff / git diff --check
- `safety-counters.json`
- `complete-blocker-ledger.json`
- `program-completion.json`
- `REPORT.md`
- artifact manifest and external ZIP SHA sidecar.

## 14. Validation baseline

M12CN submitted baseline:

- focused: 64 passed / 0 failed;
- full: 4,185 passed / 63 skipped / 0 failed;
- Treasury/KRX: 121 passed / 0 failed;
- Ruff: PASS;
- git diff --check: PASS.

No test deletion or skip inflation.

## 15. Terminal states

Use:

- `M12CN_R1_POLICY_CALIBRATION_SHADOW_PASS_READY_FOR_CHAT_REVIEW`
- `M12CN_R1_SHADOW_CONTRACT_REPAIR_PASS_EXECUTION_BLOCKED`
- `M12CN_R1_POLICY_CONTRACT_GAP_REQUIRES_CHAT_DECISION`
- `M12CN_R1_POLICY_CALIBRATION_SHADOW_FAILED`

A completed shadow remains non-production evidence only.
