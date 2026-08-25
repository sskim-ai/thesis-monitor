# thesis-monitor — 2026-08-25 US Morning Natural + Open Research Multi-Proof Review

## Metadata

- Task type: `ONE_SHOT_READ_ONLY_US_MORNING_MULTI_PROOF_REVIEW`
- Instruction version: `1.0`
- Date: `2026-08-25 KST`
- Recommended start: `09:20 KST`
- Read-only wait hard stop: `10:05 KST`
- Repository: `sskim-ai/thesis-monitor`
- Expected production main/operating: `2e3e37cc75867d56a69211bbe93a3675cd87acd1`
- Latest Adaptive Renderer shadow report tip: `5e30b17bf1fa10acb5483bfb6961b2a6d6fc8a86`
- Latest Open Research shadow report tip: `6db5d760b1b0b24ff224d4be3c89315233b8af0b`

Resolve the actual latest safe `origin/main`, operating SHA, and shadow branch tips before execution.

Known state:
- Production Assist = OFF
- Inventory = `SELECTIVE_INVENTORY`, user-visible enabled pending natural proof
- Trade AR user-visible = OFF pending natural proof
- Phase 9.0E = `SELECTIVE_CURRENT_FORMAL_FULL_FCF`
- Free Analyst shadow = PASS
- Adaptive Renderer shadow = PASS
- Open Research KR benchmark = PASS / MATERIAL_MATCH class
- US Open Research holdout = NOT_OBSERVED because automation registration timed out
- Production promotion remains BLOCKED

---

## 0. Objective

Today’s review must answer two separate questions.

### A. Production natural proof

Did the unchanged production main naturally complete:

`US packet → AI/fallback → Telegram → receipt / exactly-once`

safely?

### B. Open Research fresh holdout

Using the same immutable natural US packet, does the shadow research stack improve:

`why did the market/stock move?`

without weakening source, time, entity, fact, causality, or negative-evidence boundaries?

Do not mix these evidence classes.

---

## 1. Work-instruction protocol

Store this exact instruction at:

`docs/work-instructions/20260825-us-morning-natural-and-open-research-multi-proof-review.md`

Before review:

```bash
git fetch origin
git status
git rev-parse origin/main
git rev-parse origin/codex/adaptive-renderer-selector-shadow
git rev-parse origin/codex/open-research-event-attribution-shadow
```

Then:

1. commit/push this instruction as docs-only
2. record instruction commit SHA
3. create review branch `codex/20260825-us-morning-multi-proof-review`
4. review production evidence read-only
5. use shadow worktree only for Free Analyst / Adaptive / Open Research
6. do not merge reports into production main automatically

---

## 2. Hard prohibitions

Do NOT:

- rerun US production or backup manually
- send Telegram
- mutate production DB / receipts / notificationdelivery
- mutate assessments, warnings, investment-logic versions, Pilot
- change schedules or deadlines
- change Inventory / Trade AR / Phase 9.0E / Macro settings
- change Production Assist
- merge Free Analyst / Adaptive / Open Research to main

Hard targets:

```text
PRODUCTION_MUTATION = 0
TELEGRAM_SEND_FROM_REVIEW = 0
MAIN_PROMOTION = 0
```

---

## 3. Terminal-state rule

At 09:20 inspect:

- US primary
- US backup
- production receipt
- KRX 08:05
- night-futures 08:45
- night-futures 09:15

If terminal, proceed.

If not terminal:
- wait read-only
- never trigger jobs manually
- hard stop at 10:05

If still nonterminal:

`REVIEW_STATE = DEFERRED_NONTERMINAL`

and still generate the report ZIP.

---

# Part I — Production natural proof

## 4. Operating state

Record:

- main / origin/main / operating SHA
- parity
- API health
- worktree cleanliness
- Production Assist
- Inventory mode
- Trade AR mode
- Phase 9.0E mode
- US AI compatibility repair state
- Macro temporal repair state
- schedule state

Unexpected production config drift = P0/P1 depending impact.

---

## 5. Canonical US natural packet

Identify exact packet and record:

```text
packet_id
assessment_date
created_at
primary/backup owner
expected message count
AI candidate state
fallback state
terminal state
receipt ref
```

If primary and backup both created artifacts, identify canonical ownership.

---

## 6. Exact actual sent message bundle

Create:

`docs/reports/20260825-us-natural-sent-message-bundle.md`

