# thesis-monitor — 2026-09-02 US Run-51 Repair
## Natural Codex Runtime-State Parity + Daily-Review Quality Convergence + Night-Futures Session Mapping
## Preserve all previously validated V2/technical repairs

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-09-02 KST`
- Target failed natural run: `RUN_ID=51`
- Target packet: `2026-09-02-us-run-51-39a4d4eec53e`
- Canonical US regular session: `2026-09-01`
- Workstream: `US_RUN51_THREE_P1_REPAIR`
- Task class: `BOUNDED_PRODUCTION_PARITY + QUALITY + SESSION_MAPPING_REPAIR`
- Automated trading/order sizing: `0`
- Production Assist: preserve `OFF`
- Historical production resend: `0`
- Historical production delivery intent: `0`
- Accepted-decision policy retuning: `0`
- Price Structure algorithm change: `0`
- Valuation algorithm change: `0`
- Technical feature formula change: `0` unless an independently proven regression requires it
- Scheduler timing change: `0`
- Scheduler ownership semantics change: `0`

Primary evidence bundle:

```text
20260902-us-morning-natural-live-data-extraction-and-proof-bundle.zip
SHA-256 =
47cb6f0914065726d2315a99b4b10dd3bde8594eebe3f4b50347d13b3861a7eb
```

User-supplied external observation to verify against provider semantics:

```text
Kiwoom UI shows the overnight/night-futures session observed on
2026-09-02 KST morning with base date 2026-09-01.
```

Do not silently assume that observation is sufficient by itself.
Verify the provider field/session semantics and historical examples before changing the readiness contract.

---

# 1. Source-supported run-51 facts

The evidence bundle establishes:

```text
SOURCE_MONITOR = 14/14 success

US_TECHNICAL =
FULL 0
PARTIAL_SAFE 14
UNAVAILABLE 0
INVALID 0

US_V2_CONTEXT_READY = 14/14

schema path duplication = 0
schema exists = yes
subprocess started = yes
model call reached = 0/14
candidate generated = 0/14
accepted ready = 0/14
explicit V2 decision = 0/14

fallback stock count = 14
delivery = market 1 + stocks 14 = 15/15 exactly once
exact payload = PASS
```

Both natural V2 attempts failed with the normalized error:

```text
CODEX_APP_SERVER_INITIALIZATION_FAILED_READONLY_STATE_DB
```

The evidence report classed this as `MODEL_TRANSPORT_FAILURE`, but the model was never reached.

The separate daily-review candidate:
- initially had `47` validation errors:
  - `SCHEMA_EXTRA_FIELD = 14`
  - `VALUATION_INTERPRETATION_BINDING = 33`
- terminal numeric binding:
  - automatic = `124`
  - manual = `0`
  - rejected = `0`
  - unresolved = `0`
- then failed the unchanged runtime message-quality gate:
  - `rendered_heading_mismatch = 14`
  - `repeated_sentences = 7`
  - `max_repeat = 10`
  - `template_skeleton_repeats = 9`
  - `identity_prose_mismatch = 1`
  - `final_language_errors = 1`

Night-futures evidence:
- configured products = `2`
- KOSPI200 contract = `A0169000`
- KOSDAQ150 contract = `A0669000`
- all observed provider requests returned HTTP `200`
- provider returned `night_bas_dd = 2026-09-01`
- current readiness logic expected `2026-09-02`
- the gate therefore classified both as `STALE_PRIOR_SESSION_PRESENT`
- ready = `0/2`
- rendered = `0/2`
- raw SHA-256 was stable:
  `39fff1232b66a8ff3fc464d35d21f300ba63595391df440cc2289d2f50fd6d28`

This task must re-evaluate that night-futures status after proving the provider's date semantics.

---

# 2. Current code lineage

Run-51 observed:

```text
origin/main =
operating =
runtime =
2a6bbc449d6802490560cb89d83e0d1fc3e88b24
```

The bundle confirms this runtime contains the prior absolute-path repair.

At task start:

```text
git fetch origin
resolve latest origin/main
resolve operating/runtime SHA
verify clean worktrees
verify ancestry of:
- V2 natural CLI absolute-path repair
- canonical identifier numeric-provenance repair
- CPNG/HUT technical-recovery repair
```

Use the actual latest safe `origin/main` or a safe linear descendant.

Do NOT branch from a stale historical SHA merely because it appears in this instruction.

Hard:

```text
PREVIOUS_V2_PATH_REPAIR_LOST = 0
PREVIOUS_IDENTIFIER_PROVENANCE_REPAIR_LOST = 0
PREVIOUS_TECHNICAL_RECOVERY_LOST = 0
```

---

# 3. Three independent repair tracks

Do not collapse these into one vague "AI failure."

```text
P1-A
Natural scheduler Codex runtime/state DB parity

P1-B
Daily-review message-quality convergence

