# Thesis Monitor — Stage-2 Frozen-Core Claim-Language Validation Scope Repair + New Full22 Reproof

## 0. Task identity

Suggested work-instruction filename:

```text
20260916-stage2-frozen-core-claim-language-validation-scope-repair-full22-reproof.md
```

Suggested result bundle:

```text
thesis-monitor-20260916-stage2-frozen-core-claim-language-validation-scope-repair-full22-reproof-report.zip
```

Suggested phase name:

```text
M12CB — Stage-2 Frozen-Core Claim-Language Validation Scope Repair
```

This is a **bounded validator ownership-scope repair + wholly new frozen full22 reproof**.

It is NOT:

- a new investment-decision architecture,
- a change to overall BUY/HOLD/SELL semantics,
- a change to new-buyer ATTRACTIVE/WAIT/AVOID semantics,
- a change to holder HOLDABLE/REVIEW/REDUCE semantics,
- a reopening of Pre-Confirmation Asymmetry V2,
- a change to the M12CA `pre_confirmation_buy` lifecycle invariant,
- a change to maturity polarity,
- a change to Fundamental Core ownership,
- a relaxation of exact-ref integrity,
- a numeric-threshold relaxation,
- a ticker exception for SNDK/TSLA/TSM,
- a candidate auto-repair task,
- a selective rerun task,
- a production deploy/merge task,
- a Kiwoom live gateway configuration task.

The exact objective is:

```text
preserve the strict standalone full-candidate validator

+

when frozen Fundamental Core identity/ownership has already passed,
apply Stage-2-authored claim-language restrictions only to Stage-2-owned claims

+

keep all cross-field/canonical decision invariants strict

+

prove the repair with a wholly new US14 + KR8 full22 generation from call 1.
```

## 0.1 Integrated authoritative addendum

This revision directly incorporates the latest user-authorized source-of-truth. It supersedes conflicting wording in the earlier M12CB work-instruction draft and in the older M12BZ new-session handoff.

Source-of-truth priority is strictly:

```text
1. latest M12CA result ZIP
2. current repository state
3. prior M12BZ new-session handoff
```

The prior handoff `CURRENT_STATE.json` entry:

```text
GOOGL:preconfirmation_buy_flag_missing
```

is historical only and must not be treated as the current blocker. M12CA closed that contract.

The current blocker is exactly:

```text
FROZEN_CORE_EXACT_NUMERIC_SCOPE_FALSE_POSITIVE
affected = SNDK / TSLA / TSM
```

M12CB remains narrowly bounded to **validator ownership scope repair only**. Do not redesign or reopen Treasury, Kiwoom, three-axis, preconfirmation, polarity, typed-contract, or any other already-PASSed contract.

Operating workflow is frozen as:

```text
Chat: architecture/scope decision
→ Work/Codex: execute only the narrow authorized task
→ Chat: review the result again from the whole-system architecture perspective
```

If an implementation may already exist, inspect Git history and the existing canonical owner before writing new code. Do not create parallel ownership logic without proving that no canonical implementation exists.

---

# 1. Authoritative input/result

Use the supplied result as the authoritative latest completed phase:

```text
thesis-monitor-20260916-preconfirmation-buy-flag-contract-convergence-full22-reproof-report.zip
```

Expected SHA-256:

```text
8e227d7fb643999b6b9b50124c0c51b066ac871e414a1936c8fec32d5419bc99
```

Independently verify the ZIP hash before any code change.

Then verify `artifact-manifest.json` completely:

```text
artifact_count = 215
manifest payload entries = 215
ZIP file entries = 216 including artifact-manifest.json
hash mismatch = 0
size mismatch = 0
missing artifact = 0
secret scan failure = 0
```

Do not proceed on an integrity mismatch.

---

# 2. Authoritative repository provenance from M12CA

Use these corrected provenance values:

```text
origin_main_observed = 9b1fe2de10ff3a4d6b25b17bf1b6e24e5a5ac479
base_documentation_sha = 29878d2ecc5ff96add09b25fb7fe0fb2b216b43e
implementation_branch = codex/20260916-m12ca-preconfirmation-buy-contract-convergence
implementation_sha = 663d69eade2ba601c0248635d5656dec242563dc
final_local_sha = bba14f8d81d9a3de77b3d50244aa62146dede01e
```

Important correction:

```text
previous draft label: base_main_sha = 29878d2...
correct meaning:       base_documentation_sha = 29878d2...
actual observed origin main: 9b1fe2de...
```

Never treat `29878d2...` as the actual origin main. The previous `base_main_sha` wording was semantically incorrect and is superseded by this section.

Before changing anything, record actual current repository state:

```text
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse main
git rev-parse origin/main
git log -n 20 --oneline --decorate
```

Interpret provenance according to the frozen source-of-truth priority:

```text
latest M12CA result ZIP > current repository state > prior M12BZ handoff
```

If the latest M12CA result state and actual checkout disagree materially, classify the divergence before implementing. Do not silently substitute another branch or reinterpret `base_documentation_sha` as a mainline SHA.

---

# 3. Freeze M12CA as a successful Pre-Confirmation contract convergence

M12CA did **not** fail on the original GOOGL contract.

The following are solved and must be frozen:

