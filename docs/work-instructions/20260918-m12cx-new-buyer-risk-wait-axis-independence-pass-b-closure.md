# Thesis Monitor — M12CX New Buyer Risk-WAIT Axis Independence & Pass-B-Only Closure

## 0. Task identity

Work-instruction filename:

`20260918-m12cx-new-buyer-risk-wait-axis-independence-pass-b-closure.md`

Suggested result bundle:

`thesis-monitor-20260918-m12cx-new-buyer-risk-wait-axis-independence-pass-b-closure-report.zip`

This is a **bounded Pass-B semantic-policy repair + Pass-B-only fresh rerun using the already accepted fresh M12CW Pass-A fixture**.

It is NOT:

- a Pass-A rerun;
- a broad investment-policy redesign;
- a prompt tuning exercise to force desired labels;
- a ticker-specific TSM fix;
- a market/fundamental refresh;
- a production Stage-2 integration;
- a deployment/scheduler/broker task.

Pass-A external model calls: **0**.

Pass-B external model calls: **8 maximum**.

Production application/runtime/config behavior changes: **0**.

## 1. Exact source state

Verify M12CW-R1 result:

- ZIP SHA-256:
  `e337f34f31086b56bd0a3c1307f298f91cb30c3d83623a360ad7d04c24874727`
- Artifact manifest:
  229 declared payloads, 229/229 hash/size PASS.
- Repository implementation:
  `b63726d9c1a97886a842a304a433a5fb55166288`
- Generation:
  `20260918-m12cw-r1-pass-b-resume-20260918T045103Z-b63726d9c1a9`
- Terminal:
  `M12CW_R1_PASS_B_FAILED`

Start the shadow repair from repository implementation:

`b63726d9c1a97886a842a304a433a5fb55166288`

Allowed code changes are shadow-only.

Production application/runtime/config files must not change.

## 2. Preserve closed work

Do not reopen:

- Pass-A architecture or output;
- provider-wire dialect repair;
- directional single-scalar balance;
- typed business evidence quality;
- security valuation basis;
- fundamental valuation policy;
- capability catalog concept;
- result-tree directory ownership repair;
- isolated preflight/idempotency repair;
- failure-surface ordering;
- deterministic entry-range materialization.

The only policy surface under review is the legacy cross-axis authorization of:

`WAIT / EXECUTION_OR_THESIS_RISK`.

## 3. Immutable fresh Pass-A upstream fixture

Use only the accepted fresh M12CW Pass-A fixture.

Exact hashes:

### Pass-A classification

`c3b6537ecd75e2fc4fee685f2390275316bc14aea2f03ed045273199a1be58be`

### Pass-A freeze manifest

`44d82ba1ba774ef5725e461ff41ffeb2c8bb7ba6941bcf1d5b61ea82de97c7ea`

### Fundamental materialization

`1dc87de7336e90a50b8748d10693484c46a9357b910ba2738ad4db9d319e1737`

### Business quality

`c111b63410fc734935760a25b8432cc03920c051930b95bba8c74a9fd72cac60`

### Security valuation basis

`db583a58be65f1396b556dbb23a3a555c931c0c3296fd591402979e3e2156716`

### Existing capability catalog baseline

`d9c011ce46da40217461e4bda55d6e8f698271217b75aa040468c71abc76f568`

Before any repair:

- bind all fixture hashes;
- verify 22/22 subjects;
- verify Pass-A external calls in M12CX = 0.

If fixture binding fails:

`M12CX_FRESH_PASS_A_FIXTURE_BINDING_FAILED`

with external model calls = 0.

## 4. Exact current failure reproduction

Replay the archived M12CW-R1 TSM row.

Required reproduced facts:

- overall = HOLD
- thesis_state = INTACT
- holder = HOLDABLE
- new_buyer = WAIT
- new_buyer reason class = EXECUTION_OR_THESIS_RISK
- selected New Buyer refs belong to the subject-specific eligible material-risk catalog
- raw capability validation = PASS
- final materialized validator = FAIL
- error:
  `wait_without_authorized_structured_condition`

