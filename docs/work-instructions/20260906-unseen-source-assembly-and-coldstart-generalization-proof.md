# thesis-monitor — Unseen Source Assembly + Cold-Start Generalization Proof
## Fix the test harness, not the decision engine
## Build fresh immutable packets for arbitrary supported tickers using read-only production-grade sources
## Remove `data/ai_review` archive presence as an eligibility prerequisite
## Use the previous 11 failed-preflight names only as source-assembly fixtures
## Select a NEW final unseen holdout after source-assembly freeze
## Run unseen FIRST → A → B → C with zero same-generation repair
## Keep production/live V2 and night futures unchanged

---

# 0. Immutable source result

Source report bundle:

```text
thesis-monitor-20260906-structured-actionability-unseen-coldstart-report.zip
```

SHA-256:

```text
c4201d6b960ef68f49e51fd8caa2b6c59bbca2747743348ffa982d5da0b61a22
```

Program generation:

```text
20260906-structured-actionability-20260906T031722Z-e7085b421624
```

Architecture implementation commit:

```text
f49ce6c3aa9b7241571fdd08e7094fd08bdf2251
```

Architecture implementation tree:

```text
a2f9dfacdc4dc7c6c551b2b65b35a979bd38cace
```

Model / effort:

```text
gpt-5.6-sol / xhigh
```

Observed result:

```text
Structured Actionability = PASS
Primary action owner = STRUCTURED_FIELDS
Primary user action wording owner = RENDERER

Actionable true positive = 20/20
Safe action mention false positive = 0
Structured contradiction detection = 10/10
Known hard-safety regression = 0

USKR22 = RETIRED_FROM_TUNING
USKR22 one-shot regression = 22/22
USKR22 post-result tuning = 0

Unseen candidate pool = 11
Unseen selected = 11
Unseen eligible = 0
Unseen FIRST/A/B/C = NOT_RUN

Reported generalization verdict =
GENERALIZATION_BLOCKED_BY_SOURCE_COVERAGE
```

The preflight evidence shows a narrower root cause:

```text
all 11 selected subjects had:
packet_count = 0
base_message_count = 0

eligibility was tied to:
/data/ai_review
stored immutable packet
+
paired deterministic base message
```

Therefore this task treats the blocker as:

```text
COLD_START_SOURCE_ASSEMBLY_HARNESS_GAP
```

until a real provider/source failure is independently demonstrated.

Do not relabel archive absence as provider incapability.

---

# 1. Primary task decision

The decision engine is NOT the repair target.

This task must preserve the already-proven Structured Actionability architecture.

Repair only the ability to create fresh, immutable, production-equivalent research packets for previously unseen supported tickers without:
- monitoring registration
- production DB mutation
- pre-existing `data/ai_review` files
- AI investment judgment

Target flow:

```text
supported security universe
        ↓
objective unseen selection candidates
        ↓
read-only source acquisition
        ↓
deterministic normalization / validation
        ↓
immutable source packet
        ↓
deterministic base message / base context
        ↓
source lock
        ↓
Structured Autonomy FIRST / A / B / C
```

---

# 2. Hard freeze — decision architecture

The following decision-layer hashes are immutable throughout this task.

```text
builder_prompt =
2a4e6b4775db5e3f4d1b56b3f804613994e2602e4aaefd7902a9c1640cacb672

directional_balance =
2ecf5bbad338dc92d9996b60e3429ebb3c6b8d37cdb114439ffbff84166296ab

logical_condition =
255837edf51ff7fe06f26ed4d4782479131d2485e5e19349aa2a3f095ca1d234

stability =
e824e9dc7044033c091f8b40fdb0f461f629d8b420f193e060b42e7f27e13188

validator_renderer =
ee8dcdeaf42c40a49a8c56ebc140298271857eacd0bd2afc1cddb9fb631c018f

prompt_set =
95a46a8d3ac708aa981203270236eec7b21bdf196be7577245cc1e52fea50c89

schema_set =
e86b747a0c6f459650275598a7c3c217bb0116ef6b6f8927debf3dfa938fd668
```

