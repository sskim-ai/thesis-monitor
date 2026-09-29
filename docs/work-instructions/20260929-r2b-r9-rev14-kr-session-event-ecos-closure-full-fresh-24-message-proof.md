# Thesis Monitor — R2B-R9-REV14
## KR Completed-Session/Filtered-Technical Ownership + Event Wire/Settings + ECOS CYCLE Closure
### Then new full-fresh all-source requalification → replay twice → fresh Market/Core/A/B → exact detailed 24-message proof

**REV14 supersedes every prior unexecuted R2B-R9 instruction. Execute only REV14.**

REV13 successfully closed OpenDART.

Do not reopen:
- OpenDART header contract;
- ECOS secret-safe descriptor preselector;
- US Market completed-session owner;
- sealed provider dispatcher;
- UNKNOWN_LIMIT;
- R7 absolute-current direction guard;
- quality;
- valuation;
- issuer bridge;
- event fresh/persisted semantics;
- selected Market display;
- KOSPI200-only product scope;
- detailed stock renderer;
- Core/A/B policy;
- source-use policy.

REV13 stopped with fresh source partial before models.

The next bounded repair scope is:

1. KR current-session vs completed-session authority and the filtered technical replay contract;
2. US14 Google News exact wire serialization + pre-dispatch failure receipt ownership;
3. KR8 Naver News explicit settings/credential ownership;
4. ECOS KeyStatisticList `CYCLE` → source observation-period ownership, especially required USD/KRW;
5. prove KOSPI200 night typed unavailable can render `자료 부족` without stale fallback when no current verified pair exists.

Only after these contracts PASS may a **new** full-fresh generation start.

No REV13 mutable value may become current REV14 evidence.

---

# 0. Newest SoT

Adopt REV13 as newest implementation/result SoT.

REV13 result ZIP SHA-256:

`88b0e60083aff717201c39a9c82f01b3afa8b898608ab28f7d463f50c8ef8baa`

Sidecar:
exact match.

Independent bundle checks:

- ZIP CRC:
  PASS
- manifest entries:
  `7417`
- missing:
  `0`
- hash mismatch:
  `0`
- size mismatch:
  `0`
- extra:
  `0`

Terminal:

`R2B_R9_REV13_FULL_FRESH_SOURCE_PARTIAL`

Repository:

- branch:
  `codex/r2b-r9-rev13-opendart-header`
- base:
  `1a2b5471d0efd86906b30dea640fb1a23c620c74`
- instruction:
  `46c965235652826f4ca68f9e1b7204225d764ef9`
- implementation/final:
  `9b4a5cfc5b9ab8ac4351d904a9394858cbb65ebc`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

REV13 validation:

- focused:
  `542 PASS`
- full:
  `6595 PASS / 63 unchanged skips / 0 failures / 0 errors`
- Ruff:
  PASS
- git diff --check:
  PASS
- Investment Knowledge:
  PASS
- Chart Knowledge:
  PASS
- production side effects:
  `0`

REV13 live generation:

`rev13-live-20260929T002911Z`

Frozen sessions:

- KR:
  `2026-09-28`
- US:
  `2026-09-28`

Fresh provider attempts:

- full-fresh:
  `524`
- OpenDART diagnostic:
  `1`
- transient retries:
  `0`

All 524 full-fresh HTTP attempts returned 200.
This is capture success, not canonical source qualification.

Models:
`0`

Final messages:
`0/24`

Disk at closeout:
~`18.975 GiB` free.

---

# 1. REV13 OpenDART is closed

Preserve exactly.

REV13 proved:

- sealed headers:
  - `Accept: application/json`
  - `User-Agent: ThesisMonitor/1.0`
- redirects:
  `0`
- one diagnostic `list.json`:
  HTTP `200`, JSON status `000`
- full-fresh OpenDART attempts:
  `40/40 HTTP 200`
- KR8:
  current/prior filing + CFS/OFS source bodies captured
- second discovery slots:
  `NOT_SELECTED` where not needed, not missing failures.

