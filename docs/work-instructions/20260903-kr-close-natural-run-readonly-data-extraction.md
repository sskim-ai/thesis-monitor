# thesis-monitor — 2026-09-03 KR Close Natural-Run Read-Only Data Extraction
## Extract exactly what today's Korean-market natural production run observed and delivered
## No replay, no model rerun, no production mutation

---

# 0. Metadata

- Repository: `sskim-ai/thesis-monitor`
- Target market/date: `KR / 2026-09-03 KST`
- Expected natural schedule:
  - primary KR close run around `16:05 KST`
  - KR telemetry associated with the close run
  - backup run around `16:20 KST`
- Known operational observation from operator:
  - 16:05 KR close exit code `0`
  - KRX telemetry exit code `0`
  - 16:20 backup exit code `0`
- Task class: `READ_ONLY_NATURAL_RUN_EXTRACTION`
- Production mutation: `0`
- Replay: `0`
- Model rerun: `0`
- Fresh provider fetch for substitution: `0`
- Telegram resend: `0`

The purpose is to inspect the real natural KR run, not to reconstruct it.

---

# 1. Target KR monitored cohort

Expected reference universe:

```text
000660
003690
005490
005930
010120
012450
047810
086280
```

Resolve names from the natural run/company profile artifacts.

Do not assume coverage if a ticker is missing.
Report exact natural-run coverage.

---

# 2. First find the authoritative natural run

Locate the actual KR close-run artifacts/logs for 2026-09-03.

Identify:

```text
run_id
scheduled_at
started_at
finished_at
timezone
git commit / operating revision
scheduler unit / invocation identity
primary vs backup lineage
```

If both primary and backup executed:
determine whether backup was a no-op/dedupe-success or produced anything.

Do not merge data from unrelated manual/replay/shadow runs.

Required:

```text
AUTHORITATIVE_RUN_IDENTIFIED = PASS
```

---

# 3. Exactly-once / delivery lineage

Extract:

```text
expected market message count
expected stock message count
actual market message count
actual stock message count
fallback message count
duplicate suppression
delivery receipts/status
```

For the primary and backup separately.

Determine:

```text
was backup suppressed because primary succeeded?
did any message get duplicated?
did fallback and V2 both send for the same ticker?
```

Do not resend.

---

# 4. Pipeline stage counts

From the natural run only, extract exact counts for:

```text
source/evidence ready
technical context status
packet persistence
AI-consumability readiness
network preflight reached/pass/fail
Codex app-server reached/pass/fail
model reached
candidate count
validated candidate count
accepted count
explicit V2 rendered count
fallback count
delivery count
```

If a stage does not exist in this operating revision:
report `NOT_APPLICABLE` or `NOT_PRESENT_IN_THIS_REVISION`.

Do not infer success from downstream success if exact evidence is absent.

---

# 5. Per-ticker data freshness

For each KR8 ticker report natural-run as-of timestamps for:

```text
price
financial/earnings context
valuation
technical price structure
supply/positioning
company/event evidence
```

Classify only if native metadata supports:

```text
CURRENT
STALE
PARTIAL
UNAVAILABLE
```

Do not invent freshness thresholds.

---

# 6. Current price facts

Per ticker extract:

```text
current/close price used by the run
currency
price as_of_date
previous close if stored
```

If the run stores OHLC:
preserve exact raw facts in the machine-readable report,
but the executive table needs only fields relevant to decisions.

No new market fetch.

---

# 7. Price structure

Per ticker extract all verified structured price facts actually available to the run:

```text
nearest support
nearest resistance
major support
major resistance
registered support zone
confirmation price/rule
warning price
invalidation price
technical context status
price-map source/fingerprint if present
```

Do not create support/resistance from raw OHLC in this task.

Do not calculate new indicators.

---

# 8. Returns / technical windows

If natural artifacts expose:

```text
daily/weekly/monthly window_return_pct
```

preserve exact:
- value
- actual_count
- as_of_date

Do not rename them:
- 1-day return
- 1-week return
- 1-month return

unless the source explicitly owns that semantics.

---

# 9. KR supply / positioning

Where `price.supply.available=true`, extract only the actual supported fields:

```text
today foreign flow
today institution flow
today individual flow

5-day foreign/institution/individual flow
20-day foreign/institution/individual flow

foreign ownership ratio
score
quality
primary signal
as_of_date
```

Use native units.

Do not guess whether positive flow is "fundamental strengthening."

Supply remains positioning evidence only.

---

# 10. Earnings / financial checkpoint

Per ticker extract the latest financial/earnings context that the natural packet used:

```text
latest reporting period
revenue / operating profit / attributable income where safely owned
margin where directly present or safely validated
guidance if actually present
earnings checkpoint summary
financial currency
```

Do not create missing:
- FCF
- ROIC
- balance-sheet items
- per-share numbers

from incomplete preliminary results.

Do not recompute unsafe PER/PBR.

---

# 11. Valuation

Per ticker extract exact natural-run valuation context:

```text
PER
PBR
forward PER
forward PBR
historical percentile/context
valuation quality/caution
currency/security basis limitations
as_of_date
```

