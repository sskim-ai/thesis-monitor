# Thesis Monitor — Bounded US Supported-Universe Expansion & Issuer-Audit Reconciliation

## 0. Task identity and boundary

Work-instruction filename:

```text
20260907-bounded-us-supported-universe-expansion-and-issuer-audit-reconciliation.md
```

Result bundle:

```text
thesis-monitor-20260907-bounded-us-supported-universe-expansion-issuer-audit-reconciliation-report.zip
```

This is a **reference-universe / issuer-identity / diagnostic-accounting task**, followed by bounded model-free source-readiness checks.

The current identity repair is not reopened. The purpose is to make genuinely new, supported issuers available without manufacturing support, weakening source sufficiency, or consuming another real holdout.

This task has four workstreams:

```text
A. Expand the small US supported reference universe generically.
B. Reconcile US/KR security-versus-issuer counts and exclusion sets.
C. Correct the simulation market manifest inconsistency.
D. Complete bounded US and KR source-readiness diagnostics without model calls.
```

This task DOES NOT authorize:

```text
any real investment model invocation
any model-backed fictional canary
FIRST / A / B / C execution
creation or activation of a final real ownership-proof cohort
a final ownership-proof source lock
architecture / prompt / investment-schema redesign
transport / guard / timeout redesign
Monitoring Bootstrap implementation
production monitoring or Telegram message changes
```

Do not automatically launch real proof when candidate diagnostics pass. Finish this task, freeze its evidence, and hand off to a separately authorized new-holdout selection/proof task.

Model-free stubs and offline validators are allowed. Official reference/source requests through approved adapters are allowed within precommitted budgets. These are not model calls.

---

## 1. Source of truth and verified input

Authoritative newest result:

```text
thesis-monitor-20260907-runtime-identity-lock-repair-fullpath-preflight-new-holdout-report.zip
SHA-256:
7e721fa8f28024b1f4e14d928dc860325e87e710b03c7552ea9bf18a81b50d31
```

Recompute the ZIP checksum before using it. A mismatch is an input-integrity stop.

Use concern-specific authority:

- The newest result records historical outcomes.
- Current repository HEAD/worktree records the actual implementation now.
- This instruction defines the authorized new scope.
- Current frozen repository contracts and the Investment Thesis Analysis & Monitoring Knowledge Guide define investment/evidence semantics.
- Historical files bundled under `historical/` remain historical, not newly executed results.

Do not silently reconcile conflicting facts. Report discrepancies with their original field names and locations.

### Input integrity measured during preparation of this instruction

```text
ZIP members = 1273
indexed artifacts = 1268
indexed SHA-256 / byte-size mismatches = 0
duplicate ZIP member names = 0
ZIP CRC check = PASS
```

Five files were intentionally not individually indexed:

```text
reports/18-program-completion.md
reports/README.md
reports/artifact-index.json
reports/artifact-index.md
reports/proofs/18-program-completion.json
```

The entire ZIP checksum covers them, but the internal index does not. Do not describe the prior index as covering all 1273 members. Section 24 establishes improved finalization for this task.

---

## 2. Historical baseline — keep repair and proof separate

The latest result reports:

```text
root_cause = RUNTIME_GENERATION_SCHEMA_CONST_MISMATCH
identity_repair_status = PASS
identity_binding_single_source = 1
actual_request_identity_preflight = PASS

all_core_schema_binding_status = PASS
all_timing_schema_binding_status = PASS
all_run_binding_status = PASS

whole_path_model_free_rehearsal_status = PASS
simulated_invocation_count = 64
model_free_real_model_call_count = 0

new_real_model_invocation_count = 0
new_ordered_cohort = []
new_source_generation_id = null
new_source_lock = null

FIRST / A / B / C = NOT_RUN
ownership_generalization_verdict = NOT_ESTABLISHED
proof_readiness = NOT_READY

stop_reason =
US_UNSEEN_SUPPORTED_ISSUER_COUNT_1_BELOW_TARGET_4

next_scope =
BOUNDED_US_SUPPORTED_UNIVERSE_EXPANSION_BEFORE_NEW_HOLDOUT
```

The 64 simulated contexts are:

```text
fresh / resumed
× FIRST / A / B / C
× DIRECTIONAL_CORE / PRICE_TIMING
× four batches
```

The report records 17 regression cases as PASS, including one positive control. Tests/lint/diff are reported PASS. Those statements describe the submitted result; this instruction does not claim repository tests were independently rerun outside that repository.

