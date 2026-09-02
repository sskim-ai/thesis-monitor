# thesis-monitor — Night Futures Previous-KRX-Business-Day Contract Repair
## Focused follow-up to US run-51
## Make the US morning market digest use the immediately preceding valid KRX business date
## Preserve the already-passing Codex runtime, V2, daily-review, and technical repairs

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-09-02 KST`
- Target historical run: `RUN_ID=51`
- Target packet: `2026-09-02-us-run-51-39a4d4eec53e`
- Task class: `FOCUSED_NIGHT_FUTURES_SESSION_POLICY_REPAIR`
- Production Assist: preserve `OFF`
- Automated trading/order sizing: `0`
- Historical production resend: `0`
- Production delivery intent during replay/test: `0`
- Scheduler timing change: `0`
- Scheduler ownership change: `0`
- V2 decision-policy change: `0`
- Daily-review quality-threshold change: `0`
- Price Structure change: `0`
- Valuation change: `0`
- Technical-feature formula change: `0`

Primary completion bundle being corrected:

```text
20260902-us-run51-runtime-state-daily-review-night-futures-repair-bundle.zip
```

That bundle successfully repaired:
- Codex natural runtime-state parity
- run-51 V2 model/candidate/accepted path
- daily-review schema/provenance/message quality
- prior V2 path/provenance/technical regressions

But its night-futures contract does NOT implement the required user-facing behavior.

---

# 1. Current promoted state to preserve

The prior completion bundle reports:

```text
base before prior repair =
2a6bbc449d6802490560cb89d83e0d1fc3e88b24

prior implementation =
16fa1222136b300d900682904f8391ef5c4b482a

prior final main / operating =
ec616105f69aea3ba561ea9a6eea0835801d9a07
```

At task start:

```text
git fetch origin
resolve actual latest origin/main
resolve actual operating/runtime SHA
verify clean worktrees
verify ancestry contains the prior successful repairs
```

Use the latest safe main or a safe linear descendant.

Do NOT branch from a stale pre-repair SHA.

Hard:

```text
CODEX_RUNTIME_STATE_REPAIR_REGRESSION = 0
V2_NATURAL_PATH_REPAIR_REGRESSION = 0
DAILY_REVIEW_QUALITY_REPAIR_REGRESSION = 0
PRODUCT_IDENTIFIER_PROVENANCE_REGRESSION = 0
CPNG_HUT_TECHNICAL_RECOVERY_REGRESSION = 0
```

---

# 2. Normative user-facing contract

For the **US morning market digest**, the night-futures reference date is:

```text
the immediately preceding valid KRX business date
relative to the KST observation date
```

This contract is normative for this product path.

Example:

```text
observation =
2026-09-02 08:00 KST

latest valid XKRX session strictly before 2026-09-02 =
2026-09-01

