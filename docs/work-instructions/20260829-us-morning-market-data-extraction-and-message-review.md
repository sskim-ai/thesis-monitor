# thesis-monitor — 2026-08-29 US Morning Market Data Extraction + Message Review
## Read-only current-morning collection
## Pull the actual completed US session, market internals, Korea night futures, macro context, and render the final US morning message candidate
## No production delivery / no assessment mutation

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Date: `2026-08-29 KST`
- Workstream: `US_MORNING_MARKET_DATA_EXTRACTION_AND_MESSAGE_REVIEW`
- Task class: `READ_ONLY_CURRENT_MORNING_MARKET_REVIEW`
- Execution target: actual current KST morning
- Expected latest completed US regular session: likely `2026-08-28`, but MUST resolve from provider/session calendar rather than hard-code
- Production Telegram send: `0`
- Test-sink send: `0`
- DB mutation: `0`
- Thesis/assessment mutation: `0`
- Scheduler mutation: `0`
- Production Assist: no change
- US Price Structure: no change
- KR Price Structure: no change

Before running:

```text
git fetch origin
resolve latest safe origin/main
resolve actual operating checkout
record execution_time_kst
```

Do not modify runtime code for this task unless a data-contract defect is discovered and separately reported.

---

# 1. Objective

Collect the full data set needed to judge the US market this morning and render the exact user-facing market-message candidate.

Required analysis order:

```text
1. session resolution
2. major index returns
3. participation / style
4. semiconductor relative behavior
5. sector dispersion
6. official breadth
7. Korea night futures
8. temporally safe macro context
9. exact US morning message candidate
10. data-quality / missing-data review
```

The task is complete only when both:

```text
raw review table
+
exact message candidate
```

are produced.

---

# 2. Resolve the latest completed US session

At actual execution time:

record:

```text
EXECUTION_TIME_KST
LATEST_COMPLETED_US_SESSION
US_MARKET_CALENDAR_STATUS
```

The latest completed session should be determined from the actual US trading calendar and provider timestamps.

Do not assume today’s calendar date equals the US target session.

Hard:

```text
LATEST_COMPLETED_US_SESSION_RESOLVED = PASS
```

---

# 3. Major index block

Collect current completed-session data for:

```text
SPY
QQQ
IWM
SOXX
RSP
```

For each record:

```text
ticker
close
session_return_pct
session_date
source
state
```

Required current state:

```text
CURRENT_DIRECTIONAL
```

or repository-native equivalent.

Do not annualize, interpolate, or infer returns.

Hard:

```text
SPY_CURRENT = PASS
QQQ_CURRENT = PASS
IWM_CURRENT = PASS
SOXX_CURRENT = PASS
RSP_CURRENT = PASS
```

---

# 4. User-facing index formatting

Prepare:

```text
📈 주요 지수
• SPY +x.xx%
• QQQ +x.xx%
• IWM +x.xx%
• SOXX +x.xx%
• RSP +x.xx%
```

Use backend-owned returns.

No AI-calculated return.

Hard:

```text
AI_CALCULATED_INDEX_RETURN = 0
```

---

# 5. Participation / style

Evaluate:

```text
SPY vs RSP
QQQ vs SPY
IWM vs SPY
```

Goal:

identify whether the session was:

```text
broad participation
large-cap concentrated
growth/tech led
small-cap confirmation
small-cap divergence
mixed
```

Do not turn RSP into exchange breadth.

Required output:

```text
PARTICIPATION_STYLE_SUMMARY
```

and evidence refs.

Hard:

```text
RSP_AS_EXCHANGE_BREADTH = 0
```

---

# 6. Semiconductor relative behavior

Use:

```text
SOXX vs SPY
SOXX vs QQQ
```

to determine whether semiconductors were:

```text
relative strength
relative weakness
roughly in line
```

Output:

```text
SEMICONDUCTOR_RELATIVE_STATE
SEMICONDUCTOR_RELATIVE_SPREAD_VS_SPY
```

Backend calculates the relative spread.

AI must not calculate it.

---

# 7. Sector dispersion

Collect the current completed-session returns for the supported US sector proxy universe.

At minimum the existing supported 11-sector ETF universe should be used.

For each:

```text
ticker
sector_name
return_pct
session_date
state
```

Produce:

```text
full sector table
ranked strongest → weakest
```

Then select:

```text
strongest 3
weakest 3
```

for review.

The final user-facing message may remain concise, but the report must preserve the full sector table.

Hard:

```text
SECTOR_CURRENT_SESSION_COUNT = expected supported count
AI_DERIVED_SECTOR_RANKING = 0
```

