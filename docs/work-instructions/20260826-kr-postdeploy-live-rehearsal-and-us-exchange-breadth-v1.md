# thesis-monitor — Immediate KR Post-Deploy Live Rehearsal + US Exchange Breadth Integration v1
## Current-code same-session data/message verification first, then US breadth plumbing

## Metadata

- Workstream: `KR_POSTDEPLOY_LIVE_REHEARSAL_THEN_US_EXCHANGE_BREADTH_V1`
- Instruction version: `1.0`
- Instruction date: `2026-08-26 KST`
- Authoring-time reference: `2026-08-26 00:06 KST`
- Repository: `sskim-ai/thesis-monitor`
- Source policy: `FREE_ONLY`
- Open Research production integration: `0`
- Free Analyst full mode: `OFF`
- Existing bounded AI canary: preserve `market 1 / stocks 2 / total 3`
- Production Assist governance: preserve current state
- Trade AR: preserve OFF
- Public Action: `0.4.5`
- operationId: `20/20 unique`
- schema: `4`

## Current reported operating baseline

From the immediately preceding Kiwoom KR market-context integration completion:

```text
FINAL_MAIN = 73de7d4cc35bb05af3fe40fdfbca46243e0f6f6c
OPERATING  = 73de7d4cc35bb05af3fe40fdfbca46243e0f6f6c

KIWOOM_KR_MARKET_CONTEXT = DEPLOYED_PENDING_NATURAL
KIWOOM_LIVE_PROBE = PASS
KR_INDEX_BREADTH = PASS
KR_SECTOR_SIZE_CONTEXT = PASS
KR_MARKET_WIDE_INVESTOR_FLOW = PASS
KR_MARKET_FLOW_CONCENTRATION = PASS / KOSDAQ_ONLY
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
```

Resolve actual `origin/main` and operating SHA again before execution.  
Do not assume this SHA if the repository has advanced safely.

---

# 0. Project decision

Do not wait until the next natural KR run merely to see what the newly deployed code produces.

First perform a **read-only production-equivalent live rehearsal** using the latest deployed code and the most recently completed KR session.

Then, if that rehearsal is clean, proceed directly to:

`US Exchange Breadth Integration v1`

The sequence is mandatory:

```text
PHASE A
KR current-code live data collection
→ canonical context
→ production-equivalent messages
→ exact validation

PHASE B
US exchange breadth source audit
→ implementation
→ immutable completed-session replay
→ message validation

PHASE C
safe production promotion if gates pass
→ natural proof later
```

---

# 1. Date/session clarification — mandatory

At authoring time it is:

```text
2026-08-26 00:06 KST
```

Therefore the latest completed Korean cash-equity session is:

```text
KR TARGET SESSION = 2026-08-25
```

Do **not** label the test as a `2026-08-26` KR market close.

For US:
- at this authoring time, the `2026-08-25 ET` regular session is still in progress
- do not use an incomplete US session as completed-session breadth proof
- for immutable US replay, bind to the exact completed regular-session date inside the target US packet metadata
- do not infer session date from packet filename alone

If execution occurs after the US 2026-08-25 close, a fresh completed-session breadth probe may be collected as an additional proof, but it must remain separate from the immutable replay if the dates differ.

---

# 2. Work-instruction repository protocol

Store this exact instruction at:

`docs/work-instructions/20260826-kr-postdeploy-live-rehearsal-and-us-exchange-breadth-v1.md`

Before any implementation:

```bash
git fetch origin
git status
git rev-parse HEAD
git rev-parse origin/main
```

Then:

1. commit/push this exact instruction as a docs-only instruction commit
2. record:
   - instruction path
   - instruction commit SHA
   - current production main
   - operating SHA
3. PHASE A must be run before US breadth production-code changes
4. PHASE B should use a dedicated branch from the latest safe main
5. no force push / history rewrite

Recommended branches:

```text
codex/20260826-kr-postdeploy-live-rehearsal
codex/us-exchange-breadth-v1
```

PHASE A may be a reports-only branch if no code repair is needed.