```text
historical contract = preconfirmation-asymmetry-decision-engine-v2
historical work instruction = 46bdf4c
historical implementation = c0c9139babb06ead11112aea072a67ef364a9b22
reuse classification = HISTORICAL_PRECONFIRMATION_CONTRACT_ALREADY_CANONICAL_BUT_PROMPT_BYPASSED
```

Canonical lifecycle invariant recovered by M12CA:

```text
pre_confirmation_buy required when:
  decision = BUY
  AND at least one decisive driver maturity is EARLY or PARTIAL

pre_confirmation_buy=true additionally requires:
  asymmetry = FAVORABLE
  factual_safety_state != BLOCKED
  all six explanation claims present

flag/explanation invariant:
  flag=true  <=> explanation is non-null
  flag=false <=> explanation is null
```

Independence rules are frozen:

```text
pre_confirmation_buy independent of new_buyer_axis
pre_confirmation_buy independent of holder_axis
pre_confirmation_buy independent of timing
pre_confirmation_buy independent of price-confirmation status
```

Do not rewrite or weaken these rules in M12CB.

---

# 4. Freeze the GOOGL success

M12CA proved this exact valid combination:

```text
ticker = GOOGL
overall_direction = BUY
directional_balance = 6.0 / 4.0
overall_maturity = PARTIAL
asymmetry = FAVORABLE
pre_confirmation_buy = true
new_buyer = WAIT
holder = HOLDABLE
timing = UNFAVORABLE
semantic_validator_status = PASS
contract_convergence = PASS
```

This is a regression fixture for M12CB. It is also proof that the old `GOOGL:preconfirmation_buy_flag_missing` blocker is closed and must not be revived from stale handoff state.

M12CA convergence additionally froze:

```text
preconfirmation semantic validation = PASS
mechanical new-buyer mapping count = 0
price-confirmation contamination count = 0
```

Never reinterpret this as:

```text
BUY => ATTRACTIVE
pre_confirmation_buy => favorable timing
pre_confirmation_buy => price confirmation passed
```

All are false mappings.

---

# 5. M12CA deterministic baseline

Freeze the completed local checks:

```text
focused tests = 115 passed
wider tests = 208 passed, 4 skipped
full pytest = 4050 passed, 63 skipped, 2 warnings
ruff = PASS
git diff --check = PASS
```

Freeze production firewall results:

```text
production_db_mutations = 0
assessment_production_writes = 0
warning_production_mutations = 0
notification_production_queue_writes = 0
production_sends = 0
scheduler_mutation_count = 0
automatic_monitoring_resume = 0
main_merges = 0
deployments = 0
remote_push_count = 0
raw_model_artifact_remote_push_count = 0
```

---

# 6. Exact M12CA full22 proof state

Do not resume or stitch this generation:

```text
generation_id = 20260916-uskr22-m12ca-20260916T021457Z-663d69eade2b
planned calls = 16
started = 9
completed = 9
usable = 9
resume_allowed = false
```

Proof state:

```text
US Fundamental Core = 14/14 valid
Stage-2 schema valid = 12
Stage-2 semantic valid = 9
KR Stage-2 = NOT RUN
final composition = NOT REACHED
```

Hard-failure batch:

```text
US Stage-2 batch 4
SNDK
TSLA
TSM
```

Terminal proof state:

```text
PRECONFIRMATION_CONVERGENCE_PROVEN_FULL22_BLOCKED_BY_NEW_VALIDATOR_SCOPE_FAILURE
```

Retry/fallback/judge/repair/selective rerun all remained zero.

---

# 7. Exact new blocker

The failure classification is:

```text
FROZEN_CORE_EXACT_NUMERIC_SCOPE_FALSE_POSITIVE
```

Affected tickers:

```text
SNDK
TSLA
TSM
```

Observed error:

```text
freeform_exact_numeric_claim
```

Critically:

```text
stage2_owned_exact_numeric_claim_count = 0
frozen_core_exact_numeric_claim_count = 4
```

Therefore this is **not evidence that Stage-2 authored forbidden exact numbers**.

It is evidence that a Stage-2 validation path is revalidating frozen Fundamental Core prose with a rule whose scope belongs to Stage-2-authored prose.

---

# 8. Concrete failure examples — freeze, do not special-case

Examples from the failed M12CA batch include:

SNDK frozen core:

```text
"컨센서스 선행 PER 6.5026배는 선행 이익 기준 밸류에이션 부담을 완화한다."
```

TSLA frozen core:

```text
"선행 PER 145.9029배이고 후행 PER은 역사적 95.5백분위로 이익 대비 밸류에이션 부담이 크다."
```

TSM frozen core:

```text
"AI/HPC 수요·첨단공정 강점과 잠정 60.3% 영업이익률이 보유 논리를 지지하되 해외 팹 비용의 마진 희석은 점검해야 한다."
```

and:

```text
"2026년 2분기 잠정 영업이익률 60.3%는 높은 수익성을 보여준다."
```

Do not solve this with:

- ticker allowlists,
- number allowlists,
- PER-specific exemptions,
- 60.3%-specific exemptions,
- regex weakening,
- threshold changes.

The repair must be based on **field/claim ownership**, not content exceptions.

---

# 9. Root cause — freeze exactly

Authoritative root cause from M12CA:

```text
_validate_preconfirmation_candidate receives Stage2-owned claims only for the
unsupported-metric check, but exact-number and general prose checks still iterate
candidate_claims(candidate), which includes frozen Fundamental Core claims.
```

Current shape:

```text
validate_preconfirmation_candidate(...)
  -> _validate_preconfirmation_candidate(
       unsupported_metric_claims=candidate_claims(candidate)
     )

validate_preconfirmation_stage2_owned_semantics(...)
  -> _validate_preconfirmation_candidate(
       unsupported_metric_claims=stage2_owned_candidate_claims(candidate)
     )
```

But inside `_validate_preconfirmation_candidate`:

```text
claims = candidate_claims(candidate)
for claim in claims:
    claim_not_korean
    order_command_language
    fixed_score_language
    invented_target_price_language
    freeform_exact_numeric_claim
    unknown_evidence_ref
```

So only `unsupported_metric_or_inference` is currently ownership-scoped.

That is the path-convergence defect.

---

# 10. No-repeat / canonical-owner rule

Before implementing any new code, assume an existing implementation may already exist until proven otherwise.

1. Search current source, Git history, prior M12B* commits, archived reports, tests, reflogs/worktrees if available.
2. Specifically locate the introduction of:
   - `stage2-frozen-core-ownership-v1`
   - `stage2_owned_candidate_claims()`
   - `validate_preconfirmation_stage2_owned_semantics()`
   - `accepted_v2_stage2_validation_scope_manifest()`.
3. Determine whether a broader scoped-claim validator already existed historically.
4. Reuse the existing ownership inventory/helper if possible.
5. Do not create a second Stage-2 ownership taxonomy.
6. Identify the canonical owner before adding any helper, validator path, inventory, or semantic abstraction.
7. Prefer reuse/convergence of an existing canonical path over parallel new code.

Expected likely classification:

```text
EXISTING_STAGE2_OWNERSHIP_SCOPE_HELPER_INCOMPLETE_APPLICATION
```

But prove it; do not force this label.

---

# 11. Canonical ownership boundary

Current frozen top-level Fundamental Core fields are:

```text
ticker
decision
holder_axis
directional_balance
buy_drivers
sell_drivers
balance_summary
confidence
decisive_reason
```

Cross-stage identity field:

```text
fundamental_core_sha256
```

All remaining candidate fields are Stage-2-owned.

Existing helper:

```text
stage2_owned_candidate_claims(candidate)
```

must remain the single source of truth for the Stage-2-owned prose claim set unless historical provenance proves a better existing canonical helper.

Do not duplicate this list in another validator.

---

# 12. Trust preconditions before scoped Stage-2 validation

Scoped Stage-2 validation is allowed only after the existing frozen-core ownership gate has passed.

Preserve these trust preconditions:

```text
fundamental_core_schema_valid
fundamental_core_canonical_semantic_valid
fundamental_core_sha256_exact
frozen_core_fields_exact_copy
no_core_mutation
```

Operationally, preserve the current fail-closed structure:

```text
ownership_errors = validate_accepted_v2_candidate_ownership(...)

if ownership_errors:
    use strict standalone/full-candidate validation path
else:
    use trusted Stage-2-owned semantic scope
```

A candidate with a mutated frozen core must never gain an exemption merely because a field would otherwise be outside Stage-2 scope.

---

# 13. Required scope decision before code change

Audit every check in `_validate_preconfirmation_candidate` and classify it as one of:

```text
A. FULL-CANDIDATE CROSS-FIELD INVARIANT
B. FULL-CANDIDATE OWNERSHIP/IDENTITY INVARIANT
C. STAGE2-AUTHORED CLAIM-LANGUAGE INVARIANT AFTER TRUST
D. STANDALONE-ONLY FULL-CANDIDATE CLAIM-LANGUAGE INVARIANT
```

At minimum explicitly classify:

```text
claim_not_korean
order_command_language
fixed_score_language
invented_target_price_language
freeform_exact_numeric_claim
unknown_evidence_ref
unsupported_metric_or_inference
```

Also inspect, but do not casually move:

```text
directional_balance_language_errors
balance_summary_not_korean
directional_balance_unregistered_numeric
market_expectation evidence-category ownership
pricing requirement evidence-category ownership
asymmetry evidence-category ownership
pre_confirmation_buy invariants
post_confirmation_hold invariants
factual safety invariants
maturity date ownership
logical-condition validation
```

The repair must be justified by ownership semantics, not simply by the fact that a test turns green.

---

# 14. Intended repair boundary

The expected architectural shape is:

```text
_validate_preconfirmation_candidate(
    packet,
    candidate,
    *,
    claim_language_claims=...,
    unsupported_metric_claims=...,
)
```

or one equally small equivalent abstraction.

Standalone path:

```text
validate_preconfirmation_candidate
  claim-language scope = candidate_claims(candidate)
  unsupported-metric scope = candidate_claims(candidate)
```

Trusted Stage-2 path:

```text
validate_preconfirmation_stage2_owned_semantics
  claim-language scope = stage2_owned_candidate_claims(candidate)
  unsupported-metric scope = stage2_owned_candidate_claims(candidate)
```

Do not implement this exact signature mechanically if the historical code proves a cleaner canonical design.

The invariant matters more than the parameter name.

---

# 15. Standalone strictness must remain unchanged

This is mandatory.

