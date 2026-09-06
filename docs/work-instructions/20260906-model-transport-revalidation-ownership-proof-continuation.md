# thesis-monitor — Model Transport Revalidation + Ownership Proof Continuation
## Separate authorized generation after zero-output 1,800-second model timeout
## Do NOT re-run the consumed latest-holdout16 one-shot regression
## Keep Directional Core / Price-Timing ownership architecture frozen
## Diagnose transport before touching a real holdout
## Reuse the already-locked new holdout ONLY if semantic equivalence is proven
## FIRST → A → B → C on the same immutable source lock
## No production / registration / scheduler / Telegram / night-futures mutation

---

# 0. Immutable source result

Source report bundle:

```text
thesis-monitor-20260906-directional-core-price-timing-ownership-new-holdout-report.zip
```

SHA-256:

```text
8e496adf1373ca7a4489c76c8c9eda01b7b9641e55b666d6e60e5abef4597678
```

Repository state reported by the completed task:

```text
branch:
codex/20260906-directional-core-price-timing-ownership

work-instruction commit:
c90b1aa

implementation freeze:
447865ffb080aca32270cfa5f29b792428043be8

final report commit:
2ea2c93a49896f733cc24215de178fd3115d05ec
```

Implementation tree:

```text
8c16608dc4438c682288407c76ff6a515e1e07f2
```

Source generation:

```text
20260906-direction-timing-holdout-20260906T093200Z-bd30668470f0
```

Observed stop:

```text
required latest-holdout16 one-shot regression
failed_stage = DIRECTIONAL_CORE
failed_batch = 1
attempts = 1
timeout_seconds = 1800
model_output_documents = 0
completed_subjects = 0
error_class = MODEL_TIMEOUT
```

Model:

```text
gpt-5.6-sol
reasoning_effort = xhigh
```

Regression prompt/schema lock SHA-256:

```text
7f2bdd107a59fc147b25f0b9d7a928e12bf171ca56f80a9b1b45c56944f5f02a
```

Regression log SHA-256:

```text
e275ebf1134e2b8300075f36df8196d9261b8bd9f4aa21f00864e4e078d5caac
```

Implementation validation already passed:

```text
full tests = 2580 passed
Ruff = PASS
git diff --check = PASS
GitHub Actions = PASS
```

No production mutation occurred.

---

# 1. Failure classification for this continuation

The previous task produced:

```text
0 model output documents
0 completed subjects
```

Therefore the ownership architecture was NOT disproven.

Do not classify the timeout as:
- price ownership violation
- validator failure
- prompt semantic failure
- source failure
- model judgment instability

until output exists.

Initial continuation classification:

```text
BLOCKER_CLASS =
MODEL_TRANSPORT_OR_INVOCATION_TIMEOUT
```

This task must determine a narrower cause where observable.

Allowed final transport classifications include:

```text
MODEL_COMPUTE_SLOW
CLI_OR_TRANSPORT_HANG
OUTER_TIMEOUT_PREEMPTION
PROCESS_WAIT_OR_PIPE_DEADLOCK
OUTPUT_COLLECTION_OR_PARSE_BLOCK
CHILD_PROCESS_CLEANUP_FAILURE
UNKNOWN_MODEL_TRANSPORT
TRANSPORT_HEALTHY_AFTER_REVALIDATION
```

Do not claim a provider failed unless that provider was actually called and failed.

---

# 2. Separate generation; do not resume the failed regression

This is a NEW authorized continuation generation.

Forbidden:

```text
resume old regression generation
selectively rerun failed regression batch
replay only PLTR/NKE
reuse previous partial model output
```

The failed regression had no model documents, but its one-shot contract is consumed.

Required:

```text
LATEST_HOLDOUT16_MODEL_CALLS_THIS_GENERATION = 0
LATEST_HOLDOUT16_RERUN_COUNT_THIS_GENERATION = 0
```

---

# 3. Consumed latest-holdout16

The following cohort is regression-only and already consumed:

```text
PLTR, V, MA, AMZN, XOM, DIS, NKE, MCD, 033920, 104480, 071320, 096240, 032860, 060570, 016600, 462520
```

Do not issue any new model call for these subjects in this task.

Static artifact inspection is allowed.

No new investment judgment on them.

---

# 4. Ownership architecture freeze

Expected architecture hashes:

```text
alias_fencing =
3c9e7b0869a0157b40d8558c7618c5ed5c83bb8ce2240698755d2cf65b155c83

directional_balance =
2ecf5bbad338dc92d9996b60e3429ebb3c6b8d37cdb114439ffbff84166296ab

ownership_runner =
5f52ec5c866f3f07968c76ed955db8110ae052d16c2eaf8232825832647d0929

ownership_service =
8cba5d93801833ad3b004a97cefe30e2ab71c7caee75be76c93123bec0b3273a

stability_classifier =
e824e9dc7044033c091f8b40fdb0f461f629d8b420f193e060b42e7f27e13188

validator_renderer =
ee8dcdeaf42c40a49a8c56ebc140298271857eacd0bd2afc1cddb9fb631c018f
```

Expected execution mode:

```text
TWO_STAGE_FENCED
```

Expected model:

```text
gpt-5.6-sol / xhigh
```

No investment-threshold change.

Required:

```text
OWNERSHIP_ARCHITECTURE_HASH_DRIFT = 0
INVESTMENT_DECISION_THRESHOLD_MUTATION = 0
DIRECTION_TIMING_POLICY_MUTATION = 0
```

The only authorized code changes are transport/runtime/instrumentation changes that do not alter model semantics.

---

# 5. Fundamental source and source-sufficiency freeze

Expected source hashes:

```text
coldstart_assembler =
ce6bd772ad105cd2425570607806ae1ec8afa109eca94fd4c6b2e08c4b306780

company_profile =
fd4854c7781d672bf414ea43341e21ceb1879436c97defc5dff153037bdbbf5f

financial_lineage =
1a9ba3fa0d867f4d0c1fb2c5e1b034d9adeebbe32b22b0d796571d468922ff91

fundamental_enrichment =
c18627e3dd3a9a124b08583466de4361e1c5246be7ed6d2aadb306c770ed7538

opendart_recovery =
c3190d3db087ca474a9cdf250570ba36c4fd82554439b60a6ac31354cfec19b0

orchestrator =
2599d049400eab81fdf54336807bd37912496836504d1722c636cad70710afbe

provider_sector_map =
e0c1ca2c52809484594b88e1dd904fd0a985c9db76d8524c21134ab8850d99bf

provider_symbol_registry =
6cc8d7f38545a3abbe2fa882ef187ff7200d71a914d8b63e521a3917b6e226a6

sec_financial_normalizer =
9fa2d3c12c75adf0872010a84ef749b8a4c6449d244ee4f35bb042ded7874136
```

Required:

```text
FUNDAMENTAL_SOURCE_ENRICHMENT_DRIFT = 0
SOURCE_SUFFICIENCY_POLICY_DRIFT = 0
```

Do not refresh or improve company evidence during this continuation unless a new holdout is required by the semantic-equivalence gate.

---

# 6. Existing new-holdout source lock

The previous task selected a new holdout BEFORE any directional model call.

Locked cohort:

```text
ORCL, UNH, KO, AVGO, 095570, 058860, 246960, 099520, 403870, 014790, 079810, 060980, 061970, 012030, 225190, 245620
```

Market mix:

```text
US = 4
KR = 12
```

Locked source SHA-256:

```text
efe64d0942afa00c3b40131afc4de5fa411babc0680271d1571aaac69816050d
```

Pre-lock directional model calls:

```text
0
```

FIRST / A / B / C:

```text
NOT_RUN
```

This cohort is still potentially usable for real-model proof because it has not produced investment outputs.

However, reuse is conditional on Section 16.

---

# 7. Transport-only mutation boundary

Allowed changes:

```text
subprocess / CLI invocation wrapper
timeout ownership
process-group termination/cleanup
stdout/stderr collection
transport lifecycle instrumentation
bounded concurrency / queueing
external watchdog coordination
non-semantic batching container
```

Forbidden changes:

```text
Directional Core prompt wording
Price-Timing prompt wording
output schema semantics
evidence aliases
evidence selection
model
reasoning effort
direction thresholds
ownership rules
composer rules
renderer semantics
source packet contents
```

If fixing the timeout requires any forbidden change:

```text
CURRENT_HOLDOUT_REUSE_ALLOWED = 0
```

and follow Section 17.

---

# 8. Do not solve this by blindly increasing 1,800 seconds

A timeout increase without diagnosis is not sufficient.

Before changing a timeout, record what can actually be observed.

The task must distinguish, where possible:

```text
process never spawned
process spawned but input not completed
input completed but no stdout
stdout began but process never exited
process exited but output collection blocked
output collected but parse/validation blocked
outer watchdog killed child early
child timeout fired as designed
```

