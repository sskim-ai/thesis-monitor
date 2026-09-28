# Thesis Monitor — R2B-R5
## Sealed Market Producer→Consumer Adapter Closure + Monitoring-AI 24-Message Dry Run

**Purpose:** close the sole pre-model contract drift left by R2B-R4:

`SEALED_MARKET_PRODUCER_CONSUMER_INPUT_CONTRACT_UNCLOSED`

R2B-R4 proves:

- V2 blind fairness = PASS
- Core readiness = 22/22
- A readiness = 22/22
- B readiness = 22/22
- source hashes unchanged
- quality supplement unchanged
- no unclassified model-visible time refs
- no quality-owner gaps

The only failure is that the sealed unified producer emits:

`market_sources.component`

while the existing accepted Market consumer:

`scripts.m12ds_r4_r4_market.market_context`

expects:

`packet['market_context']`

for both US and KR.

R2B-R5 must first prove the exact existing Market input contract field-by-field, then create the smallest deterministic **offline sealed-source adapter** that projects the unified source-owned market components into the exact accepted Market consumer shape.

It must not:
- fetch new market data;
- call production DB/cache to fill missing values;
- synthesize empty market context;
- copy an old market packet;
- change market investment policy;
- weaken Market validators;
- change source authority;
- skip Market and run stock messages only.

After the adapter passes exact parity/preflight for US and KR, R2B-R5 may immediately execute the existing bounded Monitoring-AI plan and seal the 24-message result bundle.

---

# 0. Newest SoT

Adopt R2B-R4 as newest execution SoT.

R2B-R4 result ZIP SHA-256:

`fda4d4fdbe007df116b800de217ec3b85fd89e7bf61b4c08844a9daf2f9c1698`

Terminal:

`R2B_R4_PREMODEL_CONTRACT_DRIFT`

Repository:

- branch:
  `codex/r2b-r4-monitoring-ai-execution`
- base:
  `d3761b155050abdb3aa0bf5c36c272adab725f16`
- instruction:
  `9e825f499baa18ba985a8eda2cea1402c49e1825`
- audit implementation:
  `691c53a3d5258da04637e24acdbafb3d59ed5d05`
- final:
  `4b216489c31c47ebc1f9efbb92da3a04b4766deb`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

R2B-R4 integrity:

- ZIP/sidecar exact
- internal bundle manifest:
  `37/37`
- missing:
  `0`
- hash mismatch:
  `0`
- size mismatch:
  `0`
- extra manifest-scope files:
  `0`

R2B-R4 accepted state:

- blind fairness gate:
  `PASS_V2`
- Core:
  `22/22`
- A:
  `22/22`
- B:
  `22/22`
- Market input ready:
  `0/2`
- actual Market/Core/A/B calls:
  `0/0/0/0`
- rendered previews:
  `0/24`
- model input binding:
  `NOT_ISSUED`
- provider refresh:
  `0`
- production side effects:
  `0`
- independent assessment content read:
  `false`
- reveal gate:
  `CLOSED`

Validation:

- focused:
  `524 PASS`
- full:
  `6159 PASS / 63 unchanged skips`
- Ruff / diff / Investment Knowledge / Chart Knowledge:
  PASS

Do not reopen Core/A/B/quality/UNKNOWN_LIMIT/stored-price-rule work.

---

# 1. Immutable source and blind identities

Preserve exact sealed source:

- FullSourceRunSeed:
  `df3b7f1102fcacd27b70e594fb58b139644a7ba1daa18620279bf1a455916bdc`
- US whole-source packet:
  `b2b603850e517c70d6a9a201b297952677d6542271f72db6f0eecbdebe09fdb1`
- KR whole-source packet:
  `d3081027ec1203a5af09adc590b13ca81dce3c049a65b988606a0d3311f74845`
- combined full-source packet:
  `c4fbc25ec81abe61c3981bfaa44204cc7e15cc252f25cbe6aedc6b2a1de9b44f`
- source-authority graph:
  `0b69d1913e139078ed42b0fb1c0b01928b065fd2d76863e3835622b3ee0992b6`

Blind source ZIP SHA-256:

`d705d36dabfa99f8d096a2bce4ddf996229680650cb09a45abffb5d7e9213ec3`

Quality supplement SHA-256:

`2d59748a3064a91d1ddcbbb68aefb90a961eaf4e9baa4334619c4e0db38f7edd`

Neutral V2 freeze receipt SHA-256:

`9c9eec930400db3e7390984b6045e72961684e3db774eedd633b3f6fa1e9650d`

No source hash may change in R2B-R5.

---

# 2. Anti-contamination remains hard-gated

R2B-R5 may verify only the neutral V2 freeze receipt.

It must not read/open/search/mount/parse/diff/summarize:

- independent assessment V1 JSON/MD/ZIP
- independent assessment V2 JSON/MD/ZIP
- any independent market or stock verdict
- any independent ratio/stance

through Monitoring-AI result sealing.

Required:

`independent_assessment_content_read = false`

through result seal.

---

# 3. Exact R2B-R4 Market failure

For both markets, R2B-R4 passed the original whole-source packet unchanged to:

`scripts.m12ds_r4_r4_market.market_context`

The existing Market consumer delegate accessed:

`packet['market_context']`

and raised:

`KeyError('market_context')`

Current unified producer:

`app.services.unified_full_source_cohort.compose_full_source`

publishes root keys including:

- `market`
- `run_seed_sha256`
- `market_sources`
- `publication_context`
- `night_and_publication_context` where applicable
- `class_c_versions`
- `optional_denials`
- `authority_subset`
- `authority_graph_sha256`
- `stocks`
- `persisted_business_events`

It does **not** publish top-level:

`market_context`

Do not fix this with:

`packet['market_context'] = packet['market_sources']['component']`

without proving the full consumer contract.

---

# 4. First task — recover the exact accepted Market consumer contract

Before implementation, audit the actual current accepted Market path.

At minimum inspect:

- `scripts.m12ds_r4_r4_market.market_context`
- its R3 delegate
- Market prompt/context builder
- Market typed schema
- Market semantic validator
- Market numeric validator/binder
- Market renderer input
- prior accepted/current-market smoke builders
- any prior successful Market 2/2 frozen inputs available in repository/history

Produce:

`market-consumer-contract-inventory.json`

For every required/optional input path record:

- consumer JSON/path/key
- type
- mandatory/optional
- owner
- semantic meaning
- source-time/session requirements
- numeric-registry requirement
- source-ref requirement
- coverage requirement
- denial/unavailable representation
- Market stage(s) consuming it
- renderer dependency
- whether the unified whole-source packet already owns an equivalent source value

No field may be populated by guesswork.

---

# 5. Field-by-field producer→consumer parity matrix

Produce:

`sealed-market-producer-consumer-parity-matrix.json`

For every Market consumer field:

- consumer field/path
- legacy/accepted owner
- unified source role
- exact sealed source artifact/ref
- source period/session
- source value
- source basis
- transformation required
- transformation owner
- numeric registry binding
- authority binding
- coverage state
- projection status:
  - EXACT
  - DETERMINISTIC_DERIVED
  - EXPLICIT_UNAVAILABLE
  - MISSING_UNRESOLVED
- output field/hash

Do this separately for US and KR.

A mandatory `MISSING_UNRESOLVED` field blocks model dispatch.

---

# 6. Do not treat old Market outputs as source authority

Prior successful Market messages/contexts may be used only to recover:

- shape
- schema
- ownership contract
- deterministic formatting rules

They may **not** supply:

- current values
- current session/date
- current breadth
- current macro values
- current night values
- current interpretation

All current Market facts must come from the sealed REV8/REV10/R2B source graph.

No historical value splicing.

---

# 7. Adapter architecture

Implement the smallest pure/offline adapter, repository naming permitting:

`project_sealed_market_context(...)`

Input:

- exact US or KR whole-source packet
- FullSourceRunSeed
- source-authority graph
- existing Market contract/config
- existing numeric binder/formatter policy

Output:

- exact accepted `market_context` structure required by the current Market consumer
- projection receipt
- context semantic hash

The adapter must be:

- deterministic
- side-effect free
- network free
- production DB/cache free
- source-authority preserving

It must not create a second Market policy engine.

---

# 8. US Market projection

Audit actual current sealed US market components.

At minimum preserve source-owned facts actually consumed by Market, including those available under the current contract such as:

- configured major-index/market symbol observations
- sector/style market observations/rankings where owned
- current/latest-published macro facts where retained
- KRX night/publication context where the US Market contract consumes it
- eligible Class-C market/macro facts
- explicit optional denials

Do not require fields removed by the current product policy merely because an older message format once had them.

Do not reintroduce:
- US index rows deliberately removed from user-facing messages
- WTI/yield rows if current renderer policy no longer exposes them
unless the current Market owner still consumes them internally and the sealed packet owns them.