Required artifact:

`m12cw-r1-tsm-risk-wait-cross-axis-failure-reproducer.json`

Do not rewrite the archived model output.

## 5. Audit the exact legacy rule before code changes

Inspect:

- current source implementation of `wait_without_authorized_structured_condition`;
- related tests/fixtures;
- git history/blame for the rule;
- M12CR/M12CR-R1 semantic inventory;
- M12CV capability/validator parity matrix;
- all currently authorized WAIT conditions.

Determine precisely which conditions the current validator treats as sufficient for WAIT.

Separately identify the sub-condition represented in M12CV parity as:

`risk_wait_matches_selected_holder_or_thesis_state`.

Create:

`wait-authorized-condition-source-history-audit.json`

If the error code contains unrelated safety checks beyond the New-Buyer/Holder/Thesis coupling, preserve those as separate rules.

Do not delete the entire validator blindly.

## 6. Chat-approved three-axis independence contract

Freeze these semantics.

### Overall

Answers:

> Is the long-term company thesis/value direction intact, strengthening, mixed, impaired or invalidated?

Overall is not an entry-timing proxy.

### New Buyer

Answers:

> Is committing new capital at this point appropriate?

New Buyer may be more cautious than Holder even when the long-term thesis remains intact.

### Holder

Answers:

> Does an already-owned position remain reasonably holdable, or does it require review/reduction?

Holder REVIEW/REDUCE has its own material evidence threshold.

The three axes are related by shared evidence but are not mechanically nested.

## 7. Revised authorization for WAIT / EXECUTION_OR_THESIS_RISK

A New Buyer output:

`WAIT / EXECUTION_OR_THESIS_RISK`

is authorized when all are true:

1. the subject-specific Pass-B capability catalog exposes that branch;
2. the branch was exposed because:
   `material_bearish_business_evidence_available = true`
   under the existing frozen capability contract;
3. selected `new_buyer_decision.evidence_refs` are non-empty;
4. every selected ref belongs to the exact subject-local eligible material-risk ref catalog for that branch;
5. selected refs pass same-subject/meaning ownership validation;
6. the evidence is not valuation-only, security-basis-only or business-quality-confidence-only.

It does **not** additionally require:

- Holder = REVIEW/REDUCE;
- thesis_state in MIXED/IMPAIRED/INVALIDATED/UNRESOLVED;
- Overall = HOLD/SELL.

Therefore these combinations may be valid when independently supported:

- BUY / WAIT-risk / HOLDABLE
- HOLD / WAIT-risk / HOLDABLE
- BUY / WAIT-risk / REVIEW
- HOLD / WAIT-risk / REVIEW
- other combinations allowed by the independently frozen Overall/Holder rules.

Do not create a forced relationship merely to satisfy a validator.

## 8. Preserve independent Holder validation

Do not weaken Holder rules.

HOLDABLE remains valid when the selected Holder evidence does not meet REVIEW/REDUCE thresholds.

REVIEW still requires eligible:
- thesis uncertainty;
- evidence contradiction;
- execution deterioration;
- balance-sheet/material ownership risk;
- other frozen nonvaluation risk classes.

REDUCE still requires the stronger material-negative reason/evidence surface.

New Buyer WAIT-risk cannot automatically upgrade Holder to REVIEW.

## 9. Preserve independent Overall validation

Do not weaken Overall rules.

For durable/structural businesses:
- valuation/timing/security-basis alone cannot justify downgrade;
- non-BUY outcomes require eligible business/thesis/cycle/competitive/earnings/cash-flow evidence under the frozen contract.

For execution-dependent growth:
- the broader frozen execution-economics policy remains.

New Buyer WAIT-risk cannot automatically force Overall HOLD/SELL.

## 10. Replace the demonstrated cross-axis rule

After the source/history audit, version the relevant rule.