If the underlying CLI exposes no request-accepted event, record:

```text
REQUEST_ACCEPTED_OBSERVABILITY = UNAVAILABLE
```

Do not fabricate it.

---

# 9. Required transport lifecycle instrumentation

For every model invocation in this continuation, record machine-readable fields such as:

```text
invocation_id
generation_id
stage
batch_id
subject_count
transport_grouping_mode

model
reasoning_effort

cli_binary_identity
cli_version
working_directory_identity

prompt_sha256
schema_sha256
input_payload_sha256
input_bytes

process_spawn_monotonic
stdin_complete_monotonic
first_stdout_byte_monotonic
last_stdout_byte_monotonic
process_exit_monotonic
output_parse_complete_monotonic

elapsed_to_first_stdout_seconds
elapsed_to_exit_seconds
elapsed_to_parse_seconds

stdout_bytes
stderr_bytes
exit_code
termination_signal

configured_timeout_seconds
timeout_owner
termination_initiator
child_cleanup_status
```

Only include fields actually observable.

Never log:
- authentication tokens
- API keys
- secrets

Required:

```text
SECRET_EXPOSURE_COUNT = 0
```

---

# 10. Single authoritative timeout owner

Inventory every timeout/deadline affecting the model invocation:

```text
model/CLI internal timeout if any
Python/subprocess timeout
outer automation timeout
shell timeout
job watchdog
parent process interruption
```

Produce a timeout-owner graph.

There must be one authoritative owner for the bounded model invocation.

Required:

```text
MODEL_TIMEOUT_OWNER_COUNT = 1
EARLY_OUTER_INTERRUPT = 0
```

Any outer watchdog must expire AFTER the authoritative invocation deadline plus cleanup margin.

Do not recreate the earlier class of failure where an outer owner kills a child before the child contract completes.

---

# 11. Cleanup contract

When the authoritative timeout fires:

```text
capture diagnostics
terminate the child/process group deterministically
wait for cleanup
verify no orphan process remains
write timeout receipt exactly once
```

Required:

```text
ORPHAN_MODEL_PROCESS_COUNT = 0
DUPLICATE_TIMEOUT_RECEIPT_COUNT = 0
```

Do not send repeated Ctrl-C/SIGINT loops.

---

# 12. No retry on a real holdout timeout

Real-holdout model execution is one-attempt-per-run.

If FIRST times out:

```text
STOP
```

No:
- automatic retry
- selective ticker rerun
- batch retry
- partial completion promotion

Required:

```text
REAL_HOLDOUT_TRANSPORT_RETRY_COUNT = 0
```

Transport canaries are separate and defined below.

---

# 13. Batch semantics audit

Before changing batch size or grouping, determine what "batch" means in the frozen runner.

Classify:

```text
A. TRANSPORT_ONLY_GROUPING
each subject has an independent prompt/model context;
batch is only worker/queue/process grouping

B. MODEL_CONTEXT_COUPLED
multiple subjects share one model prompt/context/output document
```

Produce a code-grounded proof.

Do not infer from naming.

---

# 14. Batch split semantic equivalence

If current batching is `TRANSPORT_ONLY_GROUPING`, splitting may be transport-only ONLY when all per-subject semantic inputs remain identical.

Prove for representative synthetic invocations:

```text
same per-subject prompt SHA
same schema SHA
same model
same effort
same evidence aliases
same source packet SHA
same output schema
same instruction set
```

Allowed differences:

```text
batch_id
worker_id
queue grouping
process scheduling metadata
```

Required gate:

```text
BATCH_SPLIT_SEMANTIC_EQUIVALENCE =
PASS / FAIL / NOT_NEEDED
```

If batching is `MODEL_CONTEXT_COUPLED`:

```text
BATCH_SPLIT_SEMANTIC_EQUIVALENCE = FAIL
```

unless byte-equivalent model context is actually demonstrated.

Do not call "smaller batches" transport-only merely because they produce the same schema.

---

# 15. Timeout change semantic equivalence

A timeout/runtime change is transport-only only if it changes no model input.

Required:

```text
PROMPT_SHA_DRIFT = 0
SCHEMA_SHA_DRIFT = 0
MODEL_DRIFT = 0
REASONING_EFFORT_DRIFT = 0
EVIDENCE_PACKET_DRIFT = 0
```

Do not change model or effort to make the timeout disappear.

---

# 16. Current holdout reuse gate

The existing locked cohort may be reused only if ALL are true:

```text
pre-lock directional model calls = 0
no model output exists for the cohort
source lock unchanged
architecture hashes unchanged
prompt/schema semantics unchanged
model unchanged
reasoning effort unchanged
source-sufficiency policy unchanged

AND

transport repair changes only invocation/runtime behavior

AND

if batch grouping changed:
BATCH_SPLIT_SEMANTIC_EQUIVALENCE = PASS
```

Then:

```text
CURRENT_HOLDOUT_REUSE_ALLOWED = 1
```

Use source lock:

```text
efe64d0942afa00c3b40131afc4de5fa411babc0680271d1571aaac69816050d
```

in the NEW continuation generation.

Do not refresh the packets.

---

# 17. If semantic equivalence is not proven

If any prompt/schema/model/effort/evidence semantics change, or batch splitting changes model context:

```text
CURRENT_HOLDOUT_REUSE_ALLOWED = 0
```

Then:

1. retire the existing 16 from generalization use
2. freeze the repaired architecture/transport
3. exclude every issuer exposed in all earlier cohorts, including the existing 16
4. select a completely NEW issuer-level holdout
5. assemble fresh source-sufficient packets
6. create a new source lock
7. do not model-call before that source lock

No standard may be weakened to obtain 12+ names.

---

# 18. Transport canaries — no real issuer judgment

Before any real holdout model call, run bounded synthetic transport canaries.

Canaries must use fictional/ticker-free subjects.

They are not investment generalization evidence.

Do not use the consumed latest-holdout16.

Maximum:

```text
8 synthetic model invocations
```

unless fewer are sufficient.

Required sequence should include the smallest set needed to distinguish failure modes.

---

# 19. Canary 1 — CLI/process smoke

Purpose:

```text
Can the configured model/effort invocation start, emit output and exit?
```

Use:
- same CLI/runtime path
- same model `gpt-5.6-sol`
- same effort `xhigh`
- tiny non-investment structured output

Record transport timing.

This does NOT prove architecture transport readiness.

---

# 20. Canary 2 — exact Directional Core prompt/schema synthetic

Use the frozen real Directional Core prompt/schema with a ticker-free synthetic evidence packet.

Requirements:

```text
same Directional Core prompt template
same schema
same model
same effort
same ownership validator
```

No real issuer.

Verify:
- valid structured output
- transport timestamps
- validator can consume it

---

# 21. Canary 3 — representative payload size

Use synthetic subjects to approximate the real Directional Core input size and subject count.

If the frozen runner is model-context coupled, use the same contextual batch shape.

If transport-only grouping, test the actual per-subject invocation shape.

Purpose:

```text
detect payload-size / batching / pipe / output-size sensitivity
```

Do not tune investment labels from this canary.

---

# 22. Canary 4 — Price-Timing stage

Use a frozen synthetic Directional Core result plus technical aliases.

Where available in the existing technical schema include synthetic representatives of:

```text
support/resistance
volume
RSI
MACD
Bollinger
moving-average state
multi-timeframe structure
risk/reward state
supply/positioning
```

No missing feature may be fabricated as a real provider fact.

This is schema/transport test data only.

Verify Price Timing cannot mutate core direction/balance/lean.

---

# 23. Canary promotion gate

Before real holdout FIRST:

```text
TRANSPORT_CANARY_STATUS = PASS
```

Requires:
- required canaries exit normally
- structured outputs parse
- no timeout-owner conflict
- no orphan process
- prompt/schema semantic drift 0
- ownership synthetic validation still passes

If canaries fail:

```text
STOP_BEFORE_REAL_HOLDOUT = 1
```

Do not consume the current holdout.

---

# 24. Timeout policy after canary

Do not prescribe a larger timeout before evidence.

If diagnostics show the child is healthy and making observable progress near the existing deadline, a bounded timeout increase is allowed.

Maximum for this task:

```text
3600 seconds
```

Any increase must be accompanied by:

```text
old timeout
new timeout
observed canary duration
reason for increase
authoritative owner
outer watchdog deadline
cleanup margin
```

If there is no evidence of healthy progress and no stdout/output for an excessive interval, diagnose transport/hang instead of simply increasing repeatedly.

No second timeout increase in the same generation.

---

# 25. Existing current-holdout source facts

If Section 16 passes, use exactly this cohort:

```text
ORCL, UNH, KO, AVGO, 095570, 058860, 246960, 099520, 403870, 014790, 079810, 060980, 061970, 012030, 225190, 245620
```

and exactly this source lock:

```text
efe64d0942afa00c3b40131afc4de5fa411babc0680271d1571aaac69816050d
```

Do not change the 4 US / 12 KR composition.

The previous selection was valid under its frozen minimum/maximum rules.

This transport continuation is not the place to improve market balance.

---

# 26. FIRST continuation

Create a NEW continuation run identity.

Run Directional Core FIRST.

Then, only for successfully validated Directional Core outputs, run Price Timing and composer.

No result from a different run may be used.

Required per subject:
- Directional Core output
- non-price evidence refs/domains
- Directional Core transport receipt
- Price-Timing output
- technical/supply refs
- Price-Timing transport receipt
- composer output
- ownership validation
- renderer shadow result where applicable

---

# 27. FIRST gates

FIRST must show:

```text
DIRECTIONAL_CORE_PRICE_TECHNICAL_REFS = 0
DIRECTIONAL_CORE_SUPPLY_REFS = 0
SUPPLY_DIRECTIONAL_CORE_USAGE = 0

BUY_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0
SELL_WITHOUT_NONPRICE_MATERIAL_ANCHOR = 0

TIMING_STAGE_DIRECTION_MUTATION = 0
TIMING_STAGE_BALANCE_MUTATION = 0
TIMING_STAGE_HOLD_LEAN_MUTATION = 0

PRICE_TIMING_NEW_BUYER_UPGRADE = 0
PRICE_ONLY_HOLDER_REDUCE = 0

validator false positive = 0
schema failure = 0
source-sufficiency escape = 0
```

If any semantic/ownership failure appears:

```text
STOP
```

Do not repair in the same holdout generation.

---

# 28. A / B / C continuation

Proceed only if FIRST is clean.

Use:
- same holdout
- same source lock
- same model
- same effort
- same prompt/schema
- same transport policy
- same architecture

Run:

```text
A
B
C
```

No run reads another run.

No majority-vote production output.

If any run has transport timeout:

```text
STOP
```

No retry.

---

# 29. Core vs timing stability

Measure separately:

## Directional Core

```text
overall direction
BUY:SELL balance
HOLD lean
fundamental new-buyer stance
fundamental holder stance
```

## Price Timing

```text
technical state
timing modifier
entry mode
price review
holder price review
```

A timing fluctuation is not core instability.

Report:

```text
CORE_STABLE
CORE_BOUNDARY_UNCERTAINTY
CORE_UNSTABLE

TIMING_STABLE
TIMING_BOUNDARY_UNCERTAINTY
TIMING_UNSTABLE
```

---

# 30. Real-model ownership proof

The central proof is not a particular NKE/PLTR label.

Required invariants:

```text
FINAL_DIRECTION_OWNER = DIRECTIONAL_CORE

PRICE_ONLY_DIRECTIONAL_OWNERSHIP_VIOLATIONS = 0
PRICE_ONLY_HOLDER_REDUCE = 0

TIMING_STAGE_DIRECTION_MUTATION = 0
TIMING_STAGE_BALANCE_MUTATION = 0
TIMING_STAGE_HOLD_LEAN_MUTATION = 0
```

Do not require:
- NKE becomes HOLD
- PLTR becomes neutral
- any desired BUY/HOLD/SELL distribution

Those are not ground truth.

---

# 31. OHLCV / technical routing remains frozen

Preserve the prior routing result.

Existing locked holdout showed, where emitted:

```text
RSI = available
MACD = available
Bollinger = available
moving averages = available
support/resistance = available
volume = available
multi-timeframe technical context = available
```

`risk_reward` and `supply_positioning` may be unavailable for a subject.

Unavailable is not neutral or zero.

Required:

```text
OHLCV_ANALYST_CALCULATION_ALGORITHM_MUTATION = 0
INVENTED_TECHNICAL_INDICATOR = 0
```

---

# 32. Hard-safety regression

After real-model output exists, re-run hard-safety and renderer checks that were previously `NOT_MEASURED`.

At minimum:

```text
numeric provenance
accounting attribution
ADR/security basis
evidence identity/fencing
future checkpoint
logical condition
Structured Actionability command detection
structured/prose contradiction
source sufficiency
issuer dedup
renderer ownership
```

Required:

```text
KNOWN_HARD_SAFETY_REGRESSION = 0
PRIMARY_USER_ACTION_WORDING_OWNER = RENDERER
AI_IMPERATIVE_PRIMARY_ACTION = 0
```

---

# 33. No monitoring bootstrap implementation yet

This task remains proof/transport continuation only.

