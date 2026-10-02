# Thesis Monitor — R2B-R9-REV12-REV2
## OpenDART HTTP-302 Route Closure + ECOS Secret-Safe Preselector Repair + US Market Native Completed-Session Bridge Closure
### Then new full-fresh live generation → replay twice → fresh Market/Core/A/B → exact detailed 24-message proof

**REV12-REV2 supersedes REV12 and every prior unexecuted R2B-R9 instruction. Execute only REV12-REV2.**

REV11 successfully completed the sealed dispatcher/provider-plan layer and entered a real fresh provider generation.

Do not reopen analytical/product contracts.

The REV11 result has two explicit P1s and one additional latent Market integration blocker that is already visible in the captured evidence:

1. all KR8 OpenDART discovery requests returned HTTP 302 with redirect following intentionally disabled;
2. ECOS candidate preselection compares the credential-bearing raw URL path against a redacted descriptor path before the already-proven canonical public wire comparison;
3. all 22 US Market sealed descriptors, including SPY/QQQ/IWM/sector symbols, returned HTTP 200, but the current native `OhlcvMarketProvider` consumer produced `ValueError` for every symbol and zero Market observations.

A separate operational prerequisite exists:

4. free disk was ~7.75–7.77 GiB, below the existing 10 GiB model-execution guard.

REV12-REV2 closes only the three source/transport/bridge issues above, verifies the disk guard, then starts a **new** full-fresh proof generation.

REV11 captured sources may be used as offline diagnostic/regression fixtures only.
They must not be carried into the new current source graph.

No old model output may be reused.
No new provider may be introduced.
No source/decision validator may be weakened.

---

# 0. REV11 SoT

REV11 result ZIP SHA-256:

`6394d2aeafe294e010bcccc0b7a6c688d9cdd300f293600e94ed4353be0ecdaa`

Terminal:

`R2B_R9_REV11_FRESH_FINANCIAL_SOURCE_PARTIAL`

Repository:

- branch:
  `codex/r2b-r9-rev11-sealed-dispatcher`
- base:
  `e419371e05e0aabb18d651be6da5b98a9ea2375c`
- instruction:
  `fe909d26f47ee232cb986ddae7d2e86d724876cb`
- implementation/final:
  `1f3901daeed1ff6940394477c12b2b0e3bb354b7`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

REV11 provider plan:

- descriptor count:
  `895`
- theoretical maximum transport attempts:
  `2641`
- `live_dispatch_allowed=true`
- plan SHA:
  `f49f938c8ed4d086209e9d7a17659964a59653fe8f95447792b2a2dca36e75f0`

Actual REV11:

- HTTP attempts:
  `455`
- transient retries:
  `0`
- model calls:
  `0`
- exact payloads:
  `0/24`
- production side effects:
  `0`

Captured successes:

- stock OHLCV roles:
  `88/88` raw capture + native parser replay PASS
- Kiwoom:
  `358` HTTP 200 attempts
- SEC:
  `73` HTTP 200 attempts
- FRED:
  `13` PASS
- EIA:
  `3` PASS
- KR pagination:
  KOSPI `14 pages / 1,306 rows / complete`
  KOSDAQ `19 pages / 1,821 rows / complete`

Explicit failures/stops:

- OpenDART:
  `8 × HTTP 302`
- ECOS:
  `0` external calls due safe preselector stop
- KRX night/events/models:
  not reached.

Additional US Market observation:

- sealed logical requests:
  discovery ND/NY/NA + 22 Market symbols all `PASS/HTTP 200`;
- raw SPY body contains source rows including `2026-09-28` in-progress/current row and `2026-09-25` completed row;
- `phase-us-market.json`:
  `observations=[]`;
- warnings:
  every configured Market symbol → `ValueError`;
- current worker suppresses the specific internal cause to only the exception class.

This is not yet a qualified Market source.

---

# 1. Preserve accepted REV11/REV10 contracts

Do not change:

- sealed request descriptor semantics;
- descriptor→attempt→raw→normalization→role binding;
- current all22 source semantics;
- UNKNOWN_LIMIT;
- quality;
- valuation;
- issuer bridge;
- event semantics;
- R7 absolute-current direction guard;
- selected Market display contract;
- KOSPI200-only night;
- detailed stock renderer;
- Core/A/B policy;
- source-use policy;
- production isolation.

No target fitting.

---

# 2. Disk prerequisite

REV11 observed approximately:

`7.75–7.77 GiB free`

Existing model guard:

`10 GiB`

Before a new full-fresh generation, record:

- total;
- used;
- free bytes;
- guard threshold.

Required at minimum immediately before model execution:

`free >= 10 GiB`.

Prefer requiring the same before the new provider generation begins so the source corpus is not rebuilt while downstream execution is already impossible.

REV12-REV2 must not delete user files automatically.

If free space remains below the required guard:

`R2B_R9_REV12_REV2_DISK_GUARD`

No new full-fresh proof.

---

# 3. P1-A — retain secret-safe redirect metadata

REV11 OpenDART failed with:

- HTTP 302;
- empty body;
- empty stored response headers.

The system correctly did not follow redirects, but cannot diagnose the official route safely.

Modify the sealed transport so non-2xx/redirect receipts retain an allowlisted, secret-safe redirect metadata object.

At minimum:

- status;
- canonical/redacted `Location` host;
- canonical/redacted `Location` path;
- query key names without values;
- same-origin result;
- scheme relation;
- `Content-Type`;
- non-secret request/correlation header if useful.

Never persist:

- cookies;
- Authorization;
- API key;
- credential-bearing raw Location;
- secret query values.

Create an exact typed `SecretSafeRedirectMetadata` or repository equivalent.

---

# 4. One-request OpenDART diagnostic generation

After offline tests, perform exactly one diagnostic request outside the final proof generation.

Use one existing KR monitored request descriptor, preferably 000660 discovery, because it is already an existing generic owner case.

Rules:

- exact existing request semantics;
- redirects disabled;
- one request;
- no result broadening;
- capture secret-safe redirect metadata;
- diagnostic output cannot enter final source graph.

Classify:

## A. Direct HTTP 200

No redirect policy needed.
Use the same official route in the final plan.

## B. HTTP 302 with safely provable deterministic same-origin canonical target

Only acceptable if all are proven:

- official OpenDART trust domain;
- no scheme downgrade;
- same API operation;
- same corp/date/report/page semantics;
- no unplanned extra business query;
- no credential leakage;
- deterministic route.

Preferred repair:
freeze the canonical final official endpoint directly in the new full plan.

Only if direct canonical endpoint is impossible:
allow at most one exact same-origin redirect pattern pre-sealed in the descriptor.

The diagnostic request itself is not current evidence.

## C. Cross-origin/login/ambiguous/changed semantics/secret risk

Stop:

`R2B_R9_REV12_REV2_OPENDART_REDIRECT_ROUTE_UNRESOLVED`

Do not follow.
Do not change provider.
Do not reuse old DART values.

---

# 5. OpenDART negative regression

Require:

- direct 200 positive;
- exact same-origin canonical redirect positive if applicable;
- > allowed redirects denied;
- cross-origin denied;
- scheme downgrade denied;
- operation/path mutation denied;
- corp/date/report/page mutation denied;
- extra query denied;
- secret leakage denied;
- missing/ambiguous Location denied;
- wrong corp_code denied;
- wrong host denied.

No unredacted credential in result bundle.

---

# 6. P1-B — ECOS canonical public preselector

REV11 already proved offline:

- raw credential-bearing path == redacted descriptor path:
  false;
- canonical public/redacted route:
  true;
- canonical public wire identity:
  true;
- ECOS external calls:
  0.

Therefore change only descriptor candidate preselection.

Use the secret-safe canonical public identity for candidate narrowing:

- provider;
- host;
- method;
- operation/path;
- public/redacted credential slot;
- allowed query key set;
- config identity.

After candidate selection, retain the strict final request/config/wire binding.

Do not weaken final descriptor enforcement.

---

# 7. ECOS negative regression

Offline tests:

- correct public route + correct current config → select;
- wrong host → deny;
- wrong operation/path → deny;
- wrong stat/item/cycle → deny;
- wrong date/window → deny;
- missing parameter → deny;
- extra parameter → deny;
- wrong generation → deny;
- wrong config identity → deny;
- malformed credential placement → deny;
- secret value never exported.

No network needed for this repair test.

---

# 8. P1-C — US Market HTTP-200 raw → native owner failure

REV11 captured 25 US Market related sealed requests:

- 3 exchange-discovery;
- 22 Market symbols.

All sealed logical requests are `PASS` with HTTP 200.

Yet the Market consumer returned:

- provider `ohlcv_analyst`;
- observations `[]`;
- all 22 symbol warnings `ValueError`.

This must be closed before a new live generation.

Do not treat HTTP 200 capture as source qualification.

---

# 9. Offline reproduce the exact US Market failure

Use REV11 captured raw bodies/receipts only as offline fixtures.

No network.

At minimum replay:

- SPY;
- QQQ;
- IWM;
- one sector ETF.

Feed the exact captured:

- discovery responses;
- chart responses;
- current native owner version;
- target completed session.

Reproduce through:

`SealedNativeBridge/current worker semantics`
→ `OhlcvService`
→ `OhlcvMarketProvider`

Capture a **secret-safe bounded diagnostic error receipt** with:

- exception class;
- stable error code / failing contract;
- stack location/module/function;
- no request credentials;
- no raw secret-bearing exception string if unsafe.

The current `ValueError` class alone is insufficient.

---

# 10. Completed-session authority for US Market

REV11 actual execution was ad-hoc while the US regular market was open.

Frozen target completed US session:

`2026-09-25`

Captured SPY raw includes:

- `2026-09-28` current/in-progress row;
- `2026-09-25` completed row.

The US Market native owner must not fail merely because a newer in-progress source row exists.

It must also not promote the in-progress row as the completed-session market fact.

Require a generic completed-session selector:

- source raw rows remain immutable;
- target session comes from the frozen exchange calendar;
- select exact target completed session when present;
- later/in-progress rows remain raw context only or are excluded according to current source contract;
- no date relabel;
- no stale fallback to an older session if target row is absent.

If target `2026-09-25` exists in the raw fixture, replay must select it.

This rule must be generic and calendar/session-owned, not SPY-specific.

---

# 11. US exchange-discovery / symbol binding audit

Also verify the captured ND/NY/NA discovery bindings.

For each configured Market symbol prove:

- exact symbol exists in the sealed discovered exchange response;
- selected exchange matches the frozen response-binding policy;
- resolved request SHA matches the selected exchange;
- chart response belongs to that exact logical symbol role.

If the ValueError is due exchange binding rather than session selection:
fix that generic owner instead.

Do not hardcode SPY/QQQ exchange fixes.

---

# 12. US Market offline acceptance

Before new network calls require the full REV11 captured 22-symbol corpus to replay offline.

For all configured Market symbols:

- raw HTTP 200 body parses;
- exact target completed session selected;
- canonical observation created;
- no unexpected ValueError;
- selected session/date/source hash recorded;
- Market source fact binding valid.

Require:

`22/22`

for the current captured fixture set.

This proves parser/bridge/session ownership only.
It does not make REV11 raw data current for REV12.

---

# 13. Repair freeze

After P1-A/B/C offline closure:

- focused tests PASS;
- full pytest PASS;
- Ruff PASS;
- git diff --check PASS;
- Investment Knowledge PASS;
- Chart Knowledge PASS;
- secret scan PASS.

Freeze implementation.

No code/config changes after the final full-fresh generation starts.

---

# 14. New REV12-REV2 provider generation

Do not resume REV11.

Create a completely new generation.

Recompute:

- actual query time;
- current US/KR calendars;
- latest eligible completed sessions;
- all descriptors;
- page/document caps;
- OpenDART route;
- ECOS public identity binding;
- US Market bindings;
- event plans;
- valuation plans;
- KOSPI200 plans.

Require finite exact plan.

Alpha Vantage:
`0`

