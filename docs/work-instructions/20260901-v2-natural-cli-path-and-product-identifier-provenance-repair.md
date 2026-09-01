# thesis-monitor — V2 Natural CLI Path + Product-Identifier Provenance Repair
## Fix the production-only `--output-schema` path/cwd regression
## Fix generic numeric-provenance false positives for model/product identifiers such as KF-21 / FA-50
## Preserve the completed CPNG/HUT technical-recovery architecture
## Replay KR run-50 in test namespace, then verify KR8 + US14 production-equivalent paths

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-09-01 KST`
- Workstream: `V2_NATURAL_RUNTIME_PARITY_AND_IDENTIFIER_PROVENANCE_REPAIR`
- Task class: `MATERIAL_P1_BOUNDED_REPAIR`
- Automated trading: `0`
- Order sizing: `0`
- Production Assist: preserve `OFF`
- Scheduler changes: `0`
- Historical production replay/send: `0`
- Accepted-decision policy retuning: `0`
- Price Structure algorithm changes: `0`
- Valuation algorithm changes: `0`

Primary source bundles:

```text
20260901-kr-natural-live-failure-deep-readonly-root-cause-investigation-bundle.zip
20260901-cpng-hut-technical-recovery-finality-feature-scope-secondary-source-bundle.zip
```

---

# 1. Lineage

The failed 2026-09-01 KR natural run executed on:

```text
RUNTIME_CODE_SHA =
69d74fdf1600f812f0e542f0c3de5fcc544e5bc6
```

The later completed CPNG/HUT technical-recovery work promoted:

```text
FINAL_MAIN / ORIGIN_MAIN / OPERATING =
1aa10f04016cabede492c82686b6d671b4c27f55
```

The technical-recovery promotion happened after the failed KR delivery window.

Therefore:

```text
1aa10f... contains technical-recovery work that must be preserved.
```

At implementation start:

```text
git fetch origin
verify clean worktrees
resolve actual latest origin/main
resolve operating/runtime SHA
use 1aa10f... or a safe linear descendant as base
record exact ancestry
```

Do NOT branch from 69d74f.

Hard:

```text
REPAIR_BASE_OMITS_CPNG_HUT_TECHNICAL_RECOVERY = 0
```

---

# 2. Source-supported KR natural failure

Target run:

```text
RUN_ID = 50
KR_CANONICAL_SESSION_DATE = 2026-09-01
```

Primary packet:

```text
2026-09-01-kr-run-50-a601ddc0620a
```

Backup packet:

```text
2026-09-01-kr-run-50-44156fe0fa76
```

Source monitor:

```text
8 / 8 success
```

Packet-owned technical context:

```text
FULL = 8
PARTIAL_SAFE = 0
UNAVAILABLE = 0
INVALID = 0
```

V2 context preparation:

```text
8 / 8 ready
```

But:

```text
model call reached = NO
V2 candidate generated = 0 / 8
accepted ready = 0 / 8
explicit V2 decision = 0 / 8
```

Deterministic fallback safely delivered:

```text
market 1 + stock 8 = 9 / 9 exactly once
```

---

# 3. Material P1-A — production V2 CLI output-schema path regression

Observed live error:

```text
Failed to read output schema file
data/ai_review/claims/...decision-v2-schema.json:
No such file or directory
```

The real schema existed.

Natural production invocation did:

```text
schema =
data/ai_review/claims/<claim>.decision-v2-schema.json

