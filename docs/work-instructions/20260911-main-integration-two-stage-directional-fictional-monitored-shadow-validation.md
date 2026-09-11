# Thesis Monitor — Latest Main Integration + Two-Stage Directional + Fictional & Monitored Shadow Validation

## 0. Task identity

Suggested work-instruction filename:

```text
20260911-main-integration-two-stage-directional-fictional-monitored-shadow-validation.md
```

Suggested result bundle:

```text
thesis-monitor-20260911-main-integration-two-stage-directional-fictional-monitored-shadow-validation-report.zip
```

Master-workflow phase:

```text
M12AE-R2 — Integrated-Main Validation
            A. Freeze latest main and current M12AD source head
            B. Create isolated integration branch
            C. Merge current Thesis Monitor work onto latest main
            D. Establish a clean post-merge integration baseline
            E. Implement Directional Core → Stance two-stage architecture
            F. Full 8 × 3 fictional two-stage Sol canary
            G. Existing monitored-stock same-packet shadow compatibility
            H. Fresh unseen real-proof readiness decision
```

This instruction **supersedes** both earlier M12AE instructions:

```text
20260911-directional-core-stance-decoupling-architecture-and-full-two-stage-sol-canary.md

20260911-directional-core-stance-decoupling-fictional-and-monitored-shadow-compatibility.md
```

Do not run any superseded M12AE instruction.

The user has explicitly authorized moving from feature-branch-only validation
to an integrated-main validation phase.

The user has NOT authorized a final merge back into `main`.

The required direction is:

```text
latest main
+
current completed Thesis Monitor work
→ isolated integration branch
→ full validation
```

NOT:

```text
integration branch
→ main
```

---

# 1. Authoritative latest completed result

Authoritative latest completed proof bundle:

```text
thesis-monitor-20260911-financial-framework-negation-scope-holder-stance-decision-material-stability-full-sol-canary-report.zip
```

Verified SHA-256:

```text
9e8ad1e2191ae5fd530eadde2d2acfa62fec64d2b4b499148910b3b5fd9c393f
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Prior integrity:

```text
indexed payloads = 168
missing = 0
extra = 0
hash mismatch = 0
size mismatch = 0
```

Recompute independently.

---

# 2. M12AD completed source branch — reference only

Reported M12AD branch:

```text
codex/20260911-financial-framework-negation-holder-stability-m12ad
```

Reported commits:

```text
base_sha =
6fc68f6bb8a7f88b375338cefc357670f617d575

work_instruction_commit =
ee61646c5c0e7516bbf318d2c75232bb9f2c60bf

implementation_commit =
c52b852c515e08c5123534810fd33c4768f67060

report_commit =
689fc9181bfeee8f5fd404d45954dfb6bef8790b
```

The exported completion file did not provide a trusted concrete final HEAD.

Therefore at task start resolve the actual current/source branch HEAD from Git.

Record:

```text
m12ad_source_branch
m12ad_source_head_sha
m12ad_source_worktree_status
```

If the source branch cannot be unambiguously resolved:

```text
STOP
M12AD_SOURCE_HEAD_UNRESOLVED
```

Do not guess from the report commit.

---

# 3. Freeze latest main exactly once

At task start:

```text
fetch/resolve latest remote main
```

Record:

```text
main_remote
main_branch_name
main_frozen_sha
main_commit_date
```

Preferred authority:

```text
origin/main
```

or the repository's actual configured primary remote/main ref.

If no remote main is available,
use the repository's authoritative main branch
and state the limitation.

Once:

```text
main_frozen_sha
```

is recorded, do NOT chase a newer moving main during this task.

If main advances later:

```text
record MAIN_ADVANCED_AFTER_FREEZE
```

but keep this proof on the frozen integration baseline.

A later final-main merge can revalidate any new drift separately.

---

# 4. Working-tree precondition

Before integration:

```text
working tree must be clean
```

Allowed exceptions:

```text
task-generated artifacts outside repository
```

If tracked/untracked repository changes exist
and cannot be attributed to the authorized source branch:

```text
STOP
DIRTY_WORKTREE_BEFORE_INTEGRATION
```

Do not stash unknown user work silently.

---

# 5. Create an isolated integration branch

Suggested branch:

```text
codex/20260911-main-integration-two-stage-directional
```

Preferred construction:

```text
start from main_frozen_sha