A separate local artifact review revalidated all 64 simulated outputs against their bundled schemas and checked runtime IDs and selected exact artifact hashes. Those checks passed. This is offline artifact validation, not model execution or real-output ownership proof.

Retain the distinction:

```text
identity/harness repair readiness = PASS
real investment ownership generalization = NOT_ESTABLISHED
```

---

## 3. Current universe facts and review findings

### 3.1 US — an actual supported-universe bottleneck

`reports/proofs/14-us-unseen-universe-audit.json` records:

```text
raw_supported_security_count = 33
canonical_supported_security_count = 32
canonical_issuer_count = 31

remaining_unseen_supported_issuer_count = 1
remaining_unseen_supported_issuers = [MSFT]
required_target = 4
target_feasibility = FAIL
```

The bundled predecessor's `15-us-supported-universe-root-cause.json` attributes the narrow universe to the provider's small static US symbol registry plus prior exposure exclusions. Its classifications include:

```text
INTENTIONAL_SUPPORTED_UNIVERSE_BOUNDARY
STALE_OR_INCOMPLETE_SECURITY_MASTER
EXPOSURE_REGISTRY_DOMINATES_UNIVERSE
```

This is not a claim that the US market has only one new company or that every other US company lacks financial data.

Inspect the current implementation before choosing how to expand support. A larger external listing directory is not by itself evidence that every listed security is supported end-to-end.

### 3.2 KR — reported count is internally inconsistent

`reports/proofs/15-kr-unseen-universe-audit.json` records:

```text
raw_supported_security_count = 2539
canonical_supported_security_count = 2539
canonical_issuer_count = 2411
remaining_unseen_supported_issuer_count = 2460
remaining_unseen_supported_issuers = a list of 2460 unique security-code strings
required_target = 12
target_feasibility = PASS
```

If the two issuer fields share one population and unit, a remaining subset cannot contain more issuers than the whole set:

```text
2460 > 2411
```

The bundle proves the count inconsistency, not its exact implementation cause. Possible explanations must remain hypotheses until code/row-level evidence resolves them.

Do not silently relabel 2460 as a corrected issuer count. Do not assume the 2460 strings represent 2460 distinct economic issuers. Do not declare the entire KR pipeline broken either.

The task must recompute the actual unique-issuer sets and publish a corrected count or an explicit unresolved state.

### 3.3 Simulation manifests misreport market mix

The independent artifact review found:

```text
64 simulated context manifests in total
16 actual US4 prompt contexts
48 actual KR4 prompt contexts

all 64 manifests report:
market_mix = {"kr": 0, "us": 4}
```

The actual prompts for the 48 KR contexts contain explicit `market: "kr"`. Thus:

```text
confirmed manifest-versus-prompt market discrepancies = 48
```

Example:

```text
simulation/resumed/model-contexts/C/PRICE_TIMING/batch-04/prompt.txt
simulation/resumed/model-contexts/C/PRICE_TIMING/batch-04/context_manifest.json
```

The corresponding runtime ID/schema/output checks passed. This is a confirmed reporting inconsistency; the bundle does not establish that a real KR model call was routed to US, nor that the identity fix failed.

Inspect the market field's producer and consumers. Correct a reporting-only derivation generically. If the defect also changes real routing or model semantic inputs, report the broader impact and do not silently perform a routing redesign here.

---

## 4. Repository provenance and instruction-first commit

Latest reported provenance:

```text
base_sha =
900880717b805b0112af1a784a1b016738fcd713

work_instruction_commit =
04311203142b997398a71eec1cc1def050559080

implementation_commit =
94fafaf9776937e73080f79a74bcf0c666f78f5c

implementation_freeze_commit / final_head_sha =
11a3139bd672b11b8187cd9b1187d7971bf89839

reported implementation_freeze_utc =
2026-09-07T11:30:02+09:00

branch =
codex/20260907-runtime-identity-lock-repair-fullpath-preflight-new-holdout
```

The timestamp field carries a `+09:00` offset despite its `_utc` name. Preserve the original and, if normalized, record the timezone conversion explicitly. Do not invent a real-spawn timestamp; none exists for that task.

Before implementation:

```text
git branch --show-current
git rev-parse HEAD
git status --short
```

Classify changes since the reported state. Do not reset, merge, cherry-pick, discard unrelated changes, or assume branch/HEAD identity.

Commit this work instruction before implementation. Record the exact new instruction commit.

Unexplained changes affecting investment architecture, source-sufficiency policy, runtime identity, guard, transport, or deployed behavior must be resolved or stop implementation. Unrelated documentation changes need not be treated as semantic failures.

