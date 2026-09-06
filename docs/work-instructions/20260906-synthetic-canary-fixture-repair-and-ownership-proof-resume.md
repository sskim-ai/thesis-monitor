# thesis-monitor — Synthetic Canary Fixture Repair + Ownership Proof Resume
## Fix only the test-harness schema bug exposed before model invocation
## Keep transport topology, Directional Core / Price-Timing ownership architecture, sources, thresholds and model semantics frozen
## Revalidate architecture-scale transport with schema-valid fictional fixtures
## Preserve MODEL_CONTEXT_COUPLED batch shape
## If canaries pass, resume the untouched current holdout on the exact immutable source lock
## FIRST → A → B → C, no retry and no same-generation semantic repair
## No production mutation

---

# 0. Source result

Latest report bundle:

```text
thesis-monitor-20260906-model-transport-revalidation-ownership-proof-continuation-report.zip
```

SHA-256:

```text
c5b12a585ee56fd1d501658e04c1040b718dc731824198a91d63abfa61d7e9b1
```

Latest continuation generation:

```text
20260906-model-transport-continuation-20260906T110814Z-274deef7195c
```

Observed result:

```text
smoke transport = PASS

smoke:
gpt-5.6-sol / xhigh
first output ≈ 1.09s
exit ≈ 6.60s
structured output = PASS
orphan process = 0

Directional Core canary =
NOT INVOKED

reason:
DecisionEvidencePacket rejected
market="synthetic"

allowed schema:
market ∈ {"kr", "us"}

representative payload =
NOT_RUN

Price Timing canary =
NOT_RUN

current holdout FIRST/A/B/C =
NOT_RUN
```

Latest program stop:

```text
SYNTHETIC_CANARY_FIXTURE_SCHEMA_INVALID_BEFORE_DIRECTIONAL_CORE_INVOCATION
```

This is a test-harness fixture defect.

It is NOT evidence of:
- model transport failure
- ownership architecture failure
- source failure
- validator failure
- investment judgment instability

---

# 1. Work-instruction first

Create and commit this work instruction before implementation.

Record:

```text
base SHA
work-instruction commit SHA
branch
working tree state
```

No implementation before the work-instruction commit.

---

# 2. Scope of authorized repair

The only semantic repair authorized before the first model canary is:

```text
synthetic canary fixture construction
```

Specifically:

```text
market="synthetic"
```

must be removed because it violates the real `DecisionEvidencePacket` schema.

The production packet schema itself must NOT be changed to accept `"synthetic"`.

Required:

```text
PRODUCTION_MARKET_ENUM_MUTATION = 0
PRODUCTION_PACKET_SCHEMA_MUTATION = 0
```

---

# 3. Fictional identity and valid routing market are different concepts

Use:

```text
fictional company / security identity
+
valid routing market enum
```

Examples conceptually:

```text
fictional US fixture
market = "us"

fictional KR fixture
market = "kr"
```

Do not use a live issuer merely to make the fixture validate.

If the packet schema requires ticker/security identifiers:
- use test-only fictional/reserved identifiers accepted by the existing schema
- do not resolve them through external providers
- do not add production ticker exceptions
- keep `synthetic_fixture=true` or equivalent in a TEST-HARNESS SIDECAR if needed

Do not add `synthetic_fixture` to the production model schema solely for this test.

Required:

```text
REAL_ISSUER_USED_AS_CANARY = 0
TICKER_SPECIFIC_PRODUCTION_EXCEPTION = 0
```

---

# 4. Schema preflight before model calls

Before any canary model invocation, construct and validate:

```text
1 fictional US DecisionEvidencePacket
1 fictional KR DecisionEvidencePacket
1 fictional 4-subject US shared-context batch
1 fictional 4-subject KR shared-context batch
1 fictional US Price-Timing input
1 fictional KR Price-Timing input
```

Use the exact frozen Pydantic/schema objects used by production-equivalent ownership runs.

Required:

```text
SYNTHETIC_PACKET_SCHEMA_PREFLIGHT = PASS
```

If deterministic schema preflight fails:
- repair the test fixture only
- do not model-call
- do not touch production architecture
- freeze the fixture builder once preflight passes

