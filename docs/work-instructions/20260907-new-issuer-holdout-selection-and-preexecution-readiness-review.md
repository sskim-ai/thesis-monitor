# Thesis Monitor — New Issuer Holdout Selection & Pre-Execution Readiness Review

## 0. Task identity and authorization boundary

Work-instruction filename:

```text
20260907-new-issuer-holdout-selection-and-preexecution-readiness-review.md
```

Result bundle:

```text
thesis-monitor-20260907-new-issuer-holdout-selection-preexecution-readiness-review-report.zip
```

This is a **bounded selection and pre-execution readiness review** following successful reference-universe expansion and issuer/market audit reconciliation.

It is not another US universe expansion or runtime-identity repair by default. Inspect the accepted artifacts first; do not reopen closed repairs without direct contradictory evidence.

Authorized sequence:

```text
verify latest evidence
→ preserve canonical exclusion and deterministic candidate order
→ reconcile primary/reserve source-status scopes
→ review US4 + KR12 proposal independently by market
→ review source periods, evidence provenance and price-readiness boundaries
→ prepare a non-executable proposed cohort / source manifest
→ validate actual future request construction without model calls
→ produce a selection/pre-execution decision
→ stop
```

Hard boundary for THIS task:

```text
new_real_investment_model_invocation_count = 0
model_backed_fictional_canary_count = 0
real_first_a_b_c_execution_count = 0

final_real_holdout_activation = 0
executable_proof_source_lock_created = 0
production_activation = 0
```

A proposed selection manifest and its SHA-256 are allowed. They are review artifacts, not an authorization to execute FIRST. Do not turn a review manifest into a final proof source lock or feed it into a real model.

Only a separately authorized subsequent task may finalize an executable proof generation and run FIRST/A/B/C. A review PASS is not ownership proof.

## 1. Authoritative input and precedence by concern

Newest measured result:

```text
thesis-monitor-20260907-bounded-us-supported-universe-expansion-issuer-audit-reconciliation-report.zip

SHA-256:
12ed21a8fcd378036fb86e08193fcffb5b3e0f9f0710f92602a2f3c595c18cf4
```

Recompute the ZIP hash. Check CRC, duplicate members, safe paths, internal index membership, byte sizes and hashes before using the evidence.

Independent bundle review found:

```text
ZIP members = 1309
indexed payload files = 1308
index self-exclusion = artifact-index.json only
indexed hash mismatches = 0
indexed byte-size mismatches = 0
unexpected unindexed payloads = 0
```

Those counts describe this input, not the expected size of the new result.

Authority is concern-specific:

- Historical facts: the newest supplied result and its exact preserved artifacts.
- Current code/configuration: actual repository HEAD/worktree.
- Authorized work: this instruction.
- Investment/source/runtime semantics: frozen repository contracts and Investment Thesis Analysis & Monitoring Knowledge Guide.
- Older handoffs: context only where not superseded.

Use `reports/proofs/24-program-completion.json` as the finalized historical completion.
The bundled `evidence/program-summary.json` retains packaging placeholders in some fields; do not parse those as final results or overwrite the finalized completion from them.

An unexplained material conflict is a reportable blocker, not permission to silently reconcile facts.

## 2. Accepted historical state — repair versus real proof

Latest completed task reports:

```text
status = PASS
repair_readiness = PASS
readiness = READY_FOR_NEW_ISSUER_HOLDOUT_SELECTION_REVIEW
next_scope = NEW_ISSUER_HOLDOUT_SELECTION_REVIEW_ONLY

US fundamental-source-sufficient diagnostic issuers = 4
KR fundamental-source-sufficient diagnostic issuers = 12
dual_market_diagnostic_source_readiness = PASS

identity_repair_regression_status = PASS
actual_request_identity_preflight_status = PASS
model_free_simulated_invocation_count = 64
model_free_identity_failure_count = 0

market_manifest_conflicts_before = 48
market_manifest_conflicts_after = 0
actual_routing_impact = REPORTING_ONLY_CONFIRMED

new_real_model_invocation_count = 0
new_real_subject_output_count = 0
model_backed_fictional_canary_count = 0
final_real_holdout_created = 0
final_proof_source_lock_created = 0
FIRST / A / B / C = NOT_RUN
ownership_generalization_verdict = NOT_ESTABLISHED
```

Submitted logs report:

```text
focused tests: 22 passed
full pytest: 2648 passed, 2 warnings
Ruff: PASS
git diff check: PASS
```