---

# 8. Sector message policy

Prepare both:

```text
SECTOR_TOP3_STRONG
SECTOR_TOP3_WEAK
```

Then report what the CURRENT production renderer actually selects:

```text
top 1 / bottom 1
or
top 3 / bottom 3
```

Do not silently change the renderer policy in this read-only task.

---

# 9. Official Nasdaq breadth

Check the official Nasdaq breadth source for the exact target US session.

Record:

```text
requested_session
latest_official_source_session
advance_count
decline_count
unchanged_count
advance_decline_ratio
publication_state
```

Possible state:

```text
CURRENT
PUBLICATION_PENDING
SOURCE_UNAVAILABLE
```

Exact-session required.

Do not use a prior session as if it were current.

Hard:

```text
STALE_NASDAQ_BREADTH_AS_CURRENT = 0
```

---

# 10. NYSE breadth

If the current production architecture still has no supported official/free NYSE breadth source:

record:

```text
NYSE_BREADTH = UNAVAILABLE
```

Do not synthesize or substitute unofficial data in this task.

---

# 11. Korea night futures

Run the canonical Korea night-futures gate.

Collect:

```text
KOSPI200 night futures
KOSDAQ150 night futures
```

Record:

```text
expected overnight session
actual session
return_pct
state
source
```

Possible state:

```text
CURRENT_OVERNIGHT_DIRECTIONAL
NOT_READY
PUBLICATION_PENDING
SOURCE_UNAVAILABLE
STALE
```

or repository-native equivalents.

Hard:

```text
NIGHT_FUTURES_CANONICAL_GATE_USED = PASS
RAW_SUMMARY_NIGHT_FUTURES_BYPASS = 0
```

---

# 12. Night-futures session mapping

Because execution is on a Saturday KST morning:

do not guess the relevant Korean overnight session.

Resolve:

```text
execution_time_kst
latest completed US session
next relevant KR regular trading session
expected night-futures session
```

using the canonical session resolver.

Hard:

```text
NIGHT_FUTURES_SESSION_MAPPING = PASS
```

---

# 13. Night-futures user-facing policy

If a product is current-safe:

render:

```text
🌙 한국 야간선물
• KOSPI200 야간선물 +x.xx%
• KOSDAQ150 야간선물 -x.xx%
```

If only one is current-safe:

show only one.

If none are current-safe:

omit the entire section.

Hard:

```text
STALE_NIGHT_FUTURES_VISIBLE = 0
EMPTY_NIGHT_FUTURES_SECTION = 0
```

---

# 14. Macro context

Use the current macro pipeline.

Audit at minimum:

```text
US 10Y nominal yield
US 10Y real yield
VIX
WTI
USD/KRW
broad dollar index / other currently supported liquidity context
```

For each record:

```text
observation_date
value
change
temporal_role
source
```

Temporal roles should remain repository-native equivalents of:

```text
CURRENT_OBSERVATION
PRIOR_MARKET_SESSION
REFERENCE_LAGGING
STALE_FOR_DAILY_SIGNAL
UNAVAILABLE
```

---

# 15. Macro user-facing selection

Only use macro facts when:

```text
specific
material
temporally safe
```

Current or explicitly date-qualified prior facts may be used.

Generic neutral macro:

```text
omit
```

Do not render malformed generic text.

Hard:

```text
GENERIC_NO_CHANGE_MACRO_SECTION_VISIBLE = 0
MALFORMED_ZERO_CHANGE_KOREAN = 0
STALE_MACRO_AS_CURRENT = 0
```

---

# 16. Macro role in the message

Priority:

```text
1. major indices
2. market internals
3. sectors
4. Korea night futures
5. macro
6. next check
```

Macro must not crowd out current market evidence.

Hard:

```text
MACRO_CROWDS_OUT_CURRENT_MARKET = 0
```

---

# 17. Current production message contract

Render the exact current candidate using the deployed message contract.

Target structure:

```text
🇺🇸 미국시장 마감

📈 주요 지수
• SPY ...
• QQQ ...
• IWM ...
• SOXX ...
• RSP ...

🔎 시장 내부
• participation/style
• semiconductor relative state
• sector strong/weak

🌙 한국 야간선물
• ...
(only if current-safe)

🌐 보조 시장환경
• ...
(only if specific/material/temporally safe)

📌 다음 확인
• ...
```

Do not invent sections that current production policy does not support.

---

# 18. Exact message candidate

Create:

```text
EXACT_US_MORNING_MESSAGE_CANDIDATE
```

This is the exact text that would be sent under the current deployed renderer.

DO NOT send it in this task.

