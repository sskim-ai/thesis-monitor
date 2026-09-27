# Thesis Monitor — M12DS-R6-R5F-R2B0-R5-REV8
## Live Same-Attempt Full-Source Cohort Acquisition + Composition Closure
### Capture real US/KR mandatory market inputs together with all 22 Class-A stock roles, then build one immutable full-source authority graph

**Purpose:** resolve the exact REV7 blockers:

- `FROZEN_US_MARKET_SOURCE_INPUT_NOT_AVAILABLE`
- `FROZEN_KR_MARKET_SOURCE_INPUT_NOT_AVAILABLE`

REV7 proves 22/22 stock/business source packets but cannot compose a whole-source packet because no compatible frozen mandatory market source receipts exist. REV8 must therefore create a new **real source proof cohort** in which market and stock Class-A inputs belong to the same declared proof generation, bind Class-B exactly once, bind eligible Class-C versions, and then replay the captured cohort offline into the full-source assembler and source-authority graph.

This is still a source-adapter proof task. **Market/Core/A/B/model/render/send remain 0.**

If REV8 PASSes, generate the next **R2B AI-only 24-message dry-run instruction using the sealed REV8 full-source packet with provider calls = 0**. Do not execute R2B in REV8.

---

# 0. Newest accepted SoT

Adopt REV7 as the newest SoT.

REV7 result ZIP SHA-256:

`a3ec25f9ac7a610755aad11c172166332f937d47eb5cc3e952823d902653f323`

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV7_FROZEN_MARKET_SOURCE_INPUT_GAP`

REV7 accepted facts:

- stock source/business packets: `22/22 PASS`
- blocked stock subjects: `0`
- stock cohort SHA-256:
  `654716580f2b3e2e58da56d075946d1fe912eb857b51970d6ff09c4f87836068`
- KRX historical owner replay:
  `PASS_TWICE`
- KRX owner output SHA-256:
  `68991ed322b5d067f46e6d0a1ae4f9151533ff10177e4d31ab61997c39210937`
- acquisition class inventory:
  - A / ATTEMPT_FRESH = `5`
  - B / RUN_FRESH_ONCE = `4`
  - C / VERSIONED_PERSISTED_ALLOWED = `12`
  - D / OPTIONAL_UNAVAILABLE = `3`
  - total roles = `24`
- `NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = false`
- `complete_source_adapter_qualified = false`
- R2B instruction generated = false
- R2B executed = false

Exact REV7 blockers:

## US
role:
`us_market_prices`

blocker:
`FROZEN_US_MARKET_SOURCE_INPUT_NOT_AVAILABLE`

Missing:
- real whole-symbol raw request/response receipts
- exact source time/session
- attempt binding
- non-synthetic raw bodies bound to owner output

## KR
role:
`kr_local_indices_sectors_breadth`

blocker:
`FROZEN_KR_MARKET_SOURCE_INPUT_NOT_AVAILABLE`

Historical parser bytes exist but lack:
- exact original request/page/cursor receipt graph
- compatible attempt/run binding

REV7 result integrity independently rechecked:

- ZIP/sidecar exact
- bundle manifest: `76/76`
- missing: `0`
- hash mismatch: `0`
- size mismatch: `0`
- extra manifest-scope files: `0`

Repository:

- REV7 branch:
  `codex/m12ds-r6-r5f-r2b0-r5-rev7-full-source`
- base:
  `febd3931fe6003f6d3f6f6c61b17607ebc67058a`
- instruction:
  `9a619b25351f726a7071243cd846f6c43e19d098`
- final:
  `b0dc78708f480d591889b40ea9f50707ef1283db`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

Validation:

- focused `942 PASS`
- full `5930 PASS / 63 unchanged skips`
- Ruff/diff/Investment Knowledge/Chart Knowledge/disabled smoke PASS

No provider/model/production side effect occurred in REV7.

---

# 1. REV8 is not historical receipt reconstruction

Do not search more old report roots for compatible market receipts.

Do not splice:

- 2026-09-07 KR market payload
- historical KRX packet
- synthetic US market fixture
- 2026-09-26 stock packet

into a fake common historical run.

REV8 creates one new real acquisition cohort.

---

# 2. Proof mode versus production schedule

REV8 may be executed outside the normal production acquisition window.

It must explicitly classify itself as one of:

## `SCHEDULED_ELIGIBLE_PROOF`

The actual run begins inside an existing valid market acquisition slot and may use the existing production-equivalent attempt timing semantics.

## `AD_HOC_LIVE_SOURCE_PROOF`

The run occurs outside the scheduled production acquisition slot.

Rules:

- actual real provider calls are allowed;
- exact query time is preserved;
- latest eligible/completed source session is determined by existing exchange/session owners;
- no source is relabelled as a scheduled production snapshot;
- no Telegram/model/message/delivery is permitted;
- packet scope must say:
  `LIVE_SOURCE_ADAPTER_PROOF_NOT_PRODUCTION_DECISION`.

Do not spoof the clock to enter a production window.

If a mandatory owner refuses to produce an eligible proof source outside its operational window:
- fail that market honestly;
- do not bypass its temporal validator.

---

# 3. Parent proof generation + market sub-attempts

Create one parent:

`FullSourceProofRun`

with:

- `proof_run_id`
- proof mode
- proof start timestamp
- source policy hash
- 24-role inventory hash
- code/config identity
- US sub-attempt ID
- KR sub-attempt ID
- Class-B acquisition IDs
- Class-C version-set hash

The US and KR markets do **not** need the same trading session date.

They must each be internally coherent.

Example:

- US Class-A market + US14 stock source roles -> one US attempt generation
- KR Class-A market + KR8 stock source roles -> one KR attempt generation

The parent proof binds both.

Do not require US and KR market sessions to be equal.

---

# 4. Current subject universe

## US14

- CORZ
- CPNG
- CRCL
- GOOGL
- HUT
- IBM
- MU
- RXRX
- SKHY
- SNDK
- TSLA
- TSM
- WRD
- WULF

## KR8

- 000660
- 003690
- 005490
- 005930
- 010120
- 012450
- 047810
- 086280

No subject addition/removal.

---

# 5. Current Class-A stock acquisition

Re-acquire the exact current stock source roles for all 22.

Roles:

1. `adjusted_daily`
2. `adjusted_weekly`
3. `adjusted_monthly`
4. `unadjusted_weekly_valuation`

Logical stock-role count:

`22 × 4 = 88`

This is a fresh proof cohort.

Do not reuse the old 88 price receipts as current Class-A values.

The accepted old corpus is only a regression/provenance reference.

---

# 6. Preserve accepted OHLC/anomaly policy

Use the already accepted generic source-integrity policy.

In particular:

- never repair provider values;
- retain row-level anomalies;
- anomaly relevance is consumer-scoped;
- current/latest malformed mandatory row -> role failure;
- historical anomaly outside consumed window -> preserved, non-blocking;
- historical anomaly inside mandatory consumer -> exact component failure.

CPNG historical anomaly semantics must remain unchanged.

No ticker/date exception.

---

# 7. US mandatory market Class-A acquisition

Acquire:

`us_market_prices`

through:

`app.macro.providers.market.OhlcvMarketProvider.collect`

using the actual configured `MARKET_SYMBOLS` registry.

Before network access freeze every configured symbol.

The plan must list:

- registry identity/hash
- symbol
- provider request
- request hash
- logical request ID
- timeout/retry policy
- expected normalized role

Do not hardcode a symbol count in the instruction implementation.

The actual plan must produce:

`US_MARKET_SYMBOL_COUNT = exact integer`

before any request.

All configured required symbols belong to the same US attempt generation.

Partial prior-attempt substitution is forbidden.

---

# 8. KR mandatory market Class-A acquisition

Acquire:

`kr_local_indices_sectors_breadth`

through:

`KiwoomKrMarketContextService.collect`

using the existing declared owner graph, including the exact currently consumed:

- ka20001
- ka20003
- ka20009

and any deterministic page/cursor reads required by the existing owner.

Before network access freeze:

- endpoint/role
- request
- page/cursor bounds
- logical request IDs
- theoretical maximum pages/calls
- request hashes

No request begins if pagination/theoretical maximum is unbounded.

All successful required pages belong to the same KR attempt generation.

No page from a previous attempt.

---

# 9. Optional KR Class-A flow role

Role:

`kr_market_investor_flows`

Owner:
existing ka10051/ka10066 owner.

This role remains optional.

Before network:

- if the owner can produce a finite exact request/page plan, it may be acquired in the KR attempt;
- otherwise bind the existing typed owner denial and do not call it.

Do not allow optional flow acquisition to block an otherwise complete mandatory KR source packet.

No missing-to-zero.

---

# 10. Class-B acquisition — exactly once per proof run

Existing RUN_FRESH_ONCE roles:

1. `news_and_filing_events` — optional, both markets
2. `earnings_calendar` — optional US
3. `us_exchange_breadth` — optional US
4. `night_and_publication_context` — mandatory US

Each planned Class-B owner is invoked at most once per parent proof run.

A Class-A retry must never refresh Class-B.

---

# 11. Mandatory US night/publication context

Role:

`night_and_publication_context`

Owner:

`KrxNightFuturesProvider.collect`

This is mandatory for US source composition.

REV8 must capture a **real current proof-run source receipt**, not reuse the historical REV7 KRX owner packet as the current Class-B value.

Before network freeze:

- product roles
- source endpoints/documents
- publication/session target
- exact logical request plan
- theoretical max
- request hashes

Preserve original overnight publication time.

Do not relabel it as the US price query time.

If current proof time has no eligible night/publication source under the existing owner:
- US proof is incomplete;
- return exact blocker;
- do not use the historical 2026-09-22 owner output as replacement.

---

# 12. Optional Class-B roles

For:

- news/filing events
- earnings calendar
- US exchange breadth

freeze exact finite plans first.

If an optional owner is unavailable or denied:
- produce typed explicit unavailable/denial state;
- continue.

Do not invoke undeclared fallbacks.

Do not broaden event/news queries beyond current owner policy.

---

# 13. Class-C version set

Use the accepted current eligible persisted/versioned source owners.

Roles include:

- universe
- security identity
- stored thesis/business metadata
- SEC financial/fundamental domains
- OpenDART financial/fundamental domains
- canonical cashflow/working-capital
- eligible valuation estimates
- rates/credit/liquidity/risk
- energy
- Korea macro
- central-bank published events
- KR overnight cross-assets

No mandatory external refresh is implied by Class C.

At proof start freeze:

- record IDs
- source/version hashes
- cutoff
- source-use/quality state
- exact eligibility

Produce:

`class-c-version-set.json`
and hash.

Do not choose “latest-looking” rows.

---

# 14. Preserve all REV6/REV7 business evidence semantics

Re-run the complete stock owner using:

- new fresh Class-A price roles;
- current proof-run Class-B evidence where qualified;
- accepted Class-C business/fundamental evidence.

Preserve:

- SKHY same-legal-issuer bridge
- SKHY per-share bridge = false
- SKHY valuation bridge = false
- original 000660 denied fields
- 003690 insurance-revenue semantics
- TSM/WRD accepted foreign statement semantics
- SNDK event authority
- CPNG anomaly contract

The old 22 stock packets are controls, not current price inputs.

---

# 15. Pre-network exact request plan

Before any external request create:

`rev8-full-source-acquisition-plan.json`

and SHA.

It must enumerate every planned external logical request.

At minimum budget sections:

## Stock Class A

- stock roles:
  `88 logical acquisitions`

The underlying owner must additionally freeze actual page/chart transport count.

## US market Class A

- exact `MARKET_SYMBOLS` count
- exact logical calls
- exact theoretical max

## KR market Class A

- exact ka20001/ka20003/ka20009 request/page plan
- exact logical calls
- exact theoretical max

## KR optional flows

- exact plan if attempted
- otherwise typed denial

## Class B

- night/publication exact plan
- event exact plan if attempted
- earnings calendar exact plan if attempted
- Nasdaq breadth exact plan if attempted

No network request may execute if any mandatory planned/theoretical cell is:

- unknown
- null
- unbounded
- derived only after execution begins

---

# 16. Provider budget ledger

Before network, record per provider:

- planned logical requests
- theoretical max logical requests
- planned pagination
- theoretical max pagination
- planned document/chart page requests
- theoretical max document/chart page requests
- retry policy
- theoretical max transport attempts

After execution record:

- actual logical requests
- actual HTTP/provider attempts
- retries
- pagination
- failures
- cap exhaustion

Explicit:

- Alpha Vantage planned = `0`
- Alpha Vantage actual = `0`
- Massive = `0`
- mock = `0`
- undeclared fallback = `0`

The account-wide Alpha budget remains 25/day and must not be consumed here.

---

# 17. Transport policy

For individual source requests:

- timeout: `600 seconds`
- transient retry max: `2`
- total attempts max: `3`
- retry must be byte-identical

Retries permitted only for:

- timeout
- transient transport failure
- connection reset/failure
- provider transient server condition under the existing retry classifier

No retry for:

- identity failure
- schema failure
- semantic failure
- source-use denial
- policy failure
- session/date mismatch
- quality failure
- security mismatch
- period mismatch
- current/latest integrity failure

Every retry consumes declared budget.

---

# 18. Class-A attempt retry semantics

Do not confuse transport retries with full Class-A attempt retries.

## Scheduled proof mode

If running inside an eligible production-like slot, preserve the accepted full-attempt state machine:

### US
- 08:10 initial
- incomplete -> full Class-A recollect 08:15
- incomplete -> full Class-A recollect 08:20

### KR
- 16:00 initial
- incomplete -> full Class-A recollect 16:05
- incomplete -> full Class-A recollect 16:10

A new attempt recollects the **complete Class-A required set for that market**.

No partial patching.

Class B remains frozen from the first run-level acquisition.

## Ad-hoc proof mode

Use exactly **one Class-A attempt per market**.

No five-minute retry simulation.

If mandatory Class-A is incomplete:
- market proof fails;
- preserve exact blocker.

This avoids pretending an ad-hoc execution is a scheduled production cycle.

---

# 19. Market-session ownership

Each market attempt must derive:

- query timestamp
- intended market/session
- completed-session identity where required
- owner temporal verdict

from existing calendar/session logic.

Do not inject an artificial time.

Do not relabel stale response dates.

If the provider returns a session inconsistent with the owner contract:
- fail the role.

US and KR may reference different market dates.

---

# 20. Build current stock packets

After each market's Class-A capture completes:

materialize the relevant current stock packets.

Require:

- US14 packet PASS
- KR8 packet PASS
- exact source refs
- exact new attempt ID
- current price eligibility
- mandatory technical availability
- business evidence eligibility
- packet hash

If one subject fails:
- report it exactly;
- do not silently substitute its old REV6 packet.

REV8 must prove the current acquisition path, not merely keep 22/22 by inherited price data.

---

# 21. Implement the REV7 full-source assembler

REV7 stopped before implementation due missing inputs.

REV8 must now implement and validate:

- `FullSourceRunSeed`
- role generation bindings
- US whole-source packet
- KR whole-source packet
- combined source packet
- source-authority graph

Use repository naming conventions if different.

No separate weaker authority model.

Integrate with the existing `build_source_authority` contract.

---

# 22. FullSourceRunSeed

The seed must bind:

- proof mode
- parent proof run ID
- source policy hash
- acquisition-class inventory hash
- code/config hash
- US attempt ID/hash
- KR attempt ID/hash
- Class-B acquisition IDs/hashes
- Class-C version-set hash
- universe hash
- US14 packet cohort hash
- KR8 packet cohort hash
- KRX night/publication receipt
- optional denial set
- SKHY issuer bridge hash
- source authority contract hash

The seed itself receives a deterministic semantic hash.

---

# 23. US whole-source packet

Must include:

- FullSourceRunSeed reference
- real US market packet
- US14 current stock packets
- mandatory current night/publication context
- retained Class-B optional inputs/denials
- eligible Class-C inputs
- authority graph subset
- US packet SHA

All Class-A values must belong to the same US attempt.

---

# 24. KR whole-source packet

Must include:

- FullSourceRunSeed reference
- real KR local indices/sectors/breadth packet
- KR8 current stock packets
- KR optional flows or explicit denial
- retained run/persisted roles
- authority graph subset
- KR packet SHA

All mandatory Class-A values must belong to the same KR attempt.

---

# 25. Combined full-source authority graph

Every retained consumed fact/role must bind:

`parent proof run`
→ `market sub-attempt or version generation`
→ `role`
→ `owner`
→ `provider`
→ `request/persisted source artifact`
→ `normalizer/projector`
→ `quality/source-use`
→ `market/security/issuer scope`
→ `packet field`

For derived evidence:
- exact input IDs
- derivation owner/version

For SKHY:
- explicit issuer-level bridge remains visible.

No prior AI output, renderer prose, or report prose is a source.

---

# 26. Captured-cohort offline replay

After all source acquisition finishes:

**disable network**.

Then replay the entire captured cohort from raw/source artifacts.

Require:

- current stock materialization replay
- US market owner replay
- KR market owner replay
- Class-B replay
- Class-C version binding
- whole-source composition
- full authority graph

Run composition twice offline.

Hashes must match:

- run seed
- US packet
- KR packet
- combined full-source packet
- authority graph
- 22 current stock packet cohort
- optional denial set

---

# 27. Source-adapter qualification gates

REV8 may set:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`