These are historical test results, not proof of the current worktree. Run applicable tests for changes made in this task.

An independent offline review also checked the 64 bundled simulated outputs against their exact schemas and matched actual prompt/schema/output/receipt/manifest identities, subjects and market counts:

```text
US4 contexts = 16
KR4 contexts = 48
schema / identity / market / selected-artifact hash mismatches = 0
```

This remains model-free artifact evidence. No actual investment output was obtained by the latest task.

## 3. Repository provenance and instruction-first commit

Latest reported provenance:

```text
base_sha = 11a3139bd672b11b8187cd9b1187d7971bf89839
work_instruction_commit = c29fac688ead6cd18331e98f91907e8332e0afba

implementation_commit =
eb5c6b929438ba7780d4959f5da702e33f64216f

implementation_freeze_commit =
eb5c6b929438ba7780d4959f5da702e33f64216f

final_head_sha =
edd24c8bd0bf1d79d8bd49a875bf609eb90752eb

branch =
codex/20260907-bounded-us-universe-expansion-issuer-reconciliation
```

Before any implementation change record:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Classify differences from the reported implementation and final HEAD. Report code versus documentation/packaging differences separately; do not assume every later commit is semantic drift.

Commit this work instruction before implementation. Record its exact commit.

No reset, merge, cherry-pick, unrelated worktree discard, or production deployment is authorized. If changes affect investment/source semantics, identity binding, live guard or canonical transport and cannot be explained, stop implementation.

## 4. Narrow mutation surface and production isolation

Allowed on an isolated non-production branch/artifact root:

```text
selection-review orchestration
candidate/reserve status accounting
proposed cohort and source-manifest serialization
model-free pre-execution checks using existing code
regression tests for changed review tooling
result packaging/finalization
```

Reuse the accepted reference adapter, official issuer mappings, source assemblers, runtime binding and market-manifest producer. Do not expand reference coverage again merely because more listed securities exist.

Not authorized:

```text
investment architecture or threshold changes
source-sufficiency relaxation
sector/framework overrides to make a candidate pass
ticker-specific exceptions
generic source/parser repair discovered during this review
prompt or investment-schema semantic changes
removing identity consts or accepting multiple runtime IDs
guard/transport redesign, timeout changes or retries
paid-provider/credential changes
live DB/cache/watchlist writes
scheduler changes, Telegram production sends, V2 activation
Monitoring Bootstrap implementation
Night Futures mutation
```

If a genuine implementation defect outside review/report tooling is discovered, preserve evidence and propose a separate bounded repair. Safe independent work in the other market may continue, but do not label blocked readiness PASS.

Prove that edited code and cache roots are not imported/written by live US/KR monitoring. If isolation cannot be established, stop mutation.

## 5. Preserve precise universe units and membership

Use the latest snapshot's set definitions:

```text
supported security ≠ canonical issuer
canonical issuer ≠ unseen supported issuer
unseen supported issuer ≠ fundamental-source-sufficient issuer
fundamental sufficiency ≠ complete investment information
fundamental readiness ≠ all price/technical inputs available
```

Latest verified snapshot accounting:

| Field | US | KR |
|---|---:|---:|
| Raw reference rows | 13188 | 2539 |
| Supported securities | 52 | 2539 |
| Supported canonical issuers | 52 | 2539 |
| Excluded issuers within that supported set | 27 | 48 |
| Unseen supported canonical issuers | 25 | 2491 |

Do not describe 13,188 discovered listing rows as supported or source-ready.
The US route candidate universe is larger than the bounded 52-issuer supported snapshot; that does not require exhaustive route probing in this task.

Preserve these files and their hashes:

```text
evidence/membership/us-reference-membership.jsonl
evidence/membership/kr-reference-membership.jsonl
evidence/membership/us-set-reconciliation.json
evidence/membership/kr-set-reconciliation.json
evidence/membership/exclusion-registry.json
reports/proofs/23-next-holdout-selection-handoff.json
```

Recompute sets rather than copying scalar PASS:

```text
S = supported unique security IDs
I = canonical issuer IDs represented by S
E = all canonical exclusions
U = I minus E

|I| <= |S|
|U| <= |I|
U = I - E
U intersect E = empty
```

Unknown identity is not an unseen issuer. Do not infer corporate identity from ticker syntax, Korean-name normalization, currency, or assumed one-security/one-issuer relationships.

## 6. Exclusion registry and irreversible retirement

Latest canonical registry:

```text
actual-output-exposed securities = 66
actual-output-exposed issuers = 65
whole-cohort-retired issuers = 48
overlap between exposed and retired issuers = 28
canonical excluded issuer union = 85

65 + 48 - 28 = 85
```

Do not add overlapping counts or interpret the 66-to-65 unit correction as removal of an excluded issuer.

Canonical-JSON registry digest reported by the handoff:

```text
f91ec0a8ea6a224a5da3375da28d83f01b46c518e8b94a8da0df23398a3f2415
```

Raw-file SHA-256 of the same bundled registry:

```text
46aedb73eea4ca2040a3370214a7bd8b019d2d2b1b3d4980134df1c9b34a4a47
```

These are different hash bases, not conflicting registry contents.
Recompute the canonical digest with the declared canonicalization contract and verify the raw-file digest against the bundle index.
Do not compare a pretty-printed file's raw hash to the canonical-JSON digest and falsely stop on a mismatch.

If the registry has changed due to newly proven historical exposure, preserve old and new versions plus lineage. Never shrink it to fill a target.

Minimum whole-cohort exclusions remain:

```text
NVDA JPM WMT BRK-B
142210 060900 002680 035420
216050 100700 001530 487580
038870 342870 060230 415380

ORCL UNH KO AVGO
095570 058860 246960 099520
403870 014790 079810 060980
061970 012030 225190 245620

PLTR V MA AMZN XOM DIS NKE MCD
033920 104480 071320 096240
032860 060570 016600 462520
```

These lists are not the full 85-issuer registry.

Retirement applies to the entire precommitted cohort, including subjects that did not return output, and to alternate supported share classes of the same issuer.

Actual output rejected by an identity gate still counts as real exposure.
Source-only diagnostics and clearly labelled model-free simulations do not consume real-model unseen status.

If current historical lineage is unresolved, quarantine the issuer rather than declare it unseen. This task does not authorize arbitrary retroactive removal of exclusions.

## 7. Preserve accepted identity and market repairs

KR historical count root cause is reported as:

```text
KOREAN_NAME_ASCII_STRIP_AND_COLLISION
```

The accepted correction uses OpenDART corp_code, not a stripped company-name key. The input snapshot has 2539 distinct supported corp_code identities; 48 excluded gives 2491 unseen.

Market manifests must come from verified explicit packet/context market:

```text
market ∈ {kr, us}
manifest market counts = actual context market counts
sum(market counts) = subject_count
```

Do not reintroduce ticker.isdigit() or default-to-US inference.

Retain source identity separately from runtime identity:

```text
source_generation_id
source artifact manifest / source lock identity
per_subject_packet_hashes
```

versus:

```text
runtime_generation_id
run_id
stage
batch_id
invocation_id
ordered_subjects
output_contract
```

The current output `packet_id` contract is runtime_generation_id.
Actual prompt, actual reopened schema file, validator, receipt, output and manifest must agree under one binding. Historical source IDs remain immutable.

## 8. Starting candidate evidence — not a finalized cohort

The input diagnosed six US candidates in order:

```text
1 NVMI  PASS
2 SKYH  PASS
3 YARW  FAIL
4 WKSP  PASS
5 DMII  FAIL
6 EROC  PASS
```

Known US source failures:

```text
YARW:
  CLINICAL_REGULATORY_CURRENT
  LIQUIDITY_CASHFLOW_CURRENT

DMII:
  BUSINESS_CURRENTORSECTOR_OPERATING_CURRENT
  EARNINGS_FINANCIAL_CURRENTORLIQUIDITY_CASHFLOW_CURRENTORSECTOR_OPERATING_CURRENT
  validated_current_sec_financial_occurrence_unavailable
```

Do not reclassify these as transport failures or merely untested rows.

Starting proposed US4, subject to this review:

```text
NVMI / SKYH / WKSP / EROC
```

Starting proposed KR12, all diagnostic PASS:

```text
373160 / 452200 / 389470 / 380550
008970 / 047080 / 068270 / 475830
033160 / 079940 / 103140 / 278280
```

Treat these as source-only diagnostic outcomes, not stock recommendations or already authorized proof subjects.

All 16 reported price-timing readiness READY. Their technical context includes PARTIAL_SAFE; do not infer that every indicator is available.

## 9. Deterministic selection lineage and reserve reconciliation

Reuse the exact ordered candidate list in:

```text
reports/proofs/23-next-holdout-selection-handoff.json
```