expected night-futures reference date =
2026-09-01
```

Therefore a valid provider row keyed/labeled:

```text
night_bas_dd = 2026-09-01
```

is the current row for the 2026-09-02 morning US digest, subject to all independent:
- instrument identity
- contract/maturity
- data integrity
- finality
- change/value provenance

checks.

Required run-51 expectation:

```text
RUN51_EXPECTED_NIGHT_REFERENCE_DATE = 2026-09-01
```

---

# 3. What must be removed from the current contract

The promoted `night-futures-session-date-v2` documentation currently treats:

```text
BAS_DD = completed night-session end date
```

and therefore maps the 2026-09-02 08:xx observation to:

```text
expected BAS_DD = 2026-09-02
```

This is NOT the required behavior for the US morning digest.

Do not allow that semantic interpretation to override the explicit product contract.

Replace/refactor the digest-facing contract.

Hard:

```text
US_MORNING_EXPECTED_NIGHT_DATE_EQUALS_OBSERVATION_DATE = 0
```

---

# 4. Do not solve this with simple calendar subtraction

Forbidden generic rule:

```text
expected_date = observation_date - 1 calendar day
```

Required:

```text
expected_date =
latest valid XKRX session strictly earlier than observation_date_kst
```

This must handle:

```text
weekends
KRX holidays
consecutive KRX holidays
month boundaries
year boundaries
```

Gate:

```text
US_MORNING_NIGHT_REFERENCE_XKRX_CALENDAR = PASS
```

---

# 5. Do not hard-code the US regular-session date

Run-51 happens to have:

```text
US regular session date = 2026-09-01
expected KRX night reference date = 2026-09-01
```

Do NOT implement:

```text
night reference date = US regular-session date
```

The correct owner is the KRX calendar relative to the KST observation date.

Hard:

```text
US_MORNING_NIGHT_DATE_HARDCODED_TO_US_SESSION = 0
```

---

# 6. Separate raw provider date from product reference date

If internal provider documentation uses a different conceptual name for `BAS_DD`, retain the raw field exactly.

But the market-digest readiness layer must expose separate concepts:

```text
provider_raw_bas_dd
us_morning_expected_night_reference_date
night_reference_match
```

Do not overload one field with multiple semantics.

Preferred contract shape:

```json
{
  "observation_time_kst": "...",
  "expected_reference_date": "YYYY-MM-DD",
  "provider_raw_bas_dd": "YYYY-MM-DD",
  "reference_date_match": true,
  "instrument_valid": true,
  "contract_valid": true,
  "finality_valid": true,
  "value_provenance_valid": true,
  "readiness": "READY"
}
```

Use repository-native names if equivalent structures already exist.

---

# 7. Readiness rule for the US morning digest

A night-futures product is `READY` only if:

```text
provider_raw_bas_dd == expected_reference_date
AND
instrument identity valid
AND
contract/maturity valid
AND
row integrity valid
AND
row finality valid
AND
display/change provenance valid
```

For the date dimension:

```text
provider date == immediately preceding valid XKRX business date
→ CURRENT_DATE_MATCH
```

Do not classify it as stale merely because it is not the KST observation date.

---

# 8. Stale / future / unexpected date semantics

Given:

```text
expected_reference_date = D
```

classify:

```text
provider_raw_bas_dd == D
→ DATE_MATCH

provider_raw_bas_dd < D
→ STALE_PRIOR_REFERENCE

