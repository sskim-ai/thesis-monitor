# Thesis Monitor — M12DS-R6-R5F-R2B0-R5-REV7
## Offline Full-Source Composition & Authority Closure
### 22/22 stock/business packets → declared run seed → US/KR whole-source packets → end-to-end source authority

**Purpose:** close the sole remaining REV6 prequalification blocker:

`FULL_MARKET_STOCK_SOURCE_COMPOSITION_NOT_PROVEN`

REV6 already proves 22/22 stock source/business packets. REV7 must not collect or repair source data. It must implement and prove the missing source-only composition layer that binds existing market owners, stock owners, KRX night/publication context, acquisition classes, optional denials, and the SKHY issuer bridge into one deterministic full-source graph.

This task is **offline/network-free**. It must not run Market/Core/A/B, render messages, send Telegram, mutate schedulers, or relabel historical proof data as current.

---

# 0. Newest accepted SoT

Adopt REV6 as the newest SoT.

REV6 result ZIP SHA-256:

`b653fb8503be9439b91300f135353338c49f0323aa13fb391975000b29c816aa`

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV6_SKHY_ISSUER_BUSINESS_BRIDGE_PASS`

REV6 accepted facts:

- stock source/business packets: `22/22 PASS`
- blocked stock subjects: `0`
- previous controls invariant: `21/21`
- SKHY issuer-level business bridge: PASS
- bridged metric:
  `revenue_comparison`
- SKHY issuer-business eligibility: true
- SKHY per-share bridge eligibility: false
- SKHY security valuation bridge eligibility: false
- original 000660 operating-income/net-income denials unchanged
- network calls: `0`
- model/Market/Core/A/B/render/send/scheduler/production writes: `0`

Repository:

- base:
  `0558dcbf205d689fd6b08930421b71a6afdbed0b`
- REV6 instruction:
  `f166ba089451b7b0f5e90d40a565c390d8f683d8`
- REV6 implementation/final:
  `febd3931fe6003f6d3d6f6c61b17607ebc67058a`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

REV6 validation:

- new identity/scope/provenance tests: `55 PASS`
- focused: `942 PASS`
- full: `5930 PASS / 63 unchanged skips`
- Ruff/diff/Investment Knowledge/Chart Knowledge/disabled smoke: PASS

REV6 bundle integrity was independently rechecked:

- ZIP/sidecar exact
- `bundle-manifest.json`: `145/145`
- missing: `0`
- hash mismatch: `0`
- size mismatch: `0`
- extra manifest-scope files: `0`

Do not overwrite REV6.

---

# 1. Exact remaining blocker

REV6 network-free source prequalification is:

`FAIL_CLOSED`

with sole blocker:

`FULL_MARKET_STOCK_SOURCE_COMPOSITION_NOT_PROVEN`

Root cause from REV6:

> Bounded stock owners and mandatory market aggregate owners are individually available, but no declared full-role run seed / whole-source packet with end-to-end source-authority bindings is produced by the current source-only adapter.

REV6 explicitly reports:

- `stock_source_business_complete = 22`
- `stock_source_business_prequalified = true`
- `issuer_business_bridge_pass = true`
- `KRX_historical_native_owner_replay = PASS`
- `full_market_stock_run_seed_hash = null`
- `full_source_packet_hash = null`
- `source_only_full_packet_assembler_present_in_REV6 = false`
- `NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = false`

This is an orchestration/authority-composition gap, not a provider-data gap.

---

# 2. Do not reopen accepted source work

Do not redesign or recollect:

- stock OHLCV/current-price owner
- R2B0 sealed 88 stock roles
- CPNG anomaly isolation
- technical evidence
- bounded SEC/OpenDART owners
- TSM/WRD FPI semantics
- 003690 insurance revenue semantics
- SKHY same-legal-issuer business bridge
- KRX native history/night owner
- investment judgment policy
- Overall/New Buyer/Holder policy
- renderer/message policy
- scheduler timing policy

No source refresh is authorized in REV7.

---

# 3. Source-role inventory is frozen

Use the existing:

`docs/operations/UNIFIED_ACQUISITION_CLASSES.json`

REV6 inventory counts:

- `ATTEMPT_FRESH = 5`
- `RUN_FRESH_ONCE = 4`
- `VERSIONED_PERSISTED_ALLOWED = 12`
- `OPTIONAL_UNAVAILABLE = 3`

Total roles:

`24`

Do not add/remove/reclassify roles in REV7 unless a direct inventory bug is proven and separately documented.

---

# 4. Mandatory role inventory

At minimum the existing mandatory roles include:

## Both markets

- `universe`
- `security_identity`
- `stored_thesis_and_business_metadata`
- `stock_chart_adjusted_daily_weekly_monthly`
- `stock_valuation_unadjusted_price`

## US

- `us_market_prices`
- `night_and_publication_context`

## KR

- `kr_local_indices_sectors_breadth`

All other roles retain their existing mandatory/optional state from the inventory.

Do not promote optional roles to mandatory merely to maximize completeness.

Do not allow a mandatory role to become an optional denial.

---

# 5. Implement a source-only full packet assembler

Add or extend a generic source-only composition API.

Suggested conceptual objects:

- `FullSourceRunSeed`
- `RoleBinding`
- `USWholeSourcePacket`
- `KRWholeSourcePacket`
- `FullSourcePacket`
- `SourceAuthorityGraph`

Names may follow repository conventions.

The assembler must accept **already materialized source-owner outputs/receipts**.

It must not invoke providers.

It must not invoke models.

---

# 6. FullSourceRunSeed contract

The run seed must explicitly bind the whole source proof.

At minimum include:

- proof/run mode:
  `OFFLINE_NETWORK_FREE`
- run seed ID
- seed version
- source policy version/hash
- acquisition-class inventory hash
- universe identity/hash
- market:
  - US
  - KR
  - combined proof
- source cutoff/proof cutoff
- attempt generation identity
- attempt ID where applicable
- run-fresh-once acquisition generation
- persisted-source version set identity
- optional-denial set identity
- stock cohort hash
- stock packet hashes
- market owner input/output hashes
- KRX night/publication owner hash
- issuer bridge identity/hash
- authority-contract hash

Every child packet must carry the same seed hash.

---

# 7. Do not invent a fake common source timestamp

Offline source proof artifacts may originate from different accepted source times.

REV7 must preserve each role's original:

- acquisition time
- publication time
- session/date
- version/as-of
- attempt identity

Do not relabel historical/frozen source data as current.

The run seed's proof cutoff is an **offline composition cutoff**, not a market-data timestamp.

If an existing temporal contract requires same-attempt or same-session inputs, enforce it.

If a frozen artifact cannot satisfy that contract:
- do not alter its timestamp;
- return an exact temporal-cohort blocker.

---

# 8. Acquisition-class binding semantics

## ATTEMPT_FRESH

All retained values for one market attempt must bind to one exact attempt generation.

Required checks:

- no cross-attempt stock price mixing
- no cross-attempt market aggregate mixing
- no old current-price substitution
- complete required-set identity
- exact source receipts

The offline proof may use a sealed replay generation, but it must identify it as replay/proof and preserve original source times.

## RUN_FRESH_ONCE

Bind once per run seed.

Price retry semantics must not create a new business/event/night acquisition.

Require exact original acquisition ID/hash.

## VERSIONED_PERSISTED_ALLOWED

Bind exact eligible version/record/source receipts at the proof cutoff.

No latest-row heuristic.

No missing provenance.

## OPTIONAL_UNAVAILABLE

Bind an explicit owner/source-policy denial.

No missing-to-zero.

No unbound `null`.

---

# 9. Market packet composition — US

Build a typed US market source packet from declared market owners.

Mandatory components must include the existing:

- `us_market_prices`
- `night_and_publication_context`

and the shared mandatory baseline roles where the current architecture consumes them.

Optional roles are admitted only if their existing owners/eligibility pass.

Examples from the inventory include:

- earnings calendar
- US exchange breadth
- rates/credit/liquidity/risk
- energy
- Korea macro where actually consumed
- central-bank published events
- explicit optional exclusions

Do not add a role merely because data exists.

Do not splice an unrelated historical normalized market candidate into the proof.

---

# 10. Market packet composition — KR

Build a typed KR market source packet from declared market owners.

Mandatory market component:

- `kr_local_indices_sectors_breadth`

Preserve optional semantics for:

- `kr_market_investor_flows`
- `kr_overnight_cross_assets`
- macro/publication roles
- explicit excluded KR FX

No Alpha-backed cached value may leak through the excluded FX role.

---

# 11. Market owner source requirement

A market role may count toward prequalification only if it is backed by an exact frozen **source-owned** owner artifact/receipt sufficient to rerun or validate the declared owner.

A pure synthetic value fixture may test API/schema behavior but may **not** satisfy the final source-authority gate.

If REV7 cannot locate source-owned frozen inputs for a mandatory market role:

return exact blocker such as:

`FROZEN_US_MARKET_SOURCE_INPUT_NOT_AVAILABLE`

or

`FROZEN_KR_MARKET_SOURCE_INPUT_NOT_AVAILABLE`

Do not synthesize market values.

Do not fetch live values in REV7.

---

# 12. Stock packet composition

Use the accepted REV6 `22/22` stock source/business packets.

Do not recompute the stock source chain from external providers.

Require:

- exact stock packet hash
- exact stock result hash
- ticker/security ID
- market
- current mandatory status
- source graph hash
- business union authority
- issuer bridge state where applicable

All 22 must be present once.

No duplicate/missing subject.

---

# 13. SKHY issuer-business authority binding

The whole-source graph must represent the REV6 bridge explicitly.

Required chain:

`SKHY monitored security`
→ `same-legal-issuer bridge`
→ legal issuer
→ OpenDART issuer `DART:00164779`
→ original 000660 filing/field occurrences

The authority graph must preserve:

- `ISSUER_LEVEL_CROSS_SECURITY_EVIDENCE`
- original provider = OpenDART
- original issuer ID
- original filing/report
- exact current/prior revenue occurrences
- KRW/consolidated/period lineage
- original quality/source-use
- target monitored security = SKHY

It must also preserve:

- security per-share bridge = false
- security valuation bridge = false
- price/technical transfer count = 0

No downstream authority consumer may interpret the bridged evidence as:

- SEC-native SKHY financial evidence
- SKHY per-share evidence
- SKHY valuation evidence

---

# 14. Full source authority graph

Every retained consumed role must have an explicit authority edge.

At minimum represent:

`run seed`
→ `role`
→ `owner`
→ `provider/source family`
→ `request/source artifact or persisted record`
→ `normalization/projection owner`
→ `quality/source-use state`
→ `market/security/issuer scope`
→ `consumer packet field`

For derived facts:

- preserve exact input fact IDs
- preserve derivation owner/version
- never assign authority to renderer prose or prior AI output.

---

# 15. Integrate with build_source_authority

Audit:

`scripts/m12dr_financial_source_authority.py`
and its `build_source_authority` consumer path.

REV6 states that it still expects separately frozen:

- source generation
- quality
- issuer bindings

REV7 must wire the new whole-source packet into the existing authority contract rather than bypassing it.

Do not create a parallel weaker authority model.

If the existing builder is financial-specific, make the smallest generic extension or adapter necessary to accept the full role graph while preserving existing financial validations.

---

# 16. Source-generation ownership

Define exact generation identities for:

- attempt-fresh stock sources
- attempt-fresh market sources
- run-fresh-once sources
- persisted-version sources
- optional denials

Reject:

- same role from two generations
- cross-attempt price values
- market source from an unrelated proof generation
- persisted source after cutoff
- source receipt whose hash does not match the packet
- unowned raw value

---

# 17. FullSourcePacket structure

Produce at minimum:

## US

- run seed
- US market packet
- US14 stock packets
- relevant shared role bindings
- KRX night/publication context
- optional/denied role bindings
- authority graph
- US whole-source packet hash

## KR

- run seed
- KR market packet
- KR8 stock packets
- relevant shared role bindings
- optional/denied role bindings
- authority graph
- KR whole-source packet hash

## Combined proof

- common seed identity
- US packet hash
- KR packet hash
- 22-stock cohort hash
- role inventory hash
- combined authority hash
- full-source packet hash

No model input/output is part of this packet.

---

# 18. Deterministic replay

Run the full source composition twice from the exact same frozen inputs.

Require:

- run seed hash identical
- US source packet hash identical
- KR source packet hash identical
- combined full-source packet hash identical
- authority graph hash identical
- optional denial set identical

No current wall-clock timestamp may enter the digest unless explicitly excluded from semantic hash.

---

# 19. Exact positive gate

Set:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`