Include exact:
- US market digest
- all monitored stock messages
- sent order
- packet ID
- delivery mode
- send time

No secret destination identifiers.

---

## 7. US AI compatibility natural proof

Audit:

- candidate generated?
- correction attempts
- numeric validation
- semantic validation
- final-language validation
- runtime-quality validation
- actual delivery mode

Regression hard targets:

```text
FCF fiscal/YTD/FY period errors = 0
current-price RR ownership errors = 0
unsupported Fact ownership = 0
```

Set:

`US_AI_COMPATIBILITY_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED`

---

## 8. Macro temporal natural proof

For every macro item used in the actual US digest record:

```text
metric
observation date
retrieval date
temporal role
important_change eligibility
today_signal eligibility
actual wording
```

Hard targets:

```text
false-current claims = 0
missing temporal metadata defaulted current = 0
reference-only fact creating today_signal = 0
genuinely new observation incorrectly suppressed = 0
```

Set:

`MACRO_TEMPORAL_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED`

---

## 9. Phase 9.0E cash-flow regression

For rendered FCF contexts audit:

- ticker
- Fact ID
- period
- scope
- currency
- current-formal state
- baseline consistency
- wording
- duplicate number use
- valuation mutation

Set:

`PHASE_9_0E_NATURAL_REGRESSION = PASS / FAIL / NOT_OBSERVED`

---

## 10. Inventory natural proof

For each stock record:

```text
ticker
eligible
selected/suppressed
suppression reason
context ID
Fact IDs
relation ID
balance date
comparison basis
actual delivered wording
```

Set:

`INVENTORY_USER_VISIBLE_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED`

LIVE_PASS requires at least one actually delivered Inventory enrichment with:
- total Inventory semantic
- correct Fact/relation/date/PIT
- no demand-collapse/oversupply overclaim
- no Inventory Days / CCC
- no hidden FCF inference
- no delivery regression

---

## 11. Trade AR natural canary

Audit detached Phase 9.1D canary:

- exact `trade_accounts_receivable`
- no broad AR substitution
- relation vs Revenue
- PIT/freshness
- numeric binding
- no DSO
- no causal overclaim
- production influence = 0

Set:

`TRADE_AR_NATURAL_PROOF = LIVE_PASS / FAIL / NOT_OBSERVED`

Hard user-visible target:

```text
Trade AR = 0
Broad AR = 0
AP = 0
```

If LIVE_PASS:

`TRADE_AR_ENABLEMENT_CANDIDATE = YES_PENDING_SEPARATE_ENABLEMENT`

Do not enable.

---

## 12. Primary / backup / exactly-once

Review primary and backup lifecycle.

Hard targets:

```text
sent = expected
duplicates = 0
orphans = 0
receipt_integrity = PASS
exactly_once = PASS
```

Set:

`US_PRODUCTION_NATURAL = LIVE_PASS / FAIL`

---

## 13. Night-futures telemetry

Collect all natural attempts for expected NIGHT session.

Per attempt:

```text
timestamp
expected NIGHT BAS_DD
preceding eligible DAY
HTTP
returned BAS_DD inventory
raw rows
candidate rows
ready products
contract/maturity
rejection reason
raw ref/SHA
```

Also record 08:45 and 09:15 observer results.

Derive only the tightest observed interval:

```text
08:20 unavailable, 08:45 ready → (08:20, 08:45]
08:45 unavailable, 09:15 ready → (08:45, 09:15]
09:15 unavailable → UNKNOWN_WITHIN_HORIZON
```

Set:

```text
NIGHT_FUTURES_TELEMETRY_GAP =
LIVE_EVIDENCE_CAPTURE_PASS / FAIL / NOT_OBSERVED

FAIL_CLOSED_SAFETY =
PASS / FAIL

DEADLINE_VERDICT =
KEEP_CURRENT_DEADLINE /
COLLECT_MORE_NATURAL_EVIDENCE /
BOUNDED_DEADLINE_REVIEW_REQUIRED /
DEADLINE_UNPROVEN
```

Do not change deadline.

---

## 14. KRX 08:05

Review exact observation:

```text
observation ID
scheduled/actual time
role target
target XKRX date
HTTP
provider dates
row counts
eligible rows
readiness
raw refs/SHA
terminal state
duplicates
```

Set:

```text
KRX_0805_ROLE_TARGET_NATURAL =
LIVE_PASS / FAIL / NOT_OBSERVED

KRX_0805_PUBLICATION_READINESS =
<actual state>
```

---

## 15. Price / valuation / ownership regression

Audit actual messages for:

- current-price RR ownership
- support/resistance ownership
- confirmation/invalidation
- fabricated technical level = 0
- current vs historical valuation ownership
- denominator reverse-engineering = 0
- unsafe security basis = 0
- working-capital/flow driven valuation mutation = 0

---

## 16. Production message-quality review

Check:

- deterministic-like prose
- repeated FCF wording
- duplicated next-check/Unknown
- excessive numeric recitation
- rigid template structure
- typed prose skeleton
- data caution clarity

Classify P0/P1/P2.

Do not judge current production against unreleased Free Analyst as a correctness requirement.

---

# Part II — US Open Research fresh holdout

## 17. Holdout execution rule

Run only after the immutable natural US packet is terminal.

Preferred:
consume the previously intended automated holdout if it exists.

Known issue:
Open Research holdout automation registration previously timed out.

If no task exists, this instruction explicitly authorizes **one manual shadow-only holdout execution** using the immutable packet.

This is NOT a production rerun.

Allowed:

```text
immutable natural packet
+
fresh public web research
→ research sidecar
→ Event Attribution
→ Free Analyst
→ Adaptive Renderer
→ shadow message
```

Still forbidden:
- production provider rerun
- Telegram
- production DB/receipt mutation
- main merge

---

## 18. Research cutoff

Set one:

`US_RESEARCH_CUTOFF_KST = <actual timestamp>`

Also persist the matching US market-session context.

Do not add sources discovered after cutoff to the same holdout.

---

## 19. Market-level research

Research only material drivers, potentially:

- S&P 500 / Nasdaq / Russell
- SOX / semiconductor behavior
- breadth / concentration
- equal-weight vs cap-weight where available
- sector rotation
- Treasury / real yields
- dollar
- oil
- VIX
- major macro release
- major next event

Do not fill all categories by force.

---

## 20. Stock-level research selection

Do not deep-research every ticker.

Select material names based on:

- unusual move
- new official event
- earnings/guidance
- thesis-sensitive event
- new warning
- price/flow anomaly
- sector shock

Record selection reason.

Quiet stocks may retain no-research Adaptive output.

---

## 21. Competing hypotheses

For each material cluster test multiple plausible causes:

```text
company-specific catalyst
earnings/guidance
sector/peer event
broad risk-on/risk-off
macro discount-rate channel
positioning/flow if actual evidence exists
mechanical/index effect
unresolved
```

Do not force a cause.

---

## 22. Source hierarchy

Use:

1. issuer official release / IR
2. SEC
3. exchange / regulator
4. Fed / Treasury / BLS / BEA / official stats
5. high-quality major news
6. secondary corroboration
7. low-quality sources as leads only

Low-quality source alone cannot support a confirmed Fact.

---

## 23. Entity / event-time validation

For every research item record:

```text
entity
relationship type
event_at
published_at
retrieved_at
research_cutoff
market_session
causal_time_eligible
```

An event after the price move cannot be used as the cause of that move.

---

## 24. Negative-evidence safety

Allowed:

> 현재 확인한 공식자료와 주요 보도 범위에서는 신규 주문 감소 근거를 확인하지 못했습니다.

Forbidden:

> 주문 감소는 없습니다.

Every negative-evidence statement must preserve:
- search scope
- source classes
- time window
- limitations

Set:

`US_NEGATIVE_EVIDENCE_SAFETY = PASS / FAIL / NOT_OBSERVED`

---

## 25. Deterministic research arithmetic

If research needs:

- breadth ratio
- index contribution
- sector spread
- concentration ratio
- flow concentration

compute deterministically from compatible inputs.

No hidden AI arithmetic.

If inputs are incompatible:
Unknown.

---

## 26. Event Attribution output

For each material cluster create:

```text
observed move
primary hypothesis
secondary hypotheses
weak/rejected hypotheses
supporting evidence
contradicting evidence
negative evidence
unknowns
next confirmation event
```

Set:

`US_EVENT_ATTRIBUTION = PASS / PARTIAL / FAIL / NOT_OBSERVED`

---

## 27. Research + Free Analyst

Pass only validated research sidecar into Free Analyst.