P1-C
Night-futures provider session-date mapping/readiness
```

Each must have:
- independent root-cause proof
- independent regression tests
- independent pass/fail gate

A pass in one track must not mask a failure in another.

---

# 4. Track A — correct failure taxonomy first

Because run-51 never reached the model:

```text
CODEX_APP_SERVER_INITIALIZATION_FAILED_READONLY_STATE_DB
```

must not remain classified solely as generic external model transport failure.

Introduce or map to a local runtime class such as:

```text
LOCAL_CODEX_RUNTIME_STATE_FAILURE
```

or the closest existing repository-native enum.

Required distinction:

```text
LOCAL_RUNTIME_PRE_MODEL_FAILURE
!=
MODEL_TRANSPORT_FAILURE
```

Reserve model transport for failures after the model/app-server transport layer is actually reached.

Hard:

```text
PRE_MODEL_STATE_FAILURE_MISCLASSIFIED_AS_MODEL_TRANSPORT = 0
```

---

# 5. Track A — prove the exact state DB failure

Do not fix permissions before finding the exact DB and failing operation.

For both primary and backup capture:

```text
scheduler/service identity
PID/parent PID if retained
effective UID
effective GID
supplementary groups
HOME
CODEX_HOME if defined
XDG/state-home variables if relevant
TMPDIR
cwd
umask
CLI binary path/version
state DB absolute path
state DB parent directory
SQLite journal/WAL/SHM path requirements
file owner/group
file mode
parent owner/group/mode
ACL
extended attributes
immutable/restricted flags
mount/read-only state
sandbox/process-namespace restrictions
```

Never print secret values.

For environment variables:
- record presence and safe path identity only
- redact auth/session/token values

On macOS, inspect repository-native service definitions plus appropriate:
- process identity
- file metadata
- ACL/flags
- launch environment
- mount/filesystem state

Do not rely only on `os.access()`.

---

# 6. Compare natural vs passing test environments

The previous production-equivalent tests passed, while natural scheduler run-51 failed.

Create a structured diff:

```text
INTERACTIVE/PREFLIGHT/TEST-SINK
vs
NATURAL PRIMARY
vs
NATURAL BACKUP
```

Compare:

```text
UID/GID/groups
HOME
CODEX_HOME/state home
cwd
PATH
TMPDIR
umask
CLI binary
CLI version
Python environment
scheduler wrapper
environment allowlist
sandbox namespace
state DB path
state DB parent
writable scratch locations
```

Mandatory:

```text
TEST_LIVE_CODEX_STATE_FIRST_DIVERGENCE = ...
```

Do not report "permissions differ" without exact path/identity evidence.

---

# 7. Do not use unsafe permission repairs

Forbidden:

```text
chmod -R 777
world-writable Codex home
running the scheduler as root
broad sudo/chown across user home
copying plaintext auth tokens into repository/runtime files
disabling OS sandbox/security globally
moving secrets into /tmp
```

Hard:

```text
WORLD_WRITABLE_CODEX_STATE = 0
RUN_CODEX_AS_ROOT = 0
PLAINTEXT_AUTH_COPY = 0
GLOBAL_SANDBOX_DISABLE = 0
```

---

# 8. Repair state ownership at the correct boundary

After proving the root cause, choose the smallest supported solution.

Acceptable classes include:

```text
A. canonical writable Codex runtime home owned by the scheduler identity

B. supported per-run/per-service writable state home, if Codex officially
   supports state-home separation and authentication remains securely referenced

C. scheduler environment correction so natural and test processes resolve
   the same intended writable state path
```

Do NOT invent unsupported environment variables.

Use only:
- existing repository contract
- actual Codex CLI supported config
- existing production service mechanisms

Record why the selected solution is correct.

---

# 9. SQLite writeability requirements

If the state store is SQLite, verify all required write surfaces:

```text
database file
parent directory
journal/WAL/SHM creation
rename/delete semantics if used
locking
```

A writable database file with a non-writable parent is not sufficient.

A writable parent with an immutable database file is not sufficient.

Do not manually edit Codex tables.

Hard:

```text
CODEX_STATE_DB_MANUAL_TABLE_EDIT = 0
```

---

# 10. Primary/backup concurrency

Primary and backup must not corrupt or race the shared runtime state.

Determine:

```text
can they overlap?
does packet ownership make them serial?
does Codex state support concurrent readers/writers?
```

If a common state home is used:

```text
concurrency/locking behavior must be proven safe
```

Do not solve read-only failure by creating a later corruption/lock failure.

Gate:

```text
CODEX_PRIMARY_BACKUP_STATE_CONCURRENCY = PASS
```

---

# 11. Runtime-state preflight and observability

Add a bounded local readiness check before V2 model launch.

It must verify at least:

```text
resolved state home
required path exists
DB/parent ownership compatible with scheduler identity
required parent writeability
no known immutable/read-only filesystem condition
```

Do not mutate Codex tables.

If a harmless supported app-server/runtime probe exists, it may be used.

If not, use filesystem-level readiness plus the real safe test invocation.

Failure should be:

```text
LOCAL_CODEX_RUNTIME_STATE_NOT_READY
```

and must not consume model retry budget as if it were a network retry.

---

# 12. Scheduler-context parity probe

This is mandatory because ordinary shell tests missed the defect.

Build a non-production probe that uses the same production scheduler wrapper/runtime environment but is cryptographically or structurally incapable of production delivery.

Required safeguards:

```text
production recipient = unavailable
production delivery intent = impossible
historical packet mutation = impossible
accepted production state mutation = impossible
```

The probe must execute:

```text
natural service environment
→ same Codex CLI binary
→ same state-home resolution
→ same app-server initialization
→ safe test model call
→ schema response
```

No stock decision needs to be persisted to production.

Gate:

```text
SCHEDULER_CONTEXT_CODEX_APP_SERVER_PROBE = PASS
```

A normal interactive shell test does not satisfy this gate.

---

# 13. Track A — run-51 V2 frozen replay

After the runtime-state repair:

use immutable copies of run-51 packet/evidence.

Exercise the production-equivalent V2 path:

```text
context 14/14
schema path
Codex app-server init
model call
candidate
candidate validation
adjudication if required
accepted plan
renderer
```

Target:

```text
RUN51_V2_CONTEXT_READY_COUNT = 14
RUN51_V2_MODEL_CALL_REACHED = PASS
RUN51_V2_CANDIDATE_GENERATED_COUNT = 14
```

Do not force decision labels.

No production send.

---

# 14. Track B — daily-review role/ownership

The separate daily-review path is a safety/secondary AI path.

It must never override a valid packet-bound V2 accepted plan.

Required:

```text
V2 accepted exists
→ V2 accepted remains downstream authority
```

Hard:

```text
DAILY_REVIEW_OVERRIDES_VALID_V2_ACCEPTED = 0
```

If V2 is unavailable, the daily-review path may be used only according to existing selector policy and only after all safety/quality gates pass.

---

# 15. Track B — reproduce exact run-51 quality failures

Use the immutable run-51 daily-review candidate artifacts.

Produce a per-ticker/per-span ledger for:

```text
SCHEMA_EXTRA_FIELD = 14
VALUATION_INTERPRETATION_BINDING = 33