only if all of the following hold:

1. 22/22 stock source/business packets pass;
2. mandatory US market owner inputs are source-owned and valid;
3. mandatory KR market owner inputs are source-owned and valid;
4. KRX night/publication owner replay passes where consumed;
5. all mandatory roles have authority bindings;
6. all optional retained roles have authority bindings;
7. all optional unavailable roles have explicit denials;
8. one immutable run seed binds the graph;
9. no cross-attempt mixing;
10. no historical artifact relabeled current;
11. no banned provider value enters;
12. SKHY issuer bridge authority/isolation is preserved;
13. deterministic second replay matches;
14. full packet/authority hashes are non-null;
15. negative tests pass.

`complete_source_adapter_qualified` remains false until the later current-source execution.

---

# 20. Mandatory negative controls

At minimum prove:

## Run seed/generation

- stock packet from wrong run seed -> fail
- market packet from wrong run seed -> fail
- attempt-fresh market from attempt A + stocks from attempt B -> fail
- stale/future generation mismatch -> fail

## Roles

- missing mandatory US market role -> fail
- missing mandatory KR market role -> fail
- missing mandatory stock role -> fail
- optional missing without explicit denial -> fail
- optional explicit denial -> may pass
- mandatory role denied -> fail

## Source authority

- source artifact hash tamper -> fail
- owner/provider mismatch -> fail
- raw value with no source ref -> fail
- source-use denied field retained -> fail
- wrong security/issuer -> fail