Retire only the sub-rule equivalent to:

`risk_wait_matches_selected_holder_or_thesis_state`

and replace it with a rule such as:

`risk_wait_requires_eligible_material_risk_evidence`

Stable naming is implementation-owned, but the semantics must match section 7.

Update:

- semantic-validator rule inventory;
- capability/validator parity matrix;
- Pass-B branch coverage;
- final materialized consistency validator.

Expected new parity:

### Capability schema

Deterministically owns whether the risk-WAIT branch is available.

### Cross-reference validator

Owns whether the model-selected refs actually belong to and semantically support that branch.

### No cross-axis holder/thesis prerequisite

Holder/thesis state is not part of the risk-WAIT authorization predicate.

## 11. Required offline fixtures

Before any external call add generic renamed fixtures.

### Must PASS

1. WAIT-risk + HOLDABLE + INTACT + eligible material-risk refs.
2. WAIT-risk + REVIEW + MIXED + eligible material-risk refs.
3. WAIT-risk + HOLDABLE + STRENGTHENING + eligible execution-risk refs, if Overall/Holder independent validators otherwise permit the row.
4. FUNDAMENTAL_UNRESOLVED + HOLDABLE + INTACT under its existing valid prerequisites.
5. TACTICAL_TIMING + HOLDABLE + INTACT under its existing valid prerequisites.

### Must FAIL

6. WAIT-risk + empty evidence refs.
7. WAIT-risk + valuation-only refs.
8. WAIT-risk + security-basis-only refs.
9. WAIT-risk + business-quality-confidence-only refs.
10. WAIT-risk + cross-ticker/unknown refs.
11. WAIT-risk where capability catalog did not expose the branch.
12. Holder REVIEW supported only by the New Buyer risk branch with no independently eligible Holder evidence.
13. Overall downgrade supported only by the New Buyer risk branch where the frozen Overall contract requires stronger/different evidence.

The TSM archived row is a snapshot regression fixture only, never a ticker rule.

## 12. Re-audit all remaining model/model cross-field validators

Do not stop at the demonstrated TSM error.

Inventory all Pass-B final validators whose predicate depends on **two or more model-authored fields**, especially:

- New Buyer reason vs Holder;
- New Buyer reason vs thesis state;
- Overall vs thesis state;
- Overall vs Holder;
- Holder vs thesis state.

For each classify:

- `VALID_INDEPENDENT_AXIS_SAFETY_RULE`
- `LEGACY_CROSS_AXIS_COUPLING_TO_RETIRE`
- `GENUINE_SHARED_EVIDENCE_CROSS_REFERENCE`
- `UNRESOLVED_REQUIRES_CHAT`

The goal is not to remove meaningful consistency checks.

The goal is to prevent one axis from being mechanically forced to a worse label solely to authorize another axis.

Required artifact:

`pass-b-model-axis-cross-field-rule-audit.json`

If another material legacy coupling is found and its intended policy cannot be resolved from existing Chat decisions/history, stop before model calls:

`M12CX_ADDITIONAL_CROSS_AXIS_POLICY_REQUIRES_CHAT`

## 13. Provider schema and capability builder

Do not add a joint schema that forces Holder/Thesis negative states merely to permit New Buyer risk-WAIT.

The existing subject-specific branch may remain model-visible when material risk evidence exists.

Regenerate all 8 Pass-B schemas after the shadow validator/policy version change.

Require:

- provider dialect PASS 8/8;
- unsupported provider keywords = 0;
- wire uniqueItems = 0;
- arrays/items complete;
- outbound request binding 8/8;
- analytical input drift from fresh M12CW A fixture = 0 except explicitly versioned B-policy/schema hashes.

## 14. Harness repair remains frozen

Preserve the M12CW-R1 harness fix.

Required reproof:

- result-tree directory collision reproducer still passes;
- live path does not call preflight builder against frozen evidence subtree;
- frozen subtree write/overwrite/delete count after freeze = 0;
- isolated preflight hash equality PASS;
- analytical request drift caused by filesystem mechanics = 0.