Required:

```text
MONITORING_REGISTRATION_CALLS = 0
BOOTSTRAP_PRODUCTION_MUTATION = 0
```

If ownership proof succeeds, prepare the next task for:

```text
user-approved Initial Analysis
→ monitor registration
→ stored investment-logic baseline
→ same fundamental enrichment bootstrap
→ source sufficiency
→ monitoring-ready baseline
→ Daily Delta only after baseline
```

Bootstrap enrichment is baseline completion, not Daily Delta.

---

# 34. Production remains unchanged

Required:

```text
MAIN_MERGE = 0
PRODUCTION_DB_MUTATION = 0
PRODUCTION_TELEGRAM_SEND = 0
PRODUCTION_SCHEDULER_CHANGE = 0
LIVE_STRUCTURED_AUTONOMY_ACTIVATION = 0
LIVE_V2_CHANGE = 0
```

---

# 35. Night futures remains unchanged

Required:

```text
NIGHT_FUTURES_CODE_MUTATION = 0
NIGHT_FUTURES_DECISION_PACKET_INJECTION = 0
```

---

# 36. Verdicts

Transport verdict:

```text
TRANSPORT_HEALTHY_AFTER_REVALIDATION
TRANSPORT_BLOCKED_MODEL_COMPUTE
TRANSPORT_BLOCKED_CLI_OR_RUNTIME
TRANSPORT_BLOCKED_TIMEOUT_OWNERSHIP
TRANSPORT_BLOCKED_UNKNOWN
```

Ownership/generalization verdict:

```text
OWNERSHIP_GENERALIZATION_STRONG
OWNERSHIP_GENERALIZATION_ACCEPTABLE_WITH_BOUNDARY_UNCERTAINTY
OWNERSHIP_GENERALIZATION_NEEDS_ARCHITECTURE_WORK
OWNERSHIP_GENERALIZATION_NOT_MEASURED_TRANSPORT_BLOCKED
```

---

# 37. Readiness

If:
- transport canaries pass
- current holdout reuse is semantically valid or a new holdout was selected
- FIRST/A/B/C all run on one immutable source lock
- ownership invariants are clean
- core stability is acceptable
- hard-safety regression is 0

then maximum:

```text
READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW
```

Still no production deployment.

If transport blocks before real proof:

```text
NOT_READY_TRANSPORT_BLOCKED
```

---

# 38. Required reports

Create:

1. `docs/reports/20260906-transport-continuation-root-cause.md`
2. `docs/reports/20260906-architecture-freeze-reverification.md`
3. `docs/reports/20260906-source-freeze-reverification.md`
4. `docs/reports/20260906-consumed-regression-no-rerun.md`
5. `docs/reports/20260906-model-transport-topology.md`
6. `docs/reports/20260906-timeout-owner-audit.md`
7. `docs/reports/20260906-process-cleanup-contract.md`
8. `docs/reports/20260906-batch-semantics-audit.md`
9. `docs/reports/20260906-batch-split-semantic-equivalence.md`
10. `docs/reports/20260906-transport-canary-smoke.md`
11. `docs/reports/20260906-transport-canary-directional-core.md`
12. `docs/reports/20260906-transport-canary-representative-payload.md`
13. `docs/reports/20260906-transport-canary-price-timing.md`
14. `docs/reports/20260906-transport-canary-verdict.md`
15. `docs/reports/20260906-current-holdout-reuse-gate.md`
16. `docs/reports/20260906-continuation-source-lock.md`
17. `docs/reports/20260906-continuation-first.md`
18. `docs/reports/20260906-continuation-run-a.md`
19. `docs/reports/20260906-continuation-run-b.md`
20. `docs/reports/20260906-continuation-run-c.md`
21. `docs/reports/20260906-continuation-core-stability.md`
22. `docs/reports/20260906-continuation-timing-stability.md`
23. `docs/reports/20260906-continuation-dominance-ownership.md`
24. `docs/reports/20260906-continuation-renderer-shadow-proof.md`
25. `docs/reports/20260906-continuation-hard-safety-regression.md`
26. `docs/reports/20260906-monitoring-bootstrap-next-handoff.md`
27. `docs/reports/20260906-production-no-change.md`
28. `docs/reports/20260906-night-futures-no-change.md`
29. `docs/reports/20260906-program-completion.md`
30. `docs/reports/20260906-artifact-index.md`

Use actual completion date if execution crosses dates.

---

# 39. Machine-readable proofs

Create:

```text
transport-continuation-root-cause.json
architecture-freeze-reverification.json
source-freeze-reverification.json
consumed-regression-no-rerun.json
model-transport-topology.json
timeout-owner-audit.json
process-cleanup-contract.json
batch-semantics-audit.json
batch-split-semantic-equivalence.json
transport-canary-smoke.json
transport-canary-directional-core.json
transport-canary-representative-payload.json
transport-canary-price-timing.json
transport-canary-verdict.json
current-holdout-reuse-gate.json
continuation-source-lock.json
continuation-first.json
continuation-run-a.json
continuation-run-b.json
continuation-run-c.json
continuation-core-stability.json
continuation-timing-stability.json
continuation-dominance-ownership.json
continuation-renderer-shadow-proof.json
continuation-hard-safety-regression.json
monitoring-bootstrap-next-handoff.json
production-no-change.json
night-futures-no-change.json
program-completion.json
```

---

# 40. Required gates

```text
SOURCE_REPORT_BUNDLE_SHA256 =
8e496adf1373ca7a4489c76c8c9eda01b7b9641e55b666d6e60e5abef4597678

SEPARATE_CONTINUATION_GENERATION =
1 / 0

LATEST_HOLDOUT16_MODEL_CALLS_THIS_GENERATION =
0 / NONZERO

LATEST_HOLDOUT16_RERUN_COUNT_THIS_GENERATION =
0 / NONZERO

OWNERSHIP_ARCHITECTURE_HASH_DRIFT =
0 / NONZERO

FUNDAMENTAL_SOURCE_ENRICHMENT_DRIFT =
0 / NONZERO

SOURCE_SUFFICIENCY_POLICY_DRIFT =
0 / NONZERO

INVESTMENT_DECISION_THRESHOLD_MUTATION =
0 / NONZERO

MODEL =
gpt-5.6-sol / OTHER

REASONING_EFFORT =
xhigh / OTHER

MODEL_TIMEOUT_OWNER_COUNT =
1 / OTHER

EARLY_OUTER_INTERRUPT =
0 / NONZERO

ORPHAN_MODEL_PROCESS_COUNT =
0 / NONZERO

SECRET_EXPOSURE_COUNT =
0 / NONZERO

BATCH_SEMANTICS =
TRANSPORT_ONLY_GROUPING /
MODEL_CONTEXT_COUPLED /
UNKNOWN

BATCH_SPLIT_SEMANTIC_EQUIVALENCE =
PASS / FAIL / NOT_NEEDED

PROMPT_SHA_DRIFT =
0 / NONZERO

SCHEMA_SHA_DRIFT =
0 / NONZERO

MODEL_DRIFT =
0 / NONZERO

REASONING_EFFORT_DRIFT =
0 / NONZERO

EVIDENCE_PACKET_DRIFT =
0 / NONZERO

TRANSPORT_CANARY_MODEL_CALL_COUNT =
...

TRANSPORT_CANARY_STATUS =
PASS / FAIL

TRANSPORT_VERDICT =
...

CURRENT_HOLDOUT_REUSE_ALLOWED =
0 / 1

CURRENT_HOLDOUT_SOURCE_LOCK =
efe64d0942afa00c3b40131afc4de5fa411babc0680271d1571aaac69816050d /
NEW_LOCK

REAL_HOLDOUT_TRANSPORT_RETRY_COUNT =
0 / NONZERO

FIRST_ABC_SOURCE_DRIFT =
0 / NONZERO

CONTINUATION_FIRST_VALIDATED =
... / NOT_RUN

CONTINUATION_RUN_A_VALIDATED =
... / NOT_RUN

CONTINUATION_RUN_B_VALIDATED =
... / NOT_RUN

CONTINUATION_RUN_C_VALIDATED =
... / NOT_RUN

DIRECTIONAL_CORE_PRICE_TECHNICAL_REFS =
0 / NONZERO

DIRECTIONAL_CORE_SUPPLY_REFS =
0 / NONZERO

SUPPLY_DIRECTIONAL_CORE_USAGE =
0 / NONZERO

BUY_WITHOUT_NONPRICE_MATERIAL_ANCHOR =
0 / NONZERO

SELL_WITHOUT_NONPRICE_MATERIAL_ANCHOR =
0 / NONZERO

TIMING_STAGE_DIRECTION_MUTATION =
0 / NONZERO

TIMING_STAGE_BALANCE_MUTATION =
0 / NONZERO

TIMING_STAGE_HOLD_LEAN_MUTATION =
0 / NONZERO

PRICE_TIMING_NEW_BUYER_UPGRADE =
0 / NONZERO

PRICE_ONLY_HOLDER_REDUCE =
0 / NONZERO

FINAL_DIRECTION_OWNER =
DIRECTIONAL_CORE / OTHER / NOT_MEASURED

PRICE_ONLY_DIRECTIONAL_OWNERSHIP_VIOLATIONS =
0 / NONZERO / NOT_MEASURED

CORE_STABLE_COUNT =
... / NOT_MEASURED

CORE_BOUNDARY_UNCERTAINTY_COUNT =
... / NOT_MEASURED

CORE_UNSTABLE_COUNT =
... / NOT_MEASURED

TIMING_STABLE_COUNT =
... / NOT_MEASURED

TIMING_BOUNDARY_UNCERTAINTY_COUNT =
... / NOT_MEASURED

TIMING_UNSTABLE_COUNT =
... / NOT_MEASURED

OHLCV_ANALYST_CALCULATION_ALGORITHM_MUTATION =
0 / NONZERO

INVENTED_TECHNICAL_INDICATOR =
0 / NONZERO

KNOWN_HARD_SAFETY_REGRESSION =
0 / NONZERO / NOT_MEASURED

PRIMARY_USER_ACTION_WORDING_OWNER =
RENDERER / OTHER / NOT_MEASURED

MONITORING_REGISTRATION_CALLS =
0 / NONZERO

BOOTSTRAP_PRODUCTION_MUTATION =
0 / NONZERO

MAIN_MERGE =
0 / NONZERO

PRODUCTION_DB_MUTATION =
0 / NONZERO

PRODUCTION_TELEGRAM_SEND =
0 / NONZERO

PRODUCTION_SCHEDULER_CHANGE =
0 / NONZERO

LIVE_STRUCTURED_AUTONOMY_ACTIVATION =
0 / NONZERO

LIVE_V2_CHANGE =
0 / NONZERO

NIGHT_FUTURES_CODE_MUTATION =
0 / NONZERO

OWNERSHIP_GENERALIZATION_VERDICT =
...

READINESS =
READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW /
NEEDS_ARCHITECTURE_WORK /
NOT_READY_TRANSPORT_BLOCKED /
NOT_READY
```