The input selection salt was:

```text
20260907-bounded-us-universe-expansion-issuer-reconciliation-v1
```

Rank material:

```text
sha256(selection_salt|market|canonical_issuer_key|canonical_security_id)
```

Preserve the original reference snapshot, representative-share-class rule and exclusion hash when using this order. Do not choose a new salt after seeing diagnostic results.

Full US order:

```text
NVMI SKYH YARW WKSP DMII EROC
NU LNG TCI WMG ACHR ISOU SHOT PBLS
BNED CROX AWX WYNN DOX DXYZ NWS ASTI RMD VRAX MSFT
```

Correct scope accounting:

```text
25 eligible unseen supported issuers
= 4 fundamental PASS
+ 2 fundamental FAIL
+ 19 fundamental UNTESTED

21 non-primary supported issuers
= 2 known fundamental FAIL
+ 19 fundamental UNTESTED
```

The prior `untested_ranked_candidate_count=18` is scoped to the first 24-candidate budget.
The final full-order candidate MSFT is outside that first-24 scope, giving 19 globally untested.

Do not mark all 21 as `UNTESTED` or `SOURCE_SUFFICIENT`.
Publish disjoint memberships and both scope names.

Recommended reserve ledger statuses:

```text
IDENTITY_SUPPORTED_FUNDAMENTAL_UNTESTED
FUNDAMENTAL_SOURCE_FAILED
FUNDAMENTAL_SOURCE_SUFFICIENT_NOT_PRIMARY
QUARANTINED_IDENTITY_OR_SUPPORT
OUTSIDE_PRECOMMITTED_DIAGNOSTIC_BUDGET
```

These may be orthogonal fields rather than an overloaded enum.
A failed reserve can become eligible only after objective new source evidence and an explicitly versioned source diagnostic—not repeated attempts to obtain a desired result.

The prior buffer objective was eight identity/capability-supported reserves, not eight financial-source-tested reserves. Do not impose a new eight-full-source-pass condition just to manufacture extra work.

## 10. Review policy must precede new diagnostic requests

First write, hash and commit or immutably timestamp a review policy including:

```text
input ZIP / reference / exclusion hashes
candidate order and representative security rule
primary-selection rule
reserve scopes and statuses
source snapshot/as_of policy
freshness/refresh rules copied from existing contracts
objective replacement rules
request budgets and retries
cache isolation and natural-live coexistence rules
exact zero-model boundary
```

Default to offline reuse of the latest diagnostic artifacts where suitable. Do not fetch all 25 US or 2491 KR fundamentals.

If new source-only requests are necessary:

```text
US full fundamental evaluations: maximum 24 total this task
KR full fundamental evaluations: maximum 24 total this task
additional provider route checks: maximum 8, only for concrete support-change evidence
reference directory refresh: at most one per each of the existing four feeds, only if justified
per-resource attempts: 1
automatic retries: 0
```

Count rechecks of already diagnosed candidates within the same limits. Predeclare any lower limits. Do not extend caps after failures.

Do not add new providers, permissions, entitlements or credentials.
Preserve every failed attempt and stop reasons. A provider failure must not cause repeated silent requests.

Do not change the source-sufficiency contract, freshness tolerance or security basis to meet targets.

## 11. US and KR reviews remain independent

Review both markets even if an ordinary shortfall occurs in the first.

Required terminal matrix:

```text
BOTH_READY_FOR_SELECTION
US_BLOCKED_KR_READY
US_READY_KR_BLOCKED
BOTH_BLOCKED
```

Global safety/integrity failures may stop both; record the actual reason.

An ordinary US provider/source/identity shortfall does not justify skipping KR.
Conversely, a KR problem does not erase validated US evidence.

Diagnostic statuses from the input are historical facts. A current proposed selection requires explicit snapshot/basis compatibility, not unqualified reuse of stale scalars.

## 12. Source sufficiency, freshness and exact provenance review

For every proposed primary issuer preserve:

```text
canonical issuer/security identity and market
source requests and outcome lineage
framework and required-family coverage
source packet raw-file SHA-256 and byte size
canonical-JSON packet digest and canonicalization definition
official source document identity / period / filing_date / as_of
packet generated_at and assessment_date
fundamental-source status
price and technical readiness
security/accounting basis validation
unknowns and material limitations
```

The input packets use canonical JSON digests distinct from pretty-printed file byte hashes.
A local independent check reproduced the full-packet digest with:

```python
json.dumps(
    packet,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
).encode("utf-8")
```

Verify the repository contract before adoption. Preserve both raw-file hash and semantic/canonical hash; never compare them as if identical.

Do not claim the original raw SEC financial response is bundled merely because a source_payload_sha256 exists. Record retrieval/storage provenance and whether exact raw response bytes are present or only normalized facts. If an existing gate requires exact raw bytes and they are unavailable, report the limitation rather than inventing them.

Example of a period distinction to retain:
the input NVMI business/earnings evidence records `2025-FY` with filing date `2026-02-17`, while its identity profile as_of is `2026-09-02`.
That difference alone does not prove an error or omission.
Check the existing freshness/official-foreign-reporting contract and state the available evidence scope; do not relabel older annual financial evidence as a newer quarter.

Source sufficiency PASS means the unchanged required-family gate passed. It is not proof of comprehensive Initial Analysis coverage, all current-quarter metrics, or investment correctness.

Do not create undocumented stale thresholds or relax published ones. If a required check is unavailable, mark the specific review dimension NOT_MEASURED/BLOCKED.

## 13. Price, security and financial safety remain unchanged

Retain:

```text
valid fundamentals + valid available price
→ retain fundamental readiness and applicable timing readiness

valid fundamentals + safely unavailable price
→ fundamental readiness may remain valid
→ timing follows UNAVAILABLE_SAFE under the existing contract

future / malformed / conflicting price or invalid security basis
→ hard block remains
```

Do not drop a valid candidate merely to force every technical feature to be available.
Do not select replacements to obtain more attractive price trends or desired BUY/HOLD/SELL distributions.

Maintain:

```text
no quarter-EPS annualization to PER
no EPS/BVPS reverse engineering from provider multiples
no total-income/common/parent attribution substitution
no ADR/ordinary-share or currency-basis mixing
no invented balance-sheet/FCF/ROIC from provisional earnings
no price/supply as fundamental direction
no fabricated RSI/MACD/support/target/stop
```

Foreign issuer / ADR / ordinary-share basis must remain explicit where applicable. Do not infer it solely from US listing venue.

A framework or semantic financial bug outside the review scope requires a separate generic repair task, not a candidate-specific override.

## 14. Proposed selection and objective replacement

If compatible snapshot checks pass, the starting proposal is the first four US source-PASS issuers and the first twelve KR source-PASS issuers in the preserved deterministic lineage.

Publish a proposed ordered cohort with:

```text
US4
KR4
KR4
KR4
```

Do not mix markets or split four-subject contexts.

Replacement is permitted only before any real-model exposure and only for objective:

```text
newly proven prior exposure / retirement
identity or alias conflict
actual support loss
hard source validation failure
source insufficiency under unchanged rules
unavailable mandatory evidence under current contract
```

Use the precommitted reserve sequence. Known failures are not automatically promoted.
State whether using frozen diagnostic snapshot outcomes or a versioned current refresh, and apply the same selection rule consistently.

No replacement for expected output, company popularity, valuation attractiveness, source prose richness, latency speculation, or desired stability.

If a target cannot be met within budget, complete the other market's safe diagnostics and stop review with the exact unresolved condition.

Do not activate/finalize the real experiment cohort here. Use:

```text
selection_status = PROPOSED_REVIEWED
execution_authorized = false
```

## 15. Non-executable review manifest and exposure classification

Create a source/readiness review manifest containing the proposed subjects, markets, packet hashes, source periods, exclusions, candidate order, price-path status and code identities.

Required fields include:

```text
artifact_role = SELECTION_REVIEW_MANIFEST
executable = false
model_execution_authorized = false
proof_source_lock = null
source_manifest_sha256
```

Hash the review manifest once finalized; do not call this an executable proof source lock.

Normal task output:

```text
proposed_cohort_output_exposure_state = UNEXPOSED
proposed_cohort_semantic_revelation_state = NOT_MEASURED
holdout_activation_state = NOT_ACTIVATED_REVIEW_ONLY
future_unseen_eligibility = CONDITIONAL_ON_PRE_EXECUTION_RECHECK
ownership_generalization_verdict = NOT_ESTABLISHED
```

Do not retire source-only candidates solely because source data were inspected.
Do not promise future eligibility if intervening model experiments may expose the issuer.

If an unauthorized real invocation/output occurs, stop immediately, preserve lifecycle and exposure evidence, and report scope violation. Do not reset the counters or claim UNEXPOSED merely because a parser or identity validator rejected the output.