Only where supplied and valid.

If denominator or security basis is unsafe:
report limitation rather than recomputing.

---

# 12. Market expectations

Where stored in packet/accepted plan, extract:

```text
level:
depressed / low / balanced / elevated / very_high / speculative / unknown

summary
priced_in
upside_surprises
downside_surprises
evidence basis
```

Do not manufacture market-expectation state if today's production revision does not store it.

---

# 13. Business / event evidence

Per ticker extract the top natural-run evidence items used or available:

```text
material filing/event
earnings checkpoint
capital allocation
customer/competitive evidence
business-risk evidence
```

Include:
- source/provider
- date
- concise fact summary

Do not turn price-only news, target-price articles, rumors, or promotional articles into investment-logic events.

---

# 14. Actual production decision outputs

Extract exactly what today's operating revision produced per ticker:

```text
decision label
directional balance if present
lean if present
business thesis state if present
new-buyer view if present
holder view if present
core judgment
re-evaluation conditions
```

Important:

The current operating revision may NOT contain the latest shadow structured-autonomy fields.

If absent:

```text
NOT_PRESENT_IN_PRODUCTION_REVISION
```

Do not synthesize them in this extraction task.

---

# 15. Candidate vs accepted

Where artifacts exist, compare per ticker:

```text
fresh candidate
adjudication
accepted decision plan
rendered decision
```

Report any discrepancy.

Accepted plan remains the downstream authority if the current revision has that architecture.

Do not regenerate a candidate.

---

# 16. Exact delivered messages

Capture exact natural delivered message text for:

```text
KR market message
8 stock messages
```

or exact subset if actual coverage differs.

Store each as UTF-8 text.

Do not rewrite the message in the raw artifact.

Also create a compact human-readable summary report.

---

# 17. Market message facts

From the exact KR market message and its source artifacts extract supported items such as:

```text
KOSPI / KOSDAQ / relevant broad indices
sector leaders/laggards if present
rates/FX/commodity only if included
night futures only if actually user-visible in today's production message
```

Do not re-enable or reconstruct night futures.

If night futures were suppressed:
report:

```text
USER_VISIBLE_NIGHT_FUTURES = 0
```

Do not treat canonical hidden night-futures raw facts as part of the delivered market message.

---

# 18. KRX telemetry

Inspect today's KRX telemetry associated with the KR close run.

Report:

```text
telemetry timestamp
provider success/failure
relevant endpoint/product coverage
night-futures publication observation if logged
raw date labels if present
```

This is data extraction only.

Do not change session-date mapping.

If `BAS_DD=20260903 NIGHT` appeared naturally in telemetry,
preserve the exact raw row separately for tomorrow's reconciliation review.

Do not use it to modify mapping in this task.

---

# 19. 16:20 backup behavior

Inspect exact backup outcome.

Classify:

```text
NOOP_PRIMARY_ALREADY_DELIVERED
DEDUPE_SUPPRESSED
BACKUP_DELIVERED_MISSING_CONTENT
BACKUP_FULL_DELIVERY
OTHER
```

Report exact evidence.

No resend.

---

# 20. Produce a decision-ready KR8 fact table

Create one compact row per ticker with columns:

```text
ticker
name
close/as_of
source readiness
technical status
supply status
latest earnings period
market expectation
valuation summary
support
resistance
confirmation
warning/invalidation
actual production decision
balance if present
delivery status
```

Use `—` only when truly absent.

Do not silently fill from previous days.

---

# 21. Produce a positioning table

For tickers with supply data, create:

```text
ticker
today foreign
today institution
today individual
5d foreign
5d institution
20d foreign
20d institution
foreign ownership
primary signal
as_of_date
```

No fundamental conclusion in this table.

---

# 22. Produce a price-structure table

Create:

```text
ticker
close
nearest support
nearest resistance
major support
major resistance
confirmation
warning
invalidation
technical status
as_of_date
```

Only sourced numbers.

---

# 23. Produce an AI-pipeline table

Create:

```text
ticker
packet ready
AI-consumability ready
model reached
candidate
accepted
rendered V2
fallback
delivered
```

Where pipeline state is global rather than ticker-specific, record that clearly.

---

# 24. Produce exact artifact inventory

Record paths and SHA-256 for:

```text
natural run log
packet artifacts
candidate artifacts
accepted artifacts
rendered messages
delivery receipts
telemetry
backup-run log
```

Only existing artifacts.

No need to package secrets/state DB contents.

---

# 25. Missing-data policy

If an item cannot be found:

```text
MISSING_FROM_NATURAL_ARTIFACTS
```

Do not:
- fetch a replacement
- use tomorrow's data
- use a shadow replay
- reconstruct from public web data
- infer from Telegram text unless the task explicitly marks it as message-derived

Message-derived values must be labeled:

```text
SOURCE = DELIVERED_MESSAGE_TEXT
```

---

# 26. No repair in this task

If an anomaly appears:

```text
record it
classify impact
identify first failing stage
```

Do not patch code.

Examples:
- stale price
- missing supply
- candidate/render mismatch
- backup duplicate
- valuation caution
- technical invalid
- Telegram duplication

