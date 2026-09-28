# Thesis Monitor — R2B-R9-REV6
## Preflight Contract Closure → Full Fresh All-Source Recollection → Post-R7 Live Requalification → Fresh 24-Message Proof
### KOSPI200-only night scope + explicit Market display selection + true all22 fresh acquisition + source-owned macro dates + restored detailed stock renderer

**REV6 supersedes every prior unexecuted R2B-R9 / REV2 / REV3 / REV4 / REV5 instruction. Execute only REV6.**

R9 preflight proved that network execution must not start yet. Four P1 contracts are open before any provider call:

1. KRX night-futures product scope is still hard-wired to KOSPI200 + KOSDAQ150.
2. The accepted Market renderer emits every eligible numeric claim in source order instead of the explicitly required user-facing display blocks.
3. The old all-source controller imports persisted macro and parent business/quality artifacts and is not a true all22 fresh-generation controller.
4. Macro provider normalization does not consistently preserve the source-owned observation/publication period; ECOS in particular currently substitutes the query `as_of`.

REV6 must close these four contracts **offline first**.
Only after all four preflight contracts PASS may it freeze finite provider budgets and perform the full fresh acquisition.

No comparison ZIP is required.
No previous source packet or model output may fill an R9 role.

---

# 0. Authoritative prior result and runtime

Adopt the R9 preflight-gap result only as diagnostic SoT for the four pre-network gaps.

Result ZIP SHA-256:

`91894cd071a43f7677e1fd26757a26883ca3e0eeac4597d0413676b2fcc9e60c`

Terminal:

`R2B_R9_LIVE_ADAPTER_REQUALIFICATION_GAP`

Accepted diagnostic facts:

- provider requests: `0`
- fresh stock packets: `0/22` — NOT_RUN, not provider failures
- fresh Market contexts: `0/2`
- Market/Core/A/B calls: `0/0/0/0`
- fresh messages: `0/24`
- `COMPLETE_SOURCE_ADAPTER_QUALIFIED = false`
- P0 open: `0`
- P1 preflight gaps: `4`
- runtime executable drift from accepted R7: `0`
- focused: `717 PASS`
- full: `6222 PASS / 63 unchanged skips`
- Ruff / diff / Investment Knowledge / Chart Knowledge: PASS

Preflight branch:

`codex/r2b-r9-full-fresh-requalification`

R9 diagnostic instruction commit:

`da925a96c5f8d905da16ee7daee5cf079db54b9e`

Accepted post-R7 runtime under test:

`174af2b0a0cef373c85a9a27fe22604839c8acf9`

Operating main remains unchanged:

`b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

REV6 may modify runtime code only for the four generic preflight closures and the final renderer contract specified below.

Do not merge main.

---

# 1. Final target of REV6

REV6 has two hard phases.

## Phase A — offline contract closure

Close all four P1 preflight gaps with no provider/model calls.

Required result:

`R9_REV6_PREFLIGHT_CONTRACTS_PASS`

Only then proceed.

## Phase B — full fresh live/ad-hoc generation

Freshly acquire all mutable roles for:

- US market;
- KR market;
- US14 monitored stocks;
- KR8 monitored stocks;
- all current stock price/OHLCV/technical inputs;
- all financial/business inputs;
- all valuation inputs;
- all macro inputs consumed/displayed;
- configured KOSPI200 night context.

Then:
- build a new full source graph;
- replay it offline twice;
- qualify the adapter;
- run fresh Market/Core/A/B;
- render 24 exact final payloads.

No Phase B call is allowed when Phase A is partial.

---

# 2. P1-A — KOSPI200-only night-futures product scope

Current diagnostic conflict:

- product requirement: `KOSPI200`
- current collector/config: `KOSPI200`, `KOSDAQ150`
- `KrxNightFuturesProvider.collect` treats success as exactly two observations;
- probe `TARGET_PRODUCTS` contains both;
- current source/replay contracts expect both.

This must be fixed as a **product-scope contract**, not a renderer hide.

## 2.1 Single product-scope owner

Create one repository-native configured owner for night products.

Current final user product scope:

`KOSPI200`

The product list must be consumed by:

- network collector;
- probe/request planner;
- receipt validator;
- raw/source normalization;
- history owner;
- D/W/M aggregation;
- source role completeness;
- source-authority graph;
- offline replay;
- numeric catalog;
- Market model input;
- final renderer.

No duplicated hardcoded product lists.

## 2.2 Receipt/completeness

Replace:

`len(observations) == 2`

with completeness against the exact configured product set.

For KOSPI200-only:

- one qualified KOSPI200 observation may complete the product role;
- KOSDAQ150 absence is not a denial;
- an unexpected KOSDAQ150 row must not silently become mandatory.

## 2.3 History

The current run must use a new private R9 night-history location.

Build/rebuild KOSPI200:

- daily;
- weekly current period;
- monthly current period;
- included/expected sessions.

Do not copy an old D/W/M result as current.

Historical official KRX rows may be fetched/read as required by the current history owner, with finite request budgets.

## 2.4 Renderer

Final US Market message shows only:

`한국 야간선물 · KOSPI200`

with:
- 일
- 주
- 월

For each unavailable horizon:
`자료 부족`

Do not render KOSDAQ150.

## 2.5 Tests

At minimum:

- configured one product → one valid observation PASS;
- configured one product → zero observation FAIL/unavailable;
- wrong product only → FAIL;
- extra unconfigured product cannot change semantic hash;
- D/W/M with partial history;
- replay exact;
- source-authority product mismatch negative;
- renderer contains no KOSDAQ150.

---

# 3. P1-B — explicit Market internal-facts vs display-selection contract

Current diagnostic conflict:

`daily_digest_renderer`
→ `accepted_calibration_message_service.calibration_market_render`
→ `market_numeric_claim_service.render_typed_market_facts`

renders eligible numeric claims in source order.

That route does not own:
- US/KR explicit sector TOP3/BOTTOM3 display;
- exact display ordering;
- suppression of internal-only facts.

Do not solve by deleting facts from the Market model context.

## 3.1 Separate two surfaces

Create:

### `MARKET_INTERNAL_FACT_VIEW`

Used by:
- Market model;
- source/numeric validation;
- policy reasoning.

May contain all current qualified Market facts.

### `MARKET_USER_DISPLAY_VIEW`

Used only by final renderer.

Contains exact selected rows/blocks specified in Sections 12–14.

Every displayed number remains bound to the same canonical fact/numeric registry.

The display selector changes visibility/order only.

It does not change source authority or model inputs.

## 3.2 Deterministic display selector

Implement one typed display plan per market.

For each display item include:

- block ID;
- display order;
- canonical fact IDs;
- numeric-registry keys;
- display label;
- value formatting;
- source observation/session date;
- required/optional;
- unavailable rendering policy.

Final numeric audit must audit the **selected display plan**, not require every internal fact to appear in prose.

## 3.3 Sector ranking owner

TOP3/BOTTOM3 must be deterministic.

Require:

- same eligible completed session;
- exact venue/universe;
- exact sector taxonomy;
- qualified return metric;
- no missing-to-zero;
- deterministic tie handling;
- selected fact IDs retained.

US:
- TOP3/BOTTOM3 from the qualified configured US sector universe.

KR:
- KOSPI TOP3/BOTTOM3;
- KOSDAQ TOP3/BOTTOM3;
- keep venue-specific ranking separate.

If a market/venue lacks sufficient qualified sector rows:
`자료 부족`

Do not infer sectors from monitored stocks.

## 3.4 Tests

- internal facts > displayed facts positive;
- hidden internal macro remains available to Market but absent from renderer if not selected;
- exact US display order;
- exact KR display order;
- sector ranking deterministic under input permutation;
- stale/mismatched-session sector cannot rank;
- selected numeric tamper fails;
- unselected internal fact does not make final numeric audit fail;
- display cannot invent a claim absent from internal catalog.

---

# 4. P1-C — true all22 fresh acquisition/composition controller

Current `scripts/unified_live_cohort_proof.py` is an older REV8 controller.

It imports from parent accepted packets:

- persisted macro observations;
- earnings-comparison facts;
- quality bundles;
- financial-source graphs;
- issuer bridge outputs.

That controller must not be used for R9 fresh qualification.

## 4.1 New controller

Create a distinct R9 controller, repository naming permitting:

`r2b_r9_full_fresh_requalification.py`

It must not accept an old source ZIP as a data input.

Old results may be passed only as post-seal regression references.

The new controller owns:

1. static universe/config freeze;
2. finite request plans;
3. fresh collection;
4. fresh normalization;
5. fresh financial/business owner execution;
6. fresh quality/valuation projection;
7. fresh market/macro/night owner execution;
8. fresh full-source composition;
9. source-authority graph;
10. offline replay;
11. adapter qualification;
12. optional downstream fresh AI proof.

## 4.2 Parent-packet carry-in prohibition

Add runtime checks that fail if any current-generation source fact contains lineage such as:

- parent result ZIP as current value source;
- old accepted-stock packet as current business fact owner;
- old macro observation as current macro owner;
- old financial-quality bundle as current quality result;
- old issuer bridge as current bridge result;
- old AI output.

Persisted **configuration/thesis** is allowed.

Persisted **business event evidence** is allowed only if:
- current product policy permits persisted evidence;
- original immutable source is preserved;
- a new R9 current-eligibility decision is produced;
- it is explicitly labeled persisted;
- it is not presented as fresh acquisition.

## 4.3 All22 means all22

Do not exclude:
- 005930;
- 047810;
- SNDK;
- previously complete controls.

All US14/KR8 current official financial/business owners run under R9.

No “already complete” bypass.

---

# 5. P1-D — source-owned macro observation/publication time

Current diagnostic conflict:

`app/macro/providers/ecos.py`

sets normalized `observed_at` from the query `as_of`.

That is not source-owned observation time.

## 5.1 Time fields

Every macro observation must separate:

- `retrieved_at`;
- `observation_period` / `observation_date`;
- `published_at` if the source exposes it;
- `query_as_of`;
- `cadence`;
- `latest_available_at_query_time`;
- `freshness_state`.

`query_as_of` may never stand in for `observation_period`.

## 5.2 FRED

For every consumed/displayed FRED series:

- preserve the exact returned observation date;
- preserve fresh R9 retrieval receipt;
- reject missing/placeholder observations according to existing owner;
- prove the selected row is the latest qualified row available from the R9 response/window.

Configured/known series inventory includes current mapped roles such as:

- DGS3;
- DGS5;
- DGS10;
- DGS30;
- DFII10;
- T10YIE;
- BAMLH0A0HYM2;
- VIXCLS;
- DCOILWTICO;
- DTWEXBGS;

plus other configured internal roles only if actually consumed.

Do not display DGS2/WALCL/RRPONTSYD merely because they are fetched if current product display does not select them.

## 5.3 EIA

Preserve source `period` for each observation.

Do not map query time to observation time.

Unconsumed EIA rows remain internal or optional according to the current Market contract.

## 5.4 ECOS / USDKRW

USD/KRW is a required final KR Market display role.

The R9 current source must own an actual observation period/date.

First audit the current ECOS response.

### If the current response contains the period:
- preserve it in normalized output;
- add exact tests.

### If the current KeyStatisticList route does not expose a sufficient observation period:
- use an already-authorized official ECOS time-series route within the same provider family if the repository supports it or a minimal bounded route can be implemented generically;
- freeze endpoint/stat/item/cycle/request budget before network;
- preserve raw period;
- do not add an undeclared provider.

If no bounded official ECOS route can prove USDKRW observation time:
- `R2B_R9_REV6_USDKRW_SOURCE_TIME_GAP`
- no live proof.

Do not use stale cached FX.

## 5.5 Latest-published semantics

A value may be `LATEST_PUBLISHED_VERIFIED` only when:

- R9 performed a current source query/read;
- the exact returned observation period is preserved;
- the selected row is proven latest under the bounded query response/owner;
- source cadence is known enough for the existing contract.

Fresh retrieval alone is insufficient if observation time is unknown.

---

# 6. Pre-network finite request budget closure

The failed preflight had `dispatch_allowed=false` because several provider theoretical maxima were null.

REV6 must close budgets offline before Phase B.

No request executes while any mandatory plan cell is null/unknown/unbounded.

## 6.1 Kiwoom stock 88 roles

Current planned logical roles:

- adjusted daily;
- adjusted weekly;
- adjusted monthly;
- unadjusted weekly valuation;

for all22 = `88` role reads.

Audit the exact StockRead/page contract.

Freeze per role:

- requested bar count/window;
- page size;
- maximum pages;
- continuation cap;
- timeout;
- transport retries;
- theoretical max attempts.

If the API/service uses open-ended pagination, add a finite generic cap derived from the declared required history, not a ticker exception.

Cap exhaustion is explicit failure.

## 6.2 US market OHLCV universe

Current configured US market universe includes:

- SPY
- QQQ
- IWM
- RSP
- SOXX
- XLB
- XLC
- XLF
- XLE
- XLI
- XLK
- XLP
- XLRE
- XLU
- XLV
- XLY
- NVDA
- MSFT
- AAPL
- GOOGL
- AMZN
- META

Freeze the exact current owner request count, timeout, page/window bound and theoretical transport attempts.

No stale-cache fallback.

## 6.3 Kiwoom REST KR market

Freeze exact requests/pages for:

- indices;
- KOSPI sectors;
- KOSDAQ sectors;
- breadth;
- flows if configured/eligible.

Consumer-complete page semantics may be used only where already proven by exact source-dependency tests.

## 6.4 SEC

Use the already-developed bounded SEC financial owner, extended to all current US14.

Before dispatch freeze:

- issuer/security map;
- form families;
- discovery pages;
- admitted candidate count;
- filing-index requests;
- document reads;
- linked exhibit cap;
- current/prior target roles;
- timeout/retries;
- theoretical maximum.

Do not reuse a frozen business comparison instead of current acquisition.

## 6.5 OpenDART

Use the bounded OpenDART owner for all KR8.

Before dispatch freeze:

- corp/security identity;
- report families;
- discovery page cap;
- statement/document reads;
- current/prior target roles;
- field/statement selection;
- timeout/retries;
- theoretical maximum.

005930 and 047810 must execute the fresh owner.

## 6.6 Event/news owner

If current product role inventory includes a mutable event/news acquisition:

- freeze provider;
- subjects;
- query;
- page/document count;
- timeout;
- retry;
- theoretical maximum.

No broadening to make a subject PASS.

If an event role is optional and current financial evidence suffices, its unavailable state must remain explicit according to the current product contract.

## 6.7 Macro

Freeze exact R9 calls for:
- FRED;
- EIA;
- ECOS;
- KRX night.

Alpha Vantage:
`planned = 0`
`actual = 0`

Massive/mock/undeclared fallback:
`0`

---

# 7. Phase-A completion gate

Before any provider call require all:

- night product scope PASS;
- Market internal/display split PASS;
- US/KR display-plan fixtures PASS;
- all22 fresh controller has zero current-data parent carry-in;
- macro source-time semantics PASS;
- USDKRW observation-time owner PASS;
- every mandatory provider request plan finite;
- all theoretical max attempts finite;
- source secrets/config valid without exporting secret values;
- operating/scheduler/DB state frozen;
- full focused tests PASS;
- no unexplained skip/xfail.

If any remain open:

`R2B_R9_REV6_PREFLIGHT_CONTRACT_GAP`

Return exact blocker and do not call a provider.

---

# 8. Fresh-generation identity

Only after Section 7 PASS create a new R9-REV6 generation.

It must contain no old source packet identity.

Record:

- generation ID;
- code SHA;
- policy/schema hashes;
- execution mode;
- actual timestamp;
- calendars;
- target sessions;
- provider plans;
- role inventory.

Historical result hashes are regression metadata only.

---

# 9. Execution mode / market windows

Support:

## Scheduled window

Verify exact current repository config before use.

Expected current config from the preflight result:

### US
- 08:10
- if incomplete → 08:15 full Class-A recollection
- if incomplete → 08:20 full Class-A recollection

### KR
- 16:00
- if incomplete → 16:05 full Class-A recollection
- if incomplete → 16:10 full Class-A recollection

No primary/backup.

If runtime config differs:
- stop before network.

## Ad-hoc live requalification

Allowed outside window.

Use:
- actual current query time;
- latest eligible completed regular session per exchange;
- same production owners/role inventory;
- no fiction that it was scheduled.

At the prior 13:58 KST diagnostic:
- US latest completed = 2026-09-25
- KR latest completed = 2026-09-23 because KR was intraday/provisional.

R9-REV6 must recalculate at its actual execution time.

---

# 10. Fresh mutable-data rule

Every mutable role used in source qualification or user display must have an R9-REV6 retrieval/read identity.

Forbidden as current data:

- R6/R7 price;
- R6/R7 OHLCV;
- R6/R7 technical state;
- old US/KR market rows;
- old macro values;
- old night D/W/M output;
- old financial comparisons;
- old quality bundles;
- old source-use PASS;
- old valuation multiples;
- old AI outputs.

A provider returning the same economic value is fine.

The retrieval/eligibility proof must be new.

---

# 11. Fresh stock collection — all US14/KR8

US14:

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

KR8:

- 000660
- 003690
- 005490
- 005930
- 010120
- 012450
- 047810
- 086280

Freshly collect all configured current roles.

No complete-control exemption.

At minimum where consumed:

- current/eligible completed-session price;
- D/W/M OHLCV or exact canonical technical history;
- technical indicators/structure;
- support/resistance/Bollinger structure;
- stock flow/volume-positioning inputs;
- financial/business source;
- current/prior comparison inputs;
- quality inputs;
- valuation numerator/denominator inputs;
- current/latest-published forward estimate input;
- current event/news role where configured.

---

# 12. Final US Market message contract

Exact final information architecture:

`미국 시장 · YYYY-MM-DD`

## 주요 지수

Show qualified current completed-session rows such as:

- SPY
- QQQ
- IWM
- other configured major-index/style rows selected by current display contract

Compact format:

`SPY  +4.21 (+0.73%)`

Use native price/index change value and percent.

## Macro

Compact block with currently selected qualified values such as:

- configured Treasury yields;
- WTI;
- dollar index/role;
- VIX;
- other current display-approved macro.

If not same-session, include observation date compactly.

Only `LATEST_PUBLISHED_VERIFIED` delayed values may display.

## 시장 판단

- one or two core interpretation sentences;
- `판단 확신도`.

## 섹터

- 상승 TOP3;
- 하락 TOP3.

If insufficient qualified same-session sector universe:
`자료 부족`

## 한국 야간선물

Only:

`KOSPI200`

Show:
- 일
- 주
- 월

Per unavailable horizon:
`자료 부족`

No KOSDAQ150.

---

# 13. Final KR Market message contract

Exact final information architecture:

`한국 시장 · YYYY-MM-DD`

## 시장 판단

Summarize:

- KOSPI direction;
- KOSDAQ direction;
- breadth if qualified;
- investor flows if qualified;
- one/two concise interpretation sentences;
- confidence where owned.

## 섹터

### KOSPI
- 상승 TOP3
- 하락 TOP3

### KOSDAQ
- 상승 TOP3
- 하락 TOP3

If one venue unavailable:
`자료 부족` only for that venue.

## 환율

Required user-facing role:

`USD/KRW`

Show:
- level;
- change/percent if source-owned;
- observation date if not same-session.

No stale cached FX.

---

# 14. Final detailed stock-message contract

The simplified R9 summary-card format is forbidden.

Preserve the established detailed monitoring format.

Preferred stable order:

1. optional pilot/run label only if product is actually in pilot mode;
2. company/ticker;
3. AI analysis judgment / BUY:SELL balance / confidence / evidence maturity / New Buyer / Holder;
4. reevaluation conditions;
5. thesis state / structural risk / market expectation;
6. core judgment;
7. business/earnings;
8. existing warnings;
9. key monitoring;
10. current price structure;
11. stock flow or volume/positioning;
12. Valuation.

Do **not** render standalone sections for:
- existing registered price rules;
- data caution;
- next checks;
- unresolved/unknown.

Their structured states remain internal and may affect decision/validation.

## 14.1 Header / judgment

Example shape:

```text
🏢 Micron Technology(MU)