Hard targets:

```text
unsourced external facts = 0
unsupported causality = 0
hidden arithmetic accepted = 0
temporal violations = 0
```

Set:

`RESEARCH_FREE_ANALYST_FACT_BOUNDARY = PASS / FAIL`

---

## 28. Research + Adaptive Renderer

Use existing selector:

```text
DIRECT
→ competing hypotheses / negative-evidence boundary matter

HYBRID
→ primary cause clear, one caveat sufficient

MINIMAL
→ no meaningful research value
```

Set:

```text
RESEARCH_ADAPTIVE_RENDERER = PASS / FAIL
RESEARCH_MATERIAL_INFORMATION_LOSS = 0
```

---

## 29. No-value behavior

If research adds no verified value:

`OPEN_RESEARCH_VALUE_ADD = NO_MATERIAL_VALUE`

Keep the no-research Adaptive message.

Do not invent a story.

---

## 30. US research value-add gate

Set:

`US_RESEARCH_FREE_ANALYST_VALUE_ADD = PASS / NO_MATERIAL_VALUE / FAIL / NOT_OBSERVED`

PASS requires at least one:

- verified company-specific catalyst absent from original packet
- useful market-breadth explanation
- competing-hypothesis discrimination
- safe negative evidence narrowing the cause
- verified next event improving next-check framing
- cross-sectional concentration explaining the move

Article summary alone is not enough.

---

## 31. Exact research comparison bundle

Create:

`docs/reports/20260825-us-fresh-open-research-message-bundle.md`

For researched items include:

```text
NATURAL_PRODUCTION_MESSAGE
FREE_ANALYST_NO_RESEARCH
FREE_ANALYST_WITH_RESEARCH_DIRECT
FREE_ANALYST_WITH_RESEARCH_HYBRID
ADAPTIVE_SELECTED_RESEARCH
```

Mark research variants:

`SHADOW — NOT SENT`

---

## 32. Claim provenance

For every research-derived final sentence persist:

```text
final sentence
→ analysis item
→ support type
→ research evidence refs
→ canonical packet refs if used
→ source tier
```

No private chain-of-thought.

---

## 33. US/KR common-core check

Confirm US uses the same semantic model already validated in KR:

```text
Fact
Interpretation
Negative Evidence
Unknown
Competing Hypotheses
Event Attribution
Free Analyst
Adaptive Renderer
```

US-only data/source gaps should be reported as adapter gaps, not silently filled.

---

## 34. Research source / latency audit

Record:

```text
query count
source count
primary source count
high-quality news count
duplicate source families
research duration
model calls
estimated token usage if available
```

---

## 35. Open Research global gates

Set:

```text
SOURCE_PROVENANCE = PASS / FAIL
ENTITY_TIME_VALIDATION = PASS / FAIL
EVENT_ATTRIBUTION_FACT_BOUNDARY = PASS / FAIL
CAUSAL_ATTRIBUTION_SAFETY = PASS / FAIL
NEGATIVE_EVIDENCE_SAFETY = PASS / FAIL
RESEARCH_FREE_ANALYST_FACT_BOUNDARY = PASS / FAIL
RESEARCH_END_TO_END_SHADOW = PASS / FAIL
```

---

## 36. Previous automation-registration blocker

Previous issue:

`US holdout automation registration timeout`

If today’s manual shadow holdout succeeds:

the architecture correctness blocker is closed.

The tooling issue may be reclassified separately as P2 only if:
- US architecture works
- no production impact
- manual shadow holdout completed
- repeat automation is not required for immediate correctness

Do NOT claim the automation backend itself is fixed.

---

# Part III — Combined decision

## 37. Candidate gates

Set independently:

```text
PRODUCTION_CORE_NATURAL_READY = YES / NO

FREE_ANALYST_ADAPTIVE_PRODUCTION_CANDIDATE = YES / NO

OPEN_RESEARCH_PRODUCTION_CANDIDATE = YES / NO
```

No promotion in this task.

---

## 38. Promotion prerequisites

Free Analyst + Adaptive can become a separate production-integration candidate only if:

```text
OPEN_P0 = 0
OPEN_MATERIAL_P1 = 0
US_PRODUCTION_NATURAL = LIVE_PASS
US_AI_COMPATIBILITY_NATURAL = LIVE_PASS or safely explained
MACRO_TEMPORAL_NATURAL = LIVE_PASS or no material blocker
```

