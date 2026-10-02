# Thesis Monitor — M12DS-R6-R5F-R2A-R3
## Final Offline Source-Owner Closure
### Event Receipts + Full Class-C Projections + Transitive Aggregate Composition + Concrete Adapter Reachability

**Purpose:** close the three remaining partial owner-gap groups from R2A-R2 and finish network-free source-adapter prequalification. No full live US14/KR8 cohort, AI/model calls, scheduler activation, delivery, or production writes are authorized. If this task passes, it must generate the bounded R2B instruction; R2B itself remains unexecuted.

---

# 0. Newest accepted SoT

Adopt R5F-R2A-R2 as the newest SoT for source-owner closure.

Result ZIP SHA-256:

`65966116ac95d8af53240dfceae8a7f3b6a46c688286eb9d8b338b97158001ea`

Terminal:

`M12DS_R6_R5F_R2A_R2_OWNER_INTERFACE_GAP_REMAINS`

State:

- `READY_FOR_PROMOTION = NO`
- `PIPELINE_PASS = NO`
- `source_gate = FAILED_CLOSED`
- `complete_source_adapter_qualified = false`
- `complete_ai_adapter_qualified = false`
- `R2B = NOT_GENERATED_NOT_EXECUTED`
- `R3 = BLOCKED`

Repository identities:

- base:
  `99c78db1e8a326ee2b52be4a70b7d3a82b57f99d`
- instruction:
  `5b973579ef2c1a7cf60d07eda459b09d63432c97`
- implementation:
  `96bc8fe78012d6876fcd7dbf946e000ab122ac57`
- final:
  `bf7ffe59329b664521574dd88c338252c9064428`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

Accepted validation:

- focused: `304 PASS`
- full: `5404 PASS / 63 pre-existing skips / 0 failures`
- Ruff: PASS
- diff check: PASS
- Investment Knowledge: PASS
- Chart Knowledge: PASS
- disabled unified entrypoint smoke: PASS
- provider/model/render/Telegram calls: 0
- scheduler/production DB/notification mutations: 0

Bundle integrity independently verified:

- ZIP/sidecar SHA exact;
- manifest-listed artifacts hash/size exact;
- no missing manifest artifacts.

Do not overwrite R2A-R2.

---

# 1. Accepted R2A-R2 progress — preserve it

The following are accepted and must not be rewritten unless a concrete integration defect requires the smallest possible change.

## Gap group 1 — PASS at owner-interface level

### US market

`app.macro.providers.market.OhlcvMarketProvider.collect`

Accepted:

- all configured market-symbol reads can emit source-response receipts;
- exact source bytes/hash;
- completed session;
- symbol/provider/adjusted basis;
- owner normalization hash;
- separate A/B/C attempt fixtures;
- prior attempt reuse rejection.

### KR market

Accepted paths:

- `app.providers.kiwoom_rest_client.KiwoomRestClient.request`
- `app.services.kiwoom_kr_market_context_service.KiwoomKrMarketContextService.collect`

Accepted:

- data POST attempts/pages/cursors are receipted;
- OAuth secrets are excluded;
- page ordinals/cursor identity preserved;
- raw payload hashes preserved;
- typed page-set normalization exists;
- missing page / cross-attempt page mixing fail closed;
- existing reconciliation/units/session semantics retained.

Do not regress these interfaces.

The remaining aggregate bridge is addressed separately in this task; it does not reopen the basic owner-interface PASS.

---

# 2. Remaining gap A — real News/Event Class-B owner receipts

Current state:

`CollectionService.collect_events` / `_fetch_provider_events` are safely denied in unified opt-in mode because real nested provider/cache wire ownership is not yet represented.

Safe denial is not functional qualification.

Close the actual existing event owner path.

## Required inventory

Before coding, enumerate every provider/cache path reachable from:

- `app.services.collection_service.CollectionService.collect_events`
- `CollectionService._fetch_provider_events`

For each path record:

- provider;
- live/cache/local source;
- request function;
- request count behavior;
- retry behavior;
- publication timestamp source;
- entity/symbol identity source;
- raw/source artifact availability;
- normalized `RawEvent` lineage;
- optional/mandatory semantics;
- current fallback behavior.

Do not assume the provider registry alone is the full call graph.

## Required receipt contract

For every qualified event provider/cache source:

- run acquisition ID;
- provider/source ID;
- sanitized request identity;
- actual request/source-open time;
- raw source bytes or exact immutable source artifact;
- source SHA-256;
- provider/publication timestamp;
- subject/entity identity;
- normalized event identity/hash;
- relevance/identity/temporal validator receipt;
- error/denial receipt;
- retry/refetch ordinal when applicable.