Massive/undeclared fallback:
`0`

No old mutable current values.

---

# 15. Full fresh all22 acquisition

Run new sealed plan for:

US14:
CORZ, CPNG, CRCL, GOOGL, HUT, IBM, MU, RXRX, SKHY, SNDK, TSLA, TSM, WRD, WULF

KR8:
000660, 003690, 005490, 005930, 010120, 012450, 047810, 086280

Fresh:

- price/OHLCV;
- technical;
- financial/business;
- events per current plan;
- quality;
- valuation;
- flow/positioning;
- issuer bridge when needed.

No REV11 source value is current evidence.

---

# 16. Fresh OpenDART acceptance

All KR8 require successful official owner path.

For each:

- discovery;
- filing/report selection;
- statement/document;
- current/prior or explicit valid no-comparison;
- field/statement lineage;
- current generation receipts.

005930 and 047810 remain mandatory fresh regression subjects.

SKHY issuer bridge can use 000660 only after current-generation 000660 business evidence qualifies.

---

# 17. Fresh US Market acceptance

For every configured selected US Market role:

- sealed descriptor PASS;
- raw parse PASS;
- target completed-session selection PASS;
- canonical observation PASS.

Before Market AI require at minimum:

- SPY;
- QQQ;
- IWM;
- required selected sector universe coverage.

Do not use the current/in-progress row when the product target is a prior completed session.

---

# 18. Fresh KR Market / ECOS / macro / night

Fresh KR:

- KOSPI;
- KOSDAQ;
- breadth;
- KOSPI/KOSDAQ sectors;
- flows where qualified;
- ECOS USD/KRW.

ECOS must pass the repaired preselector and preserve source-owned observation period.

Fresh US macro:

- FRED;
- EIA;
- current selected macro roles.

Fresh night:

`KOSPI200` only.

No stale cache substitution.

---

# 19. Source closure

Require:

- stock packets `22/22`;
- Market source `2/2`;
- US completed-session Market roles qualified;
- macro currentness;
- USD/KRW currentness;
- KOSPI200;
- quality all22;
- valuation all22;
- event/bridge states complete.

Create new:

- FullSourceRunSeed;
- US packet;
- KR packet;
- combined packet;
- authority graph.

---

# 20. Replay twice

Freeze the new raw/source corpus.

Disable provider access.

Replay entire graph twice.

Require exact semantic equality.

Only then set:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED=true`

and:

`COMPLETE_SOURCE_ADAPTER_QUALIFIED=true`

when live role coverage also passes.

---

# 21. Recheck disk before models

Immediately before models:

`free >= 10 GiB`

If not:

`R2B_R9_REV12_REV2_DISK_GUARD`

Preserve the frozen source corpus.
Do not call models.

---

# 22. Fresh AI

After source qualification and disk PASS:

- Market `2/2`;
- Core `22/22`;
- A `22/22`;
- B `22/22`.

No old output reuse.
No target fitting.
No source recollection after models start.
No semantic/schema repair.
No fallback/judge/selective ticker rerun.

---

# 23. Final user-facing messages

Preserve the accepted contract.

## US Market

- major indices/proxies with change + %;
- macro values;
- market judgment + confidence;
- sector TOP3/BOTTOM3 or honest 자료 부족;
- KOSPI200 D/W/M.

## KR Market

- KOSPI/KOSDAQ judgment;
- breadth/flow if qualified;
- KOSPI/KOSDAQ sector TOP3/BOTTOM3;
- USD/KRW.

## Stocks

Detailed format:

- AI judgment/balance/confidence/evidence maturity/New Buyer/Holder;
- reevaluation;
- thesis/risk/expectation;
- core judgment;
- business/earnings;
- existing warnings;
- key monitoring;
- current price structure;
- flow/positioning;
- Valuation.

Do not render standalone:
- registered price rules;
- data caution;
- next checks;
- unresolved/unknown.

---

# 24. Exact sender-boundary capture

Delivery disabled.

Capture exact:

- MARKET_US;
- MARKET_KR;
- US14;
- KR8;
- ALL_MESSAGES.md.

Total:

`24/24`.

No post-hoc reconstruction.

---

# 25. Human-review bundle

On full PASS create:

`r2b-r9-rev12-rev2-fresh-24-message-human-review.zip`

Include:

- exact 24 payloads;
- hashes;
- OpenDART diagnostic + closure;
- ECOS preselector audit;
- US Market offline REV11 replay diagnostic;
- US completed-session selector proof;
- new final provider plan;
- provider actual counters;
- all22 source matrix;
- Market/macro/FX/night;
- financial comparison;
- events;
- quality;
- valuation;
- bridge;
- replay;
- fresh AI ledger;
- validation;
- production isolation.

---

# 26. Production side effects

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

# 27. Success terminal

Use only:

`R2B_R9_REV12_REV2_FULL_FRESH_ALL_SOURCE_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