merge m12ad_source_head_sha
with history preserved
```

Use a real integration branch.

Do not:

```text
force-push main
commit directly on main
reset main
squash away source history without reason
```

Record:

```text
integration_branch
integration_premerge_main_sha
integration_source_head_sha
integration_merge_base_sha
integration_merge_commit_sha
```

If the repository policy requires another equivalent merge method,
document it.

---

# 6. Merge conflict policy

If Git conflicts occur:

```text
do not use blanket "ours"
do not use blanket "theirs"
```

Every conflict must receive:

```text
file path
conflict type
main-side behavior
Thesis-Monitor-side behavior
chosen resolution
semantic rationale
test coverage
```

Create:

```text
integration-conflict-ledger.json
```

Important conflict domains include:

```text
Directional services/prompts/schemas

financial-context services

business-delta validators

financial-framework scope validators

source sufficiency

monitoring lifecycle

warnings/notifications

Price-Timing

Renderer

persistence/storage

runner/runtime

configuration
```

If a conflict cannot be resolved without changing a frozen semantic contract:

```text
STOP
MAIN_INTEGRATION_SEMANTIC_CONFLICT_REQUIRES_REVIEW
```

---

# 7. No silent loss of latest-main behavior

The integration must preserve legitimate latest-main fixes/features.

Do not assume:

```text
feature branch always wins.
```

After merge, audit main-only changes touching Thesis Monitor-relevant modules.

Record:

```text
main_only_relevant_commit_count

main_only_relevant_files

main_only_semantic_change_summary
```

If latest main introduced a newer intentional semantic contract
that conflicts with M12AD:

```text
STOP
MAIN_AND_M12AD_SEMANTIC_CONTRACT_CONFLICT
```

Do not silently overwrite it.

---

# 8. No silent loss of M12AD semantics

The integrated baseline must retain completed M12AD contracts:

```text
FIRST_CLASS_TYPED_EVIDENCE_UNIFICATION

working-capital materiality grounding

QTD/YTD Korean period semantics

financial-framework negation/contrastive application scope

business-delta alias/canonical resolution

absolute current state != business delta

market-expectation economic-independence contract

Directional balance/confidence separation

holder REVIEW/REDUCE contract

decision-material stability policy
```

Create a semantic fingerprint before and after merge.

Required:

```text
m12ad_semantic_fingerprint_status = PRESERVED
```

or STOP.

---

# 9. Integration baseline must be validated BEFORE two-stage implementation

This is mandatory.

After:

```text
latest main + M12AD
```

but BEFORE two-stage code changes,
run an integration-baseline validation.

Required:

```text
focused existing Thesis Monitor tests PASS

full local repository tests PASS

ruff PASS

git diff --check PASS

runtime/config smoke checks PASS

production side-effect firewall PASS
```

Record:

```text
post_merge_baseline_sha
```

Only after this baseline passes may two-stage architecture implementation begin.

Purpose:

```text
separate merge regressions
from
two-stage regressions.
```

If post-merge baseline fails:

```text
repair only integration regressions

rerun baseline tests
```

If still unresolved:

```text
STOP
MAIN_INTEGRATION_BASELINE_FAIL
```

No model calls.

---

# 10. Integration entrypoint audit

Before two-stage implementation,
map actual integrated runtime entrypoints.

At minimum identify:

```text
current authoritative monolithic Directional entrypoint

financial-context producer path

business-delta validator path

financial-framework scope validator path

Price-Timing entrypoint

Structured Composer

Renderer

monitoring assessment path

cold-start/onboarding path

shadow/nonproduction runner path
```

Report:

```text
authoritative_production_path

experimental_shadow_path

duplicate_or_stale_path_count
```

Do not leave multiple ambiguous production-authoritative paths.

---

# 11. Stale/duplicate path detection

The merge may expose both:

```text
newer main path

older feature-branch path
```

for the same function.

Audit for:

```text
duplicate Directional runners

duplicate prompt constructors

duplicate schema versions

duplicate evidence projection paths

duplicate delta validators

duplicate framework validators

stale feature flags

dead legacy adapters
```

Do not delete working legacy paths merely because they are old.

Classify:

```text
AUTHORITATIVE

LEGACY_COMPATIBILITY

SHADOW_CONTROL

DEAD_OR_STALE_REVIEW_REQUIRED
```

No destructive cleanup beyond what is required for unambiguous testing.

---

# 12. Proof-critical model/runtime

Use:

```text
model = gpt-5.6-sol
reasoning = xhigh
```

for all proof-critical model calls.

No GPT-6 Astra.

No fallback.

Runtime:

```text
MODEL_CONTEXT_COUPLED
up to 4 subjects/context
1800-second finite watchdog
single authoritative watchdog
wrapper auto-retry = 0
batch split = 0
```

If actual runner differs:

```text
STOP
SOL_RUNNER_MODEL_TARGET_MISMATCH
```

---

# 13. Why two-stage architecture is still required

M12AD showed a credible monolithic cross-field interference signal.

Same frozen FIC-FIN-05 source context:

```text
M12AC:
core SELL 4.0:6.0 ×3
new buyer AVOID ×3
holder REDUCE / REVIEW / REDUCE