cwd =
data/ai_review/claims
```

so the CLI effectively resolved:

```text
<repo>/data/ai_review/claims/
data/ai_review/claims/<schema>
```

The path prefix was duplicated.

The model call never started.

Classification:

```text
KR_PRIMARY_FAILURE_CLASS = CODE_REGRESSION
PASSING_TEST_VS_LIVE_FIRST_DIVERGENCE =
V2_CLI_OUTPUT_SCHEMA_PATH_RESOLUTION
KR_FAILURE_TRIGGER = NOT_DATA_TRIGGERED
```

---

# 4. Why the previous 22/22 test did not catch P1-A

The CPNG/HUT technical-recovery preflight used:

```text
absolute temp output_dir
absolute output.schema.json
absolute cwd
```

and therefore passed.

Natural production used:

```text
repository-relative claim paths
+
relative schema
+
cwd=schema.parent
```

The same helper was exercised under different path semantics.

This is a test/live parity gap.

Hard:

```text
PREFLIGHT_ONLY_ABSOLUTE_PATH_COVERAGE_CONSIDERED_SUFFICIENT = 0
```

---

# 5. Material P1-B — product/model identifiers parsed as numeric claims

The KR legacy/correction path produced false positives for `047810`.

Canonical product/model identifiers included:

```text
KF-21
FA-50
```

Validator errors incorrectly extracted:

```text
21
50
```

as unsupported numeric claims in multiple fields.

This is analogous in class, but not identical, to the previously repaired `Russell 2000` boundary bug.

The repair must be generic.

Hard:

```text
KF21_FA50_HARDCODED_ALLOWLIST = 0
```

---

# 6. Secondary validator controls

Two additional legacy-path rejections were observed:

```text
000660:
valuation_interpretation_evidence_invalid:
v_quality_earnings:quality_unknown:earnings

005930:
unsupported_risk_reward_comparison:
core_judgment.text
```

These are NOT the earliest V2 failure.

Treat them as negative controls first.

Do NOT weaken the validator to make them pass.

If existing correction logic can safely remove/rephrase unsupported interpretation, test that path separately.

Hard:

```text
GENUINE_000660_005930_GUARDS_WEAKENED = 0
```

---

# 7. Work split

```text
Track A
Production V2 CLI path normalization + natural/test parity

Track B
Generic canonical-identifier-aware numeric provenance

Track C
Frozen KR run-50 replay + legacy negative controls + exact failure closure

Track D
Preserve CPNG/HUT technical recovery + KR8/US14 test sink + merge + natural-live guard
```

---

# 8. Track A — normalize the invocation boundary, not individual callers

Locate the repository-native signed-in Codex invocation helper used by both:

```text
natural primary/backup V2
preflight/test V2
```

Preferred architectural fix:

```text
normalize all filesystem arguments at the subprocess boundary
```

including:

```text
cwd
prompt
output
log
schema
```

Do not patch only the KR caller.

Hard:

```text
KR_ONLY_SCHEMA_PATH_PATCH = 0
```

---

# 9. Absolute-path contract

Before subprocess execution, normalize:

```text
cwd_abs
prompt_abs
output_abs
log_abs
schema_abs
```

All file arguments passed to the CLI should be unambiguous absolute paths unless the repository has a stronger existing contract.

Required preconditions:

```text
cwd_abs exists and is directory
prompt_abs exists
schema_abs exists and is file
output parent exists
log parent exists
```

Fail before CLI if path preconditions do not hold.

Do not rely on subprocess cwd to reinterpret repository-relative file arguments.

---

# 10. Repository-relative claim paths

Natural claims may legitimately persist:

```text
final_output_path
```

as repository-relative values.

Do not require DB/archive migration merely to fix this bug.

The invocation layer must resolve them against the correct repository/worktree root.

Hard:

```text
CLAIM_PATH_STORAGE_FORCED_TO_ABSOLUTE = 0
```

unless an existing storage contract already requires it.

---

# 11. Path root ownership

Identify one canonical root:

```text
repository root / operating checkout root
```

Do not derive root from arbitrary current process cwd.

Required:

```text
relative persisted path
→ canonical repository root
→ absolute invocation path
```

Hard:

```text
PATH_RESOLUTION_DEPENDS_ON_LAUNCH_CWD = 0
```

---

# 12. Primary / backup parity

Both natural owners must call the exact same normalized invocation contract.

Hard:

```text
PRIMARY_BACKUP_SCHEMA_PATH_LOGIC_DIFF = 0
```

---

# 13. Path-preflight telemetry

Before model call, record safe diagnostics:

```text
cwd_is_absolute
schema_is_absolute
schema_exists
prompt_exists
output_parent_exists
```

Do not record sensitive filesystem data in user-facing messages.

Internal logs may retain sanitized relative artifact identities.

---

# 14. Path permutation tests

Mandatory unit/integration fixtures:

```text
absolute schema + absolute cwd
relative schema + relative cwd
relative schema + absolute cwd
relative prompt/output/log + relative claim path
```

All must resolve to the intended canonical files.

Negative control:

```text
schema truly missing
→ fail before model call
```

Gate:

```text
V2_CLI_PATH_PERMUTATION_TESTS = PASS
```

---

# 15. Exact natural-path regression fixture

Create a fixture matching run-50 natural shape:

```text
claim final_output_path =
data/ai_review/claims/<claim>.json

