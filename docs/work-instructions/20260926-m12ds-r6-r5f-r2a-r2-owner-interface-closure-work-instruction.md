# Thesis Monitor — M12DS-R6-R5F-R2A-R2
## Remaining Source-Owner Interface Closure
### Close the Four Owner-Bound Receipt Gaps Before Full Source Cohort / AI Parity

**Purpose:** finish the remaining real-owner interfaces left open by R5F-R2A-REV1. This task does not run a complete US14/KR8 live source cohort, does not call models, and does not activate schedulers. It only makes the existing owners capable of producing the exact receipt/projection contracts needed by the unified pipeline.

---

# 0. Newest accepted SoT

Adopt R5F-R2A-REV1 as newest SoT for source-receipt architecture.

R5F-R2A-REV1 result ZIP SHA-256:

`8e00d434d551b8e88809d7db72841864fa24b1a144aac33a8abf2c9f2922bce9`

Terminal:

`M12DS_R6_R5F_R2A_SOURCE_RECEIPT_OWNER_GAP_REMAINS`

State:

- `READY_FOR_PROMOTION = NO`
- `PIPELINE_PASS = NO`
- `source_gate = FAILED_CLOSED`
- `complete_source_adapter_qualified = false`
- `complete_ai_adapter_qualified = false`

Repository identities:

- base:
  `59690071f58f0be6ccbabf38999b7a0c5edddb38`
- R2A instruction:
  `adb7eac34dd8dce7e3fbdbf8aaa508435cc2eb3b`
- acquisition-class freeze:
  `94a0ba72fffa03be6c726a7a1c2708aa70c2bbd6`
- implementation/full-validation:
  `7b9818d11dd2eba4d5d6e691f91bd22a97b53f6b`
- final:
  `99c78db1e8a326ee2b52be4a70b7d3a82b57f99d`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

Validation accepted from R2A-REV1:

- focused: `144 PASS`
- full: `5371 PASS / 63 pre-existing skips / 0 failures`
- Ruff/diff/Investment Knowledge/Chart Knowledge/disabled smoke: PASS
- provider calls: 0
- Alpha: 0
- Massive: 0
- model: 0
- render: 0
- Telegram: 0
- scheduler mutation: 0
- production DB mutation: 0

Bundle integrity independently verified:

- ZIP/sidecar SHA exact;
- manifest entries: `74/74`;
- missing: `0`;
- hash/size mismatch: `0`;
- extra manifest-scope files: `0`.

Do not overwrite R2A-REV1.

---

# 1. Accepted acquisition-class contract

Preserve exactly:

## A — `ATTEMPT_FRESH`
Recollect the complete required query-time price/market set for each attempt.

## B — `RUN_FRESH_ONCE`
Acquire once for the market run; preserve original publication/session/acquisition time across A/B/C price retries.

## C — `VERSIONED_PERSISTED_ALLOWED`
Reuse exact persisted versions only if the existing owner’s temporal/source eligibility passes for the current run.

## D — `OPTIONAL_UNAVAILABLE`
Explicit unavailable/denial; no value, zero, hidden fallback or substitute.

Do not reclassify roles for convenience.

R2A-REV1 froze 24 role families:

- A = 5
- B = 4
- C = 12
- D = 3

Any classification change requires an explicit evidence-backed amendment before implementation.

---

# 2. Already accepted mechanisms — do not rewrite

Preserve:

- `unified_source_observer`
- `unified_source_replay`
- `unified_source_composition`
- `unified_source_policy`
- opt-in OHLCV request/error/refetch receipt capture
- exact source artifact/raw hash
- normalization/validator receipts
- hidden/undeclared upstream provider rejection
- mock provider rejection
- symlink/path-escape rejection
- A/B/C composition rules
- Class C seed hashing
- B/C original temporal identity
- optional denial semantics
- no cross-attempt A mixing
- Alpha/Massive/mock/undeclared exclusions at already-covered surfaces.

Do not weaken or duplicate these mechanisms.

---

# 3. Exact remaining owner-gap groups

Close exactly the four gap groups accepted in R2A-REV1.

## Gap 1 — US market + Kiwoom KR market receipt interfaces

### US
Owner:
`app.macro.providers.market.OhlcvMarketProvider.collect`

Role:
`us_market_prices`

Current gap:
- independent OHLCV client path does not expose unified request/source/normalization receipts.

Required closure:
- use the shared observer/receipt contract;
- one receipt per actual symbol/source read;
- bind provider, market symbol, date/session, basis, raw/source artifact, normalized observation, validation;
- no inherited prior attempt artifact;
- whole configured Class-A set recollected per price attempt.

### KR
Owner:
`app.services.kiwoom_kr_market_context_service.KiwoomKrMarketContextService`

Roles include:
- local indices;
- sectors;
- breadth;
- optional investor flows/concentration.

Required closure:
- instrument OAuth-authenticated data reads without exposing token/secret;
- capture every request attempt;
- capture every pagination/page read;
- page-set normalization receipt;
- exact run/attempt identity;
- original provider query timestamps;
- response/source-artifact hashes;
- normalized role hashes;
- existing reconciliation/scale/typed validators;
- no page mixing across attempts.

