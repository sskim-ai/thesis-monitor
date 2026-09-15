# Thesis Monitor — GPT-6 Astra Transport Runtime Architecture Review & Full Fictional Canary

## 0. Task identity

Suggested work-instruction filename:

```text
20260910-astra-transport-runtime-architecture-review-and-full-fictional-canary.md
```

Suggested result bundle:

```text
thesis-monitor-20260910-astra-transport-runtime-architecture-review-full-fictional-canary-report.zip
```

Master-workflow phase:

```text
M12V — GPT-6 Astra Transport Runtime Architecture Review
       + Full Fictional Financial Canary
```

This task begins only after M12U ended with:

```text
status = PARTIAL_STOPPED
stop_reason = M12B_RUNTIME_FAILURE
next_scope = ASTRA_TRANSPORT_RUNTIME_ARCHITECTURE_REVIEW
```

The stop-reason string reuses an older runtime-failure label.
The actual failing task is M12U.

Authoritative M12U fact:

```text
run-1/context-01
→ gpt-6-astra / xhigh
→ 1800-second timeout
→ output bytes = 0
→ no semantic output available
→ remaining 5 contexts not started
```

M12V is now a runtime-architecture task.

It must:

```text
1. forensically compare successful and failed Astra/xhigh generations

2. map the current CLI / streaming / watchdog / process topology

3. evaluate supported runtime architectures

4. select ONE bounded runtime contract

5. implement it only if necessary

6. run deterministic regression

7. if the runtime gate passes,
   immediately run one NEW full 8-subject × 3-repeat fictional canary
   in the SAME task
```

M12V must not end as a preparation-only phase
if a safe runtime contract can be frozen and validated.

---

# 1. Authoritative latest result

Authoritative latest result bundle:

```text
thesis-monitor-20260910-financial-sector-exclusion-validator-market-expectation-leverage-boundary-full-fictional-canary-report.zip
```

Verified SHA-256:

```text
73e2c4ca3713689e077507df9f54ca569f7f50055ecdca2426ecc0537b32c976
```

Recompute at task start.

If mismatch:

```text
STOP
LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH
```

Artifact index independently verified for the uploaded bundle:

```text
indexed payload count = 134
ZIP payload count excluding artifact-index = 134
missing = 0
extra = 0
hash mismatch = 0
size mismatch = 0
```

Recompute before trusting the result.

---

# 2. M12U repository provenance

Reported M12U final state:

```text
branch =
codex/20260910-financial-exclusion-expectation-m12u

base_sha =
e8e82e353ff71f251c66a1c6940af4d70ff0c778

work_instruction_commit =
459af1097022b11fab15d9cda0a5836bd144bd9c

implementation_commit =
551f98f92e1f075990de1db1fd23eff4753c4da4

report_commit =
b3bd63ac734047d624d94e08f558d47ce6b679f7

final_head_sha =
b3bd63ac734047d624d94e08f558d47ce6b679f7
```

At M12V start use actual repository HEAD as authority.

Record:

```text
actual_branch
actual_head
working_tree_state
remote_branch_sha
```

If unexplained semantic drift exists in:

```text
Directional prompt/calibration
financial validators
first-class financial evidence
fictional fixtures
runtime runner
transport adapter
watchdog
```

STOP:

```text
UNEXPLAINED_M12V_BASELINE_DRIFT
```

---

# 3. Model target — hard frozen

User-authorized target:

```text
Codex authoring =
gpt-6-astra / xhigh

investment judgment =
gpt-6-astra / xhigh
```

Required:

```text
authoring_model_target_match = true
runner_model_target_match = true
model_target_fallback_count = 0
```

Forbidden:

```text
gpt-5.6-sol fallback
another GPT model fallback
ultra authoring
reasoning downgrade
silent model-id substitution
```

If authoring target mismatch:

```text
STOP
AUTHORING_MODEL_TARGET_MISMATCH
```

If runner target unavailable:

```text
STOP
MODEL_TARGET_UNAVAILABLE
```

---

# 4. M12U deterministic semantic work is frozen

M12U completed offline semantic work before the model timeout.

## 4.1 Financial-sector exclusion

Root cause:

```text
EXPLICIT_NON_APPLICABILITY_NOMINAL_COMPLEMENT_NOT_RECOGNIZED
```

Repair status:

```text
OFFLINE_PASS
```

The validator now recognizes explicit non-applicability forms such as:

```text
적용 대상이 아니다
평가 대상이 아니다
사용 대상이 아니다
is not applicable
does not apply
```

while mixed exclusion + actual application remains rejected.

Offline fixture set includes:

```text
positive exclusion fixtures
negative application fixtures
mixed contradiction controls
```

False accept / false reject:

```text
0 / 0
```

Do not reopen this semantic repair in M12V.

## 4.2 Market expectation / leverage contract

Frozen classification:

```text
CONDITIONAL_ON_SAME_UNRESOLVED_RISK
```

Frozen outcome:

```text
LEV_EXPECTATION_CONTEXT_DEPENDENT_WITH_EXPLICIT_RULE
```

Frozen FIC-FIN-05 target:

```text
overall direction = HOLD

directional balance = 4.5 : 5.5

HOLD lean = SELL_LEAN
```

Pattern:

```text
high complete debt
+
thin cash
+
stable profitable operations
+
refinancing severity/maturity unresolved
+
market expectation conditional on that same unresolved downside
+
no distinct established pricing/expectation risk
```

The market-expectation category does NOT automatically provide
independent corroboration merely because it is a different source category.

M12U added one bounded Directional clarification for this contract.

Do not change it in M12V.

---

# 5. M12U deterministic validation is frozen

M12U local validation passed:

```text
focused tests = 186 passed

full local tests = 3225 passed

ruff = PASS

git diff --check = PASS
```

Hosted CI remains:

```text
FAIL_KNOWN_HISTORICAL_PORTABILITY

3220 passed
5 failed
new M12U failures = 0
```

The 5 hosted-CI failures are the known historical git-object/local-artifact portability backlog.

They are not the transport timeout cause.

M12V must not broaden into that P1 cleanup.

New M12V tests must introduce:

```text
new hosted-CI failure count = 0
```

---

# 6. M12U runtime failure — exact evidence

Generation:

```text
20260910-m12u-fictional-20260909T231913Z-1e045065810d
```

Attempted:

```text
run-1/context-01 only
```

Receipt:

```text
model = gpt-6-astra

reasoning effort = xhigh

CLI = OpenAI Codex v0.153.4

prompt bytes = 29190

schema bytes = 44296

timeout seconds = 1800

elapsed seconds = 1800.068784

output bytes = 0

output exists = false

return code = -15

timeout = true

CLI internal retry events = 0

wrapper retry = 0

orphan process count = 0
```

Network-readiness preflight:

```text
ready = true
resolved address count = 4
```

Runtime isolation:

```text
invocation unique = true
namespace unique = true
working directory unique = true
session identity unique = true
sqlite WAL probe = PASS
```

In-flight observation around ~15 minutes:

```text
runner process alive
CLI process alive
runner CPU snapshot ~0%
CLI CPU snapshot ~1%
current context = run-1/context-01
```

No backend output was produced before the authoritative watchdog terminated the process.

Do not interpret:

```text
empty semantic audit rows
```

as a clean semantic proof.

---

# 7. Repeated Astra timeout history

The runtime architecture review must use all comparable Astra/xhigh history.

## Earlier successful Astra contexts

M12E:

```text
context-01 ≈ 371 seconds
context-02 ≈ 330 seconds
```

M12T:

```text
context-01 ≈ 322 seconds
context-02 ≈ 332 seconds
```

Same broad runtime family:

```text
gpt-6-astra / xhigh
MODEL_CONTEXT_COUPLED
4 subjects/context
1800-second authoritative watchdog
wrapper retry = 0
```

## Long-tail / failure observations

M12F:

```text
context-01 ≈ 1133 seconds
→ completed after WebSocket reset / CLI internal retry

context-02 = 1800-second timeout
→ WebSocket reset / internal retry observed
→ no final model output
```

M12U:

```text
context-01 = 1800-second timeout
→ no output
→ no CLI retry event observed
```

Thus:

```text
1800-second timeouts have occurred in two separate Astra generations.

A clean Astra generation also demonstrated ~5–6 minute normal completions in between.
```

This is now enough to justify a runtime-architecture review.

It is NOT enough to assert one exact backend cause.

---

# 8. M12V primary question

Answer:

```text
What transport/runtime contract can preserve:
- gpt-6-astra / xhigh
- 4-subject coupled semantics if feasible
- no semantic retry/cherry-picking
- auditable receipts
- finite failure detection

while avoiding repeated false proof failures from intermittent 1800-second no-output stalls?
```

The answer must be based on supported local/runtime capabilities.

Do not invent undocumented transport options.

---

# 9. Current transport topology audit

Map the current path end-to-end:

```text
holdout/canary runner

→ transport adapter

→ subprocess launch

→ isolated CODEX_HOME/runtime namespace

→ Codex CLI v0.153.4

→ provider = openai

→ GPT-6 Astra / xhigh sampling request

→ CLI stdout/stderr

→ runner readers

→ authoritative monotonic watchdog

→ process-group termination

→ output parse

→ receipt
```

For each layer record:

```text
module/function

timeout owner

retry owner

stream/event visibility

request/session identifier visibility

failure modes

cleanup behavior

whether progress can be distinguished from silence
```

---

# 10. Supported-interface inventory

Inspect only actually available/supported interfaces.

At minimum inspect:

```text
current Codex CLI help / supported machine-readable output modes

current transport adapter capabilities

existing OpenAI client/runtime code already present in repository, if any

whether the current environment already exposes a supported direct model-call path
using the same authenticated account/model target

whether the CLI exposes structured streaming lifecycle events,
request IDs, response IDs, progress events, or retry events
```

Do NOT:

```text
add a new paid API
add a new secret
print auth tokens
copy credentials
invent a command-line flag
```

If an option is unsupported:

```text
classify UNSUPPORTED
```

---

# 11. Runtime architecture options to evaluate

Evaluate at least these options.

## Option A — Current CLI + 1800 absolute watchdog

```text
Codex CLI
absolute 1800-second hard cap
wrapper retry = 0
4 subjects/context
```

Status:

```text
known to succeed sometimes
known to timeout in at least two separate generations
```

Do not choose KEEP unchanged without explicitly accepting that observed intermittent proof-failure risk.

## Option B — Current CLI + bounded larger hard cap

Evaluate whether the repeated history justifies a larger finite absolute hard cap.

Requirements:

```text
no infinite wait

no wrapper retry

no semantic changes

hard cap remains finite

increase must be justified by measured Astra long-tail observations,
not merely "it might need longer"
```

If selected in M12V, cap increase must be:

```text
bounded
documented
experimental runtime contract
```

Do not exceed 2× the current 1800-second cap
without explicit user authorization in a later task.

## Option C — Event-aware / activity-aware watchdog

Evaluate ONLY if the supported CLI/transport exposes reliable progress/activity events.

Potential structure:

```text
activity/stream-idle watchdog
+
larger absolute hard cap
```

But this option is valid only if:

```text
the event signal actually proves request/stream progress
```

Process liveness or low CPU alone is NOT a valid activity heartbeat.

If no supported progress event exists:

```text
Option C = UNSUPPORTED
```

Do not fake a heartbeat from a local timer.

## Option D — Supported direct model transport

Evaluate only if the existing environment/repository already has a supported direct
GPT-6 Astra/xhigh model transport using the same authorized credentials/account.

Potential advantages to evaluate:

```text
structured response/request IDs

stream events

clearer retry/error taxonomy

less agent/CLI wrapper overhead
```

Potential risks:

```text
different request semantics

different schema handling

auth/entitlement mismatch

loss of established runtime-isolation assumptions
```

Do not implement a new API integration merely for this review
if the necessary supported client/auth path does not already exist.

No new secret.

## Option E — Smaller context topology

Evaluate:

```text
4 subjects/context
vs
2 subjects/context
vs
1 subject/context
```

ONLY as a last-resort runtime architecture.

This changes the model-context coupling contract.

Therefore:

```text
it is NOT transport-neutral
```

If selected, all fictional stability must be re-baselined under the new topology,
and future real proof must use the same topology.

Do not select solely because smaller prompts "seem faster".

Require evidence that context size/topology is a likely contributor.

## Option F — Generation-level rerun after transport failure

Evaluate as a diagnostic/fallback policy only.

Important holdout rule:

```text
for real unseen cohorts,
once any real output exists,
the whole precommitted cohort is exposed/retired from unseen proof.
```

Therefore a generation-level retry cannot be the primary architecture for real proof reliability.

Do not use selective per-context retry.

Default:

```text
wrapper retry remains 0
```

---

# 12. Architecture evaluation criteria

Compare each supported option qualitatively on:

```text
transport reliability

tail-latency tolerance

failure detection

observability

request identity

cohort/proof integrity

semantic comparability

implementation complexity

cleanup safety

auth/security impact

future real-holdout suitability
```

Use qualitative labels:

```text
STRONG
ACCEPTABLE
WEAK
BLOCKING
UNSUPPORTED
```

Do not create a weighted score.

---

# 13. Required architecture decision

M12V must select exactly ONE runtime contract:

```text
KEEP_CURRENT_1800_ABSOLUTE

INCREASED_FINITE_ABSOLUTE_WATCHDOG

EVENT_AWARE_WITH_FINITE_HARD_CAP

SUPPORTED_DIRECT_TRANSPORT

REDUCED_CONTEXT_TOPOLOGY

OTHER_BOUNDED_RUNTIME_CONTRACT
```

or:

```text
NO_SAFE_RUNTIME_CONTRACT_AVAILABLE
```

If no safe contract can be frozen:

```text
STOP
NO_MODEL_CALLS
next_scope = ASTRA_TRANSPORT_RUNTIME_ARCHITECTURE_REVIEW_V2
```

Do not produce a vague menu as the final decision.

---

# 14. No silent timeout inflation

If a larger hard cap is selected:

Required artifact must state:

```text
old cap

new cap

reason

expected failure behavior

why this does not mask an indefinite hang

why wrapper retry remains 0
```

No timeout change merely to make the test pass.

The new hard cap is an experiment/runtime parameter,
not a change to investment semantics.

