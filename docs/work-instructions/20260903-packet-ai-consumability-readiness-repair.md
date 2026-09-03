# thesis-monitor — Packet AI-Consumability / Numeric-Semantic Readiness Repair
## Fix US run-53's earliest failure
## Preserve suppressed night-futures raw facts without letting non-AI-consumable fields block V2 readiness
## Generic consumer-scope contract — no field-path allowlist

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-09-03 KST`
- Failed natural run: `RUN_ID=53`
- Failed packet: `2026-09-03-us-run-53-055ae8ea01f6`
- Target US regular session: `2026-09-02`
- Task class: `BOUNDED_PACKET_READINESS_REPAIR`
- Production Assist: preserve `OFF`
- Automated trading/order sizing: `0`
- Production recipient send during repair: `0`
- Historical production replay/send: `0`
- Production packet mutation: `0`
- Decision-policy retuning: `0`
- Night-futures session/date contract repair: `0`
- Night-futures user-facing re-enable: `0`
- Treasury block change: `0`
- Scheduler timing/ownership change: `0`

Primary evidence bundle:

```text
20260903-us-morning-natural-live-immediate-extraction-and-proof-bundle.zip
```

Source-supported earliest failure:

```text
source monitor                   14/14
technical                       14/14 PARTIAL_SAFE
production persistence          PASS

shadow numeric-semantic readiness
ready_for_ai = false

unsupported preserved raw fields:
market:night_futures:1:fields.reference_price
market:night_futures:2:fields.reference_price

therefore:
no pending AI-ready packet
→ primary/backup did not claim
→ network preflight NOT_REACHED
→ Codex state/app-server NOT_REACHED
→ model NOT_REACHED
→ candidate 0/14
→ accepted 0/14
→ fallback 14/14
→ delivery 15/15 exactly once
```

This is the only material P1 to repair in this task.

---

# 1. Preserve current safe behavior

At task start:

```text
git fetch origin
resolve latest origin/main
resolve operating HEAD
resolve runtime/deployed SHA
verify clean worktrees
```

Verify base ancestry contains:

```text
Codex runtime-state repair
Codex DNS/network preflight/retry
V2 natural path repair
directional BUY:SELL balance
same-evidence/adjudication controls
daily-review convergence
canonical identifier provenance
CPNG/HUT technical recovery
3Y/5Y/10Y/30Y Treasury block
common disclaimer removal
temporary night-futures user-facing suppression
```

Required:

```text
BASE_CONTAINS_CURRENT_SAFE_REPAIRS = PASS
```

Do not branch from a stale SHA.

---

# 2. What is broken

Current packet behavior conflates:

```text
fact exists in canonical/raw packet
```

with:

```text
fact must pass AI numeric-semantic readiness
```

Those are not the same.

Night-futures facts are intentionally:

```text
collected = yes
preserved = yes
history/DWM = yes
user-facing rendered = no
AI stock-decision consumed = no
```

while the KRX/Kiwoom session convention remains unresolved.

The raw `reference_price` values remained inside the packet and were incorrectly included in the shadow AI-readiness numeric surface.

Result:

```text
non-consumable raw data
→ unsupported numeric semantic
→ entire AI packet blocked
```

This is a packet consumer-ownership bug.

---

# 3. Repair principle

Readiness must answer:

```text
"Are all numeric/semantic facts that THIS consumer can actually receive safe?"
```

not:

```text
"Does every numeric field stored anywhere in the packet have an AI semantic owner?"
```

Required architecture:

```text
canonical packet
→ fact consumer-scope projection
→ consumer-specific numeric/semantic readiness
```

Examples of consumers:

```text
STOCK_V2
DAILY_REVIEW
MARKET_RENDERER
ARCHIVE_ONLY
NIGHT_FUTURES_MODULE
```

Use repository-native names if equivalents already exist.

---

# 4. Do NOT derive AI consumability from user visibility

These are distinct dimensions.

A fact may be:

```text
user_visible = false
AI_consumable = true
```

for hidden reasoning context.

A fact may also be:

```text
user_visible = false
AI_consumable = false
```

for raw archival/provider evidence.

Therefore this repair must NOT implement:

```text
if hidden from Telegram:
    skip AI validation
