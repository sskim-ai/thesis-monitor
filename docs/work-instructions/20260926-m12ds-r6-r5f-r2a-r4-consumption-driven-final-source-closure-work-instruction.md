# Thesis Monitor — M12DS-R6-R5F-R2A-R4
## Consumption-Driven Final Source Closure
### Close Only the Source Roles Actually Consumed by the Real Market/Core/A/B Path, Then Assemble the Network-Free Concrete Adapter

**Purpose:** close the remaining offline source-owner gaps from R2A-R3 without expanding into exhaustive provider/domain implementation that the real message pipeline does not consume. The task must trace the actual production-equivalent Market/Core/A/B input graph first, qualify exactly those source roles, represent optional unavailable roles honestly, install real aggregate replayers for reachable mandatory owners, and assemble one complete network-free concrete source adapter.

No live provider call, model call, rendering, delivery, scheduler activation, deploy, or production DB mutation is authorized.

---

# 0. Newest accepted SoT

Adopt R5F-R2A-R3 as the newest SoT.

R2A-R3 result ZIP SHA-256:

`6525f68626b0ae7f3d0f386af3c0cc8302a628dcdd39525939d749bc1eddd467`

Terminal:

`M12DS_R6_R5F_R2A_R3_FINAL_OWNER_GAP_REMAINS`

Repository identities:

- base:
  `bf7ffe59329b664521574dd88c338252c9064428`
- instruction:
  `3852d769fd2c25cdc3017b7c7f5601716482007b`
- validated implementation:
  `a30a03251b37fcb8227fd80e3cfee7895b478757`
- final:
  `4ea1da1d2bf135b6b0aeaa9d47b35e7c2da6885c`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

Accepted validation:

- focused: `362 PASS`
- full: `5462 PASS / 63 pre-existing skips / 0 failures`
- new tests: `58`
- Ruff/diff/Investment Knowledge/Chart Knowledge/disabled smoke: PASS
- external provider calls: `0`
- Kiwoom live calls: `0`
- Alpha Vantage calls: `0`
- Massive calls: `0`
- model calls: `0`
- rendered messages: `0`
- Telegram sends: `0`
- scheduler mutations: `0`
- production DB mutations: `0`

Bundle integrity independently verified:

- manifest entries: `278/278`
- missing: `0`
- hash/size mismatch: `0`
- extra manifest-scope files: `0`.

Current state:

- `NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = false`
- `complete_source_adapter_qualified = false`
- `complete_ai_adapter_qualified = false`
- `source_gate = FAILED_CLOSED`
- `R2B = NOT_GENERATED_NOT_EXECUTED`
- `R3 = BLOCKED`.

Do not overwrite or reinterpret R2A-R3.

---

# 1. Accepted mechanisms — preserve

Do not rewrite already accepted mechanics unless the smallest integration defect requires it:

- A/B/C/D acquisition classes;
- owner-bound request/source/normalization receipts;
- US market receipt interface;
- Kiwoom KR request/page receipt interface;
- Google RSS / Naver / SEC / OpenDART event receipt transport;
- exact cache-origin and prohibited-provider enforcement;
- read-only local seed projection;
- selected SEC/OpenDART direct metric lineage;
- macro temporal projections;
- transitive aggregate receipt schema and child-integrity validation;
- no cross-attempt Class-A mixing;
- no B/C timestamp relabeling;
- query-time snapshot semantics;
- Alpha/Massive/mock/undeclared source prohibition;
- fail-closed default.

The task is to connect these mechanisms to the **actual consumed production graph**, not create another parallel source architecture.

---

# 2. Remaining gaps accepted from R2A-R3

Current gap IDs:

1. `C_ESTIMATE`
2. `C_CANONICAL_CONSUMPTION`
3. `C_DOMAIN_AND_BRIDGE`
4. `AGGREGATE_OWNER`
5. `FULL_ADAPTER`

These are offline code/contract gaps.

A live canary does not solve them and is not authorized.

---

# 3. First principle — consumption-driven closure, not exhaustive data-domain expansion

Before implementing any remaining Class-C owner, derive the exact input graph consumed by the existing production-equivalent:

- Market
- Core
- A
- B
- validators
- renderer

for:

- US market message + US14 stock messages;
- KR market message + KR8 stock messages.

For every downstream input field record:

- stage;
- schema/typed field;
- mandatory/optional at that stage;
- originating source role;
- owner;
- provider;
- acquisition class;
- fallback behavior;
- whether absence is already permitted by current schema/policy;
- exact source/temporal validator.

This **consumed-field graph** is the authority for closure scope.

Do not implement a financial/macro domain merely because it exists in storage.

Do not require an optional role to contain a value when existing downstream policy allows it to be unavailable.