rendered_heading_mismatch = 14
repeated_sentences = 7
max_repeat = 10
template_skeleton_repeats = 9
identity_prose_mismatch = 1
final_language_errors = 1
```

For each error capture:

```text
ticker
field
exact offending span
expected contract
actual output
owning stage:
  generator /
  normalizer /
  renderer /
  quality validator
```

Do not repair based only on aggregate counts.

---

# 16. Track B — schema contract convergence

`SCHEMA_EXTRA_FIELD = 14` suggests a systematic schema mismatch.

Determine whether the extra field was:

```text
generated by the model
added by a normalizer
added by renderer/adapter
or valid under a newer schema but rejected by an older validator
```

Fix the schema owner, not the validator symptom.

Hard:

```text
SCHEMA_VALIDATOR_RELAXED_TO_ACCEPT_UNKNOWN_FIELDS = 0
```

Preferred:

```text
one canonical schema version
→ generator
→ parser
→ normalizer
→ validator
```

---

# 17. Track B — valuation interpretation binding

For the `33` valuation binding errors:

classify each as:

```text
valid fact not bound
semantic basis mismatch
period mismatch
security/share-basis mismatch
currency mismatch
unsupported interpretation
duplicate/derived claim without provenance
```

If the claim is unsupported:

remove/rewrite it.

Do not synthesize EPS/BVPS/multiples.

Hard:

```text
VALUATION_BINDING_GUARD_WEAKENED = 0
```

---

# 18. Track B — deterministic structural ownership

The all-14 `rendered_heading_mismatch` strongly suggests a systematic contract mismatch.

Inspect the exact expected and actual headings.

If headings/identity labels are deterministic UI structure:

prefer:

```text
structured candidate fields
→ deterministic renderer owns headings/company identity
```

rather than asking the model to reproduce exact structural strings.

Do not make the model authoritative for:

```text
company name
ticker
section heading
decision label formatting
```

when canonical structured values already exist.

Gate:

```text
RUN51_RENDERED_HEADING_MISMATCH = 0
```

---

# 19. Track B — repetition quality

Do NOT lower repetition thresholds merely to pass.

For each repeated span determine:

```text
required deterministic skeleton
or
substantive repeated prose
```

If a repeat is mandated structural scaffolding:
- exclude it from substantive-prose comparison only if the current validator is semantically misclassifying structure
- document the rationale
- do not lower the substantive threshold

If it is substantive prose:
- change generation/correction so it is specific to each ticker's evidence
- preserve facts and decision ownership

Hard:

```text
SUBSTANTIVE_REPEAT_THRESHOLD_RELAXED = 0
```

---

# 20. Track B — bounded quality correction

Implement or refine a bounded correction pass for only the failing spans.

The correction context may include:

```text
exact quality errors
canonical identity
accepted decision if applicable
fact IDs already used
forbidden unsupported numbers
required headings/structure
```

The correction must not:
- change accepted decision
- invent new facts
- invent price targets/stops
- change valuation basis
- bypass numeric provenance

After correction rerun:

```text
schema
numeric provenance
semantic provenance
valuation
identity
language
repetition
final message quality
```

Hard:

```text
QUALITY_CORRECTION_CHANGES_ACCEPTED_DECISION = 0
QUALITY_CORRECTION_INTRODUCES_UNBOUND_NUMERIC = 0
QUALITY_REPAIR_LOOP_UNBOUNDED = 0
```

---

# 21. Track B — identity and language

For the one identity mismatch:

derive visible identity from canonical company/security master.

Do not permit freeform AI identity ownership.

For the one language error:

repair only the failing text span with bounded correction.

Gate:

```text
RUN51_IDENTITY_PROSE_MISMATCH = 0
RUN51_FINAL_LANGUAGE_ERRORS = 0
```

---

# 22. Track B — run-51 terminal quality target

On immutable replay:

```text
numeric automatic binding may differ only if output legitimately changes
manual bindings = 0
rejected numeric bindings = 0
unresolved numeric bindings = 0
```

Required terminal:

```text
RUN51_DAILY_REVIEW_SCHEMA = PASS
RUN51_DAILY_REVIEW_NUMERIC = PASS
RUN51_DAILY_REVIEW_VALUATION = PASS
RUN51_DAILY_REVIEW_QUALITY = PASS
```

Do not force the daily-review path to send if V2 accepted is healthy.
This is path health proof only.

---

# 23. Track C — night-futures root-cause correction

The run-51 report currently says:

```text
expected_night_bas_dd = 2026-09-02
provider returned = 2026-09-01
→ STALE_PRIOR_SESSION_PRESENT
```

The user independently observes that Kiwoom itself displays the relevant night session as `2026-09-01`.

Investigate and prove the actual semantics of:

```text
night_bas_dd
```

for:
- KOSPI200 night futures
- KOSDAQ150 night futures

Use:
- provider/Kiwoom field semantics available in repository/provider docs
- raw response
- historical known-good rows
- existing UI/provider examples if available

Do not use the KST message date as the session date by assumption.

---

# 24. Provider-session semantic model

Define explicit concepts:

```text
observation_time_kst
US_regular_session_date
KRX_regular_business_date
night_session_business_date
provider_night_bas_dd
night_session_finality
```

These are not interchangeable.

The expected provider date must be derived from:

```text
provider night-session convention
+
KRX business calendar
+
observation time/cutoff
```

not from:

```text
observation calendar date
```

alone.

Hard:

```text
NIGHT_SESSION_EXPECTED_DATE_EQUALS_OBSERVATION_DATE_BY_DEFAULT = 0
```

---

# 25. Business-calendar mapping

Do not implement:

```text
expected = observation_date - 1 calendar day
```

as a general rule.

Implement/centralize a KRX-business-calendar-aware mapper.

It must handle:
- ordinary Tuesday/Wednesday/etc morning
- Monday morning
- weekends
- KRX holidays
- consecutive holidays
- month/year boundaries

The mapping must represent the provider's actual session convention.

Gate:

```text
NIGHT_SESSION_KRX_BUSINESS_CALENDAR_MAPPING = PASS
```

---

# 26. Do not shortcut via US session date

For run-51:

```text
US session = 2026-09-01
provider night_bas_dd = 2026-09-01
```

They happen to match.

Do not encode:

```text
expected_night_bas_dd = US regular session date
```

unless the provider specification proves that identity for all relevant cases.

Add counterexamples around:
- US holiday / KRX open
- KRX holiday / US open
- weekend differences

Hard:

```text
NIGHT_SESSION_MAPPING_HARDCODED_TO_US_SESSION = 0
```

---

# 27. Night-session finality

A matching business date is not enough.

Prove the returned row is final/safe for the 08:xx KST US market message.

Determine:
- night session close/finality semantics
- provider update timing
- whether the row can still mutate
- whether contract/maturity identity is correct

Only completed/safe rows may be `READY`.

Required:

```text
NIGHT_FUTURES_FINALITY_GATE = PASS
```

---

# 28. Contract identity and maturity

For run-51 controls:

```text
KOSPI200 = A0169000
KOSDAQ150 = A0669000
maturity = 2026-09
```

Verify:
- instrument identity
- active/expected contract
- maturity
- scale/unit
- sign
- change calculation basis

Do not accept a matching date from the wrong contract.

---

# 29. Change-percent provenance

The run-51 proof had:

```text
provider_change_crosscheck_status = NOT_OBSERVED
```

For the corrected path, bind the displayed night-futures change to exact provider fields/calculation.

Record:

```text
source field(s)
baseline
current/final value
change_pct
rounding
fact_id
```

If provider supplies an official change value, prefer it when contract semantics are verified.

Do not invent a change from unrelated day-session values.

---

# 30. Run-51 night-futures immutable replay

Use the stored raw response with SHA:

```text
39fff1232b66a8ff3fc464d35d21f300ba63595391df440cc2289d2f50fd6d28
```

No fresh provider request is needed to prove historical classification.

Under the corrected session mapper:

```text
derive expected provider night session
match KOSPI200
match KOSDAQ150
apply finality
apply contract identity
apply change provenance
```

If the provider semantics confirm the user's observation and both rows are safe:

target:

```text
RUN51_NIGHT_FUTURES_READY_COUNT = 2
RUN51_NIGHT_FUTURES_STATUS = PASS
```

If a row fails an independent finality/identity/provenance gate:

do not force 2/2; return the exact blocker.

Hard:

```text
RUN51_NIGHT_FUTURES_RECLASSIFIED_WITHOUT_SEMANTIC_PROOF = 0
```

---

# 31. Market-message renderer integration

If run-51 replay yields ready night-futures facts:

the market packet must include them and the market renderer must render them in the existing user-facing night-futures section.

Do not create a new AI-owned freeform section if a deterministic market section exists.

Required:

```text
READY_NIGHT_FUTURES_OMITTED_BY_RENDERER = 0
```

The exact message wording may follow repository-native style.

---

# 32. Correct status semantics

After repair:

```text
SOURCE_LIMITATION_SAFE
```

may only be used when the correctly mapped expected provider session truly has no usable row.

Introduce/retain a diagnostic such as:

```text
SESSION_DATE_MAPPING_FAILURE
```

for mapping defects.

Hard:

```text
SESSION_MAPPING_BUG_REPORTED_AS_SOURCE_LIMITATION = 0
```

---

# 33. Track D — preserve run-51 good behavior

Do not regress:

```text
US source monitor 14/14
schema path duplication 0
packet cutoff/ownership
CPNG invalid-row preservation
CPNG invalid numeric leakage 0
HUT quote/completed-close separation
technical failure isolation
product/model identifier provenance
market numeric provenance
exact payload
exactly-once delivery
```

---

# 34. Technical context is not the run-51 root cause

Run-51 had:

```text
PARTIAL_SAFE = 14
INVALID = 0
UNAVAILABLE = 0
```

Do not "fix" this repair by forcing FULL.

Preserve the finality semantics that caused safe partial context.

Hard:

```text
TECHNICAL_PARTIAL_SAFE_FORCED_TO_FULL = 0
```

---

# 35. CPNG regression

Reference run-51:

```text
aggregate = PARTIAL_SAFE
D/W/M = INVALID / INVALID / PARTIAL_SAFE
safe/blocked features = 170/46
invalid raw rows preserved = 2
secondary recovery = 0
invalid numeric leakage = 0
```

Counts may change with fresh data.

Contract must remain:

```text
bad primary rows preserved
safe independent features usable
unsafe dependent features blocked
no synthetic OHLC
```

---

# 36. HUT regression

Reference run-51:

```text
current quote = 77.57
completed technical close = 78.64 as of 2026-08-31
current quote owns completed close = 0
```

Preserve quote/final-bar separation and automatic future recovery.

---

# 37. V2 natural path regression

Keep the previous absolute path contract:

```text
schema
prompt
output
log
cwd
```

must resolve unambiguously.

Required:

```text
V2_SCHEMA_PATH_DUPLICATION = 0
V2_NATURAL_PATH_REGRESSION = PASS
```

---

# 38. Canonical identifier provenance regression

Preserve:
- KF-21 / FA-50 class identifier handling
- real adjacent number validation
- unsupported identifier rejection

Required:

```text
PRODUCT_IDENTIFIER_PROVENANCE_REGRESSION = 0
```

---

# 39. Run-51 end-to-end isolated replay

After Tracks A/B/C:

use immutable copies.

Replay:

```text
market data
→ corrected night-futures mapping
→ market packet
→ market renderer