---

# 3. Hard prohibitions

Do NOT:

- manually send Telegram
- manually execute the normal production scheduler task
- mutate monitoring DB state during rehearsal/replay
- write official thesis assessments
- rewrite immutable packet archives
- change watchlist contents
- increase canary limits
- enable Free Analyst full mode
- enable Open Research in production
- enable Trade AR
- weaken numeric/semantic/temporal validators
- fabricate missing breadth
- use incomplete US intraday breadth as completed-session evidence
- label Nasdaq-listed breadth as NYSE breadth
- label S&P500 constituent breadth as exchange breadth
- infer US foreign/institution/retail daily flow
- introduce paid APIs
- scrape article prose for exchange breadth
- silently default unavailable breadth fields to zero

---

# PHASE A — Immediate KR Current-Code Live Rehearsal

# 4. Purpose

Verify what the **already deployed Kiwoom KR code** produces now, using the completed `2026-08-25` KR session.

This is not a natural scheduler proof.

It is:

```text
LIVE_PROVIDER
+ CURRENT_PRODUCTION_CODE
+ READ_ONLY
+ PRODUCTION_EQUIVALENT_RENDERING
```

The result must answer:

1. what structured market data the current code collects
2. what normalized market context is produced
3. what all current monitored-stock messages look like using that data
4. which 3 messages the current canary selector would choose
5. whether any factual, numeric, ownership, temporal, or quality issue remains

---

# 5. No production-code changes before first capture

Before collecting PHASE A evidence:

- do not modify Kiwoom production logic
- do not modify Free Analyst logic
- do not modify renderer/validator logic
- do not change canary selector

Use the exact current deployed code path.

A thin read-only invocation harness is allowed only if:
- it calls existing production functions
- it contains no duplicated business logic
- it cannot mutate DB/Telegram/official assessments

Prefer an existing repo rehearsal/replay entry point.

---

# 6. KR live data collection target

Collect for:

```text
session_date = 2026-08-25
market = KR
exchange_basis = current production configured basis
```

Run current Kiwoom adapter paths corresponding to:

```text
ka20001
  KOSPI
  KOSDAQ

ka20003
  size/style
  sector rows

ka10051
  KOSPI market-wide participant flow
  KOSDAQ market-wide participant flow

ka10066
  KOSPI full pagination
  KOSDAQ full pagination
```

Do not reuse the previous JSON as the new result.

The point is to verify that the deployed code can recollect/reproduce the completed-session evidence.

---

# 7. Expected stable-reference comparison

The previous validated 2026-08-25 capture may be used only as a comparison baseline:

```text
KOSPI
  6742.74
  +0.68%
  breadth 647 / 226 / 34

KOSDAQ
  827.15
  +1.70%
  breadth 1186 / 466 / 74

KOSPI size
  large +0.62%
  mid   +1.37%
  small +1.54%

KOSPI market-wide flow
  foreign     -4000.1bn KRW
  institution +1252.1bn KRW
  retail      +1158.5bn KRW

KOSDAQ market-wide flow
  foreign     +136.1bn KRW
  institution +21.1bn KRW
  retail      -147.2bn KRW

ka10066
  KOSPI 14 pages / 1316 rows
  KOSDAQ 19 pages / 1824 rows
```

These are **comparison expectations**, not values to inject.

If live recollection differs:
- preserve the new raw result
- explain whether the difference is:
  - provider correction
  - exchange-basis change
  - publication timing
  - parser regression
  - source instability
  - unresolved

Never force expected values.

---

# 8. KR raw/live evidence artifact

Create a sanitized live artifact:

`docs/reports/20260826-kr-postdeploy-live-evidence.json`

Include:

```text
retrieved_at
target_session
provider
TR
request semantic fields
page counts
row counts
publication state
market basis
normalized unit
raw evidence hash/reference
```

Exclude:
- access token
- authorization header
- account identifiers
- secrets

---

# 9. KR canonical context artifact

Create:

`docs/reports/20260826-kr-postdeploy-canonical-market-context.json`