M12AD after detailed holder contract in same monolithic prompt:
core SELL / HOLD / HOLD
new buyer WAIT ×3
holder REVIEW ×3
```

This is not perfect causal proof.

It is enough to enforce:

```text
stance instructions must not be able
to mutate finalized core fields.
```

---

# 14. Selected two-stage architecture

Use internal:

```text
Stage 1 — Core Economic Judgment

Stage 2 — Fundamental Stance

Deterministic Composer
```

Directional remains the owning domain.

No ownership transfer to Price-Timing or Renderer.

---

# 15. Stage 1 ownership

Stage 1 owns:

```text
ticker

overall_direction

directional_balance

hold_lean

directional_confidence

business_thesis_change

core_investment_judgment

material_directional_anchor_basis

business_thesis_context

buy_drivers

sell_drivers

earnings_estimate_context

market_expectation_context

valuation_context

sector_interpretation

risk_context

uncertainty_limit

unknown_treatments

business_reevaluation_up

business_reevaluation_down
```

Stage 1 MUST NOT output:

```text
fundamental_new_buyer

fundamental_holder
```

Stage 1 prompt MUST NOT contain substantive calibration for:

```text
ATTRACTIVE / WAIT / AVOID

HOLDABLE / REVIEW / REDUCE
```

---

# 16. Stage 2 ownership

Stage 2 receives:

```text
frozen Stage 1 core object

same evidence alias catalog required for citations

generic new-buyer contract

generic holder contract
```

Stage 2 outputs only:

```text
ticker

fundamental_new_buyer

fundamental_holder
```

Stage 2 schema MUST NOT expose writable:

```text
overall_direction

directional_balance

hold_lean

directional_confidence

business_thesis_change

buy_drivers

sell_drivers
```

---

# 17. Core immutability

Compute:

```text
core_snapshot_sha256
```

over normalized Stage 1 core.

After Stage 2 + composition:

```text
post_compose_core_sha256
```

Hard require:

```text
core_snapshot_sha256
=
post_compose_core_sha256
```

Mismatch:

```text
OBJECTIVE_ARCHITECTURE_HARD_FAILURE
STOP
```

---

# 18. Final external schema compatibility

Internal schemas may be new.

Final composed Directional object must remain compatible with:

```text
Price-Timing

Structured Composer

Renderer

monitoring lifecycle

existing final validators

stored legacy output readers
```

Required:

```text
final_user_facing_directional_schema_change_count = 0
```

If latest main changed the final schema,
use the integrated-main schema as authority
and prove backward compatibility.

---

# 19. Integration-specific persistence audit

Because this task now runs on latest-main integrated code,
audit:

```text
storage model compatibility

assessment persistence expectations

watchlist/monitoring record compatibility

warning lifecycle

notification payload expectations

serialized final Directional payload readers
```

M12AE-R2 does NOT write to production persistence.

But the new composed final object must be consumable
by the current integrated-main persistence/read paths.

If broad DB migration is required:

```text
STOP
TWO_STAGE_PERSISTENCE_INTEGRATION_REVIEW_REQUIRED
```

Do not migrate production in this task.

---

# 20. Price-Timing / Renderer integration audit

After two-stage composition,
validate that integrated-main:

```text
Price-Timing
Renderer
```

consume the final object without:

```text
missing fields

duplicate fields

wrong ownership assumptions

core mutation

holder/new-buyer recalculation
```

No substantive Price-Timing change.

No substantive Renderer change.

Required:

```text
price_timing_semantic_change_count = 0

renderer_substantive_change_count = 0
```

---

# 21. Freeze monolithic control after main integration

The monitored shadow comparison requires a control.

Freeze the latest integrated monolithic Directional control:

```text
same latest-main + M12AD semantic baseline

before two-stage architecture affects the model-facing path
```

Record:

```text
monolithic_control_prompt_sha256

monolithic_control_schema_sha256

monolithic_control_code_sha256
```

Do not later alter the control silently.

The comparison is:

```text
same integrated codebase
same semantic contract
same evidence packet

monolithic generation
vs
two-stage generation.
```

---

# 22. Fictional proof must run first

Before monitored-stock shadow calls:

```text
full two-stage fictional proof must PASS hard/material gates.
```

If fictional phase fails:

```text
STOP
NO MONITORED SHADOW MODEL CALLS
```

Do not use existing monitored names to debug a broken architecture.

---

# 23. Fictional topology

Frozen subjects:

```text
FIC-FIN-01
FIC-FIN-02
FIC-FIN-03
FIC-FIN-04
FIC-FIN-05
FIC-FIN-06
FIC-FIN-07
FIC-FIN-08
```

Three repetitions.

Per repetition:

```text
Stage 1:
2 contexts × 4 subjects