Do not reopen filesystem ownership.

## 15. B-only execution mode

After offline policy proof, create a new generation:

`mode = PASS_B_ONLY_AFTER_NEW_BUYER_AXIS_INDEPENDENCE_REPAIR`

Record:

- upstream fresh M12CW Pass-A generation;
- Pass-A aggregate SHA;
- deterministic materialization SHAs;
- capability-policy version;
- implementation commit;
- external harness SHA.

Pass-A model calls = 0.

## 16. Pass-B live topology

Run all 8 batches from batch 1.

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

Hard:

- one attempt;
- retry 0;
- repair model 0;
- fallback 0;
- judge 0;
- selective rerun 0;
- per-ticker rerun 0;
- prompt/schema/policy hotfix after call 1 = 0.

First hard B failure stops later calls.

Do not rerun A.

## 17. Validation order

For each B call:

1. persist raw output;
2. provider/raw-contract validation;
3. raw capability/semantic validation;
4. persist exact rule IDs;
5. stop on raw failure;
6. normalize;
7. deterministic directional balance;
8. deterministic tactical/entry materialization;
9. typed quality/basis validation;
10. final independent-axis policy validation.

No downstream envelope error may mask the primary rule.

## 18. B-only PASS requirements

Terminal:

`M12CX_PASS_B_AXIS_INDEPENDENCE_CLOSURE_PASS_READY_FOR_CHAT_CALIBRATION_REVIEW`

requires:

### Upstream

- Pass-A external calls = 0;
- fresh A fixture exact 22/22;
- deterministic upstream artifact hashes exact.

### Offline policy

- TSM archived failure now classified under the old coupling and the new rule passes it without rewriting the row;
- invalid risk-WAIT evidence fixtures still fail;
- Holder and Overall independent safety rules remain closed;
- unresolved cross-axis policy count = 0;
- capability/validator parity PASS;
- provider-wire schemas 8/8 PASS;
- target-label leak = 0.

### Live B

- 8/8 responses complete;
- 8/8 raw contract PASS;
- 8/8 raw semantic PASS;
- 22/22 normalized/materialized/final semantic PASS;
- PB_BALANCE_SUM 22/22;
- model-authored sell = 0;
- New Buyer consistency 22/22;
- Holder consistency 22/22;
- Overall consistency 22/22;
- impossible branch exposure 0.

### Safety

- production changes = 0;
- sends/intents/DB/scheduler/broker/merge/push/deploy = 0.

## 19. Combined analytical freeze

On B PASS, combine only:

1. fresh M12CW Pass A;
2. exact fresh deterministic materialization/capability input state;
3. new M12CX Pass B.

Create a provenance-rich combined result.

Do not claim uninterrupted same-process execution.

This combined result is valid for calibration review because Pass A's contract/input is unchanged by the New Buyer/Holder-axis repair.

Freeze all combined 22 rows and hashes before historical comparison access.

## 20. Pre-reveal analysis

Before revealing historical judgments, report:

- Overall distribution;
- New Buyer distribution;
- Holder distribution;
- directional buy-score distribution;
- risk-WAIT count;
- risk-WAIT + HOLDABLE count;
- risk-WAIT + REVIEW/REDUCE count;
- risk-WAIT by thesis state;
- fundamental resolved/unresolved;
- WAIT with resolved price range;
- WAIT with unresolved fundamental;
- Holder REVIEW reasons;
- execution-dependent growth outcomes;
- security-basis-unresolved outcomes.

For resolved WAIT ranges include exact price, method/tier, band, distance, tactical component and canonical refs.

## 21. One post-freeze three-way comparison

Only after combined freeze:

open the sealed comparison archive once.

Compare descriptively:

1. original M12CM production AI;
2. independent assistant blind judgment;
3. combined fresh M12CW-A + M12CX-B result.

Report:

- exact 3-axis agreement;
- Overall agreement;
- New Buyer agreement;
- Holder agreement;
- label distributions;
- BUY/WAIT/HOLDABLE frequency;
- Holder REVIEW frequency;
- changes in excessive conservatism;
- resolved WAIT price coverage;
- major differences for durable/core, structural cyclicals, execution-growth and security-basis-unresolved names.

Do not treat previous judgments as ground truth.

After reveal:
- model calls 0;
- policy edits 0;
- prompt/schema edits 0;
- threshold tuning 0.

## 22. Validation

Before live B:

- axis-independence tests;
- legacy rule/history audit;
- model-axis cross-field audit;
- capability fixtures;
- provider dialect 8/8;
- outbound binding 8/8;
- harness idempotency/collision reproof;
- focused;
- frozen-contract.

After live B:

- focused;
- frozen-contract;
- full suite;
- Treasury/KRX;
- scoped Ruff check;
- scoped Ruff format check;
- git diff --check.

No repo-wide mass formatting.
No test deletion or skip inflation.

## 23. Production boundary

Even on PASS:

- production Stage-2 unchanged;
- production investment policy unchanged;
- production entry-price schema unchanged;
- production sends/intents/DB writes = 0;
- broker read/order/modify/cancel = 0;
- scheduler changes = 0;
- main merge = 0;
- remote push = 0;
- deployment = 0.

Return to Chat.

## 24. Required artifacts

At minimum:

- `source-base-integrity.json`
- `m12cw-r1-chat-review-reconciliation.json`
- fresh Pass-A fixture binding
- `m12cw-r1-tsm-risk-wait-cross-axis-failure-reproducer.json`
- `wait-authorized-condition-source-history-audit.json`
- `new-buyer-risk-wait-axis-independence-contract.json`
- `pass-b-model-axis-cross-field-rule-audit.json`
- updated semantic-validator rule inventory
- updated capability-validator parity matrix
- axis-independence positive/negative fixtures
- all 8 regenerated Pass-B schemas/prompts/ref catalogs/contexts
- provider dialect scan 8
- outbound request binding 8
- harness collision/idempotency reproof
- B-only generation provenance
- all 8 raw outputs/logs where executed
- raw semantic validation artifacts
- B call ledger
- directional balance 22
- entry materialization 22
- New Buyer consistency 22
- Overall/Holder validation 22
- combined 22-subject result
- combined final freeze manifest
- pre-reveal analysis
- post-freeze comparison JSON/MD
- validation logs/JUnit
- scoped formatting proof
- safety counters
- blocker ledger
- program completion
- REPORT.md
- artifact manifest
- external result ZIP SHA sidecar.

## 25. Terminal states

Use one:

- `M12CX_PASS_B_AXIS_INDEPENDENCE_CLOSURE_PASS_READY_FOR_CHAT_CALIBRATION_REVIEW`
- `M12CX_FRESH_PASS_A_FIXTURE_BINDING_FAILED`
- `M12CX_WAIT_AXIS_POLICY_HISTORY_CONFLICT_REQUIRES_CHAT`
- `M12CX_ADDITIONAL_CROSS_AXIS_POLICY_REQUIRES_CHAT`
- `M12CX_PROVIDER_WIRE_REQUEST_DRIFT`
- `M12CX_PASS_B_FAILED`
- `M12CX_BLINDNESS_OR_TARGET_LEAK_FAILURE`
- `M12CX_NEW_PRODUCTION_DEPENDENCY_REQUIRES_CHAT`
- `M12CX_POSTRUN_VALIDATION_FAILED`

No state authorizes production integration automatically.

## 26. Hard safety

- Pass-A external model calls = 0
- Pass-B external model calls <= 8
- Fundamental Core calls = 0
- market refresh = 0
- production runtime/config behavior changes = 0
- production sends/intents/DB writes = 0
- broker read/order/modify/cancel = 0
- scheduler changes = 0
- main merge = 0
- remote push = 0
- deployment = 0.