Do not revisit OpenDART in REV14 except regression.

The separate older two-route diagnostic with headerless requests is historical diagnostic only:
both `list.json` and `company.json` were `302 /error1.html`.
It is superseded by REV13's verified header contract.

---

# 2. REV13 explicit blockers

REV13 reported exactly three P1s:

## 2.1 KR_COMPLETED_SESSION_AND_FILTERED_TECHNICAL_OWNERSHIP

At query time ~09:32 KST:

- target completed KR session:
  `2026-09-28`
- raw KR daily OHLCV for every KR8 contains:
  `2026-09-29` later/current-session row
- target row:
  `2026-09-28`
  is also present.

For each KR8:
- raw daily rows:
  `1000`
- target present:
  `true`
- later-than-target:
  `["2026-09-29"]`.

The first exact whole-source failure:

`technical_component_fact_parity_mismatch:daily`

For 000660:
- component owner filtered the daily technical facts to `0`;
- replay owner retained unfiltered `78`;
- weekly:
  `78/78`
- monthly:
  `78/78`.

KR Market current TR also represented 2026-09-29 intraday while frozen target was 2026-09-28 and existing current/historical equality logic failed.

## 2.2 US_EVENT_WIRE_SERIALIZATION_AND_FAILURE_RECEIPT

For all US14:

- provider:
  `google_news_rss`
- planned:
  `14`
- actual HTTP attempts:
  `0`
- parsed query pairs:
  equal
- headers:
  equal
- URL bytes:
  unequal
- strict wire:
  unequal.

A pre-dispatch exact-slot denial occurred.

Then a finally/normalization path tried to read a response receipt that did not exist and produced `FileNotFoundError`, obscuring the original wire denial.

## 2.3 KR_EVENT_EXPLICIT_SETTINGS_OWNERSHIP

For KR8:

- provider:
  `naver_news`
- planned:
  `8`
- actual HTTP attempts:
  `0`.

Operating `.env` had credentials, but `fetch_events()` used ambient `get_settings()` rather than the explicit provider/collector settings instance.

No credentials were copied into the worktree or result bundle.

Preserve that safety.

---

# 3. Additional latent blocker found during independent review — ECOS CYCLE ownership

REV13 fresh ECOS request itself succeeded:

- planned:
  `1`
- actual:
  `1`
- HTTP:
  `200`.

The raw `KeyStatisticList` already contains source-owned periods.

Example required user-facing FX row:

```json
{
  "CLASS_NAME": "환율",
  "KEYSTAT_NAME": "원/달러 환율(종가)",
  "DATA_VALUE": "1365.1",
  "CYCLE": "20260928",
  "UNIT_NAME": "원"
}
```

Yet `phase-ecos.json` returned:

`USDKRW: source_observation_period_unavailable`

and zero canonical observations.

This is a parser/owner mismatch.

Do not add another ECOS endpoint or another FX provider.

Fix the already-captured `CYCLE` ownership generically.

---

# 4. P1-A — one completed-session EligibleBarSet owner

Do not edit raw OHLCV.

Create one canonical session-filtered bar-set owner, repository naming permitting:

`EligibleCompletedSessionBarSet`

Inputs:

- exact raw D/W/M source receipts;
- exchange calendar;
- frozen target completed session;
- security identity;
- adjustment basis;
- frequency.

For a completed-session proof:

- daily rows later than the frozen completed target are `OUT_OF_SCOPE_CURRENT_OR_FUTURE_SESSION`;
- target and prior eligible rows remain;
- no row date is relabelled;
- no current 9/29 row may affect 9/28 completed-session technicals.

The canonical eligible bar set must be the **single input** for:
- technical indicator computation;
- technical component construction;
- replay reconstruction;
- source/fact parity checks.

Do not compute indicators on an unfiltered series and then merely hide the resulting facts.

Filter eligible bars **before** indicator computation.

---

# 5. D/W/M technical semantics under a completed target