Stage 2:
2 contexts × 4 subjects
```

Total:

```text
Stage 1 fictional calls = 6

Stage 2 fictional calls = 6

fictional model calls total = 12

final fictional outputs = 24
```

No judge calls.

---

# 24. Fictional hard acceptance

Require:

```text
Stage 1 6 / 6 success

Stage 2 6 / 6 success

24 / 24 final composed rows valid

timeout = 0

capacity failure = 0

orphan = 0

wrapper retry = 0

core mutation after stance = 0

objective financial semantic failure = 0

invalid evidence refs = 0

grounding failure = 0

business-delta violation = 0

financial-sector true misuse = 0

legitimate exclusion false reject = 0

Stage 2 core-field output attempt = 0

Stage 2 price/technical/supply fundamental-stance contamination = 0
```

---

# 25. Fictional decision-material stability

Blocking fields:

```text
overall_direction

business_thesis_change

fundamental_new_buyer.stance

fundamental_holder.stance
```

Readiness blockers:

```text
PRIMARY_DIRECTION_UNSTABLE

BUSINESS_DELTA_UNSTABLE

NEW_BUYER_STANCE_UNSTABLE

HOLDER_STANCE_UNSTABLE
```

Same-direction 0.5 balance/lean/confidence variation remains reported,
but does not automatically block.

FIC-FIN-05 holder target remains:

```text
REVIEW ×3
```

under the frozen holder contract.

---

# 26. Existing monitored universe — reference snapshot

At instruction creation time, the read-only active monitored universe was:

```text
KRX — 8

000660  SK하이닉스
003690  코리안리
005490  POSCO홀딩스
005930  삼성전자
010120  LS일렉트릭
012450  한화에어로스페이스
047810  한국항공우주산업
086280  현대글로비스
```

```text
US — 14

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

Reference count:

```text
22
```

At shadow-phase start,
re-enumerate active monitored stocks read-only.

Use the actual task-start list.

Do not hard-code the 22 count.

---

# 27. Existing monitored stocks are compatibility cohort, not unseen proof

The active monitored universe is:

```text
exposed

familiar

not a generalization holdout
```

Use it for:

```text
regression detection

architecture compatibility

migration impact

decision-material difference review
```

Do not report shadow success as:

```text
fresh real generalization PASS.
```

---

# 28. Shadow phase uses frozen same-packet evidence

For every active monitored ticker,
retrieve or construct ONE reproducible fundamental evidence packet.

Preferred:

```text
latest archived/accepted local DecisionEvidencePacket
or equivalent deterministic local packet
```

No external provider refresh by default.

Hard default:

```text
provider_source_fetches = 0
```

For each ticker compute:

```text
shadow_packet_sha256
```

The exact same packet must feed:

```text
monolithic control

two-stage Stage 1

two-stage Stage 2 evidence/citation context
```

If hashes differ:

```text
SHADOW_COMPARISON_INVALID
```

---

# 29. Do not compare to stale production output as primary baseline

Do NOT primarily compare:

```text
old stored production assessment
vs
new two-stage output on a different packet.
```

Primary architecture comparator:

```text
same frozen packet
same integrated codebase
same semantic contract

monolithic control
vs
two-stage path.
```

Historical stored assessment may be shown separately as:

```text
HISTORICAL_DESCRIPTIVE_ONLY
```

---

# 30. Shadow call topology

For:

```text
N = task-start active monitored stock count
```

Use:

```text
context_count = ceil(N / 4)
```

Then:

```text
monolithic control calls = context_count

two-stage Stage 1 calls = context_count

two-stage Stage 2 calls = context_count

total shadow calls = 3 × context_count
```

At N=22 reference:

```text
6 + 6 + 6 = 18 shadow calls
```

Do not hard-code 18.

One comparison per monitored ticker only.

No three-repeat shadow test.

---

# 31. Shadow run order

For each frozen context group:

```text
1. monolithic control

2. two-stage Stage 1

3. two-stage Stage 2

4. deterministic composition

5. compatibility comparison
```

Record:

```text
context tickers

packet hashes

model invocation IDs

core hashes
```

No packet refresh between paths.

---

# 32. Shadow comparison fields

Per ticker compare:

## Core

```text
overall_direction

directional_balance

hold_lean

directional_confidence

business_thesis_change
```

## Stance

```text
fundamental_new_buyer.stance

fundamental_holder.stance
```

## Support

```text
material anchor domains

dominant evidence refs

major Unknowns

business reevaluation conditions

business invalidation condition
```