derived schema =
data/ai_review/claims/<claim>.decision-v2-schema.json

natural cwd =
data/ai_review/claims
```

After repair:

```text
effective schema path = exactly the real schema
duplicated prefix = 0
```

Gate:

```text
RUN50_NATURAL_PATH_FIXTURE = PASS
```

---

# 16. Test must use production `_paths()` / invocation logic

Do not prove this repair only through:

```text
v2_production_cutover_preflight.py
```

with a temp absolute `output_dir`.

At least one regression test must construct the same persisted claim/path object and call the same path-building + CLI invocation boundary as natural production.

Hard:

```text
NATURAL_PATH_NOT_COVERED_BY_TEST = 0
```

---

# 17. No model-call retry for deterministic path bugs

A nonexistent schema caused by local path construction is not a model transport failure.

Do not waste retry budget on identical malformed paths.

Required:

```text
local path precondition error
→ deterministic local failure class
```

after the repair tests should never hit it in healthy paths.

---

# 18. Track B — canonical identifier span model

Numeric provenance must distinguish:

```text
numeric factual claims
```

from:

```text
canonical model/product/index/security identifiers containing digits
```

Examples:

```text
KF-21
FA-50
F-35
B-21
A320neo
S&P500
KOSPI200
KOSDAQ150
Russell 2000
```

Do not treat this list as an allowlist.

Use generic identifier provenance.

---

# 19. Identifier eligibility

Digits may be excluded from numeric-claim extraction only when the full identifier span is safely owned by one of:

```text
canonical evidence text
registered structured label
instrument/index registry
product/model identifier fact
security identifier fact
```

The full visible token/span must match canonical provenance.

An invented identifier must not become safe merely because it looks alphanumeric.

Hard:

```text
UNPROVEN_IDENTIFIER_DIGITS_AUTO_EXEMPT = 0
```

---

# 20. Exact-span behavior

For:

```text
KF-21
```

the validator should classify the whole token as:

```text
canonical_identifier
```

and not emit standalone numeric claim `21`.

Likewise:

```text
FA-50
```

must not emit `50`.

But:

```text
KF-21 10대
```

must still validate `10`.

And:

```text
FA-50 계약가치 50억원
```

must still validate the factual `50억원` independently.

Hard:

```text
IDENTIFIER_MASK_HIDES_ADJACENT_NUMERIC_CLAIM = 0
```

---

# 21. Range / subtraction negative controls

Do not interpret:

```text
21-50
```

as a product identifier unless the complete canonical identifier contains required alphabetic/structural context and exact provenance.

Plain ranges remain numeric.

---

# 22. Dates remain dates

Do not break existing date handling:

```text
2026-09-01
2023-06-05
```

They must remain under the date/token contract, not product identifiers.

---

# 23. Existing structural-label controls

Preserve previous repaired behavior for:

```text
Russell 2000
S&P500
KOSPI 200
KOSDAQ 150
미국 10년물
```

No regression.

---

# 24. Identifier diagnostics

When digits are suppressed as identifier components, retain diagnostic metadata:

```text
full span
identifier type
canonical source
fact/ref ID
character span
```

No hidden chain-of-thought.

---

# 25. Unsupported identifier control

If the AI invents an unsupported model name:

```text
ZZ-999
```

with no canonical evidence/reference:

it must NOT gain safety through the identifier recognizer.

The existing fact/semantic validator should reject it, or the identifier layer should mark it unsupported.

Gate:

```text
UNSUPPORTED_PRODUCT_IDENTIFIER_REJECTED = PASS
```

---

# 26. 047810 exact replay controls

Use the run-50 legacy candidate/correction artifacts.

Require zero phantom numeric errors for canonical:

```text
KF-21
FA-50
```

across all previously affected fields.

Gate:

```text
047810_PRODUCT_IDENTIFIER_PHANTOM_NUMERIC = 0
```

---

# 27. Real-number controls near identifiers

Mandatory:

```text
KF-21 21대
FA-50 50대
KF-21 수출 5조원
FA-50 마진 12%
```

Identifier digits are not numeric claims.

The trailing factual numbers are.

Gate:

```text
PRODUCT_IDENTIFIER_ADJACENT_NUMERIC_PROVENANCE = PASS
```

---

# 28. No broad hyphen-number exemption

Strings such as:

```text
-21%
21-50
$-50
```

must remain under numeric parsing rules.

Hard:

```text
GENERIC_HYPHEN_NUMBER_NUMERIC_VALIDATION_DISABLED = 0
```

---

# 29. Track C — frozen run-50 V2 replay

Create immutable replay copies of the natural run-50 packets.

Do not mutate production packet/archive records.

Use:

```text
primary packet
2026-09-01-kr-run-50-a601ddc0620a