Open Research additionally requires:

```text
US_FRESH_RESEARCH_HOLDOUT = PASS
SOURCE_PROVENANCE = PASS
ENTITY_TIME_VALIDATION = PASS
EVENT_ATTRIBUTION_FACT_BOUNDARY = PASS
CAUSAL_ATTRIBUTION_SAFETY = PASS
NEGATIVE_EVIDENCE_SAFETY = PASS
RESEARCH_END_TO_END_SHADOW = PASS
```

---

## 39. Required reports

Create:

### Production
1. `docs/reports/20260825-us-natural-production-review.md`
2. `docs/reports/20260825-us-natural-sent-message-bundle.md`
3. `docs/reports/20260825-us-ai-compatibility-natural-proof.md`
4. `docs/reports/20260825-us-macro-temporal-natural-proof.md`
5. `docs/reports/20260825-phase9-0e-natural-regression.md`
6. `docs/reports/20260825-inventory-user-visible-natural-proof.md`
7. `docs/reports/20260825-trade-ar-natural-canary-proof.md`
8. `docs/reports/20260825-us-exactly-once-review.md`
9. `docs/reports/20260825-us-price-valuation-regression.md`

### Night / KRX
10. `docs/reports/20260825-night-futures-natural-review.md`
11. `docs/reports/20260825-night-futures-natural-review.json`
12. `docs/reports/20260825-krx-0805-natural-review.md`

### Open Research
13. `docs/reports/20260825-us-fresh-research-search-log.md`
14. `docs/reports/20260825-us-fresh-research-evidence.md`
15. `docs/reports/20260825-us-fresh-event-attribution.md`
16. `docs/reports/20260825-us-fresh-open-research-message-bundle.md`
17. `docs/reports/20260825-us-fresh-research-value-add.md`
18. `docs/reports/20260825-us-open-research-causality-safety.md`
19. `docs/reports/20260825-us-open-research-latency-cost.md`

### Combined
20. `docs/reports/20260825-us-morning-multi-proof-gates.md`
21. `docs/reports/20260825-us-morning-multi-proof-artifact-index.md`
22. `docs/reports/20260825-us-morning-multi-proof-summary.json`

---

## 40. Mandatory ZIP

Create:

`20260825-us-morning-natural-and-open-research-multi-proof-bundle.zip`

Include all sanitized reports.

Even if deferred, produce the ZIP.

Report SHA-256.

---

## 41. Gate report

`docs/reports/20260825-us-morning-multi-proof-gates.md`

Must include:

```text
REVIEW_STATE = COMPLETE / DEFERRED_NONTERMINAL

US_PRODUCTION_NATURAL = LIVE_PASS / FAIL
US_AI_COMPATIBILITY_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED
MACRO_TEMPORAL_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED
PHASE_9_0E_NATURAL_REGRESSION = PASS / FAIL / NOT_OBSERVED
INVENTORY_USER_VISIBLE_NATURAL = LIVE_PASS / FAIL / NOT_OBSERVED
TRADE_AR_NATURAL_PROOF = LIVE_PASS / FAIL / NOT_OBSERVED
TRADE_AR_ENABLEMENT_CANDIDATE = ...

NIGHT_FUTURES_TELEMETRY_GAP = ...
FAIL_CLOSED_SAFETY = ...
DEADLINE_VERDICT = ...

KRX_0805_ROLE_TARGET_NATURAL = ...
KRX_0805_PUBLICATION_READINESS = ...

US_FRESH_RESEARCH_HOLDOUT =
PASS / FAIL / NOT_OBSERVED / DEFERRED_NONTERMINAL

US_EVENT_ATTRIBUTION =
PASS / PARTIAL / FAIL / NOT_OBSERVED

US_RESEARCH_FREE_ANALYST_VALUE_ADD =
PASS / NO_MATERIAL_VALUE / FAIL / NOT_OBSERVED

SOURCE_PROVENANCE = PASS / FAIL
ENTITY_TIME_VALIDATION = PASS / FAIL
EVENT_ATTRIBUTION_FACT_BOUNDARY = PASS / FAIL
CAUSAL_ATTRIBUTION_SAFETY = PASS / FAIL
NEGATIVE_EVIDENCE_SAFETY = PASS / FAIL
RESEARCH_END_TO_END_SHADOW = PASS / FAIL

PRODUCTION_CORE_NATURAL_READY = YES / NO
FREE_ANALYST_ADAPTIVE_PRODUCTION_CANDIDATE = YES / NO
OPEN_RESEARCH_PRODUCTION_CANDIDATE = YES / NO

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION = ...
```