Required:

```text
DECISION_ENGINE_HASH_DRIFT = 0
INVESTMENT_DECISION_THRESHOLD_MUTATION = 0
ACTIONABILITY_CONTRACT_MUTATION = 0
ACTION_RENDERER_SEMANTIC_MUTATION = 0
```

Source-assembly code may change before its own freeze.
Decision code may not.

---

# 3. Source assembly may change; decision semantics may not

Allowed implementation work:

```text
arbitrary-ticker identity resolution
read-only source orchestration
packet normalization
fresh packet persistence to experiment artifacts
deterministic base-context generation
source freshness / completeness classification
objective candidate-universe expansion
```

Forbidden:

```text
BUY/HOLD/SELL changes
WAIT/AVOID/ATTRACTIVE changes
holder stance changes
validator relaxation
new ticker-specific prompt rules
phrase allowlists
valuation threshold tuning
```

---

# 4. Remove archive-presence circularity

Previous eligibility required a packet already present in:

```text
data/ai_review
```

That is inappropriate for a true cold-start subject.

New policy:

```text
PREEXISTING_AI_REVIEW_PACKET_REQUIRED = 0
PREEXISTING_BASE_MESSAGE_REQUIRED = 0
```

`data/ai_review` may be:
- a historical archive
- a regression fixture store
- an output destination

but not a prerequisite for an unseen ticker to enter source assembly.

---

# 5. Discover and reuse the existing production-grade source path

Before implementing a new collector, inventory the repository.

Find the canonical existing read-only paths that currently build the 22-subject packet from approved sources.

Prefer reuse of existing components for:
- company/security identity
- earnings
- events / filings
- price / valuation
- positioning when supported
- market context
- deterministic price structure already used by the current system

Do not create a parallel web-scraping research stack.

Required report:

```text
SOURCE_ASSEMBLY_REUSE_MAP
```

showing:
- existing component
- input
- output
- whether reused unchanged
- whether a generic adapter was required

---

# 6. No new unapproved provider dependency

This task must not add:
- paid provider dependency
- browser scraping
- website-specific HTML parser
- ticker-specific manual data file

Use approved existing providers and repository source paths only.

Required:

```text
NEW_PAID_PROVIDER = 0
NEW_WEBSITE_SCRAPER = 0
TICKER_SPECIFIC_SOURCE_OVERRIDE = 0
```

If existing approved sources cannot support enough unseen names, report objective source coverage honestly.

---

# 7. Arbitrary-ticker read-only assembler

Create or expose a reusable source-assembly entry point conceptually equivalent to:

```text
assemble_research_packet(ticker, as_of, mode=read_only)
```

The exact API follows repository conventions.

It must:
1. normalize ticker/security identity
2. resolve supported market/security
3. fetch only approved read-only sources
4. apply the same numeric/accounting/security-basis validation used in production
5. preserve Unknown / unavailable / stale states
6. produce the same source-contract family expected by the Structured Autonomy engine
7. create no monitoring registration
8. create no production assessment
9. send no message

---

# 8. No fabricated baseline

If the Structured Autonomy packet contract implicitly requires a stored monitoring thesis/version, do NOT synthesize one silently.

Add gate:

```text
MONITORING_BASELINE_REQUIRED_FOR_SOURCE_PACKET =
0 / 1
```

If `1`, stop before unseen judgment and report:

```text
COLD_START_ARCHITECTURE_DEPENDENCY =
MONITORING_BASELINE_REQUIRED
```

Do not call monitoring-registration APIs or mutate the production DB.

If an existing read-only unregistered analysis context is supported, use it.

---

# 9. Deterministic base context/message

The previous harness also required a paired deterministic base message.