---

# 15. No selective retry

Hard freeze:

```text
per-context wrapper retry = 0
```

If a model context fails:

```text
generation stops
```

Do not rerun only the failed context.

Do not stitch generations.

A later new generation may be authorized only as a new proof attempt,
with the failed generation preserved.

---

# 16. Runtime observability instrumentation

M12V may add semantic-neutral instrumentation.

Prefer recording:

```text
process spawn timestamp

network-readiness timestamp

first stderr event timestamp

last stderr event timestamp

first stdout byte timestamp

last stdout byte timestamp

CLI internal retry timestamps

session/request/response ID if actually exposed

watchdog trigger timestamp

process termination timestamp

return code

stdout/stderr byte counts

process CPU/RSS snapshots at bounded intervals
if supported safely

runtime namespace / workdir identity
```

Do not store:

```text
auth tokens
cookies
secret headers
```

Do not use instrumentation to mutate or interfere with the model process.

---

# 17. First-byte / no-output distinction

Current M12U receipt shows:

```text
output bytes = 0
```

but that does not necessarily prove the backend did no work.

M12V should distinguish, if supported:

```text
NO_STREAM_ACTIVITY

STREAM_ACTIVITY_BUT_NO_FINAL_OUTPUT

FINAL_OUTPUT_PARTIAL

FINAL_OUTPUT_COMPLETE
```

Do not invent a state that cannot be measured.

If Codex CLI only exposes final stdout,
state that limitation clearly.

---

# 18. CLI internal retry vs wrapper retry

Continue to separate:

```text
CLI_INTERNAL_RETRY

THESIS_MONITOR_WRAPPER_RETRY
```

M12F observed internal CLI retry events.

M12U did not.

Required runtime receipt fields:

```text
cli_internal_retry_event_count

wrapper_retry_count
```

Do not claim "retry = 0" without saying which layer.

---

# 19. Runtime version audit

Record:

```text
Codex CLI version

Python version

OS

transport adapter version/hash

runner hash

watchdog implementation hash
```

Compare failed/successful generations.

Do not upgrade CLI/dependencies automatically.

If version drift is identified as causal:

```text
freeze a bounded version decision
```

before changing it.

No broad dependency upgrade.

---

# 20. Local resource / contention audit

For comparable historical runs and current environment inspect what is available:

```text
concurrent Codex/model processes

CPU load

memory pressure

file-descriptor pressure

disk pressure

runtime-state SQLite lock/WAL state

process orphan state
```

Do not claim resource contention unless evidence supports it.

M12U observed:

```text
runner ~0% CPU
CLI ~1% CPU
```

at one snapshot.

This is evidence of low local CPU activity,
not proof of backend stall.

---

# 21. Prompt/schema complexity audit

Compare successful vs failed calls for:

```text
prompt bytes

schema bytes

subject count

evidence row count

typed financial row count

instruction count / repeated paragraphs

JSON schema complexity
```

M12U:

```text
prompt bytes = 29190
schema bytes = 44296
```

Do not claim prompt-size causality unless the historical successful/failed sample supports it.

If a true accidental duplication/regression exists,
repair only that duplication.

Do not simplify semantic contracts merely to reduce bytes.

---

# 22. Runtime architecture implementation boundary

Allowed changes:

```text
transport adapter

watchdog configuration/logic

supported event-stream handling

runtime receipt telemetry

subprocess lifecycle

supported direct transport adapter if already available/authorized

context topology only if explicitly selected by architecture decision
```

Forbidden changes:

```text
financial evidence facts

fictional case values

Directional semantic rules

balance thresholds

market-expectation leverage contract

exclusion validator semantics

QTD/YTD validator semantics

working-capital grounding

source sufficiency

renderer
```

---

# 23. M12U semantic freeze proof

Before new model calls verify unchanged:

```text
explicit financial-sector exclusion repair

market-expectation economic-independence rule

FIC-FIN-05 target =
HOLD 4.5:5.5 SELL_LEAN

FIC-FIN-01 target =
BUY 6.0:4.0

FIC-FIN-02 target =
HOLD 4.5:5.5 SELL_LEAN

FIC-FIN-04 target =
HOLD 5.0:5.0 NEUTRAL

first-class typed financial evidence

materiality-scoped WC grounding

QTD/YTD validator

FCF / YoY / debt-completeness / normalized-earnings validators
```

Required:

```text
financial_semantic_change_count = 0
directional_semantic_change_count = 0
fictional_case_change_count = 0
```

---

# 24. Threshold / ownership freeze

Required unchanged:

```text
BUY >= 6.0

SELL >= 6.0

0.5 increments

HOLD 5.5:4.5 BUY_LEAN

HOLD 5.0:5.0 NEUTRAL

HOLD 4.5:5.5 SELL_LEAN

conservative adjacent tie-break toward 5.0
```