🧠 AI 분석 판단: HOLD
판단 균형: BUY 5 : SELL 5
판단 확신도: 중간 | 증거 성숙도: 혼재
신규 매수자: WAIT
보유자: HOLD
```

UNKNOWN_LIMIT:
- `AI 분석 판단: OBSERVE`
- no fake 5:5;
- `판단 균형: 판단 자료 부족`
- New Buyer/Holder OBSERVE.

## 14.2 재평가 조건

When structured checkpoints exist:

```text
🔄 재평가 조건
• 상향 재평가: ...
• 하향 재평가: ...
```

No filler.

## 14.3 Thesis-state summary

When owned:

```text
투자 논리: ...
구조적 위험: ...
시장 기대: ...
```

## 14.4 핵심 판단

```text
🎯 핵심 판단
<1–3 concise sentences>
```

## 14.5 사업·실적

When qualified:

```text
📈 사업·실적
...
```

Directional statements require comparative or other direction-eligible evidence.

## 14.6 기존 경고

When current configured/observed warnings exist:

```text
⚠️ 기존 경고
• ...
```

## 14.7 핵심 감시

```text
👁 핵심 감시
• ...
```

Prefer material 2–4 items.

## 14.8 현재 가격 구조

When qualified:

```text
📐 현재 가격 구조
• 현재가(정규장 종가): ...
• 가까운 지지: ...
• 가까운 저항: ...
• 볼린저 저항(주봉): ...
• 잠정 볼린저 저항(월봉·진행중): ... · 봉 마감 전 변동 가능
```

Show only owned lines.

Support/resistance are technical, not fair value.

## 14.9 수급 / 거래량·포지셔닝

KR, where qualified:

```text
📊 수급(주요 3주체) · <date> 기준
당일: 외국인 ... · 기관 ... · 개인 ...
5일: ...
20일: ...
외국인 보유: ... · ...%
수급 점수: ... · <plain-language state>
```

US, where the current source owns only participation:

```text
📊 거래량·포지셔닝
...
```

No price-direction-as-flow inference.

If unavailable:
`자료 부족`

## 14.10 Valuation — mandatory section

Every stock message includes:

```text
📐 Valuation
...
```

Show qualified current-price metrics:

- PER;
- PBR;
- Forward PER / fPER;
- other already-approved current-security valuation metric.

Where qualified, preserve rich calculation/explanation.

Example:

```text
PBR = 현재가 ÷ BVPS = 1,783,000원 ÷ 368,991.21원 = 4.8배
과거 대비:
PER 중앙값 11.3배 · PBR 중앙값 1.7배 · 88백분위
현재 Valuation: ...
오늘 Valuation 변화: ...
```

Rules:

- current R9 price;
- exact denominator period;
- same traded-security/share basis;
- compatible currency/unit;
- provider-native vs deterministic method recorded;
- fPER estimate horizon/as-of/latest-published status;
- historical distribution same metric/security basis.

If metric basis is unresolved:
`판단 자료 부족`

Non-positive denominator:
use accepted `N/M`/not meaningful state.

Valuation may affect New Buyer/entry under existing policy.

Valuation alone must not create Overall business direction.

---

# 15. Post-R7 absolute-current direction guard

Fresh R9 facts must satisfy:

A current absolute amount may be factual context.

It must not become directional merely because:

- revenue > 0;
- operating income > 0;
- net income > 0;
- amount is negative.

Directional financial use requires:

- compatible current/prior pair; or
- another explicitly approved directional fact.

Mandatory fresh controls:

- 005930;
- 047810.

If no direction-eligible business evidence remains:
`UNKNOWN_LIMIT / OBSERVE`

No continuity forcing.

---

# 16. Fresh financial/business acquisition — all22

Run current official owners for every monitored subject.

No exclusions for previously complete stocks.

For each subject build fresh/current-eligibility results for:

- exact issuer/security;
- filing/report/event;
- current/prior periods;
- field occurrences;
- statement basis;
- currency/unit;
- financial quality;
- source-use;
- direction eligibility.

US:
bounded SEC owner and configured event owner.

KR:
bounded OpenDART owner and configured event owner.

No parent accepted packet as current data.

---

# 17. Fresh 005930 / 047810 controls

Both must execute current OpenDART owner.

For displayed/directional financial fields freeze:

- filing ID;
- statement;
- current period;
- prior comparison period;
- consolidation basis;
- currency/unit;
- raw occurrences;
- quality;
- source-use.

Expected possibilities:

- valid comparative financial direction;
- context only;
- UNKNOWN_LIMIT.

Do not assume outcome.

---

# 18. Fresh quality owner — all22

Run from R9 financial/business inputs.

Output per subject:

- applicability;
- state;
- reason codes;
- source period;
- source refs;
- business-evidence quality effect;
- security valuation basis.

No old R6/R7 quality carry-in.

No absent→clean shortcut.

---

# 19. Fresh valuation owner — all22

Run current valuation owner using R9 values.

Per subject:

- current traded-security price/as-of;
- PER status/value;
- EPS denominator identity/period;
- PBR status/value;
- BVPS/book denominator identity/period;
- fPER status/value;
- forward EPS period/horizon/as-of;
- provider-native/deterministic method;
- historical median/distribution/percentile where qualified;
- currency/unit;
- security/share basis;
- source refs;
- display eligibility;
- New Buyer/entry use eligibility.

No old multiple reuse as current proof.

No cross-security transfer.

---

# 20. Fresh SKHY / SNDK special controls

## SKHY

Do not reuse old issuer bridge.

If current source requires a bridge:
- freshly prove same legal issuer;
- freshly acquire/revalidate current issuer financial comparison;
- no security per-share/valuation bridge unless explicitly verified.

If direct current official source qualifies:
use it.

## SNDK

Run current financial/event owners.

Possible:
- fresh financial;
- fresh event;
- persisted event with new current-eligibility proof;
- UNKNOWN_LIMIT.

Context-only headline remains non-directional.

---

# 21. Fresh US market source

Freshly retrieve:

- SPY/QQQ/IWM and other selected major/style symbols;
- sector universe;
- breadth/participation if current owner supports it;
- macro roles;
- KOSPI200 night context if consumed internally.

No prior market packet.

All display rows must bind to R9 facts.

---

# 22. Fresh KR market source

Freshly retrieve:

- KOSPI;
- KOSDAQ;
- breadth;
- KOSPI sectors;
- KOSDAQ sectors;
- flows where current owner qualifies them;
- USDKRW with source observation period.

No old market row.

---

# 23. Macro freshness/currentness

For every current macro role:

- fresh R9 retrieval;
- source-owned observation period;
- publication time if available;
- cadence;
- latest-selected proof;
- display eligibility;
- direction eligibility.

Allowed states include:

- CURRENT_SESSION_OR_DATE;
- LATEST_PUBLISHED_VERIFIED;
- DELAYED_BY_SOURCE_CADENCE;
- PUBLICATION_CURRENTNESS_UNPROVEN;
- OPTIONAL_UNAVAILABLE.

`PUBLICATION_CURRENTNESS_UNPROVEN` cannot display as current.

No arbitrary N-day age threshold replaces source currentness.

---

# 24. Attempt isolation

For production-like retry windows:

- attempt states are isolated;
- next attempt never patches the prior attempt;
- if retry policy triggers, recollect the entire declared Class-A set for the market;
- only the first complete attempt proceeds downstream.

No old-generation import.

---

# 25. Fresh source closure

After collection require:

- R9 stock packets `22/22`;
- US Market source ready `1/1`;
- KR Market source ready `1/1`;
- KOSPI200 night role ready according to configured policy;
- macro currentness complete for mandatory display/internal roles.

Then generate new:

- FullSourceRunSeed;
- US whole-source packet;
- KR whole-source packet;
- combined source packet;
- authority graph.

All identities are new R9-REV6 identities.

---

# 26. Offline replay twice

Freeze the new raw/source corpus.

Disable provider access.

Replay full source composition twice.

Require identical semantic hashes for:

- stock 22;
- Market US;
- Market KR;
- night;
- whole-source packets;
- authority graph.

Set:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`