For ad-hoc execution during an open KR session:

target:
latest eligible completed session.

Daily:
use bars `<= target`.

Weekly/monthly:
derive/consume period bars only from source data eligible through the target session.

If a weekly/monthly bar is incomplete as of the target:
- preserve its provisional status where the existing technical contract allows it;
- it must still be based only on data `<= target`.

Never include the live 9/29 row when the target is 9/28.

Do not change the user-facing distinction between:
- completed technical levels;
- provisional current weekly/monthly Bollinger values.

For this completed-session proof, a “provisional” period may be provisional **as of the frozen target**, not as of the later query-time intraday row.

---

# 6. Technical parity contract

Both live component and replay must consume the same exact eligible bar-set hash.

Add receipt fields:

- raw corpus SHA;
- target session;
- excluded row dates;
- included row dates/range;
- eligible bar-set SHA;
- technical input SHA;
- technical fact-set SHA.

Require for all KR8:

- daily parity;
- weekly parity;
- monthly parity.

No `0 vs 78` asymmetry.

Negative tests:

- later current-session row included by replay only → fail;
- later row included by component only → fail;
- target missing → fail closed;
- target relabel → fail;
- adjustment basis mismatch → fail;
- different bar-set hash → fail.

No ticker-specific branch.

---

# 7. KR Market completed-session role separation

Do not require a current/intraday TR value to equal the prior completed-session historical value.

Define explicit roles:

- `KR_CURRENT_SESSION_INTRADAY`
- `KR_COMPLETED_SESSION`

or repository-equivalent.

In `AD_HOC_LIVE_REQUALIFICATION` while KR market is open:

- final proof target is the latest completed session;
- current/intraday 9/29 rows may be captured but are not authority for the 9/28 completed-session market message;
- completed-session index facts must come from an existing qualified historical/completed-session owner;
- the current-session row must not cause a false mismatch merely because it differs from the target completed session.

No date relabel.

No current value copied into prior session.

---

# 8. KR Market mandatory/optional display ownership

For the frozen completed-session target:

Mandatory:
- KOSPI/KOSDAQ completed-session direction/context;
- USD/KRW required by the final KR Market message.

Venue sector ranking:
- KOSPI TOP3/BOTTOM3 when same-session qualified;
- KOSDAQ TOP3/BOTTOM3 when same-session qualified;
- `자료 부족` is allowed per venue when the current approved source genuinely cannot produce a qualified completed-session sector universe.

Breadth/flows:
- render only if qualified.

Do not force an intraday sector/flow snapshot into the previous completed session.

---

# 9. P1-B — one Google News request serialization owner

Current failure proves semantic query equality but wire-byte inequality.

Do not weaken strict wire checking.

Instead eliminate dual serialization.

Create one request serializer used by both:

- sealed descriptor generation;
- actual provider request.

The provider must execute the exact request produced by the accepted descriptor/serializer.

The request contract should bind:

- method;
- base route;
- ordered query pairs or an explicitly canonical ordering;
- encoding rules;
- headers;
- timeout;
- generation;
- role.

Queries include punctuation/quotes and must have deterministic encoding.

Do not compare two independently re-serialized URLs.

---

# 10. Google News wire regression

Use offline fixtures including:

- quotes;
- commas;
- spaces;
- ampersand;
- plus;
- non-ASCII company name where current owner supports it.

Require:

`descriptor canonical wire == provider executed wire`

exactly.

Negative:

- reordered params when order is semantically bound → deny;
- different percent-encoding → deny;
- added param → deny;
- missing param → deny;
- changed query → deny;
- wrong generation → deny.

No Google News network call required for the offline repair proof.

---

# 11. Preserve original pre-dispatch denial receipt

Current finally path masks the actual exact-slot denial because no response receipt exists.

Introduce a typed pre-dispatch terminal receipt, e.g.:

`PRE_DISPATCH_DENIED`

Required fields:

- descriptor/request hash;
- denial code;
- failing field;
- provider;
- generation;
- timestamp;
- HTTP attempts:
  `0`;