No:

```text
majority vote
balance averaging
fixed financial scorecard
```

Price-Timing remains separate.

Renderer remains primary action wording owner.

---

# 25. Hosted CI portability remains separate

Keep current P1:

```text
HOSTED_CI_HISTORICAL_ARTIFACT_PORTABILITY_REPAIR
```

M12V must not add new absolute local artifact dependencies.

Required:

```text
new hosted-CI failure count = 0
```

Do not claim hosted CI PASS unless it becomes fully green.

---

# 26. Deterministic validation before model calls

After architecture selection/implementation run:

```text
focused pytest

full local pytest

ruff

git diff --check
```

Focused suite must include:

```text
runtime/transport adapter

watchdog behavior

process cleanup

runtime isolation

receipt generation

M12U semantic freeze regressions

exclusion validator regression

market-expectation leverage fixtures

first-class evidence

WC grounding

QTD/YTD

source-sufficiency no-change

Daily Delta no-change

Price-Timing no-change

renderer ownership
```

All must PASS.

---

# 27. Phase A model-call gate

Before any new model call require:

```text
authoring = gpt-6-astra / xhigh

latest result integrity PASS

runtime history comparison complete

supported-interface inventory complete

architecture options evaluated

one runtime architecture selected

runtime implementation complete if required

finite hard-failure contract exists

wrapper retry = 0

no semantic contract drift

focused/full local tests PASS

ruff PASS

git diff --check PASS

production side-effect firewall PASS
```

If any fail:

```text
STOP
NO_MODEL_CALLS
```

---

# 28. New full fictional generation

If Phase A passes,
run the actual proof in the SAME task.

Create a NEW generation ID.

Use exact frozen fictional subjects:

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

Do not reuse M12U output.

M12U produced none,
but its failed generation remains preserved.

Do not alter cases to reduce runtime.

---

# 29. Canary topology

Default topology remains:

```text
8 subjects
2 contexts
4 subjects/context
3 repetitions
```

Total:

```text
6 fictional model calls
24 subject outputs
```

ONLY if the selected runtime architecture explicitly changes context topology
may this differ.

If topology changes:

```text
record NEW_TOPOLOGY_BASELINE

do not compare formal stability directly to old 4-subject topology
```

No real issuers.

No judge calls.

---

# 30. Full-canary runtime contract

Use selected M12V runtime architecture.

Always require:

```text
model = gpt-6-astra
reasoning = xhigh
wrapper retry = 0
finite hard termination condition
unique invocation ID
unique runtime namespace
unique working directory
unique session identity
```

No fallback.

---

# 31. Whole-generation stop rule

If any context has:

```text
transport timeout

transport failure

hard semantic failure

target-bucket contract failure
```

then:

```text
stop immediately

preserve all emitted artifacts

do not selectively continue later contexts

do not wrapper-retry

do not stitch samples
```

Do not alter runtime parameters in the middle of the generation.

---

# 32. Runtime proof acceptance

Require:

```text
all planned contexts return successfully

timeout count = 0

capacity failure = 0

orphan process count = 0

wrapper retry = 0

runtime isolation valid
```

CLI internal retry may occur,
but must be separately reported.

If a CLI internal retry recovers successfully:

```text
transport recovered with internal retry
```

not:

```text
no transport issue
```

---

# 33. Financial hard-semantic gates

Across all completed rows require zero:

```text
invalid financial refs

material financial grounding failures

working-capital grounding failures

narrative substitution failures

price/technical/supply Directional refs

partial PPE called FCF

prior-year-end called YoY

partial debt called total debt

total liabilities called debt

normalized/adjusted earnings invention

true financial-sector industrial-framework misuse

explicit exclusion false reject

missing optional evidence treated as bearish

fixed financial scoring

QTD/YTD false reject

QTD/YTD false accept

AI imperative primary action
```

---

# 34. Frozen target-bucket contracts

Use M12U frozen contracts.

## FIC-FIN-01

```text
BUY 6.0:4.0
```

when stronger 6.5 evidence remains unresolved.

## FIC-FIN-02

```text
HOLD 4.5:5.5
SELL_LEAN
```

under shared-lineage cash-conversion divergence
with material causal/reversibility Unknown.

## FIC-FIN-04

```text
HOLD 5.0:5.0
NEUTRAL
```

when operations are flat
and non-operating composition is the only positive offset.

## FIC-FIN-05

```text
HOLD 4.5:5.5
SELL_LEAN
```

when:

```text
high complete debt
thin cash
stable profitable operations
refinancing severity unresolved
market expectation conditional on the same unresolved refinancing downside
no distinct established current pricing/expectation risk
```

Do not use old GPT-5.6 Sol labels as targets.

---

# 35. FIC-FIN-08 exclusion proof

All repetitions must allow explicit non-application language such as:

```text
"일반 사업회사의 부채·운전자본 틀은 적용 대상이 아니다."
```