Implement fresh deterministic base-context generation from the assembled packet using the existing production-equivalent deterministic builder.

It must not call the investment-judgment model.

Allowed:

```text
facts
validated numeric values
known data-quality notices
existing deterministic price/valuation context
neutral section scaffolding
```

Forbidden:

```text
new BUY/HOLD/SELL judgment
new market-expectation judgment
new thesis strengthening/weakening judgment
invented narrative
```

Required:

```text
BASE_CONTEXT_AI_JUDGMENT_CALLS = 0
```

---

# 10. Packet immutability and provenance

Every assembled packet must include or be accompanied by:

```text
ticker/security id
company identity
market
security basis
assessment/session date
source timestamps
provider/source lineage
packet schema version
normalization version
validation result
packet SHA-256
deterministic base-context SHA-256
```

After final cohort source lock:

```text
SOURCE_PACKET_MUTATION = 0
```

through FIRST/A/B/C.

---

# 11. Freshness semantics

Use latest completed market sessions according to the repository's established market/session rules.

Do not label weekend/holiday data as live.

Record:
- assessment date
- price as-of
- source as-of
- stale/partial components that materially affect interpretation

Do not refresh sources between FIRST/A/B/C.

Required:

```text
FIRST_ABC_SOURCE_DRIFT = 0
```

---

# 12. Source-assembly validation fixtures — previous 11 names

The 11 names from the failed preflight may be used ONLY to validate source assembly.

Fixture set:

```text
010140
011200
017800
021240
024110
035420
051160
055550
443060
MSFT
NVDA
```

Purpose:

```text
prove that fresh packet creation does not require a prior archive
exercise KR + US identity/source paths
find generic identity/source orchestration bugs
```

Do NOT run Structured Autonomy judgment on these 11 in this task.

They are no longer eligible for the final unseen scoring cohort.

---

# 13. Fixture-stage repair policy

During source-assembly fixture work, generic source-assembly defects may be repaired.

Examples:

```text
security-master lookup bug
supported-market identity normalization bug
fresh packet output path bug
deterministic base-context builder requiring archive path
```

Forbidden:

```text
if ticker == NVDA
if ticker == MSFT
manual company-name map solely for one fixture
manual packet injection
manual expected data values
```

Any identity mapping must be source-owned / canonical and general.

---

# 14. Fixture success is not generalization proof

The previous 11 are engineering fixtures.

Report per fixture:

```text
ASSEMBLED
OBJECTIVE_SOURCE_LIMIT
IDENTITY_UNRESOLVED
UNSUPPORTED_SECURITY
VALIDATION_BLOCK
```

Do not require all 11 to succeed by lowering standards.

Do not interpret fixture success as unseen investment-judgment proof.

---

# 15. Freeze source-assembly implementation before final unseen selection

After:
- generic source assembler tests pass
- fixture audit completes
- hard source validation passes

freeze:

```text
source-assembly code hash
provider config hash
identity-resolution policy hash
packet schema/normalization hash
deterministic base-context builder hash
unseen selection algorithm hash
market/sector stratification policy hash
```

Then no source-assembly code/config change until the unseen experiment terminates.

Required:

```text
SOURCE_ASSEMBLY_MUTATION_AFTER_FREEZE = 0
```

---

# 16. Final unseen cohort must be NEW

Exclude both:

## Retired USKR22

```text
CORZ, CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF, 000660, 003690, 005490, 005930, 010120, 012450, 047810, 086280
```

## Previous 11 preflight/source-assembly fixtures

```text
010140, 011200, 017800, 021240, 024110, 035420, 051160, 055550, 443060, MSFT, NVDA
```

Required:

```text
FINAL_UNSEEN_OVERLAP_RETIRED22 = 0
FINAL_UNSEEN_OVERLAP_PREFLIGHT11 = 0
```

This prevents the source-fixture set from becoming the judgment holdout.

---

# 17. Expand the candidate universe objectively

Previous candidate sources were limited to:

```text
watchlistitem
securitymaster
```

and produced only 11 candidates.

Build the final candidate pool from the canonical supported-security universe already available to the repository.

Do not require:
- watchlist membership
- monitoring status
- prior AI-review archive presence

Candidate selection may use only objective metadata such as:
- supported market
- supported security type
- canonical identity quality
- duplicate issuer
- sector/framework taxonomy where already available

Do not use:
- expected return
- known investment label
- prior AI judgment
- hand-picked company quality

---

# 18. Final unseen selection policy

Target:

```text
16 subjects
```

Preferred market balance when source support permits:

```text
KR 8
US 8
```

Allowed total:

```text
12–20
```

Minimum executable:

```text
12
```

If market balance cannot be achieved without lowering source quality:
- preserve quality
- report the imbalance
- do not force a quota

---

# 19. Diversity without cherry-picking

Use predeclared framework/sector strata where metadata exists.

Aim to cover multiple distinct frameworks such as:
- financial/bank
- insurance
- consumer
- industrial
- construction/EPC
- software/cloud
- semiconductor/hardware
- healthcare/biotech
- cyclical/asset-heavy
- transport
- foreign/ADR where safely supported
- pre-profit growth where safely supported

Do not force unsupported categories.

Within each stratum use deterministic ordering, e.g. stable hash / canonical ticker order, defined before subject names are revealed in the final selection report.

---

# 20. Oversampling and replacements

To avoid manual cherry-picking, predeclare a ranked candidate list larger than the target.

Recommended:

```text
ranked candidate pool >= 32
target eligible = 16
```

Run read-only source assembly in frozen ranking order.

If a candidate fails an objective preflight gate, move to the next ranked candidate.

Every exclusion remains in the audit.

No manual replacement after seeing AI judgments.

---

# 21. Objective final preflight

A final unseen subject is eligible only if:

```text
identity resolved
supported market/security
fresh immutable source packet assembled
hard numeric/accounting/security validation passed
deterministic base context generated
no retired/preflight overlap
```

Do NOT require a prior monitoring thesis unless the architecture truly requires it.

If it truly does, stop under Section 8.

---

# 22. No AI investment judgment during cohort assembly

Before final source lock:

```text
STRUCTURED_AUTONOMY_MODEL_CALLS = 0
AI_REVIEWER_INVESTMENT_JUDGMENT_CALLS = 0
```

Source assembly and cohort eligibility must not see:
- BUY/HOLD/SELL
- new-buyer stance
- holder stance
- prior reviewer labels

---

# 23. Final immutable source lock

Once at least 12 eligible subjects exist:

freeze:
- ordered eligible cohort
- all packet SHAs
- all base-context SHAs
- market/session dates
- source/provider lineage
- macro snapshot if used

Create:

```text
UNSEEN_SOURCE_LOCK_SHA256
```

FIRST/A/B/C must use exactly this lock.

---

# 24. Decision engine re-verification before unseen FIRST

Immediately before FIRST, verify the decision architecture is unchanged from the previous proven architecture.

Required exact hashes:

```text
builder_prompt = 2a4e6b4775db5e3f4d1b56b3f804613994e2602e4aaefd7902a9c1640cacb672
directional_balance = 2ecf5bbad338dc92d9996b60e3429ebb3c6b8d37cdb114439ffbff84166296ab
logical_condition = 255837edf51ff7fe06f26ed4d4782479131d2485e5e19349aa2a3f095ca1d234
stability = e824e9dc7044033c091f8b40fdb0f461f629d8b420f193e060b42e7f27e13188
validator_renderer = ee8dcdeaf42c40a49a8c56ebc140298271857eacd0bd2afc1cddb9fb631c018f
prompt_set = 95a46a8d3ac708aa981203270236eec7b21bdf196be7577245cc1e52fea50c89
schema_set = e86b747a0c6f459650275598a7c3c217bb0116ef6b6f8927debf3dfa938fd668
```

