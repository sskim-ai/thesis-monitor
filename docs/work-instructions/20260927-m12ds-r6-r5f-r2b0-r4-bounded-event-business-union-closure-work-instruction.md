# Thesis Monitor — M12DS-R6-R5F-R2B0-R4
## Bounded Event Business-Union Closure
### Add the missing event input to the stock owner, then prospectively acquire at most one bounded news/event request for each of the 20 blocked subjects

**Purpose:** take the shortest valid path from R2B0-R3 to complete stock packets. Do not repair or execute the currently unbounded SEC/OpenDART financial-refresh paths. The existing Core rule already allows the observed-business union to be satisfied by an eligible reported financial **or an eligible business event**. Therefore, add the missing receipt-bound event input and independent business cutoff to the complete stock owner, then execute one frozen bounded event-only plan using existing single-request event owners.

No OHLCV recollection. No Alpha/Massive. No model calls. No scheduler mutation.

---

# 0. Newest accepted SoT

Adopt R2B0-R3 as the newest SoT for this scope.

R2B0-R3 result ZIP SHA-256:

`b43e88df23b490403689d73ebee039d68b9aefd106d11f8f5e3380b854f7d50c`

Terminal:

`M12DS_R6_R5F_R2B0_R3_BUSINESS_OWNER_GAP_REMAINS`

Bundle integrity independently verified:

- ZIP/sidecar SHA exact;
- manifest entries: `93/93`;
- missing: `0`;
- hash/size mismatch: `0`;
- extra manifest-scope files: `0`.

Repository identities:

- base:
  `4f61f308fe382fc149ee8435a31cbedf9b81fd06`
- R2B0-R3 instruction:
  `7dae4d6211a6e31de3b9bc7b062541fbe02b2c71`
- final/tested local:
  `a0de7b591c33ac5cc0f5c449def29c1460a2d539`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

Accepted baseline:

- sealed price source roles: `88/88`
- current prices eligible: `22/22`
- complete stock packets: `2/22`
- blocked: `20/22`
- already complete:
  - `005930`
  - `047810`
- CPNG mandatory technical blockers: `0`
- CPNG safe typed technical facts: `170`

R2B0-R3 execution:

- candidate business entries: `40`
- executable entries: `0`
- actual logical acquisitions: `0`
- actual transport count: `0`
- provider/auth/model/render/send/scheduler mutation: `0`

Do not overwrite the R2B0 price corpus or R2B0-R1/R2/R3 results.

---

# 1. Exact R2B0-R3 findings

R2B0-R3 correctly stopped before network because:

## Financial owner blockers

### SEC
`SecFinancialSnapshotService.refresh`
unconditionally enters foreign-filing discovery and the existing five-6-K selection rule does not bound:
- index requests;
- linked exhibits;
- all 20-F requests.

Therefore its transport budget is not bounded at the required preflight boundary.

### OpenDART
`OpenDartRecoveryClient.discover(limit=1)`
limits selected filings only after fetching `total_page`; there is no owner-enforced discovery page cap.

These are real owner-design gaps.

**They do not need to be fixed to satisfy the current observed-business union if an eligible event is available.**

Preserve them as separate technical debt. Do not execute these financial refresh paths in this task.

## Stock owner blocker

`app.services.unified_stock_owner.assemble_stock` currently:
- accepts no event input;
- builds `evidence=[]`;
- admits only qualified earnings/report refs;
- uses the sealed price plan cutoff for business/assessment timing.

This is the blocking interface that must be repaired now.

---

# 2. Existing Core union semantics — do not change

The current denial is:

`observed_business_union:eligible_reported_financial_or_event`

Therefore the existing contract already permits:

`qualified reported financial`
**OR**
`qualified business event`

to satisfy the observed-business union.

This task must not:

- lower union cardinality;
- replace the union with thesis/config;
- make any event automatically qualified;
- bypass identity/relevance/temporal validation;
- convert a financial denial into financial PASS.

A qualified event is a legitimate alternative branch of the existing union, not a workaround.

---

# 3. Minimal stock-owner repair

Modify only what is needed so the complete stock owner can consume source-owned event evidence.

Add an explicit typed event input equivalent to:

- subject/security identity;
- event owner/provider;
- raw/source receipt ID/hash;
- source URL/document identity where applicable;
- publication timestamp;
- normalized event identity/hash;
- event category/type;
- existing identity validator result;
- existing relevance validator result;
- existing temporal eligibility result.

Do not pass free-form event prose without source ownership.

---

# 4. Separate `business_cutoff` from price identity

Do not use the sealed R2B0 `price_plan.frozen_at` as the only cutoff for newly prospectively acquired business evidence.

Introduce an explicit:

`business_cutoff`

or existing equivalent.

Required semantics:

- price/technical packet keeps its original sealed query/session identity;
- newly acquired business event keeps its real publication/source identity;
- business event eligibility is evaluated against the explicit business cutoff;
- no event may claim to have existed at the older price collection time if it was published later;
- the assembled proof packet must preserve both time domains explicitly.

For this R2B0-R4 **materializer/provenance proof**, the business cutoff is the actual one-shot business acquisition review time, not a claim about historical availability at the old price collection time.

Do not use this mixed-time proof packet as a historical production decision.

A later R2B current cohort will acquire price and business inputs under one current run.

---

# 5. Preserve existing financial denial

If a subject's existing financial evidence is denied, keep the denial.

Examples:

- `003690`: selected financial tuple mismatch remains.
- `000660`: financial-quality denial remains.
- US subjects with unqualified historical filing lineage remain financially unavailable.

An eligible event may satisfy the **observed-business union**, but it does not rewrite:

`reported_financial = qualified`

when reported financial is still denied.

The final packet must distinguish:
- `financial_evidence = unavailable/denied`
- `event_evidence = qualified`
- `observed_business_union = non-empty`

where applicable.

---

# 6. Bounded event-only acquisition plan

Do not execute SEC/OpenDART financial refresh.

Use only existing event owners already proven capable of single-request bounded acquisition and source receipts.

Freeze this event plan before network access:

## US14 blocked subjects

Provider/owner:
existing Google RSS event/news owner.

One logical request each:

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

Logical requests:
`14`

## KR6 blocked subjects

Provider/owner:
existing Naver event/news owner.

One logical request each:

- 000660
- 003690
- 005490
- 010120
- 012450
- 086280

Logical requests:
`6`

Total frozen logical requests:

`20`

Do not reacquire events for already complete:

- 005930
- 047810

---

# 7. Transport budget

Before the first event request generate an exact deterministic plan JSON with:

- 20 logical entries;
- exact provider/owner per subject;
- request query identity;
- canonical subject/security identity;
- logical acquisition ID;
- retry = 0;
- maximum external attempts = 1;
- source-receipt owner;
- expected event validation path.

The external transport ceiling for this task is:

`20 event requests`

unless the existing one-request owner itself demonstrably performs a protocol redirect that is counted by the HTTP transport but not a second application-level request. Redirect behavior must be disabled or explicitly counted and documented.

No hidden provider fallback.

No pagination expansion.

No financial-owner requests.

---

# 8. Event query identity

Use the existing event owner's canonical subject/company query construction.

Do not manually invent broader keyword searches merely to force a result.

The query must preserve:

- canonical company/security identity;
- ticker/name aliases already accepted by the owner;
- market/language semantics;
- existing source relevance rules.

Do not use generic topic-only queries that can return unrelated companies.

---

# 9. One request / no retry

For every planned subject:

- at most one external event request;
- no retry;
- no backfill from another event provider;
- no second broader query;
- no manual web search;
- no SEC/OpenDART financial fallback.

If no qualified event is returned:
- subject remains blocked;
- preserve exact reason;
- continue all remaining subjects.

The goal is prospective evidence, not forced 22/22 success.

---

# 10. Event receipt requirements

For every request preserve:

- run/business-acquisition ID;
- subject;
- security/company identity;
- provider;
- exact query/request identity;
- request timestamp;
- raw response/source bytes or immutable response artifact;
- raw/source SHA-256;
- every candidate event identity considered;
- publication timestamp;
- source URL/document identity;
- normalized event hash;
- identity validator result;
- relevance validator result;
- temporal validator result;
- selected event(s);
- denial reason if none qualify.