Current policy/renderer—not old documentation prose—owns the field set.

---

# 9. KR Market projection

Audit sealed KR market components.

Preserve exact source-owned:

- KOSPI/KOSDAQ completed-session context
- sector rankings/sector observations actually consumed
- breadth
- optional investor flows only if the sealed owner qualified them
- explicit optional denials
- eligible Class-C macro/publication facts actually consumed

Do not fabricate flow values.

Do not turn optional unavailable into zero.

Do not mix source pages/attempts outside the sealed KR packet.

---

# 10. Session and assessment ownership

The projected Market context must preserve the existing session contract.

At minimum validate consistency of:

- `market`
- `assessment_date`
- `market_session`
- `assessment_state`
- source session/date
- query/proof time
- latest-published informational dates

Do not make the ad-hoc proof run appear to be a scheduled production run.

Do not relabel old published macro/night timestamps as the Market query timestamp.

---

# 11. Market fact catalog

If the accepted consumer expects a `fact_catalog`, populate it only from source-owned sealed facts.

Every fact must preserve:

- canonical fact/ref ID
- field semantic
- value
- unit
- source period/as-of
- source artifact/ref
- source authority
- eligibility
- market scope

No raw provider/parser debug metadata in model-visible context.

No unowned text-only facts.

---

# 12. Numeric registry

If the Market contract expects numeric provenance, rebuild the accepted registry deterministically from the sealed facts.

Use the existing canonical numeric binder.

Each model-visible numeric value must bind to the accepted key structure, such as the repository-native equivalent of:

- fact ID
- field path
- value
- unit
- semantic type

Do not let the model invent/recalculate backend-owned market numbers.

No orphan numeric token.

---

# 13. Coverage / availability state

The projected Market context must carry the existing explicit coverage semantics.

For every expected block distinguish:

- available
- delayed/latest-published
- optional unavailable
- denied
- not applicable

Do not infer completeness from object presence alone.

Do not hide missing mandatory facts.

A mandatory coverage gap blocks Market readiness.

---

# 14. Publication / night context

The US Market adapter must bind the exact sealed night/publication context under its existing authority.

Do not copy raw KRX provider rows directly into model-visible Market context unless the existing Market owner does so.

Use the accepted normalized owner output.

Preserve:

- contract/product
- source date/session
- D/W/M state where current contract consumes it
- unavailable fields
- source refs

No source refresh.

---

# 15. Optional denials

Project explicit optional denials from the whole-source packet into the exact Market consumer representation.

Do not:

- omit an expected optional field silently
- replace denial with zero/empty numeric value
- treat optional denial as whole-Market failure unless existing policy does

The adapter must preserve the semantic distinction between absent and explicitly unavailable.

---

# 16. No live DB/cache dependency

R2B-R4 specifically identified that invoking the operating Market builder naively may read live DB/cache.

R2B-R5 must prove the adapter can run from the sealed source packet alone.

Required negative control:

- disable/block production DB/cache reads
- adapter still produces identical Market input

Any hidden read from:
- production DB
- cache
- current source service
- external provider

is a FAIL.

---

# 17. Deterministic Market projection proof

For each market:

run the sealed projection twice.

Require exact equality for:

- Market context semantic hash
- fact catalog hash
- numeric registry hash
- coverage hash
- source-ref set
- session identity
- prompt-input hash

No wall-clock entropy in semantic hash.

---

# 18. Existing Market consumer acceptance

Pass the projected packet into the exact current:

`scripts.m12ds_r4_r4_market.market_context`

and all downstream pre-model Market validators.

Require:

- US Market input readiness:
  `1/1 PASS`
- KR Market input readiness:
  `1/1 PASS`
- no KeyError
- no synthetic fallback
- no source-policy weakening

Produce exact accepted Market input hashes.

---

# 19. Market contract regression against accepted historical path

Where a prior successful Market 2/2 input artifact exists:

compare **shape/ownership semantics**, not current values.

Require:

- required keys parity
- schema parity
- source-ref semantics parity
- numeric registry semantics parity
- session/coverage semantics parity
- no newly introduced model-owned deterministic numbers

Differences caused by the newer product/source policy must be explicitly documented and accepted by current schema/validator—not hidden.

---

# 20. Preserve R2B-R3/R4 stock readiness

After Market adapter closure, re-run the current preflight.

Require unchanged:

- Core = 22/22
- A = 22/22
- B = 22/22
- quality applicability:
  - PRESENT 7
  - RECONSTRUCTIBLE 14
  - NOT_APPLICABLE 1