only on PASS.

---

# 27. Complete live adapter qualification

Set:

`COMPLETE_SOURCE_ADAPTER_QUALIFIED = true`

only if:

- Phase-A four P1s closed;
- all mandatory current roles freshly acquired;
- all request budgets stayed within frozen bounds;
- no prior packet filled current data;
- no fallback provider;
- stock 22/22;
- Market 2/2;
- KOSPI200-only scope PASS;
- macro source-time/currentness PASS;
- post-R7 direction guard PASS;
- replay twice PASS.

Do not inherit this flag.

---

# 28. Fresh AI — no old output reuse

After source qualification, run completely fresh:

- Market `2/2`;
- Core `22/22`;
- A/New Buyer `22/22`;
- B/Holder `22/22`.

Do not reuse R5/R6/R7 AI output.

Use current accepted model/prompt/schema/policy.

No independent-assessment target labels.

No result-driven hotfix.

No source refresh after AI begins.

---

# 29. Model transport

Use current accepted model configuration.

Preserve:

- no semantic retry;
- no schema repair;
- no repair model;
- no judge;
- no fallback;
- no selective per-ticker rerun.

Only the existing explicitly approved transient transport retry rule may apply.

Record planned/attempted/accepted/completed counts.

---

# 30. Exact 24-message final-boundary capture