```

Hard:

```text
AI_CONSUMABILITY_DERIVED_ONLY_FROM_USER_VISIBILITY = 0
```

---

# 5. Consumer-scope metadata

Preferred structured fact contract:

```json
{
  "fact_id": "...",
  "consumer_scopes": [
    "ARCHIVE_ONLY",
    "NIGHT_FUTURES_MODULE"
  ],
  "numeric_semantic": "...",
  "user_visible": false
}
```

or repository-native equivalent.

For ordinary stock-decision facts:

```text
consumer_scopes may include STOCK_V2 / DAILY_REVIEW
```

For temporarily suppressed night-futures raw fields:

```text
must NOT include STOCK_V2
must NOT include DAILY_REVIEW
must remain available to ARCHIVE / NIGHT_FUTURES_MODULE
```

---

# 6. Fail-safe default

Do NOT make unknown/unclassified facts automatically invisible to AI readiness.

Preferred migration rule:

```text
existing facts without explicit new metadata
→ retain current/legacy validation behavior
```

Only facts explicitly owned by a non-AI consumer contract may be excluded from an AI readiness projection.

Hard:

```text
UNCLASSIFIED_FACTS_DEFAULT_TO_AI_EXEMPT = 0
```

This prevents the repair from becoming a broad validator bypass.

---

# 7. No field-path allowlist

Forbidden:

```text
if path == market:night_futures:1:fields.reference_price:
    ignore

if field_name == reference_price:
    ignore