This bounded fixture repair may iterate only BEFORE the first model canary call.

After the first model canary starts:

```text
CANARY_FIXTURE_MUTATION = 0
```

---

# 5. Architecture freeze

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

Required:

```text
OWNERSHIP_ARCHITECTURE_HASH_DRIFT = 0
DIRECTION_TIMING_POLICY_MUTATION = 0
INVESTMENT_DECISION_THRESHOLD_MUTATION = 0
```

Expected execution mode:

```text
TWO_STAGE_FENCED
```

---

# 6. Source/sufficiency freeze

Expected source hashes:

```text
{
  "coldstart_assembler": "ce6bd772ad105cd2425570607806ae1ec8afa109eca94fd4c6b2e08c4b306780",
  "company_profile": "fd4854c7781d672bf414ea43341e21ceb1879436c97defc5dff153037bdbbf5f",
  "financial_lineage": "1a9ba3fa0d867f4d0c1fb2c5e1b034d9adeebbe32b22b0d796571d468922ff91",
  "fundamental_enrichment": "c18627e3dd3a9a124b08583466de4361e1c5246be7ed6d2aadb306c770ed7538",
  "opendart_recovery": "c3190d3db087ca474a9cdf250570ba36c4fd82554439b60a6ac31354cfec19b0",
  "orchestrator": "2599d049400eab81fdf54336807bd37912496836504d1722c636cad70710afbe",
  "provider_sector_map": "e0c1ca2c52809484594b88e1dd904fd0a985c9db76d8524c21134ab8850d99bf",
  "provider_symbol_registry": "6cc8d7f38545a3abbe2fa882ef187ff7200d71a914d8b63e521a3917b6e226a6",
  "sec_financial_normalizer": "9fa2d3c12c75adf0872010a84ef749b8a4c6449d244ee4f35bb042ded7874136"
}
```

Required:

```text
FUNDAMENTAL_SOURCE_ENRICHMENT_DRIFT = 0
SOURCE_SUFFICIENCY_POLICY_DRIFT = 0
```

Do not refresh the current holdout.

---

# 7. Transport topology freeze

The previous continuation established:

```text
subprocess.Popen(start_new_session=True)
stdin writer thread
stdout reader thread
stderr reader thread
single monotonic watchdog
process-group cleanup
output-file parse
single receipt
```

Timeout owner:

```text
PYTHON_MONOTONIC_LIFECYCLE_WATCHDOG
```

Timeout owner count:

```text
1
```

Cleanup:

```text
SIGTERM process group
→ WAIT_ONCE
→ SIGKILL group if needed
```

Previous smoke proved:
- no orphan process
- no duplicate timeout receipt
- no early outer interrupt

This transport topology is frozen in this task.

Required:

```text
TRANSPORT_TOPOLOGY_MUTATION = 0
MODEL_TIMEOUT_OWNER_COUNT = 1
EARLY_OUTER_INTERRUPT = 0
ORPHAN_MODEL_PROCESS_COUNT = 0
SECRET_EXPOSURE_COUNT = 0
```

---

# 8. Do not change timeout in this task

The architecture-scale canary has never actually run.

Therefore:

```text
MODEL_TIMEOUT_SECONDS = 1800
TIMEOUT_INCREASE_THIS_TASK = 0
```

Do not infer that 1,800 seconds is too short from the previous fixture validation failure.

If an architecture-scale synthetic canary reaches the 1,800-second timeout:
- capture the transport receipt
- stop
- do not retry
- do not increase timeout in this task
- return a real transport classification

---

# 9. Batch semantics are frozen

Previously proven:

```text
BATCH_SEMANTICS = MODEL_CONTEXT_COUPLED

batch_size = 4

path:
batches(cohort)
→ one _core_prompt(contexts[4])
→ one model output
```

Therefore:

```text
BATCH_SPLIT_SEMANTIC_EQUIVALENCE = FAIL
BATCH_SPLIT_ADOPTED = 0
```

Do NOT change:
- 4 → 1
- 4 → 2
- shared context shape

merely to avoid timeout.

Required:

```text
REAL_RUN_BATCH_SIZE = 4
MODEL_CONTEXT_SHAPE_MUTATION = 0
```