If any mismatch:

```text
STOP
```

---

# 25. Unseen FIRST

Run one fresh unseen FIRST with:

```text
gpt-5.6-sol / xhigh
```

or the exact same current production-equivalent model/effort only if the operating configuration has legitimately changed before task start and the change is documented before source selection.

No candidate reuse.
No selective rerun.
No same-generation repair.

Classify every subject:

```text
VALIDATED
SOURCE_COVERAGE_LIMIT
ONTOLOGY_GAP
MODEL_SEMANTIC_MISUSE
VALIDATOR_FALSE_POSITIVE
HARD_SAFETY_TRUE_REJECT
ACCOUNTING_OR_SECURITY_BASIS_BLOCK
SCHEMA_FAILURE
```

---

# 26. FIRST gate for A/B/C

Proceed to A/B/C only if:

```text
UNSEEN_FIRST_VALIDATOR_FALSE_POSITIVE = 0
UNSEEN_FIRST_SCHEMA_FAILURE = 0
KNOWN_HARD_SAFETY_REGRESSION = 0
```

A true hard-safety reject does not automatically imply validator failure.
Report it separately.

If a subject fails because the frozen source packet itself is insufficient:
- classify it
- do not mutate the packet
- do not replace it after model output

---

# 27. Unseen A/B/C

If FIRST gate permits:

```text
A
B
C
```

Use exactly:
- same eligible subjects
- same source lock
- same decision hashes
- same model
- same effort
- same schema
- same renderer
- same validator

No run may read another run's output.

No majority-vote decision.

---

# 28. Stability analysis

Only after completed unseen FIRST/A/B/C.

Classify per subject:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

Measure:
- overall BUY/HOLD/SELL
- BUY:SELL balance
- new-buyer stance
- entry mode
- holder stance

Do not define 5.5↔6.0 movement as automatically unstable.

---

# 29. Generalization verdict

Use evidence-based verdicts:

```text
GENERALIZATION_STRONG
GENERALIZATION_ACCEPTABLE_WITH_BOUNDARY_UNCERTAINTY
GENERALIZATION_NEEDS_ARCHITECTURE_WORK
GENERALIZATION_BLOCKED_BY_REAL_SOURCE_COVERAGE
```

Important:

`GENERALIZATION_BLOCKED_BY_REAL_SOURCE_COVERAGE` is allowed only if the fresh read-only assembler actually attempted approved sources and could not produce sufficient eligible packets.

Archive absence alone is NOT sufficient.

---

# 30. Same-generation repair remains forbidden

After final unseen selection/source lock/model output:

```text
DECISION_CODE_CHANGE = 0
SOURCE_ASSEMBLY_CODE_CHANGE = 0
PROMPT_CHANGE = 0
VALIDATOR_CHANGE = 0
RENDERER_CHANGE = 0
ONTOLOGY_CHANGE = 0
PACKET_EDIT = 0
SELECTIVE_RERUN = 0
```

Any future repair requires:
- a separately authorized task
- a new source freeze
- a new unseen holdout cohort

---

# 31. Source-assembly quality audit

Separately report whether unseen source packets have materially lower information quality than the retired 22.

Compare generic availability of:
- latest earnings context
- valuation
- price context
- cash-flow/capital-efficiency facts where supported
- identity/security basis
- event/filing evidence

Do not require identical fields across industries.

Industry-irrelevant missing metrics are not defects.

---

# 32. Initial-analysis / monitoring lifecycle check

Because these are unseen/unregistered securities, explicitly report whether the packet/decision path depends on:
- a stored monitoring thesis
- thesis version
- stored price rules
- prior daily assessment

Required fields:

```text
STORED_MONITORING_STATE_REQUIRED =
0 / 1

UNREGISTERED_TICKER_SUPPORTED =
0 / 1
```

If the engine can operate with no prior state, prove it.