---

## 5. Mutation surface and production isolation

Allowed on a non-production branch/snapshot:

```text
generic US reference-universe discovery/import
canonical issuer/security/alias reference mapping
supported-universe eligibility and capability reporting
experiment-only universe funnel/exclusion accounting
experiment-only market manifest construction
deterministic candidate/source diagnostics
tests, fixtures, and report packaging
```

Adding issuer support must be generic and provenance-backed. The code may change on an isolated branch; deployed production behavior must not change.

Before altering shared reference code, prove the checkout, process import path, reference/cache storage, and service configuration do not cause the edits to affect live monitoring. Use isolated fixtures/snapshots/caches. If live processes consume the edited tree directly and safe isolation cannot be established, stop implementation.

Forbidden:

```text
changing Directional Core / Price-Timing / composer / renderer semantics
changing decision thresholds or action ownership
relaxing source-sufficiency requirements
removing output schema identity consts
accepting both stale and current runtime IDs
changing accounting / ADR / valuation safety
changing runtime guard or canonical transport semantics
increasing timeout or enabling automatic model retries
modifying live DB / scheduler / Telegram / watchlist
deploying a new reference universe into production
activating live Structured Autonomy / V2
changing Night Futures
```

Explicit reporting:

```text
authorized_reference_universe_expansion = measured 0/1
authorized_issuer_audit_correction = measured 0/1
authorized_market_manifest_correction = measured 0/1

investment_architecture_semantic_drift = 0
decision_prompt_semantic_drift = 0
investment_schema_semantic_drift = 0
source_sufficiency_policy_drift = 0
canonical_transport_mutation = 0
guard_semantics_mutation = 0
production_activation = 0
```

New reference snapshots and new diagnostic packets will naturally have new hashes. Do not pretend their input contents are unchanged from historical cohorts. Preserve historical bytes while distinguishing authorized new diagnostic data from prohibited investment-semantic drift.

---

## 6. Define counting units before rebuilding any universe

Publish a unit contract and row schema before recalculating counts.

At minimum distinguish:

```text
raw reference row
provider symbol / alias
tradable security / share class
canonical issuer
supported security
supported issuer
unseen supported issuer
fundamental-source-sufficient issuer
price-timing-ready security
```

Each canonical security row must carry, when actually supported:

```text
market
canonical_security_id
canonical_issuer_key
issuer_key_namespace
display symbol
provider symbol / aliases
share class / security type
reference source and source-row identity
reference as_of / retrieval time
identity resolution status
routing/support capability status
eligibility decision and reason
```

Use existing authoritative issuer mappings. Do not manufacture issuer identity from ticker syntax, company-name similarity, currency, or an assumed one-security/one-issuer relationship.

For US CIK-backed mappings, verify the association and namespace; for KR use the supported canonical corporate identity. Dual listings and share classes require actual lineage. Where cross-market issuer identity is unresolved, quarantine rather than declare the listing unseen.

An unknown identity is not a new issuer.

---

## 7. Set-based funnel and exclusion reconciliation

For each market, materialize the membership of every set, not just scalar counts.

Suggested sets:

```text
R = raw reference rows
S = unique eligible supported securities
I = canonical issuers represented by S
E_output = issuers with actual prior real investment output
E_retired = issuers excluded by entire-cohort retirement
E_other = other pre-existing canonical exclusions
E_all = union(E_output, E_retired, E_other)
U = I minus E_all
```

Required invariants, using compatible snapshots and units:

```text
unique issuer count <= unique supported security count
unseen supported issuer count <= supported issuer count
U intersect E_all = empty
U = I minus E_all
sum(disjoint terminal candidate outcomes) = attempted candidate count
```

Publish both:

```text
global exclusion-set sizes
within-current-universe intersection sizes
```

Exclusion reasons overlap. Do not subtract several overlapping global counts as though they were disjoint removals.

For each eligible issuer, retain all exclusion reasons. A sequential waterfall may be provided, but label its order and disjoint deltas.

For KR, prove why 2411 and 2460 appeared in the prior report. If they have different snapshots or scopes, identify them. If one producer counted security codes under an issuer label, fix the generic count path and membership mapping. Do not repair the arithmetic by changing a label or taking max/min without lineage.

US and KR diagnostics remain independent: an ordinary US target shortfall must not abort KR reconciliation. A global integrity/safety stop may block both; report its exact reason.

---

## 8. Reconstruct and preserve the full exclusion registry

The latest result reports:

```text
prior_actual_output_exposure_registry_count = 66
whole_cohort_retirement_exclusion_count = 48
issuer_deduplicated_exclusion_count = 85
```

Treat these as historical reported counts, not three disjoint quantities to add.

Reconstruct the full row-level registry from relevant repository experiment history and the supplied artifacts. The result bundle's scalar counts are not a substitute for membership evidence.

For every exclusion record preserve:

```text
canonical issuer key
market / security aliases
generation and invocation lineage if applicable
actual real model spawn status
actual output-exposure status
whole-cohort retirement reason
other historical exclusion reason
source artifact path/hash
```

Do not shrink the exclusion set to meet a target. If newly verified identity mapping consolidates aliases, explain the count change while preserving every excluded issuer relationship. Unresolved historical rows remain quarantined, not eligible.

The latest retired 16 remain excluded:

```text
NVDA JPM WMT BRK-B
142210 060900 002680 035420
216050 100700 001530 487580
038870 342870 060230 415380
```

Both earlier cohorts remain excluded:

```text
ORCL UNH KO AVGO
095570 058860 246960 099520
403870 014790 079810 060980
061970 012030 225190 245620

PLTR V MA AMZN XOM DIS NKE MCD
033920 104480 071320 096240
032860 060570 016600 462520
```

These lists are minimum historical exclusions, not the complete registry. Do not reuse the latest KR12 merely because they had source PASS before their cohort was retired.

Fictional model-free simulation subjects are not real-issuer exposures. Source-only diagnostics with zero investment-model calls do not themselves consume an unseen holdout. Actual output rejected by an identity gate still counts as output exposure.

---

## 9. Prove the US reference-universe root cause in current code

Trace:

```text
reference provider / security master
→ supported symbol registry
→ canonical identity mapping
→ share-class alias resolution
→ market/security eligibility
→ provider capability
→ exposure exclusion
→ unseen candidate universe
```

Record function/module paths and exact filters with row counts.

Explain which boundary is:

```text
intentional product support limitation
small static discovery registry
stale/incomplete reference data
unavailable authoritative identity
unsupported provider route
actual lack of fundamental data
historical exclusion
```

Do not conflate the watchlist, an experiment fixture list, and the supported securities universe.

Confirm whether the frozen source pipeline can already process a generically resolved issuer beyond the tiny static discovery list. If yes, expand discovery through that supported path. If the pipeline genuinely cannot process additional security classes, report the capability blocker rather than advertising them as supported.

---

## 10. Generic US universe expansion

Prefer an existing approved, authoritative security/issuer reference adapter already available in the repository.

If a new reference feed integration is necessary, it may be added only as a bounded, generic reference-data adapter with:

```text
official/provider provenance
current documented field semantics
stable issuer/security identifiers
market and security-type classification
as_of / retrieved_at
raw reference snapshot and hash
deterministic normalization
cache/isolation policy
missing/ambiguous identity handling
tests
```

Do not add subscriptions, credentials, entitlements, or scrape unofficial lists to bypass actual support. Do not expose secrets in raw request logs.

Do not append a hand-picked list of familiar tickers simply to get four passing names. Do not make source logic depend on the desired cohort.

A name in a directory is only a discovered candidate. Promotion must be explicit:

```text
DISCOVERED
→ IDENTITY_RESOLVED
→ ROUTING_SUPPORTED
→ ELIGIBLE_UNSEEN
→ FUNDAMENTAL_SOURCE_SUFFICIENT
```

Price-Timing readiness is a separate axis.

Do not automatically label all discovered securities source-sufficient. Security types outside existing supported semantics remain excluded/quarantined; do not expand into a new investment framework to fill the cohort.

---

## 11. Precommit budgets and deterministic diagnostic selection

Before new network/source diagnostics, write a policy artifact containing:

```text
reference feeds and retrieval scope
raw snapshot cut-off
deterministic selection salt/rule
candidate ranking and representative-share-class rule
exclusion-registry hash
per-market attempt limits
pagination/request budgets
per-resource retry limit and backoff
provider unavailability stop policy
cache isolation and natural-live coexistence policy
```

Suggested bounded scope, to be finalized before outcomes are observed:

```text
US identity/capability candidate inspections: at most 40
US full fundamental-source diagnostics: at most 24 issuers
KR bounded source diagnostics: at most 24 issuers
per-resource attempts: no more than existing supported policy, capped at 3
```

Reference-directory pagination must have an explicit page/request cap. Do not let a directory import become thousands of per-issuer requests.