US14 evidence
→ technical context
→ natural V2 paths
→ scheduler-equivalent Codex runtime state
→ model
→ candidates
→ validation
→ adjudication
→ accepted
→ renderer
→ final validator
```

No production delivery.

Required preferred result:

```text
RUN51_V2_CONTEXT_READY_COUNT = 14
RUN51_V2_MODEL_CALL_REACHED = PASS
RUN51_V2_CANDIDATE_GENERATED_COUNT = 14
RUN51_ACCEPTED_READY_COUNT = 14
RUN51_EXPLICIT_V2_DECISION_COUNT = 14

RUN51_NIGHT_FUTURES_READY_COUNT = 2
RUN51_NIGHT_FUTURES_RENDERED_COUNT = 2
```

The night-futures `2/2` target is conditional on semantic/finality proof as described above.

Do not force BUY/HOLD/SELL distribution.

---

# 40. Daily-review secondary-path replay

Independently replay the daily-review candidate path.

Require:

```text
schema PASS
numeric PASS
valuation PASS
identity PASS
language PASS
repetition/substantive quality PASS
```

Do not send it.

This confirms that if V2 transport is unavailable for an unrelated future reason, the secondary path is no longer guaranteed to terminate at the same quality failure.

---

# 41. Scheduler environment change policy

A runtime-environment repair may require a bounded change to the service/launch environment.

Therefore distinguish:

```text
SCHEDULER_TIMING_DIFF = 0
SCHEDULER_OWNERSHIP_DIFF = 0
SCHEDULER_RUNTIME_ENV_DIFF = documented bounded diff or 0
```

Do not hide a required environment change under `SCHEDULER_DIFF=0`.

If a service definition changes:
- show exact non-secret diff
- explain why
- preserve timing/ownership
- use repository-standard deployment/reload
- verify service health

---

# 42. Cross-market production-equivalent tests

After repair run non-production equivalents for:

```text
US = 14
KR = 8
```

or actual active frozen counts if legitimately changed.

These tests must use:
- natural persisted claim paths
- actual path builder
- repaired Codex runtime-state contract
- scheduler-equivalent environment probe
- accepted-decision ownership
- current technical-context contract

Required:

```text
US_PRODUCTION_EQUIVALENT_V2 = PASS
KR_PRODUCTION_EQUIVALENT_V2 = PASS
```

---

# 43. Dedicated test sink

Use the dedicated non-production test sink.

Reference expected if cohort unchanged:

```text
US 14
KR 8
TOTAL 22
```

Require:
- exact payload
- no production recipient
- no production delivery intent
- exact remaining-subset continuation after rate limit if it occurs
- no duplicates

Hard:

```text
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST = 0
TEST_SINK_DUPLICATE = 0
```

---

# 44. Market message regression

Use run-51 market facts as frozen controls.

Preserve:
- SPY/QQQ/IWM/SOXX/RSP numeric values
- relative-strength selection
- sector selection
- real-yield temporal safety
- stale/reference macro wording
- market numeric provenance

Only expected semantic difference in run-51 market replay:

```text
night-futures section may now be present
```

if corrected rows prove ready.

Hard:

```text
NON_NIGHT_MARKET_NUMERIC_DIFF = 0
```

---

# 45. Price Structure / valuation / decision policy

This repair must not alter:

```text
Price Structure numerics
valuation numerics
decision thresholds/policy
pre-confirmation asymmetry logic
accepted-decision ownership
```

Required:

```text
PRICE_STRUCTURE_NUMERIC_DIFF = 0
VALUATION_NUMERIC_DIFF = 0
DECISION_POLICY_RETUNED = 0
ACCEPTED_DECISION_OWNERSHIP_REGRESSION = 0
```

---

# 46. Tests / CI

Require:

```text
focused Track A tests PASS
focused Track B tests PASS
focused Track C tests PASS
run-51 frozen replay PASS
US production-equivalent V2 PASS
KR production-equivalent V2 PASS
test sink PASS
full pytest PASS
Ruff PASS
git diff --check PASS
GitHub Actions Test/Lint PASS
```

---

# 47. Main merge gate

Merge only if all are true:

```text
exact Codex state DB root cause proven
natural/test first environment divergence proven
unsafe permission hacks = 0
scheduler-context app-server probe PASS
run-51 V2 model reached
run-51 candidates 14/14
daily-review quality PASS without threshold relaxation
night_bas_dd semantics proven
KRX-business-calendar mapper PASS
run-51 night rows correctly reclassified or exact independent blocker documented
ready night facts render
schema-path repair preserved
identifier provenance preserved
CPNG/HUT technical recovery preserved
US/KR production-equivalent tests PASS
test sink exact
P0 = 0
material P1 = 0
```

---

# 48. Deployment and natural-live guard

After merge/deploy:

Do NOT replay historical production.

If runtime service/environment requires reload:
- use bounded repository-standard reload
- verify actual operating/runtime SHA
- verify service health
- verify scheduler timing/ownership unchanged

Then wait for ordinary natural runs.

For next US natural live require:
- model call reached
- candidate/accepted/explicit V2
- correct night-futures session mapper
- ready rows rendered
- exactly-once delivery

For next KR natural live:
- model call reached
- candidate/accepted/explicit V2
- no regression from runtime-state change

Test success is not natural LIVE_PASS.

---

# 49. Required architecture docs

Create/update:

```text
docs/architecture/CODEX_NATURAL_RUNTIME_STATE_CONTRACT.md
docs/architecture/CODEX_TEST_LIVE_ENVIRONMENT_PARITY.md
docs/architecture/DAILY_REVIEW_MESSAGE_QUALITY_CONTRACT.md
docs/architecture/NIGHT_FUTURES_SESSION_DATE_CONTRACT.md
docs/architecture/MARKET_PACKET_TEMPORAL_ROLES.md
docs/architecture/DECISION_ENGINE_V2_PRODUCTION_RUNTIME.md
```

---

# 50. Required reports

Create at minimum:

1. `docs/reports/20260902-run51-codex-state-db-root-cause.md`
2. `docs/reports/20260902-run51-test-live-runtime-environment-diff.md`
3. `docs/reports/20260902-codex-runtime-state-contract.md`
4. `docs/reports/20260902-scheduler-context-codex-probe.md`
5. `docs/reports/20260902-run51-v2-frozen-replay.md`
6. `docs/reports/20260902-daily-review-quality-root-cause.md`
7. `docs/reports/20260902-daily-review-schema-valuation-controls.md`
8. `docs/reports/20260902-daily-review-heading-identity-controls.md`
9. `docs/reports/20260902-daily-review-repetition-quality-controls.md`
10. `docs/reports/20260902-run51-daily-review-quality-replay.md`
11. `docs/reports/20260902-night-futures-provider-session-semantics.md`
12. `docs/reports/20260902-night-futures-krx-calendar-mapping.md`
13. `docs/reports/20260902-run51-night-futures-reclassification.md`
14. `docs/reports/20260902-run51-market-message-replay.md`
15. `docs/reports/20260902-cpng-hut-technical-regression.md`
16. `docs/reports/20260902-v2-path-identifier-regression.md`
17. `docs/reports/20260902-us-production-equivalent-runtime.md`
18. `docs/reports/20260902-kr-production-equivalent-runtime.md`
19. `docs/reports/20260902-three-p1-test-sink.md`
20. `docs/reports/20260902-three-p1-message-quality.md`
21. `docs/reports/20260902-three-p1-main-merge.md`
22. `docs/reports/20260902-three-p1-natural-live-guard.md`
23. `docs/reports/20260902-three-p1-repair-readiness.md`
24. `docs/reports/20260902-three-p1-artifact-index.md`

Machine-readable:

```text
docs/reports/20260902-codex-runtime-state-proof.json
docs/reports/20260902-daily-review-quality-proof.json
docs/reports/20260902-night-futures-session-proof.json
docs/reports/20260902-run51-replay-proof.json
docs/reports/20260902-three-p1-readiness.json
```

---

# 51. Required gates

Set exactly:

```text
BASE_SHA =
...