Do not put credentials/tokens into artifacts.

---

# 11. Event qualification remains strict

A returned search/news item does not automatically qualify.

Use existing event validators unchanged.

Require at minimum the current owner's existing:

- entity/security match;
- publication identity;
- temporal eligibility;
- business relevance;
- duplicate handling;
- source/provider policy.

Do not change relevance thresholds or event categories to obtain PASS.

If multiple candidates arrive in the one response:
- evaluate all according to the existing owner;
- select only qualified candidates;
- preserve all candidate/selection receipts.

---

# 12. Re-run stock owner after event acquisition

After all 20 planned requests finish, re-run the complete R2B0-R2 stock owner using:

## Price / technical
unchanged sealed R2B0 88-role corpus.

## Anomaly scoping
unchanged R2B0-R1 component states.

## Financial
unchanged existing qualified/denied financial states.

## Business events
new source-owned event input with explicit business cutoff.

## Local/Class-C
existing identity/thesis/versioned evidence.

## Numeric registry
existing exact registry/source-ref contract.

No provider calls during assembly.

---

# 13. Subject PASS

A previously blocked subject may become complete if:

1. four sealed price roles still pass;
2. mandatory technical fields pass;
3. optional anomaly-blocked technical fields remain explicit unavailable;
4. either:
   - reported financial is qualified, or
   - at least one business event qualifies;
5. observed-business union >= 1;
6. event source refs are exact;
7. financial denials remain visible if present;
8. numeric registry/source-ref validation passes;
9. typed stock packet passes;
10. packet hash is non-null.

Do not require the event to repair unrelated financial metrics.

---

# 14. Regression subjects

## CPNG

Require:
- malformed OHLC source unchanged;
- anomaly scoping unchanged;
- mandatory technical blockers = 0;
- event evidence is the only newly introduced business-union source if financial remains denied;
- no price requery.

## 003690

Require:
- financial selected tuple mismatch remains;
- no mixed-filing synthetic earnings;
- qualified event may satisfy union only through the existing event branch.

## 000660

Require:
- financial-quality denial remains;
- no threshold change;
- qualified event may satisfy union only through the existing event branch.

## 005930 / 047810

Require:
- existing qualified packets remain byte/semantic equivalent without new event acquisition;
- do not replace their qualified evidence with news merely for symmetry.

---

# 15. Completion outcomes

## Outcome A — 22/22 complete stock packets

Terminal:

`M12DS_R6_R5F_R2B0_R4_BOUNDED_EVENT_BUSINESS_UNION_PASS`

Require:

- 20/20 bounded event requests attempted;
- no hidden extra provider call;
- 20 previously blocked subjects now complete;
- existing 2 remain complete;
- 22 packet hashes non-null;
- no price requery;
- financial denials preserved honestly;
- full validation PASS.

Then rebuild complete network-free source prequalification.

If complete:
- `NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`
- `complete_source_adapter_qualified = false`
- generate bounded R2B instruction.

## Outcome B — event evidence partial

Terminal:

`M12DS_R6_R5F_R2B0_R4_EVENT_BUSINESS_UNION_PARTIAL`

Report each remaining blocked subject with exact reason:
- no candidate event;
- identity mismatch;
- relevance failure;
- temporal failure;
- event owner error.

Do not automatically broaden queries or add providers.

## Outcome C — event interface/implementation gap

Terminal:

`M12DS_R6_R5F_R2B0_R4_EVENT_OWNER_GAP_REMAINS`

Use only for a genuine code/interface defect after the minimal stock-owner repair.

---

# 16. Network-free source prequalification

If 22/22 stock packets complete, combine them with already accepted:

- US market owner mechanics;
- KR market owner mechanics;
- KRX history/night replay;
- B/C/D source mechanics;
- run seed.

Freeze:

- US packet hash;
- KR packet hash;
- run-seed hashes;
- aggregate-graph hashes;
- mandatory coverage;
- optional unavailable matrix.