If the caps cannot answer the question, report exhaustion; do not silently extend them after seeing failures. Do not repeat the historical large 502-retry pattern.

Selection must be outcome-independent. Use a declared stable hash order or existing deterministic selector over the frozen reference snapshot. Select a representative eligible security per issuer before source-readiness outcomes. Record all attempted ranks and objective rejection reasons.

Diagnostic objectives:

```text
US minimum: 4 distinct supported unseen issuers with sufficient fundamental input
US reserve objective: 8 additional identity/capability-supported unseen issuers
KR minimum: 12 distinct supported unseen issuers with sufficient fundamental input
```

The reserve objective is a buffer, not permission to weaken eligibility. Report reserve candidates as untested where source sufficiency has not been checked.

Do not rank by desired BUY/HOLD/SELL, technical trend, valuation attractiveness, or expected model output. Stop optional diagnostic consumption at the predeclared objective/budget.

---

## 12. Source-readiness diagnostics without model calls

After identity/capability/exclusion gates, use the unchanged canonical source pipeline in an isolated diagnostic mode.

For every inspected issuer preserve:

```text
rank and representative security
canonical issuer identity
source request/outcome lineage
fundamental framework
required-family coverage
source validation errors
packet creation status and hash
fundamental_source_sufficiency
price_timing_input_readiness
security/accounting basis status
final diagnostic eligibility and reason
```

Market-level outcomes must distinguish:

```text
universe shortfall
identity/capability shortfall
fundamental-source shortfall
safe price absence
hard price/security validation failure
request budget exhausted
unknown
```

`SUPPORTED_UNSEEN` is not synonymous with `SOURCE_SUFFICIENT`. The prior KR universe count is not evidence that 2460 issuers passed source sufficiency.

Complete the bounded KR work even when US fails. Do not re-fetch the entire KR universe's fundamental history. A corrected registry plus bounded candidate/source checks is sufficient for this task.

Produce diagnostic packets and their hashes, not a final real-proof source lock or a committed real 16-issuer cohort.

---

## 13. Preserve the price/fundamental separation

The preceding price-context gate repair established that missing safe technical context need not invalidate fundamental Directional Core sufficiency.

Keep the canonical behavior:

```text
valid fundamentals + valid available price
→ evaluate both relevant readiness dimensions

valid fundamentals + safely unavailable price
→ preserve fundamental readiness
→ Price-Timing = UNAVAILABLE_SAFE under the existing contract

future / malformed / conflicting price or security basis
→ preserve the existing hard validation block
```

Do not silently convert hard-invalid price into safe absence.

Do not fabricate a quote/date from unsuitable bars. Do not fabricate RSI/MACD, support/resistance, target/stop, EPS/BVPS, ADR conversions, or unavailable financial data.

Bank/insurer sector mapping and all financial attribution/provenance requirements remain unchanged. Candidate coverage must improve by valid reference/support integration, not by loosening the financial contract.

---

## 14. Correct market manifests at their actual producer

Trace how `context_manifest.market_mix` is computed. Compare it to:

```text
explicit per-subject market in the canonical context
the actual serialized adapter prompt
the ordered-subject binding
```

Do not derive market by testing whether a synthetic ticker is numeric or starts with a particular label. Do not infer market from currency alone.

For each context:

```text
manifest market counts =
counts of verified explicit canonical subject markets

sum(market counts) = subject_count
manifest subjects = binding ordered_subjects
prompt subject identities/markets = canonical context identities/markets
```

Missing/contradictory market metadata must not silently default to US.

If only reporting is affected, implement the generic correction and tests. Preserve historical artifacts unchanged. New corrected simulation artifacts belong to a new diagnostic generation.

If current code proves routing or semantic model inputs are affected, record the impact and stop that repair scope. Continue safe read-only registry diagnosis where possible, but do not mark readiness for real proof.

---

## 15. Preserve the runtime identity lock

Retain the single identity-binding source and its source/runtime separation.

Historical contract:

```text
source_generation_id
source_lock_sha256
per_subject_packet_hashes
```

are evidence identity.

```text
runtime_generation_id
run_id
stage
batch_id
invocation_id
ordered_subjects
output_contract
```

are execution identity.

The model output packet_id remains runtime_generation_id under the current frozen contract.

Keep exact-path validation of:

```text
actual prompt passed to the adapter
actual schema file reopened by the adapter
validator expected identity
receipt identity
output identity
context manifest and binding lock
```

Do not repair counts or market metadata by weakening runtime ID checks or rewriting historical source IDs.