---

# 10. Consumed prior regression remains forbidden

Do not model-call the consumed cohort:

```text
PLTR, V, MA, AMZN, XOM, DIS, NKE, MCD, 033920, 104480, 071320, 096240, 032860, 060570, 016600, 462520
```

Required:

```text
LATEST_HOLDOUT16_MODEL_CALLS = 0
LATEST_HOLDOUT16_RERUN_COUNT = 0
```

---

# 11. Synthetic canary sequence

Maximum:

```text
7 model invocations
```

Run only after Section 4 schema preflight passes and the fixture builder is frozen.

Sequence:

```text
C1 — process smoke
C2 — fictional US Directional Core, single-subject schema/runtime canary
C3 — fictional KR Directional Core, single-subject schema/runtime canary
C4 — fictional 4-US shared-context Directional Core
C5 — fictional 4-KR shared-context Directional Core
C6 — fictional US Price-Timing canary
C7 — fictional KR Price-Timing canary
```

The single-subject canaries do NOT prove real batch semantic equivalence.
C4/C5 are the architecture-scale transport proof.

---

# 12. Canary inputs

Directional Core synthetic evidence must use only allowed non-price domains.

Price-Timing synthetic evidence may include representative technical fields already supported by the frozen schema, such as where available:

```text
support/resistance
volume
RSI
MACD
Bollinger
moving averages
multi-timeframe technical state
risk/reward
supply/positioning
```

Synthetic fixture values are transport/schema test data only.

Do not represent them as real market facts.

Do not invent new production indicator fields.

Required:

```text
OHLCV_ANALYST_CALCULATION_ALGORITHM_MUTATION = 0
INVENTED_PRODUCTION_TECHNICAL_INDICATOR = 0
```

---

# 13. Canary transport receipts

Use the existing lifecycle receipt contract.

For each model call preserve:
- input hash
- prompt hash
- schema hash
- model / effort
- subject count
- batch shape
- spawn
- stdin complete
- first output
- exit
- parse
- byte counts
- timeout owner
- cleanup status

Do not log secrets.

---

# 14. Canary pass gate

Required:

```text
C1 = PASS
C2 = PASS
C3 = PASS
C4 = PASS
C5 = PASS
C6 = PASS
C7 = PASS
```

If one canary fails due:
- schema
- parse
- timeout
- process
- ownership validator

then:

```text
STOP_BEFORE_REAL_HOLDOUT = 1
```

No real holdout call.

No same-generation repair after a model canary has started.

---

# 15. Current untouched holdout

Current locked holdout:

```text
ORCL, UNH, KO, AVGO, 095570, 058860, 246960, 099520, 403870, 014790, 079810, 060980, 061970, 012030, 225190, 245620
```

Source lock:

```text
efe64d0942afa00c3b40131afc4de5fa411babc0680271d1571aaac69816050d
```

Facts:

```text
pre-lock directional model calls = 0
prior model output exists = 0
FIRST = NOT_RUN
A = NOT_RUN
B = NOT_RUN
C = NOT_RUN
```

It is NOT consumed by the failed synthetic canary.

---

# 16. Holdout reuse gate

After all synthetic canaries pass, verify:

```text
architecture hashes unchanged
source hashes unchanged
source lock unchanged
prompt semantics unchanged
schema semantics unchanged
model unchanged
reasoning effort unchanged
batch size/context unchanged
transport topology semantically neutral
```

Then:

```text
CURRENT_HOLDOUT_REUSE_ALLOWED = 1
```

Do not refresh the source lock.

If any semantic input changed:

```text
CURRENT_HOLDOUT_REUSE_ALLOWED = 0
```

Stop and request a separately authorized new holdout task.

Do not select a new holdout opportunistically in this task.

---

# 17. Natural live-workload coexistence guard

Before each heavy synthetic 4-subject canary and each real-model batch, check whether a natural scheduled KR/US live AI job is:
- currently using the same model transport/runtime resources, or
- imminently due in a way that creates credible contention.

If resource isolation is proven:

```text
LIVE_WORKLOAD_CONTENTION_RISK = 0
→ continue
```