backup packet
2026-09-01-kr-run-50-44156fe0fa76
```

---

# 30. Replay the production path, not only preflight

The replay must use:

```text
persisted claim path semantics
accepted_v2_production_paths()
natural production invocation helper
same batch-size logic
same schema generation
same V2 candidate validation
same adjudication
same accepted-plan ownership
```

Do not substitute the temp preflight path as proof.

---

# 31. Run-50 V2 target

With the path bug repaired:

```text
context ready = 8
model invocation started = YES
candidate generated = 8 / 8
```

unless a new independently proven subject-level V2 error appears.

Then require normal:

```text
candidate → adjudication if needed → accepted plan
```

Do not force decision labels/distribution.

Gate:

```text
RUN50_V2_CANDIDATE_GENERATED_COUNT = 8 / OTHER
```

---

# 32. Candidate/accepted ownership

Preserve sole downstream authority:

```text
accepted_decision_plan
```

Hard:

```text
ACCEPTED_DECISION_OWNERSHIP_REGRESSION = 0
```

---

# 33. 000660 genuine guard control

Replay the observed legacy/correction valuation-quality issue.

Determine whether:

```text
candidate claim genuinely relied on quality_unknown earnings evidence
```

If yes:

```text
validator must continue rejecting the unsupported interpretation
```

Allowed repair, only if correction path already supports it:

```text
remove unsafe interpretation
or
retarget to a valid evidence fact
```

Do not relabel unknown evidence as valid.

Gate:

```text
000660_VALUATION_QUALITY_GUARD = PASS
```

---

# 34. 005930 genuine RR guard control

Replay:

```text
unsupported_risk_reward_comparison
```

If the comparison lacks a fully supported Entry/Target/Stop basis, validator rejection is correct.

Do not create target/stop values.

Allowed correction:

```text
remove unsupported R/R statement
or
rewrite without unsupported comparison
```

Gate:

```text
005930_RISK_REWARD_GUARD = PASS
```

---

# 35. Genuine guards must not block healthy V2 ownership

The legacy/free-analyst candidate path is separate from packet-bound V2 accepted decisions.

Once V2 accepted plans exist:

```text
legacy candidate rejection must not suppress a valid accepted V2 block
```

unless selector contract explicitly requires it and that requirement is justified.

Audit selector ordering.

Hard:

```text
LEGACY_VALIDATION_REJECTION_SUPPRESSES_VALID_V2_ACCEPTED = 0
```

---

# 36. Final renderer control

For every accepted-ready KR subject in replay:

```text
🧠 AI 분석 판단: BUY / HOLD / SELL
```

must be visible in the production-equivalent rendered stock message.

Gate:

```text
RUN50_EXPLICIT_V2_DECISION_COUNT = ...
```

---

# 37. No historical production send

All run-50 replay work:

```text
test/replay namespace only
```

Hard:

```text
RUN50_PRODUCTION_RESEND = 0
RUN50_PRODUCTION_DELIVERY_INTENT = 0
```

---

# 38. Track D — preserve CPNG/HUT technical recovery

The current main includes a completed generic technical-recovery architecture.

Must preserve:

```text
quote vs completed-candle separation
completed-bar finality
feature-dependency-scoped validity
recursive-indicator dependency safety
approved-secondary-source boundary
packet-owned technical context
```

Hard:

```text
CPNG_HUT_TECHNICAL_RECOVERY_REGRESSION = 0
```

---

# 39. CPNG control after this repair

Reference current technical-recovery result:

```text
aggregate = PARTIAL_SAFE
safe features = 170
blocked features = 46
bad historical date = 2023-06-05
secondary source = none approved
```

Current live data may legitimately change counts.

Regression criteria are contract-based, not hardcoded counts:

```text
bad row preserved
no synthetic OHLC
safe feature scope correct
blocked recursive dependencies remain blocked
invalid numeric does not enter V2
```

---

# 40. HUT control after this repair

Reference:

```text
aggregate = PARTIAL_SAFE
current D/W newest row finality unavailable
monthly safe partial context
current quote does not own completed close
secondary source = none approved
```

Preserve automatic future recovery when a valid FINAL row appears.

---

# 41. KR technical regression

All current KR monitored subjects must use the same packet-owned technical contract.

Reference expected current cohort:

```text
8
```

Previous technical-recovery regression:

```text
FULL 8 / 8
```

Current run may differ only with evidence.

Gate:

```text
KR_TECHNICAL_CONTEXT_REGRESSION = PASS
```

---

# 42. US technical regression

Current US/foreign monitored subjects:

reference count:

```text
14
```

Ensure this CLI/provenance repair does not change:

```text
technical state
feature numerics
Price Structure numerics
valuation numerics
```

except for fresh market data in a current capture.

Use frozen fixtures for exact parity.

---

# 43. Production-equivalent KR path test

This is mandatory.

Create a non-production claim whose path is repository-relative exactly like natural production.

Run:

```text
source/evidence fixture
→ natural `_paths()`
→ schema write
→ normalized CLI helper
→ model
→ candidate
→ validation
→ accepted
→ renderer
```

for KR8.

Do not use only the preflight script.

Gate:

```text
KR_PRODUCTION_EQUIVALENT_PATH = PASS
```

---

# 44. Production-equivalent US path test

Repeat the same natural path contract for US14.

This catches market-independent schema bugs before the next natural US cycle.

Gate:

```text
US_PRODUCTION_EQUIVALENT_PATH = PASS
```

---

# 45. Dedicated test sink

After production-equivalent path tests pass:

reference frozen monitored counts:

```text
US = 14
KR = 8
TOTAL = 22
```

If actual active frozen cohort legitimately changes, record actual counts.

Require exact payload.

Hard:

```text
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST = 0
```

---

# 46. Rate-limit continuation

The previous 22-message test sink required:

```text
20 initial
+
2 continuation after HTTP 429
```

Preserve exact remaining-subset resume semantics.

Do not resend already acknowledged test messages.

Gate:

```text
TEST_SINK_RATE_LIMIT_RESUME_REGRESSION = 0
```

---

# 47. Path regression across test sink/replay

Test sink success does not count unless the decision artifacts were generated using:

```text
natural production-equivalent path semantics
```

Hard:

```text
TEST_SINK_BYPASSES_REPAIRED_NATURAL_PATH = 0
```

---

# 48. Scheduler unchanged

Do not modify:

```text
KR primary/backup/fallback schedules
US primary/backup/fallback schedules
KRX telemetry schedules
onboarding reconciler schedules
```

Hard:

```text
SCHEDULER_DIFF = 0
```

---

# 49. Services

Do not restart OHLCV service unless required for unrelated health failure.

This repair is not an OHLCV transport repair.

If runtime deployment requires thesis-monitor API restart, use the repository-standard bounded restart after main promotion.

Record health.

---

# 50. Full validation

Require:

```text
focused V2 path tests PASS
identifier provenance tests PASS
run-50 frozen replay PASS
KR production-equivalent path PASS
US production-equivalent path PASS
CPNG/HUT technical regression PASS
full pytest PASS
Ruff PASS
git diff --check PASS
GitHub Actions Test/Lint PASS
```

---

# 51. Main merge gate

Merge only if:

```text
P1-A schema path root cause reproduced
schema path repair generic
natural path test exists
primary/backup parity PASS
P1-B identifier false positive eliminated
real numeric claims near identifiers still validated
unsupported identifier control PASS
000660 genuine guard preserved
005930 genuine guard preserved
run-50 candidate generation 8/8
accepted ownership unchanged
KR production-equivalent path PASS
US production-equivalent path PASS
technical recovery preserved
test sink exact
P0 = 0
material P1 = 0
```

---

# 52. Natural-live proof

After main/operating deployment:

do NOT replay production.

Observe the next ordinary natural cycles read-only.

If the next eligible market is US:

require:

```text
14 cutoff-eligible subjects if unchanged
model call reached
candidate generated
accepted-ready
explicit V2 block
fallback count
exactly-once
```

Then separately observe the next KR natural cycle.

Test success is not natural LIVE_PASS.

---

# 53. Required architecture docs

Create/update:

```text
docs/architecture/V2_CODEX_CLI_PATH_CONTRACT.md
docs/architecture/V2_TEST_LIVE_RUNTIME_PARITY.md
docs/architecture/NUMERIC_PROVENANCE_VALIDATION.md
docs/architecture/CANONICAL_IDENTIFIER_NUMERIC_BOUNDARIES.md
docs/architecture/DECISION_ENGINE_V2_PRODUCTION_RUNTIME.md
```

---

# 54. Required reports

Create at minimum:

1. `docs/reports/20260901-v2-cli-path-root-cause.md`
2. `docs/reports/20260901-v2-cli-path-contract.md`
3. `docs/reports/20260901-v2-natural-path-permutation-controls.md`
4. `docs/reports/20260901-run50-production-path-replay.md`
5. `docs/reports/20260901-product-identifier-provenance-root-cause.md`
6. `docs/reports/20260901-product-identifier-provenance-controls.md`
7. `docs/reports/20260901-047810-kf21-fa50-control.md`
8. `docs/reports/20260901-000660-valuation-quality-negative-control.md`
9. `docs/reports/20260901-005930-risk-reward-negative-control.md`
10. `docs/reports/20260901-legacy-vs-v2-selector-ownership.md`
11. `docs/reports/20260901-cpng-hut-technical-recovery-regression.md`
12. `docs/reports/20260901-kr-production-equivalent-v2-path.md`
13. `docs/reports/20260901-us-production-equivalent-v2-path.md`
14. `docs/reports/20260901-v2-runtime-test-sink.md`
15. `docs/reports/20260901-v2-runtime-message-quality.md`
16. `docs/reports/20260901-v2-runtime-main-merge.md`
17. `docs/reports/20260901-v2-runtime-natural-live-guard.md`
18. `docs/reports/20260901-v2-runtime-repair-readiness.md`
19. `docs/reports/20260901-v2-runtime-artifact-index.md`

Machine-readable:

```text
docs/reports/20260901-v2-cli-path-controls.json
docs/reports/20260901-product-identifier-controls.json
docs/reports/20260901-run50-replay.json
docs/reports/20260901-v2-runtime-repair-readiness.json
```

---

# 55. Required gates

Set exactly:

```text
REPAIR_BASE_OMITS_CPNG_HUT_TECHNICAL_RECOVERY =
0 / NONZERO

