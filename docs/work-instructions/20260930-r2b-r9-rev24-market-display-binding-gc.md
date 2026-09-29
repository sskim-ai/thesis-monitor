# Thesis Monitor — R2B-R9-REV24
## Market Directional-vs-Display View Separation + KR Alias→Canonical Display Binding
### Explicit External Transmission Approval + Archive-Backed Storage GC
### Then new full-fresh all-source requalification → replay twice → fresh Market/Core/A/B → exact detailed 24-message proof

**REV24 supersedes every prior unexecuted R2B-R9 instruction. Execute only REV24.**

REV23 successfully closed:

- SEC logical-cell reference grouping/routing;
- TSM source completeness;
- WRD/TSM JSON-native slot-plan persistence parity;
- all22 fresh stock-source ownership;
- whole-source graph replay twice and registry verification;
- prior current-price / technical / event / financial / valuation owner boundaries.

REV23 then stopped at exactly one P1:

`SOURCE_PARTIAL:mandatory_market_display_coverage`

This is not a provider-data absence.

The current gate incorrectly uses **directional request eligibility** as the source set for
**user-facing mandatory display coverage**.

Consequences observed in REV23:

1. Fresh/current or latest-published verified US macro facts exist and are `display_eligible=true`,
   but they are intentionally `direction_eligible=false` / absent from `request_eligible_refs`,
   so the display gate marks them missing.

2. Fresh ECOS USD/KRW exists and is `display_eligible=true`, but it is intentionally
   non-directional, so the display gate marks it missing.

3. Fresh completed-session KOSPI/KOSDAQ index facts exist through native Kiwoom aliases.
   The exact numeric alias→canonical binding already PASSes, but the mandatory display gate tests
   canonical IDs against the native alias ref set and therefore marks KOSPI/KOSDAQ missing.

REV24 must separate:

- **Market directional/model eligibility**
from
- **Market deterministic user-display eligibility**.

Do not broaden directional reasoning.
Do not make lagging/latest-published macro values today-signals.
Do not relabel observation dates.
Do not create alias authority without the existing exact numeric binding.

After offline closure:
1. seal minimal REV23 regression fixtures;
2. verify REV23 immutable archive;
3. execute standing storage GC;
4. start a completely new full-fresh generation;
5. require source 22/22 and Market 2/2;
6. replay twice;
7. run fresh Market/Core/A/B under the explicit external-transmission approval below;
8. capture exact 24 sender-boundary payloads;
9. generate human-review bundle.

---

# 0. Newest SoT

Adopt REV23 as newest implementation/result SoT.

REV23 result ZIP SHA-256:

`3fbd48f2035a2e9c05e093b20a9a5d5d1405ca78c74ba7b591555adac3d8dda4`

Uploaded sidecar:
exact match.

Independent verification:

- ZIP CRC:
  PASS
- internal manifest:
  `7895/7895`
- missing:
  `0`
- hash mismatch:
  `0`
- size mismatch:
  `0`
- extra:
  `0`

Terminal:

`R2B_R9_REV23_LIVE_ADAPTER_REQUALIFICATION_GAP`

Terminal detail:

`SOURCE_PARTIAL:mandatory_market_display_coverage`

Repository:

- branch:
  `codex/r2b-r9-rev23-json-native-slot-parity-gc`
- base:
  `89ca33e8ee831ea64550fd905f1f055b5a4b5bc0`
- instruction:
  `16a3ec1b1b1c48f905f0c0547ecff1738621f31f`
- implementation/final:
  `3f1fc1afa4f5cd0e07c4e738bf1ecd1c5bb1142a`
- operating:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- clean:
  true
- local-only:
  true

Validation:

- focused:
  `371 PASS`
- full:
  `6893 PASS / 63 unchanged skips`
- Ruff:
  PASS
- git diff --check:
  PASS
- Investment Knowledge:
  PASS
- Chart Knowledge:
  PASS

REV23 fresh generation:

`rev23-live-20260929T161451Z`

Frozen completed sessions:

- KR:
  `2026-09-29`
- US:
  `2026-09-28`

Provider attempts:

`539`

Model calls:

`0`

Messages:

`0/24`

Stock source diagnostic:

`22/22 PASS`

Slot-plan persistence parity:

- TSM:
  exact equality PASS, non-JSON-native paths `0`
- WRD:
  exact equality PASS, non-JSON-native paths `0`

Whole-source graph:

- replay-twice exact equality returned;
- persisted whole-source SHA:
  `3828c3f763b87ad71414442eabcc6feb6e3e8f5dc0caa6f19f0146a559e473e6`;
- complete qualification receipt not issued only because the mandatory Market display gate failed afterward.

No source mutation / qualification override / selective rerun occurred.

---

# 1. Explicit user approval for external transmission — authoritative for REV24

The user explicitly requested that the next work instruction **explicitly approve external transmission**.

This instruction carries the user's explicit approval for the following bounded REV24 external transmissions.

## 1.1 Approved read-only provider/API transmission

Approved:

- outbound requests to the already-declared and already-configured provider/API routes
  required by the sealed REV24 fresh provider plan;
- only the current approved provider inventory;
- read-only acquisition only;
- finite sealed request descriptors/budgets;
- no undeclared provider;
- no fallback provider;
- no broker/trading action.

This approval is sufficient for the REV24 controller/tool safety review.
Do not stop solely to request the user to re-approve the same declared provider reads.

## 1.2 Approved model-input transmission

The user explicitly approves transmission of the qualified current REV24 source/model payloads to the
**existing official GPT-5.6 Sol / xhigh model runner** used by Thesis Monitor.

Approved stages after all source/replay/model gates PASS:

- Market:
  up to 2 logical calls
- Core:
  up to the existing frozen batching plan
- A:
  up to the existing frozen batching plan
- B:
  up to the existing frozen batching plan

Expected maximum logical model calls under the current accepted batching:

`26`

Use the exact current frozen model transport policy for timeout/transient retries.
No semantic/schema/result-driven retry.
No fallback model.
No judge model.
No selective ticker rerun.

The user approves source-derived prompt/input transmission to this existing official model destination.

Do not stop solely for a separate "external model transmission approval" if the requested destination,
model, and scope match this section.

## 1.3 Approved report upload transmission

Approved:

- secret-scanned immutable result ZIP;
- `.sha256` sidecar;
- human-review ZIP/SHA when generated;

to the **existing configured iCloud Drive / Thesis Monitor folder**.

No credentials/secrets may be exported.

## 1.4 Not approved as part of REV24

This approval does **not** authorize actual Telegram/recipient delivery of the 24 monitoring messages.

REV24 must continue to use:

`delivery_disabled = true`

for final sender-boundary capture.

Telegram / production-recipient delivery remains:

`0`

until the exact 24 human-review messages are reviewed under the existing cutover process.

Also still prohibited:

- production DB decision/warning writes;
- scheduler mutation;
- broker actions;
- deploy;
- main merge;
- remote push;
- service restart.

This distinction is intentional:
external provider/model/report transmission is explicitly approved;
production recipient delivery is not part of REV24 proof.

---

# 2. Preserve all closed REV23 contracts

Do not reopen:

- JSON-native slot-plan representation;
- exact TSM/WRD disk/recompute equality;
- SEC logical cell reference grouping;
- TSM non-financial exhibit routing;
- canonical code-owner registry;
- completed-session current-price owner;
- current-effective technical owner;
- selected financial owner;
- SNDK 52/53-week fiscal contract;
- FPI bounded acquisition;
- OpenDART header contract;
- Google/Naver event ownership;
- ECOS CYCLE source-period ownership;
- latest-published FX currentness;
- KOSPI200 typed unavailable;
- Pass-A technical-family exclusion;
- UNKNOWN_LIMIT;
- R7 absolute-current financial direction guard;
- valuation policy;
- detailed stock renderer;
- Core/A/B policy.

REV24 changes only Market display-view selection / identity binding and then runs a new proof.

---

# 3. Exact REV23 Market blocker — US

REV23 US mandatory display gate reported missing:

- `DGS3`
- `DGS5`
- `DGS10`
- `DGS30`
- `DFII10`
- `T10YIE`
- `VIXCLS`
- `DCOILWTICO`
- `DTWEXBGS`

The fresh source facts existed.

Observed examples:

## Treasury nominal yields

DGS3 / DGS5 / DGS10 / DGS30:

- observation date:
  `2026-09-25`
- fresh query in current generation:
  yes
- `freshness_state`:
  `LATEST_PUBLISHED_VERIFIED`
- `latest_available_at_query_time`:
  true
- `display_eligible`:
  true
- `direction_eligible`:
  false
- `request_eligible`:
  false.

## T10YIE

- observation date:
  `2026-09-28`
- latest-published verified:
  true
- display eligible:
  true