If contention is plausible:

```text
pause shadow execution
wait for the authoritative natural live model/send lifecycle to finish
then resume
```

Do NOT:
- cancel natural live work
- change scheduler
- change production timeout
- compete deliberately with the live run

Record pause/resume timestamps.

---

# 18. FIRST

Only after:

```text
synthetic canaries = PASS
current holdout reuse gate = PASS
```

create a new FIRST run identity.

Use:

```text
gpt-5.6-sol
xhigh
batch size = 4
source lock = efe64d0942...
```

One attempt.

No automatic retry.

---

# 19. FIRST ownership gates

Required:

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

FINAL_DIRECTION_OWNER = DIRECTIONAL_CORE

validator false positive = 0
schema failure = 0
source-sufficiency escape = 0
```

If FIRST has any hard semantic/ownership failure:
- stop
- freeze evidence
- no same-generation repair

---

# 20. A/B/C

Proceed only if FIRST is clean.

Run:

```text
A
B
C
```

with:
- exact same holdout
- exact same source lock
- same model
- same effort
- same batch shape
- same transport policy
- same prompts/schemas
- same ownership architecture

No run sees another run.

No majority vote.

No retry on timeout.

---

# 21. Stability

Measure Directional Core separately from Price Timing.

Core:

```text
direction
BUY:SELL balance
HOLD lean
fundamental new-buyer stance
fundamental holder stance
```

Timing:

```text
technical state
timing modifier
entry mode
price review
holder price review
```

Report:

```text
CORE_STABLE
CORE_BOUNDARY_UNCERTAINTY
CORE_UNSTABLE

TIMING_STABLE
TIMING_BOUNDARY_UNCERTAINTY
TIMING_UNSTABLE
```

Do not tune threshold crossings.

---

# 22. Ownership proof

Required final invariants:

```text
FINAL_DIRECTION_OWNER = DIRECTIONAL_CORE
PRICE_ONLY_DIRECTIONAL_OWNERSHIP_VIOLATIONS = 0
PRICE_ONLY_HOLDER_REDUCE = 0
TIMING_STAGE_DIRECTION_MUTATION = 0
TIMING_STAGE_BALANCE_MUTATION = 0
TIMING_STAGE_HOLD_LEAN_MUTATION = 0
```

Do not require any historical ticker to receive a particular label.

---

# 23. Renderer / hard safety

After real outputs exist, verify:

```text
PRIMARY_USER_ACTION_WORDING_OWNER = RENDERER
AI_IMPERATIVE_PRIMARY_ACTION = 0
KNOWN_HARD_SAFETY_REGRESSION = 0
```

Re-run existing:
- numeric provenance
- accounting attribution
- ADR/security basis
- evidence fencing
- future checkpoint
- logical condition
- source sufficiency
- actionability contradiction
- issuer dedup

Do not weaken numeric/semantic validation to obtain a pass.

---

# 24. Monitoring bootstrap remains next task

Do NOT implement it here.

Maximum next handoff if ownership proof passes:

```text
user-approved Initial Analysis
→ monitor registration
→ stored investment-logic baseline
→ fundamental enrichment bootstrap
→ source sufficiency
→ monitoring-ready baseline
→ Daily Delta only after baseline
```

Bootstrap enrichment is baseline completion, not a Daily Delta.

---

# 25. Production remains unchanged

Required:

```text
MAIN_MERGE = 0
PRODUCTION_DB_MUTATION = 0
PRODUCTION_TELEGRAM_SEND = 0
PRODUCTION_SCHEDULER_CHANGE = 0
LIVE_STRUCTURED_AUTONOMY_ACTIVATION = 0
LIVE_V2_CHANGE = 0
MONITORING_REGISTRATION_CALLS = 0
BOOTSTRAP_PRODUCTION_MUTATION = 0
NIGHT_FUTURES_CODE_MUTATION = 0
```

---

# 26. Readiness

If canaries + FIRST/A/B/C + ownership + hard safety all pass:

```text
READINESS =
READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW
```

If architecture-scale canary transport fails:

```text
READINESS =
NOT_READY_TRANSPORT_BLOCKED
```

If real ownership semantics fail:

```text
READINESS =
NEEDS_ARCHITECTURE_WORK
```

---

# 27. Required reports

Create:

1. `docs/reports/20260906-canary-fixture-root-cause.md`
2. `docs/reports/20260906-canary-fixture-schema-contract.md`
3. `docs/reports/20260906-canary-schema-preflight.md`
4. `docs/reports/20260906-architecture-freeze-reverification.md`
5. `docs/reports/20260906-source-freeze-reverification.md`
6. `docs/reports/20260906-transport-freeze-reverification.md`
7. `docs/reports/20260906-consumed-regression-no-rerun.md`
8. `docs/reports/20260906-canary-smoke.md`
9. `docs/reports/20260906-canary-directional-us.md`
10. `docs/reports/20260906-canary-directional-kr.md`
11. `docs/reports/20260906-canary-shared-context-us4.md`
12. `docs/reports/20260906-canary-shared-context-kr4.md`
13. `docs/reports/20260906-canary-price-timing-us.md`
14. `docs/reports/20260906-canary-price-timing-kr.md`
15. `docs/reports/20260906-canary-verdict.md`
16. `docs/reports/20260906-current-holdout-reuse-gate.md`
17. `docs/reports/20260906-live-workload-coexistence-audit.md`
18. `docs/reports/20260906-resume-source-lock.md`
19. `docs/reports/20260906-resume-first.md`
20. `docs/reports/20260906-resume-run-a.md`
21. `docs/reports/20260906-resume-run-b.md`
22. `docs/reports/20260906-resume-run-c.md`
23. `docs/reports/20260906-resume-core-stability.md`
24. `docs/reports/20260906-resume-timing-stability.md`
25. `docs/reports/20260906-resume-dominance-ownership.md`
26. `docs/reports/20260906-resume-renderer-shadow-proof.md`
27. `docs/reports/20260906-resume-hard-safety-regression.md`
28. `docs/reports/20260906-monitoring-bootstrap-next-handoff.md`
29. `docs/reports/20260906-production-no-change.md`
30. `docs/reports/20260906-night-futures-no-change.md`
31. `docs/reports/20260906-program-completion.md`
32. `docs/reports/20260906-artifact-index.md`

Use actual completion date if execution crosses dates.

---

# 28. Required gates

```text
SOURCE_REPORT_BUNDLE_SHA256 =
c5b12a585ee56fd1d501658e04c1040b718dc731824198a91d63abfa61d7e9b1