- quality supplement hash:
  `2d59748a3064a91d1ddcbbb68aefb90a961eaf4e9baa4334619c4e0db38f7edd`
- UNKNOWN_LIMIT PASS
- stored price-rule ownership 20/20
- model-visible time unclassified = 0

Market adapter work must not mutate stock input semantics.

---

# 21. Blind fairness remains PASS_V2

Verify:

- original blind source SHA
- quality supplement SHA
- neutral V2 receipt SHA

Required:

`BLIND_FAIRNESS_GATE = PASS_V2`

Independent V1/V2 contents remain unread.

The Market adapter must not add new **material model-visible market facts** that were absent from the blind source review.

Audit this explicitly.

If the adapter merely restructures already-present sealed source facts:
- fairness remains valid.

If it exposes a genuinely new economic fact that the blind reviewer did not receive:
- stop before model dispatch with:
  `R2B_R5_BLIND_MARKET_VIEW_MATERIAL_CHANGE`
- do not execute AI until independent review is refreshed.

---

# 22. Whole-cohort model-input binding

Only after:

- Market 2/2 readiness PASS
- Core/A/B 22/22 unchanged
- blind fairness PASS
- source/hash invariance PASS

issue:

`ISSUED_WHOLE_COHORT_READY`

The immutable binding must include:

- run-seed/source hashes
- Market US input/context hash
- Market KR input/context hash
- Market contract version/hash
- Core/A/B input hashes
- quality supplement hash
- 22 decision modes
- visible/denied ref sets
- prompt/schema/provider-wire hashes
- blind fairness receipt hash

No model call before this binding is sealed.

---

# 23. Execute the existing bounded Monitoring-AI plan

After binding:

- Market max `2`
- Core max `8`
- A max `8`
- B max `8`
- maximum total model calls `26`

Use existing frozen model configuration.

Expected:
- GPT-5.6 Sol
- existing xhigh reasoning plan
- per-call timeout `1200s`
- retry `0`
- semantic retry `0`
- repair `0`
- fallback `0`
- judge `0`
- provider/source refresh `0`

No selective rerun.

---

# 24. Required execution order

1. Market readiness frozen
2. Market calls
3. validate/freeze Market outputs
4. Core calls
5. validate/freeze Core outputs
6. A calls
7. validate/freeze A outputs
8. B calls
9. validate/freeze B outputs
10. final cross-axis/source-use validation
11. render
12. seal result bundle
13. only then open comparison gate

No independent assessment input anywhere.

---

# 25. Market model output constraints

Market AI may interpret only source-authorized Market facts.

Do not:

- recalculate backend metrics
- invent missing changes
- infer direction from absolute index level alone where no directional source exists
- convert unavailable optional data into neutral numeric values
- use raw provider metadata as facts

Market output must reference only accepted Market fact refs/numeric registry.

---

# 26. Stock model constraints remain unchanged

Preserve:

- UNKNOWN_LIMIT for SNDK
- CRCL/IBM/SKHY confidence-only quality semantics
- security valuation basis separation
- stored price-rule version ownership
- SKHY issuer bridge restrictions
- CPNG anomaly semantics
- 000660 denied sibling fields

No policy changes.

---

# 27. Required 24-message set

On full execution PASS:

- US Market = `1`
- US stocks = `14`
- KR Market = `1`
- KR stocks = `8`
- total = `24`

No Telegram send.

No recipient intent.

No production DB write.

No scheduler mutation.

---

# 28. Monitoring-AI result bundle

Create a new immutable result bundle with a new generation ID.

Include:

- REPORT.md
- summary.json
- Market adapter contract inventory
- producer/consumer parity matrix
- US/KR projected Market contexts
- Market context hashes
- Market input acceptance receipts
- whole-cohort model-input binding
- actual Market/Core/A/B call receipts
- raw/validated outputs
- validators
- 24 rendered previews
- message hashes
- source/hash binding
- anti-contamination receipt
- safety counters
- bundle manifest

Do not include independent assessment V1/V2 contents.

---

# 29. Seal before reveal

Before revealing Monitoring-AI results:

require:

- result ZIP finalized
- result ZIP SHA frozen
- 24 messages frozen
- call ledger frozen
- model/source binding frozen
- independent assessment content read = false

Then generate neutral receipt:

`MONITORING_AI_RESULT_SEALED_READY_FOR_COMPARISON`

No verdict content in the receipt.