without false reject,
while actual industrial-framework misuse remains rejected.

Required:

```text
explicit exclusion false reject = 0

financial-sector true misuse = 0
```

---

# 36. Core balance stability

If full generation completes,
require for targeted subjects:

```text
FIC-FIN-01 balance unique count = 1

FIC-FIN-02 balance unique count = 1

FIC-FIN-04 balance unique count = 1

FIC-FIN-05 balance unique count = 1
```

and all stable buckets must be contract-consistent.

Do not accept:

```text
stable but wrong
```

---

# 37. Formal stability

Run the unchanged formal classifier.

Report:

```text
STABLE
BOUNDARY_UNCERTAINTY
UNSTABLE
```

No:

```text
majority vote
balance averaging
classifier weakening
```

Required:

```text
opposite direction reversal = 0
```

---

# 38. Stance / delta variance

Measure separately:

```text
business_thesis_change

fundamental_new_buyer

fundamental_holder
```

Do not repair them in M12V.

If core balance/direction is stable but a formal stance/delta ambiguity remains:

```text
fresh_real_proof_readiness = NOT_READY
```

and choose the smallest bounded semantic follow-up.

Absolute direction must remain separate from business-thesis delta.

---

# 39. Runtime latency / tail audit on new generation

For every context record:

```text
prompt bytes
schema bytes
elapsed seconds
first stdout time if measurable
last stdout time if measurable
CLI internal retry count
watchdog state
return code
output bytes
```

Summarize:

```text
median
max
minimum
long-tail contexts
internal retry events
```

Compare descriptively with:

```text
M12E
M12F
M12T
M12U
```

Use:

```text
SAME_MODEL_RUNTIME_DESCRIPTIVE
```

where semantic/runtime contract is comparable.

---

# 40. Real-proof suitability decision

After successful fictional proof,
the selected runtime contract must be evaluated specifically for a fresh real holdout.

Remember:

```text
a transport timeout after some real outputs can retire the entire precommitted real cohort
from unseen-proof use.
```

Therefore before setting real readiness to READY,
state why the selected runtime contract is sufficiently robust for:

```text
no selective retry
no exposed-cohort reuse
```

Do not rely on:

```text
"we can just rerun failed real names"
```

---

# 41. No real issuer calls

Required:

```text
model_calls_real = 0
real_issuer_model_exposure_count = 0
```

M12V is still fictional validation.

---

# 42. Production side-effect firewall

Required:

```text
provider_source_fetches = 0

production_db_mutations = 0
monitoring_registrations = 0
assessment_persistence_mutations = 0
warning_mutations = 0

notification_queue_writes = 0
production_sends = 0

main_merges = 0
deployments = 0

automatic_monitoring_resume = 0
```

Observe approved paused schedules at start/end.

Do not resume them.

---

# 43. Required artifacts — provenance / integrity

Produce:

```text
01-repository-provenance

02-latest-result-integrity

03-m12v-scope-freeze

04-model-target-contract

05-authoring-model-provenance

06-runner-model-provenance
```

---

# 44. Required historical runtime artifacts

Produce:

```text
07-astra-runtime-history-table

08-m12e-runtime-extract

09-m12f-runtime-extract

10-m12t-runtime-extract

11-m12u-runtime-extract

12-success-vs-timeout-comparison
```

---

# 45. Required architecture audit artifacts

Produce:

```text
13-current-transport-topology

14-timeout-retry-ownership-map

15-supported-interface-inventory

16-cli-stream-event-capability-audit

17-direct-transport-capability-audit

18-context-topology-runtime-audit

19-resource-contention-audit

20-prompt-schema-complexity-audit

21-runtime-observability-gap-audit
```

---

# 46. Required architecture option artifacts

Produce:

```text
22-option-a-current-1800-absolute

23-option-b-larger-finite-hard-cap

24-option-c-event-aware-watchdog

25-option-d-supported-direct-transport

26-option-e-reduced-context-topology

27-option-f-generation-level-rerun-policy

28-runtime-architecture-comparison

29-preferred-runtime-architecture-decision

30-frozen-runtime-contract
```

Unsupported options must say why.

---

# 47. Required runtime implementation artifacts

If runtime changes are selected, produce:

```text
31-runtime-implementation-diff

32-watchdog-before-after

33-transport-adapter-before-after

34-runtime-receipt-contract

35-runtime-observability-implementation

36-process-cleanup-proof

37-runtime-isolation-proof
```

If no runtime code change is selected,
produce no-change equivalents.

---

# 48. Required semantic freeze artifacts

Produce:

```text
38-m12u-exclusion-contract-freeze-proof

39-m12u-market-expectation-leverage-freeze-proof

40-directional-bucket-contract-freeze-proof

41-first-class-financial-evidence-freeze-proof

42-working-capital-validator-freeze-proof

43-qtd-ytd-validator-freeze-proof

44-other-financial-validator-freeze-proof

45-source-sufficiency-no-change-proof

46-daily-delta-no-change-proof

47-price-timing-no-change-proof

48-renderer-ownership-no-change-proof
```

---

# 49. Required deterministic validation artifacts

Produce:

```text
49-focused-test-results

50-full-local-test-results

51-ruff-and-diff-results

52-hosted-ci-portability-observation

53-model-call-gate
```

---

# 50. Required full fictional canary artifacts

If Phase A passes:

```text
54-fictional-canary-generation-manifest

55-fictional-canary-source-lock

56-run-1-context-01

57-run-1-context-02

58-run-2-context-01

59-run-2-context-02

60-run-3-context-01

61-run-3-context-02

62-full-fictional-semantic-audit

63-full-fictional-exclusion-audit

64-full-fictional-market-expectation-leverage-audit

65-full-fictional-grounding-audit

66-full-fictional-business-delta-audit

67-full-fictional-formal-stability

68-full-fictional-core-only-stability

69-full-fictional-stance-variance

70-full-fictional-runtime-tail-audit

71-full-fictional-message-specificity-advisory

72-runtime-observations
```

Preserve:

```text
prompt
schema
raw output
receipt
transport log
run document
```

for every attempted context.

---

# 51. Required completion artifacts

Produce:

```text
73-runtime-architecture-proof-decision

74-runtime-real-holdout-suitability-decision

75-exclusion-validator-full-proof-decision

76-market-expectation-leverage-full-proof-decision

77-core-balance-stability-decision

78-business-delta-followup-decision

79-new-buyer-stance-followup-decision

80-holder-stance-followup-decision

81-fresh-real-proof-readiness-decision

82-hosted-ci-portability-handoff

83-production-no-change

84-schedule-pause-observation

85-master-workflow-update

86-program-completion
```

---

# 52. Phase A acceptance criteria

Before the new fictional generation:

```text
authoring model = gpt-6-astra / xhigh

latest result integrity PASS

historical Astra success/timeout evidence fully compared

current transport topology mapped

timeout/retry ownership mapped

supported runtime interfaces inspected

one runtime architecture selected

runtime contract has a finite hard-failure condition

wrapper retry remains 0

semantic contracts unchanged

runtime isolation PASS

process cleanup PASS

focused/full local tests PASS

ruff PASS

git diff --check PASS

new hosted-CI failures = 0

production side-effect firewall PASS
```

---

# 53. Full fictional acceptance criteria

If Phase A proceeds:

```text
all planned contexts complete successfully

24 / 24 subject outputs schema PASS
unless topology was explicitly changed,
in which case all precommitted subject/repetition outputs must complete

timeout count = 0

capacity failure = 0

orphan count = 0

wrapper retry = 0

hard financial semantic violation count = 0

explicit exclusion false reject = 0

financial-sector true misuse = 0

market-expectation/leverage target violation = 0

grounding failures = 0

QTD/YTD false reject = 0

QTD/YTD false accept = 0

price/technical/supply violation = 0

AI imperative primary action = 0

FIC-FIN-01 target balance unique count = 1

FIC-FIN-02 target balance unique count = 1

FIC-FIN-04 target balance unique count = 1

FIC-FIN-05 target balance unique count = 1

opposite-direction reversal = 0
```

Formal stability must be measured.

---

# 54. Fresh real proof readiness

Set:

```text
fresh_real_proof_readiness = READY
```

only if:

```text
selected runtime architecture passes the full fictional proof

runtime contract is judged suitable for exposed real holdout integrity

hard semantics PASS

core balance/direction stable

formal stability has no unresolved material business-delta/new-buyer/holder ambiguity

no real issuer exposure occurred
```

Then:

```text
next_scope =
FRESH_REAL_FINANCIAL_CONTEXT_GENERALIZATION_PROOF_GPT6_ASTRA_XHIGH
```

Do not start real proof inside M12V.

If stance/delta ambiguity remains,
select the smallest semantic follow-up.

If runtime fails again,
keep fresh real readiness NOT_READY.

---

# 55. Failure handling

## A. No safe runtime architecture can be frozen

```text
status =
M12V_RUNTIME_ARCHITECTURE_BLOCKED

next_scope =
ASTRA_TRANSPORT_RUNTIME_ARCHITECTURE_REVIEW_V2
```

No model calls.

## B. New canary has another transport timeout/failure

```text
status =
M12V_RUNTIME_PROOF_FAIL

fresh_real_proof_readiness =
NOT_READY
```

Do not retry inside the generation.

Next scope must name the selected runtime architecture's failed assumption.

## C. Runtime passes but semantic contract fails

Use:

```text
BOUNDED_DIRECTIONAL_FINANCIAL_CONTEXT_REPAIR_GPT6_ASTRA
```