## 16. Model-free actual-request readiness review

Use the already repaired request construction, identity binding, guard and preservation code.
Do not change canonical runtime semantics for this review.

Required coverage:

```text
fresh and resumed runtime identities
FIRST / A / B / C
Directional Core / Price-Timing
all four context groups
available / PARTIAL_SAFE / UNAVAILABLE_SAFE fixture branches
pre-spawn failure and post-spawn receipt expectations
per-context preservation followed by applicable semantic audit
per-run gate before next run
```

Reuse the accepted 64-context fictional fixture as baseline. Re-run it if review tooling or request construction changes; historical PASS is not a new execution claim.

Additionally construct future real-subject requests in a strict dry-run path from the proposed packets. Reopen actual prompt/schema files and check IDs, market, subject order, alias ownership, permitted data domains, file paths and hashes.

Do not call a real model to validate those requests.

Simulation-only source/binding hashes may be created for request rehearsal under an unmistakable model-free artifact mode.
They are not a finalized executable real-proof source lock and cannot authorize a real adapter.
Keep the canonical runtime identity semantics intact when constructing those fixture bindings.

Where timing requires core output, use visibly labelled deterministic fixtures only:

```text
artifact_mode = MODEL_FREE_REAL_INPUT_REHEARSAL
synthetic_adapter_output = true
real_investment_output = false
```

Such fixtures test wiring only. They are not investment judgments and must not enter the real-model exposure registry or generalization counts.

Do not weaken a schema to make a fixture pass. If a real-subject dry-run path cannot be exercised without semantic code change, report that blocker and stop the affected scope.

Model-free validator output must never be described as measured real-output ownership.

## 17. Guard and lifecycle checks — no stale authorization

Use existing live-workload coexistence semantics:

```text
protected natural-live window → do not launch heavy shadow work
active natural/model workload → block/defer as existing contract requires
observation unavailable → fail closed
```

Read actual current schedule/configuration at execution time when required; do not reuse old hardcoded clock windows.

No `ps` PermissionError bypass. No fallback from observation failure to zero contention.
No fabricated receipt for pre-spawn failure.

Required lifecycle distinctions:

```text
PRE_SPAWN:
  model_spawn_started = 0
  transport_receipt_expected = 0
  original guard exception preserved

POST_SPAWN:
  use actual lifecycle evidence
  receipt expectations follow canonical transport contract
```

This task does not actually spawn an investment model; post-spawn branches are fixtures.
A passing model-free guard review is not a permanent safe-to-spawn permit.
The future execution task must re-observe workload immediately before every heavy context.

Do not add unattended scheduling or background execution for the next proof.

## 18. Future proof contract — retained, not executed here

For the subsequent separately authorized real proof, retain frozen runtime values:

```text
model = gpt-5.6-sol
reasoning_effort = xhigh
batch_semantics = MODEL_CONTEXT_COUPLED
subjects_per_shared_context = 4
model_timeout_seconds = 1800
authoritative_timeout_owner_count = 1
```

Do not update these to newer model/CLI defaults as part of this review.

The future lifecycle remains:

```text
final implementation/configuration freeze
→ final source lock and binding
→ exact-path preflight and live coexistence recheck
→ FIRST
→ FIRST ownership / renderer / hard-safety gates
→ A only if all required gates pass
→ B only after A gates pass
→ C only after B gates pass
→ valid repeated-run stability/generalization audit
```

After each successful context, before the next:

```text
preserve exact raw model output
preserve actual prompt/schema and receipt/log evidence
record hashes, bytes, stage, batch, subjects and markets
run applicable offline context gates
```

Future real hard gates include:

```text
DIRECTIONAL_CORE_PRICE_TECHNICAL_REFS = 0
DIRECTIONAL_CORE_SUPPLY_REFS = 0
SUPPLY_DIRECTIONAL_CORE_USAGE = 0
BUY_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0
SELL_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0
DIRECTIONAL_MODEL_CALLS_ON_SOURCE_INSUFFICIENT = 0
PRICE_ONLY_DIRECTIONAL_MODEL_CALLS = 0

TIMING_STAGE_DIRECTION_MUTATION = 0
TIMING_STAGE_BALANCE_MUTATION = 0
TIMING_STAGE_HOLD_LEAN_MUTATION = 0
PRICE_TIMING_NEW_BUYER_UPGRADE = 0
PRICE_ONLY_HOLDER_REDUCE = 0
PRICE_ONLY_DIRECTIONAL_OWNERSHIP_VIOLATIONS = 0

FINAL_DIRECTION_OWNER = DIRECTIONAL_CORE
PRIMARY_USER_ACTION_WORDING_OWNER = RENDERER
AI_IMPERATIVE_PRIMARY_ACTION = 0
KNOWN_HARD_SAFETY_REGRESSION = 0
```