PREFLIGHT_ONLY_ABSOLUTE_PATH_COVERAGE_CONSIDERED_SUFFICIENT =
0 / NONZERO

KR_ONLY_SCHEMA_PATH_PATCH =
0 / NONZERO

CLAIM_PATH_STORAGE_FORCED_TO_ABSOLUTE =
0 / NONZERO

PATH_RESOLUTION_DEPENDS_ON_LAUNCH_CWD =
0 / NONZERO

PRIMARY_BACKUP_SCHEMA_PATH_LOGIC_DIFF =
0 / NONZERO

V2_CLI_PATH_PERMUTATION_TESTS =
PASS / FAIL

RUN50_NATURAL_PATH_FIXTURE =
PASS / FAIL

NATURAL_PATH_NOT_COVERED_BY_TEST =
0 / NONZERO

V2_EFFECTIVE_SCHEMA_PATH_DUPLICATION =
0 / NONZERO

V2_SCHEMA_PRECHECK =
PASS / FAIL

KF21_FA50_HARDCODED_ALLOWLIST =
0 / NONZERO

UNPROVEN_IDENTIFIER_DIGITS_AUTO_EXEMPT =
0 / NONZERO

IDENTIFIER_MASK_HIDES_ADJACENT_NUMERIC_CLAIM =
0 / NONZERO