If not, do not hide the limitation.
Do not auto-register subjects.

---

# 33. Renderer shadow proof on final unseen cohort

If FIRST validates eligible subjects, render at least:
- one BUY if present
- one HOLD if present
- one SELL if present
- one WAIT/AVOID/REVIEW example if present

Do not force missing labels.

Verify:

```text
PRIMARY_USER_ACTION_WORDING_OWNER = RENDERER
AI_IMPERATIVE_PRIMARY_ACTION = 0
```

---

# 34. Hard-safety regression

Re-run:
- actionable-command synthetic suite
- structured/prose contradiction suite
- numeric provenance
- accounting attribution
- ADR/security basis
- evidence fencing
- severity ownership
- future-checkpoint ownership
- logical condition ownership
- lifecycle/exactly-once relevant unit tests

Required:

```text
KNOWN_HARD_SAFETY_REGRESSION = 0
```

---

# 35. Night futures remains unchanged

Current handoff:

```text
READY_FOR_BOUNDED_PRODUCTION_INTEGRATION
```

This task does not alter night-futures code.

Required:

```text
NIGHT_FUTURES_CODE_MUTATION = 0
NIGHT_FUTURES_STRUCTURED_AUTONOMY_INJECTION = 0
```

Night futures remains market/timing context only.

---

# 36. Live V2 remains inactive

Do not activate Structured Autonomy in production scheduled KR/US delivery.

Required:

```text
LIVE_STRUCTURED_AUTONOMY_ACTIVATION = 0
PRODUCTION_TELEGRAM_SEND = 0
PRODUCTION_SCHEDULER_CHANGE = 0
PRODUCTION_DB_MUTATION = 0
MAIN_MERGE = 0
```

Current legacy live messages may continue during this task.

---

# 37. Maximum readiness

If:
- fresh arbitrary-ticker assembler works
- at least 12 final unseen are eligible
- unseen FIRST/A/B/C complete under one frozen source lock
- no validator false-positive family appears
- hard-safety regression = 0
- stability is acceptable

maximum verdict:

```text
READY_FOR_PRODUCTION_INTEGRATION_REVIEW
```

Still no deployment.

---

# 38. Next production integration handoff

If ready, prepare a later bounded task that proves:

```text
authoritative scheduled KR job
+
authoritative scheduled US job
```

actually use:

```text
promoted Structured Autonomy decision source
+
V2 action renderer
```

Natural proof must distinguish:
- live scheduled path
- shadow/CLI path
- compatibility path
- fallback path

A V2 CLI render alone is not activation proof.

---

# 39. Required reports

Create:

1. `docs/reports/20260906-source-assembly-root-cause.md`
2. `docs/reports/20260906-source-assembly-reuse-map.md`
3. `docs/reports/20260906-arbitrary-ticker-source-packet-contract.md`
4. `docs/reports/20260906-deterministic-base-context-contract.md`
5. `docs/reports/20260906-preflight11-source-assembly-fixtures.md`
6. `docs/reports/20260906-source-assembly-freeze.md`
7. `docs/reports/20260906-final-unseen-selection-policy.md`
8. `docs/reports/20260906-final-unseen-cohort-selection.md`
9. `docs/reports/20260906-final-unseen-source-preflight.md`
10. `docs/reports/20260906-final-unseen-source-lock.md`
11. `docs/reports/20260906-decision-engine-freeze-verification.md`
12. `docs/reports/20260906-unseen-first.md`
13. `docs/reports/20260906-unseen-run-a.md`
14. `docs/reports/20260906-unseen-run-b.md`
15. `docs/reports/20260906-unseen-run-c.md`
16. `docs/reports/20260906-unseen-stability.md`
17. `docs/reports/20260906-unseen-source-quality-audit.md`
18. `docs/reports/20260906-unregistered-lifecycle-audit.md`
19. `docs/reports/20260906-unseen-renderer-shadow-proof.md`
20. `docs/reports/20260906-hard-safety-regression.md`
21. `docs/reports/20260906-generalization-verdict.md`
22. `docs/reports/20260906-production-integration-next-handoff.md`
23. `docs/reports/20260906-night-futures-no-change.md`
24. `docs/reports/20260906-program-completion.md`
25. `docs/reports/20260906-artifact-index.md`