## Safety

```text
invalid refs

grounding

business-delta support

financial-sector/ADR basis safety

price/technical/supply contamination
```

---

# 33. Shadow compatibility taxonomy

Each ticker gets one primary label:

```text
NO_DECISION_MATERIAL_CHANGE

SAME_DIRECTION_CALIBRATION_CHANGE

BUSINESS_DELTA_CHANGE

NEW_BUYER_STANCE_CHANGE

HOLDER_STANCE_CHANGE

PRIMARY_DIRECTION_CHANGE

MULTI_FIELD_DECISION_CHANGE

EXPECTED_CONTRACT_CORRECTION

POTENTIAL_ARCHITECTURE_REGRESSION

NOT_COMPARABLE_PACKET_UNAVAILABLE

NOT_COMPARABLE_PACKET_MISMATCH

OTHER_REVIEW_REQUIRED
```

Do not automatically call every difference a regression.

---

# 34. Expected contract correction

Use only when the two-stage result is clearly more consistent
with an already-frozen semantic rule.

Examples:

```text
monolithic REDUCE
→ two-stage REVIEW

while critical severity/persistence remains unresolved
and frozen holder contract clearly says REVIEW
```

or:

```text
monolithic WEAKENED
→ two-stage UNCHANGED

while same packet has no baseline deterioration.
```

Still report the material change.

---

# 35. Potential architecture regression

Use when the two-stage result introduces a decision-material change
not justified by:

```text
same packet

frozen semantic contract

or removal of monolithic cross-field interference.
```

Examples:

```text
core direction changes after Stage 1 loses a material evidence domain

business delta loses valid comparable evidence

Stage 2 contradicts core

holder REDUCE appears without sufficient fundamental severity

new buyer becomes ATTRACTIVE despite unresolved critical validation/valuation conditions
```

Every such classification needs exact evidence refs.

---

# 36. Shadow sector/security-basis coverage

Report actual integrated compatibility across:

```text
KR / US

insurance/financial sector

memory/semiconductors

cyclical materials

industrial/electrical

defense/aerospace

logistics

internet/consumer

AI/HPC data center

software/enterprise

biotech

autonomous driving

automotive/AI

foundry

other stored sectors
```

Do not invent labels not supported by stored metadata.

Special hard audits:

```text
003690 코리안리
→ financial-sector framework safety

SKHY
→ ADR/security/currency-basis safety

memory/material cyclical names
→ no simplistic peak-cycle PER-only reasoning
```

---

# 37. Production side-effect firewall

Across merge/integration/fake/shadow phases:

```text
model_calls_real_fresh_unseen = 0

provider_source_fetches = 0

production_db_mutations = 0

monitoring_registrations = 0

monitoring_stops = 0

assessment_persistence_mutations = 0

warning_mutations = 0

notification_queue_writes = 0

production_sends = 0

main_branch_mutations = 0

main_merges = 0

deployments = 0

automatic_monitoring_resume = 0
```

Git merge INTO the isolated integration branch is allowed.

Merge FROM integration branch INTO main is forbidden.

---

# 38. Schedule state

Existing monitoring schedules remain paused.

Observe at start/end.

Do not resume them.

Do not change unrelated scheduler jobs.

Record:

```text
observed_paused_schedule_count

scheduler_mutation_count

automatic_monitoring_resume
```

---

# 39. Hosted CI portability

Preserve existing known portability backlog.

The integration task must report:

```text
post_merge_hosted_ci_status

post_two_stage_hosted_ci_status

new_hosted_ci_failure_count
```

Do not introduce new portability failures.

Do not claim CI PASS unless fully green.

Do not broaden this task into cleanup of pre-existing portability failures
unless latest main already fixed them naturally.

---

# 40. Required integration artifacts

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-main-freeze

04-m12ad-source-head-freeze

05-integration-branch-creation

06-integration-merge-base

07-integration-conflict-ledger

08-main-only-relevant-change-audit

09-m12ad-semantic-fingerprint-before-merge

10-integrated-semantic-fingerprint-after-merge

11-post-merge-entrypoint-map

12-duplicate-stale-path-audit

13-persistence-compatibility-audit

14-price-timing-renderer-integration-audit

15-post-merge-integration-baseline-tests

16-post-merge-baseline-freeze
```

Artifact 16 must include:

```text
post_merge_baseline_sha
```

No two-stage code before baseline PASS.

---

# 41. Required two-stage architecture artifacts

Produce:

```text
17-monolithic-control-prompt-freeze

18-monolithic-control-schema-freeze

19-two-stage-directional-contract

20-stage1-core-schema

21-stage1-core-prompt-contract

22-stage2-stance-schema

23-stage2-stance-prompt-contract