Preserve exact line breaks.

---

# 19. AI / deterministic fallback review

Generate:

```text
AI-assisted candidate
deterministic fallback candidate
```

Compare:

```text
index numerics
sector numerics
night-futures visibility
temporal macro safety
section order
```

Hard:

```text
AI_FALLBACK_INDEX_NUMERIC_PARITY = PASS
AI_FALLBACK_SECTOR_NUMERIC_PARITY = PASS
AI_FALLBACK_NIGHT_FUTURES_PARITY = PASS
AI_FALLBACK_TEMPORAL_PARITY = PASS
```

---

# 20. Natural-run inspection

Check whether the regular US morning natural job already executed today.

If yes, read-only collect:

```text
run id
packet id
route
delivery state
exact delivered message
```

Compare the natural delivered message against the current extracted evidence.

Do not mutate the natural run.

Set:

```text
NATURAL_US_MORNING_RUN =
FOUND / NOT_FOUND
```

If found:

```text
NATURAL_US_MORNING_MESSAGE_EVIDENCE_PARITY =
PASS / FAIL
```

---

# 21. Data-quality review

Create a compact issue table:

```text
component
expected
actual
state
impact
```

At minimum cover:

```text
core indices
RSP
SOXX
sector universe
Nasdaq breadth
night futures
macro
natural run
```

Classify issues:

```text
NONE
SAFE_OMISSION
PUBLICATION_PENDING
STALE
PROVIDER_ERROR
SEMANTIC_CONFLICT
MATERIAL_P1
```

---

# 22. Final morning review table

Create one operator-facing summary:

```text
US target session
SPY
QQQ
IWM
SOXX
RSP

participation/style
semiconductor relative state

top 3 sectors
bottom 3 sectors

Nasdaq breadth state
KOSPI200 night futures
KOSDAQ150 night futures

macro facts actually selected
natural-run status
```

---

# 23. Required reports

Create:

1. `docs/reports/20260829-us-morning-session-resolution.md`
2. `docs/reports/20260829-us-major-index-data.md`
3. `docs/reports/20260829-us-participation-style.md`
4. `docs/reports/20260829-us-semiconductor-relative.md`
5. `docs/reports/20260829-us-sector-dispersion.md`
6. `docs/reports/20260829-us-nasdaq-breadth.md`
7. `docs/reports/20260829-us-korea-night-futures.md`
8. `docs/reports/20260829-us-macro-context.md`
9. `docs/reports/20260829-us-morning-exact-message-candidate.md`
10. `docs/reports/20260829-us-morning-ai-fallback-parity.md`
11. `docs/reports/20260829-us-natural-run-inspection.md`
12. `docs/reports/20260829-us-morning-data-quality.md`
13. `docs/reports/20260829-us-morning-review-summary.md`
14. `docs/reports/20260829-us-morning-artifact-index.md`

Machine-readable:

```text
docs/reports/20260829-us-morning-market-data.json
docs/reports/20260829-us-morning-review-summary.json
```

---

# 24. Required gates

Set exactly:

```text
EXECUTION_TIME_KST =
...

LATEST_COMPLETED_US_SESSION =
...

LATEST_COMPLETED_US_SESSION_RESOLVED =
PASS / FAIL

SPY =
...

QQQ =
...

IWM =
...

SOXX =
...

RSP =
...

SPY_CURRENT =
PASS / FAIL

QQQ_CURRENT =
PASS / FAIL

IWM_CURRENT =
PASS / FAIL

SOXX_CURRENT =
PASS / FAIL

RSP_CURRENT =
PASS / FAIL

PARTICIPATION_STYLE_SUMMARY =
...

SEMICONDUCTOR_RELATIVE_STATE =
...

SEMICONDUCTOR_RELATIVE_SPREAD_VS_SPY =
...

SECTOR_CURRENT_SESSION_COUNT =
...

SECTOR_TOP3_STRONG =
...

SECTOR_TOP3_WEAK =
...

NASDAQ_BREADTH_STATE =
CURRENT / PUBLICATION_PENDING / SOURCE_UNAVAILABLE / FAIL

NASDAQ_BREADTH_SOURCE_SESSION =
...

STALE_NASDAQ_BREADTH_AS_CURRENT =
0 / NONZERO

NYSE_BREADTH =
UNAVAILABLE / CURRENT / OTHER

EXPECTED_NIGHT_FUTURES_SESSION =
...

KOSPI200_NIGHT_FUTURES =
...

KOSPI200_NIGHT_FUTURES_STATE =
...

KOSDAQ150_NIGHT_FUTURES =
...

KOSDAQ150_NIGHT_FUTURES_STATE =
...

NIGHT_FUTURES_CANONICAL_GATE_USED =
PASS / FAIL

NIGHT_FUTURES_SESSION_MAPPING =
PASS / FAIL

RAW_SUMMARY_NIGHT_FUTURES_BYPASS =
0 / NONZERO

STALE_NIGHT_FUTURES_VISIBLE =
0 / NONZERO

MACRO_SELECTED_FACTS =
...

GENERIC_NO_CHANGE_MACRO_SECTION_VISIBLE =
0 / NONZERO

MALFORMED_ZERO_CHANGE_KOREAN =
0 / NONZERO

STALE_MACRO_AS_CURRENT =
0 / NONZERO

AI_CALCULATED_INDEX_RETURN =
0 / NONZERO

AI_DERIVED_SECTOR_RANKING =
0 / NONZERO

AI_FALLBACK_INDEX_NUMERIC_PARITY =
PASS / FAIL

AI_FALLBACK_SECTOR_NUMERIC_PARITY =
PASS / FAIL

AI_FALLBACK_NIGHT_FUTURES_PARITY =
PASS / FAIL

AI_FALLBACK_TEMPORAL_PARITY =
PASS / FAIL

NATURAL_US_MORNING_RUN =
FOUND / NOT_FOUND

NATURAL_US_MORNING_RUN_ID =
...

NATURAL_US_MORNING_PACKET_ID =
...

NATURAL_US_MORNING_MESSAGE_EVIDENCE_PARITY =
PASS / FAIL / NOT_APPLICABLE

OPEN_P0 =
...

OPEN_MATERIAL_P1 =
...

US_MORNING_DATA_REVIEW =
PASS / PARTIAL_SAFE / FAIL
```

---

# 25. Completion response

Return:

```text
BASE_SHA = ...
OPERATING = ...

EXECUTION_TIME_KST = ...
LATEST_COMPLETED_US_SESSION = ...

SPY = ...
QQQ = ...
IWM = ...
SOXX = ...
RSP = ...

PARTICIPATION_STYLE_SUMMARY = ...
SEMICONDUCTOR_RELATIVE_STATE = ...

SECTOR_TOP3_STRONG = ...
SECTOR_TOP3_WEAK = ...

NASDAQ_BREADTH_STATE = ...
NASDAQ_BREADTH_SOURCE_SESSION = ...

EXPECTED_NIGHT_FUTURES_SESSION = ...

KOSPI200_NIGHT_FUTURES = ...
KOSPI200_NIGHT_FUTURES_STATE = ...

KOSDAQ150_NIGHT_FUTURES = ...
KOSDAQ150_NIGHT_FUTURES_STATE = ...

MACRO_SELECTED_FACTS = ...

EXACT_US_MORNING_MESSAGE_CANDIDATE =
...

AI_FALLBACK_INDEX_NUMERIC_PARITY = ...
AI_FALLBACK_SECTOR_NUMERIC_PARITY = ...
AI_FALLBACK_NIGHT_FUTURES_PARITY = ...
AI_FALLBACK_TEMPORAL_PARITY = ...

NATURAL_US_MORNING_RUN = ...
NATURAL_US_MORNING_RUN_ID = ...
NATURAL_US_MORNING_PACKET_ID = ...
NATURAL_US_MORNING_MESSAGE_EVIDENCE_PARITY = ...

DATA_QUALITY_ISSUES =
...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...

US_MORNING_DATA_REVIEW =
PASS /
PARTIAL_SAFE /
FAIL

NEXT_ACTION =
REVIEW_EXACT_MESSAGE /
BOUNDED_REPAIR /
NO_ACTION

ZIP = ...
ZIP_SHA256 = ...
```

---

# 26. Mandatory completion ZIP

Create:

`20260829-us-morning-market-data-extraction-and-message-review-bundle.zip`

Include:

```text
exact instruction
session-resolution report
major-index data
participation/style
semiconductor relative analysis
full sector table
Nasdaq breadth
Korea night futures
macro temporal context
exact message candidate
AI/fallback parity
natural-run inspection
data-quality review
summary JSON
artifact index
```

Exclude:

```text
secrets
Telegram IDs
tokens
auth headers
account identifiers
hidden chain-of-thought
```

Compute SHA-256.

---

# 27. Final principle

This task is about seeing the US market as it actually closed last night.

Show the hard numbers first:

```text
SPY / QQQ / IWM / SOXX / RSP
```

Then explain:

```text
participation
semiconductor leadership
sector dispersion
breadth
Korea night futures
macro
```

Use only the exact completed-session and temporally safe facts available this morning.