WORK_INSTRUCTION_COMMIT =
...

PRODUCTION_MARKET_ENUM_MUTATION =
0 / NONZERO

PRODUCTION_PACKET_SCHEMA_MUTATION =
0 / NONZERO

REAL_ISSUER_USED_AS_CANARY =
0 / NONZERO

TICKER_SPECIFIC_PRODUCTION_EXCEPTION =
0 / NONZERO

SYNTHETIC_PACKET_SCHEMA_PREFLIGHT =
PASS / FAIL

CANARY_FIXTURE_MUTATION_AFTER_FIRST_MODEL_CALL =
0 / NONZERO

OWNERSHIP_ARCHITECTURE_HASH_DRIFT =
0 / NONZERO

FUNDAMENTAL_SOURCE_ENRICHMENT_DRIFT =
0 / NONZERO

SOURCE_SUFFICIENCY_POLICY_DRIFT =
0 / NONZERO

TRANSPORT_TOPOLOGY_MUTATION =
0 / NONZERO

MODEL =
gpt-5.6-sol / OTHER

REASONING_EFFORT =
xhigh / OTHER

MODEL_TIMEOUT_SECONDS =
1800 / OTHER

TIMEOUT_INCREASE_THIS_TASK =
0 / NONZERO

MODEL_TIMEOUT_OWNER_COUNT =
1 / OTHER

BATCH_SEMANTICS =
MODEL_CONTEXT_COUPLED / OTHER

REAL_RUN_BATCH_SIZE =
4 / OTHER

BATCH_SPLIT_ADOPTED =
0 / NONZERO

MODEL_CONTEXT_SHAPE_MUTATION =
0 / NONZERO