with the exact failing contract.

## D. Runtime and core balance pass but stance/delta remains ambiguous

Use the smallest one of:

```text
BOUNDED_BUSINESS_DELTA_CONTRACT_REPAIR

BOUNDED_NEW_BUYER_STANCE_CALIBRATION_REPAIR_GPT6_ASTRA

BOUNDED_HOLDER_STANCE_CALIBRATION_REPAIR_GPT6_ASTRA
```

Do not combine unless one shared generic root cause is proven.

---

# 56. Production readiness

Even if M12V passes:

```text
production_readiness = NOT_READY
```

Still required:

```text
fresh unseen real GPT-6 Astra generalization proof

production integration review

explicit user authorization
```

Existing scheduled monitoring remains paused.

---

# 57. Program-completion fields

Include at least:

```text
base_sha
work_instruction_commit
implementation_commit
report_commit
final_head_sha
branch

latest_result_zip_sha256
latest_result_integrity

m12u_status
m12v_status

implementation_model_target
implementation_reasoning_effort
investment_judgment_model_target
investment_judgment_reasoning_effort

authoring_model_target_match
runner_model_target_match
model_target_fallback_count

astra_successful_historical_context_count
astra_timeout_historical_context_count

current_transport_type
current_cli_version
current_timeout_seconds
current_wrapper_retry_count
current_subjects_per_context

runtime_option_a_status
runtime_option_b_status
runtime_option_c_status
runtime_option_d_status
runtime_option_e_status
runtime_option_f_status

preferred_runtime_architecture

runtime_code_change_count
timeout_change_count
selected_timeout_seconds
wrapper_retry_change_count
selected_wrapper_retry_count
context_topology_change_count
selected_subjects_per_context

event_stream_supported
direct_transport_supported
request_id_observable
response_id_observable
first_byte_observable
progress_event_observable

transport_root_cause_classification

cli_internal_retry_event_count
wrapper_retry_count

fictional_generation_id
fictional_subject_count
fictional_context_count
fictional_repetition_count

model_calls_real
model_calls_fictional
model_calls_judge

model_context_success_count
model_context_failure_count
timeout_count
capacity_failure_count
orphan_process_count

fictional_output_row_count
fictional_schema_pass_count

hard_financial_semantic_violation_count
explicit_exclusion_false_reject_count
financial_sector_true_misuse_count
market_expectation_leverage_target_violation_count
grounding_failure_count

fic_fin_01_directional_balance_unique_count
fic_fin_02_directional_balance_unique_count
fic_fin_04_directional_balance_unique_count
fic_fin_05_directional_balance_unique_count

formal_stable_count
formal_boundary_uncertainty_count
formal_unstable_count
opposite_direction_reversal_count

business_delta_variance_subject_count
new_buyer_stance_variance_subject_count
holder_stance_variance_subject_count

runtime_median_elapsed_seconds
runtime_max_elapsed_seconds

runtime_real_holdout_suitability

hosted_ci_status
hosted_ci_failure_count
new_hosted_ci_failure_count
hosted_ci_portability_backlog_count

real_issuer_model_exposure_count

provider_source_fetches
production_db_mutations
monitoring_registrations
assessment_persistence_mutations
warning_mutations
notification_queue_writes
production_sends

main_merges
deployments

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

fresh_real_proof_readiness
production_readiness
status
stop_reason
next_scope
```

Anything not measured must remain:

```text
NOT_MEASURED
```

---

# 58. Artifact integrity

Freeze:

```text
program completion
master workflow
runtime architecture reports
all attempted model-call artifacts
```

before final artifact index creation.

Required:

```text
hash mismatch = 0
size mismatch = 0
secret scan failure = 0
```

Report final ZIP SHA-256.

---

# 59. Final task principle

M12U's semantic work was not disproven.

It was not model-tested because the first GPT-6 Astra context produced no output
before the same 1800-second class of timeout that already appeared in M12F.

The runtime history is now:

```text
normal Astra/xhigh completion:
~5–6 minutes in several contexts

long but successful:
~18.9 minutes in one M12F context

hard timeout:
M12F once
M12U once
```

The correct next move is therefore:

```text
review the transport architecture itself

→ understand what the current CLI/watchdog can actually observe

→ compare finite runtime contracts

→ freeze one runtime architecture

→ preserve all investment semantics

→ run one completely new full fictional generation in the same task

→ only if that runtime + semantic + stability proof is clean,
   authorize the fresh real cohort
```

Not:

```text
blindly raise timeout
```

Not:

```text
add selective retries
```

Not:

```text
change the financial model to make requests shorter
```

Not:

```text
split the context without acknowledging a new semantic topology
```

Not:

```text
re-run only the failed context
```

Not:

```text
use real issuers to debug transport
```

And not:

```text
resume production monitoring
```

Fix proof reliability before risking a fresh unseen real cohort.