---

## 16. Model-free regression and rehearsal

Re-run the existing frozen identity/whole-path regression through the actual experiment request-construction path with a model-free adapter. No real model process may be spawned.

Cover:

```text
fresh and resumed runtime identities
FIRST / A / B / C
Directional Core and Price-Timing
all four batches
available and UNAVAILABLE_SAFE price paths
preservation and run-gate sequencing
```

Retain the 64-context coverage matrix if the canonical fixture is unchanged. Retain the 17 prior regression cases, including their positive control; do not imply all 17 are negative cases.

Add tests for:

```text
KR explicit market does not become US in manifests
US explicit market remains US
market metadata absent/contradictory does not default silently
non-numeric fictional identity with market=kr
one issuer represented by multiple share classes
provider aliases map to the same security/issuer correctly
issuer-level retirement blocks alternate eligible share classes
cross-market duplicate issuer handling where mapping is proven
ambiguous issuer identity quarantined
overlapping exclusion reasons are unioned, not double-subtracted
global versus within-universe exclusions reported separately
remaining issuer count cannot exceed starting issuer count
listed-but-unsupported security not promoted to supported
safe missing price distinct from invalid price
provider failure bounded and explicitly classified
```

No market=`synthetic`; fixture identity is fictional, routing enum remains `kr | us`.

Expected simulation manifest totals per fresh/resumed path:

```text
4 runs × 2 stages × (one US4 batch + three KR4 batches)

US4 context manifests = 8
KR4 context manifests = 24
total = 32
```

Across fresh plus resumed:

```text
US4 = 16
KR4 = 48
market_mix conflicts = 0
```

Reopen actual preserved prompt/schema/output/receipt/manifest files and validate hashes and identities. Do not count simulated outputs as real investment proof.

---

## 17. Tests, measurement, and evidence boundaries

Run focused tests, the repository's required full suite, lint, and diff checks. Do not merely copy PASS from the preceding result.

Include sanitized command identity, exit code, logs or machine-readable results, and tested commit. Do not execute optional model-backed tests under a misleading full-suite claim. If a required gate cannot run without violating the zero-model-call rule, report it and keep the relevant readiness blocked.

Counters must distinguish:

```text
reference-source requests
candidate/source-only evaluations
model-free simulated invocations
real investment model invocations
raw real subject outputs
identity-accepted real outputs
semantically audited real outputs
```

Required for this task:

```text
new_real_model_invocation_count = 0
new_real_subject_output_count = 0
model_backed_fictional_canary_count = 0

FIRST / A / B / C real runs = NOT_RUN
real ownership gates = NOT_MEASURED
real renderer gates = NOT_MEASURED
real hard-safety generalization = NOT_MEASURED
ownership_generalization_verdict = NOT_ESTABLISHED
```

An unexecuted violation counter initialized to zero is not a PASS.

---

## 18. Diagnostic completion and readiness rules

Report each workstream independently:

```text
US supported-universe expansion
US/KR issuer-count reconciliation
market-manifest correction
model-free identity regression
US diagnostic source readiness
KR diagnostic source readiness
production isolation/no-change
```

Minimum next-selection-review readiness requires:

```text
US >= 4 distinct supported unseen fundamental-source-sufficient issuers
KR >= 12 distinct supported unseen fundamental-source-sufficient issuers
issuer/security units reconciled
exclusion membership and alias handling verified
market manifest discrepancies corrected or safely blocked with no readiness
identity/full-path model-free regressions PASS
production no-change proven
```

The additional US reserve objective must be reported separately. A small reserve buffer is not a fabricated failure or success; label it as limited and carry it into the selection review.

Possible next states:

```text
READY_FOR_NEW_ISSUER_HOLDOUT_SELECTION_REVIEW
READY_FOR_NEW_ISSUER_HOLDOUT_SELECTION_REVIEW_WITH_LIMITED_RESERVES
NOT_READY_US_SUPPORTED_UNIVERSE_BLOCKED
NOT_READY_ISSUER_IDENTITY_OR_COUNT_RECONCILIATION_BLOCKED
NOT_READY_US_SOURCE_COVERAGE_BLOCKED
NOT_READY_KR_SOURCE_COVERAGE_BLOCKED
NOT_READY_REFERENCE_CAPABILITY_OR_ENTITLEMENT_BLOCKED
NOT_READY_MARKET_ROUTING_SCOPE_REVIEW
```

Use existing canonical equivalents and supply a mapping where necessary.