provider_raw_bas_dd > D
→ UNEXPECTED_FUTURE_REFERENCE
```

Do not silently accept a future/unexpected row.

Do not label a date-mapping defect as provider source limitation.

Required:

```text
SESSION_MAPPING_BUG_REPORTED_AS_SOURCE_LIMITATION = 0
```

---

# 9. Finality remains independent

The date repair must NOT weaken finality.

A matching previous-KRX-business-day row can only be used after the configured/proven night-session completion condition is satisfied.

Keep or improve the existing finality check.

But:

```text
finality
```

must not be inferred solely from:

```text
BAS_DD == observation_date
```

Required:

```text
NIGHT_FINALITY_DEPENDS_ON_OBSERVATION_DATE_MATCH = 0
```

If the existing `06:00 KST` boundary remains part of the validated finality contract:
- preserve it
- test it
- do not use it to shift the reference date forward

At 08:xx KST the run-51 row should pass finality if all other stored evidence supports it.

---

# 10. Run-51 immutable raw control

Use the stored run-51 raw response.

Reference raw SHA-256:

```text
39fff1232b66a8ff3fc464d35d21f300ba63595391df440cc2289d2f50fd6d28
```

Do not needlessly refetch the historical source to prove the classification.

Reference products:

```text
KOSPI200 night futures = A0169000
KOSDAQ150 night futures = A0669000
```

Reference provider date:

```text
2026-09-01
```

---

# 11. Required run-51 date replay

Under the corrected US morning contract:

```text
observation = 2026-09-02 08:xx KST
XKRX previous valid business date = 2026-09-01
provider_raw_bas_dd = 2026-09-01
```

Therefore:

```text
reference_date_match = true
```

Required:

```text
RUN51_EXPECTED_NIGHT_REFERENCE_DATE = 2026-09-01
RUN51_PROVIDER_NIGHT_BAS_DD = 2026-09-01
RUN51_NIGHT_DATE_MATCH_COUNT = 2
```

---

# 12. Run-51 readiness target

For each of the two stored products, independently verify:

```text
date match
instrument
contract/maturity
integrity
finality
change/value provenance
```

If the prior completion bundle contains no independent blocker beyond the wrong date mapping, target:

```text
RUN51_NIGHT_FUTURES_READY_COUNT = 2
```

If another independent blocker exists:
- identify it exactly
- prove it from stored evidence
- do not reuse the old date mismatch as the blocker

Hard:

```text
OLD_20260902_EXPECTATION_USED_AS_BLOCKER = 0
```

---

# 13. Change/value provenance

For each product record the exact provider values used by the market message.

Capture:

```text
instrument
contract
provider_raw_bas_dd
current/final reference value
comparison/base value
change
change_pct
source fields
rounding
fact_id
```

Do not invent or reverse-engineer from unrelated regular-session values if the provider already supplies the canonical values.

Required:

```text
RUN51_NIGHT_CHANGE_PROVENANCE = PASS
```

---

# 14. Market-packet integration

When a product is `READY`, the market packet must contain it as a structured fact.

Required fields should include:

```text
instrument identity
reference date
change/value
source
quality
finality
```

The market renderer must consume only packet-owned ready facts.

Hard:

```text
READY_NIGHT_FACT_NOT_IN_MARKET_PACKET = 0
```

---

# 15. Renderer acceptance

If run-51 has two ready facts, the frozen market replay must render two night-futures entries.

Required target:

```text
RUN51_NIGHT_FUTURES_RENDERED_COUNT = 2
READY_NIGHT_FUTURES_OMITTED_BY_RENDERER = 0
```

The exact section title/wording should follow the existing production message style.

Do not make the AI invent raw night-futures numbers.

---

# 16. Run-51 market replay

Replay the market message using immutable run-51 facts.

The only intended content delta versus the actually delivered run-51 market message is:

```text
addition of the validated night-futures section/facts
```

All non-night facts must remain unchanged.

Required:

```text
RUN51_NON_NIGHT_MARKET_NUMERIC_DIFF = 0
RUN51_NON_NIGHT_MARKET_SELECTION_DIFF = 0
```

---

# 17. Correct run-51 status

If both rows pass independent checks:

```text
RUN51_NIGHT_FUTURES_STATUS = PASS
```

The following result is NOT acceptable solely due to the old date contract:

```text
SOURCE_LIMITATION_SAFE
ready 0
rendered 0
```

Hard:

```text
RUN51_SOURCE_LIMITATION_DUE_ONLY_TO_OLD_DATE_MAPPING = 0
```

---

# 18. Calendar test matrix

Create unit/integration fixtures for at least:

```text
A. ordinary weekday
observation Wed morning
→ previous Tue XKRX session

B. Monday morning
→ previous Friday XKRX session
  unless Friday is not a valid session

C. KRX holiday
observation after a KRX holiday
→ most recent earlier valid XKRX session

D. consecutive Korean holidays
→ last valid session before the holiday block

E. month boundary

F. year boundary

G. US holiday / KRX open mismatch
→ still follows XKRX calendar