LATEST_HOLDOUT16_MODEL_CALLS =
0 / NONZERO

TRANSPORT_CANARY_MODEL_CALL_COUNT =
...

TRANSPORT_CANARY_STATUS =
PASS / FAIL

ARCHITECTURE_SCALE_TRANSPORT_STATUS =
PASS / FAIL / NOT_RUN

CURRENT_HOLDOUT_REUSE_ALLOWED =
0 / 1

CURRENT_HOLDOUT_SOURCE_LOCK =
efe64d0942afa00c3b40131afc4de5fa411babc0680271d1571aaac69816050d

LIVE_WORKLOAD_CONTENTION_RISK =
0 / 1 / NOT_OBSERVED

SHADOW_PAUSE_FOR_NATURAL_LIVE =
0 / NONZERO

REAL_HOLDOUT_TRANSPORT_RETRY_COUNT =
0 / NONZERO

RESUME_FIRST_VALIDATED =
... / NOT_RUN

RESUME_RUN_A_VALIDATED =
... / NOT_RUN

RESUME_RUN_B_VALIDATED =
... / NOT_RUN

RESUME_RUN_C_VALIDATED =
... / NOT_RUN

DIRECTIONAL_CORE_PRICE_TECHNICAL_REFS =
0 / NONZERO / NOT_MEASURED

DIRECTIONAL_CORE_SUPPLY_REFS =
0 / NONZERO / NOT_MEASURED

BUY_WITHOUT_NONPRICE_MATERIAL_ANCHOR =
0 / NONZERO / NOT_MEASURED

SELL_WITHOUT_NONPRICE_MATERIAL_ANCHOR =
0 / NONZERO / NOT_MEASURED

TIMING_STAGE_DIRECTION_MUTATION =
0 / NONZERO / NOT_MEASURED

TIMING_STAGE_BALANCE_MUTATION =
0 / NONZERO / NOT_MEASURED

TIMING_STAGE_HOLD_LEAN_MUTATION =
0 / NONZERO / NOT_MEASURED

PRICE_TIMING_NEW_BUYER_UPGRADE =
0 / NONZERO / NOT_MEASURED

PRICE_ONLY_HOLDER_REDUCE =
0 / NONZERO / NOT_MEASURED

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

KNOWN_HARD_SAFETY_REGRESSION =
0 / NONZERO / NOT_MEASURED

PRIMARY_USER_ACTION_WORDING_OWNER =
RENDERER / OTHER / NOT_MEASURED

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

READINESS =
READY_FOR_MONITORING_BOOTSTRAP_INTEGRATION_REVIEW /
NOT_READY_TRANSPORT_BLOCKED /
NEEDS_ARCHITECTURE_WORK /
NOT_READY
```

---

# 29. Stop conditions

STOP if:
- production packet schema is changed to allow `"synthetic"`
- a live issuer is used as a fictional canary shortcut
- architecture/source/threshold semantics drift
- transport topology changes before architecture-scale remeasurement
- timeout is increased
- batch size/context changes
- consumed latest-holdout16 is model-called
- a canary fails after model execution starts and a same-generation repair is proposed
- a real holdout timeout is retried
- source lock changes
- natural live scheduled work is disrupted
- production state is mutated

---

# 30. Completion response

Return:

```text
CANARY FIXTURE REPAIR =
root cause ...
production schema mutation = 0

SCHEMA PREFLIGHT =
US ...
KR ...
US4 ...
KR4 ...
timing US/KR ...

ARCHITECTURE / SOURCE / TRANSPORT FREEZE =
...

CANARIES =
C1 ...
C2 ...
C3 ...
C4 ...
C5 ...
C6 ...
C7 ...

ARCHITECTURE-SCALE TRANSPORT =
...

CURRENT HOLDOUT REUSE =
...

LIVE WORKLOAD COEXISTENCE =
...

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
...

HARD SAFETY =
...

MONITORING BOOTSTRAP =
next handoff only

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

# 31. Final principle

The previous continuation stopped before the Directional Core model was called because the fictional test fixture violated the real market enum.

Fix the fixture.

Do not fix the production schema.

Then measure the architecture-scale transport and, only if it passes, resume the untouched real holdout.