## SKHY bridge

- issuer bridge missing -> fail
- bridge target changed -> fail
- original provider relabeled SEC -> fail
- per-share/valuation eligibility changed true -> fail
- 000660 price/technical inserted into SKHY -> fail
- bridged revenue source occurrence tampered -> fail

## Providers

- Alpha value admitted -> fail
- Massive/mock admitted -> fail
- undeclared fallback -> fail

## Temporal

- original historical source relabeled current -> fail
- run cutoff used as fake market timestamp -> fail
- incompatible attempt/session role mixed -> fail

---

# 21. Frozen market input audit

Before implementation claims PASS, produce:

`frozen-market-source-input-matrix.json`

For every mandatory market role record:

- market
- role
- owner
- source artifact/fixture path
- source receipt/hash
- original source time/session
- replayability
- authority eligibility
- whether it is a real captured source artifact or synthetic test fixture

Synthetic-only mandatory inputs cannot close the gate.

If source-owned frozen inputs are missing:
- stop at exact partial terminal;
- do not perform network collection.

---

# 22. Do not use historical candidate splicing

REV6 explicitly refused:

`historical_market_candidate_splice`

REV7 must preserve that constraint.

Do not:

- take an old market packet from another generation and simply attach it to the 22-stock cohort;
- copy old market packet hashes into the new full packet;
- rewrite market dates;
- make a historical packet appear current.