PREVIOUS_V2_PATH_REPAIR_LOST =
0 / NONZERO

PREVIOUS_IDENTIFIER_PROVENANCE_REPAIR_LOST =
0 / NONZERO

PREVIOUS_TECHNICAL_RECOVERY_LOST =
0 / NONZERO

PRE_MODEL_STATE_FAILURE_MISCLASSIFIED_AS_MODEL_TRANSPORT =
0 / NONZERO

CODEX_STATE_DB_PATH =
<redacted-safe-path-identity>

CODEX_STATE_DB_ROOT_CAUSE =
...

TEST_LIVE_CODEX_STATE_FIRST_DIVERGENCE =
...

WORLD_WRITABLE_CODEX_STATE =
0 / NONZERO

RUN_CODEX_AS_ROOT =
0 / NONZERO

PLAINTEXT_AUTH_COPY =
0 / NONZERO

GLOBAL_SANDBOX_DISABLE =
0 / NONZERO

CODEX_STATE_DB_MANUAL_TABLE_EDIT =
0 / NONZERO

CODEX_PRIMARY_BACKUP_STATE_CONCURRENCY =
PASS / FAIL

CODEX_RUNTIME_STATE_PREFLIGHT =
PASS / FAIL

SCHEDULER_CONTEXT_CODEX_APP_SERVER_PROBE =
PASS / FAIL