This must be the exact structured context fed into analysis.

At minimum show:

```text
KOSPI:
  close
  return
  advancers
  decliners
  unchanged

KOSDAQ:
  same

size/style

sector rows actually eligible for reasoning

market-wide flow:
  foreign
  institution
  individual
  other supported categories
  unit

flow-concentration:
  only where current gates allow it

data_gaps
publication state
```

---

# 10. KOSPI concentration guard remains unchanged

Current known state:

```text
KOSPI ka10051 ↔ ka10066
= unresolved basis/taxonomy difference

KOSDAQ
= within aggregate resolution
```

Do not loosen this just to make the rehearsal richer.

Expected:

```text
KOSPI concentration percentage
= blocked unless the current live recollection independently resolves the basis

KOSDAQ concentration
= eligible only if current reconciliation again passes
```

---

# 11. Production-equivalent KR message generation

Using the freshly collected 2026-08-25 canonical market context:

run the same current analysis pipeline:

```text
current immutable KR packet / current monitored-stock baseline
+
fresh supplemental live structured market context
→ Free Analyst
→ synthesis validator
→ Adaptive Renderer
→ hard validators
→ canary selector simulation
```

Do not send.

---

# 12. Generate ALL KR messages

Do not stop at the 1/2/3 canary selection.

Generate the full production-equivalent set for human inspection:

```text
KR MARKET DIGEST
+
all monitored KR stock messages represented by the target packet
```

Expected current target count from the previous replay:

```text
8 total messages
```

If the current monitored/packet count differs:
report the reason and actual count.

---

# 13. Exact KR message report

Create:

`docs/reports/20260826-kr-postdeploy-exact-generated-messages.md`

For each message include:

```text
MESSAGE_ID
ENTITY / MARKET
RENDERER
CANARY_ELIGIBLE
CANARY_SELECTED
VALIDATION_STATUS

EXACT_RENDERED_TEXT
```

No paraphrased summary only.

This report is the primary human-review artifact.

---

# 14. KR message validation

For every generated message run:

```text
Fact validation
numeric provenance
unit validation
semantic ownership
ticker/entity ownership
temporal-role validation
causality validation
hidden-arithmetic validation
generic-synthesis quality gate
duplicate-section quality gate
material-information-loss audit
```

Set:

```text
KR_POSTDEPLOY_MESSAGE_VALIDATION =
PASS / FAIL
```

---

# 15. KR specific human review

Mandatory manual-style classifications:

```text
KR market digest
SK hynix
Hanwha Aerospace
Samsung Electronics if present
```

For each classify:

```text
MATERIAL_IMPROVEMENT
GOOD_CURRENT_STATE
SAFE_BUT_WEAK
REGRESSION
```

Focus on whether current domestic data is actually used.

---

# 16. KR market-digest acceptance

The current-code digest should lead with domestic evidence when available.

Expected analytical shape:

```text
KOSPI vs KOSDAQ
→ breadth
→ size/sector
→ market-wide participant flow
→ concentration only when valid
→ global context secondarily
```

Reject if the message returns to:
- US context as the main KR explanation
- generic "no new observation" despite rich KR context
- raw participant-number dumping without interpretation

---

# 17. PHASE A safety targets

Hard targets:

```text
FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC = 0
UNIT_CONFLICT = 0
SESSION_DATE_CONFLICT = 0
SEMANTIC_OWNERSHIP_ERRORS = 0
UNSUPPORTED_CAUSALITY = 0
HIDDEN_ARITHMETIC = 0
DEFAULT_ZERO = 0
PAGINATION_PARTIAL_PROMOTED = 0
DUPLICATE_SECURITY_DOUBLE_COUNT = 0
TELEGRAM_SEND = 0
DB_MUTATION = 0
OFFICIAL_ASSESSMENT_MUTATION = 0
ARCHIVE_REWRITE = 0
```

---

# 18. PHASE A gates

Set:

```text
KR_POSTDEPLOY_LIVE_RECOLLECTION =
PASS / PARTIAL / FAIL

KR_POSTDEPLOY_DATA_STABILITY =
MATCH / EXPLAINED_DIFFERENCE / UNRESOLVED_DIFFERENCE / FAIL

KR_POSTDEPLOY_CANONICAL_CONTEXT =
PASS / FAIL

KR_POSTDEPLOY_MESSAGES =
PASS / FAIL

KR_POSTDEPLOY_MESSAGE_VALIDATION =
PASS / FAIL

KR_POSTDEPLOY_CANARY_SIMULATION =
PASS / FAIL

PHASE_A_READY_TO_PROCEED =
YES / NO
```

Proceed to PHASE B when:
- no P0
- no material P1
- current production path remains safe

P2 does not block.

---

# 19. PHASE A reports

Create:

1. `docs/reports/20260826-kr-postdeploy-live-rehearsal.md`
2. `docs/reports/20260826-kr-postdeploy-live-evidence.json`
3. `docs/reports/20260826-kr-postdeploy-canonical-market-context.json`
4. `docs/reports/20260826-kr-postdeploy-data-stability.md`
5. `docs/reports/20260826-kr-postdeploy-exact-generated-messages.md`
6. `docs/reports/20260826-kr-postdeploy-message-validation.md`
7. `docs/reports/20260826-kr-postdeploy-canary-simulation.md`

Do not merge a production behavior change in PHASE A unless a bounded P0/P1 repair is actually required.

---

# PHASE B — US Exchange Breadth Integration v1

# 20. Objective

Fill the next material US market-context gap:

```text
exchange-wide market breadth
```

without changing the Common AI Core.

Current US reasoning already has useful structured context such as:

```text
SPY
QQQ
IWM
SOXX
RSP / equal-weight context
sector context
rates / real yields / macro context
```

The missing breadth prevents direct confirmation of how widely a market move participated.

US participant-flow imitation is out of scope.

---

# 21. Primary source candidate — Nasdaq official free daily market files

Audit first:

```text
NasdaqTrader Daily Market Files / year-to-date file
NasdaqTrader Daily Market Statistics field definitions
```

Official free definitions currently include:

```text
NASDAQ Advances
NASDAQ Declines
NASDAQ Unchanged
```

The source is a strong Tier-1 candidate for completed-session Nasdaq-listed breadth.

Validate:
- publication time
- date field
- issue universe definition
- ETF/other-security inclusion semantics if documented
- revision behavior
- file format stability
- historical access

Do not infer more scope than the source defines.

---

# 22. Nasdaq breadth canonical semantics

If source contract passes, normalize as:

```text
exchange_breadth:
  scope = NASDAQ_LISTED_ISSUES
  session_date
  advances
  declines
  unchanged
  eligible_issue_count
  source
  retrieved_at
  publication_state
```

Only set:

`eligible_issue_count`

if the source definition supports the denominator.

Do not call this:
- NYSE breadth
- all-US breadth
- S&P500 breadth

---

# 23. Deterministic Nasdaq derived relations

Backend may calculate:

```text
net_advances = advances - declines

participation_denominator =
  advances + declines + unchanged

advance_share =
  advances / participation_denominator

decline_share =
  declines / participation_denominator

advance_decline_ratio =
  advances / declines
```

Guard:
- denominator > 0
- declines > 0 for A/D ratio
- same completed session
- source fields complete

Store formula + input refs.

No AI arithmetic.

---

# 24. NYSE breadth source audit

Run a separate source capability audit.

Priority:

## Tier 1
official NYSE / ICE public structured source that is free and legally usable

## Tier 2
existing production structured provider already available in thesis-monitor

## Tier 3
deterministic derivation from a complete verified NYSE-listed universe and existing batch EOD source

Do not use:
- news article market diaries
- copied Dow Jones/WSJ prose
- unstable HTML scraping
as the primary production source.

---

# 25. NasdaqTrader symbol directory as NYSE universe metadata candidate

Audit:

```text
NasdaqTrader otherlisted.txt
```

It identifies other-exchange-listed securities and defines exchange code:

```text
N = New York Stock Exchange
```

This may be used for **listing identity/universe metadata only**.

It is not itself a breadth source.

A derived NYSE breadth is allowed only if the repo already has a safe, sustainable, free structured EOD price source capable of complete compatible coverage.

---

# 26. Derived NYSE breadth completeness rule

Do not promote derived NYSE breadth from partial symbol sampling.

For a derived universe:

```text
eligible NYSE universe
→ deterministic exclusions
→ all remaining eligible securities require same-session close/change classification
```

Record:

```text
universe_count
excluded_count by reason
required_priced_count
priced_count
missing_count
duplicate_identity_count
```

If the eligible universe is not complete after deterministic exclusions:

```text
NYSE_BREADTH = UNAVAILABLE / PARTIAL
```

Do not extrapolate.

---

# 27. NYSE exclusions must be explicit

If building a derived breadth universe, classify security types deliberately.

Do not silently mix/exclude:
- common stock
- preferred
- ETF
- closed-end fund
- warrant
- unit
- rights
- test issue

The definition must either match an authoritative reference breadth or be clearly labeled as a custom breadth universe.

Prefer authoritative source semantics over custom derivation.

---

# 28. v1 may ship Nasdaq-only breadth safely

Do not block the whole integration because NYSE official free breadth is unavailable.

Allowed v1 state:

```text
NASDAQ_BREADTH = PASS
NYSE_BREADTH = UNAVAILABLE
US_EXCHANGE_BREADTH = PARTIAL
```

This is preferable to a weak third-party scrape.

---

# 29. Completed-session timing rule

At instruction authoring time:

```text
US 2026-08-25 regular session
= IN PROGRESS
```

Therefore:

- do not use current intraday advances/declines as completed-session proof
- bind the initial immutable replay to the exact completed session represented by the existing target US packet
- resolve packet `session_date` from metadata
- if Nasdaq official historical file contains that exact date, use it

If implementation occurs after 2026-08-25 ET close:
- collect that completed session too as a separate fresh holdout
- do not back-project it into an older packet

---

# 30. Target US immutable replay

Primary benchmark packet:

```text
2026-08-25-us-run-37-7e04812311c2
```

But:

```text
TARGET_COMPLETED_SESSION =
resolve from packet/session metadata
```

Do not equate packet date with market session without verification.

Construct:

```text
immutable US packet
+
same-session supplemental breadth
→ Free Analyst
→ Adaptive Renderer
→ validators
```

---

# 31. US canonical market-context extension

Reuse current common adapter.

Add/reuse fields such as:

```text
us_market_context:
  session_date
  session_state

  indices_style:
    SPY
    QQQ
    IWM
    SOXX
    RSP

  sectors

  exchange_breadth:
    nasdaq:
      advances
      declines
      unchanged
      derived relations
      source_scope
      publication_state

    nyse:
      same if supported

  rates_macro

  data_gaps
```

Do not create a parallel US reasoning schema.

---

# 32. Breadth interpretation boundary

Allowed analytical implication:

```text
QQQ/SOXX weak
+ Nasdaq declines broadly exceed advances
→ weakness appears broader within Nasdaq-listed issues
```

Allowed:

```text
SPY weak
+ RSP stronger
+ Nasdaq breadth mixed
→ weakness may be concentrated rather than uniformly broad
```

Not allowed:

```text
Nasdaq breadth alone proves all-US risk-off
```

Not allowed:

```text
breadth proves business fundamentals weakened
```

---

# 33. RSP / sector / breadth interaction

The US digest should combine, when same-session valid:

```text
cap-weight vs equal-weight
+
growth/semiconductor relative behavior
+
sector dispersion
+
exchange breadth
+
rates/real yield
```

Purpose:

classify:

```text
broad participation
concentrated mega-cap move
growth-specific weakness
semiconductor-specific weakness
mixed rotation
unresolved
```

Do not force one classification when evidence conflicts.

---

# 34. US market-wide participant flow remains Unknown

This task does not add:

```text
foreign
institution
retail
```

US daily participant cash-equity flow.