`RawEvent` output alone is not a receipt.

Do not reconstruct lost source bytes from `RawEvent`.

## Cache rule

If a cache artifact is consumed:

- identify its original provider/source;
- preserve original acquisition/publication time;
- prove the cache artifact is exactly bound to the current event output;
- enforce unified provider policy before cache consumption;
- prohibited-provider cache must fail closed just like prohibited live access.

## Optionality

Do not make events mandatory merely to prove the interface.

If the product contract says optional:
- explicit unavailable/denied is valid Class D behavior;
- no substitute/mock value.

After closure, the event family must no longer need a blanket guard that denies all real qualified event owners.

---

# 3. Remaining gap B — full Class-C owner projections

R2A-R2 currently has:

- 3 local projections partially tested;
- SEC/OpenDART freshness-only projection;
- 7 role families without real owner projection;
- no qualified final immutable seed.

Close all 12 frozen Class-C role families at the owner-projection level.

The frozen acquisition-class inventory remains authoritative.

Do not add or remove role families for convenience.

## 3.1 Mandatory local Class C

At minimum fully bridge:

- canonical universe;
- security identity/master;
- stored thesis + business metadata.

Requirements:

- exact record IDs;
- version/content hash;
- owner code/version fingerprint;
- current-run eligibility;
- final immutable composition bridge;
- no previous AI assessment as source evidence;
- no query-time price leakage.

These mandatory local projections must be serializable into the final run seed.

## 3.2 SEC / OpenDART

Freshness-only is insufficient.

For the selected financial facts actually consumed downstream, bind:

- issuer/security identity;
- filing/report identity;
- statement/report period;
- publication/filing date;
- source/provider;
- exact persisted fact/record IDs;
- metric/domain identity;
- units/currency;
- version/hash;
- original source receipt where current contract retains one;
- current typed eligibility;
- derived-domain lineage into the downstream packet.

Do not fabricate a provider receipt from an ORM row when original receipt is absent.

Where original raw receipt is historically absent:
- preserve that limitation;
- prove owner/record/version lineage honestly;
- classify exactly what the persisted-evidence contract can and cannot claim.

No live SEC/OpenDART fetch in this task.

## 3.3 Canonical cashflow / working-capital

Implement read-only projection for the exact canonical derived domains used by analysis.

Bind:
- derived domain version;
- input fact IDs;
- source periods/dates;
- calculation/owner version;
- normalized hash;
- eligibility.

Do not recalculate with a new formula.

## 3.4 Eligible valuation estimates

Owner:
`ValuationSnapshotService` / existing typed source path.

Requirements:

- exact allowed provider;
- security identity/basis;
- estimate period;
- source/provider version;
- persisted record IDs/hash;
- freshness eligibility;
- no Alpha cached estimate/share/overview values in unified mode;
- no mutation-coupled dividend sync;
- no hidden fallback.

If no qualified estimate exists:
- explicit unavailable is valid where optional.

## 3.5 Publication macro projections

Implement read-only projections for frozen roles including:

- FRED rates/credit/liquidity/risk;
- EIA energy;
- ECOS Korea macro;
- Federal Reserve published events;
- KR overnight cross-assets / previous-US-session context.

For each:
- series/event/product identity;
- original observation/publication/session date;
- original source/provider;
- exact persisted artifact/record;
- units/basis;
- version/hash;
- current temporal eligibility;
- explicit overnight classification where applicable.

Do not relabel historical/publication observations as query-time fresh.

No network fetch.

---

# 4. Remaining gap C — transitive aggregate receipt composition

The unified composition layer must represent aggregate owner outputs honestly.

Do not impersonate:

- a multi-page Kiwoom source;
- a multi-request Class-B acquisition;
- a grouped normalization

as one synthetic HTTP response receipt.

Implement an aggregate/transitive receipt type or equivalent typed contract.

Required aggregate fields:

- aggregate owner;
- run ID;
- attempt ID or run acquisition ID;
- market/role;
- child receipt IDs/hashes;
- deterministic child ordering;
- expected child set / cardinality;
- actual child set / cardinality;
- aggregate normalized output hash;
- aggregate validator receipt;
- source/session/publication coverage summary;
- aggregate hash binding all child identities and normalized result.

## Validation requirements

Fail closed if:

- any required child receipt missing;
- unexpected child injected;
- duplicate child;
- child from another run;
- child from another attempt when Class A;
- child source hash tampered;
- child normalized hash tampered;
- child provider prohibited;
- page/cursor continuity invalid where required;
- aggregate output does not match child-derived normalization.