GENERIC_HYPHEN_NUMBER_NUMERIC_VALIDATION_DISABLED =
0 / NONZERO

UNSUPPORTED_PRODUCT_IDENTIFIER_REJECTED =
PASS / FAIL

047810_PRODUCT_IDENTIFIER_PHANTOM_NUMERIC =
0 / NONZERO

PRODUCT_IDENTIFIER_ADJACENT_NUMERIC_PROVENANCE =
PASS / FAIL

000660_VALUATION_QUALITY_GUARD =
PASS / FAIL

005930_RISK_REWARD_GUARD =
PASS / FAIL

GENUINE_000660_005930_GUARDS_WEAKENED =
0 / NONZERO

RUN50_V2_CONTEXT_READY_COUNT =
8 / OTHER

RUN50_V2_MODEL_CALL_REACHED =
PASS / FAIL

RUN50_V2_CANDIDATE_GENERATED_COUNT =
8 / OTHER

RUN50_ACCEPTED_READY_COUNT =
...

RUN50_EXPLICIT_V2_DECISION_COUNT =
...

LEGACY_VALIDATION_REJECTION_SUPPRESSES_VALID_V2_ACCEPTED =
0 / NONZERO

ACCEPTED_DECISION_OWNERSHIP_REGRESSION =
0 / NONZERO