- direction eligible:
  false.

## VIXCLS / DCOILWTICO

REV23's source owner classified the returned rows as:

- fresh-query sourced;
- latest-published verified;
- display eligible;
- direction ineligible.

Do not reinterpret the observation dates.
If these are still the latest official published rows in the new generation, display them with exact dates.

## Dollar

DTWEXBGS:

- latest-published verified;
- display eligible;
- direction ineligible.

The current gate fails because it passes `request_eligible_refs` into mandatory numeric display coverage.

That is the wrong ownership surface.

---

# 4. Exact REV23 Market blocker — KR

REV23 KR mandatory display gate reported missing:

- `USDKRW`
- `KOSPI`
- `KOSDAQ`

## USD/KRW

Fresh ECOS fact:

- fact ID:
  `market:fx:USDKRW`
- observation date:
  `2026-09-29`
- provider:
  ECOS
- `freshness_state`:
  `CURRENT_SESSION_OR_DATE`
- `latest_available_at_query_time`:
  true
- `display_eligible`:
  true
- `direction_eligible`:
  false
- `request_eligible`:
  false.

This is a valid display-only macro/context row.
It is intentionally not a directional Market signal.

## KOSPI / KOSDAQ

Fresh completed-session rows exist:

- KOSPI:
  close `6870.81`
  return `-0.27%`
- KOSDAQ:
  close `849.8`
  return `+0.38%`
- session:
  `2026-09-29`.

Native refs used in the current request-visible set:

- `kiwoom:ka20009:KOSPI:2026-09-29`
- `kiwoom:ka20009:KOSDAQ:2026-09-29`

Canonical display fact IDs:

- `market:cross-section:index:KOSPI`
- `market:cross-section:index:KOSDAQ`

REV23 numeric alias binding already PASSed exact value/unit/semantic identity for:

- close;
- return_pct.

The gate currently compares the canonical IDs directly to the native alias ref set.

That identity-layer mismatch is the KR index omission.

---

# 5. Two independent Market views

Formalize two independent views.

## 5.1 MarketDirectionalModelView

Purpose:

- Market AI reasoning;
- today-directional signal selection.

It continues to consume only refs/facts authorized by the existing directional/current eligibility policy.

No change to:

- `direction_eligible`;
- `today_signal_eligible`;
- `request_eligible_refs`;
- REFERENCE_LAGGING semantics.

Latest-published lagging macro/FX must **not** become directional merely because it is displayable.

## 5.2 MarketUserDisplayView

Purpose:

- deterministic user-facing Market numeric blocks;
- mandatory display coverage;
- Market sender rendering.

It may include facts that are not directional if the exact display contract qualifies them.

The two views must have separate receipts and hashes.

Do not infer one from the other after construction.

---

# 6. Typed MarketDisplayEligibilityDecision

Create a deterministic display owner, repository naming permitting:

`MarketDisplayEligibilityDecision`

For a publication/macro/FX fact, display eligibility requires all relevant conditions:

1. current REV24 generation performed the source query;
2. exact source row/fact identity is owned;
3. source observation period/date is preserved;
4. `display_eligible = true`;
5. `latest_available_at_query_time = true`;
6. freshness state is an already-approved display state such as:
   - `CURRENT_SESSION_OR_DATE`; or
   - `LATEST_PUBLISHED_VERIFIED`;
7. numeric value/unit binding PASS;
8. no current source-quality denial that prohibits display.

Display eligibility does not imply directional eligibility.

---

# 7. Observation-date rendering

When a displayed macro/FX observation date differs from the Market completed session:

the user-facing display must include the source observation date.

Examples of acceptable shape:

- `미 10년물 4.xx% · 9/25`
- `WTI $xx.xx · 9/22`
- `달러지수 xxx.x · 9/25`
- `VIX xx.x · 9/22`
- `USD/KRW 1,365.1원 · 9/29`

Exact formatting may follow the current renderer.

Forbidden:

- relabeling 9/25 as 9/28 or 9/29;
- wording that implies same-session close when it is latest-published lagging data;
- replacing source date with retrieval/query date.

---

# 8. US mandatory display coverage

The mandatory US display gate must consume:

`MarketUserDisplayView`

not:

`request_eligible_refs`.

Use the current configured product-display role registry as authority.

REV23 regression must prove the observed required roles are satisfiable from display eligibility when their
fresh/currentness receipts qualify, including the current mandatory set:

- DGS3
- DGS5
- DGS10
- DGS30
- DFII10
- T10YIE
- VIXCLS
- DCOILWTICO
- DTWEXBGS

Do not hardcode them only for REV23.
Bind to the existing Market display-role configuration.

If a required role in a new generation has no qualified display fact:
render/stop according to the existing mandatory-display contract.

Do not substitute stale cache.

---

# 9. Display-only facts do not enter Market directional reasoning

For every latest-published display-only fact, prove:

- visible in MarketUserDisplayView;
- absent from MarketDirectionalModelView unless an independent existing directional contract permits it;
- does not enter today's signal summary;
- cannot change Market direction/confidence solely through the display path.

Add negative tests where `display_eligible=true` but `direction_eligible=false`.

The Market model prompt/input must not gain the fact through another category alias.

---

# 10. KR alias→canonical display identity binding

Create/formalize a typed binding, repository naming permitting:

`MarketDisplayIdentityBinding`

It binds:

- native source alias ref;
- canonical Market fact ID;
- semantic field;
- value;
- unit;
- session date;
- source hash;
- binding hash.

For KOSPI/KOSDAQ current completed-session facts:

the existing numeric alias binding is the source of truth.

The mandatory display gate may satisfy canonical KOSPI/KOSDAQ requirements when:

- the native alias is request/current eligible;
- the exact alias→canonical numeric binding PASSes;
- session identity matches;
- value/unit/semantic type match.

Do not create a second numeric value.

Do not widen alias authority beyond the bound canonical fields.

---

# 11. KR alias-binding negative tests

Require:

- KOSPI alias + exact canonical close/return binding → PASS;
- KOSDAQ alias + exact binding → PASS;
- wrong value → fail;
- wrong unit → fail;
- wrong semantic type → fail;
- wrong session → fail;
- wrong canonical index → fail;
- unbound alias → fail;
- duplicate conflicting aliases → fail;
- alias from another generation → fail.

The canonical fact and alias remain separately auditable.

---

# 12. USD/KRW display contract

USD/KRW is a display macro/context role.

Fresh/current or latest-published official ECOS row may display when Section 6 passes.

It remains:

`direction_eligible = false`

unless a separate existing policy independently authorizes otherwise.

The mandatory KR display gate must not require directional request eligibility for the FX display line.

No alternate FX provider.

No date relabel.

---

# 13. KOSPI200 night remains nonblocking

Preserve REV23 behavior.

If a current verified KOSPI200 NIGHT/reference pair exists:
render qualified D/W/M horizons.

If it does not:
render:

`자료 부족`

per unavailable horizon/current contract.

Do not stale-promote a previous verified pair.

Missing night values must not be reintroduced as the REV24 hard blocker unless the current product contract
has independently changed.

No KOSDAQ150.

---

# 14. Sector/breadth unavailable semantics

Preserve current contract.

If current completed-session sector universe / breadth / flow qualifies:
render it.

If the approved source cannot qualify the required rows:
use honest `자료 부족` / omit optional subrows under the current renderer.

Do not use intraday values as previous completed-session evidence.

Do not make optional sector/night data a directional eligibility shortcut.

---

# 15. Separate gate receipts

Generate at least:

- `market-directional-view.json`
- `market-display-view.json`
- `market-display-coverage.json`
- `market-display-identity-bindings.json`

For each Market:

record:

- directional refs;
- display refs;
- display-only refs;
- canonical IDs;
- alias bindings;
- observation dates;
- source/currentness receipts;
- missing mandatory display roles;
- nonblocking unavailable roles;
- view hashes.

No hidden view conversion.

---

# 16. REV23 offline regression fixture extraction

Before GC of REV23 expanded data, seal a minimal Market regression fixture.

Include only what is needed to reproduce:

## US
- the publication facts/currentness receipts for the REV23 mandatory macro display set;
- current `request_eligible_refs`;
- old display-gate failure receipt.

## KR
- USD/KRW fact/currentness receipt;
- KOSPI/KOSDAQ native alias refs;
- canonical index facts;
- numeric alias binding receipt;
- old display-gate failure receipt.

## Night
- typed current-unavailable KOSPI200 receipt proving nonblocking behavior.

Create:

`rev23-market-display-regression-fixture/`

with manifest + SHA.

Do not retain the whole 539-request REV23 expanded generation merely for this regression.

---

# 17. Offline positive regression

Using only the sealed REV23 fixture:

## US

Require:

- directional view unchanged from REV23;
- display-only macro rows enter display view;
- mandatory US display coverage PASS;
- exact observation dates retained;
- display-only rows remain absent from directional reasoning.

## KR

Require:

- KOSPI/KOSDAQ canonical mandatory display roles satisfied through exact alias binding;
- USD/KRW display role PASS;
- USD/KRW remains non-directional;
- completed-session index values unchanged;
- night remains typed unavailable/nonblocking.

Then render deterministic Market numeric blocks offline.

No model calls.

---

# 18. Offline negative regression

Require:

- stale/unverified macro → display denied;
- latest-published verified macro with older date → display allowed with date;
- display-only fact leaks into directional view → fail;
- direction-only fact without display contract → do not assume display;
- KR alias numeric mismatch → fail;
- alias session mismatch → fail;
- canonical fact missing binding → fail;
- FX query-time substitution → fail;
- stale night promotion → fail.

---

# 19. Market AI input regression

Run exact deterministic Market-input materializer offline.

Require:

- display-only macro/FX do not become Market AI today-signal inputs;
- directional indices/current facts remain;
- schema/preflight PASS;
- no model calls.

Then run deterministic Market renderer fixture with synthetic accepted Market output to prove the final display block can combine:

- model judgment;
- deterministic display-only macro values;
- exact dates;
- sector/night unavailable states.

No post-hoc unsupported numbers.

---

# 20. Canonical code-owner registry

REV24 changes code.

Recompute whole-source code-owner hashes under the new exact implementation.

If the display-view owner is implemented inside an already registered Market/full-source owner module:
preserve path inventory.

If a genuinely new mandatory source/whole-source owner file is added:
update the canonical registry centrally and require:

producer = seed = consumer = replay1 = replay2.

No manual second inventory.

---

# 21. Whole offline gate

Before destructive GC or network require:

- MarketDirectionalModelView PASS;
- MarketUserDisplayView PASS;
- MarketDisplayEligibilityDecision PASS;
- US mandatory macro display regression PASS;
- display-only/directional isolation PASS;
- KR alias→canonical display binding PASS;
- USD/KRW display contract PASS;
- KOSPI200 unavailable nonblocking PASS;
- deterministic Market renderer fixture PASS;
- all22 offline source readiness PASS;
- canonical code-owner registry parity PASS;
- Pass-A visibility regression PASS;
- completed-session price regression PASS;
- all prior closed source-owner regressions PASS;
- focused tests PASS;
- full pytest PASS;
- Ruff PASS;
- git diff --check PASS;
- Investment Knowledge PASS;
- Chart Knowledge PASS;
- secret scan PASS.

Freeze implementation.

Only after this gate may storage GC execute.

---

# 22. Archive-backed Storage GC

REV23 is now sealed.

REV23 result ZIP:

`thesis-monitor-20260930-r2b-r9-rev23-json-native-slot-parity-gc-report.zip`

SHA:

`3fbd48f2035a2e9c05e093b20a9a5d5d1405ca78c74ba7b591555adac3d8dda4`

Before deleting REV23 expanded evidence:

- verify ZIP/SHA;
- CRC PASS;
- manifest `7895/7895`;
- seal Section 16 minimal Market fixture;
- verify no other test requires full expanded data.

Then REV23 expanded generation/report becomes GC-eligible.

Preserve immutable ZIP/SHA.

---

# 23. GC scope and protections

Apply the standing policy.

Eligible when archive-backed and dependency-safe:

- REV23 expanded live provider/source/replay data;
- REV23 unpacked report internals;
- older superseded R9 expanded data still present;
- obsolete diagnostic/validation exports;
- clean old worktrees satisfying all existing conditions.

Never auto-delete:

- current REV24 worktree;
- operating/main;
- shared `.git`;
- production DB/WAL;
- `.env`;
- credentials;
- scheduler/production state;
- immutable ZIP/SHA;
- registered minimal fixtures;
- active new generation.

Use `git worktree remove`, not raw deletion, for worktrees.

No aggressive shared-Git pruning.

---

# 24. Storage receipts

Create:

- `storage-gc-plan.json`
- `storage-gc-result.json`
- `storage-gc-protected.json`
- `storage-gc-fixtures.json`

Record:

- before/after free bytes;
- candidate paths/sizes;
- archive identities;
- deletion/skipped reasons;
- actual reclaimed bytes;
- worktree removals.

No silent deletion.

---

# 25. Disk guards

REV23 storage:

- logical removed:
  `1,508,132,719 bytes`
- actual free delta:
  `1,580,859,392 bytes`
- expanded directories removed:
  `17`
- worktree removed:
  `1`
- REV23 closeout/current free:
  approximately `14.86 GB` class.

Remeasure.

Hard pre-collection minimum:

`12 GiB`

Preferred:

`14 GiB+`

Hard pre-model minimum:

`10 GiB`

If safe GC cannot reach 12 GiB:

`R2B_R9_REV24_STORAGE_GC_HEADROOM_GAP`

Do not delete protected/unverified evidence merely to reach the threshold.

---

# 26. New REV24 full-fresh generation

Only after:

- offline Market gate PASS;
- archive-backed GC executed;
- free >= 12 GiB;
- explicit external transmission approval receipt is bound to this instruction;

start a completely new generation.

Do not resume REV23.
Do not reuse REV23 mutable/current source values.

Recompute:

- query time;
- US/KR calendars;
- completed sessions;
- provider descriptors;
- financial plans;
- events;
- Market/macro/FX/night;
- valuation;
- exact budgets.

Alpha Vantage:

`0`

Massive/undeclared fallback:

`0`.

---

# 27. Fresh all22 acquisition

Run all current owners for US14 + KR8.

Fresh:

- price/OHLCV;
- completed-session current price;
- technical;
- financial/business;
- selected financial owner;
- events;
- quality;
- valuation;
- flow/positioning;
- bridge where required.

No old mutable current values.

---

# 28. Fresh Market source acceptance

US:

- completed-session major indices/proxies;
- sector universe;
- FRED/EIA;
- current/latest-published display states.

KR:

- completed-session KOSPI/KOSDAQ;
- sectors/breadth/flows where qualified;
- ECOS USD/KRW.

Night:

- KOSPI200 only.

Require both Market views:

- directional;
- display.

No source-value substitution.

---

# 29. Full source closure

Require:

- stock packets:
  `22/22`
- Market source:
  `2/2`
- Market directional view:
  `2/2`
- Market display view:
  `2/2`
- mandatory display coverage:
  PASS
- current-price/technical states owned;
- selected financial owners complete;
- events:
  `22/22`
- quality:
  `22/22`
- valuation:
  `22/22`
- macro/FX/night typed states complete.

Create:

- FullSourceRunSeed;
- US whole-source packet;
- KR whole-source packet;
- combined packet;
- authority graph.

---

# 30. Replay twice

Freeze the new source corpus.

Disable providers/network.

Replay entire graph twice.

Require exact semantic equality for:

- stocks 22;
- financial states;
- current-price/technical;
- events;
- quality;
- valuation;
- Market directional views;
- Market display views;
- alias bindings;
- macro/FX/night;
- whole-source packets;
- authority graph;
- code-owner registry.