Support at minimum:

1. Kiwoom KR page-set aggregates;
2. Class-B multi-read owner aggregates;
3. any US market multi-symbol owner representation needed by the final adapter.

Individual child receipts remain preserved in the bundle.

---

# 5. Remaining gap D — concrete-adapter reachability / policy closure

Do not settle for “registry has an allowlist”.

Construct the real network-free adapter call graph and prove unified source policy reaches every source/cache access path that it can invoke.

Audit at minimum:

- event provider/cache paths;
- historical-statistics cache;
- macro caches;
- valuation estimate/cache;
- dividend/capital-return selectors;
- KR FX briefing;
- KRX historical cache;
- Nasdaq breadth cache/history;
- SEC/OpenDART persisted owners;
- any source helper transitively reachable from the concrete adapter.

For every reachable boundary:

- allowed provider/source -> typed owner receipt/projection;
- prohibited live provider -> deny before call;
- prohibited cached provider -> deny before read/consumption;
- mock -> deny;
- undeclared -> deny;
- optional unavailable -> explicit D;
- mandatory unavailable -> fail source packet.

Do not globally change legacy behavior outside the unified opt-in path.

---

# 6. Network-free full prequalification assembly

Only after Sections 2–5 individually PASS, assemble the full network-free source adapter.

Inputs may include:

- genuine saved owner artifacts;
- deterministic local persisted DB fixtures/snapshots;
- real read-only owner projections;
- synthetic transport only where needed to prove interface mechanics, clearly labelled.

Prequalification must represent **all frozen mandatory source roles**.

Required output:

- A=5 / B=4 / C=12 / D=3 inventory exact;
- every mandatory A/B source has a receipt/aggregate contract;
- every mandatory C has real read-only projection;
- optional C/D state explicit;
- final run-seed hash;
- aggregate receipt graph;
- no prohibited provider/cache path reachable;
- deterministic immutable source packet assembly.

At this stage:

`complete_source_adapter_qualified`

must remain **false for live production use**, because no current genuine full cohort has been executed.