24-core-immutability-hash-contract

25-final-composer-contract

26-final-schema-compatibility-proof

27-legacy-output-compatibility-proof

28-cross-field-isolation-proof

29-integrated-persistence-reader-compatibility-proof

30-integrated-price-timing-consumer-proof

31-integrated-renderer-consumer-proof
```

---

# 42. Required deterministic validation artifacts

Produce:

```text
32-focused-test-results-after-two-stage

33-full-local-test-results-after-two-stage

34-ruff-and-diff-results

35-hosted-ci-portability-observation

36-fictional-model-call-gate
```

No fictional model calls before artifact 36 PASS.

---

# 43. Required fictional artifacts

Produce:

```text
37-fictional-two-stage-generation-manifest

38-fictional-source-lock

39-stage1-run-1-context-01

40-stage1-run-1-context-02

41-stage2-run-1-context-01

42-stage2-run-1-context-02

43-stage1-run-2-context-01

44-stage1-run-2-context-02

45-stage2-run-2-context-01

46-stage2-run-2-context-02

47-stage1-run-3-context-01

48-stage1-run-3-context-02

49-stage2-run-3-context-01

50-stage2-run-3-context-02

51-full-stage1-hard-semantic-audit

52-full-stage1-core-stability

53-full-stage2-stance-semantic-audit

54-full-stage2-new-buyer-stability

55-full-stage2-holder-stability

56-full-core-immutability-audit

57-full-final-composition-schema-audit

58-full-final-decision-material-stability

59-full-final-calibration-variance

60-full-financial-framework-scope-audit

61-full-business-delta-audit

62-full-grounding-audit

63-full-two-stage-runtime-audit

64-fictional-two-stage-readiness-decision
```

If artifact 64 != PASS:

```text
STOP
NO MONITORED SHADOW MODEL CALLS
```

---

# 44. Required monitored-shadow setup artifacts

Only after fictional PASS:

```text
65-task-start-active-monitored-universe

66-reference-vs-task-start-universe-diff

67-shadow-packet-source-contract

68-shadow-packet-inventory

69-shadow-packet-hash-manifest

70-shadow-batching-manifest

71-shadow-model-call-gate
```

---

# 45. Required monitored-shadow artifacts

Produce:

```text
72-shadow-monolithic-control-artifacts

73-shadow-stage1-core-artifacts

74-shadow-stage2-stance-artifacts

75-shadow-final-composition-artifacts

76-shadow-per-ticker-comparison-table

77-shadow-core-direction-differences

78-shadow-business-delta-differences

79-shadow-new-buyer-differences

80-shadow-holder-differences

81-shadow-same-direction-calibration-differences

82-shadow-expected-contract-corrections

83-shadow-potential-architecture-regressions

84-shadow-unresolved-review-required

85-shadow-sector-coverage

86-shadow-adr-security-basis-audit

87-shadow-financial-sector-audit

88-shadow-cyclical-valuation-framework-audit

89-shadow-core-immutability-audit

90-shadow-runtime-audit

91-shadow-compatibility-readiness-decision
```

Raw prompt/schema/output/receipt/log/run artifacts
must be preserved for each actual shadow model context.

---

# 46. Required final completion artifacts

Produce:

```text
92-main-integration-success-decision

93-two-stage-architecture-success-decision

94-fictional-proof-success-decision

95-shadow-compatibility-success-decision

96-existing-monitored-impact-summary

97-two-stage-real-holdout-suitability

98-fresh-real-proof-readiness-decision

99-final-main-merge-readiness-note

100-hosted-ci-portability-handoff

101-astra-future-experiment-handoff

102-production-no-change

103-schedule-pause-observation

104-master-workflow-update

105-program-completion
```

---

# 47. Post-merge integration baseline acceptance

Before two-stage implementation:

```text
latest main frozen

M12AD source head frozen

integration branch created from latest main

M12AD merged into integration branch

all conflicts documented

M12AD semantic fingerprint preserved

latest-main relevant behavior preserved

authoritative entrypoints unambiguous

focused baseline tests PASS

full local baseline tests PASS

ruff PASS

git diff --check PASS

production side-effect firewall PASS
```

If this fails:

```text
STOP
MAIN_INTEGRATION_BASELINE_FAIL
```

No model calls.

---

# 48. Two-stage deterministic acceptance

Before fictional model calls:

```text
Stage 1 has no substantive stance contract

Stage 1 schema has no stance fields

Stage 2 schema has no core mutable fields

core hash immutability tests PASS

final integrated-main schema compatibility PASS

legacy output compatibility PASS

integrated persistence readers accept composed output

integrated Price-Timing accepts composed output

integrated Renderer accepts composed output