Do not remove a role that is actually mandatory.

---

# 4. Optional Class-C rule

The frozen acquisition class `C = VERSIONED_PERSISTED_ALLOWED` describes how a role is sourced, not a requirement that every optional C role always have a value.

For an optional C role:

- if a qualified eligible persisted value exists and the real downstream graph consumes it:
  - project it through the existing owner;
- if no eligible value exists and existing product semantics allow absence:
  - emit an explicit typed unavailable/denial state;
- do not fetch a new provider merely to fill it;
- do not invent zero/default;
- do not let unavailable silently become stale value.

An optional C role may remain acquisition class C while its current run outcome is unavailable. Do not reclassify the frozen A/B/C/D inventory just to express run-time availability.

This task must therefore close **owner behavior**, not force universal value presence.

---

# 5. Gap A — eligible valuation estimates

Current state:

`project_estimate_inventory` is inventory/denial only.

Existing owner:
`ValuationSnapshotService.fetch`

Required work:

1. trace which exact estimate fields the real Core/A/B schemas actually consume;
2. identify their existing accepted provider(s), period/basis and security identity rules;
3. split/extract a **read-only selection + eligibility owner** from mutation/network behavior;
4. no dividend synchronization;
5. no hidden provider fallback;
6. no Alpha cached estimates/shares/overview in unified mode;
7. bind:
   - security ID;
   - provider;
   - estimate type;
   - estimate period;
   - source observation/version;
   - currency/unit/basis;
   - persisted record IDs;
   - current eligibility;
   - deterministic normalized hash.

If no currently eligible estimate exists and the consumed field is optional:
- explicit unavailable is valid.

If a consumed estimate is mandatory:
- absence must fail the source packet.

No live estimate fetch is permitted.

---

# 6. Gap B — canonical cashflow / working-capital consumption

Current state:

`project_canonical_catalog` has lineage but `consumption_eligible=false`.

Do not create a new financial formula.

Trace the exact existing current-formal / PIT / consumption owner used by the real downstream packet.

Bind the existing verdict into a read-only immutable projection containing:

- canonical domain ID;
- exact source input fact IDs;
- statement/report periods;
- original provider/source dates;
- current-formal / PIT selection identity;
- owner/calculation version;
- existing consumption verdict;
- deterministic output hash.

Required:

- future/unowned input -> denied;
- stale/ineligible input -> denied under existing rule;
- conflicting source ownership -> fail closed;
- no mutation;
- no recomputation with a new formula.

If downstream does not consume a particular canonical domain, do not make its closure a blocker.

---

# 7. Gap C — consumed financial/domain bridge

R2A-R3 selected direct SEC/OpenDART fields but did not cover every possible foreign/balance/derived domain.

R2A-R4 must cover **every field actually consumed by the current US14/KR8 analysis path**, and only those fields are mandatory for closure.

For each consumed financial field/domain:

- originating typed schema field;
- selected source owner;
- issuer/security identity;
- filing/report identity;
- filing/publication date;
- fiscal/report period;
- statement/domain;
- metric identity;
- unit/currency;
- occurrence/record ID;
- source version/hash;
- existing quality/ownership/freshness verdict;
- downstream packet field;
- deterministic projection hash.

For foreign filing / balance-sheet / derived domains:

- use the existing source-selection owner if present;
- preserve ambiguity/exclusion logic;
- do not broaden to “all possible filings”;
- if the current downstream schema treats a field as optional and no qualified source exists, emit unavailable.

A field required by the current typed schema cannot be marked optional merely to pass.

---

# 8. Macro / Fed / overnight Class-C bridge

R2A-R3 already has temporal projections for:

- FRED/rates/credit/liquidity/risk;
- EIA energy;
- ECOS Korea macro;
- Federal Reserve published context;
- KR overnight cross-assets.

For each **actually consumed** field:

- install immutable OwnerAdapter projection callback;
- preserve original observation/publication/session time;
- preserve units/basis;
- apply existing temporal eligibility;
- no model-written Fed implication;
- no query-time relabeling;
- no live refresh.

For configured optional context not consumed or unavailable:
- explicit unavailable is sufficient.

Do not expand series coverage beyond the actual downstream input graph.

---

# 9. Gap D — real aggregate owner replayers

Install real offline `project_aggregate_and_validate` callbacks for every aggregate owner reachable by the concrete source adapter.

At minimum audit and implement where actually reachable:

- Kiwoom KR page sets;
- KRX run acquisition/history owner;
- event multi-read owner;
- Nasdaq breadth;
- US multi-symbol market owner.

Each replayer must:

1. consume the exact planned child receipts/artifacts;
2. re-run or invoke the existing real owner parser/normalizer offline;
3. validate exact planned child set/cardinality;
4. validate deterministic ordering;
5. validate run/attempt/acquisition identity;
6. validate page/cursor continuity where relevant;
7. produce aggregate normalized output;
8. bind aggregate hash to child hashes;
9. compare output to the candidate aggregate packet;
10. fail closed on any mismatch.

A callback that merely returns/trusts the already-normalized aggregate is prohibited.

If an aggregate owner is not reachable by the actual consumed graph, record that and do not implement it merely for theoretical completeness.

---

# 10. Gap E — concrete transitive reachability

Construct the real network-free concrete source adapter graph.

The graph must start from the actual unified run source request and end at every consumed A/B/C/D role.

For every reachable boundary prove:

- owner;
- provider/source;
- acquisition class;
- receipt/projection;
- provider/cache policy;
- mandatory/optional;
- failure behavior;
- downstream field(s).

Prove no reachable branch can consume:

- Alpha Vantage;
- Massive;
- mock provider;
- undeclared provider;
- prohibited cached value;
- prior attempt Class-A value;
- stale prior-run query-time packet;
- historical event row without required receipt;
- prior AI output as source evidence.

Legacy non-unified behavior remains unchanged.

---

# 11. Full network-free source adapter assembly

After Sections 3–10 PASS, assemble one complete network-free source packet for each market using:

- genuine saved raw/source artifacts where available;
- real offline owner replay;
- read-only persisted projections;
- explicit unavailable states;
- synthetic transport only for transport mechanics where no genuine historical wire bytes exist, clearly marked and never presented as current data.

Required:

## US
- canonical US14;
- all mandatory market/source roles used by the real downstream graph;
- exact consumed optional roles or typed unavailable states.

## KR
- canonical KR8;
- all mandatory market/source roles used by the real downstream graph;
- exact consumed optional roles or typed unavailable states.

Freeze:

- run seed hash;
- aggregate receipt graph hash;
- final source packet hash;
- mandatory-role coverage matrix;
- optional availability matrix.