Do not use ETF flows/options/13F as substitutes.

Keep separate evidence types for future work.

---

# 35. Source-failure behavior

Breadth is supplemental.

If source fails:

```text
breadth = Unknown
→ current US market packet continues
→ current RSP/sector/index/rate context remains usable
```

No breadth provider may become a packet-blocking dependency.

---

# 36. US exact message benchmark

Create:

`docs/reports/20260826-us-exchange-breadth-exact-message-benchmark.md`

At minimum include:

```text
US MARKET DIGEST

SPARSE / PRE-BREADTH
BREADTH-ENRICHED
DETERMINISTIC_REFERENCE
ADAPTIVE_SELECTED
```

Also include stock messages only where market breadth changes the interpretation materially.

Do not force CORZ/CRCL to mention breadth if irrelevant.

---

# 37. US full shadow message replay

Generate all messages in the target immutable US packet.

Expected previous benchmark size:

```text
14 messages
```

Report actual count.

Hard targets:
- all reach safe terminal state
- no newly introduced generic synthesis
- no semantic ownership regression
- no material information loss

---

# 38. US breadth value-add gate

Set:

```text
US_EXCHANGE_BREADTH_VALUE_ADD =
PASS / NO_MATERIAL_VALUE / FAIL
```

PASS means breadth improves at least one of:

```text
broad-vs-concentrated classification
growth-vs-market differentiation
semiconductor-vs-market differentiation
rotation interpretation
risk-on/risk-off qualification
```

Longer text alone is not value-add.

---

# 39. US focused tests

Mandatory:

### Nasdaq official source
- YTD file parse
- exact session selection
- advances/declines/unchanged mapping
- publication timing
- malformed row fail closed
- missing date fail closed
- no intraday-as-final promotion

### Derived relations
- net advances
- denominator
- advance share
- decline share
- A/D ratio zero guard
- numeric provenance

### NYSE source audit
- exchange identity
- universe completeness
- security-type exclusions
- missing-price fail closed
- no partial extrapolation

### Common adapter
- same schema
- data gaps preserved
- provider failure does not block packet

### AI/rendering
- breadth claim ownership
- no all-US overclaim from Nasdaq-only breadth
- no business-thesis mutation
- no hidden arithmetic
- current RSP/sector facts preserved

---

# 40. US source reports

Create:

1. `docs/reports/20260826-us-exchange-breadth-source-capability.md`
2. `docs/reports/20260826-nasdaq-official-breadth-contract.md`
3. `docs/reports/20260826-nyse-breadth-source-audit.md`
4. `docs/reports/20260826-us-exchange-breadth-publication-timing.md`

---

# 41. US implementation/replay reports

Create:

5. `docs/reports/20260826-us-exchange-breadth-implementation.md`
6. `docs/reports/20260826-us-exchange-breadth-live-or-historical-probe.md`
7. `docs/reports/20260826-us-exchange-breadth-canonical-context.json`
8. `docs/reports/20260826-us-exchange-breadth-run37-replay.md`
9. `docs/reports/20260826-us-exchange-breadth-exact-message-benchmark.md`
10. `docs/reports/20260826-us-exchange-breadth-validation.md`
11. `docs/reports/20260826-us-exchange-breadth-canary-simulation.md`
12. `docs/reports/20260826-us-exchange-breadth-production-readiness.md`
13. `docs/reports/20260826-us-exchange-breadth-artifact-index.md`

Recommended JSON:

`docs/reports/20260826-us-exchange-breadth-production-readiness.json`

---

# 42. US integration gates

Set exactly:

```text
NASDAQ_OFFICIAL_BREADTH_CONTRACT =
PASS / FAIL

NASDAQ_BREADTH =
PASS / PARTIAL / FAIL

NYSE_BREADTH_SOURCE =
PASS / UNAVAILABLE / FAIL

NYSE_BREADTH =
PASS / PARTIAL / UNAVAILABLE / FAIL

US_EXCHANGE_BREADTH =
PASS / PARTIAL / FAIL

US_EXCHANGE_BREADTH_VALUE_ADD =
PASS / NO_MATERIAL_VALUE / FAIL

US_BREADTH_RUN37_REPLAY =
PASS / FAIL

US_BREADTH_MESSAGE_VALIDATION =
PASS / FAIL

US_BREADTH_CANARY_SIMULATION =
PASS / FAIL

US_EXCHANGE_BREADTH_PRODUCTION_READY =
YES / NO
```