Set:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`

only if the complete consumed graph assembles and validates.

This is still not current live source qualification.

---

# 17. Generate R2B after full prequalification

If Outcome A + full prequalification PASS, generate but do not execute the R5F-R2B instruction.

R2B must:

1. freeze exact current provider-call plan;
2. collect one genuine current source cohort;
3. collect current US/KR Class-A price/market sources;
4. Class-B business/event acquisition once per run;
5. Class-C eligible versioned projections;
6. Alpha/Massive/mock/undeclared fallback = 0;
7. fail before model if mandatory source packet incomplete;
8. qualify concrete current source adapter;
9. invoke existing Market/Core/A/B owners;
10. render:
    - US market 1 + US14 = 15
    - KR market 1 + KR8 = 9
    - total = 24
11. same immutable source packet across all stages;
12. Telegram send = 0;
13. production delivery intent = 0;
14. scheduler mutation = 0;
15. package all 24 messages for direct review.

Do not execute R2B here.

---

# 18. Financial transport gaps remain separate non-blocking debt

Do not repair in this task:

- `SEC_FINANCIAL_TRANSPORT_PLAN_UNBOUNDED`
- `OPENDART_FINANCIAL_DISCOVERY_PLAN_UNBOUNDED`

Record them as open technical debt for future prospective financial refresh hardening.

They are not current whole-pipeline blockers if the existing observed-business union is legitimately satisfied through qualified events.

Do not misreport them as closed.

---

# 19. Safety

Allowed network activity:
- exactly the frozen 20 event/news requests.

Required zero:

- stock OHLCV calls = 0
- SEC financial refresh calls = 0
- OpenDART financial recovery calls = 0
- Alpha Vantage = 0
- Massive = 0
- model = 0
- Market/Core/A/B model calls = 0
- render = 0
- Telegram sends = 0
- production delivery intents = 0
- broker actions = 0
- production DB decision/warning writes = 0
- scheduler mutation = 0
- notification mutation = 0
- deploy = 0
- service restart = 0

Record actual application-level and HTTP-level event transport counts.

---

# 20. Configuration/state discipline

Before first request capture:

- worktree HEAD/clean;
- operating main HEAD/clean;
- R2B0/R1/R2/R3 ZIP identities;
- sealed price-corpus fingerprints;
- provider config fingerprint;
- secret-safe environment fingerprint;
- scheduler state;
- exact 20-request event-plan SHA.

After task prove:
- price corpus unchanged;
- config/environment unchanged;
- scheduler unchanged;
- no secrets in bundle.

---

# 21. Tests

Required:

## Interface
- stock owner accepts receipt-bound event inputs;
- distinct business cutoff;
- event not backdated to price cutoff;
- financial denial preserved while event union can qualify.

## Event plan
- exact 14 US + 6 KR = 20;
- no duplicate;
- no complete-subject request;
- no fallback;
- retry=0.

## Qualification
- identity positive/negative;
- relevance positive/negative;
- temporal positive/negative;
- raw/source hash binding;
- candidate selection determinism.

## Stock packets
- all subject outcomes;
- CPNG regression;
- 003690 financial mismatch preserved;
- 000660 quality denial preserved;
- 005930/047810 no recollection/evidence replacement.

## Regression
- prior source/anomaly/materializer tests;
- full pytest;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan;
- disabled unified entrypoint smoke;
- no new unexplained skip/xfail.

Do not weaken event/financial/schema thresholds.

---

# 22. Required result bundle

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- R2B0-R3 identity/SHA receipt
- repository identities
- changed-file inventory
- 20-request event acquisition plan + SHA
- exact provider/query mapping
- actual logical/HTTP request counts
- per-subject raw event/source receipts
- candidate event matrix
- selected/denied event matrix
- business cutoff receipt
- financial denial preservation matrix
- CPNG regression
- 003690 regression
- 000660 regression
- 005930/047810 invariance
- 22-subject stock packet matrix
- packet hashes
- sealed price-corpus invariance
- network-free prequalification result if reached
- R2B instruction + SHA if reached
- provider/model/scheduler counters
- config/env/scheduler before-after
- validation logs
- secret scan
- open financial-transport technical-debt receipt
- bundle manifest.

---

# 23. Final principle

Do not repair an unbounded financial refresh path just to satisfy an observed-business union that already permits qualified event evidence.

Use the shortest existing legitimate source branch, keep every denial visible, and preserve the sealed price data unchanged.