RUN51_V2_CONTEXT_READY_COUNT =
14 / OTHER

RUN51_V2_MODEL_CALL_REACHED =
PASS / FAIL

RUN51_V2_CANDIDATE_GENERATED_COUNT =
14 / OTHER

RUN51_ACCEPTED_READY_COUNT =
...

RUN51_EXPLICIT_V2_DECISION_COUNT =
...

DAILY_REVIEW_OVERRIDES_VALID_V2_ACCEPTED =
0 / NONZERO

SCHEMA_VALIDATOR_RELAXED_TO_ACCEPT_UNKNOWN_FIELDS =
0 / NONZERO

VALUATION_BINDING_GUARD_WEAKENED =
0 / NONZERO

RUN51_SCHEMA_EXTRA_FIELD =
0 / NONZERO

RUN51_VALUATION_INTERPRETATION_BINDING_ERRORS =
0 / NONZERO

RUN51_RENDERED_HEADING_MISMATCH =
0 / NONZERO

SUBSTANTIVE_REPEAT_THRESHOLD_RELAXED =
0 / NONZERO

RUN51_REPEATED_SUBSTANTIVE_SENTENCES =
0 / NONZERO

RUN51_TEMPLATE_SKELETON_FALSE_POSITIVE =
0 / NONZERO