H. KRX holiday / US open mismatch
→ still follows XKRX calendar
```

Required:

```text
NIGHT_REFERENCE_CALENDAR_TESTS = PASS
```

---

# 19. Observation-time controls

This contract is specifically for the US morning digest.

Test at least:

```text
08:00 KST
08:20 KST
```

Both should use:

```text
latest valid XKRX business date strictly before the KST calendar date
```

Finality remains a separate gate.

If the same resolver is callable outside the US morning digest:
- either scope it explicitly
- or document its valid observation window

Do not accidentally change unrelated intraday/night-futures consumers.

Hard:

```text
UNRELATED_NIGHT_FUTURES_CONSUMER_SEMANTICS_CHANGED = 0
```

---

# 20. Architecture versioning

Replace/update the current digest-facing contract:

```text
night-futures-session-date-v2
```

with a new explicit version, e.g.:

```text
us-morning-night-reference-date-v3
```

or repository-native equivalent.

Architecture documentation must state plainly:

```text
For the US morning digest on KST date D,
the expected night-futures reference date is the latest valid
XKRX business date strictly before D.
```

Include the concrete example:

```text
2026-09-02 08:00 KST
→ 2026-09-01
```

---

# 21. Do not rewrite provider history

No provider row mutation.

No changing:

```text
2026-09-01
```

to:

```text
2026-09-02
```

in stored raw data.

Hard:

```text
RAW_PROVIDER_DATE_REWRITTEN = 0
SYNTHETIC_NIGHT_ROW_CREATED = 0
```

---

# 22. Preserve Codex runtime-state repair

The previous completion successfully introduced a scheduler-safe Codex runtime-state contract.

Regression requirements:

```text
scheduler-context Codex app-server probe PASS
local state preflight PASS
run-51 frozen V2 model call PASS
candidate generation 14/14
```

Do not modify that architecture unless a direct compile/test compatibility change is required.

Required:

```text
CODEX_RUNTIME_STATE_REPAIR_REGRESSION = 0
```

---

# 23. Preserve run-51 V2 result

Reference prior repaired replay:

```text
context = 14/14
model reached = PASS
candidate = 14/14
accepted = 14/14
explicit V2 = 14/14
```

The night-futures repair must not change stock-decision ownership or labels through unrelated code.

Required:

```text
RUN51_V2_CONTEXT_READY_COUNT = 14
RUN51_V2_MODEL_CALL_REACHED = PASS
RUN51_V2_CANDIDATE_GENERATED_COUNT = 14
RUN51_ACCEPTED_READY_COUNT = 14
RUN51_EXPLICIT_V2_DECISION_COUNT = 14
```

Do not force the historical BUY/HOLD/SELL distribution if the replay implementation legitimately regenerates nondeterministic prose/decision inputs; where frozen accepted artifacts exist, compare ownership and packet identity rather than retuning policy.

---

# 24. Preserve daily-review quality repair

Reference prior repaired result:

```text
schema PASS
numeric PASS
valuation PASS
heading mismatch 0
substantive repeat 0
identity mismatch 0
language errors 0
quality PASS
```

Required:

```text
DAILY_REVIEW_QUALITY_REPAIR_REGRESSION = 0
```

Do not weaken or bypass quality gates.

---

# 25. Preserve technical recovery

Do not alter:
- CPNG invalid historical row preservation
- feature-dependency-scoped safety
- HUT quote vs completed-close separation
- PARTIAL_SAFE semantics
- invalid numeric leakage protection

Required:

```text
CPNG_HUT_TECHNICAL_RECOVERY_REGRESSION = 0
TECHNICAL_PARTIAL_SAFE_FORCED_TO_FULL = 0
```

---

# 26. Preserve path and identifier provenance

Required:

```text
V2_SCHEMA_PATH_DUPLICATION = 0
V2_NATURAL_PATH_REGRESSION = PASS
PRODUCT_IDENTIFIER_PROVENANCE_REGRESSION = 0
```

---

# 27. Cross-market regression

Run non-production production-equivalent regression for the active/frozen cohorts.

Reference if unchanged:

```text
US = 14
KR = 8
```

The night-futures repair should not change stock messages except timestamps/fresh-data effects in non-frozen tests.

Use frozen fixtures for exact parity.

Required:

```text
US_PRODUCTION_EQUIVALENT_V2 = PASS
KR_PRODUCTION_EQUIVALENT_V2 = PASS
```

---

# 28. Dedicated test sink

If the existing repository release gate requires it, run the dedicated non-production sink.

Reference if cohort unchanged:

```text
US 14
KR 8
TOTAL 22
```

Hard:

```text
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST = 0
TEST_SINK_DUPLICATE = 0
```

Do not require a production send to prove the market replay.

---

# 29. Scheduler

Do not change:
- US primary time
- US backup time
- fallback/dispatcher time
- KR schedules
- packet ownership

Required:

```text
SCHEDULER_TIMING_DIFF = 0
SCHEDULER_OWNERSHIP_DIFF = 0
```

This focused repair should normally require no scheduler-runtime change.

If an unexpected scheduler environment diff appears, stop and classify rather than hiding it.

---

# 30. Focused root-cause report

The report must state the corrected root cause plainly:

```text
The prior implementation mapped the US morning night-futures expected date
to the observation/session-end date 2026-09-02.