A frozen source artifact may be replayed **only** as an explicit offline owner proof with its own original identity, and only where the composition contract permits proof-mode binding.

---

# 23. Full consumed-source graph documentation

Update or verify:

`docs/operations/UNIFIED_CONSUMED_SOURCE_GRAPH.md`

Document:

- full run seed
- acquisition class boundaries
- US market roles
- KR market roles
- stock roles
- issuer bridge
- optional roles/denials
- authority graph
- generation relationships
- current execution distinction

Documentation must match executable schema/tests.

---

# 24. No source refresh in REV7

Required provider/network count:

`0`

Specifically:

- OHLCV = 0
- Kiwoom = 0
- SEC = 0
- OpenDART = 0
- KRX live = 0
- Finnhub = 0
- Nasdaq Trader = 0
- FRED/EIA/ECOS/Fed = 0
- events/news = 0
- Alpha Vantage = 0
- Massive = 0

Only frozen/local artifacts and deterministic owner replay are permitted.

---

# 25. R2B generation condition

If and only if:

`NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`

then generate an immutable **R2B current-source + 24-message dry-run work instruction** and SHA sidecar.

Do not execute it.

The generated R2B instruction must require:

- one genuine current source cohort
- exact pre-network call plan
- US/KR query-time source semantics
- US conditional 08:10 → 08:15 → 08:20 recollection
- KR conditional 16:00 → 16:05 → 16:10 recollection
- no cross-attempt Class-A mixing
- Class-B once per run
- eligible Class-C versions
- Alpha/Massive/mock/undeclared fallback = 0
- concrete current full-source packet
- current authority graph
- existing Market/Core/A/B owners
- US market 1 + US14 = 15 messages
- KR market 1 + KR8 = 9 messages
- total `24`
- Telegram send = 0
- recipient intent = 0
- scheduler mutation = 0
- production decision/warning DB write = 0
- package all 24 rendered messages for direct review
- no official-finality claim.

---

# 26. Completion terminals