RUN50_PRODUCTION_RESEND =
0 / NONZERO

RUN50_PRODUCTION_DELIVERY_INTENT =
0 / NONZERO

CPNG_HUT_TECHNICAL_RECOVERY_REGRESSION =
0 / NONZERO

KR_TECHNICAL_CONTEXT_REGRESSION =
PASS / FAIL

KR_PRODUCTION_EQUIVALENT_PATH =
PASS / FAIL

US_PRODUCTION_EQUIVALENT_PATH =
PASS / FAIL

TEST_SINK_US_COUNT =
...

TEST_SINK_KR_COUNT =
...

TEST_SINK_TOTAL_EXACT =
PASS / FAIL

TEST_SINK_RATE_LIMIT_RESUME_REGRESSION =
0 / NONZERO

TEST_SINK_BYPASSES_REPAIRED_NATURAL_PATH =
0 / NONZERO

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST =
0 / NONZERO

PRICE_STRUCTURE_NUMERIC_DIFF =
0 / NONZERO

VALUATION_NUMERIC_DIFF =
0 / NONZERO

DECISION_POLICY_RETUNED =
0 / NONZERO

SCHEDULER_DIFF =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

V2_NATURAL_RUNTIME_REPAIR =
READY_FOR_MAIN /
FAIL
```

---

# 56. Completion response

Return:

```text
MASTER_INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_IMPLEMENTATION = ...
TRACK_B_IMPLEMENTATION = ...
TRACK_C_RESULT = ...
TRACK_D_RESULT = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
ORIGIN_MAIN = ...
OPERATING = ...
RUNTIME_CODE_SHA = ...