None authorizes real model execution in this task. Never emit Monitoring Bootstrap readiness from a universe-only task.

---

## 19. No automatic proof resume

Even if all diagnostics succeed:

```text
final_real_holdout_created = 0
final_proof_source_lock_created = 0
real_model_calls = 0
```

Provide:

```text
verified reference snapshot
corrected exclusion registry
deterministic candidate order
per-candidate source diagnostics
remaining reserve order/status
model-free regression artifacts
known limitations
```

The next separately authorized task will choose/freeze a new cohort and evidence snapshot. This separation avoids changing reference/support code and consuming a real holdout before its accounting and integration results have been reviewed.

---

## 20. Production and natural-live monitoring no-change

The user chose to leave existing US/KR monitoring and message formats unchanged until full integration review.

Preserve:

```text
main_merge = 0
production_db_mutation = 0
production_scheduler_change = 0
production_telegram_send = 0
monitoring_registration_calls = 0
live_structured_autonomy_activation = 0
live_v2_change = 0
night_futures_code_mutation = 0
night_futures_decision_packet_injection = 0
natural_live_cancel_count = 0
```

Reference/source diagnostics must respect existing natural-live resource protection. Do not disable the guard, assume no contention because observation failed, or write to shared production stores.

Use current policy-derived protected windows, not a hardcoded time window copied from a past run.

No live monitoring status should be inferred merely from zero changes in the result report.

---

## 21. Required result artifacts

Produce Markdown summaries plus machine-readable evidence, including:

```text
01-input-integrity-and-repository-provenance
02-historical-identity-repair-baseline
03-production-isolation-and-change-boundary
04-counting-units-and-canonical-identity-contract

05-us-universe-codepath-and-filter-funnel
06-us-reference-adapter-decision-and-capabilities
07-reference-snapshots-and-normalization-lineage
08-us-universe-before-after-membership

09-prior-exposure-and-retirement-registry
10-us-exclusion-set-reconciliation
11-kr-issuer-count-root-cause-and-reconciliation
12-cross-market-alias-and-dedup-proof

13-market-manifest-root-cause-and-impact
14-market-manifest-correction-and-tests

15-deterministic-diagnostic-policy-and-budgets
16-us-candidate-and-source-readiness-audit
17-kr-candidate-and-source-readiness-audit
18-dual-market-readiness-and-reserve-summary

19-model-free-fullpath-identity-and-market-matrix
20-negative-and-positive-regression-results
21-tests-lint-diff-and-implementation-freeze
22-production-no-change
23-next-holdout-selection-handoff
24-program-completion
```

Include actual membership rows needed to reproduce counts. A scalar issuer count without security-to-issuer lineage is insufficient.

Archive reference evidence and diagnostic packet provenance where permitted; redact secrets with hashes and explicit derivative labels. Preserve exact historical artifacts as historical, never relabel them as new.

---

## 22. Minimum completion fields

Use typed records and explicit NOT_MEASURED/NOT_RUN where appropriate.

```text
input_zip_sha256
base_sha
work_instruction_commit
implementation_commit
implementation_freeze_commit
final_head_sha
branch

identity_repair_regression_status
actual_request_identity_preflight_status

authorized_reference_universe_expansion
authorized_issuer_audit_correction
authorized_market_manifest_correction

us_reference_source
reference_snapshot_id
reference_snapshot_sha256
reference_as_of
reference_retrieved_at

us_raw_reference_rows_before / after
us_supported_security_count_before / after
us_supported_issuer_count_before / after
us_unseen_supported_issuer_count_before / after
us_fundamental_source_sufficient_count
us_identity_supported_reserve_count
us_reserve_source_status

kr_raw_reference_rows
kr_supported_security_count
kr_supported_issuer_count
kr_unseen_supported_issuer_count
kr_fundamental_source_sufficient_count
kr_prior_count_conflict_root_cause
kr_count_reconciliation_status

canonical_exclusion_issuer_count
actual_output_exclusion_issuer_count
whole_cohort_retirement_issuer_count
other_exclusion_issuer_count
exclusion_overlap_counts
within_universe_exclusion_intersections
ambiguous_identity_quarantine_count

diagnostic_policy_hash
source_request_count_by_market_and_provider
candidate_attempt_count_by_market
candidate_success_failure_memberships
budget_exhaustion
provider_unavailability_counts

market_manifest_conflicts_before
market_manifest_conflicts_after
actual_routing_impact
model_free_simulated_invocation_count
model_free_identity_failure_count

new_real_model_invocation_count
new_real_subject_output_count
model_backed_fictional_canary_count
final_real_holdout_created
final_proof_source_lock_created

investment_architecture_semantic_drift
decision_prompt_semantic_drift
investment_schema_semantic_drift
source_sufficiency_policy_drift
canonical_transport_mutation
guard_semantics_mutation
historical_artifact_mutation

repair_readiness
us_universe_readiness
kr_identity_audit_readiness
dual_market_diagnostic_source_readiness
reserve_buffer_status
ownership_generalization_verdict

production_no_change
main_merge
production_db_mutation
production_scheduler_change
production_telegram_send
monitoring_registration_calls
live_structured_autonomy_activation
live_v2_change
night_futures_code_mutation
natural_live_cancel_count

artifact_count
indexed_artifact_count
index_self_exclusion
hash_mismatch_count
size_mismatch_count
unexpected_unindexed_files
secret_scan_status

readiness
stop_reason
next_scope
```