---

# 41. Stop conditions

STOP if:
- consumed latest-holdout16 is model-called again
- architecture hash drift appears
- source/sufficiency policy changes without triggering a new holdout
- model or reasoning effort changes
- prompt/schema semantics change while reusing the existing holdout
- batch split changes model context but is called "transport-only"
- transport canary fails and real holdout is nevertheless called
- more than one authoritative timeout owner remains
- an outer watchdog can preempt the authoritative model deadline
- a real holdout timeout is automatically retried
- output is partially promoted after timeout
- same-generation semantic hotfix is attempted
- source lock changes between FIRST/A/B/C
- production/registration/night-futures state is mutated

---

# 42. Completion response

Return:

```text
TRANSPORT ROOT CAUSE =
...

CONTINUATION GENERATION =
...

CONSUMED REGRESSION =
model calls = 0

ARCHITECTURE FREEZE =
hash drift = 0

SOURCE FREEZE =
drift = 0

TRANSPORT TOPOLOGY =
...

TIMEOUT OWNER =
...

BATCH SEMANTICS =
...

BATCH SPLIT EQUIVALENCE =
...

CANARIES =
smoke ...
directional core ...
representative payload ...
price timing ...

TRANSPORT VERDICT =
...

CURRENT HOLDOUT REUSE =
allowed 0/1
reason ...

SOURCE LOCK =
...

FIRST =
...

A =
...

B =
...

C =
...

CORE STABILITY =
...

TIMING STABILITY =
...

OWNERSHIP =
direction owner ...
price-only violations ...
price-only REDUCE ...

HARD SAFETY =
...

MONITORING BOOTSTRAP =
not activated
next handoff ...

PRODUCTION MUTATION =
0

NIGHT FUTURES =
unchanged

READINESS =
...

REPORT ZIP =
...

ZIP SHA256 =
...
```

---

# 43. Final principle

A zero-output 1,800-second timeout is not evidence that the investment architecture is wrong.

The next proof must first establish:

```text
model invocation can reliably start
→ emit
→ exit
→ parse
```

without changing:

```text
what the model sees
or
what the model is asked to decide
```

Only then resume the real ownership proof.

Transport repair is allowed.

Semantic repair is not.