Unavailable stages remain NOT_MEASURED, not zero-violation PASS.
Count raw output, identity-accepted output, semantically audited output and violations separately.

No automatic model retry, same-cohort hotfix, remaining-subject continuation after failure, timeout increase, or batch splitting.
Precommitted FIRST/A/B/C repetitions are not retries.

Any partial real output consumes unseen status. Entire-cohort retirement rules remain.
Failure after clean FIRST must not reset FULLY_EXPOSED to PARTIALLY_EXPOSED.
No real result is generated in this review task.

## 19. Tests and evidence limits

For changed review/report tooling run focused tests plus repository-required full suite, lint and diff checks in a no-model configuration. Include commands, tested commit, exit status and logs.

Retain tests for:

```text
known source failure is not relabelled untested reserve
global versus budget-scoped untested count
raw-file versus canonical JSON hash distinction
excluded issuer blocks alternate share class
non-numeric KR identity retains explicit market=kr
missing/contradictory market does not default to us
current runtime ID is shared by actual prompt/schema/validator/receipt
pre-spawn original exception is not masked by missing receipt
model-free real-input fixtures never count as real exposure
review PASS cannot enable a real adapter
no network retries beyond policy
```

Do not execute model-backed tests under a misleading full-suite claim.
If the required test set cannot be run without model calls, report the exact limitation.

An offline artifact check is not an application test rerun.
A supplied command log is not independent confirmation of current live service behavior.

## 20. Success / blocked decision matrix

This task succeeds as selection review when:

```text
input integrity and repository isolation verified
all canonical exclusions preserved
candidate and reserve scopes reconciled
US4 and KR12 proposal meets unchanged identity/support/source rules
source periods/provenance/hash semantics documented
price-ready versus safe-absent versus hard-invalid paths preserved
model-free binding/market/preservation checks pass
no unmeasured mandatory pre-execution gate is hidden
real-model and production counters remain zero
```

Then report:

```text
selection_review_status = PASS
readiness = READY_FOR_SEPARATELY_AUTHORIZED_NEW_HOLDOUT_PROOF
next_scope = NEW_ISSUER_HOLDOUT_FINAL_FREEZE_AND_OWNERSHIP_PROOF

proof_executed = false
ownership_generalization_verdict = NOT_ESTABLISHED
```

Use a repository canonical equivalent with explicit mapping if available.

If blocked, distinguish:

```text
US_SELECTION_OR_SOURCE_REVIEW_BLOCKED
KR_SELECTION_OR_SOURCE_REVIEW_BLOCKED
BOTH_MARKETS_REVIEW_BLOCKED
IDENTITY_OR_EXCLUSION_RECONCILIATION_BLOCKED
SOURCE_PERIOD_OR_PROVENANCE_REVIEW_BLOCKED
MODEL_FREE_REQUEST_PATH_BLOCKED
LIVE_WORKLOAD_OBSERVATION_UNAVAILABLE
PRODUCTION_ISOLATION_UNPROVEN
REQUEST_BUDGET_EXHAUSTED
```

Do not automatically propose a broad repair when only a reporting dimension is unresolved.

No path ends at Monitoring Bootstrap yet. Only successful actual FIRST/A/B/C ownership proof can make Bootstrap Integration Review the next scope.

## 21. Required artifacts

Produce Markdown summaries plus machine-readable artifacts for:

```text
01-input-integrity-and-repository-provenance
02-accepted-latest-baseline-and-final-completion-authority
03-production-isolation-and-change-boundary
04-review-policy-and-request-budgets
05-exclusion-registry-continuity-and-alias-fence
06-supported-universe-snapshot-and-set-invariants
07-us-primary-reserve-status-reconciliation
08-kr-candidate-and-reserve-status-review
09-us-source-period-provenance-and-readiness-review
10-kr-source-period-provenance-and-readiness-review
11-dual-market-selection-review-decision
12-proposed-cohort-and-context-grouping
13-nonexecutable-source-review-manifest
14-packet-raw-and-canonical-hash-audit
15-runtime-identity-and-explicit-market-preflight
16-model-free-fullpath-and-fixture-mode-audit
17-guard-lifecycle-and-preservation-readiness
18-tests-lint-diff-and-freeze
19-production-no-change-and-zero-model-counters
20-next-proof-handoff-draft
21-program-completion
```