```

Hard:

```text
NIGHT_REFERENCE_PRICE_PATH_ALLOWLIST = 0
FIELD_NAME_BASED_AI_EXEMPTION = 0
```

The behavior must be driven by structured consumer ownership.

---

# 8. Numeric-semantic validation remains strict

If a fact is in:

```text
STOCK_V2
or
DAILY_REVIEW
```

its numeric semantic must remain fully validated.

Do not:
- weaken numeric provenance
- auto-assign semantic meaning from field name
- whitelist unsupported values
- convert unknown numeric semantics to neutral

Hard:

```text
NUMERIC_SEMANTIC_VALIDATOR_WEAKENED = 0
UNKNOWN_AI_NUMERIC_AUTO_ACCEPTED = 0
```

---

# 9. Market renderer ownership is separate

A fact may be consumed by:

```text
MARKET_RENDERER
```

without being consumed by:

```text
STOCK_V2
```

Market-message readiness must validate only its own consumer surface.

Do not let stock-decision readiness inherit every market raw field.

Required:

```text
MARKET_RENDERER_FACTS_DO_NOT_IMPLICITLY_ENTER_STOCK_V2 = PASS
```

---

# 10. Night-futures current temporary state

Until the separate KRX/Kiwoom session-date module is completed:

```text
collection/history/DWM remains enabled
user-facing night-futures remains suppressed
STOCK_V2 consumption = false
DAILY_REVIEW consumption = false
```

Do not change:
- provider rows
- date/session fields
- near-month logic
- history store
- D/W/M calculations

Required:

```text
NIGHT_FUTURES_COLLECTION_REGRESSION = 0
NIGHT_FUTURES_USER_FACING_COUNT = 0
NIGHT_FUTURES_SESSION_CONTRACT_CHANGED = 0
```

---

# 11. Shadow readiness contract

The shadow readiness gate must accept:

```text
consumer = STOCK_V2
```

or equivalent.

Build its numeric/semantic surface only from facts whose consumer ownership allows STOCK_V2.

Similarly, daily-review readiness must build from DAILY_REVIEW-owned facts.

Required output diagnostics:

```text
consumer
included_fact_count
excluded_nonconsumer_fact_count
unsupported_included_numeric_count
```

No sensitive raw payload dump required.

---

# 12. Exclusion diagnostics

When a raw fact is excluded because it is not consumable by the current AI consumer, record a safe reason such as:

```text
NOT_IN_CONSUMER_SCOPE
```

Do not call it:
- validated
- neutral
- semantically safe

It is simply outside that consumer's input surface.

Required:

```text
EXCLUDED_FACT_MISREPORTED_AS_VALIDATED = 0
```

---

# 13. Prompt/input parity

After repair, prove:

```text
consumer readiness projection
```

matches the facts actually supplied to the AI prompt/context.

There must not be:

```text
fact excluded from readiness
but still sent to STOCK_V2 prompt
```

Hard:

```text
READINESS_PROMPT_CONSUMER_SURFACE_MISMATCH = 0
```

This is one of the most important gates.

---

# 14. Renderer/input parity

Likewise:

```text
night-futures raw facts
```

must not accidentally reappear in user-facing US market prose while suppression is active.

Required:

```text
SUPPRESSED_NIGHT_FACT_LEAKAGE_TO_MESSAGE = 0
```

---

# 15. Track A — focused contract tests

Create focused tests covering:

### Case A
```text
raw fact
scope ARCHIVE_ONLY
unsupported AI semantic
→ STOCK_V2 readiness unaffected
```

### Case B
```text
raw fact
scope NIGHT_FUTURES_MODULE
unsupported AI semantic
→ STOCK_V2 readiness unaffected
```

### Case C
```text
hidden fact
scope STOCK_V2
unsupported AI semantic
→ STOCK_V2 readiness FAIL
```

This proves visibility does not own AI consumability.

### Case D
```text
visible market-renderer fact
scope MARKET_RENDERER only
→ STOCK_V2 readiness unaffected
→ market renderer readiness validates it
```

### Case E
```text
unclassified legacy fact
unsupported AI semantic
→ current strict behavior preserved
```

Required:

```text
TRACK_A_CONSUMER_SCOPE_TESTS = PASS
```

---

# 16. Run-53 frozen repair replay

Use an immutable copy/reference of:

```text
2026-09-03-us-run-53-055ae8ea01f6
```

Do NOT modify the production packet.

Recompute readiness in a test/shadow namespace under the repaired consumer contract.

Required first target:

```text
RUN53_STOCK_V2_READY_FOR_AI = true
```

and:

```text
RUN53_UNSUPPORTED_INCLUDED_STOCK_V2_NUMERICS = 0
```

The two night-futures `reference_price` facts must be reported as:

```text
preserved
excluded from STOCK_V2 consumer surface
reason = NOT_IN_CONSUMER_SCOPE
```

---

# 17. Run-53 readiness counts

Require:

```text
source/cutoff subjects = 14
stock V2 readiness = READY
context = 14/14
```

Do not fake readiness by removing canonical facts from the packet.

Required:

```text
RUN53_CANONICAL_RAW_FACT_COUNT_PRESERVED = PASS
```

---

# 18. Run-53 production-equivalent V2 replay

After readiness passes, replay in non-production namespace:

```text
run-53 frozen packet
→ repaired readiness
→ scheduler-equivalent network preflight
→ Codex state preflight
→ app-server
→ actual signed-in model
→ candidate
→ directional balance
→ candidate validation
→ adjudication
→ accepted plan
→ renderer
→ final validator
```

No production send.

Preferred result:

```text
context = 14
candidate = 14
accepted = 14
explicit V2 = 14
balance visible = 14
fallback = 0
```

No forced BUY/HOLD/SELL distribution.

---

# 19. Directional balance regression

Preserve:

```text
BUY+SELL = 10
6:4 BUY
5:5 HOLD
4:6 SELL
neutral band HOLD
HOLD != prior carry-forward
```

Set:

```text
RUN53_BALANCE_SCHEMA = PASS
```

---

# 20. GOOGL / accepted-ownership control

For run-53 replay capture:

```text
GOOGL candidate label/balance
adjudication
accepted label/balance
evidence fingerprint
```

Do not retune its decision.

Required:

```text
ACCEPTED_DECISION_PLAN_REMAINS_AUTHORITY = PASS
```

---

# 21. Network/runtime regression

The natural run-53 did not reach network preflight because readiness failed.

The repaired replay must prove the path now reaches:

```text
network preflight
Codex state
app-server
model
```

Set:

```text
RUN53_NETWORK_PREFLIGHT_REACHED = PASS
RUN53_CODEX_APP_SERVER_REACHED = PASS
RUN53_MODEL_REACHED = PASS
```

This does not yet prove the next NATURAL scheduled run, but it proves the readiness repair no longer blocks transport.

---

# 22. Timeout note — do not scope-creep

The prior production-equivalent test recorded:
- one 900-second model timeout
- one bounded rerun using the runtime-standard 1800-second limit

This was NOT run-53's natural failure.

In this task:

```text
do not redesign model timeout policy
```

But record:

```text
current natural timeout
current production-equivalent timeout
whether they are equal
```

Set:

```text
MODEL_TIMEOUT_POLICY_PARITY =
PASS / REVIEW_REQUIRED
```

If a dangerous mismatch is found:
report it as a separate follow-up.
Do not silently widen timeouts in this bounded readiness repair.

---

# 23. Daily-review regression

Ensure consumer-scope changes do not bypass daily-review validation.

Use the already-passing daily-review fixtures.

Required:

```text
DAILY_REVIEW_STRICT_VALIDATION_REGRESSION = 0
```

---

# 24. KR cross-market regression

Run the same consumer-scope readiness logic on the frozen/current KR production-equivalent fixture.

Required:

```text
KR_STOCK_V2_READINESS = PASS
KR_CANDIDATE_COUNT = 8
KR_ACCEPTED_COUNT = 8
KR_EXPLICIT_COUNT = 8
```

if the fixture cohort remains 8.

No KR packet field should become silently excluded merely because the US night-futures case introduced consumer scopes.

---

# 25. US production-equivalent regression

Reference cohort if unchanged:

```text
14
```

Require:

```text
US_STOCK_V2_READINESS = PASS
US_CANDIDATE_COUNT = 14
US_ACCEPTED_COUNT = 14
US_EXPLICIT_COUNT = 14
US_FALLBACK_COUNT = 0
```

---

# 26. US market-message regression

Preserve:

```text
SPY/QQQ/IWM/SOXX/RSP
sector/relative facts
Treasury 3Y/5Y/10Y/30Y
night futures absent
```

Required:

```text
US_TREASURY_BLOCK_REGRESSION = 0
US_NIGHT_FUTURES_SECTION_PRESENT = 0
```

---

# 27. Test recipient / sink

After US/KR production-equivalent gates pass, use the existing dedicated non-production test sink/recipient according to repository standard.

No production recipient.

Use real transport if that is the existing release gate.

Require:
- exact payload
- duplicates 0
- acknowledged continuation only for unsent remainder on rate-limit
- no production delivery intent

Hard:

```text
PRODUCTION_RECIPIENT_SEND = 0
PRODUCTION_DELIVERY_INTENT_CREATED = 0
```

---

# 28. Production state isolation

All replay/test work:

```text
production packet mutation = 0
production claim mutation = 0
production accepted mutation = 0
production assessment mutation = 0
production notification mutation = 0
production delivery-ledger mutation = 0
```

---

# 29. Full regression gate

Require:

```text
consumer-scope focused tests PASS
run-53 readiness replay PASS
run-53 model/candidate/accepted replay PASS
daily-review regression PASS
KR production-equivalent PASS
US production-equivalent PASS
market-message regression PASS
test sink PASS
full pytest PASS
Ruff PASS
git diff --check PASS
GitHub Actions Test/Lint PASS
service health PASS
```

---

# 30. Merge gate

Merge only if:

```text
night raw fields preserved
night fields excluded from STOCK_V2 only by structured scope
no path/field-name allowlist
unclassified facts retain strict validation
hidden AI-consumable facts still validated
readiness input == actual AI input
run-53 ready_for_ai true
run-53 candidate/accepted 14/14
night user-facing still absent
Treasury block preserved
KR regression PASS
P0 = 0
material P1 = 0
```

---

# 31. Next natural US live guard

After merge/deploy:

do NOT replay production run-53.

Wait for the next ordinary US natural cycle.

Read-only proof must verify:

```text
packet ready_for_ai = true
primary/backup claim path reached
network preflight reached
Codex app-server reached
model reached
candidate 14 or actual cutoff count
accepted
directional balance visible
fallback 0
Treasury present
night futures absent
exactly-once delivery
```

Test/replay PASS is not natural LIVE_PASS.

---

# 32. Required architecture docs

Create/update:

```text
docs/architecture/PACKET_FACT_CONSUMER_SCOPE_CONTRACT.md
docs/architecture/AI_NUMERIC_SEMANTIC_READINESS_SURFACE.md
docs/architecture/MARKET_PACKET_CONSUMER_OWNERSHIP.md
docs/architecture/US_MARKET_TEMPORARY_NIGHT_FUTURES_SUPPRESSION.md
```

---

# 33. Required reports

Create:

1. `docs/reports/20260903-run53-readiness-root-cause.md`
2. `docs/reports/20260903-packet-fact-consumer-scope-contract.md`
3. `docs/reports/20260903-ai-readiness-surface-before-after.md`
4. `docs/reports/20260903-night-futures-consumer-ownership.md`
5. `docs/reports/20260903-readiness-prompt-parity.md`
6. `docs/reports/20260903-consumer-scope-negative-controls.md`
7. `docs/reports/20260903-run53-frozen-readiness-replay.md`
8. `docs/reports/20260903-run53-v2-production-equivalent-replay.md`
9. `docs/reports/20260903-run53-directional-balance-regression.md`
10. `docs/reports/20260903-model-timeout-policy-parity.md`
11. `docs/reports/20260903-daily-review-consumer-scope-regression.md`
12. `docs/reports/20260903-us-production-equivalent-after-readiness.md`
13. `docs/reports/20260903-kr-production-equivalent-after-readiness.md`
14. `docs/reports/20260903-us-market-message-regression-after-readiness.md`
15. `docs/reports/20260903-readiness-repair-test-sink.md`
16. `docs/reports/20260903-readiness-repair-main-merge.md`
17. `docs/reports/20260903-readiness-repair-natural-live-guard.md`
18. `docs/reports/20260903-readiness-repair-artifact-index.md`

Machine-readable:

```text
docs/reports/20260903-consumer-scope-contract.json
docs/reports/20260903-run53-readiness-before-after.json
docs/reports/20260903-run53-v2-replay.json
docs/reports/20260903-readiness-repair-readiness.json
```

---

# 34. Required gates

Set exactly:

```text
BASE_SHA =
...

