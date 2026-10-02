# Thesis Monitor — R2B-R9-REV13
## OpenDART Header Contract Closure → New Full-Fresh Live Requalification → Fresh Detailed 24-Message Proof

**REV13 supersedes every prior unexecuted R2B-R9 instruction. Execute only REV13.**

REV12-REV2 closed the ECOS preselector and US Market completed-session owner offline.
The only remaining P1 is OpenDART access behavior.

A manual diagnostic using the same Mac mini, same network and same OpenDART credential proved:

- endpoint: official OpenDART `company.json`
- redirects followed: `0`
- retries: `0`
- `Accept: application/json`
- `User-Agent: ThesisMonitor/1.0`
- HTTP status: `200`
- Content-Type: `application/json;charset=UTF-8`
- JSON:
  - `status = "000"`
  - `message = "정상"`

Therefore:
- credential is valid;
- current IP/network is accepted;
- official OpenDART service is reachable;
- the prior `302 → /error1.html` behavior is attributable to the headerless sealed request path, not to a bad API key or unavailable OpenDART account.

REV13 must close this header contract generically, prove `list.json` with the exact sealed OpenDART request semantics, then start a **new** full-fresh proof generation.

Do not reuse the manual diagnostic as current evidence.
Do not reuse REV11/REV12 mutable source rows as current evidence.

No new provider.
No redirect-follow workaround.
No analytical-policy changes.

---

# 0. Newest SoT

Adopt REV12-REV2 as the newest implementation SoT.

Result ZIP SHA-256:

`0711c944662a81a14d9f3d672710d8de3a0b85e347d3d72818dc7389b697c071`

Terminal:

`R2B_R9_REV12_REV2_OPENDART_REDIRECT_ROUTE_UNRESOLVED`

Repository:

- branch:
  `codex/r2b-r9-rev12-rev2-source-bridge`
- base:
  `1f3901daeed1ff6940394477c12b2b0e3bb354b7`
- work-instruction:
  `a050692a5f81714d37f60c78b152d0b8e065970e`
- implementation/final:
  `1a2b5471d0efd86906b30dea640fb1a23c620c74`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

REV12-REV2 validation:

- focused:
  `522 PASS`
- full:
  `6575 PASS / 63 unchanged skips / 0 failures`
- Ruff / diff / Investment Knowledge / Chart Knowledge:
  PASS
- provider calls:
  OpenDART diagnostic `1`
- model calls:
  `0`
- production side effects:
  `0`

Disk:

- closeout free:
  ~`18.87 GiB`
- 10 GiB guard:
  PASS.

Preserve REV12-REV2 ECOS and US Market fixes exactly.

---

# 1. Preserve already-closed contracts

Do not reopen:

- ECOS canonical public/redacted preselector;
- final ECOS strict wire/config binding;
- US Market completed-session selector;
- US Market 22/22 offline replay;
- KOSPI200-only night;
- sealed request descriptor chain;
- UNKNOWN_LIMIT;
- financial direction guard;
- quality semantics;
- valuation semantics;
- event semantics;
- issuer bridge;
- selected Market display;
- detailed stock renderer;
- Core/A/B policy;
- production isolation.

No target fitting.

---

# 2. OpenDART header contract

Add explicit provider-owned request headers to the OpenDART sealed descriptor/transport.

Required headers:

```http
Accept: application/json
User-Agent: ThesisMonitor/1.0
```

These headers are part of the OpenDART request contract.

They must be represented in the descriptor identity in a secret-safe way.

The API credential remains secret and must not be exported.

Do not add browser impersonation or arbitrary additional headers.

Do not follow redirects.

---

# 3. Header identity semantics

For OpenDART descriptors, bind:

- method;
- official host;
- official API path;
- exact business query parameters;
- redacted credential slot/config identity;
- `Accept`;
- `User-Agent`;
- timeout;
- redirect policy;
- retry policy.

The semantic request hash must change if either required header changes.

Negative tests:

- missing Accept → descriptor mismatch/deny;
- missing User-Agent → descriptor mismatch/deny;
- different User-Agent → mismatch unless explicitly versioned in the provider contract;
- wrong Accept → mismatch;
- extra business parameter → deny;
- wrong host/path → deny;
- credential leakage → deny.

---

# 4. OpenDART transport behavior

The transport must send exactly the sealed OpenDART headers.

Redirects remain disabled.

If HTTP 302 still occurs with the exact required headers:

- preserve the existing secret-safe redirect metadata;
- stop:
  `R2B_R9_REV13_OPENDART_HEADER_ROUTE_UNRESOLVED`
- do not follow redirect;
- do not broaden headers;
- do not change provider.

If HTTP 200 occurs:
- require JSON content type or parseable JSON under the existing API contract;
- require documented OpenDART `status/message` semantics;
- proceed according to source result.