Include only the necessary immutable input references or copies to keep lineage understandable.
Do not overwrite historical artifacts.
Keep newly generated model-free fixtures separate from historical real outputs.

Every candidate row should include market, rank, issuer/security key, representative rule, source status, last evaluation snapshot, reserve role, failure reasons and exact artifact references.

## 22. Minimum completion fields

At minimum:

```text
base_sha / work_instruction_commit / implementation_commit / final_head_sha / branch
input_zip_sha256 / input_integrity_status
accepted_reference_snapshot_ids
exclusion_registry_hash_before / exclusion_registry_hash_after
exclusion_membership_removed_without_provenance
canonical_exclusion_issuer_count

us_unseen_supported_count
us_source_pass_count
us_known_source_fail_count
us_untested_global_count
us_untested_within_budget_count
us_identity_supported_nonprimary_count
us_source_sufficient_reserve_count

kr_unseen_supported_count
kr_review_attempted_count
kr_review_pass_count
kr_review_fail_count

proposed_us4 / proposed_kr12
proposed_context_grouping
selection_policy_hash
review_manifest_sha256
review_manifest_executable
executable_proof_source_lock_created

source_period_review_status
source_provenance_review_status
raw_and_canonical_hash_status
price_readiness_by_subject
mandatory_unknowns

actual_request_identity_preflight_status
explicit_market_preflight_status
model_free_simulated_context_count
model_free_real_input_request_count
model_free_fixture_exposure_registry_leak_count
guard_review_status
guard_authorization_requires_future_recheck

real_investment_model_invocation_count
real_subject_output_count
model_backed_fictional_canary_count
real_first_a_b_c_execution_count
ownership_generalization_verdict

investment_architecture_semantic_drift
source_sufficiency_policy_drift
prompt_schema_semantic_drift
runtime_identity_contract_drift
guard_transport_semantic_drift
historical_artifact_mutation

production_no_change
main_merge / production_db_mutation / production_cache_write
production_scheduler_change / production_telegram_send
monitoring_registration_calls / live_structured_autonomy_activation / live_v2_change
night_futures_code_mutation / night_futures_decision_packet_injection
natural_live_cancel_count

request_counts_by_market_and_provider
retry_count / budget_exhaustion
artifact_count / indexed_artifact_count
hash_mismatch_count / size_mismatch_count / unexpected_unindexed_files
secret_scan_status
selection_review_status / readiness / stop_reason / next_scope
```

Numbers mean actual counts; unexecuted semantic measurements remain NOT_MEASURED.
Do not use initialized zero-violation counters as proof when no relevant output was audited.

## 23. Finalization and artifact integrity

Freeze all payloads, including README, completion JSON/Markdown, program summary and handoff, before constructing `artifact-index.json`.

The index covers every payload file except itself:

```text
relative path
raw-file SHA-256
byte size
artifact class
historical / source-only / model-free
market / candidate / run / stage where applicable
```

No mutable finalized completion files outside the index.

Avoid stale placeholders in a file presented as the current final summary.
Either finalize the summary from the same canonical completion object or label an immutable intermediate snapshot unmistakably and link the final object.

Reopen the final ZIP and verify CRC, member uniqueness, indexed hashes and sizes, and unexpected unindexed files.

Do not attempt to include the final ZIP checksum inside the same ZIP as a self-referential payload. Write an external `.zip.sha256` sidecar after packaging.

Secret-bearing raw requests/logs must not be bundled. Preserve exact safe bytes or label redacted derivatives and hash the originals locally under the existing security policy.

## 24. Final task principle

The latest result removed the former narrow-universe bottleneck and corrected issuer/market reporting.
Do not turn that success into an unsupported claim that real ownership proof passed.

The next useful step is:

```text
reuse verified candidate evidence
→ make selection and reserve status exact
→ verify source/readiness and actual execution inputs without a model
→ freeze the review
→ hand off to a separately authorized real proof
```

Not:

```text
reopen closed runtime repairs by default
re-probe the whole US/KR market
promote every reserve as source-ready
change source gates to keep preferred names
run FIRST automatically from a review task
change existing production monitoring messages
```

Preserve the existing live US/KR behavior.

Complete the selection review without consuming real holdout evidence.