only when the captured cohort can be replayed without network and all authority/negative gates pass.

Because REV8 also exercised actual current provider acquisition, it may additionally set:

`COMPLETE_SOURCE_ADAPTER_QUALIFIED = true`

only if:

- all mandatory live proof sources were captured by the concrete adapter;
- full source packet/authority graph passes;
- no inherited Class-A value;
- no prohibited provider;
- deterministic offline replay passes.

Do not set this flag merely from offline fixtures.

---

# 28. Mandatory negative controls

At minimum:

## Plan/budget
- unbounded mandatory plan -> no network
- request absent from frozen plan -> fail
- budget overrun -> systemic stop

## Attempt generation
- US market attempt A + stock attempt B -> fail
- KR page from prior attempt -> fail
- old REV6 Class-A packet inserted -> fail
- current stock missing -> fail
- cross-attempt patch -> fail

## Class B
- night context reacquired on price retry -> fail
- wrong run-level acquisition -> fail

## Class C
- record/version after cutoff -> fail
- unowned persisted value -> fail

## Authority
- source hash tamper -> fail
- provider/owner mismatch -> fail
- wrong security/issuer -> fail
- SKHY bridge loss/leakage -> fail

## Optional
- absent optional without explicit denial -> fail
- explicit allowed denial -> pass