A legitimate JSON OpenDART status such as no-data may be handled by existing source semantics.
Do not convert it into transport failure.

---

# 5. One-request list.json diagnostic

After offline tests, run exactly one bounded diagnostic using the actual current `list.json` descriptor semantics.

Use one current monitored KR issuer, preferably the existing 000660 descriptor, only as a representative request.

Required:

- same official `list.json` route;
- same business parameters as the current bounded owner;
- exact sealed headers:
  - `Accept: application/json`
  - `User-Agent: ThesisMonitor/1.0`
- redirects disabled;
- max attempts `1`;
- retries `0`.

This diagnostic is not current proof evidence.

Record only:

- HTTP status;
- Content-Type;
- JSON `status/message`;
- response hash;
- secret-safe redirect metadata if any;
- exact header contract hash;
- no API key.

## Diagnostic success

Accept when:
- HTTP 200;
- JSON parse succeeds;
- OpenDART status/message are source-owned.

`status=000` is normal success.

A documented no-data status may also prove the route/header contract if the exact bounded query legitimately has no data, but the next full proof still requires the normal stock owner to qualify current data as applicable.

## Diagnostic failure

If 302/error page persists:
`R2B_R9_REV13_OPENDART_HEADER_ROUTE_UNRESOLVED`

No full fresh generation.

---

# 6. New full-fresh generation only after diagnostic PASS

Do not resume REV12 diagnostic generation.

Create a new generation.

Recompute:

- actual query time;
- US/KR latest eligible completed sessions;
- all descriptors;
- request budgets;
- OpenDART descriptors including required headers;
- ECOS descriptors;
- US Market descriptors;
- macro;
- event;
- valuation;
- KOSPI200.

Require finite plan.

Alpha Vantage:
`0`

Massive/undeclared fallback:
`0`.

---

# 7. Fresh OpenDART acquisition — all KR8

Run current official OpenDART owner for:

- 000660
- 003690
- 005490
- 005930
- 010120
- 012450
- 047810
- 086280

Every OpenDART request must use the sealed header contract.

Require per subject:

- discovery;
- report/filing selection;
- source receipt;
- current/prior comparison or explicit valid no-comparison;
- field/statement lineage;
- no redirect ambiguity;
- no old DART carry-in.

005930 and 047810 remain mandatory fresh direction-guard controls.

---

# 8. Fresh US14 acquisition

Freshly acquire all current mutable roles for:

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

No old current source reuse.

---

# 9. Fresh US Market

Use the already-closed completed-session owner.

Freshly acquire current selected Market roles.

Require:

- SPY;
- QQQ;
- IWM;
- configured sector/style universe;
- exact latest eligible completed session;
- no promotion of an in-progress row;
- no stale fallback if target session absent.

The REV12 offline 22/22 proof is regression only, not current data.

---

# 10. Fresh KR Market / ECOS / macro / night

KR:

- KOSPI;
- KOSDAQ;
- breadth;
- KOSPI sectors;
- KOSDAQ sectors;
- flows where qualified;
- USD/KRW through repaired ECOS preselector.

Macro:

- FRED;
- EIA;
- source-owned observation periods;
- current/latest-published verification.

Night:

`KOSPI200` only.

No stale cache.

---

# 11. Fresh business/quality/valuation/event/bridge

For all22 produce current-generation:

- financial/business facts;
- comparison applicability;
- event carrier/current eligibility where configured;
- quality;
- CurrentValuationView;
- flow/positioning;
- issuer bridge where needed.

Preserve:

- valid no-comparison → UNKNOWN_LIMIT allowed;
- actual source/lineage failure ≠ UNKNOWN_LIMIT;
- absolute current value alone not directional;
- valuation does not create Overall direction;
- no cross-security valuation transfer.

---

# 12. Source closure

Require:

- stock packets `22/22`;
- Market source `2/2`;
- US completed-session Market roles qualified;
- macro currentness;
- USD/KRW currentness;
- KOSPI200;
- quality all22;
- valuation all22;
- event/bridge current states complete.

Create new:

- FullSourceRunSeed;
- US packet;
- KR packet;
- combined packet;
- authority graph.

No prior current-source hash may fill a current role.

---

# 13. Replay twice

Freeze raw/source corpus.

Disable provider access.

Replay full graph twice.

Require exact semantic equality.