`validate_preconfirmation_candidate(packet, candidate)` is the standalone full-candidate validator.

After M12CB it must still reject a candidate containing a forbidden exact numeric free-form claim anywhere in the full candidate where the standalone contract previously rejected it.

Expected regression:

```text
standalone full-candidate exact-numeric failure = preserved
```

Do not globally weaken `_EXACT_NUMBER`.

Do not change error names merely to pass tests.

---

# 16. Trusted Stage-2 scope must be exact

For `validate_preconfirmation_stage2_owned_semantics` after frozen-core trust:

```text
exact copied frozen-core claim
  -> not reclassified as a Stage-2-authored freeform exact-number violation

Stage-2-owned exact numeric claim
  -> still hard FAIL: freeform_exact_numeric_claim
```

Likewise, if general claim-language checks are proven to be Stage-2-authored constraints under the ownership contract, apply them only to Stage-2-owned claims after trust.

Do not exempt Stage-2-owned prose.

---

# 17. Frozen-core mutation must fail before any exemption

Required negative fixture:

1. Build a valid frozen Fundamental Core.
2. Build a Stage-2 candidate.
3. Mutate a frozen core field or text in the combined candidate.
4. Even if the mutation would otherwise fall outside Stage-2 claim-language scope, validation must fail through frozen-core ownership/identity.

Expected error class includes the existing canonical failure such as:

```text
price_timing_stage_mutated_fundamental_core
```

No mutation may become valid because of scoped claim-language validation.

---

# 18. No semantic change to exact numeric policy

M12CB changes **which owner is evaluated by which stage**, not what constitutes an exact numeric free-form claim.

Freeze:

```text
_EXACT_NUMBER regex semantics
freeform_exact_numeric_claim error meaning
canonical numeric evidence policy
numeric binding policy
```

Unless forensic proof shows the regex itself is independently wrong, which would be a new task and must stop this phase.

---

# 19. No model prompt/schema semantic change expected

M12CB should be a deterministic validator ownership-scope repair.

Expected:

```text
model_prompt_semantic_change_count = 0
model_schema_semantic_change_count = 0
preconfirmation_prompt_semantic_change_count = 0
```

Do not modify M12CA's recovered preconfirmation prompt rule.

If implementation discovers that a model-facing prompt/schema change is actually required, stop before model calls and produce a bounded design decision. Do not silently broaden M12CB.

---

# 20. Required focused fixtures

Create explicit tests for all of the following.

## FCS-P01 — frozen-core canonical exact numeric copied exactly

```text
ownership identity PASS
frozen core contains canonical exact numeric prose
Stage-2-owned exact numeric claims = 0
trusted Stage-2 semantic validation = PASS
```

Use generic fixtures; do not depend only on SNDK/TSLA/TSM.

## FCS-N01 — Stage-2-owned exact numeric remains hard failure

```text
frozen core clean
Stage-2-owned claim introduces exact numeric prose
trusted Stage-2 validation = FAIL
error = freeform_exact_numeric_claim
```

## FCS-N02 — mutated numeric frozen core fails ownership

```text
original frozen core valid
combined candidate modifies a frozen core numeric claim
ownership/identity = FAIL
no scope exemption
```

## FCS-N03 — standalone validator remains strict

```text
same candidate passed to validate_preconfirmation_candidate
full-candidate exact numeric rule remains active
```

## FCS-P02 — existing prospective ROIC frozen-core regression remains valid

Preserve the already-proved behavior:

```text
standalone full-candidate validator may flag unsupported metric
trusted Stage-2 path may accept an exact-copied frozen-core prospective condition
```

## FCS-N04 — Stage-2-owned unsupported metric remains hard failure

Preserve:

```text
ROIC/CCC/DSO/DPO/runway/FCF-yield etc. newly authored in Stage-2-owned fields
-> unsupported_metric_or_inference
```

## FCS-N05 — unknown Stage-2 evidence ref remains hard failure

If `unknown_evidence_ref` is classified as scoped claim validation after trust, prove a Stage-2-owned unknown ref still fails.

## FCS-N06 — frozen-core wrong ref/mutation fails before scoped validation

Do not allow a frozen claim with changed refs to bypass ownership validation.

---

# 21. Exact M12CA failed-batch offline replay

Before any new model call, use the captured M12CA US Stage-2 batch 4 output as an **offline regression fixture**.

Required properties:

```text
candidate bytes/model output must not be modified
no repair model
no candidate patching
no ticker exception
```

Expected after the ownership-scope repair:

```text
SNDK semantic PASS if no other real errors exist
TSLA semantic PASS if no other real errors exist
TSM semantic PASS if no other real errors exist
```

The audit must show:

```text
previous freeform_exact_numeric_claim came only from frozen-core claims
Stage-2-owned exact numeric claim count = 0
frozen-core identity = exact
```

If offline replay still fails, report the new genuine failure; do not weaken another validator merely to make the replay pass.

---

# 22. GOOGL offline regression

Replay the successful M12CA GOOGL output unchanged.

Require:

```text
overall_direction = BUY
overall_maturity = PARTIAL
pre_confirmation_buy = true
new_buyer = WAIT
holder = HOLDABLE
timing = UNFAVORABLE
semantic validation = PASS
```

Also prove:

```text
preconfirmation flag failure count = 0
preconfirmation explanation failure count = 0
mechanical new-buyer mapping count = 0
price-confirmation contamination count = 0
```

---

# 23. Preserve all previously closed contracts

Do not reopen these classes:

```text
fundamental-core-batch-identity-v1
fundamental-core-exact-ref-fidelity-v1
stage2-exact-ref-fidelity-v1
model-output-exact-ref-fidelity-v1
stage2-frozen-core-ownership-v1
stage2-maturity-polarity-adapter-v1
maturity-atomic-claim-identity-v1
decision-evidence-polarity-v1
post-confirmation HOLD maturity invariant
three-axis UX independence
expectation/valuation duplicate-anchor prevention
BusinessDelta hard semantics
price/timing fundamental ownership separation
```

Run their regression suites after the focused repair.

---

# 24. Deterministic pre-model gate

No model call until all are PASS:

```text
repository provenance
latest-result ZIP SHA verification
artifact-manifest verification
M12CA failure forensic reproduced
ownership-scope classification complete
standalone validator strictness fixture PASS
trusted Stage-2 frozen-core numeric fixture PASS
Stage-2-owned numeric negative fixture PASS
mutated-core negative fixture PASS
M12CA batch-4 offline replay PASS or genuine new deterministic blocker documented
GOOGL offline replay PASS
preconfirmation regression PASS
maturity polarity regression PASS
batch identity regression PASS
exact-ref regression PASS
typed-contract regression PASS
frozen-core ownership regression PASS
postconfirmation regression PASS
three-axis regression PASS
BusinessDelta regression PASS
full pytest PASS
ruff PASS
git diff --check PASS
```

If any deterministic gate fails, do not run the new full22 proof.

---

# 25. Frozen 22 proof cohort

Use exactly the same frozen cohort.

US 14:

```text
CORZ
CPNG
CRCL
GOOGL
HUT
IBM
MU
RXRX
SKHY
SNDK
TSLA
TSM
WRD
WULF
```

KR 8:

```text
000660
003690
005490
005930
010120
012450
047810
086280
```

Frozen packet SHAs:

```text
US = 2c01a21c887ca41512798199387120e8ded5afd2888f5b78a9c54ea59e975228
KR = 819af90aa5ff159ee77ef2be69fc115ad169631acc9cfcc101081bef4318b597
```

Do not refetch providers.

Do not mutate semantic packet content.

---

# 26. New full22 generation — mandatory

M12CA generation is terminal and cannot be resumed.

Create a wholly new generation from call 1.

Required:

```text
model = gpt-5.6-sol
effort = xhigh
fallback = none
judge = none
repair = none
selective rerun = none
per-ticker retry = none
candidate patching = none
cross-generation stitching = none
```

Freeze all inputs and hashes before model call 1.

Even though M12CB is expected to change only deterministic validation scope, the formal proof must run against one coherent generation under the repaired acceptance contract.

---

# 27. Proof execution rules

The runner must hard-stop on the first unusable/invalid batch.

Do not call an automatic repair route.

If the existing production runner normally invokes repair on validation failure, the frozen proof harness must convert that route into a terminal proof failure exactly as M12CA did.

Record for every call:

```text
ordinal
market
stage
batch
subjects
prompt SHA
schema SHA
ref catalog hash/count
identity hash
maturity atomic catalog hash/count where applicable
started_at
completed_at
output SHA
schema validation result
semantic validation result
transport attempts
```

---

# 28. Full22 PASS criteria

Require all 22 subjects to complete.

At minimum:

```text
fundamental_core_valid_count = 22
stage2_schema_valid_count = 22
stage2_semantic_valid_count = 22
final_composition_valid_count = 22
```

And:

```text
frozen_core_revalidation_false_positive_count = 0
stage2_owned_exact_numeric_failure_count = 0 for valid model outputs
frozen_core_scope_exemption_without_identity_count = 0
```

Also require:

```text
preconfirmation_flag_failure_count = 0
preconfirmation_explanation_failure_count = 0
preconfirmation_three_axis_violation_count = 0
maturity_atomic_identity_failure_count = 0
maturity_same_atomic_claim_overlap_count = 0
maturity_unproven_source_overlap_count = 0
stage2_typed_contract_violation_count = 0
stage2_exact_ref_violation_count = 0
stage2_fabricated_ref_count = 0
stage2_noncanonical_date_count = 0
postconfirmation_maturity_conflict_count = 0
price_timing_core_mutation_count = 0
price_timing_holder_mutation_count = 0
expectation_valuation_duplicate_anchor_count = 0
core_mutation_count = 0
canonical_bypass_count = 0
legacy_duplicate_semantic_participation_count = 0
mechanical_stance_mapping_count = 0
```

---

# 29. Special regression dossiers

Produce explicit dossiers for:

```text
GOOGL — M12CA pre_confirmation_buy convergence must stay PASS
SNDK — previous frozen-core numeric false positive
TSLA — previous frozen-core numeric false positive
TSM  — previous frozen-core numeric false positive
CORZ — prior three-axis regression
RXRX — prior three-axis regression
SKHY — prior technical-insufficient regression
IBM  — prior holder/new-buyer regression
```

Do not force their output enums.

The dossier is for contract validation, not target-output matching.

---

# 30. Three-axis rendering proof

If full22 reaches final composition, require all 22 user-facing outputs to visibly expose:

```text
종합 방향
신규 관찰자
보유자
```

Preserve semantic independence.

Do not render `pre_confirmation_buy` as a buy-now instruction.

Do not turn timing into fundamental direction.

`REVIEW` remains “보유 근거 재검토”, not automatic sell.

---

# 31. Market context — authoritative freeze, no redesign

Market context is frozen in M12CB. Do not redesign it, refetch it, or use it as justification to broaden validator scope.

## 31.1 Treasury historical/current contract

Freeze:

```text
provider = FRED
nominal series = DGS3 / DGS5 / DGS10 / DGS30
real-yield series = DFII10
breakeven series = T10YIE
historical final renderer commit = 4407cd11a78579e11681b503b2d4e72ee3c3d60f
daily semantics regression = PASS
per-series as-of regression = PASS
bp-change regression = PASS
```

Do not replace these series, reinterpret daily semantics, or modify renderer ownership in M12CB.

## 31.2 Kiwoom historical/local contract

Freeze:

```text
historical commit = 28f4f70700046f98d5d899ee491d3e5f45922e9a
KOSPI200 replay 2026-09-01 = PASS
KOSPI200 replay 2026-09-02 = PASS
KOSPI200 replay 2026-09-03 = PASS
local LeadingMarket adapter = PASS
KOSDAQ150 historical actual fixture = NOT_VERIFIED
```

Required live read-only configuration names are exactly:

```text
KIWOOM_GATEWAY_URL
KIWOOM_GATEWAY_API_KEY
KIWOOM_GATEWAY_TIMEOUT_SECONDS
```

Current live state:

```text
live gateway = UNAVAILABLE
live read/order/modify/cancel = 0/0/0/0
```

Only read-only Kiwoom access is authorized. Order permission is neither required nor allowed for this workflow.

No live Kiwoom gateway call or configuration work is part of M12CB.

Preserve all existing market-time-layer and market-context/fundamental-ownership regressions as PASS.

---

# 32. Deployment boundary

M12CB is still not a deploy phase.

Even if full22 passes:

```text
main merge = 0
deployment = 0
production sends = 0
production DB mutations = 0
scheduler mutations = 0
monitoring registrations = 0
monitoring stops = 0
automatic monitoring resume = 0
V2 production gates remain OFF
```

A full22 PASS only makes the message/model contract eligible for the next bounded phase.

---

# 33. Required post-M12CB sequence if full22 passes

If and only if the new full22 proof is 22/22 clean:

```text
message_model_contract_readiness = READY
```

This does **not** authorize deploy, merge, scheduler activation, production sends, or production automation.

The required next sequence is fixed and must be handled as separate bounded phases:

```text
1. Kiwoom read-only gateway configuration / verification
2. current US/KR market + ticker message smoke
3. independent human judgment using only the collected evidence
4. compare independent human judgment against AI output
5. decide whether deployment / automation should be authorized
```

The sequence must not be collapsed into M12CB. Even if a Kiwoom read-only gateway becomes available, do not skip the independent evidence-only human comparison step and do not infer deploy authorization from a 22/22 model-contract PASS.

Expected immediate next scope after a clean M12CB is therefore:

```text
next_scope = KIWOOM_READONLY_GATEWAY_CONFIGURATION_AND_VERIFICATION
```

Only after that separate phase is complete may Chat authorize the bounded current-market/current-ticker smoke phase.

---

# 34. Failure handling

## A. Existing ownership helper already supports this scope

Reuse it.

Do not add a duplicate claim inventory.

## B. The offline M12CA batch-4 replay passes after the bounded scope repair

Proceed through deterministic regressions, then new full22 from call 1.

Do not reuse M12CA outputs in the formal proof.

## C. Stage-2-owned numeric text still fails

This is expected strict behavior.

Do not relax it.

## D. A mutated frozen core passes scoped validation

STOP.

The ownership gate is broken.

Classification:

```text
FROZEN_CORE_TRUST_PRECONDITION_BYPASS
```

No model calls.

## E. Standalone validator becomes less strict

STOP.

Classification:

```text
STANDALONE_VALIDATOR_REGRESSION
```

No model calls.

## F. New full22 reaches a different hard failure

Do not hotfix inside M12CB.

Freeze the generation and produce the smallest next bounded scope.

## G. New full22 passes 22/22

Do not deploy.

Close M12CB and return the result to Chat for whole-system review. The next bounded execution scope is Kiwoom read-only gateway configuration/verification only. Current-market message smoke, independent human evidence-only judgment, AI comparison, and any deploy/automation decision remain later separate steps.

---

# 35. Required forensic artifacts

Produce numbered artifacts at least:

```text
01-repository-provenance
02-m12ca-result-integrity
03-m12cb-scope-freeze
04-m12ca-proof-freeze
05-m12ca-batch4-failure-forensic
06-stage2-validation-scope-code-audit
07-stage2-field-ownership-inventory
08-claim-check-scope-classification
09-historical-scope-helper-provenance
10-reuse-classification
11-validator-repair-decision
12-model-facing-change-classification
```

---

# 36. Required implementation/test artifacts

Produce:

```text
13-claim-language-scope-implementation
14-standalone-validator-strictness-proof
15-frozen-core-exact-numeric-positive-fixture
16-stage2-owned-exact-numeric-negative-fixture
17-mutated-frozen-core-negative-fixture
18-frozen-core-prospective-metric-regression
19-stage2-owned-unsupported-metric-negative-fixture
20-stage2-owned-unknown-ref-negative-fixture
21-m12ca-batch4-offline-replay
22-googl-preconfirmation-offline-regression
23-preconfirmation-regression-suite
24-maturity-polarity-regressions
25-batch-identity-regressions
26-exact-ref-regressions
27-stage2-typed-contract-regressions
28-frozen-core-postconfirmation-regressions
29-three-axis-core-timing-expectation-regressions
30-business-delta-regressions
31-full-local-test-result
32-ruff-diff-result
33-model-validator-hash-manifest
```

---

# 37. Required new full22 proof artifacts

Produce:

```text
34-frozen22-input-identity-manifest
35-new-full22-generation-manifest
36-full22-call-plan
37-fundamental-core-model-artifacts
38-stage2-model-artifacts
39-stage2-owned-claim-scope-audit
40-frozen-core-numeric-scope-audit
41-preconfirmation-flag-audit
42-preconfirmation-three-axis-independence-audit
43-fundamental-core-batch-identity-audit
44-exact-ref-fidelity-audit
45-stage2-typed-contract-audit
46-maturity-polarity-audit
47-frozen-core-ownership-audit
48-postconfirmation-maturity-audit
49-price-timing-immutability-audit
50-expectation-valuation-audit
51-business-delta-audit
52-canonical-semantic-audit
53-final-composition-audit
54-per-ticker-result-matrix
55-googl-regression-dossier
56-sndk-tsla-tsm-scope-regression-dossier
57-corz-rxrx-skhy-ibm-regression-dossier
58-three-axis-render-audit
59-full22-reproof-decision
```

---

# 38. Required market-context freeze artifacts

Produce:

```text
60-kiwoom-restoration-regression
61-treasury-restoration-regression
62-market-time-layer-regression
63-market-context-fundamental-ownership-negative-tests
64-kiwoom-gateway-config-status
```

Artifact 61 must explicitly record the frozen FRED contract:

```text
DGS3 / DGS5 / DGS10 / DGS30 / DFII10 / T10YIE
historical final renderer commit = 4407cd11a78579e11681b503b2d4e72ee3c3d60f
```

Artifact 64 must explicitly record:

```text
required config names = KIWOOM_GATEWAY_URL / KIWOOM_GATEWAY_API_KEY / KIWOOM_GATEWAY_TIMEOUT_SECONDS
Kiwoom historical commit = 28f4f70700046f98d5d899ee491d3e5f45922e9a
KOSPI200 2026-09-01/02/03 replay = PASS
local LeadingMarket adapter = PASS
KOSDAQ150 historical actual fixture = NOT_VERIFIED
live gateway = UNAVAILABLE unless independently changed by repository/environment observation
live read/order/modify/cancel = 0/0/0/0 for the frozen M12CA state
authorized capability = READ_ONLY
```

No live call is required while the gateway remains unavailable, and M12CB must not request order permissions.

---

# 39. Required final decisions

Produce:

```text
65-stage2-validation-scope-convergence-decision
66-message-model-contract-readiness
67-market-context-readiness
68-deployment-readiness
69-next-scope-decision
70-master-workflow-update
71-program-completion
```

---

# 40. Program-completion fields

Include at least:

```text
origin_main_observed
base_documentation_sha
implementation_branch
implementation_sha
final_local_sha
legacy_base_main_sha_label_status = CORRECTED_NOT_USED

m12ca_result_zip_sha256
m12ca_result_integrity
source_of_truth_priority = M12CA_RESULT_ZIP > CURRENT_REPOSITORY_STATE > M12BZ_HANDOFF
old_googl_handoff_blocker_status = CLOSED_BY_M12CA
m12ca_generation_id
m12ca_failure_tickers
m12ca_failure_error
m12ca_failure_classification

stage2_validation_scope_contract
stage2_claim_scope_reuse_classification
standalone_validator_policy_changed
exact_number_regex_changed
model_prompt_semantic_change_count
model_schema_semantic_change_count
preconfirmation_prompt_semantic_change_count
canonical_semantic_policy_change_count

focused_test_result
wider_test_result
full_test_result
ruff_result
git_diff_check

frozen_us_packet_sha
frozen_kr_packet_sha
frozen_ticker_count

new_reproof_generation_id
planned_model_call_count
model_calls_started
model_calls_completed
model_calls_with_usable_output

fundamental_core_valid_count
stage2_schema_valid_count
stage2_semantic_valid_count
final_composition_valid_count

frozen_core_exact_numeric_claim_count_replayed
stage2_owned_exact_numeric_claim_count_replayed
frozen_core_revalidation_false_positive_count
stage2_owned_exact_numeric_violation_count
frozen_core_scope_exemption_without_identity_count
standalone_full_candidate_numeric_regression_status
mutated_frozen_core_rejection_status

preconfirmation_flag_failure_count
preconfirmation_explanation_failure_count
preconfirmation_three_axis_violation_count
maturity_atomic_identity_failure_count
maturity_same_atomic_claim_overlap_count
maturity_unproven_source_overlap_count
stage2_typed_contract_violation_count
stage2_exact_ref_violation_count
stage2_fabricated_ref_count
stage2_noncanonical_date_count
postconfirmation_maturity_conflict_count
price_timing_core_mutation_count
price_timing_holder_mutation_count
expectation_valuation_duplicate_anchor_count
business_delta_hard_failure_count
core_mutation_count
canonical_bypass_count
legacy_duplicate_semantic_participation_count
mechanical_stance_mapping_count

wrapper_retry_count
fallback_model_call_count
judge_call_count
repair_call_count
selective_rerun_count

googl_overall_direction
googl_overall_maturity
googl_pre_confirmation_buy
googl_new_buyer
googl_holder
googl_timing

sndk_regression_status
tsla_regression_status
tsm_regression_status
corz_regression_status
rxrx_regression_status
skhy_regression_status
ibm_regression_status

three_axis_visible_count
three_axis_missing_count

kiwoom_adapter_status
kiwoom_historical_commit
kiwoom_kospi200_20260901_03_replay_status
kiwoom_kosdaq150_historical_actual_fixture_status
kiwoom_gateway_configured
kiwoom_gateway_required_config_names
kiwoom_authorized_capability = READ_ONLY
live_read_order_modify_cancel_counts
treasury_provider = FRED
treasury_nominal_series
treasury_real_yield_series
treasury_breakeven_series
treasury_historical_final_renderer_commit
treasury_local_regression_status
market_context_readiness
message_model_contract_readiness
deployment_readiness

production_db_mutations
assessment_production_writes
warning_production_mutations
notification_production_queue_writes
production_sends
scheduler_mutation_count
automatic_monitoring_resume
main_merges
deployments
remote_push_count
raw_model_artifact_remote_push_count

top_level_result
next_scope

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count
```

