# Thesis Monitor — M12DS-R6-R5F-R2B0-R5-REV9
## Sealed REV8 Cohort — Offline Owner / Authority Closure
### KR consumer-complete page ownership + current stock business-owner rebinding + whole-source run-seed/authority composition

**Purpose:** close the three exact P1 gaps left by REV8 using the already-sealed live source cohort only.

REV9 is strictly **offline/network-free**.

Do not recollect because the live acquisition succeeded and the remaining defects are owner/composition defects.

If REV9 closes the full source packet, generate—but do not execute—the next **R2B Sealed-Source AI 24-Message Blind Comparison** instruction.

---

# 0. Newest accepted SoT

Adopt REV8 as the newest SoT.

REV8 result ZIP SHA-256:

`eab400412052f9a33fbc8a2fbcff867590078eac96ff7ab4b02a984013fed6e1`

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV8_FULL_SOURCE_COMPOSITION_GAP`

Proof run:

`rev8-live-20260927T083836Z`

Proof mode:

`AD_HOC_LIVE_SOURCE_PROOF`

Scope:

`LIVE_SOURCE_ADAPTER_PROOF_NOT_PRODUCTION_DECISION`

Repository:

- base / accepted REV7:
  `b0dc78708f480d591889b40ea9f50707ef1283db`
- REV8 work-instruction commit:
  `77a3a27cb898ad5ed34b639b4bc1cc3061e5a625`
- acquisition implementation:
  `6ecd3e1a6f71e768a89259099505519a5afd6c6b`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

REV8 bundle integrity independently verified:

- ZIP / SHA sidecar exact
- bundle-manifest entries: `3486/3486`
- missing: `0`
- hash mismatch: `0`
- size mismatch: `0`
- extra manifest-scope files: `0`

Do not overwrite REV8.

---

# 1. Accepted REV8 live acquisition facts

The live acquisition itself succeeded within the frozen budget.

## Actual acquisition

| Owner | Logical requests | HTTP attempts | Transient retries | Frozen logical cap |
|---|---:|---:|---:|---:|
| Kiwoom stock roles | 291 | 294 | 3 | 579 |
| Native OHLCV US market | 25 | 27 | 2 | 48 |
| Kiwoom KR market | 42 | 42 | 0 | 109 |
| KRX night | 6 | 6 | 0 | 7 |
| **Total** | **364** | **369** | **5** | **743** |

- all 88 fresh stock logical roles captured
- native stock replay: `88/88 PASS TWICE`
- current-price consumer: `22/22 eligible`
- US mandatory market source:
  `22/22 observations PASS`
- KRX current night/publication source:
  PASS, two eligible products, six raw source receipts
- KR native owner returned:
  - 2 indices
  - 63 sectors
  - breadth
- no cap exhaustion
- no systemic stop
- Alpha Vantage: `0`
- Massive: `0`
- mock/fallback: `0`
- model / Market / Core / A / B / renderer / send: `0`

Accepted US market source:

- aggregate SHA:
  `89f921f7d25653948091ea05d098e7bcc2e13e1b19f2ff1efb39cedce80b7156`
- resolved SHA:
  `bdfc2016fe499b0c339c128e010dd8dd12f3c4ab3576c464839dbe69e8e4ed0e`
- source-value SHA:
  `2c70437814026d8936df5e9c332c28a599fb80fffee7acf852057afd3462d58f`

Accepted night source-value SHA:

`69dd6393038022e10ee058946e30edf1e611e5dc538dc744707e8477efb8c92f`

Do not recollect any of these sources in REV9.

---

# 2. Exact remaining P1 gaps

REV8 reports exactly three P1 items:

1. `KR page/consumption completion contract`
2. `versioned comparative/issuer/event owner binding into current stock`
3. `full run seed and current source-authority closure`

REV9 must address exactly these three.

Do not reopen unrelated source acquisition.

---

# 3. P1-A — KR page completion: distinguish transport exhaustion from consumer completeness

Current failure:

- KOSPI `ka20001`: page 1 has `continuation=true`
- KOSPI `ka20009`: page 1 has `continuation=true`
- KOSDAQ `ka20001`: page 1 has `continuation=true`
- KOSDAQ `ka20009`: page 1 has `continuation=true`
- frozen owner plan has `max_pages=1`
- current observer/aggregate verifier therefore marks:
  `mandatory_complete=false`

The owner nevertheless returned target-session market output.

Do **not** simply ignore continuation.

Do **not** request additional pages.

Instead prove the actual consumer dependency contract.

---

# 4. Generic KR page completion modes

Introduce an explicit per-read completion contract, using repository naming conventions.

Conceptual modes:

## `TRANSPORT_EXHAUSTED`

The consumer depends on the complete provider result set.

PASS requires terminal `continuation=false`.

## `CONSUMER_COMPLETE`

The provider may have more pages, but every source path actually consumed by the owner is proven present in the captured page set.

PASS requires:

- exact consumed source paths
- exact page IDs
- exact target-session ownership
- no downstream dependency on omitted pages
- generic API/consumer contract
- metamorphic negative/positive proof

A read may use `CONSUMER_COMPLETE` only if dependency proof succeeds.

Unknown dependency:
- fail closed.

Do not use one global rule for all Kiwoom APIs.

---

# 5. Audit each mandatory KR API separately

Audit the real `KiwoomKrMarketContextService` dependency graph.

At minimum:

## `ka20001`

Captured page contains:

- top-level index/current fields
- `inds_cur_prc_tm`
- continuation=true

Determine exactly what the KR market packet consumes.

If only page-1 top-level/current-session fields are consumed:
- prove every normalized output field → exact page-1 JSON path
- prove omitted continuation rows cannot alter the packet
- permit `CONSUMER_COMPLETE`.

If the packet consumes the entire intraday series:
- one page is insufficient
- REV9 must retain KR blocker.

## `ka20009`

Captured page contains target-session daily row at `20260923` plus older rows and continuation=true.

Determine exactly:

- whether the owner consumes only the exact target-session row
- whether any previous-day / multi-day feature consumes rows that may lie after page 1
- whether target-session uniqueness/ownership is proven

Only if every consumed value is already covered may the read become `CONSUMER_COMPLETE`.

## `ka20003`

Continuation=false in REV8.

Preserve current behavior.

Do not weaken it.

---

# 6. Raw dependency ledger

Produce:

`kr-market-consumed-source-paths.json`

For every field in the normalized KR market packet:

- output field
- source API
- read key
- page identity
- source JSON pointer/path
- target session/date
- normalization owner
- whether continuation tail can affect the field
- completion mode
- proof result

No output field may lack a source dependency.

---

# 7. KR metamorphic proof

Build generic offline fixtures from the captured semantics.

At minimum:

## Consumer-complete positive

For a candidate consumer-complete API:
- page 1 contains every consumed path
- continuation=true
- add synthetic continuation pages containing adversarial unrelated tail values
- output semantic hash must remain unchanged

## Dependency negative

If a consumed path is moved exclusively to page 2:
- consumer-complete must fail

## Target-session negative

If target-session row is absent:
- fail

## Wrong-session positive-looking data

If a page contains similar values but not the owned target date:
- fail

## Duplicate target-session ambiguity

If two incompatible target-session rows exist:
- fail

## Transport-exhausted mode

Continuation=true:
- fail until terminal page is present

This proof must be API/consumer generic.

No KOSPI/KOSDAQ value hardcode.

---

# 8. Do not infer provider semantics beyond consumed data

REV9 does not claim:

- omitted pages are universally irrelevant
- Kiwoom continuation is meaningless
- page 1 is always enough

The only allowed claim is:

> the current declared consumer is complete with respect to its proven source dependency set.

If this cannot be proven:
- keep the KR live-source blocker
- do not recollect in REV9.

---

# 9. P1-B — bind accepted business evidence to the fresh REV8 stock generation

REV8 current base stock materialization:

- PASS:
  - `005930`
  - `047810`
- BLOCKED:
  - remaining `20`

The current price/technical data is valid.

The failure is because the new stock-generation path does not consume the already-accepted business owner outputs.

This is not a retraction of REV6/REV7 22/22.

Do not rebuild business evidence from scratch.

---

# 10. Current Class-A and business evidence must remain separate generations

Use:

## Current security-level data

From REV8 fresh Class A:

- exact current stock source roles
- current price
- OHLCV
- technical component projection
- current attempt IDs

## Business/fundamental evidence

From accepted source-owned versioned evidence:

- SEC comparative evidence
- OpenDART comparative evidence
- 003690 insurance semantics
- TSM/WRD foreign-statement semantics
- SKHY issuer-level bridge
- persisted accepted event evidence where independently eligible

Do not copy old stock prices from REV6/REV7 packets.

Do not copy old packet PASS flags.

Reassemble from source-owned components.

---

# 11. Generic current-stock business evidence binder

Implement a deterministic owner/binder that accepts:

- current REV8 stock/security identity
- current fresh price/technical component packet
- frozen Class-C version identity
- accepted business fact graph
- current proof cutoff
- current source policy

and emits:

- current complete stock packet
- business evidence refs
- exact source authority
- packet hash

Every business fact must be rechecked for eligibility at the REV8 proof cutoff.

Do not recalculate original historical financial periods.

---

# 12. Bind versioned comparative financial facts

Use the sealed REV8:

`sealed-live/class-c/business-versioned-<ticker>.json`

where accepted comparison facts exist.

For each fact require:

- current canonical security/issuer matches
- source provider remains original
- source filing/report remains original
- current/prior periods unchanged
- currency/unit unchanged
- quality/source-use unchanged
- version SHA bound
- no old Class-A value consumed
- proof cutoff >= original admissible publication/source time

The file itself explicitly records:

`old_class_a_values_consumed = false`

Preserve this invariant.

---

# 13. Preserve special business semantics

## CPNG

- historical OHLC anomaly handling unchanged
- business evidence binding must not alter technical state

## 003690

- exact insurance-revenue canonical semantics preserved
- accepted revenue / operating-income comparisons preserved
- no old mixed-filing tuple reintroduced

## TSM

- accepted FPI financial purpose/period and field-specific supersession preserved

## WRD

- accepted IFRS/HK statement boundary and RMB-thousands semantics preserved

## 000660

- only accepted eligible comparisons survive
- previously denied operating/net fields remain denied

## SKHY

Bind through exact REV6 bridge:

`SKHY security`
→ `same legal issuer`
→ `OpenDART issuer`
→ original accepted revenue comparison

Preserve:

- `ISSUER_BUSINESS_EVIDENCE_ELIGIBLE = true`
- `SECURITY_PER_SHARE_BRIDGE_ELIGIBLE = false`
- `SECURITY_VALUATION_BRIDGE_ELIGIBLE = false`
- price/technical transfer count = 0

---

# 14. SNDK accepted event evidence — do not relabel as current Class B

REV8 fresh event acquisition was explicitly unavailable.

Do not claim the earlier SNDK event was collected in the REV8 run.

Audit the accepted SNDK completion evidence and its persisted source record.

Possible legitimate result:

## Persisted reported-event evidence is currently eligible

If the existing typed/source policy permits a previously source-owned reported event to remain usable as **versioned persisted business evidence**:

- preserve original publication date
- preserve original event acquisition/source artifact
- bind its current version/record identity
- mark it explicitly as persisted historical business evidence
- do not call it REV8 Class-B acquisition

Then it may satisfy the stock business union.

## Existing contract does not permit persisted event reuse

Then SNDK remains blocked.

Do not silently reclassify the role.

If a generic `VERSIONED_PERSISTED_BUSINESS_EVIDENCE` distinction is needed, add it only after proving the current 24-role inventory lacks a necessary evidence-state distinction.

Do not create a SNDK exception.

---

# 15. 005930 / 047810 invariance

These two already PASS in the REV8 base stock owner.

They must remain PASS.

Do not replace their current accepted evidence merely to force a uniform code path.

The binder must support:

- base owner already complete
- comparative-version binding
- persisted-event binding
- issuer bridge

without requiring every subject to use the same evidence type.

---

# 16. Re-run all 22 current stock packets

Using the sealed REV8 current Class-A sources:

require a new matrix with:

- ticker
- current attempt ID
- fresh price roles
- technical state
- business evidence type(s)
- business source/version hashes
- current eligibility
- mandatory missing
- packet status
- packet hash

Goal:

`22/22 CURRENT STOCK PACKETS PASS`

But honest partial is allowed.

No provider calls.

---

# 17. Current stock negative controls

At minimum:

- accepted comparative fact + wrong ticker -> fail
- accepted fact + wrong issuer -> fail
- version hash tamper -> fail
- old price introduced through business version -> fail
- source period altered -> fail
- denied 000660 sibling field resurrected -> fail
- SKHY per-share transfer -> fail
- SNDK old event labelled current Class-B -> fail
- stale/ineligible persisted event -> fail
- fresh current price missing -> fail
- fresh price attempt mismatch -> fail

---

# 18. P1-C — complete full-source run seed and authority graph

Only after:

- KR mandatory source observer passes or an exact blocker remains
- all 22 current stock packets pass

attempt full composition.

Do not emit accepted whole-source artifacts from partial components.

---

# 19. FullSourceRunSeed contract

Produce an immutable seed binding the existing REV8 proof.

At minimum:

- proof run:
  `rev8-live-20260927T083836Z`
- proof mode:
  `AD_HOC_LIVE_SOURCE_PROOF`
- source policy hash
- acquisition inventory hash
- repository/code freeze
- US attempt ID
- KR attempt ID
- current stock cohort hash
- US market source hash
- KR market source hash
- KRX night source hash
- Class-B acquisition/denial set hash
- Class-C version-set hash
- 22 current packet hashes
- SKHY bridge hash
- authority contract hash

Do not use the current wall clock as a fake market timestamp.

---

# 20. Role generation binding

For all 24 roles bind:

- acquisition class
- mandatory/optional
- market
- source generation
- owner
- provider
- source/denial artifact
- exact semantic hash
- current eligibility
- authority scope

Rules:

## ATTEMPT_FRESH

Must bind to the exact REV8 market sub-attempt.

No old REV6/REV7 Class-A values.

## RUN_FRESH_ONCE

Bind only the exact REV8 run-level acquisition or explicit REV8 denial.

Do not relabel a prior run acquisition as REV8 Class B.

## VERSIONED_PERSISTED_ALLOWED

Bind exact frozen Class-C record/version set.

## OPTIONAL_UNAVAILABLE

Bind explicit policy denial.

No bare null.

---

# 21. US whole-source packet

Bind:

- REV8 US market aggregate PASS
- US14 current stock packets
- REV8 KRX night/publication context
- Class-B optional denials
- eligible Class-C roles
- authority subset
- FullSourceRunSeed

All required US Class-A source values must be from:

`rev8-live-20260927T083836Z:us:A1`

or the exact frozen REV8 US attempt identity.

No mixed generation.

---

# 22. KR whole-source packet

Bind:

- KR mandatory market packet only after P1-A closes
- KR8 current stock packets
- optional investor-flow denial or qualified optional packet
- eligible Class-C roles
- authority subset
- FullSourceRunSeed

All KR Class-A source values must bind:

`rev8-live-20260927T083836Z:kr:A1`

No page/stock source from another attempt.

---

# 23. Build source authority — no weaker parallel graph

Integrate with existing:

`scripts/m12dr_financial_source_authority.py`
and
`build_source_authority`

or the current canonical authority owner.

Do not bypass it with a "unit-test-only PASS" allocator.

Required authority edges:

`run seed`
→ `role generation`
→ `owner`
→ `provider`
→ `request / source artifact / persisted record`
→ `normalizer/projector`
→ `quality/source-use`
→ `market/security/issuer scope`
→ `consumer field`

Derived evidence must retain input IDs.

---

# 24. Current stock/business authority

The authority graph must distinguish:

- current security-level Class-A evidence
- persisted issuer/business evidence

A persisted financial fact does not become current-price evidence.

A current price does not become financial authority.

For SKHY:

- monitored security remains SKHY
- issuer-business source remains OpenDART / same legal issuer
- no security valuation bridge

For SNDK persisted event if admitted:

- source publication remains original
- current proof only owns the **decision to reuse the eligible persisted evidence**
- it does not own the event publication.

---

# 25. Whole-source packet hashes

On PASS produce:

- FullSourceRunSeed SHA
- US whole-source packet SHA
- KR whole-source packet SHA
- combined full-source packet SHA
- full authority graph SHA
- current 22-stock cohort SHA
- optional-denial-set SHA

All non-null.

---

# 26. Offline deterministic replay twice

Network must remain disabled.

Replay:

1. KR source qualification
2. 22 current stock packets
3. Class-C version eligibility
4. US market owner
5. KR market owner
6. KRX night owner
7. whole-source composition
8. authority graph

twice.

Require exact equality of all semantic hashes.

---

# 27. Qualification flags

## `NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED`

Set true only if the sealed REV8 cohort replays completely offline and all full authority gates pass.

## `COMPLETE_SOURCE_ADAPTER_QUALIFIED`

Do **not** set automatically merely because offline repair passes.

Audit the qualification meaning.

Because REV9 modifies post-capture owner/qualification/composition logic after the REV8 acquisition:

- if current policy allows a captured real live cohort + exact raw replay under repaired generic owner logic to qualify the concrete source adapter, document why and set true;
- otherwise keep false with exact:
  `FINAL_LIVE_ADAPTER_REQUALIFICATION_REQUIRED`.

Do not weaken the definition.

R2B dry-run generation does not require production scheduler promotion.

---

# 28. Generate R2B blind-comparison instruction on source-packet PASS

If a complete sealed full-source packet and authority graph are produced, generate the next work instruction even if production promotion still requires a later live requalification.

Name/scope:

**R2B — Sealed REV8 Source, Independent-Blind + Monitoring-AI 24-Message Dry Run**

Do not execute it in REV9.

---

# 29. R2B must support independent blind comparison

The generated R2B instruction must create **two physically/logically separate output layers**.

## Layer 1 — Blind source-only review bundle

Create **before any model call**.

It must contain only source-derived material needed for independent judgment:

- immutable full-source packet identity
- run seed / authority graph hashes
- US/KR market source packet
- 22 stock source/business packets
- current price/technical context
- qualified financial/business evidence
- explicit unavailable/denied fields
- source refs
- no Monitoring AI output
- no prompt response
- no model verdict
- no renderer verdict text

Seal:

- blind bundle ZIP
- SHA-256
- creation timestamp
- source packet hash

After sealing, it must never be modified.

## Layer 2 — Monitoring AI result bundle

Only after Layer 1 is sealed:

run the actual Monitoring AI:

- Market
- Core
- A
- B
- validators
- renderer

and package model outputs/messages separately.

The blind bundle must not contain or reference model verdict content.

---

# 30. R2B 24-message set

Monitoring-AI result set:

- US market: `1`
- US stocks: `14`
- KR market: `1`
- KR stocks: `8`
- total: `24`

Telegram:
`0`

recipient intent:
`0`

production DB decision/warning write:
`0`

scheduler mutation:
`0`

provider calls:
`0`

Use exact sealed REV8/REV9 full-source packet.

---

# 31. Blind-comparison workflow contract

The generated R2B instruction must support this review sequence:

1. provide the source-only blind bundle first;
2. independently evaluate the same data without exposing Monitoring AI verdicts;
3. freeze independent assessment artifact/hash;
4. only then expose Monitoring AI result bundle;
5. compare:
   - Overall
   - New Buyer
   - Holder
   - stance/ratio
   - Directional Core
   - Price Timing
   - business/financial evidence usage
   - technical evidence usage
   - uncertainty
   - unsupported claims
   - omitted important evidence
   - source attribution
   - disagreements and cause.

The system must not require the independent reviewer to see Monitoring AI output before the independent assessment is sealed.

---

# 32. REV9 network/provider policy

Hard zero:

- Kiwoom
- OHLCV
- SEC
- OpenDART
- KRX
- Finnhub
- Nasdaq
- FRED
- EIA
- ECOS
- Alpha Vantage
- Massive
- news providers
- any external HTTP

All source inputs come from the sealed REV8 bundle.

---

# 33. REV9 model/production policy

Hard zero:

- model
- Market
- Core
- A
- B
- renderer
- Telegram
- recipient intent
- production DB writes
- warning writes
- scheduler mutation
- broker action
- deploy
- main merge
- push
- service restart

REV9 only repairs offline source ownership/composition.

---

# 34. Completion terminals

## Full source packet PASS

`M12DS_R6_R5F_R2B0_R5_REV9_SEALED_COHORT_SOURCE_AUTHORITY_PASS`

Require:

- KR page completion contract PASS
- current stock `22/22`
- full run seed
- US whole-source packet
- KR whole-source packet
- combined full-source packet
- full authority graph
- deterministic replay twice
- `NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`
- R2B blind-comparison instruction generated
- R2B execution = 0

## KR dependency cannot close

`M12DS_R6_R5F_R2B0_R5_REV9_KR_CONSUMED_PAGE_DEPENDENCY_GAP`

Return exact API/output field requiring omitted pages.

No recollection.

## Current business binder partial

`M12DS_R6_R5F_R2B0_R5_REV9_CURRENT_BUSINESS_BINDING_PARTIAL`

Return exact ticker/evidence-class/reason.

Do not copy old PASS flags.

## Full authority gap

`M12DS_R6_R5F_R2B0_R5_REV9_FULL_SOURCE_AUTHORITY_GAP`

Return exact role/generation/authority edge.

Do not recollect.

---

# 35. Regression boundaries

Preserve:

- REV8 raw source bytes
- 88 current stock source roles
- US market 22/22 source
- KRX night source
- CPNG anomaly semantics
- bounded SEC/OpenDART evidence
- TSM/WRD semantics
- 003690 insurance semantics
- SKHY issuer bridge
- 000660 denied fields
- 005930/047810 current base PASS
- acquisition role inventory unless a direct evidence-class bug is proven
- investment judgment policy
- Overall/New Buyer/Holder policy
- renderer/message policy
- scheduler design

No threshold relaxation.

---

# 36. Validation

Required:

## KR page completion
- consumer-complete contract unit tests
- transport-exhausted contract tests
- source-path ledger
- continuation metamorphic tests
- target-session negatives
- KOSPI/KOSDAQ genericity

## Business binder
- 22 current packet proof
- comparative fact binding
- 003690 regression
- TSM/WRD regression
- SKHY issuer bridge regression
- SNDK persisted event class audit
- 005930/047810 invariance
- old Class-A injection negative

## Full composition
- FullSourceRunSeed
- role generation matrix
- US packet
- KR packet
- authority graph
- wrong-generation negatives
- hash tamper negatives
- optional denial negatives
- prohibited provider negatives
- replay twice

## Repository
- previous REV2–REV8 regression set
- full pytest
- Ruff
- `git diff --check`
- Investment Knowledge
- Chart Knowledge
- disabled production entrypoint smoke
- secret scan
- unchanged skip/xfail identity

No network.

---

# 37. Required result bundle

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- REV8 identity/SHA receipt
- repository identities
- changed-file inventory

## KR page contract
- four-read blocker before/after
- `kr-market-consumed-source-paths.json`
- completion-mode matrix
- metamorphic proof
- final KR source qualification

## Current stock business
- accepted business version matrix
- business evidence-class matrix
- SNDK persisted event audit
- 22 current packet matrix
- packet hashes
- 005930/047810 invariance
- SKHY bridge receipt
- business authority refs

## Full composition
- FullSourceRunSeed
- run seed SHA
- 24-role generation/binding matrix
- US whole-source packet + SHA
- KR whole-source packet + SHA
- combined packet + SHA
- full authority graph + SHA
- optional denial set + SHA
- replay #1 / #2 comparison

## Qualification
- `NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED`
- `COMPLETE_SOURCE_ADAPTER_QUALIFIED`
- exact remaining promotion/live-requalification blocker if any

## Next instruction
If source packet PASS:
- R2B blind-comparison work-instruction MD
- R2B instruction ZIP
- SHA sidecar
- explicit:
  `R2B executed = false`

## Safety / validation
- network counters = 0
- model counters = 0
- production side-effect counters = 0
- validation logs
- secret scan
- bundle manifest.

---

# 38. Final principle

REV8 already captured the live data.

REV9 must not solve owner/composition defects by recollecting it.

The task is to prove exactly which captured source bytes each consumer needs, bind already-accepted business evidence to the new price generation without importing old prices, and then construct one immutable source-authority graph.

Only after that source packet is sealed may Monitoring AI be tested—and the source-only blind bundle must be frozen first so an independent assessment can be made without contamination from the Monitoring AI verdict.