BASE_CONTAINS_CURRENT_SAFE_REPAIRS =
PASS / FAIL

AI_CONSUMABILITY_DERIVED_ONLY_FROM_USER_VISIBILITY =
0 / NONZERO

UNCLASSIFIED_FACTS_DEFAULT_TO_AI_EXEMPT =
0 / NONZERO

NIGHT_REFERENCE_PRICE_PATH_ALLOWLIST =
0 / NONZERO

FIELD_NAME_BASED_AI_EXEMPTION =
0 / NONZERO

NUMERIC_SEMANTIC_VALIDATOR_WEAKENED =
0 / NONZERO

UNKNOWN_AI_NUMERIC_AUTO_ACCEPTED =
0 / NONZERO

MARKET_RENDERER_FACTS_DO_NOT_IMPLICITLY_ENTER_STOCK_V2 =
PASS / FAIL

NIGHT_FUTURES_COLLECTION_REGRESSION =
0 / NONZERO

NIGHT_FUTURES_USER_FACING_COUNT =
0 / NONZERO

NIGHT_FUTURES_SESSION_CONTRACT_CHANGED =
0 / NONZERO

EXCLUDED_FACT_MISREPORTED_AS_VALIDATED =
0 / NONZERO

READINESS_PROMPT_CONSUMER_SURFACE_MISMATCH =
0 / NONZERO