Then:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED=true`

and with current live coverage:

`COMPLETE_SOURCE_ADAPTER_QUALIFIED=true`.

---

# 31. Pass-A visibility replay

Before model calls require:

- excluded technical family absent from A view;
- approved financial-quality/thesis/macro refs visible under existing A authority;
- final A preflight PASS;
- no authority widening.

Display-only Market macro rows must not leak into Pass A through a generic context category unless the
existing A policy independently permits that exact ref.

---

# 32. Pre-model disk guard

Immediately before external model transmission:

`free >= 10 GiB`

If below:

`R2B_R9_REV24_DISK_GUARD`

Preserve frozen source corpus.
Do not call models.

---

# 33. Fresh AI — explicitly approved external model transmission

After all gates PASS, the user has explicitly approved transmission to the existing official
GPT-5.6 Sol / xhigh runner under Section 1.

Run fresh:

- Market:
  `2/2`
- Core:
  `22/22`
- A:
  `22/22`
- B:
  `22/22`

Use current frozen batching.

Expected maximum logical model calls:

`26`

No old output reuse.
No fallback/judge model.
No result-driven source refresh.
No semantic/schema retry.
No selective ticker rerun.

Do not request another user approval for this same external model transmission scope.

---

# 34. Final US Market message

`미국 시장 · YYYY-MM-DD`

Required blocks:

1. major selected indices/proxies:
   - SPY/QQQ/IWM/current configured roles;
   - change + %.
2. macro:
   - qualified display-view rates/oil/dollar/VIX values;
   - exact observation date where not same as Market session.
3. market judgment:
   - fresh Market model output;
   - confidence.
4. sectors:
   - TOP3/BOTTOM3 when qualified;
   - honest `자료 부족` when unavailable.
5. KOSPI200 night:
   - D/W/M where qualified;
   - `자료 부족` per unavailable horizon.

Display-only lagging macro must not be presented as a same-session directional cause unless the model has
independent eligible evidence for such a causal statement.

---

# 35. Final KR Market message

`한국 시장 · YYYY-MM-DD`

Required blocks:

1. Market judgment:
   - KOSPI/KOSDAQ completed-session flow;
   - breadth/flow when qualified.
2. sectors:
   - KOSPI TOP3/BOTTOM3 or `자료 부족`;
   - KOSDAQ TOP3/BOTTOM3 or `자료 부족`.
3. FX:
   - USD/KRW display-view value;
   - exact observation date when needed.

KOSPI/KOSDAQ display rows use canonical IDs satisfied through exact native alias bindings.

No duplicate values.

---

# 36. Final detailed stock messages

Preserve accepted detailed format:

1. optional actual pilot label;
2. company/ticker;
3. AI judgment / balance or UNKNOWN_LIMIT / confidence / evidence maturity / New Buyer / Holder;
4. reevaluation;
5. thesis / structural risk / market expectations;
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

No internal refs/hashes/debug text.

---

# 37. Exact sender-boundary capture — delivery disabled

Capture exact payload bytes using the existing production sender payload builder, but with recipient delivery
disabled.

Required:

- MARKET_US
- MARKET_KR
- US14 stocks
- KR8 stocks
- ALL_MESSAGES.md

Total:

`24/24`

No post-hoc reconstruction.

Telegram / recipient send count remains `0`.

---

# 38. Human-review bundle and approved report upload

On full PASS create:

`r2b-r9-rev24-fresh-24-message-human-review.zip`

Include:

- exact 24 payloads;
- hashes;
- Market directional-vs-display audit;
- US macro display currentness;
- KR alias→canonical binding audit;
- FX display receipt;
- source 22 matrix;
- current-price/technical;
- financial/events;
- quality/valuation;
- Market/macro/FX/night;
- whole-source graph;
- replay twice;
- A visibility;
- fresh Market/Core/A/B ledger;
- validation;
- production isolation.

The user explicitly approves secret-scanned upload of:

- REV24 result ZIP + SHA;
- human-review ZIP + SHA;

to the existing iCloud Drive / Thesis Monitor folder.

No separate upload approval is required if the destination matches the existing configured folder.

---

# 39. Production side effects

Allowed external transmissions are only those explicitly approved in Section 1.

Hard zero for:

- Telegram recipient send;
- production decision/warning DB writes;
- scheduler mutation;
- notification mutation;
- broker;
- deploy;
- main merge;
- remote Git push;
- service restart.

Provider/API reads and official model-runner payload transmission are **not** counted as prohibited
production side effects in REV24; they are explicitly approved proof actions.

---

# 40. Success terminal

Use only:

`R2B_R9_REV24_FULL_FRESH_ALL_SOURCE_24_MESSAGE_PASS_READY_FOR_HUMAN_REVIEW`

Require:

1. MarketDirectionalModelView PASS;
2. MarketUserDisplayView PASS;
3. display-only macro/currentness contract PASS;
4. no display-only fact promoted to directional reasoning;
5. KR alias→canonical display binding PASS;
6. USD/KRW display role PASS;
7. KOSPI200 unavailable remains nonblocking;
8. offline deterministic Market renderer PASS;
9. canonical code-owner registry parity PASS;
10. archive-backed storage GC executed;
11. pre-collection free >= 12 GiB;
12. explicit external transmission approval receipt bound;
13. new generation uses no prior mutable source data;
14. fresh stocks `22/22`;
15. Market source/views `2/2`;
16. mandatory Market display coverage PASS;
17. events `22/22`;
18. quality/valuation `22/22`;
19. whole-source graph PASS;
20. replay twice PASS;
21. Pass-A visibility replay PASS;
22. complete adapter qualification;
23. pre-model free >= 10 GiB;
24. fresh Market/Core/A/B complete;
25. model logical calls within frozen maximum;
26. exact sender-boundary payloads `24/24`;
27. Telegram recipient sends `0`;
28. production DB/scheduler/broker/deploy mutations `0`;
29. result + human-review archives secret-scanned and uploaded to approved iCloud destination;
30. human-review ready.

---

# 41. Honest stop terminals

- `R2B_R9_REV24_MARKET_DISPLAY_VIEW_GAP`
- `R2B_R9_REV24_MARKET_DIRECTIONAL_DISPLAY_LEAK`
- `R2B_R9_REV24_KR_ALIAS_CANONICAL_BINDING_GAP`
- `R2B_R9_REV24_MANDATORY_MARKET_DISPLAY_COVERAGE_GAP`
- `R2B_R9_REV24_STORAGE_GC_ARCHIVE_GAP`
- `R2B_R9_REV24_STORAGE_GC_HEADROOM_GAP`
- `R2B_R9_REV24_FULL_FRESH_SOURCE_PARTIAL`
- `R2B_R9_REV24_LIVE_ADAPTER_REQUALIFICATION_GAP`
- `R2B_R9_REV24_DISK_GUARD`
- exact model/render stage failure.

Do not:
- admit latest-published macro into directional reasoning solely for display;
- relabel source dates;
- duplicate KR index facts;
- bypass alias binding;
- stale-promote night futures;
- request redundant external-transmission approval already granted by Section 1;
- send Telegram messages during REV24.

---

# 42. Required validation

## Market view separation
- display-only + non-directional positive;
- directional view unchanged;
- no category alias leak;
- mandatory display gate consumes display view.

## Macro/FX currentness
- same-date current;
- latest-published older-date display;
- stale/unverified negative;
- exact observation-date rendering;
- no directional promotion.

## KR identity
- KOSPI alias→canonical;
- KOSDAQ alias→canonical;
- value/unit/session/semantic mismatch negatives;
- duplicate conflict negative.

## Night/sector
- unavailable typed state nonblocking;
- stale promotion negative.

## External approval
- approved provider read scope recognized;
- approved existing GPT-5.6 Sol/xhigh destination recognized;
- maximum model-call envelope frozen;
- approved iCloud report destination recognized;
- Telegram remains disabled;
- no secret export.

## Full pipeline
- all22;
- Market2;
- financial/events;
- current-price/technical;
- quality/valuation;
- macro/FX/night;
- replay twice;
- A visibility;
- Market/Core/A/B;
- exact24.

## Storage
- REV23 archive SHA/CRC/manifest;
- minimal fixture extraction;
- expanded deletion;
- protected paths;
- free-space accounting.

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

# 43. Required result bundle

Return immutable ZIP + `.sha256`.

At minimum:

- REPORT.md;
- summary.json;
- REV23 identity/SHA;
- repository identities;
- changed-file inventory;

## Market display repair
- directional-view schema/receipt;
- display-view schema/receipt;
- MarketDisplayEligibilityDecision matrix;
- US macro display regression;
- KR alias→canonical display bindings;
- USD/KRW display proof;
- mandatory display coverage;
- deterministic Market renderer proof;
- REV23 Market fixture manifest.

## External approval
- explicit-user-external-transmission-approval.json;
- approved destination/scope receipt;
- provider/model/upload counters;
- proof Telegram delivery remains disabled.

## Storage
- storage-gc-plan/result/protected/fixtures;
- before/after disk;
- archive identities.

## Fresh live
- provider plan/counters;
- all22 source matrix;
- Market directional/display views;
- current-price/technical;
- financial/events;
- quality/valuation;
- macro/FX/night;
- whole-source graph;
- replay twice;
- Pass-A visibility;
- adapter qualification.

## AI/render
- fresh Market/Core/A/B;
- exact24 payloads;
- message hashes;
- human-review ZIP/SHA.

## Safety
- Alpha/fallback 0;
- Telegram/recipient sends 0;
- production side effects 0;
- validation;
- secret scan;
- bundle manifest.

---

# 44. Final principle

REV23 proves that source collection, all22 stock ownership, JSON persistence parity, and whole-source
replay are already functioning.

The remaining blocker is a view-layer contract error:

**what the model may use to infer today's direction is not the same as what the user may be shown as
the latest official published macro/context value.**

Direction eligibility must remain strict.

Display eligibility must preserve source currentness, exact dates and numeric ownership without
turning lagging/latest-published facts into today's signals.

KR completed-session indices already have exact native-alias→canonical numeric bindings; the display
gate must consume those bindings rather than comparing incompatible identity layers.

Once that view separation is closed, archive-backed GC runs, a new full-fresh generation is collected,
the explicitly approved official external model transmission is performed, and the proof proceeds to
the exact 24-message human-review boundary.