## Prohibited
- Alpha admitted -> fail
- Massive/mock admitted -> fail
- undeclared fallback -> fail

## Temporal
- proof timestamp relabelled as scheduled production time -> fail
- US/KR session ownership mismatch -> fail

---

# 29. Non-fail-fast policy

Independent subject/provider work should continue after ordinary subject/source failure so the final result contains the whole blocker set.

Immediate network stop only for systemic:

- auth/security compromise
- plan hash drift
- code/config drift from frozen plan
- secret integrity failure
- provider identity drift
- budget enforcement failure
- undeclared provider/fallback

A single ticker, market symbol, page, optional owner, or semantic rejection is not automatically systemic.

Mandatory market failure may prevent composition for that market but should not discard already captured independent receipts.

---

# 30. Success terminal

If all gates pass:

`M12DS_R6_R5F_R2B0_R5_REV8_LIVE_FULL_SOURCE_COHORT_AUTHORITY_PASS`

Require:

- new real Class-A stock roles captured
- real US mandatory market source receipts
- real KR mandatory market source receipts
- real mandatory night/publication receipt
- current stock packet cohort `22/22`
- full run seed hash non-null
- US whole-source hash non-null
- KR whole-source hash non-null
- combined full-source hash non-null
- authority graph hash non-null
- offline replay twice identical
- `NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`
- `COMPLETE_SOURCE_ADAPTER_QUALIFIED = true`
- provider/model/production policies PASS
- R2B AI-only instruction generated
- R2B execution `0`