SUPPRESSED_NIGHT_FACT_LEAKAGE_TO_MESSAGE =
0 / NONZERO

TRACK_A_CONSUMER_SCOPE_TESTS =
PASS / FAIL

RUN53_STOCK_V2_READY_FOR_AI =
true / false

RUN53_UNSUPPORTED_INCLUDED_STOCK_V2_NUMERICS =
0 / NONZERO

RUN53_CANONICAL_RAW_FACT_COUNT_PRESERVED =
PASS / FAIL

RUN53_V2_CONTEXT_READY_COUNT =
14 / OTHER

RUN53_NETWORK_PREFLIGHT_REACHED =
PASS / FAIL

RUN53_CODEX_APP_SERVER_REACHED =
PASS / FAIL

RUN53_MODEL_REACHED =
PASS / FAIL

RUN53_CANDIDATE_COUNT =
14 / OTHER

RUN53_ACCEPTED_COUNT =
14 / OTHER

RUN53_EXPLICIT_COUNT =
14 / OTHER

RUN53_BALANCE_SCHEMA =
PASS / FAIL

RUN53_FALLBACK_COUNT =
0 / NONZERO

ACCEPTED_DECISION_PLAN_REMAINS_AUTHORITY =
PASS / FAIL

MODEL_TIMEOUT_POLICY_PARITY =
PASS / REVIEW_REQUIRED