holder/new-buyer regressions PASS

business-delta regressions PASS

financial-framework regressions PASS

financial grounding/QTD/WC/debt regressions PASS

threshold/increment/tie-break unchanged

no majority vote

no averaging

no scorecard

focused/full local tests PASS

ruff PASS

git diff --check PASS

production side-effect firewall PASS
```

---

# 49. Fictional acceptance before shadow phase

Require:

```text
12 / 12 fictional stage calls complete

24 / 24 final rows valid

timeout = 0

capacity failure = 0

orphan = 0

wrapper retry = 0

core mutation after stance = 0

objective semantic failures = 0

invalid refs = 0

grounding failure = 0

business-delta violation = 0

financial-sector true misuse = 0

legitimate exclusion false reject = 0

PRIMARY_DIRECTION_UNSTABLE = 0

BUSINESS_DELTA_UNSTABLE = 0

NEW_BUYER_STANCE_UNSTABLE = 0

HOLDER_STANCE_UNSTABLE = 0

FIC-FIN-05 holder REVIEW ×3
```

Same-direction 0.5 calibration variance alone does not block shadow.

---

# 50. Shadow acceptance

Require:

```text
all task-start active monitored stocks accounted for

same frozen packet per ticker across monolithic/two-stage paths

all planned shadow calls complete

core mutation after stance = 0

objective semantic failure = 0

production side effects = 0

all decision-material differences reviewed

potential architecture regression count = 0

unresolved review-required count = 0

packet mismatch count = 0
```

If active monitored packets are unavailable
and cannot be reproduced locally without provider refresh:

```text
shadow_compatibility_readiness = NOT_READY
```

Do not hide coverage gaps.

---

# 51. Fresh unseen real-proof readiness

Set:

```text
fresh_real_proof_readiness = READY
```

only if:

```text
main_integration_readiness = PASS

fictional_two_stage_readiness = PASS

shadow_compatibility_readiness = PASS

two_stage_real_holdout_suitability = READY

real unseen issuer exposure = 0
```

Then:

```text
next_scope =
FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT56_SOL_XHIGH_TWO_STAGE_ON_INTEGRATED_MAIN
```

Do not start the fresh real proof inside M12AE-R2.

---

# 52. Final main merge remains prohibited

Even if everything in M12AE-R2 passes:

```text
DO NOT merge integration branch into main.
```

Instead report:

```text
final_main_merge_readiness =
READY_FOR_LATER_REVIEW
or
NOT_READY
```

Still required before final main merge:

```text
fresh unseen real proof

production integration/persistence review

explicit user authorization

final drift check against then-current main
```

If main has advanced since `main_frozen_sha`,
that future final-merge task must integrate/revalidate the new drift.

---

# 53. Failure handling

## A. Latest main + M12AD baseline fails

```text
next_scope =
MAIN_INTEGRATION_REGRESSION_REPAIR
```

## B. Two-stage fictional primary direction remains unstable

```text
next_scope =
PRIMARY_DIRECTION_BOUNDARY_POLICY_REVIEW_GPT56_SOL_ON_INTEGRATED_MAIN
```

## C. Two-stage stance unstable

```text
next_scope =
FUNDAMENTAL_STANCE_STAGE_STABILITY_REVIEW_GPT56_SOL_ON_INTEGRATED_MAIN
```

## D. Shadow finds potential architecture regression

```text
next_scope =
TWO_STAGE_MONITORED_COMPATIBILITY_REGRESSION_REVIEW
```

Include exact tickers, fields, packet hashes, and evidence refs.

## E. Shadow packets unavailable

```text
next_scope =
MONITORED_SHADOW_PACKET_REPRODUCIBILITY_REPAIR
```

No provider refresh by default.

## F. Integrated persistence/consumer incompatibility

Use:

```text
TWO_STAGE_INTEGRATED_MAIN_CONSUMER_COMPATIBILITY_REPAIR
```

No production migration.

## G. Runtime failure

Stop phase.

No selective retry.

No Astra fallback.

---

# 54. Program-completion fields

Include at least:

```text
main_frozen_sha
main_commit_date
m12ad_source_head_sha

integration_branch
integration_merge_base_sha
integration_merge_commit_sha
post_merge_baseline_sha
final_integration_head_sha

integration_conflict_count
integration_conflict_resolved_count
integration_unresolved_conflict_count

main_only_relevant_commit_count
duplicate_or_stale_path_count

m12ad_semantic_fingerprint_status
main_behavior_preservation_status
integration_entrypoint_status

post_merge_baseline_focused_test_result
post_merge_baseline_full_test_result
post_merge_baseline_ruff_result
post_merge_baseline_git_diff_check

selected_directional_architecture