The required product contract uses the immediately preceding valid XKRX
business date, which is 2026-09-01 for a 2026-09-02 morning observation.

The provider row was therefore incorrectly rejected by the prior readiness
date gate.
```

Do not restate the old `SOURCE_LIMITATION_SAFE` conclusion as the root cause.

---

# 31. Required tests

At minimum:

```text
focused night-reference resolver tests PASS
XKRX calendar matrix PASS
run-51 raw date replay PASS
run-51 readiness 2/2 or exact independent blocker
run-51 market renderer replay PASS
non-night market parity PASS
V2 runtime regression PASS
daily-review regression PASS
CPNG/HUT regression PASS
US production-equivalent PASS
KR production-equivalent PASS
full pytest PASS
Ruff PASS
git diff --check PASS
GitHub Actions Test/Lint PASS
```

---

# 32. Main merge gate

Merge only if:

```text
2026-09-02 08:xx maps to 2026-09-01
raw provider date remains unchanged
date match 2/2
no stale classification from the old 2026-09-02 expectation
independent finality/identity/value checks PASS
run-51 ready count = 2
run-51 rendered count = 2
non-night market values unchanged
Codex runtime repair preserved
V2 14/14 repaired replay preserved
daily-review quality preserved
technical recovery preserved
US/KR production-equivalent PASS
P0 = 0
material P1 = 0
```

If another independent blocker prevents 2/2:
- do NOT merge a partial semantic change while claiming the requested behavior is complete
- report the exact blocker
- set repair state `FAIL`

---

# 33. Deployment / natural-live guard

After safe merge/deploy:

Do NOT manually replay/send historical run-51 to production.

Wait for the next ordinary US morning market message.

Read-only natural-live proof must capture:

```text
observation date
expected previous XKRX business date
provider raw night date
ready count
rendered count
exact market payload
```

Success example:

```text
observation = 2026-09-03 08:xx KST
expected reference = latest valid XKRX session before 2026-09-03
provider date = same
ready = 2/2
rendered = 2/2
```

If source genuinely lacks the expected previous-business-day row:
`SOURCE_LIMITATION_SAFE` remains valid.

---

# 34. Required architecture/report files

Create/update:

```text
docs/architecture/US_MORNING_NIGHT_FUTURES_REFERENCE_DATE_CONTRACT.md
docs/architecture/MARKET_PACKET_TEMPORAL_ROLES.md
```

Create reports:

1. `docs/reports/20260902-night-reference-old-contract-root-cause.md`
2. `docs/reports/20260902-us-morning-night-reference-v3-contract.md`
3. `docs/reports/20260902-night-reference-xkrx-calendar-tests.md`
4. `docs/reports/20260902-run51-night-date-replay.md`
5. `docs/reports/20260902-run51-night-readiness-proof.md`
6. `docs/reports/20260902-run51-night-change-provenance.md`
7. `docs/reports/20260902-run51-market-night-renderer-replay.md`
8. `docs/reports/20260902-run51-non-night-market-parity.md`
9. `docs/reports/20260902-v2-daily-review-technical-regression.md`
10. `docs/reports/20260902-us-kr-production-equivalent-regression.md`
11. `docs/reports/20260902-night-reference-main-merge.md`
12. `docs/reports/20260902-night-reference-natural-live-guard.md`
13. `docs/reports/20260902-night-reference-artifact-index.md`

Machine-readable:

```text
docs/reports/20260902-night-reference-contract.json
docs/reports/20260902-run51-night-readiness.json
docs/reports/20260902-run51-market-night-replay.json
docs/reports/20260902-night-reference-repair-readiness.json
```

---

# 35. Required gates

Set exactly:

```text
BASE_SHA =
...

US_MORNING_NIGHT_REFERENCE_CONTRACT =
PREVIOUS_VALID_XKRX_BUSINESS_DATE / OTHER

RUN51_OBSERVATION_DATE_KST =
2026-09-02

RUN51_EXPECTED_NIGHT_REFERENCE_DATE =
2026-09-01 / OTHER