- response receipt:
  explicitly `NOT_CREATED`.

Normalizer/finalizer must consume this terminal receipt rather than attempt to open a nonexistent response file.

Do not transform pre-dispatch denial into:
- no-event success;
- provider empty result;
- HTTP failure.

Preserve the original root cause.

---

# 12. Valid Google News no-result semantics

After actual dispatch:

If the provider returns a valid HTTP response with zero qualified events:
- create a real response receipt;
- normalize to the existing explicit no-event/current-eligibility state if policy permits.

This is distinct from:
- pre-dispatch denial;
- transport failure;
- parser failure.

Do not fabricate an event to complete the packet.

---

# 13. P1-C — explicit Naver settings ownership

Current fetch path must not call ambient/global `get_settings()` when the provider instance already owns operating settings.

Refactor generically so the fetch owner receives/uses explicit settings from the provider/collector instance.

Required:

- provider settings identity bound before request;
- Naver client ID/secret presence checked;
- secret values never exported;
- descriptor config identity binds to the same settings source;
- actual transport uses that same settings owner.

Do not:
- copy `.env`;
- write credentials into worktree;
- write secrets into result artifact;
- mutate global environment to make the test pass.

---

# 14. Naver settings regression

Offline tests:

- explicit valid settings → request may be constructed;
- absent credentials → pre-dispatch typed denial;
- ambient global missing but explicit provider settings valid → PASS;
- explicit provider settings mismatch descriptor config identity → deny;
- wrong host/query → deny;
- secret scan → no leakage.

Then the new full-fresh generation may execute the normal KR8 event descriptors.

---

# 15. P1-D — ECOS KeyStatisticList CYCLE parser

Use `CYCLE` as the source-owned observation period for `KeyStatisticList` rows.

Do not substitute:
- query time;
- retrieval time;
- current date.

Implement a generic period parser.

At minimum recognize source shapes already present in the fresh response:

- `YYYYMMDD`
- `YYYYMM`
- `YYYYQn`
- `YYYY`

Retain:
- original raw cycle string;
- parsed period/granularity;
- source row identity;
- retrieval time;
- query time separately.

Malformed/ambiguous cycle:
deny the observation.

---

# 16. ECOS exact row ownership

Use exact KeyStatistic row matching under the existing source registry.

Required user-facing FX role:

`USD/KRW`

Current fresh row:

- class:
  `환율`
- key:
  `원/달러 환율(종가)`
- value:
  `1365.1`
- cycle:
  `20260928`
- unit:
  `원`

Do not hardcode the value/date.

Regression must prove the parser would produce:

- observation period/date:
  `2026-09-28`
- raw cycle:
  `20260928`
- value from the fresh response;
- current/latest-published evaluation under existing policy.

Also fix period ownership generically for other exact matched KeyStatistic rows such as:
- BOK base rate;
- M2;
when the current source registry consumes them.

Missing/ambiguous KeyStatistic such as an unmatched CPI row remains unavailable.
Do not fuzzy-match.

---

# 17. USD/KRW currentness gate

After fresh ECOS read:

Require:
- source row exact match;
- source-owned `CYCLE`;
- parsed observation period;
- fresh retrieval receipt;
- latest/currentness status.

For a completed KR session, a row with cycle equal to the target completed date may qualify under the current product contract.

If the fresh response lacks a qualified USD/KRW period:
stop with an exact FX source blocker.

No stale cache.
No alternate provider.

---

# 18. KOSPI200 night typed-unavailable acceptance

REV13 fresh KRX night capture:

- requests:
  current bounded owner completed;
- 2026-09-28:
  rows existed but no verified NIGHT/preceding-DAY pair;
- latest verified NIGHT pair found in available corpus was stale prior reference;
- owner correctly refused stale promotion.

Preserve this.

The user-facing contract explicitly allows:

`자료 부족`

for unavailable D/W/M horizons.