---

# 31. Partial terminals

## Mandatory US source failure

`M12DS_R6_R5F_R2B0_R5_REV8_US_LIVE_SOURCE_GAP`

Return exact role/request/attempt/session blocker.

## Mandatory KR source failure

`M12DS_R6_R5F_R2B0_R5_REV8_KR_LIVE_SOURCE_GAP`

## Current stock subject failure

`M12DS_R6_R5F_R2B0_R5_REV8_CURRENT_STOCK_SOURCE_PARTIAL`

Return every failed subject/role.

## Composition/authority gap

`M12DS_R6_R5F_R2B0_R5_REV8_FULL_SOURCE_COMPOSITION_GAP`

Do not recollect after source capture merely because assembler failed.

## Systemic stop

`M12DS_R6_R5F_R2B0_R5_REV8_SYSTEMIC_SOURCE_STOP`

Preserve all completed receipts.

---

# 32. R2B generated on REV8 PASS

On REV8 full PASS, generate an immutable next instruction:

**R2B — Sealed Current-Source AI + 24-Message Dry Run**

Important change:

R2B must use the exact sealed REV8 full-source packet.

Therefore R2B provider calls must be:

`0`

R2B must not recollect the cohort.

It must run the actual existing:

- Market
- Core
- A
- B
- validators
- renderer