RUN51_PROVIDER_NIGHT_BAS_DD =
2026-09-01 / OTHER

US_MORNING_EXPECTED_NIGHT_DATE_EQUALS_OBSERVATION_DATE =
0 / NONZERO

US_MORNING_NIGHT_DATE_HARDCODED_TO_US_SESSION =
0 / NONZERO

US_MORNING_NIGHT_REFERENCE_XKRX_CALENDAR =
PASS / FAIL

NIGHT_REFERENCE_CALENDAR_TESTS =
PASS / FAIL

RUN51_NIGHT_DATE_MATCH_COUNT =
2 / OTHER

NIGHT_FINALITY_DEPENDS_ON_OBSERVATION_DATE_MATCH =
0 / NONZERO

RUN51_NIGHT_FINALITY =
PASS / PARTIAL / FAIL

RUN51_NIGHT_INSTRUMENT_CONTRACT_VALID =
PASS / FAIL

RUN51_NIGHT_CHANGE_PROVENANCE =
PASS / FAIL

OLD_20260902_EXPECTATION_USED_AS_BLOCKER =
0 / NONZERO

RAW_PROVIDER_DATE_REWRITTEN =
0 / NONZERO

SYNTHETIC_NIGHT_ROW_CREATED =
0 / NONZERO

RUN51_NIGHT_FUTURES_READY_COUNT =
2 / OTHER

READY_NIGHT_FACT_NOT_IN_MARKET_PACKET =
0 / NONZERO

RUN51_NIGHT_FUTURES_RENDERED_COUNT =
2 / OTHER

READY_NIGHT_FUTURES_OMITTED_BY_RENDERER =
0 / NONZERO

RUN51_NIGHT_FUTURES_STATUS =
PASS /
SOURCE_LIMITATION_SAFE /
VALIDATION_FAILURE /
FAIL

RUN51_SOURCE_LIMITATION_DUE_ONLY_TO_OLD_DATE_MAPPING =
0 / NONZERO

SESSION_MAPPING_BUG_REPORTED_AS_SOURCE_LIMITATION =
0 / NONZERO

RUN51_NON_NIGHT_MARKET_NUMERIC_DIFF =
0 / NONZERO

RUN51_NON_NIGHT_MARKET_SELECTION_DIFF =
0 / NONZERO

UNRELATED_NIGHT_FUTURES_CONSUMER_SEMANTICS_CHANGED =
0 / NONZERO

CODEX_RUNTIME_STATE_REPAIR_REGRESSION =
0 / NONZERO

V2_NATURAL_PATH_REPAIR_REGRESSION =
0 / NONZERO

DAILY_REVIEW_QUALITY_REPAIR_REGRESSION =
0 / NONZERO

PRODUCT_IDENTIFIER_PROVENANCE_REGRESSION =
0 / NONZERO

CPNG_HUT_TECHNICAL_RECOVERY_REGRESSION =
0 / NONZERO

TECHNICAL_PARTIAL_SAFE_FORCED_TO_FULL =
0 / NONZERO

RUN51_V2_CONTEXT_READY_COUNT =
14 / OTHER

RUN51_V2_MODEL_CALL_REACHED =
PASS / FAIL

RUN51_V2_CANDIDATE_GENERATED_COUNT =
14 / OTHER

RUN51_ACCEPTED_READY_COUNT =
14 / OTHER

RUN51_EXPLICIT_V2_DECISION_COUNT =
14 / OTHER

US_PRODUCTION_EQUIVALENT_V2 =
PASS / FAIL

KR_PRODUCTION_EQUIVALENT_V2 =
PASS / FAIL

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST =
0 / NONZERO

TEST_SINK_DUPLICATE =
0 / NONZERO

SCHEDULER_TIMING_DIFF =
0 / NONZERO

SCHEDULER_OWNERSHIP_DIFF =
0 / NONZERO

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

OPEN_P2 =
...

NIGHT_FUTURES_REFERENCE_REPAIR =
READY_FOR_MAIN /
FAIL
```

---

# 36. Completion response

Return:

```text
WORK_INSTRUCTION_COMMIT = ...
BASE_SHA = ...