Use actual completion date if execution crosses dates.

---

# 40. Machine-readable proofs

Create:

```text
source-assembly-reuse-map.json
arbitrary-ticker-source-packet-contract.json
deterministic-base-context-contract.json
preflight11-source-assembly-fixtures.json
source-assembly-freeze.json
final-unseen-selection-policy.json
final-unseen-cohort-selection.json
final-unseen-source-preflight.json
final-unseen-source-lock.json
decision-engine-freeze-verification.json
unseen-first.json
unseen-run-a.json
unseen-run-b.json
unseen-run-c.json
unseen-stability.json
unseen-source-quality-audit.json
unregistered-lifecycle-audit.json
unseen-renderer-shadow-proof.json
hard-safety-regression.json
generalization-verdict.json
production-integration-next-handoff.json
night-futures-no-change.json
program-completion.json
```

---

# 41. Required gates

```text
SOURCE_REPORT_BUNDLE_SHA256 =
c4201d6b960ef68f49e51fd8caa2b6c59bbca2747743348ffa982d5da0b61a22

ROOT_CAUSE_CLASS =
COLD_START_SOURCE_ASSEMBLY_HARNESS_GAP /
REAL_SOURCE_COVERAGE_LIMIT /
OTHER

DECISION_ENGINE_HASH_DRIFT =
0 / NONZERO

PREEXISTING_AI_REVIEW_PACKET_REQUIRED =
0 / NONZERO

PREEXISTING_BASE_MESSAGE_REQUIRED =
0 / NONZERO

NEW_PAID_PROVIDER =
0 / NONZERO

NEW_WEBSITE_SCRAPER =
0 / NONZERO

TICKER_SPECIFIC_SOURCE_OVERRIDE =
0 / NONZERO

MONITORING_BASELINE_REQUIRED_FOR_SOURCE_PACKET =
0 / 1

STORED_MONITORING_STATE_REQUIRED =
0 / 1

UNREGISTERED_TICKER_SUPPORTED =
0 / 1

BASE_CONTEXT_AI_JUDGMENT_CALLS =
0 / NONZERO

PREFLIGHT11_JUDGMENT_MODEL_CALLS =
0 / NONZERO

SOURCE_ASSEMBLY_FIXTURE_SUCCESS_COUNT =
...

SOURCE_ASSEMBLY_FIXTURE_OBJECTIVE_FAILURE_COUNT =
...

SOURCE_ASSEMBLY_MUTATION_AFTER_FREEZE =
0 / NONZERO

FINAL_UNSEEN_OVERLAP_RETIRED22 =
0 / NONZERO

FINAL_UNSEEN_OVERLAP_PREFLIGHT11 =
0 / NONZERO

FINAL_CANDIDATE_POOL_COUNT =
...

FINAL_UNSEEN_SELECTED_COUNT =
...

FINAL_UNSEEN_ELIGIBLE_COUNT =
...

FINAL_KR_COUNT =
...

FINAL_US_COUNT =
...

UNSEEN_SOURCE_LOCK_SHA256 =
...

FIRST_ABC_SOURCE_DRIFT =
0 / NONZERO

STRUCTURED_AUTONOMY_MODEL_CALLS_BEFORE_SOURCE_LOCK =
0 / NONZERO

UNSEEN_FIRST_VALIDATED =
...

UNSEEN_FIRST_VALIDATOR_FALSE_POSITIVE =
0 / NONZERO

UNSEEN_FIRST_HARD_SAFETY_TRUE_REJECT =
...

UNSEEN_FIRST_ONTOLOGY_GAP =
...

UNSEEN_FIRST_SCHEMA_FAILURE =
0 / NONZERO

UNSEEN_RUN_A_VALIDATED =
... / NOT_RUN

UNSEEN_RUN_B_VALIDATED =
... / NOT_RUN

UNSEEN_RUN_C_VALIDATED =
... / NOT_RUN

UNSEEN_STABLE_COUNT =
... / NOT_MEASURED

UNSEEN_BOUNDARY_UNCERTAINTY_COUNT =
... / NOT_MEASURED

UNSEEN_UNSTABLE_COUNT =
... / NOT_MEASURED

KNOWN_HARD_SAFETY_REGRESSION =
0 / NONZERO

PRIMARY_USER_ACTION_WORDING_OWNER =
RENDERER / OTHER

AI_IMPERATIVE_PRIMARY_ACTION =
0 / NONZERO

GENERALIZATION_VERDICT =
GENERALIZATION_STRONG /
GENERALIZATION_ACCEPTABLE_WITH_BOUNDARY_UNCERTAINTY /
GENERALIZATION_NEEDS_ARCHITECTURE_WORK /
GENERALIZATION_BLOCKED_BY_REAL_SOURCE_COVERAGE

NIGHT_FUTURES_CODE_MUTATION =
0 / NONZERO

LIVE_STRUCTURED_AUTONOMY_ACTIVATION =
0 / NONZERO

PRODUCTION_TELEGRAM_SEND =
0 / NONZERO

PRODUCTION_SCHEDULER_CHANGE =
0 / NONZERO

PRODUCTION_DB_MUTATION =
0 / NONZERO

MAIN_MERGE =
0 / NONZERO

FULL_TESTS =
PASS / FAIL

READINESS =
READY_FOR_PRODUCTION_INTEGRATION_REVIEW /
NEEDS_ARCHITECTURE_WORK /
BLOCKED_BY_REAL_SOURCE_COVERAGE /
NOT_READY
```