Therefore prove the whole-source/Market/display path can accept a typed state such as:

`UNAVAILABLE_NO_CURRENT_VERIFIED_PAIR`

without:
- using 9/23 as current;
- inventing a return;
- failing the whole market solely because the optional night display is unavailable.

If the existing contract already supports this state, add only proof/regression; do not redesign it.

---

# 19. Repair-only offline gate

Before new provider calls require:

- KR completed-session role separation PASS;
- KR8 eligible bar-set + D/W/M technical parity PASS using REV13 raw fixtures;
- Google News serializer/wire equality PASS;
- pre-dispatch denial receipt preservation PASS;
- Naver explicit settings ownership PASS;
- ECOS CYCLE parser PASS using REV13 raw ECOS body;
- USD/KRW exact row ownership PASS;
- KOSPI200 typed unavailable → `자료 부족` path PASS;
- focused/full tests;
- Ruff;
- diff;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

Then freeze code.

Do not hotfix after the new generation starts.

---

# 20. New REV14 full-fresh generation

Do not resume or promote REV13 receipts.

Create a new generation.

Recompute:

- actual query time;
- exchange calendars;
- latest completed US session;
- latest completed KR session;
- all sealed descriptors;
- event descriptor wires;
- provider config identities;
- request budgets.

Alpha Vantage:
`0`

Massive/undeclared fallback:
`0`

No old current mutable value.

---

# 21. Fresh all22 acquisition

Run all current roles for US14 + KR8.

No complete-control exemption.

Fresh:

- price/OHLCV;
- technical from target-eligible bar sets;
- financial/business;
- event acquisition/current eligibility;
- quality;
- valuation;
- flow/positioning;
- bridge if required.

OpenDART header contract from REV13 remains mandatory.

---

# 22. Fresh US14 event acceptance

For each US subject:

- one exact serializer owner;
- descriptor/executed wire exact;
- provider attempt/response receipt if dispatched;
- normalized event/no-event current state;
- no pre-dispatch failure masked by FileNotFoundError.

Do not require a positive event headline.
Require an owned source state.

---

# 23. Fresh KR8 event acceptance

For each KR subject:

- provider explicitly owns settings;
- descriptor settings identity matches;
- if dispatched, response receipt exists;
- normalized event/no-event state owned;
- no ambient settings ambiguity.

No secret export.

---

# 24. Fresh KR technical/market acceptance

For every KR8:

- raw current query rows preserved;
- completed target present;
- eligible bar set excludes later live row;
- daily/weekly/monthly technical component/replay parity PASS.

For KR Market:

- current/intraday facts remain separately typed;
- completed-session final market message uses completed-session facts;
- no false current-vs-historical equality requirement.

---

# 25. Fresh ECOS / KR FX

Fresh ECOS request.

Require USD/KRW:
- exact row;
- exact source cycle;
- parsed observation date/period;
- currentness;
- display eligibility.

No query-time-as-observation-time.

---

# 26. Fresh US Market / macro / night

Preserve already-closed US completed-session owner.

Fresh:

- major indices/proxies;
- sector universe;
- FRED/EIA;
- KOSPI200 night.

KOSPI200:
- if current verified pair exists, render qualified horizons;
- otherwise typed unavailable → `자료 부족`;
- never stale-promote.

---

# 27. Full source closure

Require:

- stock packets:
  `22/22`
- Market source:
  `2/2`
- financial/event role ownership complete;
- quality all22;
- valuation all22;
- KR completed-session technical parity;
- USD/KRW qualified;
- macro currentness;
- KOSPI200 qualified or typed unavailable under accepted display contract.

Create new:

- FullSourceRunSeed;
- US whole-source packet;
- KR whole-source packet;
- combined packet;
- authority graph.

---

# 28. Replay twice

Freeze the new source corpus.

Disable provider access.

Replay entire graph twice.

Require exact semantic equality for:
- 22 stock packets;
- technical components;
- events;
- quality;
- valuation;
- US Market;
- KR Market;
- macro;
- night typed state;
- US/KR/combined packets;
- authority graph.