RUN51_IDENTITY_PROSE_MISMATCH =
0 / NONZERO

RUN51_FINAL_LANGUAGE_ERRORS =
0 / NONZERO

QUALITY_CORRECTION_CHANGES_ACCEPTED_DECISION =
0 / NONZERO

QUALITY_CORRECTION_INTRODUCES_UNBOUND_NUMERIC =
0 / NONZERO

QUALITY_REPAIR_LOOP_UNBOUNDED =
0 / NONZERO

RUN51_DAILY_REVIEW_SCHEMA =
PASS / FAIL

RUN51_DAILY_REVIEW_NUMERIC =
PASS / FAIL

RUN51_DAILY_REVIEW_VALUATION =
PASS / FAIL

RUN51_DAILY_REVIEW_QUALITY =
PASS / FAIL

NIGHT_BAS_DD_PROVIDER_SEMANTICS =
PROVEN / UNPROVEN

NIGHT_SESSION_EXPECTED_DATE_EQUALS_OBSERVATION_DATE_BY_DEFAULT =
0 / NONZERO

NIGHT_SESSION_MAPPING_HARDCODED_TO_US_SESSION =
0 / NONZERO

NIGHT_SESSION_KRX_BUSINESS_CALENDAR_MAPPING =
PASS / FAIL

NIGHT_FUTURES_FINALITY_GATE =
PASS / FAIL

RUN51_EXPECTED_NIGHT_BAS_DD =
...

RUN51_PROVIDER_NIGHT_BAS_DD =
2026-09-01 / OTHER

RUN51_NIGHT_FUTURES_READY_COUNT =
...

RUN51_NIGHT_FUTURES_RENDERED_COUNT =
...

RUN51_NIGHT_FUTURES_STATUS =
PASS /
SOURCE_LIMITATION_SAFE /
SESSION_DATE_MAPPING_FAILURE /
VALIDATION_FAILURE

RUN51_NIGHT_FUTURES_RECLASSIFIED_WITHOUT_SEMANTIC_PROOF =
0 / NONZERO

READY_NIGHT_FUTURES_OMITTED_BY_RENDERER =
0 / NONZERO

SESSION_MAPPING_BUG_REPORTED_AS_SOURCE_LIMITATION =
0 / NONZERO

TECHNICAL_PARTIAL_SAFE_FORCED_TO_FULL =
0 / NONZERO

V2_SCHEMA_PATH_DUPLICATION =
0 / NONZERO

V2_NATURAL_PATH_REGRESSION =
PASS / FAIL

PRODUCT_IDENTIFIER_PROVENANCE_REGRESSION =
0 / NONZERO

CPNG_HUT_TECHNICAL_RECOVERY_REGRESSION =
0 / NONZERO

US_PRODUCTION_EQUIVALENT_V2 =
PASS / FAIL

KR_PRODUCTION_EQUIVALENT_V2 =
PASS / FAIL

TEST_SINK_US_COUNT =
...

TEST_SINK_KR_COUNT =
...

TEST_SINK_TOTAL_EXACT =
PASS / FAIL

TEST_PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST =
0 / NONZERO

TEST_SINK_DUPLICATE =
0 / NONZERO

NON_NIGHT_MARKET_NUMERIC_DIFF =
0 / NONZERO

PRICE_STRUCTURE_NUMERIC_DIFF =
0 / NONZERO

VALUATION_NUMERIC_DIFF =
0 / NONZERO

DECISION_POLICY_RETUNED =
0 / NONZERO

ACCEPTED_DECISION_OWNERSHIP_REGRESSION =
0 / NONZERO

SCHEDULER_TIMING_DIFF =
0 / NONZERO

SCHEDULER_OWNERSHIP_DIFF =
0 / NONZERO

SCHEDULER_RUNTIME_ENV_DIFF =
0 / DOCUMENTED_BOUNDED_DIFF / UNSAFE_DIFF

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

OPEN_P2 =
...

THREE_P1_REPAIR =
READY_FOR_MAIN /
FAIL
```

---

# 52. Completion response

Return:

```text
WORK_INSTRUCTION_COMMIT = ...
BASE_SHA = ...