against the exact REV8 source packet.

Required message set:

- US market: `1`
- US stocks: `14`
- KR market: `1`
- KR stocks: `8`
- total: `24`

All messages must bind the exact source/run-seed/authority hashes.

If REV8 ran in `AD_HOC_LIVE_SOURCE_PROOF`, R2B messages must be explicitly marked/test-scoped as a dry-run and must not be represented as scheduled production messages.

Telegram/send:
`0`

recipient intent:
`0`

scheduler mutation:
`0`

production DB decision/warning write:
`0`

Package all 24 rendered messages for direct user review.

Do not execute R2B inside REV8.

---

# 33. Production side effects

Hard zero:

- model
- Market/Core/A/B
- renderer
- Telegram
- recipient intent
- production DB decision/warning writes
- scheduler mutation
- notification mutation
- broker
- deploy
- main merge
- push
- restart

Provider calls are allowed only according to the frozen REV8 acquisition plan.

No trading action.

---

# 34. Regression boundaries

Do not redesign:

- current price/OHLCV owner
- CPNG anomaly semantics
- stock technical evidence
- SEC/OpenDART bounded financial owners
- SKHY issuer bridge
- TSM/WRD/003690 semantic fixes
- 22-stock business/source semantics
- investment judgment policy
- Overall/New Buyer/Holder policy
- renderer/message policy
- production schedule/cutover policy

REV8 adds current market+stock cohort acquisition and whole-source composition only.

---

# 35. Validation

Required:

1. acquisition-plan freeze tests
2. provider-budget tests
3. current stock source plan tests
4. US market exact-symbol plan tests
5. KR page/cursor bound tests
6. Class-B once-per-run tests
7. Class-C version-set tests
8. current stock packet `22/22` proof
9. FullSourceRunSeed tests
10. US whole-source composition
11. KR whole-source composition
12. authority graph tests
13. SKHY bridge authority tests
14. prohibited-provider tests
15. attempt/temporal negative controls
16. full captured-cohort offline replay twice
17. previous REV2–REV7 regressions
18. full pytest
19. Ruff
20. `git diff --check`
21. Investment Knowledge
22. Chart Knowledge
23. disabled production entrypoint smoke
24. secret scan
25. no new unexplained skip/xfail

---

# 36. Required result bundle

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- REV7 identity/SHA receipt
- repository identities
- changed-file inventory

## Run / plan
- proof-mode receipt
- session/gate receipt
- `rev8-full-source-acquisition-plan.json`
- plan SHA
- provider budget ledger before/after
- code/config/env fingerprints

## Class A
- all 88 new stock role request/source receipts
- exact source body hashes
- US market symbol plan + receipts
- KR market page/cursor plan + receipts
- optional KR flow receipt/denial
- attempt identities

## Class B
- night/publication receipts
- events receipt/denial
- earnings calendar receipt/denial
- exchange breadth receipt/denial
- exact once-per-run proof

## Class C
- `class-c-version-set.json`
- version-set hash
- source-use/quality eligibility matrix

## Current stock packets
- 22 current stock packet matrix
- packet/result hashes
- old-vs-current control matrix
- exact failures if any

## Full composition
- FullSourceRunSeed
- run seed SHA
- US whole-source packet + SHA
- KR whole-source packet + SHA
- combined full-source packet + SHA
- full authority graph + SHA
- source generation matrix
- role binding matrix
- optional denial matrix
- banned-provider exclusion receipt
- SKHY issuer-bridge authority receipt

## Replay
- network-disabled replay #1
- network-disabled replay #2
- deterministic hash comparison

## Outcome
- `NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED`
- `COMPLETE_SOURCE_ADAPTER_QUALIFIED`
- exact blockers if false
- generated R2B instruction ZIP/MD/SHA if PASS
- R2B executed = false

## Safety/validation
- network/provider counters
- model/delivery/scheduler counters
- config/env/DB/scheduler invariance
- focused/full validation
- secret scan
- bundle manifest

---

# 37. Final principle

REV7 proved that old stock and market artifacts cannot honestly be fused into one run.

REV8 must solve that by acquiring the missing real market sources **together with a new full Class-A stock cohort**, then freezing and replaying that cohort as one explicit authority graph.

After that succeeds, AI/message testing should reuse the exact sealed source packet rather than recollecting it.