investment_judgment_model_target
investment_judgment_reasoning_effort
runner_model_target_match
model_target_fallback_count

stage1_core_enabled
stage2_stance_enabled

final_output_schema_change_count
internal_schema_change_count

stage1_prompt_contains_holder_contract
stage1_prompt_contains_new_buyer_contract
stage1_schema_contains_stance_fields
stage2_schema_contains_core_fields

core_snapshot_hash_enabled
fictional_core_mutation_after_stance_count
shadow_core_mutation_after_stance_count

fictional_stage1_model_calls
fictional_stage2_model_calls
fictional_model_calls_total

fictional_final_output_count
fictional_primary_direction_unstable_subject_count
fictional_business_delta_unstable_subject_count
fictional_new_buyer_unstable_subject_count
fictional_holder_unstable_subject_count
fictional_same_direction_calibration_variance_subject_count

task_start_active_monitor_count
task_start_active_monitor_tickers
reference_snapshot_added_tickers
reference_snapshot_removed_tickers

shadow_packet_available_count
shadow_packet_unavailable_count
shadow_packet_mismatch_count

shadow_context_count
shadow_monolithic_model_calls
shadow_stage1_model_calls
shadow_stage2_model_calls
shadow_model_calls_total
shadow_completed_ticker_count

shadow_no_decision_material_change_count
shadow_same_direction_calibration_change_count
shadow_primary_direction_change_count
shadow_business_delta_change_count
shadow_new_buyer_change_count
shadow_holder_change_count
shadow_multi_field_change_count

shadow_expected_contract_correction_count
shadow_potential_architecture_regression_count
shadow_unresolved_review_required_count

shadow_kr_count
shadow_us_count
shadow_sector_coverage_count

shadow_adr_security_basis_failure_count
shadow_financial_sector_framework_failure_count
shadow_cyclical_valuation_framework_failure_count

integrated_persistence_compatibility_status
integrated_price_timing_compatibility_status
integrated_renderer_compatibility_status

provider_source_fetches
production_db_mutations
monitoring_registrations
monitoring_stops
assessment_persistence_mutations
warning_mutations
notification_queue_writes
production_sends

model_calls_real_fresh_unseen

main_branch_mutations
main_merges
deployments

fictional_two_stage_readiness
shadow_compatibility_readiness
two_stage_real_holdout_suitability
fresh_real_proof_readiness
final_main_merge_readiness

directional_threshold_changed
directional_increment_changed
hold_lean_contract_changed
calibration_tiebreak_direction_changed

majority_vote_rule_count
balance_averaging_rule_count
stance_majority_vote_rule_count
fixed_score_rule_count
evidence_count_bucket_rule_count

price_timing_semantic_change_count
renderer_substantive_change_count
source_sufficiency_semantic_change_count
daily_delta_semantic_change_count

hosted_ci_status
hosted_ci_failure_count
new_hosted_ci_failure_count

observed_paused_schedule_count
scheduler_mutation_count
automatic_monitoring_resume

focused_test_result
full_test_result
ruff_result
git_diff_check

artifact_count
artifact_hash_mismatch_count
artifact_size_mismatch_count
artifact_secret_scan_failure_count

production_readiness
status
stop_reason
next_scope
```

Anything not measured:

```text
NOT_MEASURED
```

---

# 55. Artifact integrity

Freeze all integration/fake/shadow/completion artifacts
before final artifact index.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final result ZIP SHA-256.

---

# 56. Final task principle

The project is now large enough that feature-branch proof alone
is no longer sufficient.

The correct validation order is:

```text
freeze latest main once

→ create an isolated integration branch from that main

→ merge the completed Thesis Monitor work into the integration branch

→ resolve conflicts semantically

→ prove the merged baseline is clean BEFORE two-stage implementation

→ implement Core → Stance decoupling on the integrated codebase

→ prove it on the full fictional 8 × 3 two-stage canary

→ if fictional proof passes,
   freeze one same evidence packet for every active monitored stock

→ run same-packet monolithic control once

→ run same-packet two-stage path once

→ compare architecture impact across the existing monitored universe

→ require zero unresolved decision-material architecture regression

→ only then authorize a fresh unseen real cohort

→ only after the fresh real proof and production review,
   consider merging the integration branch back into then-current main
```

Do NOT:

```text
merge directly into main now

run fictional proof only on a feature branch

compare two-stage output to stale historical production output
without packet equality

refresh external providers differently for control vs two-stage

write shadow outputs into production history

change monitored investment logic or warnings

chase a moving main during one proof

let Stage 2 mutate Stage 1 core

majority-vote model outputs

return to Astra

resume production monitoring
```

Integrate first, then prove the actual code combination
that will eventually be eligible for main.
