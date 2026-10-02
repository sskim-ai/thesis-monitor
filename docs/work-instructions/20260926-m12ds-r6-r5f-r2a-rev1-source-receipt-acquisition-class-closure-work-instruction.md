# Thesis Monitor — M12DS-R6-R5F-R2A-REV1
## Source Receipt + Acquisition-Class Closure
### Fresh Query-Time Price Roles vs Run-Frozen / Versioned Persisted Evidence

**Purpose:** close the first R5F-R2 source-adapter gate without overcorrecting the product contract. Prospectively bind real source ownership/receipts to the existing owners, while explicitly distinguishing values that must be freshly collected on each price attempt from versioned persisted evidence that is legitimately reusable.

No scheduler cutover, model call, delivery, deploy, or production write is authorized in this task.

---

# 0. Newest accepted SoT

Adopt R5F-R2 as the newest source-of-truth for adapter parity.

R5F-R2 result ZIP SHA-256:

`afb6ab398e2ad0719690b8b18199a73050e717e7cc6b80d3cc65597e4dd1c199`

Terminal:

`M12DS_R6_R5F_R2_ADAPTER_PARITY_GAP_REMAINS`

State:

- `READY_FOR_PROMOTION = NO`
- `PIPELINE_PASS = NO`
- `source_gate = FAILED_CLOSED`
- `complete_source_adapter_qualified = false`
- `complete_ai_adapter_qualified = false`

Repository identities:

- operating/main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`
- R5F-R2 instruction:
  `e5ba55cdedb0926ea0d264885e1f2db3c7c979ab`
- R5F-R2 implementation:
  `3bb139ad5c29ed5c1af8f5d163a9dedd297e29ca`
- R5F-R2 final local:
  `59690071f58f0be6ccbabf38999b7a0c5edddb38`

Validation:

- focused: `111 passed`
- full: `5338 passed / 63 pre-existing skips / 0 failed`
- Ruff/diff/Investment Knowledge/Chart Knowledge: PASS
- provider calls: 0
- Alpha: 0
- Massive: 0
- model: 0
- Telegram: 0
- scheduler mutation: 0
- production DB mutation: 0

R5F-R2 bundle integrity was rechecked:
- manifest entries: `35/35`
- missing: 0
- hash/size mismatch: 0.

Do not overwrite or reinterpret the failed-closed R5F-R2 result.

---

# 1. Exact blocker being closed

R5F-R2 established that the existing source archives contain normalized/acquisition summaries but do not prove complete request-to-source-artifact-to-normalization ownership for the real production price roles.

Known concrete gap:

- canonical stocks: US14 + KR8 = 22;
- existing price roles per stock include:
  - adjusted daily;
  - adjusted weekly;
  - adjusted monthly;
  - unadjusted valuation read;
- therefore at least `22 x 4 = 88` stock price-role bindings lack a complete owner-bound raw/source receipt in the historical archives.

The absence of historical receipts must **not** be repaired by manufacturing raw HTTP payloads from normalized summaries.

This task is prospective contract closure.

---

# 2. Critical policy correction: not every input must be freshly downloaded per retry

The unified production packet contains different source classes.

Do not impose a false rule that every financial, macro, event, thesis, identity, or business datum must be reacquired from the network at 08:10/08:15/08:20 or 16:00/16:05/16:10.

Every consumed value needs lineage and temporal eligibility, but not every value needs attempt-local network acquisition.

Classify every source role into exactly one of the following acquisition classes.

---

# 3. Acquisition class A — `ATTEMPT_FRESH`

These values define the query-time market snapshot and must be freshly collected for each collection attempt.

Expected examples include, subject to the existing owner inventory:

- canonical stock price/chart roles needed for current technical/price context;
- current raw/unadjusted valuation price where the analysis actually consumes it as a current price role;
- US current market/index/style/sector/big-tech price context;
- KR current index/sector/market-flow price/context roles;
- other source values whose existing contract explicitly requires collection at the run's query time.

Requirements:

- request/source artifact must belong to the exact run + attempt;
- exact request identity;
- request/response or source-open timestamps;
- provider;
- symbol/route;
- endpoint/source family;
- session/as-of date;
- adjustment/raw basis;
- source bytes/artifact hash;
- normalized hash;
- validator receipt;
- no inherited prior-attempt cache;
- no cross-attempt merging.

On retry:

- attempt B recollects the complete required `ATTEMPT_FRESH` set;
- attempt C recollects the complete required `ATTEMPT_FRESH` set;
- A/B/C fresh roles may never be mixed.

This is the subset governed by the user's conditional 08:15/08:20 and 16:05/16:10 recollection policy.

---

# 4. Acquisition class B — `RUN_FRESH_ONCE`

These values may need acquisition during the run, but do not need to be downloaded again merely because the price snapshot is retried five minutes later.

Possible examples, only where the current owner contract actually requires current refresh:

- news/event collection;
- earnings-calendar context;
- publication telemetry;
- overnight/night-session inputs;
- other non-price context collected once for the market run.

Requirements:

- acquire once under the current run ID;
- preserve exact source artifact/request lineage;
- explicit `collected_at` and as-of/publication time;
- freeze a run-level hash;
- reuse the same run-level artifact across price attempt A/B/C;
- never label it as having been recollected at B/C when it was not;
- existing temporal eligibility must still pass.

If a role is not required to refresh every run under the existing product contract, classify it as Class C instead.

---

# 5. Acquisition class C — `VERSIONED_PERSISTED_ALLOWED`

These values may be reused from existing persisted evidence when their current typed freshness/temporal/source rules already permit reuse.

Expected examples include, subject to owner audit:

- canonical watchlist;
- security identity/master data;
- stored thesis and thesis version;
- SEC/OpenDART financial snapshots;
- canonical business/fundamental evidence;
- macro observations whose publication/as-of remains eligible;
- other versioned persisted evidence explicitly designed for reuse.

Requirements:

- exact persisted artifact/record identity;
- original provider/source;
- original observation/publication/filing date;
- original acquisition/source receipt where available under the existing contract;
- version/hash;
- temporal/freshness eligibility receipt for the current run;
- no relabeling as query-time fresh;
- no wholesale operating-DB copy presented as acquisition evidence.

Class C may be bound into every A/B/C price attempt through a separately frozen **run seed hash**.

Retrying the price snapshot must not redownload Class C merely to obtain a new attempt ID.

---

# 6. Acquisition class D — `OPTIONAL_UNAVAILABLE`

An optional source role may remain unavailable if existing product policy permits it.

Requirements:

- explicit owner denial/unavailable reason;
- no missing-to-zero;
- no invented substitute;
- no silent fallback;
- downstream typed packet must know the role is unavailable.

Optional unavailable is not equivalent to source failure unless the role is mandatory for the current message contract.

---

# 7. Freeze the acquisition-class inventory before implementation

Take the R5F-R2 `production-source-role-inventory.md` and classify every role into A/B/C/D.

For each role record:

- role name;
- market;
- canonical owner;
- provider;
- mandatory/optional;
- acquisition class;
- exact rationale from existing product/source semantics;
- freshness rule;
- retry behavior;
- fallback policy;
- receipt requirement.

Do not classify from convenience.

Do not convert a currently reusable persisted fundamental source into a mandatory live fetch without an explicit existing requirement.

Do not convert a current-price role into persisted reuse.

---

# 8. Owner-bound receipt instrumentation

Add opt-in observation/receipt support to existing source owners, beginning with the concrete R5F-R2 blocker.

For each Class A/B external/source read capture:

- run ID;
- attempt ID or run-level acquisition ID;
- market;
- role;
- canonical symbol/entity;
- provider/route;
- endpoint/source identifier;
- sanitized request identity/hash;
- request start;
- response/source-open time;
- provider response identity if available;
- exact immutable source bytes or immutable source artifact;
- source artifact SHA-256;
- adjustment/raw basis;
- session/as-of/publication date;
- normalized packet/hash;
- existing validator result;
- retry/refetch ordinal.

Instrument **every actual external retry/refetch**, not only the successful terminal response.

Default owner behavior must remain unchanged when observation is disabled.

No secret may enter receipts.

---

# 9. Source artifact is acceptable; raw HTTP bytes are not mandatory

The contract requires immutable source ownership, not an artificial raw-HTTP-only policy.

Allowed evidence includes:

- exact raw HTTP response bytes;
- official downloaded file;
- immutable provider response artifact;
- exact cache artifact created by the current request, if the request→artifact binding is proven;
- equivalent source artifact accepted by the existing source owner.

Not sufficient by itself:

- normalized bar fingerprint;
- final parsed OHLC rows;
- `valid=true`;
- a reconstructed JSON payload made from normalized rows.

---

# 10. Prohibited provider/fallback isolation

For this task and future unified run source adapter:

- Alpha Vantage = 0 unless separately authorized;
- Massive = 0;
- mock provider = 0;
- undocumented fallback provider = 0.

Audit known bypass points:

- `provider_priority`
- `ValuationSnapshotService.fetch`
- `run_kr_close_market_briefing`
- any nested provider registry
- any cached Alpha estimate/share/overview/event path.

Exclusion must apply to both:

1. new external calls;
2. persisted/cached values from prohibited providers when the current task says they are excluded.

Do not treat “API key absent” as sufficient provider exclusion.

For an excluded optional role:
- mark unavailable;
- do not substitute another provider.

---

# 11. Run seed

Create a minimal immutable run seed containing only legitimate Class C inputs and immutable business metadata.

Allowed seed content may include:

- canonical watchlist;
- security identities;
- stored thesis + version;
- eligible versioned fundamental evidence;
- eligible versioned macro/business evidence;
- declared existing business configuration.

The seed must have:

- exact item inventory;
- per-item provenance;
- per-item as-of/version;
- run-level seed SHA.

Do not seed:

- prior query-time price snapshots;
- prior market observations that are supposed to be Class A;
- previous attempt normalized packets;
- stale source cache merely to avoid acquisition;
- old decision outputs as new source evidence.

---

# 12. Night / overnight roles

Do not copy a historical night packet and rename its timestamp/attempt.

For a role that is legitimately overnight context:

- preserve its original source time/session;
- classify as B or C according to existing product semantics;
- bind it to the current run as overnight context;
- do not represent it as 08:10/16:00 query-time price.

If the existing product contract requires a new current-run overnight acquisition, acquire it under Class B in the run.

If no eligible artifact exists, fail/unavailable according to existing mandatory/optional policy.

---

# 13. Retry packet composition

For attempts A/B/C, production candidate packet is:

`RUN_SEED(Class C)`
+
`RUN_FRESH_ONCE(Class B)`
+
`ATTEMPT_FRESH(Class A for exact attempt)`
+
explicit Class D unavailable states.

Only Class A changes because a price attempt is retried.

The immutable final snapshot identity must hash/bind all components.

Prove:

- Class A cannot mix across attempts;
- B/C identity remains explicit and unchanged across retries;
- B/C is never falsely timestamped as attempt-fresh;
- failed A attempt values cannot leak into later successful packet.

---

# 14. Offline-first tests

Before any network access, use genuine saved source artifacts where they actually exist.

Required tests:

1. receipt observer captures exact request/source/normalized linkage;
2. wrong run/attempt rejected;
3. wrong symbol rejected;
4. wrong date/session rejected;
5. wrong basis rejected;
6. tampered source bytes rejected;
7. tampered normalized hash rejected;
8. symlink/path escape rejected;
9. hidden prohibited provider rejected;
10. cached prohibited provider value rejected;
11. A/B/C attempt isolation;
12. Class C seed reuse allowed without pretending fresh acquisition;
13. Class B reuse within run allowed with original timestamp;
14. optional unavailable remains explicit;
15. no model call if mandatory Class A receipt incomplete;
16. no cross-attempt price patching.

Do not manufacture provider raw payloads from normalized summaries.

Synthetic fixtures prove mechanics only, not real-source parity.

---

# 15. Controlled source-only canary policy

R2A-REV1 does **not** authorize a broad full production-data reacquisition by default.

After instrumentation and offline tests PASS:

- generate a deterministic source-only canary plan from the existing owners;
- the plan must list exact provider/endpoint/role/symbol and exact planned external request count;
- Alpha/Massive/prohibited providers must be zero;
- no model/render/delivery calls.

If genuine saved raw/source artifacts are sufficient to demonstrate owner-bound receipt mechanics, do not perform network calls.

If a real canary is necessary:
- use the smallest representative owner calls needed to prove receipt instrumentation for each distinct owner mechanism;
- do not use the canary to claim full US14/KR8 source parity;
- record exact call count;
- no retries beyond the explicitly frozen canary plan.

A later R5F-R2B task will perform the full source cohort once the receipt mechanism is accepted.

---

# 16. What R2A-REV1 may claim

PASS means:

- acquisition classes are explicit;
- owner-bound receipt instrumentation is implemented;
- prohibited source/cache exclusion is proven;
- run-seed vs attempt-fresh semantics are proven;
- current source owners can emit auditable receipts;
- source-only canary/fixture mechanics pass.

PASS does **not** mean:

- full US14/KR8 production source parity is already complete;
- Market/Core/A/B adapter parity is complete;
- 24-message proof has run;
- scheduler may be activated.

Suggested terminal:

`M12DS_R6_R5F_R2A_SOURCE_RECEIPT_ACQUISITION_CLASS_PASS`

If owner instrumentation cannot be added without source-owner redesign:

`M12DS_R6_R5F_R2A_SOURCE_RECEIPT_OWNER_GAP_REMAINS`

---

# 17. Resume path after R2A-REV1 PASS

Prepare R5F-R2B to:

1. execute/replay one complete real source cohort using the accepted receipt contract;
2. prove full mandatory-role coverage for US14 and KR8;
3. prove A/B/C run composition;
4. qualify the concrete source adapter;
5. connect existing Market/Core/A/B/validator/renderer/delivery owners;
6. run the production-equivalent US15 + KR9 = 24-message proof;
7. keep scheduler inactive.

Do not jump directly to R5F-R3 scheduler cutover.

---

# 18. Safety

This task:

- Alpha Vantage live calls = 0
- Massive live calls = 0
- model calls = 0
- Telegram sends = 0
- production delivery intents = 0
- broker actions = 0
- production DB decision/warning writes = 0
- scheduler mutations = 0
- notification mutations = 0
- deploy = 0
- service restart = 0.

Any optional canary provider calls must be explicitly enumerated in its frozen canary plan and must use only the currently configured production source owners.

Do not push unless separately authorized.

---

# 19. Validation

Required:

- acquisition-class inventory test/review;
- owner receipt tests;
- prohibited-provider + cached-provider tests;
- run-seed tests;
- A/B/C isolation tests;
- Class B/C temporal identity tests;
- optional-unavailable tests;
- disabled-entrypoint smoke;
- full pytest for production-imported changes;
- Ruff;
- git diff --check;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

No new unexplained skip/xfail.

---

# 20. Required result bundle

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- R5F-R2 identity/SHA receipt
- repository base/instruction/implementation/final SHAs
- changed-file inventory
- complete acquisition-class matrix
- mandatory/optional role matrix
- owner instrumentation inventory
- receipt schema
- request/source/normalization binding proofs
- prohibited-provider call/cache exclusion proof
- run-seed inventory/hash
- A/B/C composition proof
- offline fixture receipts
- source-only canary plan and results if executed
- provider/model/delivery counters
- scheduler before/after = unchanged
- focused/full validation
- secret scan
- iCloud-backed local-copy/hash receipt if result packaging uses it
- bundle manifest.

Do not overwrite R5F-R2.

---

# 21. Final product semantics preserved

This task must remain consistent with the user's operating policy:

## US
08:10 price/market snapshot
→ if incomplete, 08:15 new complete **Class A** recollection
→ if incomplete, 08:20 new complete **Class A** recollection
→ freeze first eligible complete packet
→ AI → render → send.

## KR
16:00 price/market snapshot
→ if incomplete, 16:05 new complete **Class A** recollection
→ if incomplete, 16:10 new complete **Class A** recollection
→ freeze first eligible complete packet
→ AI → render → send.

Versioned fundamentals/thesis/macros do not need to be pointlessly redownloaded every five minutes; they remain explicitly versioned/as-of inputs to the immutable run packet.