TRACK_A_IMPLEMENTATION = ...
TRACK_B_IMPLEMENTATION = ...
TRACK_C_IMPLEMENTATION = ...
TRACK_D_RESULT = ...

ROOT_CAUSE_A_CODEX_STATE =
...

CODEX_STATE_DB_PATH =
...

TEST_LIVE_CODEX_STATE_FIRST_DIVERGENCE =
...

CODEX_RUNTIME_STATE_REPAIR =
...

SCHEDULER_CONTEXT_CODEX_APP_SERVER_PROBE =
...

RUN51_V2_CONTEXT_READY_COUNT = 14
RUN51_V2_MODEL_CALL_REACHED = ...
RUN51_V2_CANDIDATE_GENERATED_COUNT = ...
RUN51_ACCEPTED_READY_COUNT = ...
RUN51_EXPLICIT_V2_DECISION_COUNT = ...

ROOT_CAUSE_B_DAILY_REVIEW =
...

RUN51_SCHEMA_EXTRA_FIELD = ...
RUN51_VALUATION_INTERPRETATION_BINDING_ERRORS = ...
RUN51_RENDERED_HEADING_MISMATCH = ...
RUN51_REPEATED_SUBSTANTIVE_SENTENCES = ...
RUN51_IDENTITY_PROSE_MISMATCH = ...
RUN51_FINAL_LANGUAGE_ERRORS = ...

RUN51_DAILY_REVIEW_SCHEMA = ...
RUN51_DAILY_REVIEW_NUMERIC = ...
RUN51_DAILY_REVIEW_VALUATION = ...
RUN51_DAILY_REVIEW_QUALITY = ...

ROOT_CAUSE_C_NIGHT_FUTURES =
...

NIGHT_BAS_DD_PROVIDER_SEMANTICS = ...
RUN51_EXPECTED_NIGHT_BAS_DD = ...
RUN51_PROVIDER_NIGHT_BAS_DD = 2026-09-01
RUN51_NIGHT_FUTURES_READY_COUNT = ...
RUN51_NIGHT_FUTURES_RENDERED_COUNT = ...
RUN51_NIGHT_FUTURES_STATUS = ...

CPNG_HUT_TECHNICAL_RECOVERY_REGRESSION = 0
V2_NATURAL_PATH_REGRESSION = PASS
PRODUCT_IDENTIFIER_PROVENANCE_REGRESSION = 0

US_PRODUCTION_EQUIVALENT_V2 = ...
KR_PRODUCTION_EQUIVALENT_V2 = ...

TEST_SINK_US_COUNT = ...
TEST_SINK_KR_COUNT = ...
TEST_SINK_TOTAL_EXACT = ...
TEST_PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED_DURING_TEST = 0

PRICE_STRUCTURE_NUMERIC_DIFF = 0
VALUATION_NUMERIC_DIFF = 0
DECISION_POLICY_RETUNED = 0
ACCEPTED_DECISION_OWNERSHIP_REGRESSION = 0

SCHEDULER_TIMING_DIFF = 0
SCHEDULER_OWNERSHIP_DIFF = 0
SCHEDULER_RUNTIME_ENV_DIFF = ...

FULL_TESTS = ...
RUFF = ...
GIT_DIFF_CHECK = ...
ACTIONS = ...

REPORT_COMMIT = ...
FINAL_MAIN = ...
ORIGIN_MAIN = ...
OPERATING = ...
RUNTIME_CODE_SHA = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
OPEN_P2 = ...

THREE_P1_REPAIR =
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

# 53. Mandatory completion ZIP

Create:

`20260902-us-run51-runtime-state-daily-review-night-futures-repair-bundle.zip`

Include:
- exact master instruction
- all track instructions
- run-51 source evidence references/hashes
- exact state-DB root-cause proof
- natural-vs-test environment diff
- scheduler-context app-server probe evidence
- run-51 V2 frozen replay
- daily-review exact error/span ledger
- daily-review corrected replay
- provider night-session semantic proof
- KRX calendar mapping tests
- run-51 night-futures reclassification
- run-51 market replay
- CPNG/HUT regression
- V2 path/identifier regression
- US/KR production-equivalent tests
- test-sink receipt
- CI/main/deployment reports
- machine-readable JSON
- artifact index

Exclude:
- secrets
- auth/session tokens
- Telegram recipient IDs
- account identifiers
- raw credential stores
- hidden chain-of-thought

Compute SHA-256.

---

# 54. Final principle

Run-51 revealed three different defects:

```text
A. model was never reached because the natural process could not initialize
   writable Codex runtime state

B. the secondary daily-review candidate still failed a real message-quality
   contract even after numeric binding succeeded

C. night-futures readiness used the wrong expected session/date model if
   Kiwoom/provider semantics confirm that 2026-09-01 is the current overnight
   session viewed on 2026-09-02 morning
```

Repair each at its owner boundary.

Do not:
- label a pre-model local runtime failure as external model transport
- relax quality gates to pass weak prose
- label a session-mapping bug as provider source limitation
- undo the technical/V2 repairs that are already working

The target architecture is:

```text
natural scheduler
→ correct writable Codex runtime state
→ V2 model call
→ candidate
→ accepted decision
→ explicit V2 renderer

secondary daily-review
→ schema-safe
→ provenance-safe
→ quality-safe
→ never overrides valid V2 accepted

night futures
→ provider session semantics
→ KRX business-calendar mapping
→ finality/contract validation
→ ready fact
→ market renderer
```

Then wait for the next ordinary natural US and KR cycles for final live proof.