---

# 43. Hard safety targets — PHASE B

```text
FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC = 0
SESSION_DATE_CONFLICT = 0
BREADTH_SCOPE_MISLABEL = 0
INTRADAY_PROMOTED_AS_FINAL = 0
UNIVERSE_PARTIAL_PROMOTED = 0
DEFAULT_ZERO = 0
HIDDEN_ARITHMETIC = 0
UNSUPPORTED_CAUSALITY = 0
SEMANTIC_OWNERSHIP_ERRORS = 0
MATERIAL_INFORMATION_LOSS = 0
TRADE_AR_LEAK = 0
```

---

# PHASE C — Production Promotion

# 44. Promotion policy

PHASE A:
- no production behavior change expected
- reports only unless bounded repair is necessary

PHASE B:
may promote US breadth if:

```text
NASDAQ official contract PASS
US_EXCHANGE_BREADTH PASS or safe PARTIAL
run37 replay PASS
message validation PASS
canary simulation PASS
full tests PASS
CI PASS
P0 = 0
material P1 = 0
```

Safe Nasdaq-only `PARTIAL` is production-eligible.

Do not wait for a questionable NYSE source.

---

# 45. Preserve current production governance

After promotion:

```text
FREE_ANALYST_FULL = OFF
CANARY_LIMIT = 1/2/3
OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0
TRADE_AR = OFF
```

No watchlist or monitoring-registration change.

---

# 46. Full validation

Required before final promotion:

```text
PHASE A rehearsal gates PASS/safe
focused US breadth tests PASS
US immutable breadth replay PASS
full pytest PASS
Ruff PASS
git diff --check PASS
Investment Knowledge parity PASS
Chart Knowledge parity PASS
Public Action 0.4.5 unchanged
operationId 20/20 unique
schema 4 unchanged
implementation SHA Actions PASS
final main SHA Actions PASS
API /health PASS
worktrees clean
```

---

# 47. Combined completion report

Create:

`docs/reports/20260826-kr-live-rehearsal-us-breadth-v1-completion.md`

Return:

```text
INSTRUCTION_COMMIT = ...

PHASE_A_BRANCH = ...
PHASE_A_BASE = ...
PHASE_A_REPORT_COMMIT = ...

CURRENT_MAIN_AT_REHEARSAL = ...
CURRENT_OPERATING_AT_REHEARSAL = ...

KR_TARGET_SESSION = 2026-08-25
KR_POSTDEPLOY_LIVE_RECOLLECTION = ...
KR_POSTDEPLOY_DATA_STABILITY = ...
KR_POSTDEPLOY_CANONICAL_CONTEXT = ...
KR_POSTDEPLOY_MESSAGES = .../...
KR_POSTDEPLOY_MESSAGE_VALIDATION = ...
KR_POSTDEPLOY_CANARY_SIMULATION = ...

KR_EXACT_MESSAGES_REPORT = ...

PHASE_A_FACT_MISMATCH = 0
PHASE_A_UNIT_CONFLICT = 0
PHASE_A_SESSION_DATE_CONFLICT = 0
PHASE_A_SEMANTIC_OWNERSHIP_ERRORS = 0
PHASE_A_UNSUPPORTED_CAUSALITY = 0
PHASE_A_HIDDEN_ARITHMETIC = 0
PHASE_A_TELEGRAM_SEND = 0
PHASE_A_DB_MUTATION = 0

PHASE_A_READY_TO_PROCEED = ...

US_BRANCH = ...
US_BASE = ...
US_IMPLEMENTATION_SHA = ...
US_REPORT_COMMIT = ...
FINAL_MAIN = ...
OPERATING = ...

NASDAQ_OFFICIAL_BREADTH_CONTRACT = ...
NASDAQ_BREADTH = ...
NYSE_BREADTH_SOURCE = ...
NYSE_BREADTH = ...
US_EXCHANGE_BREADTH = ...

US_TARGET_IMMUTABLE_PACKET =
2026-08-25-us-run-37-7e04812311c2

US_TARGET_COMPLETED_SESSION = ...
US_BREADTH_RUN37_REPLAY = .../...
US_EXCHANGE_BREADTH_VALUE_ADD = ...
US_BREADTH_MESSAGE_VALIDATION = ...
US_BREADTH_CANARY_SIMULATION = ...

FACT_MISMATCH = 0
UNSUPPORTED_NUMERIC = 0
SESSION_DATE_CONFLICT = 0
BREADTH_SCOPE_MISLABEL = 0
INTRADAY_PROMOTED_AS_FINAL = 0
UNIVERSE_PARTIAL_PROMOTED = 0
DEFAULT_ZERO = 0
HIDDEN_ARITHMETIC = 0
UNSUPPORTED_CAUSALITY = 0
SEMANTIC_OWNERSHIP_ERRORS = 0
MATERIAL_INFORMATION_LOSS = 0
TRADE_AR_LEAK = 0

FREE_ANALYST_CANARY = ...
FULL_MODE = OFF
CANARY_LIMIT = 1/2/3
OPEN_RESEARCH_PRODUCTION_INTEGRATION = 0

US_EXCHANGE_BREADTH_PRODUCTION_READY = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION =
WAIT_FOR_NEXT_NATURAL_PROOF /
BOUNDED_REPAIR /
CONTINUE_TO_OPEN_RESEARCH_CONNECTOR

PRODUCTION_MUTATION_FROM_REHEARSAL = 0
MANUAL_TELEGRAM_SEND = 0
MANUAL_SCHEDULED_TASK = 0

ZIP = ...
ZIP_SHA256 = ...
```

---

# 48. Mandatory final ZIP

Create:

`20260826-kr-live-rehearsal-us-exchange-breadth-v1-bundle.zip`

Include:
- this instruction
- all PHASE A reports
- all PHASE B reports
- sanitized canonical JSON
- exact generated message reports
- completion report

Never include secrets/tokens/auth headers.

Compute/report SHA-256.

---

# 49. Severity

## P0

- wrong current KR market fact
- wrong US breadth fact
- wrong session/date
- incomplete US session labeled final
- wrong breadth venue/scope
- fabricated breadth
- unit conflict
- semantic ownership regression
- hidden arithmetic
- Trade AR leak
- secret/token exposure
- Telegram/DB mutation from rehearsal

## P1

- current deployed KR code cannot reproduce its own stable completed-session evidence without explanation
- rich KR context exists but message ignores it materially
- Nasdaq-only breadth is labeled all-US breadth
- partial NYSE universe is promoted
- breadth provider failure blocks US packet
- breadth materially drops existing RSP/sector/index/rate evidence
- canary quality gate fails

## P2

- NYSE breadth source remains unavailable
- Nasdaq official file publication is delayed
- optional new-high/new-low breadth absent
- US participant flow remains Unknown
- some stock messages do not change because breadth is irrelevant
- safe PARTIAL breadth integration

---

# 50. Final principle

Do not wait for tomorrow to discover whether today's deployed KR code produces useful messages.

Verify it now with a read-only completed-session rehearsal.

Then close the next US structural gap with real exchange breadth.

The desired end state is:

```text
KR
index
+ breadth
+ size/sector
+ market-wide participant flow
+ stock flow
+ safe concentration

US
SPY/QQQ/IWM/SOXX
+ RSP
+ sectors
+ exchange breadth
+ rates/real yields
```

while keeping:

```text
same Common AI Core
same Fact boundary
same semantic ownership
same validators
same bounded canary
```

The project should move forward by improving verified evidence coverage, not by repeatedly rewriting sparse-message prose.