Then:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED=true`

and, with current live role coverage:

`COMPLETE_SOURCE_ADAPTER_QUALIFIED=true`.

Do not inherit qualification flags.

---

# 14. Disk guard before models

Immediately before models:

`free >= 10 GiB`

If not:

`R2B_R9_REV13_DISK_GUARD`

Preserve frozen source corpus.
Do not call models.

---

# 15. Fresh AI

Only after source qualification + disk PASS:

- Market `2/2`
- Core `22/22`
- A `22/22`
- B `22/22`

No old output reuse.
No target fitting.
No source recollection after model stage begins.
No semantic/schema repair.
No fallback/judge/selective rerun.

Use only the current accepted transient transport retry rule.

---

# 16. Final US Market message

`미국 시장 · YYYY-MM-DD`

Display:

1. major selected rows such as SPY/QQQ/IWM with change + %;
2. compact qualified macro values;
3. market judgment + confidence;
4. sector TOP3/BOTTOM3 or honest 자료 부족;
5. KOSPI200 day/week/month.

No KOSDAQ150.

---

# 17. Final KR Market message

`한국 시장 · YYYY-MM-DD`

Display:

1. KOSPI/KOSDAQ judgment;
2. breadth/flow if qualified;
3. KOSPI TOP3/BOTTOM3;
4. KOSDAQ TOP3/BOTTOM3;
5. USD/KRW.

No stale FX.

---

# 18. Final detailed stock messages

Stable user-facing order:

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

Each metric may be:
- qualified;
- N/M;
- 판단 자료 부족.

---

# 19. Exact 24 sender-boundary messages

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

# 20. Human-review bundle

On full PASS create:

`r2b-r9-rev13-fresh-24-message-human-review.zip`

Include:

- exact 24 payloads;
- hashes;
- OpenDART header contract tests;
- list.json one-request diagnostic;
- final provider plan;
- provider actual counters;
- all22 source matrix;
- US/KR Market;
- macro/FX/night;
- financial comparison;
- events;
- quality;
- valuation;
- bridge;
- replay twice;
- fresh Market/Core/A/B ledger;
- validation;
- production isolation.

---

# 21. Production side effects — hard zero

Throughout REV13:

- Telegram send = 0;
- recipient intent = 0;
- production DB writes = 0;
- warning/notification mutation = 0;
- scheduler mutation = 0;
- broker = 0;
- deploy = 0;
- main merge = 0;
- push = 0;
- restart = 0.

---

# 22. Success terminal

Use only:

`R2B_R9_REV13_FULL_FRESH_ALL_SOURCE_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

Require:

1. OpenDART header contract PASS;
2. one-request `list.json` diagnostic PASS;
3. no redirect workaround;
4. new exact provider plan;
5. full new fresh acquisition;
6. stocks 22/22;
7. Market 2/2;
8. US completed-session owner PASS;
9. USD/KRW PASS;
10. KOSPI200 PASS;
11. quality/valuation all22;
12. R7 direction guard PASS;
13. replay twice PASS;
14. adapter qualification PASS;
15. disk guard PASS;
16. fresh Market/Core/A/B;
17. exact final payloads 24/24;
18. message contracts PASS;
19. Alpha/fallback 0;
20. production side effects 0;
21. human-review ZIP generated.

---

# 23. Honest stop terminals

- `R2B_R9_REV13_OPENDART_HEADER_ROUTE_UNRESOLVED`
- `R2B_R9_REV13_DISK_GUARD`
- `R2B_R9_REV13_PROVIDER_PLAN_GAP`
- `R2B_R9_REV13_FULL_FRESH_SOURCE_PARTIAL`
- `R2B_R9_REV13_FRESH_FINANCIAL_SOURCE_PARTIAL`
- exact Market/macro/FX/night blocker
- `R2B_R9_REV13_LIVE_ADAPTER_REQUALIFICATION_GAP`
- exact model/render stage failure.

Do not weaken contracts to bypass a stop.

---

# 24. Validation

## OpenDART headers
- exact Accept;
- exact User-Agent;
- missing header negative;
- wrong header negative;
- semantic hash changes;
- secret scan;
- no redirect follow.

## OpenDART live diagnostic
- list.json 1 request;
- HTTP 200;
- JSON status/message;
- no current-source admission.

## Freshness
- REV11/REV12 mutable source rejected by new generation;
- new receipts only.

## Full pipeline
- KR8 DART;
- US14;
- Market2;
- ECOS;
- macro;
- night;
- quality/valuation/events/bridge;
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

# 25. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum:

- REPORT.md;
- summary.json;
- REV12-REV2 result identity/SHA;
- repository identities;
- changed-file inventory;
- disk guard;
- OpenDART header-contract proof;
- list.json diagnostic receipt;
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
- manifest.

---

# 26. Final principle

The OpenDART endpoint, credential and network are now proven valid under an explicit request-header contract.

REV13 must not follow redirects or redesign source semantics.

It only formalizes the exact header behavior that produced the verified HTTP 200 / status 000 result,
proves the actual `list.json` route with one bounded diagnostic, and then starts a completely new
full-fresh proof generation through the real 24-message human-review boundary.