## Outcome A — full network-free prequalification PASS

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV7_FULL_SOURCE_COMPOSITION_AUTHORITY_PASS`

Require:

- 22 stock packets
- source-owned US/KR market proof inputs
- full run seed
- US/KR whole-source packet hashes
- full source packet hash
- authority graph hash
- deterministic replay
- negative tests
- `NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED = true`
- R2B instruction generated
- R2B execution = 0

## Outcome B — frozen mandatory market input absent

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV7_FROZEN_MARKET_SOURCE_INPUT_GAP`

Return exact market/role/input missing.

No network.

## Outcome C — composition/authority implementation gap

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV7_FULL_SOURCE_COMPOSITION_GAP_REMAINS`

Return exact:
- role
- owner
- generation
- authority edge
- schema/contract failure.

Do not reopen stock/business source acquisition.

## Outcome D — temporal cohort contract cannot be proven offline

Terminal:

`M12DS_R6_R5F_R2B0_R5_REV7_OFFLINE_TEMPORAL_COHORT_GAP`

Preserve source timestamps.

Do not relabel.

---

# 27. Production side effects hard zero

Required:

- model = 0
- Market = 0
- Core = 0
- A = 0
- B = 0
- renderer = 0
- Telegram = 0
- recipient intent = 0
- production DB decision/warning write = 0
- scheduler mutation = 0
- notification mutation = 0
- broker = 0
- deploy = 0
- main merge = 0
- push = 0
- service restart = 0

The production adapter remains disabled.

---

# 28. Regression boundaries

Must preserve:

- 22/22 REV6 stock packets
- 21-control exact invariance
- SKHY issuer bridge
- SKHY no per-share/valuation bridge
- CPNG anomaly handling
- TSM/WRD semantics
- 003690 insurance revenue
- 000660 existing denied fields
- KRX accepted owner output hash:
  `68991ed322b5d067f46e6d0a1ae4f9151533ff10177e4d31ab61997c39210937`
- acquisition class inventory
- banned-provider policy
- current scheduler design
- investment/model/message policies

REV7 is composition/authority work only.

---

# 29. Validation sequence

Run:

1. schema/unit tests for FullSourceRunSeed/RoleBinding/FullSourcePacket
2. acquisition-class binding tests
3. frozen mandatory market-input audit
4. US whole-source composition
5. KR whole-source composition
6. SKHY issuer-bridge authority tests
7. full authority builder tests
8. negative generation/role/source/temporal/provider tests
9. deterministic replay twice
10. 22 stock invariance
11. KRX replay regression
12. full pytest
13. Ruff
14. `git diff --check`
15. Investment Knowledge
16. Chart Knowledge
17. disabled unified entrypoint smoke
18. secret scan
19. unchanged skip/xfail identity

No network anywhere.

---

# 30. Required result bundle

Return immutable ZIP + `.sha256` with at minimum:

- `REPORT.md`
- `summary.json`
- REV6 identity/SHA receipt
- repository identities
- changed-file inventory

## Inventory / frozen inputs

- acquisition-class inventory/hash
- all-source-role matrix
- mandatory/optional matrix
- frozen-market-source-input matrix
- 22 stock packet identity/hash matrix
- KRX owner replay identity

## Composition

- FullSourceRunSeed schema
- frozen run seed instance
- run seed SHA
- US market packet
- US packet SHA
- KR market packet
- KR packet SHA
- combined full-source packet
- full-source packet SHA
- deterministic second-replay receipt

## Authority

- role binding matrix
- source generation matrix
- full authority graph
- authority graph SHA
- build_source_authority before/after integration proof
- SKHY issuer bridge authority receipt
- banned-provider exclusion receipt

## Negative tests

- wrong seed
- cross-attempt
- missing mandatory role
- unbound optional
- source hash tamper
- security/issuer mismatch
- bridge leakage
- historical relabel
- prohibited provider

## Outcome

- `NETWORK_FREE_SOURCE_ADAPTER_PREQUALIFIED`
- exact blockers if false
- R2B instruction + ZIP/SHA only if PASS
- R2B executed = false

## Safety / validation

- network counters
- model/delivery/scheduler counters
- config/env/DB/scheduler invariance
- focused/full validation
- secret scan
- bundle manifest.

---

# 31. Final principle

REV6 closed stock/business evidence.

REV7 must prove that every consumed source in the full US/KR run belongs to one declared source graph with one immutable run seed and explicit authority.

Do not solve a composition gap by collecting more data or by pretending unrelated historical packets are one run.