DAILY_REVIEW_STRICT_VALIDATION_REGRESSION =
0 / NONZERO

US_STOCK_V2_READINESS =
PASS / FAIL

US_CANDIDATE_COUNT =
14 / OTHER

US_ACCEPTED_COUNT =
14 / OTHER

US_EXPLICIT_COUNT =
14 / OTHER

US_FALLBACK_COUNT =
0 / NONZERO

KR_STOCK_V2_READINESS =
PASS / FAIL

KR_CANDIDATE_COUNT =
8 / OTHER

KR_ACCEPTED_COUNT =
8 / OTHER

KR_EXPLICIT_COUNT =
8 / OTHER

US_TREASURY_BLOCK_REGRESSION =
0 / NONZERO

US_NIGHT_FUTURES_SECTION_PRESENT =
0 / NONZERO

PRODUCTION_RECIPIENT_SEND =
0 / NONZERO

PRODUCTION_DELIVERY_INTENT_CREATED =
0 / NONZERO

FULL_TESTS =
PASS / FAIL

RUFF =
PASS / FAIL

GIT_DIFF_CHECK =
PASS / FAIL

ACTIONS =
PASS / FAIL

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

OPEN_P2 =
...

PACKET_AI_CONSUMABILITY_REPAIR =
READY_FOR_MAIN /
FAIL
```

---

# 35. Completion response

Return:

```text
WORK_INSTRUCTION_COMMIT = ...
BASE_SHA = ...

ROOT_CAUSE =
...

OLD_READINESS_CONTRACT =
...

NEW_CONSUMER_SCOPE_CONTRACT =
...

NIGHT_FUTURES_RAW_FACTS =
preserved ...
STOCK_V2 consumable = false
DAILY_REVIEW consumable = false
user-facing = false

RUN53 =
ready_for_ai ...
unsupported included numerics ...
context ...
network preflight ...
app-server ...
model ...
candidate ...
accepted ...
explicit ...
fallback ...

RUN53_DECISIONS =
CORZ ...
CPNG ...
CRCL ...
GOOGL ...
HUT ...
IBM ...
MU ...
RXRX ...
SKHY ...
SNDK ...
TSLA ...
TSM ...
WRD ...
WULF ...

MODEL_TIMEOUT_POLICY_PARITY = ...

US_PRODUCTION_EQUIVALENT =
readiness ...
candidate ...
accepted ...
explicit ...

KR_PRODUCTION_EQUIVALENT =
readiness ...
candidate ...
accepted ...
explicit ...

MARKET =
Treasury regression ...
night futures absent ...

TEST_SINK =
...

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

PACKET_AI_CONSUMABILITY_REPAIR =
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

# 36. Mandatory completion ZIP

Create:

`20260903-packet-ai-consumability-readiness-repair-bundle.zip`

Include:
- exact instruction
- track instructions
- run-53 failure evidence
- consumer-scope architecture
- before/after readiness surface
- negative controls
- run-53 frozen replay
- V2 model/candidate/accepted replay
- balance regression
- timeout parity report
- daily-review regression
- US/KR production-equivalent results
- market regression
- test-sink proof
- CI/main/runtime evidence
- machine-readable JSON
- artifact index

Exclude:
- recipient IDs
- tokens/auth headers
- Codex credentials/state DB contents
- account identifiers
- secrets
- hidden chain-of-thought

Compute SHA-256.

---

# 37. Final principle

The packet may contain more data than any one consumer should see.

Therefore:

```text
canonical storage surface
!=
AI consumer surface
```

The correct repair is:

```text
preserve raw fact
+
declare consumer ownership
+
validate exactly the facts the consumer can receive
```

not:

```text
delete the raw fact
or
whitelist the failing path
or
weaken numeric semantics
```

Once this is fixed, run-53 must progress past readiness and actually reach the network/model/V2 path.