Capture exact sender-boundary payload bytes with delivery disabled.

Required:

- MARKET_US: 1
- MARKET_KR: 1
- US stocks: 14
- KR stocks: 8
- total: `24/24`

Files:

- `MARKET_US.txt`
- `MARKET_KR.txt`
- `STOCKS/us-<ticker>.txt`
- `STOCKS/kr-<ticker>.txt`
- `ALL_MESSAGES.md`

No post-hoc reconstruction/editing.

---

# 31. User-facing semantic validation

## Market US

Require exact Section 12 order/blocks.

No unselected internal fact leak.

No KOSDAQ150.

No stale macro.

## Market KR

Require exact Section 13 blocks.

Fresh USDKRW required.

## Stocks

Require exact Section 14 detailed format.

Specifically:

- detailed AI judgment;
- reevaluation conditions;
- thesis state;
- core judgment;
- business/earnings;
- warning/monitoring where owned;
- current price structure;
- flow/positioning;
- rich Valuation.

Do not render:
- registered price rules;
- data caution;
- next-check list;
- unresolved/unknown standalone section.

No internal refs/hashes/enums.

---

# 32. Human-review bundle

On full PASS create:

`r2b-r9-rev6-fresh-24-message-human-review.zip`

Include:

- exact 24 payloads;
- message hashes;
- renderer/display-plan audit;
- US/KR market source summaries;
- macro freshness/currentness ledger;
- KOSPI200 night D/W/M review;
- 22 stock source summaries;
- 22 financial comparison matrix;
- 22 quality matrix;
- 22 valuation matrix;
- 005930 trace;
- 047810 trace;
- SNDK trace;
- SKHY trace;
- source/provider call ledger;
- AI call ledger;
- validation.