Requires:

1. OpenDART official route safely resolved;
2. ECOS secret-safe preselector PASS;
3. US Market captured HTTP200→canonical completed-session replay `22/22` PASS;
4. disk guard PASS;
5. new exact provider plan;
6. all mandatory fresh acquisition;
7. stocks 22/22;
8. Market 2/2;
9. US completed-session Market source positive;
10. USD/KRW PASS;
11. KOSPI200 PASS;
12. quality/valuation all22;
13. R7 direction guard;
14. replay twice;
15. adapter qualification;
16. fresh Market/Core/A/B;
17. exact final 24 payloads;
18. message contract PASS;
19. Alpha/fallback 0;
20. production side effects 0;
21. human-review ZIP generated.

---

# 28. Honest stop terminals

- `R2B_R9_REV12_REV2_DISK_GUARD`
- `R2B_R9_REV12_REV2_OPENDART_REDIRECT_ROUTE_UNRESOLVED`
- `R2B_R9_REV12_REV2_ECOS_PRESELECTOR_GAP`
- `R2B_R9_REV12_REV2_US_MARKET_NATIVE_OWNER_GAP`
- `R2B_R9_REV12_REV2_PROVIDER_PLAN_GAP`
- `R2B_R9_REV12_REV2_FULL_FRESH_SOURCE_PARTIAL`
- `R2B_R9_REV12_REV2_FRESH_FINANCIAL_SOURCE_PARTIAL`
- exact Market/macro/FX/night blocker
- `R2B_R9_REV12_REV2_LIVE_ADAPTER_REQUALIFICATION_GAP`
- exact model/render failure.

Do not weaken a contract to bypass a stop.

---

# 29. Validation

## OpenDART
- secret-safe redirect metadata;
- direct route;
- same-origin canonical redirect if applicable;
- cross-origin/secret/query mutation negatives.

## ECOS
- public canonical preselector;
- final exact binding unchanged;
- wrong route/query/config negatives.

## US Market
- REV11 raw offline replay all22;
- exchange discovery binding;
- target completed-session exact selection;
- current/in-progress later row excluded from completed-session authority;
- target missing negative;
- no date relabel;
- no ticker-specific fix.

## Freshness
- REV11 current data rejected by new generation;
- new receipts only.

## Full pipeline
- all22;
- Market2;
- macro/FX/night;
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
- unchanged skip/xfail identity.

---

# 30. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum:

- REPORT.md;
- summary.json;
- REV11 identity/SHA;
- repository identities;
- changed-file inventory;
- disk guard;
- OpenDART redirect metadata/diagnostic/closure;
- ECOS preselector proof;
- US Market REV11 raw offline replay/root-cause;
- completed-session selector proof;
- new provider plan;
- actual request receipts;
- source qualification;
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
- safety;
- secret scan;
- manifest.

---

# 31. Final principle

REV11 already proved the sealed dispatcher and most real-source transport paths.

REV12-REV2 must not redesign the analytical system.

It closes the three concrete live-source integration gaps already visible in REV11 evidence:

- OpenDART 302 official-route ownership;
- ECOS credential-safe descriptor preselection;
- US Market HTTP200 raw data reaching the canonical completed-session owner.

Only after those are proven does a new full-fresh generation begin.