Then:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED=true`

and, when current live role coverage is complete:

`COMPLETE_SOURCE_ADAPTER_QUALIFIED=true`.

---

# 29. Disk guard

Immediately before models:

`free >= 10 GiB`

Otherwise:

`R2B_R9_REV14_DISK_GUARD`

Preserve frozen source corpus.
No models.

---

# 30. Fresh AI

Only after complete source qualification:

- Market `2/2`
- Core `22/22`
- A `22/22`
- B `22/22`

No old model output reuse.
No target fitting.
No source refresh after model execution starts.
No semantic/schema repair.
No fallback/judge/selective ticker rerun.

---

# 31. Final US Market message

`미국 시장 · YYYY-MM-DD`

Display:

- SPY/QQQ/etc major selected roles with change + %;
- compact qualified macro;
- market judgment + confidence;
- sector TOP3/BOTTOM3 or honest `자료 부족`;
- KOSPI200 일/주/월, with `자료 부족` where unavailable.

No KOSDAQ150.

---

# 32. Final KR Market message

`한국 시장 · YYYY-MM-DD`

Display:

- KOSPI/KOSDAQ completed-session judgment;
- breadth/flow only when same-session qualified;
- KOSPI sector TOP3/BOTTOM3 or `자료 부족`;
- KOSDAQ sector TOP3/BOTTOM3 or `자료 부족`;
- USD/KRW with source-owned observation period/currentness.

No intraday/completed mixing.

---

# 33. Final detailed stock messages

Preserve accepted detailed format:

1. optional actual pilot label;
2. company/ticker;
3. AI judgment / balance or UNKNOWN_LIMIT / confidence / evidence maturity / New Buyer / Holder;
4. reevaluation;
5. thesis/risk/market expectation;
6. core judgment;
7. business/earnings;
8. existing warnings;
9. key monitoring;
10. current price structure;
11. flow/positioning;
12. Valuation.

Do not render standalone:

- registered price rules;
- data caution;
- next checks;
- unresolved/unknown.

Valuation section mandatory.

---

# 34. Exact sender-boundary proof

Delivery disabled.

Capture exact:

- MARKET_US;
- MARKET_KR;
- US14;
- KR8;
- ALL_MESSAGES.md.

Total:

`24/24`

No post-hoc reconstruction.

---

# 35. Human-review bundle

On full PASS create:

`r2b-r9-rev14-fresh-24-message-human-review.zip`

Include:

- exact 24 messages;
- hashes;
- KR completed-session/eligible-bar audit;
- KR technical replay parity matrix;
- Google News serializer/wire audit;
- event failure-receipt audit;
- Naver settings-owner audit;
- ECOS CYCLE/USDKRW audit;
- KOSPI200 night availability audit;
- final provider plan/counters;
- all22 source matrix;
- financial/event/quality/valuation;
- Market/macro/FX/night;
- replay twice;
- fresh Market/Core/A/B ledger;
- validation;
- production isolation.

---

# 36. Production side effects

Hard zero:

- Telegram send;
- recipient intent;
- production DB writes;
- warning/notification mutation;
- scheduler mutation;
- broker;
- deploy;
- main merge;
- push;
- restart.

---

# 37. Success terminal

Use only:

`R2B_R9_REV14_FULL_FRESH_ALL_SOURCE_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

Require:

1. REV13 OpenDART regression PASS;
2. KR completed-session role separation PASS;
3. KR8 technical component/replay D/W/M parity PASS;
4. Google News exact serializer/wire ownership PASS;
5. US event owned current state all14;
6. Naver explicit settings ownership PASS;
7. KR event owned current state all8;
8. ECOS CYCLE observation-period owner PASS;
9. USD/KRW currentness/display PASS;
10. KOSPI200 current qualified or accepted typed unavailable/no stale promotion;
11. fresh stocks 22/22;
12. fresh Market 2/2;
13. quality/valuation all22;
14. new full-source graph PASS;
15. replay twice PASS;
16. complete adapter qualification;
17. disk guard PASS;
18. fresh Market/Core/A/B complete;
19. exact final payloads 24/24;
20. user-facing message contracts PASS;
21. Alpha/fallback 0;
22. production side effects 0;
23. human-review ZIP generated.