Auth-token acquisition itself must not leak into receipt artifacts.

---

# 4. Gap 2 — RUN_FRESH_ONCE owner identity

Close explicit run-acquisition identity and failure receipts for Class B owners.

Expected owners from frozen inventory:

- news / filing event collection;
- earnings calendar;
- US exchange breadth;
- KRX night/publication context.

For every B owner:

- one `run_acquisition_id`;
- original request/source time;
- original publication/session time where applicable;
- source artifact/hash;
- normalized output hash;
- existing relevance/identity/temporal validator;
- failures/denials preserved;
- reused across price retries without timestamp relabeling.

A B artifact acquired once for the run must never be written as if freshly acquired at 08:15/08:20 or 16:05/16:10.

Do not force optional B roles to become mandatory.

---

# 5. Gap 3 — real Class C projections and eligibility

Implement read-only owner projections for the actual persisted Class C roles.

Expected classes include:

- canonical universe;
- security identity/master;
- stored thesis + version/business metadata;
- SEC financial evidence;
- OpenDART financial evidence;
- canonical derived financial domains;
- eligible valuation estimates;
- official/publication macro evidence;
- other frozen C roles from the R2A inventory.

For each C owner produce:

- exact persisted record/artifact identity;
- version;
- original source/provider;
- original observation/publication/filing date;
- original source receipt where existing contract has one;
- current-run eligibility decision;
- owner code/version fingerprint;
- normalized value hash;
- explicit denial if current eligibility fails.

### Read-only requirement

Do not invoke an owner method that mutates ORM state merely to answer whether a persisted record is eligible.

Where current freshness logic is mutation-coupled:

1. split/extract a read-only projection/eligibility function;
2. prove the existing mutation path still consumes equivalent semantics;
3. do not run refresh/backfill/network activity in this task.

No fake source receipt may be manufactured from the final ORM row.

---

# 6. Gap 4 — nested provider/event/cache policy propagation

Thread the opt-in unified source policy through every real path that the future source adapter may invoke.

Audit at least:

- `CollectionService`
- nested provider registry calls
- event collectors
- valuation estimate consumers
- cached Alpha estimate/share/overview consumers
- historical-statistic caches
- dividend/capital-return selectors
- KR FX briefing reuse
- any source-owner helper that can open a secondary provider/cache path.

Required behavior in unified mode:

- prohibited provider external call -> denied before call;
- prohibited provider cached value -> denied before consumption;
- mock provider -> denied;
- undeclared provider -> denied;
- optional role -> explicit D/unavailable when denied;
- mandatory role -> source attempt fails closed;
- no hidden fallback substitution.

Default legacy behavior outside unified opt-in mode must remain unchanged unless separately authorized.

---

# 7. No full source cohort in this task

R2A-R2 is an interface-closure task.

Do not run the complete current US14/KR8 production source acquisition.

Do not call models.

Do not render messages.

Do not send.

Do not mutate scheduler state.

Use:

- synthetic transport fixtures;
- previously saved genuine source artifacts;
- deterministic local persisted fixtures/DB snapshots;
- exact local owner functions in read-only mode.

If a specific owner interface cannot be proven without one real request, stop and return the exact owner-specific canary need rather than silently making network calls.

---

# 8. Genuine-artifact proof requirements

Where genuine prior source artifacts exist:

- verify original byte hash;
- bind original source/owner identity;
- replay through the real owner/parser;
- preserve original timestamp/session;
- compare normalized output exactly.

This proves owner mechanics only.

Never claim:
- current run freshness;
- current Class B acquisition;
- full source cohort parity

from a historical replay.

---

# 9. Contract tests per gap

## US market
- every configured market-symbol read emits receipt;
- wrong symbol/date/basis rejected;
- one attempt cannot reuse previous-attempt source artifact;
- source normalization hash bound.

## KR market
- every page/request emits receipt;
- token/secret excluded;
- page order/set bound;
- missing page fails mandatory role;
- pages from A/B attempts cannot mix;
- optional flow gap produces explicit D only if current policy says optional.

## Class B
- acquisition ID is run-scoped;
- same artifact reused across price attempts;
- original source/publication time unchanged;
- one owner failure stays visible;
- optional failure does not become invented value;
- mandatory failure blocks packet.

## Class C
- exact record/version bound;
- current eligibility computed read-only;
- stale/ineligible record denied;
- original source/as-of preserved;
- no relabel as current query-time;
- mutation path not invoked by seed projection.

## Policy propagation
- nested live prohibited provider blocked;
- nested cached prohibited provider blocked;
- credentials-present negative control;
- no silent fallback;
- default non-unified legacy path remains unchanged.

---

# 10. Source adapter prequalification assembly

After all four gap groups pass individually, assemble a **network-free prequalification adapter** using:

- real owner interfaces;
- genuine saved artifacts where available;
- persisted read-only C projections;
- synthetic transport only where no genuine source artifact exists.