Per-market supported counts must carry unit/snapshot definitions and membership evidence. Do not silently mix security counts and issuer counts.

---

## 23. Stop matrix

### Immediate safety/integrity stop

```text
input ZIP mismatch
unexplained experiment-semantic drift
no safe isolation from live production
secret exposure that cannot be safely contained
real model invocation becomes necessary
unsupported credential/entitlement acquisition required
```

### Complete the other market's safe diagnostics, but block selection readiness

```text
US universe below target
KR count reconciliation incomplete
market-specific source insufficiency
bounded candidate/request pool exhausted
```

### No unauthorized semantic repair

If a purported reference/reporting fix requires changing investment rules, source-sufficiency policy, runtime identity, real market routing semantics, transport, or guard:

```text
record exact dependency
stop that implementation scope
retain safe forensic results
recommend a separately bounded task
```

Do not use task complexity as a reason to omit already-safe US/KR diagnostics.

---

## 24. Artifact finalization — no unindexed mutable completion files

Improve on the latest bundle's five intentional omissions.

Finalize README, reports, completion JSON, test evidence, and membership manifests before building the index.

Then:

```text
enumerate final bundle payload
hash every payload file
write one machine-readable artifact index
self-exclude only the index itself
build the ZIP
reopen ZIP and independently verify member set, sizes, hashes and CRC
write external ZIP.sha256
do not mutate completion/README after indexing
```

If an index Markdown rendering is desired, generate it before the final JSON index so it can be included. Avoid self-referential hash claims.

Report explicitly:

```text
all payload files except index itself individually indexed
unexpected_unindexed_files = []
hash_mismatch_count = 0
size_mismatch_count = 0
```

The external ZIP digest covers the index too. Do not put a purported final ZIP checksum inside the very ZIP whose bytes it would change.

---

## 25. Future proof contract retained, not executed

The next new-holdout task must retain:

```text
new unseen issuer-level US4 + KR12 cohort
all current and historical retirement exclusions
new source generation and source lock
separate runtime binding lock
implementation freeze before runtime precommit before actual model spawn
actual-path prompt/schema/validator/receipt identity preflight

model = gpt-5.6-sol
reasoning_effort = xhigh
MODEL_CONTEXT_COUPLED
four subjects per shared context
timeout = 1800
timeout owner count = 1

per-context exact output/receipt/prompt/schema preservation
per-context applicable semantic early stop
FIRST gates before A
A gates before B
B gates before C
no model retry / batch split / selective continuation
separate output exposure, semantic revelation, and retirement state
```

Safe unavailable price is not a license for technical claims. Renderer and Price-Timing real-output proof remain unmeasured until actually executed.

A fully or partly exposed cohort may not be recycled as fresh unseen evidence. Future tuning after a real semantic defect requires a separately authorized generic repair and new unseen issuer cohort.

---

## 26. Final task principle

The latest task repaired runtime identity without consuming another real holdout. Preserve that improvement.

The present blocker is the **narrow supported US reference universe**, with two demonstrated audit inconsistencies that should be corrected before the next proof.

The correct sequence is:

```text
prove the reference boundary
→ expand supported discovery generically
→ reconcile issuer identities and exclusion sets for both markets
→ correct market manifests
→ verify source readiness with zero model calls
→ freeze and review the results
→ authorize a genuinely new holdout separately
```

Not:

```text
append a few convenient tickers
reuse a retired share class / KR cohort
call security rows unique issuers
declare simulated outputs real proof
automatically spend another real holdout after a data-plane change
```

Expand real capability, not just a list. Count issuers correctly. Preserve production unchanged.