At this stage a flag equivalent to:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`

is allowed only if the entire **actual consumed graph** is represented and validated.

Still keep:

`complete_source_adapter_qualified = false`

for current/live production until R2B executes a genuine current source cohort.

---

# 12. Do not force all C roles to production_seed_qualified=true

The 12 frozen C role families may contain optional roles.

PASS is based on:

- all mandatory consumed roles qualified;
- all consumed optional roles either qualified or explicitly unavailable under current policy;
- no unknown/unowned value reaches downstream;
- complete typed packet can be built.

Do not use a mechanical condition like:

`all 12 production_seed_qualified == true`

unless all 12 are actually mandatory under the existing downstream schema.

This prevents optional context from blocking the entire pipeline indefinitely.

---

# 13. No live source / model / scheduler work

Actual counters for R2A-R4 must remain:

- external provider calls = 0
- Kiwoom live calls = 0
- Alpha Vantage calls = 0
- Massive calls = 0
- model calls = 0
- rendered messages = 0
- Telegram sends = 0
- delivery intents = 0
- broker actions = 0
- production DB writes = 0
- warning writes = 0
- scheduler mutations = 0
- notification mutations = 0
- deploy = 0
- service restart = 0.

If a specific owner cannot be closed without a live request:
- return the exact minimal canary requirement;
- do not execute it.

---

# 14. Configuration / environment / scheduler fingerprint

Before edits capture:

- worktree HEAD / clean state;
- operating main HEAD / clean state;
- tracked configuration hashes;
- secret-safe `.env` SHA only;
- effective provider configuration fingerprint;
- scheduler inventory/state.

After task:
- capture again;
- require semantic equality except repository worktree changes intentionally made by this task.

No secrets in artifacts.

---

# 15. Historical/provenance protection

Do not weaken historical validators to permit the new code.

If observed-file lists legitimately change:
- update only observed inventories/counts;
- preserve reviewed roots;
- preserve expected historical FAIL states;
- preserve accepted pins/thresholds/prompts.

Do not turn an historical FAIL into PASS through scope widening.

---

# 16. Required tests

## Consumed-field graph
- every Market/Core/A/B source field has exactly one owner mapping or explicit unavailable state;
- no orphan source field;
- no unused optional role blocks packet.

## Estimates
- eligible record positive;
- stale/foreign-security/wrong-period/wrong-basis negatives;
- optional unavailable positive;
- Alpha cache negative;
- no mutation.

## Canonical CF/WC
- existing consumption verdict positive fixture;
- future/stale/conflict negatives;
- exact input fact/version lineage;
- no formula drift.

## Financial domains
- every actually consumed SEC/OpenDART/foreign/balance/derived field has owner lineage;
- ambiguity exclusion preserved;
- optional missing explicit unavailable;
- mandatory missing fails.

## Macro/Fed/overnight
- consumed series/event callbacks;
- original date/session preserved;
- stale/future controls;
- no stored AI implication.

## Aggregate replay
- real owner replay positives;
- missing/extra/duplicate/tamper/cross-attempt/cursor negatives;
- aggregate output must be child-derived.

## Whole adapter
- US14 complete network-free packet;
- KR8 complete network-free packet;
- all mandatory consumed roles present;
- optional unavailable typed;
- no prohibited path reachable;
- deterministic packet hashes.

---

# 17. Validation

Required:

- all prior unified source tests;
- new R2A-R4 focused tests;
- network-free source-adapter full prequalification;
- disabled unified entrypoint smoke;
- full pytest;
- Ruff;
- `git diff --check`;
- Investment Knowledge;
- Chart Knowledge;
- secret scan;
- skip/xfail identity check.

No new unexplained skip/xfail.

---

# 18. PASS criteria

Use:

`M12DS_R6_R5F_R2A_R4_NETWORK_FREE_SOURCE_PREQUALIFICATION_PASS`

only if:

1. actual downstream consumed-field graph is frozen;
2. all mandatory consumed C roles have read-only qualified owners;
3. optional consumed roles are either qualified or explicit unavailable;
4. valuation estimate owner behavior is closed;
5. actual consumed canonical CF/WC behavior is closed;
6. actual consumed financial domains are closed;
7. consumed macro/Fed/overnight callbacks are installed;
8. all reachable real aggregate owners have child-derived replay callbacks;
9. concrete adapter reachability is policy-closed;
10. complete US14 and KR8 network-free source packets assemble deterministically;
11. `NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`;
12. no live provider/model/scheduler activity occurs;
13. full validation passes;
14. R2B work instruction is generated and frozen.

If a gap remains:

`M12DS_R6_R5F_R2A_R4_SOURCE_PREQUALIFICATION_GAP_REMAINS`

Return only the actual consumed owner/path blocker, not theoretical unconsumed domains.

---

# 19. Generate R2B only after PASS

If PASS, include an immutable R5F-R2B instruction in the result bundle.

R2B scope must be:

1. freeze exact genuine provider call plan before execution;
2. one real current source cohort per market under the accepted receipt contracts;
3. US Class-A collection according to current query-time snapshot path;
4. KR Class-A collection according to current query-time snapshot path;
5. Class B once per run;
6. Class C versioned read-only projections;
7. complete source packet qualification;
8. no Alpha/Massive fallback;
9. connect existing real Market/Core/A/B/validators/renderer/delivery;
10. production-equivalent dry run:
    - US market 1 + US14 = `15`;
    - KR market 1 + KR8 = `9`;
    - total rendered = `24`;
11. Telegram sends = 0;
12. production delivery intents = 0;
13. scheduler mutation = 0;
14. on incomplete source packet, fail closed before model calls;
15. preserve query-time snapshot / no official-finality claim.

Do not execute R2B inside this task.

---

# 20. R3 remains blocked

Even after R2A-R4 PASS:

- do not activate US 08:10 scheduler;
- do not activate KR 16:00 scheduler;
- do not perform scheduler cutover;
- do not deploy/restart.

R3 waits for accepted R2B full real source + 24-message proof.

---

# 21. Required result bundle

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- R2A-R3 result identity/SHA receipt
- repository identities
- changed-file inventory
- consumed-field graph
- mandatory/optional downstream source-role matrix
- estimates owner proof
- canonical CF/WC consumption proof
- consumed financial-domain lineage matrix
- macro/Fed/overnight callback matrix
- aggregate real-replay matrix
- concrete adapter reachability graph
- provider/cache policy matrix
- US14 network-free packet proof
- KR8 network-free packet proof
- run-seed / aggregate-graph / packet hashes
- optional unavailable matrix
- execution counters
- config/environment/scheduler before-after proof
- focused/full validation logs
- secret scan
- R2B instruction + SHA if PASS
- bundle manifest.

---

# 22. Product operating policy remains unchanged

US:
`08:10 fresh Class-A snapshot`
→ incomplete only: `08:15 full Class-A recollection`
→ incomplete only: `08:20 full Class-A recollection`
→ first eligible immutable packet
→ AI → render → send.

KR:
`16:00 fresh Class-A snapshot`
→ incomplete only: `16:05 full Class-A recollection`
→ incomplete only: `16:10 full Class-A recollection`
→ first eligible immutable packet
→ AI → render → send.

B/C context is not pointlessly redownloaded every five minutes.

Primary/backup scheduler topology remains retired by design, but scheduler activation is still deferred to R3.