---

# 42. Stop conditions

STOP if:
- decision-engine hashes drift
- archive presence remains an unseen eligibility prerequisite
- source assembler silently auto-registers a ticker
- production DB is mutated
- a stored thesis is fabricated
- a new paid provider or scraper is introduced
- any of the previous 11 fixtures becomes part of the final scoring holdout
- any retired USKR22 subject becomes part of the final holdout
- final candidate selection is hand-picked after source results
- source packets change after final source lock
- AI investment judgment is called before final source lock
- a final unseen result is repaired in the same generation
- hard-safety regression appears
- live V2 or night futures production is activated

---

# 43. Completion response

Return:

```text
SOURCE ASSEMBLY ROOT CAUSE =
...

DECISION ENGINE =
frozen / hash drift

ARCHIVE INDEPENDENCE =
...

PREVIOUS 11 FIXTURES =
assembled ...
objective failures ...

UNREGISTERED LIFECYCLE =
stored monitoring state required? ...
unregistered ticker supported? ...

SOURCE ASSEMBLY FREEZE =
...

FINAL UNSEEN COHORT =
candidate pool ...
selected ...
eligible ...
KR/US ...

SOURCE LOCK =
...

UNSEEN FIRST =
...

UNSEEN A/B/C =
...

STABILITY =
...

GENERALIZATION =
...

HARD SAFETY =
...

RENDERER SHADOW =
...

LIVE V2 =
not activated

NIGHT FUTURES =
unchanged

PRODUCTION MUTATION =
0

READINESS =
...

NEXT PRODUCTION INTEGRATION HANDOFF =
...

REPORT ZIP =
...

ZIP SHA256 =
...
```

---

# 44. Final principle

The previous experiment did not show that unseen companies were unsupported.

It showed that the cold-start harness required those companies to have been processed already.

Fix that circular dependency.

Then prove the investment system on genuinely new subjects while keeping the entire decision architecture frozen.