The output must prove structurally:

- all mandatory role families can be represented;
- every A/B source has a receipt contract;
- every C role has a projection/eligibility contract;
- D roles contain no value;
- A/B/C/D final packet composition is deterministic;
- no prohibited provider/cache path is reachable;
- `complete_source_adapter_qualified` remains `false` until R2B real cohort.

Do not falsely set production qualification true from this prequalification.

---

# 11. R2B handoff generation

If R2A-R2 passes, generate the next **R5F-R2B work instruction** as part of the result bundle.

R2B must be bounded to:

1. one complete genuine source cohort for US14 and KR8 under the accepted receipt contracts;
2. exact provider-call budget frozen before execution;
3. A/B/C composition;
4. complete mandatory-role/source receipt coverage;
5. concrete source adapter qualification;
6. existing Market/Core/A/B/validator/renderer/delivery adapter connection;
7. production-equivalent:
   - US market 1 + US14 = 15 messages;
   - KR market 1 + KR8 = 9 messages;
   - total = 24;
8. Telegram sends = 0;
9. scheduler mutations = 0.

Do not execute R2B inside R2A-R2.

---

# 12. Alpha / Massive / external reference

For R2A-R2:

- Alpha Vantage external calls = 0
- Massive external calls = 0
- mock external calls = 0
- undocumented fallback calls = 0

Alpha 25/day operating cap remains relevant only if Alpha is explicitly authorized for a future task.

Do not consume Alpha quota here.

---

# 13. Scheduler / production state

Must remain unchanged:

- old primary/backup automations remain in their current paused/disabled state;
- new unified US/KR scheduler templates remain inactive;
- no scheduler registration;
- no callback;
- no notification mutation;
- no production DB decision/warning write;
- no deploy;
- no service restart.

R5F-R3 remains blocked.

---

# 14. Repository discipline

Use a new worktree based on the R2A-REV1 final unless a newer accepted SoT supersedes it.

Before changes:
- record HEAD;
- worktree clean;
- operating main identity;
- scheduler state;
- provider configuration fingerprint.

Do not modify historical sealed R5 evidence.

Do not weaken:
- prompts;
- schemas;
- validators;
- investment thresholds;
- historical acceptance pins.

If a legacy historical scope test needs portability work because legitimate new owner files were added, preserve its original reviewed-root semantics and keep the historical audit failing where it historically failed. Never turn historical FAIL evidence into PASS by widening the approved scope.

---

# 15. Validation

Required:

- focused tests for all four owner-gap groups;
- source receipt/replay tests;
- A/B/C/D composition tests;
- policy propagation tests;
- read-only seed tests;
- network-free source-adapter prequalification tests;
- disabled unified entrypoint smoke;
- full pytest;
- Ruff;
- `git diff --check`;
- Investment Knowledge;
- Chart Knowledge;
- secret scan.

No new unexplained skip/xfail.

Provider/model/render/send counts must remain 0.

---

# 16. PASS criteria

Use:

`M12DS_R6_R5F_R2A_R2_OWNER_INTERFACE_CLOSURE_PASS`

only if:

1. US market owner receipt interface implemented/tested;
2. Kiwoom KR market/page receipt interface implemented/tested;
3. all frozen B owner families expose run acquisition identity/failure receipts;
4. all frozen C role families expose read-only projection/eligibility;
5. nested provider/cache policy propagation is end-to-end for every path reachable by the future adapter;
6. no prohibited provider/cache consumption remains;
7. network-free prequalification packet can represent every mandatory source role;
8. no live provider/model/scheduler activity occurred;
9. full validation PASS;
10. R2B next instruction is generated and frozen.

If one or more owner surfaces remain:

`M12DS_R6_R5F_R2A_R2_OWNER_INTERFACE_GAP_REMAINS`

Return exact owner/function/path and do not start R2B.

---

# 17. Required result bundle

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- R2A-REV1 identity/SHA receipt
- repository identities
- changed-file inventory
- frozen acquisition-class matrix
- owner gap before/after matrix
- US-market receipt-interface proof
- KR-market/page receipt-interface proof
- Class B owner acquisition matrix
- Class C projection/eligibility matrix
- nested provider/cache propagation matrix
- genuine saved-artifact replay proofs
- source-adapter network-free prequalification proof
- provider/model/render/send counters
- scheduler before/after unchanged proof
- focused/full validation logs
- secret scan
- generated R2B next work instruction if PASS
- bundle manifest.

---

# 18. Product semantics must remain unchanged

US production target remains:

`08:10 Class-A snapshot`
→ if incomplete `08:15 new complete Class-A snapshot`
→ if incomplete `08:20 new complete Class-A snapshot`
→ first eligible packet
→ AI
→ render
→ send.

KR production target remains:

`16:00 Class-A snapshot`
→ if incomplete `16:05 new complete Class-A snapshot`
→ if incomplete `16:10 new complete Class-A snapshot`
→ first eligible packet
→ AI
→ render
→ send.

B/C inputs retain original acquisition/as-of semantics and are not redundantly reacquired on five-minute price retries.