This is an extraction/observation task.

---

# 27. Required reports

Create:

1. `docs/reports/20260903-kr-natural-run-lineage.md`
2. `docs/reports/20260903-kr-natural-run-pipeline.md`
3. `docs/reports/20260903-kr8-decision-ready-facts.md`
4. `docs/reports/20260903-kr8-price-structure.md`
5. `docs/reports/20260903-kr8-supply-positioning.md`
6. `docs/reports/20260903-kr8-earnings-valuation-expectations.md`
7. `docs/reports/20260903-kr8-production-decisions.md`
8. `docs/reports/20260903-kr-exact-delivered-messages.md`
9. `docs/reports/20260903-kr-krx-telemetry.md`
10. `docs/reports/20260903-kr-backup-run-behavior.md`
11. `docs/reports/20260903-kr-natural-run-anomalies.md`
12. `docs/reports/20260903-kr-natural-run-artifact-index.md`
13. `docs/reports/20260903-kr-close-executive-summary.md`

Machine-readable:
- `20260903-kr8-facts.json`
- `20260903-kr8-price-structure.json`
- `20260903-kr8-supply.json`
- `20260903-kr8-production-decisions.json`
- `20260903-kr-natural-run-proof.json`

Exact message files:
- `messages/market.txt`
- `messages/000660.txt`
- ...
- exact delivered set only

---

# 28. Required gates

Set exactly:

```text
TARGET_DATE =
2026-09-03

TARGET_MARKET =
KR

AUTHORITATIVE_RUN_IDENTIFIED =
PASS / FAIL

AUTHORITATIVE_RUN_ID =
...

OPERATING_REVISION =
...

PRIMARY_EXIT_CODE =
...

TELEMETRY_EXIT_CODE =
...

BACKUP_EXIT_CODE =
...

EXPECTED_KR_COHORT =
8

ACTUAL_KR_COHORT =
...

SOURCE_READY_COUNT =
...

TECHNICAL_FULL_COUNT =
...

TECHNICAL_PARTIAL_SAFE_COUNT =
...

TECHNICAL_UNAVAILABLE_COUNT =
...

AI_READY_COUNT =
...

MODEL_REACHED_COUNT =
...

CANDIDATE_COUNT =
...

ACCEPTED_COUNT =
...

EXPLICIT_V2_COUNT =
...

FALLBACK_COUNT =
...

MARKET_MESSAGE_COUNT =
...

STOCK_MESSAGE_COUNT =
...

DUPLICATE_DELIVERY_COUNT =
...

USER_VISIBLE_NIGHT_FUTURES =
0 / NONZERO / NOT_PRESENT

SUPPLY_AVAILABLE_COUNT =
...

VALUATION_SAFE_COUNT =
...

PRODUCTION_DIRECTIONAL_BALANCE_PRESENT_COUNT =
...

PRODUCTION_NEW_BUYER_VIEW_PRESENT_COUNT =
...

PRODUCTION_HOLDER_VIEW_PRESENT_COUNT =
...

BACKUP_BEHAVIOR =
NOOP_PRIMARY_ALREADY_DELIVERED /
DEDUPE_SUPPRESSED /
BACKUP_DELIVERED_MISSING_CONTENT /
BACKUP_FULL_DELIVERY /
OTHER

FRESH_PROVIDER_FETCH_FOR_SUBSTITUTION =
0 / NONZERO

MODEL_RERUN =
0 / NONZERO

REPLAY =
0 / NONZERO

PRODUCTION_MUTATION =
0 / NONZERO

TELEGRAM_RESEND =
0 / NONZERO
```

---

# 29. Completion response

Return a compact summary:

```text
AUTHORITATIVE KR RUN =
run_id / revision / timestamps

PIPELINE =
source ...
technical ...
AI ready ...
model ...
candidate ...
accepted ...
explicit ...
fallback ...

DELIVERY =
market ...
stocks ...
duplicates ...
backup behavior ...

KR8 DECISIONS =
ticker / label / balance if present / delivered

PRICE STRUCTURE =
key per-ticker current/support/resistance/confirmation

SUPPLY =
important today/5d/20d flows with exact as_of_date

DATA QUALITY =
stale/partial/valuation/security-basis issues

KRX TELEMETRY =
...

ANOMALIES =
...

NO REPLAY / NO RERUN / NO MUTATION =
PASS

ZIP =
...

ZIP_SHA256 =
...
```

Do not add a fresh investment recommendation in the completion response.
This task extracts what today's production system actually observed.

---

# 30. Completion ZIP

Create:

`20260903-kr-close-natural-run-readonly-data-extraction-bundle.zip`

Include:
- exact work instruction
- all reports
- machine-readable JSON
- exact delivered message copies
- artifact index
- SHA manifest
- secret scan result

Exclude:
- auth tokens
- API keys
- recipient IDs
- credentials
- state DB contents
- hidden chain-of-thought

Compute SHA-256.

---

# 31. Final principle

Today's KR inspection must answer:

```text
What did the real natural production run actually see,
what did it decide,
what did it send,
and what data quality/price/supply state supported that output?
```

Do not turn an observation task into a replay or a repair task.