V2_CLI_PATH_ROOT_CAUSE =
...

OLD_EFFECTIVE_SCHEMA_PATH =
...

NEW_SCHEMA_PATH_CONTRACT =
...

V2_CLI_PATH_PERMUTATION_TESTS = ...
RUN50_NATURAL_PATH_FIXTURE = ...
V2_EFFECTIVE_SCHEMA_PATH_DUPLICATION = 0

PRODUCT_IDENTIFIER_ROOT_CAUSE =
...

047810_PRODUCT_IDENTIFIER_PHANTOM_NUMERIC = 0
PRODUCT_IDENTIFIER_ADJACENT_NUMERIC_PROVENANCE = PASS
UNSUPPORTED_PRODUCT_IDENTIFIER_REJECTED = PASS

000660_VALUATION_QUALITY_GUARD = ...
005930_RISK_REWARD_GUARD = ...
GENUINE_000660_005930_GUARDS_WEAKENED = 0

RUN50_V2_CONTEXT_READY_COUNT = 8
RUN50_V2_MODEL_CALL_REACHED = ...
RUN50_V2_CANDIDATE_GENERATED_COUNT = ...
RUN50_ACCEPTED_READY_COUNT = ...
RUN50_EXPLICIT_V2_DECISION_COUNT = ...

LEGACY_VALIDATION_REJECTION_SUPPRESSES_VALID_V2_ACCEPTED = 0
ACCEPTED_DECISION_OWNERSHIP_REGRESSION = 0

CPNG_HUT_TECHNICAL_RECOVERY_REGRESSION = 0
KR_TECHNICAL_CONTEXT_REGRESSION = ...

KR_PRODUCTION_EQUIVALENT_PATH = ...
US_PRODUCTION_EQUIVALENT_PATH = ...

TEST_SINK_US_COUNT = ...
TEST_SINK_KR_COUNT = ...
TEST_SINK_TOTAL_EXACT = ...
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST = 0

PRICE_STRUCTURE_NUMERIC_DIFF = 0
VALUATION_NUMERIC_DIFF = 0
DECISION_POLICY_RETUNED = 0
SCHEDULER_DIFF = 0

RUN50_PRODUCTION_RESEND = 0
RUN50_PRODUCTION_DELIVERY_INTENT = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

V2_NATURAL_RUNTIME_REPAIR =
READY_FOR_MAIN /
FAIL

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_US_LIVE /
WAIT_FOR_NEXT_NATURAL_KR_LIVE /
BOUNDED_REPAIR /
ROLLBACK_REVIEW

ZIP = ...
ZIP_SHA256 = ...
```

---

# 57. Mandatory completion ZIP

Create:

`20260901-v2-natural-cli-path-and-product-identifier-provenance-repair-bundle.zip`

Include:

```text
exact work instruction
all track instructions
path root-cause proof
path permutation tests
exact run-50 natural-path replay
identifier tokenizer/provenance proof
047810 controls
000660 / 005930 negative controls
selector ownership proof
CPNG/HUT technical regression
KR/US production-equivalent path tests
test-sink receipt
message quality
CI
main merge
natural-live guard
machine-readable JSON
artifact index
```

Exclude:

```text
secrets
Telegram recipient IDs
tokens
auth headers
account identifiers
hidden chain-of-thought
```

Compute SHA-256.

---

# 58. Final principle

The prior technical repair is valid and must remain.

Today’s KR failure was a separate production-path parity defect:

```text
test path used absolute schema
natural path used relative schema + cwd
```

Fix the invocation boundary so both paths are equivalent.

Then fix numeric provenance so:

```text
canonical identifier digits are identifiers,
real adjacent numbers remain real numeric claims.
```

Do not weaken genuine valuation or risk/reward guards.

The target is:

```text
same runtime path in test and natural production
+
generic identifier-safe provenance
+
preserved technical recovery
+
accepted V2 ownership
+
no manual production replay.
```