Only after this receipt may the independent V2 assessment be opened.

---

# 30. Network / source policy

Hard zero source/provider refresh:

- Kiwoom
- stock/market OHLCV
- SEC
- OpenDART
- KRX
- news
- Alpha Vantage
- Massive
- any external source API

Only model API calls are allowed after complete preflight PASS.

---

# 31. Production side effects

Hard zero:

- Telegram
- recipient intent
- production DB decision/warning writes
- scheduler mutation
- notification mutation
- broker
- deploy
- main merge
- remote push
- service restart

---

# 32. Success terminal

`R2B_R5_MONITORING_AI_24_MESSAGE_PASS_READY_FOR_BLIND_COMPARISON`

Require:

- exact Market consumer contract audited
- US sealed Market adapter PASS
- KR sealed Market adapter PASS
- Market readiness 2/2
- Core/A/B readiness 22/22
- blind fairness PASS_V2
- no material blind-view change
- whole-cohort binding issued
- actual Monitoring-AI execution
- 24/24 rendered messages
- result sealed
- independent assessment unread through seal
- provider refresh 0
- production side effects 0
- comparison-ready neutral receipt generated

---

# 33. Failure terminals

## Consumer contract cannot be reconstructed

`R2B_R5_MARKET_CONSUMER_CONTRACT_GAP`

Model calls = 0.

Return exact consumer field/path and missing owner contract.

## Sealed source lacks mandatory Market fact

`R2B_R5_MARKET_SOURCE_COVERAGE_GAP`

Model calls = 0.

Do not fetch live data.

## Adapter source authority mismatch

`R2B_R5_MARKET_ADAPTER_AUTHORITY_GAP`

Model calls = 0.

Do not synthesize.

## Blind Market view materially changes

`R2B_R5_BLIND_MARKET_VIEW_MATERIAL_CHANGE`

Model calls = 0.

Require independent-review refresh before AI.

## Model-stage failures

Use exact:
- MARKET_MODEL_FAILURE
- CORE_MODEL_FAILURE
- A_MODEL_FAILURE
- B_MODEL_FAILURE
- RENDER_VALIDATION_FAILURE

No retry/repair.

---

# 34. Required tests

## Market contract
- exact required/optional key inventory
- type/schema checks
- session/date consistency
- coverage semantics
- numeric-registry completeness
- source-ref completeness

## Adapter
- US projection
- KR projection
- no DB/cache/network
- deterministic replay twice
- source hash invariance
- optional denial handling
- missing mandatory source negative
- authority tamper negative
- wrong market/session negative

## Consumer
- exact Market consumer accepts US
- exact Market consumer accepts KR
- no KeyError
- prompt-input hashes deterministic

## Stock regression
- Core 22/22
- A 22/22
- B 22/22
- UNKNOWN_LIMIT
- quality supplement
- stored price rules

## Fairness
- neutral V2 receipt exact
- independent contents unread
- Market blind-view materiality audit

## Repository
- full pytest
- Ruff
- git diff --check
- Investment Knowledge
- Chart Knowledge
- secret scan
- unchanged skip/xfail identity

---

# 35. Required result artifacts

At minimum:

- REPORT.md
- summary.json
- R2B-R4 result identity/SHA
- repository identities
- changed-file inventory

## Market adapter
- `market-consumer-contract-inventory.json`
- `sealed-market-producer-consumer-parity-matrix.json`
- US projected market context
- KR projected market context
- US/ KR context hashes
- fact-catalog hashes
- numeric-registry hashes
- coverage/session receipts
- authority binding receipts
- DB/cache/network-isolation proof
- deterministic replay receipt
- historical shape/parity audit

## Preflight
- Market 2/2 readiness
- Core/A/B 22/22
- fairness receipt
- Market blind-view materiality audit
- whole-cohort binding + SHA

## AI execution on PASS
- model-call ledger
- Market/Core/A/B inputs/outputs
- validators
- 24-message inventory
- 24 message hashes
- Monitoring-AI result bundle SHA
- neutral comparison-ready receipt

## Safety
- provider refresh 0
- production side effects 0
- validation logs
- secret scan
- bundle manifest

---

# 36. Final principle

Do not solve `KeyError('market_context')` with a key rename.

The task is to prove that the sealed, source-owned unified Market components can be transformed—deterministically and without live dependencies—into the exact existing Market consumer contract, including fact ownership, coverage, session semantics and numeric provenance.

Once that adapter is proven for both markets, the previously ready Core/A/B path may finally execute.