This is the human-review artifact before scheduler cutover.

---

# 33. Production side effects — hard zero

Throughout REV6:

- Telegram send = 0
- recipient intent = 0
- production DB decision/warning writes = 0
- scheduler mutation = 0
- notification mutation = 0
- broker actions = 0
- deploy = 0
- main merge = 0
- remote push = 0
- service restart = 0

---

# 34. Success terminal

Use:

`R2B_R9_REV6_FULL_FRESH_ALL_SOURCE_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

only if:

1. all four preflight P1 contracts PASS;
2. every mandatory provider plan is finite before network;
3. all mutable current roles are fresh R9-REV6 reads;
4. stock packets = 22/22;
5. Market source = 2/2;
6. fresh USDKRW source-time contract PASS;
7. KOSPI200-only night scope PASS;
8. macro currentness/publication state PASS;
9. fresh quality/valuation owners PASS;
10. new full-source authority graph PASS;
11. post-R7 absolute-current direction guard PASS;
12. offline replay twice PASS;
13. `COMPLETE_SOURCE_ADAPTER_QUALIFIED = true`;
14. fresh Market/Core/A/B complete;
15. exact final messages = 24/24;
16. final messages match the explicit display contracts;
17. Alpha/Massive/fallback = 0;
18. production side effects = 0;
19. human-review ZIP generated.

---

# 35. Honest stop terminals

## Phase-A still open

`R2B_R9_REV6_PREFLIGHT_CONTRACT_GAP`

No provider/model calls.

## USDKRW source period unresolved

`R2B_R9_REV6_USDKRW_SOURCE_TIME_GAP`

No live proof.

## Provider plan unbounded

`R2B_R9_REV6_PROVIDER_BUDGET_GAP`

No request to that provider.

## Fresh stock partial

`R2B_R9_REV6_FRESH_STOCK_SOURCE_PARTIAL`

No AI.

## Fresh financial comparison partial

`R2B_R9_REV6_FRESH_FINANCIAL_COMPARISON_PARTIAL`

No forced direction.

## Market partial

`R2B_R9_REV6_MARKET_SOURCE_PARTIAL`

No AI.

## Adapter qualification gap

`R2B_R9_REV6_LIVE_ADAPTER_REQUALIFICATION_GAP`

No scheduler authorization.

## Model-stage failure

Use exact Market/Core/A/B/render terminal.

Preserve source corpus.

Do not recollect because AI failed.

---

# 36. Required validation

## Four preflight contracts

- night scope config;
- one-product receipt/replay;
- Market internal/display split;
- sector rank selection;
- no parent current-data carry-in;
- macro observation-period preservation;
- USDKRW source-time;
- finite plans.

## Freshness

- previous source packet cannot qualify current role;
- old macro cache negative;
- old quality/valuation negative;
- new retrieval identity required.

## Financial

- current-only absolute values non-directional;
- compatible comparison positive/negative;
- 005930;
- 047810;
- SKHY;
- SNDK;
- 000660;
- CPNG anomaly.

## Valuation

- current price binding;
- PER/PBR/fPER denominator basis;
- forward estimate time/horizon;
- historical distribution basis;
- non-positive denominator;
- no cross-security transfer;
- valuation not Overall direction.

## Market

- index change;
- macro display currentness;
- US sectors;
- KR venue-specific sectors;
- breadth/flows;
- USDKRW;
- KOSPI200 D/W/M;
- display-selector numeric binding.

## Renderer

- exact final boundary;
- US Market contract;
- KR Market contract;
- detailed stock contract;
- removed stock sections absent;
- no enum/ref/hash/debug leak.

## Repository

- focused tests;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan;
- no unexplained skip/xfail.

---

# 37. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum:

- `REPORT.md`
- `summary.json`
- diagnostic R9 result identity/SHA
- R7 runtime identity
- repository identities
- changed-file inventory

## Preflight repair
- night product-scope contract
- Market internal/display contract
- display plans
- sector-rank contract
- fresh-controller carry-in proof
- macro source-time contract
- USDKRW owner proof
- provider request plans/budgets
- Phase-A completion receipt

## Fresh collection
- all request/attempt receipts
- raw/source hashes
- observation/publication times
- 88 stock chart/valuation role receipts
- market-source receipts
- macro freshness ledger
- KOSPI200 night receipts

## Stock/business
- 22 fresh packet matrix
- 22 current/prior financial comparison matrix
- quality matrix
- event matrix
- source-use/direction matrix
- 005930 / 047810 / SKHY / SNDK detailed traces

## Valuation
- 22 current valuation matrix
- PER/PBR/fPER binding receipts
- forward estimate currentness ledger
- security valuation basis matrix
- historical multiple distribution basis audit

## Source closure
- R9-REV6 run seed
- US/KR/combined packets
- authority graph
- replay twice
- complete adapter qualification

## AI
- fresh model binding
- Market/Core/A/B call ledgers
- raw/accepted outputs
- validators

## Human review
- `r2b-r9-rev6-fresh-24-message-human-review.zip`
- SHA
- exact 24 payloads

## Safety
- provider budgets planned/theoretical/actual
- Alpha 0
- Massive/fallback 0
- production side effects 0
- secret scan
- bundle manifest

---

# 38. After full PASS — generate only

Only after human-review-ready full PASS, generate but do not execute:

`Post-R9-REV6 Unified Scheduler Cutover`

It must:
- require human approval;
- preserve one unified US schedule;
- preserve one unified KR schedule;
- keep/retire legacy primary/backup paths so active duplicate count = 0;
- preserve trading-day/holiday skip;
- preserve full-attempt recollection semantics;
- preserve downstream failure/debug behavior;
- no automatic second AI run after downstream failure.

Do not activate scheduler inside REV6.

---

# 39. Final principle

The failed R9 preflight did its job: it stopped before using a stale or internally inconsistent live contract.

REV6 first fixes those contracts offline.

Only then does it perform a genuinely new full-source generation in which:
- every mutable role is newly retrieved or newly proven latest-published;
- all22 are reacquired under current owners;
- KOSPI200 is the only night product;
- macro observation dates are source-owned;
- Market display is deliberately selected;
- stock messages use the restored detailed format;
- valuation is current-security/source-valid;
- fresh AI decisions are generated from that fresh source graph.