But use a distinct state such as:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`

only if every offline structural requirement actually passes.

Do not conflate prequalification with current live source proof.

---

# 7. No live source cohort / no AI in R2A-R3

This task remains offline.

Actual counts must remain:

- external provider market/event/macro calls = 0
- Kiwoom live calls = 0
- Alpha Vantage = 0
- Massive = 0
- model calls = 0
- rendered messages = 0
- Telegram sends = 0
- delivery intents = 0
- broker actions = 0
- production DB decision/warning writes = 0
- scheduler mutations = 0
- notification mutations = 0.

Do not use a real call merely to make a missing owner interface easier to implement.

If one owner genuinely cannot be structurally qualified without a live canary:
- freeze the exact minimal canary plan;
- return that as the only remaining blocker;
- do not execute it inside this task.

---

# 8. Preserve product retry semantics

Do not change:

## US
08:10 Class-A snapshot
→ if incomplete 08:15 complete Class-A recollection
→ if incomplete 08:20 complete Class-A recollection
→ first eligible packet.

## KR
16:00 Class-A snapshot
→ if incomplete 16:05 complete Class-A recollection
→ if incomplete 16:10 complete Class-A recollection
→ first eligible packet.

B/C data retain their original acquisition/version/as-of semantics and do not get redownloaded on five-minute price retries.

No cross-attempt Class-A mixing.

---

# 9. Environment/config fingerprint discipline

R2A-R2 noted that no pre-edit operating `.env` hash had been captured, so temporal equality could not be proven even though no config edit was performed.

For R2A-R3:

Before any repository edit, capture:

- tracked config hashes;
- relevant environment-file hash only as a secret-safe SHA-256 fingerprint;
- provider configuration fingerprint;
- scheduler state;
- operating main SHA;
- worktree SHA/clean state.

After task:
- capture again;
- prove equality.

Do not export secret values.

---

# 10. Historical scope/provenance constraints

Preserve all historical FAIL evidence and acceptance pins.

If legitimate new owner files expand observed-file inventories:
- update explicit observed inventories only where the historical test is designed to enumerate drift;
- reviewed roots remain frozen;
- semantic acceptance thresholds remain frozen;
- historical FAIL must remain FAIL where originally required.

Do not “fix” provenance by widening approved scope or changing expected FAIL to PASS.

---

# 11. Required tests

## Event owner
- live provider fixture receipt;
- cache receipt;
- publication identity;
- failure receipt;
- retry ordinal;
- prohibited cache/live denial;
- optional unavailable.

## Class C
For every one of 12 frozen C roles:
- owner projection exists;
- exact record/version/source/as-of;
- read-only eligibility;
- stale/future/ineligible negative;
- prohibited-source negative;
- output hash deterministic;
- no mutation.

## Aggregate
- exact child-set binding;
- missing child negative;
- extra child negative;
- duplicate negative;
- cross-run negative;
- cross-attempt A negative;
- tamper negative;
- page/cursor negative;
- deterministic aggregate hash.

## Reachability
- every concrete adapter branch has policy coverage;
- nested prohibited live/cache source blocked;
- no hidden fallback;
- legacy non-unified path unchanged.

## Whole prequalification
- all mandatory roles represented;
- A/B/C/D counts exact;
- immutable run seed;
- deterministic packet;
- source gate remains fail-closed for live production;
- network-free prequalification flag only.

---

# 12. Validation

Required:

- all focused R2A/R2A-R2/R2A-R3 tests;
- network-free source-adapter prequalification suite;
- disabled unified entrypoint smoke;
- full pytest;
- Ruff;
- `git diff --check`;
- Investment Knowledge check;
- Chart Knowledge check;
- secret scan;
- skip/xfail identity comparison.

No new unexplained skip/xfail.

Do not lower thresholds, change prompts, weaken schemas, or relax validators.

---

# 13. PASS criteria

Use:

`M12DS_R6_R5F_R2A_R3_FINAL_OWNER_CLOSURE_PASS`

only if all are true:

1. news/event B owner has real provider/cache receipt interfaces;
2. all 12 frozen Class-C roles have real read-only owner projection/eligibility contracts;
3. mandatory local Class-C projections are bridged into immutable final composition;
4. SEC/OpenDART consumed metric lineage is explicitly represented;
5. aggregate/transitive receipt graph is implemented and fail-closed;
6. concrete adapter reachability is policy-closed end-to-end;
7. prohibited live/cache fallback paths are unreachable in unified mode;
8. full network-free source-adapter prequalification passes;
9. no live provider/model/scheduler activity occurs;
10. full validation passes;
11. environment/config before/after fingerprints match;
12. R2B next work instruction is generated and frozen.

If any remain:

`M12DS_R6_R5F_R2A_R3_FINAL_OWNER_GAP_REMAINS`

Return exact role/owner/path and do not create a misleading R2B-ready state.

---

# 14. Generate R2B instruction only after PASS

If PASS, include a new immutable R5F-R2B work instruction in the result bundle.

R2B must be bounded and must not be executed inside this task.

R2B scope:

1. freeze exact current provider-call plan before execution;
2. execute one genuine full source cohort for the configured US14 + KR8 product;
3. Class A uses current query-time collection;
4. Class B acquired once per run;
5. Class C uses accepted versioned projections;
6. prove complete mandatory role/receipt/aggregate coverage;
7. qualify the concrete source adapter;
8. connect existing Market/Core/A/B/schema/validator/renderer/delivery owners;
9. run production-equivalent dry-run:
   - US market 1 + US14 = 15 rendered messages;
   - KR market 1 + KR8 = 9 rendered messages;
   - total = 24;
10. Telegram send = 0;
11. production delivery intent = 0;
12. scheduler mutation = 0;
13. Alpha Vantage = 0 unless a separate explicit authorization supersedes this;
14. on any source cohort incompleteness, fail closed and do not call AI.

R2B must preserve the query-time snapshot policy and no official-finality claim.

---

# 15. R3 remains blocked

Do not:

- activate US 08:10 scheduler;
- activate KR 16:00 scheduler;
- remove/modify remaining production scheduler reservations beyond already accepted paused/disabled state;
- deploy;
- restart.

R5F-R3 scheduler cutover remains blocked until R2B is accepted.

---

# 16. Required result bundle

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- R2A-R2 identity/SHA receipt
- repository SHAs
- changed-file inventory
- before/after config fingerprints
- event-owner provider/cache receipt matrix
- complete 12-role Class-C projection matrix
- SEC/OpenDART selected-metric lineage proof
- aggregate receipt schema
- aggregate positive/negative test matrix
- concrete adapter reachability graph
- provider/cache policy matrix
- network-free full prequalification receipt
- A/B/C/D exact inventory/count proof
- provider/model/render/send counters
- scheduler before/after unchanged proof
- focused/full validation logs
- secret scan
- generated R2B instruction + SHA if PASS
- bundle manifest.

---

# 17. Final boundary

R2A-R3 closes source ownership mechanics only.

It does **not** prove:
- a current genuine full source cohort;
- current query-time data completeness;
- actual AI message quality;
- delivery;
- scheduler readiness.

Those belong to R2B and then R3.