---

# 38. Honest stop terminals

- `R2B_R9_REV14_KR_COMPLETED_SESSION_OWNER_GAP`
- `R2B_R9_REV14_KR_TECHNICAL_PARITY_GAP`
- `R2B_R9_REV14_US_EVENT_WIRE_GAP`
- `R2B_R9_REV14_KR_EVENT_SETTINGS_GAP`
- `R2B_R9_REV14_USDKRW_OBSERVATION_PERIOD_GAP`
- `R2B_R9_REV14_PROVIDER_PLAN_GAP`
- `R2B_R9_REV14_FULL_FRESH_SOURCE_PARTIAL`
- `R2B_R9_REV14_FRESH_FINANCIAL_SOURCE_PARTIAL`
- exact Market/macro/FX/night source blocker
- `R2B_R9_REV14_LIVE_ADAPTER_REQUALIFICATION_GAP`
- `R2B_R9_REV14_DISK_GUARD`
- exact model/render stage failure.

Do not weaken a validator or reinterpret stale data to bypass a stop.

---

# 39. Required validation

## KR completed-session
- query during open session;
- later live daily row present;
- target completed row present;
- current row excluded before indicator computation;
- D/W/M parity;
- current/historical roles separated;
- no date relabel.

## US events
- one serializer;
- exact wire equality;
- punctuation/quote encoding;
- typed pre-dispatch denial;
- no nonexistent response read;
- valid zero-event response distinct from failure.

## KR events
- explicit provider settings;
- ambient settings absent + explicit valid settings PASS;
- config identity binding;
- missing/mismatched credentials fail closed;
- secret scan.

## ECOS
- CYCLE YYYYMMDD;
- YYYYMM;
- YYYYQn;
- YYYY;
- malformed cycle negative;
- USD/KRW exact row;
- no query-time substitution.

## Night
- current pair positive;
- current pair absent → typed unavailable;
- stale prior row not promoted;
- renderer `자료 부족`.

## Full pipeline
- all22;
- Market2;
- macro/FX/night;
- events;
- replay twice;
- Market/Core/A/B;
- exact24.

## Repository
- focused;
- full pytest;
- Ruff;
- diff;
- Investment Knowledge;
- Chart Knowledge;
- secret scan;
- skip/xfail parity.

---

# 40. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum:

- REPORT.md;
- summary.json;
- REV13 identity/SHA;
- repository identities;
- changed-file inventory;
- disk guard;
- KR completed-session owner proof;
- KR8 technical parity matrix;
- Google News wire serializer proof;
- event denial/response receipt proof;
- Naver settings owner proof;
- ECOS CYCLE/USDKRW proof;
- KOSPI200 availability proof;
- final provider plan;
- actual request receipts;
- all22 source matrix;
- Market/macro/FX/night;
- financial/business/events;
- quality/valuation/bridge;
- replay twice;
- adapter qualification;
- fresh Market/Core/A/B;
- exact24;
- human-review ZIP/SHA;
- validation;
- production isolation;
- secret scan;
- bundle manifest.

---

# 41. Final principle

REV13 proves OpenDART is no longer a blocker.

REV14 must not redesign investment semantics.

It closes the remaining source ownership boundaries exposed by a real fresh run:

- completed-session data must be computed from completed-session eligible bars, not merely hidden after using an intraday row;
- event requests must have one exact serialization/settings owner and preserve the true pre-dispatch failure cause;
- ECOS must use the source's own `CYCLE` as observation time;
- unavailable night futures may be honestly shown as `자료 부족`, never replaced by stale data.

After those boundaries close, a new fresh generation must proceed all the way to the real 24-message human-review boundary.