---

## 42. NEXT_ACTION policy

Choose the smallest justified action.

Possible:

```text
FREE_ANALYST_ADAPTIVE_PRODUCTION_INTEGRATION
OPEN_RESEARCH_SELECTIVE_PRODUCTION_INTEGRATION
TRADE_AR_ENABLEMENT_INSTRUCTION
US_AI_BOUNDED_REPAIR
MACRO_TEMPORAL_BOUNDED_REPAIR
INVENTORY_BOUNDED_REPAIR
NIGHT_FUTURES_DEADLINE_REVIEW
OPEN_RESEARCH_US_ADAPTER_REPAIR
WAIT_FOR_MORE_NATURAL_PROOF
```

If both AI and Open Research are candidates, prefer sequencing:

1. Free Analyst + Adaptive production integration
2. Open Research selective-trigger integration

unless evidence strongly justifies a combined canary.

---

## 43. Severity

### P0
- wrong delivered Fact/period
- duplicate Telegram / exactly-once failure
- Trade AR leak
- false-current macro claim
- wrong/stale night-futures value
- wrong research entity
- event-after-move treated as cause
- negative evidence stated as certainty
- unsourced external Fact accepted
- hidden arithmetic accepted
- production mutation from shadow research

### P1
- US AI compatibility natural regression
- macro temporal regression
- Inventory factual/causal regression
- price/RR ownership regression
- research causal overclaim
- source provenance loss
- material competing explanation dropped
- US research architecture fails because it is KR-specific

### P2
- harmless AI quality fallback
- Inventory not selected
- Trade AR not observed
- incomplete breadth due free-source limits
- Open Research automation registration tooling issue if manual holdout proves correctness
- query/latency tuning
- renderer preference difference

---

## 44. Completion response

Return:

```text
INSTRUCTION_COMMIT = ...
REVIEW_BRANCH = ...
REPORT_COMMIT = ...

REVIEW_STATE = ...

US_PRODUCTION_NATURAL = ...
US_AI_COMPATIBILITY_NATURAL = ...
MACRO_TEMPORAL_NATURAL = ...
PHASE_9_0E_NATURAL_REGRESSION = ...
INVENTORY_USER_VISIBLE_NATURAL = ...
TRADE_AR_NATURAL_PROOF = ...

EXACTLY_ONCE = ...
DUPLICATES = ...
ORPHANS = ...

NIGHT_FUTURES_TELEMETRY_GAP = ...
DEADLINE_VERDICT = ...
KRX_0805_ROLE_TARGET_NATURAL = ...

US_FRESH_RESEARCH_HOLDOUT = ...
US_EVENT_ATTRIBUTION = ...
US_RESEARCH_FREE_ANALYST_VALUE_ADD = ...

SOURCE_PROVENANCE = ...
ENTITY_TIME_VALIDATION = ...
EVENT_ATTRIBUTION_FACT_BOUNDARY = ...
CAUSAL_ATTRIBUTION_SAFETY = ...
NEGATIVE_EVIDENCE_SAFETY = ...
RESEARCH_END_TO_END_SHADOW = ...

PRODUCTION_CORE_NATURAL_READY = ...
FREE_ANALYST_ADAPTIVE_PRODUCTION_CANDIDATE = ...
OPEN_RESEARCH_PRODUCTION_CANDIDATE = ...

OPEN_P0 = ...
OPEN_MATERIAL_P1 = ...
P2_BACKLOG = ...

NEXT_ACTION = ...

PRODUCTION_MUTATION = 0
TELEGRAM_SEND_FROM_REVIEW = 0

ZIP = ...
ZIP_SHA256 = ...
```

---

## 45. Final principle

Today’s review must separately prove:

```text
1. Did unchanged production run safely?
2. Can shadow research explain why the market moved?
```

The natural production proof must remain uncontaminated.

The research holdout may use the immutable packet plus fresh public research, but it remains shadow-only.

If both pass, the next phase has two distinct production candidates:

- `Free Analyst + Adaptive Renderer`
- `Open Research + Event Attribution`

Each requires separate production-integration work.