Use explicit `NOT_*` values for anything not reached or not measured.

---

# 41. Expected clean result

If the validator ownership scope is repaired correctly and the full proof passes:

```text
top_level_result =
STAGE2_FROZEN_CORE_CLAIM_SCOPE_CONVERGENCE_FULL22_PASS

standalone_validator_policy_changed = false
exact_number_regex_changed = false
model_prompt_semantic_change_count = 0
model_schema_semantic_change_count = 0
preconfirmation_prompt_semantic_change_count = 0
canonical_semantic_policy_change_count = 0

fundamental_core_valid_count = 22
stage2_schema_valid_count = 22
stage2_semantic_valid_count = 22
final_composition_valid_count = 22

frozen_core_revalidation_false_positive_count = 0
stage2_owned_exact_numeric_violation_count = 0
frozen_core_scope_exemption_without_identity_count = 0

preconfirmation_flag_failure_count = 0
preconfirmation_explanation_failure_count = 0
preconfirmation_three_axis_violation_count = 0
maturity_atomic_identity_failure_count = 0
maturity_same_atomic_claim_overlap_count = 0
maturity_unproven_source_overlap_count = 0
stage2_typed_contract_violation_count = 0
stage2_exact_ref_violation_count = 0
stage2_fabricated_ref_count = 0
stage2_noncanonical_date_count = 0
postconfirmation_maturity_conflict_count = 0
price_timing_core_mutation_count = 0
price_timing_holder_mutation_count = 0
expectation_valuation_duplicate_anchor_count = 0
business_delta_hard_failure_count = 0
core_mutation_count = 0
canonical_bypass_count = 0
mechanical_stance_mapping_count = 0

GOOGL contract regression = PASS
SNDK scope regression = PASS
TSLA scope regression = PASS
TSM scope regression = PASS

three_axis_visible_count = 22
three_axis_missing_count = 0

message_model_contract_readiness = READY
market_context_readiness = LOCAL_PASS_LIVE_KIWOOM_UNAVAILABLE
or a later independently proven read-only live state

deployment_readiness = NO
next_scope = KIWOOM_READONLY_GATEWAY_CONFIGURATION_AND_VERIFICATION
```

No output enum is to be forced merely to match a prior generation.

---

# 42. Final principle

M12CA proved that the historical Pre-Confirmation BUY contract was already correct and that the current path had omitted its prompt invariant.

That blocker is closed.

The new failure is different:

```text
Frozen Fundamental Core owns a canonical numeric statement

+

Stage-2 copies that frozen core exactly

+

frozen-core identity/ownership passes

+

Stage-2 validator re-runs a Stage-2-authored freeform-number rule over all candidate claims

→ false positive
```

The correct M12CB repair is therefore:

```text
recover/reuse the existing Stage-2 ownership scope

→ preserve strict standalone full-candidate validation

→ preserve frozen-core identity/mutation gates

→ scope Stage-2-authored claim-language restrictions to Stage-2-owned claims only after trust

→ do not relax numeric semantics

→ do not change the model prompt/schema unless a new bounded design problem is proven

→ replay the failed M12CA batch offline unchanged

→ freeze deterministic regressions

→ run a wholly new US14 + KR8 generation from call 1

→ stop on the first genuine new hard failure

→ only after 22/22 PASS declare the message/model contract READY

→ still do not deploy inside M12CB

→ return to Chat for whole-system review

→ next bounded phase: Kiwoom read-only gateway configuration/verification

→ then current US/KR market + ticker message smoke

→ then independent human judgment using only collected evidence

→ compare human judgment with AI output

→ only then decide deployment/automation authorization.
```