OLD_CONTRACT_ROOT_CAUSE =
...

NEW_US_MORNING_NIGHT_REFERENCE_CONTRACT =
...

RUN51_OBSERVATION_DATE_KST = 2026-09-02
RUN51_EXPECTED_NIGHT_REFERENCE_DATE = 2026-09-01
RUN51_PROVIDER_NIGHT_BAS_DD = 2026-09-01
RUN51_NIGHT_DATE_MATCH_COUNT = 2

RUN51_NIGHT_FINALITY = ...
RUN51_NIGHT_INSTRUMENT_CONTRACT_VALID = ...
RUN51_NIGHT_CHANGE_PROVENANCE = ...

RUN51_NIGHT_FUTURES_READY_COUNT = ...
RUN51_NIGHT_FUTURES_RENDERED_COUNT = ...
RUN51_NIGHT_FUTURES_STATUS = ...

RUN51_MARKET_REPLAY =
...

RUN51_NON_NIGHT_MARKET_NUMERIC_DIFF = 0
RUN51_NON_NIGHT_MARKET_SELECTION_DIFF = 0

CODEX_RUNTIME_STATE_REPAIR_REGRESSION = 0
V2_NATURAL_PATH_REPAIR_REGRESSION = 0
DAILY_REVIEW_QUALITY_REPAIR_REGRESSION = 0
PRODUCT_IDENTIFIER_PROVENANCE_REGRESSION = 0
CPNG_HUT_TECHNICAL_RECOVERY_REGRESSION = 0

RUN51_V2_CONTEXT_READY_COUNT = 14
RUN51_V2_MODEL_CALL_REACHED = PASS
RUN51_V2_CANDIDATE_GENERATED_COUNT = 14
RUN51_ACCEPTED_READY_COUNT = 14
RUN51_EXPLICIT_V2_DECISION_COUNT = 14

US_PRODUCTION_EQUIVALENT_V2 = ...
KR_PRODUCTION_EQUIVALENT_V2 = ...

FULL_TESTS = ...
RUFF = ...
GIT_DIFF_CHECK = ...
ACTIONS = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
ORIGIN_MAIN = ...
OPERATING = ...
RUNTIME_CODE_SHA = ...

SCHEDULER_TIMING_DIFF = 0
SCHEDULER_OWNERSHIP_DIFF = 0

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
OPEN_P2 = ...

NIGHT_FUTURES_REFERENCE_REPAIR =
READY_FOR_MAIN /
FAIL

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_US_LIVE /
BOUNDED_REPAIR /
ROLLBACK_REVIEW

ZIP = ...
ZIP_SHA256 = ...
```

---

# 37. Mandatory completion ZIP

Create:

`20260902-night-futures-previous-krx-business-day-contract-repair-bundle.zip`

Include:
- exact master instruction
- all track instructions
- old-contract root-cause proof
- new reference-date contract
- XKRX calendar fixtures/results
- immutable run-51 raw-row proof
- run-51 date/readiness/finality/provenance proof
- run-51 market replay
- exact night-futures rendered section
- non-night market parity
- V2/daily-review/technical regression
- US/KR production-equivalent results
- CI/main/deployment reports
- machine-readable JSON
- artifact index

Exclude:
- secrets
- auth/session tokens
- Telegram recipient IDs
- account identifiers
- hidden chain-of-thought

Compute SHA-256.

---

# 38. Final principle

For this product path, the requirement is simple and explicit:

```text
US morning digest on KST date D
→ use the immediately preceding valid XKRX business date
  as the expected night-futures reference date
```

Concrete acceptance:

```text
2026-09-02 08:00 KST
→ expected = 2026-09-01
→ provider row 2026-09-01
→ date match
→ independent validation/finality/provenance
→ READY
→ rendered in the market message
```

Do not move the raw provider date forward.
Do not wait for a `2026-09-02` row merely because the observation date is `2026-09-02`.
Do not weaken finality or provenance.
Do not touch the already-working V2/runtime/daily-review/technical repairs.

This focused repair is complete only when the frozen run-51 market replay demonstrates the required behavior.
