# Thesis Monitor — R2B-R6
## Canonical Core→A Catalog Hash Closure + Sealed Market/Core Continuation
### Fix Unicode serializer ownership only; reuse validated Market/Core outputs; execute A/B; render and seal 24-message Monitoring-AI result

**Purpose:** close the sole deterministic local contract defect left by R2B-R5.

R2B-R5 successfully executed and sealed:

- Market `2/2`
- Core `8/8 calls`, `22/22 subjects`
- SNDK existing `UNKNOWN_LIMIT` validation
- source/fairness invariants

It stopped **before the first A model call** because an identical parsed Core authority catalog was hashed by two different JSON serializers:

- `unified_snapshot_contract.digest()` uses `ensure_ascii=False`
- `m12da_source_use_contract.canonical_sha256()` uses `ensure_ascii=True`

When fresh Core atomic-claim text contains non-ASCII characters, the byte serialization differs and therefore the SHA differs, even though the parsed JSON object is identical.

R2B-R6 must fix only the **derivative Core→A catalog hash ownership** and continue from the already-sealed R2B-R5 Market/Core outputs.

Do not rerun Market or Core.
Do not refresh providers.
Do not change source/economic facts.
Do not read the independent assessment before the final Monitoring-AI result bundle is sealed.

---

# 0. Newest SoT

Adopt R2B-R5 as newest execution SoT.

R2B-R5 result ZIP SHA-256:

`06a6f53db269a2ed344bc29a94e02c429a3cfcf799de075ddc8ea96165009695`

Terminal:

`A_MODEL_FAILURE`

Precise phase:

`local Core-to-A input composition, before any A dispatch`

Failure:

`source_input_expectation_authority_catalog_mismatch`

Repository:

- branch:
  `codex/r2b-r5-market-adapter`
- base / R4 final:
  `4b216489c31c47ebc1f9efbb92da3a04b4766deb`
- instruction-first commit:
  `825aabfe963eaf8f4623bb33b89a65249b0726f1`
- initial implementation:
  `63a97972d2bf41a3479eddc154f81c1c13b9b5c3`
- native night numeric ownership:
  `8ea8cff19c462841a046501ecfcfdc37fd2a6163`
- exact validated dispatch commit:
  `bea5f6d93b638b1b8215098023994dc1697e197c`
- report/final repository identity:
  use the exact value from the R5 result bundle
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

Accepted R5 execution:

- Market calls:
  `2/2`
- Market validated:
  `2/2`
- Core calls:
  `8/8`
- Core validated:
  `22/22`
- Core ordinary:
  `21`
- Core UNKNOWN_LIMIT:
  `1` (SNDK)
- A calls:
  `0/8`
- B calls:
  `0/8`
- rendered messages:
  `0/24`
- total actual model calls:
  `10/26`
- retry:
  `0`
- provider refresh:
  `0`
- production side effects:
  `0`
- independent assessment content read:
  `false`
- reveal gate:
  `CLOSED`

Validation at exact dispatch SHA:

- focused:
  `541 PASS`
- full:
  `6176 PASS / 63 unchanged skips`
- Ruff / diff / Investment Knowledge / Chart Knowledge:
  PASS

Do not invalidate or rerun the already accepted 10 model calls unless an integrity check proves they are corrupted.

---

# 1. Immutable source / fairness identities

Preserve:

- FullSourceRunSeed:
  `df3b7f1102fcacd27b70e594fb58b139644a7ba1daa18620279bf1a455916bdc`
- US whole-source packet:
  `b2b603850e517c70d6a9a201b297952677d6542271f72db6f0eecbdebe09fdb1`
- KR whole-source packet:
  `d3081027ec1203a5af09adc590b13ca81dce3c049a65b988606a0d3311f74845`
- combined full-source packet:
  `c4fbc25ec81abe61c3981bfaa44204cc7e15cc252f25cbe6aedc6b2a1de9b44f`
- source authority graph:
  `0b69d1913e139078ed42b0fb1c0b01928b065fd2d76863e3835622b3ee0992b6`
- blind source ZIP:
  `d705d36dabfa99f8d096a2bce4ddf996229680650cb09a45abffb5d7e9213ec3`
- quality supplement:
  `2d59748a3064a91d1ddcbbb68aefb90a961eaf4e9baa4334619c4e0db38f7edd`
- neutral V2 freeze receipt:
  `9c9eec930400db3e7390984b6045e72961684e3db774eedd633b3f6fa1e9650d`

Blind fairness remains:

`PASS_V2`

unless R2B-R6 changes model-visible economic/source content—which this task prohibits.

---

# 2. Anti-contamination hard gate

R2B-R6 may verify only the neutral V2 freeze receipt.

It must not read/open/search/mount/parse/diff/summarize:

- independent assessment V1 JSON/MD/ZIP
- independent assessment V2 JSON/MD/ZIP
- any independent verdict
- any independent BUY/SELL ratio
- any independent Overall/New Buyer/Holder decision

until the Monitoring-AI result bundle is fully sealed.

Required through result seal:

`independent_assessment_content_read = false`

---

# 3. Exact R5 root cause

The stopped stack:

`Execution.before_a`
→ `chain`
→ `r2b_r2_preflight.subject_inputs`
→ `r2b_r2_contract.bound_chain`
→ `freeze_source_use_input_expectation`

Current R5 source:

`r2b_r2_contract.bound_chain`

stores:

`catalog_sha256 = digest(cat)`

where:

`app.services.unified_snapshot_contract.digest()`

serializes JSON with:

`ensure_ascii=False`

The source-use contract's canonical owner:

`scripts.m12da_source_use_contract.canonical_sha256()`

serializes with:

`ensure_ascii=True`

The input expectation validator recomputes the authority catalog using the source-use canonical serializer.

Result:

- identical parsed JSON catalogs
- different serialized bytes when non-ASCII text exists
- different SHA-256
- local pre-A failure

No source/economic-value mismatch was found.

---

# 4. Accepted post-stop forensic evidence

R2B-R5 metadata-only diagnosis established:

- empty-claim catalogs:
  hash agreement `21/21`
- actual-claim catalogs:
  disagreement `15/21`
- agreement:
  `6/21`
- ASCII-escaped vs Unicode-decoded parsed objects:
  identical for every subject
- first runtime mismatch:
  `CORZ`

Structurally affected catalogs:

- CORZ
- CPNG
- CRCL
- GOOGL
- HUT
- IBM
- MU
- RXRX
- SKHY
- TSLA
- WRD
- WULF
- 000660
- 003690
- 005930

This list is diagnostic only.

Do not hardcode the subject list into production logic.

---

# 5. Canonical hash ownership rule

For any source-use catalog consumed by:

`m12da_source_use_contract`

the canonical catalog SHA owner is:

`scripts.m12da_source_use_contract.canonical_sha256`

or the exact repository-native equivalent owned by that source-use contract.

Do not use the generic full-source packet digest as the catalog identity.

Different semantic objects may use different canonical hash contracts.

Do not globally replace `unified_snapshot_contract.digest()`.

---

# 6. Minimal implementation repair

Audit:

`scripts/r2b_r2_contract.py`

especially:

`bound_chain(...)`

Current problematic operation:

`catalog_sha256=digest(cat)`

Repair it so that the **source-use catalog identity** is calculated by the source-use canonical hash owner.

Preferred shape:

- import/use `canonical_sha256` from `scripts.m12da_source_use_contract`
- compute `catalog_sha256 = canonical_sha256(cat)`
- pass that exact hash through derivative/binding/expectation
- keep other unrelated full-source hashes on their existing digest owners

Do not change:

`app.services.unified_snapshot_contract.digest()`

globally.

A global digest change could alter:

- source packet hashes
- run seed hashes
- authority graph identities
- previously sealed evidence

and is prohibited in R2B-R6.

---

# 7. One semantic object → one canonical identity per contract

Audit all Core→A catalog hash comparisons.

Require:

- producer-side derivative catalog SHA
- source-use expectation catalog SHA
- source-use authority-manifest catalog SHA
- validator recomputation

all use the same source-use canonical serializer.

Do not permit:

- serializer A at producer
- serializer B at validator

for the same semantic identity.

Create:

`core-to-a-catalog-hash-owner-matrix.json`

with:

- semantic object
- producer
- consumer
- current serializer
- repaired canonical owner
- before hash
- after hash
- parsed-object equality
- validation result

---

# 8. Unicode and canonical-JSON regression tests

Add generic tests.

At minimum:

## ASCII

Catalog contains only ASCII text.

Require producer/consumer hash equality.

## Hangul

Include Korean text.

Require equality.

## Mixed Latin + Hangul

Require equality.

## Other Unicode

Include at least one additional Unicode script or symbol.

Require equality.

## Escaped-vs-unescaped serialization

Two JSON serializations representing the same parsed object:

- `ensure_ascii=True`
- `ensure_ascii=False`

must converge to the **source-use canonical hash** after parsing/canonicalization.

## Key order

Different input mapping order:
- same canonical hash.

## Array order

Where array order is semantically meaningful:
- reordered array must change hash.

Where the source-use contract already normalizes a collection before hashing:
- preserve that exact existing normalization.

Do not introduce new sorting semantics.

## Tamper negative

Change actual claim text/value/ref:
- hash must change
- expectation validation must fail.

---

# 9. Preserve non-ASCII claim bytes/content

Do not sanitize, transliterate, ASCII-strip, normalize away, or replace:

- Korean text
- mixed-script text
- Unicode punctuation

merely to make hashes equal.

The object content stays unchanged.

Only canonical hash ownership changes.

If the existing canonical source-use serializer has a Unicode normalization contract, preserve it exactly.

Do not invent NFC/NFKC behavior if absent.

---

# 10. Replay all sealed Core outputs offline

Before any new model call:

load the exact R2B-R5 accepted Market/Core output artifacts.

Verify:

- Market accepted output hashes exact
- Core raw output hashes exact
- Core accepted output hashes exact
- schemas exact
- source run seed exact
- source packet hashes exact

Do not rerun Market/Core.

Then rebuild the Core→A deterministic chain with the hash repair.

Require:

- all 21 evidence-based ordinary subjects pass source-input expectation
- SNDK UNKNOWN_LIMIT path remains valid
- full A input composition reaches `22/22`

No model calls during this proof.

---

# 11. Model-visible content invariance audit

The hash repair must not change model-visible economic/judgment content.

For every A subject context compare before-vs-after where "before" can be structurally generated up to the failing hash gate:

- claim objects
- claim text
- source refs
- quality state
- security valuation basis
- current price
- stored price rules
- technical context
- market context
- decision mode

Allowed difference:

- derivative catalog SHA / expectation SHA / binding metadata that uses the repaired canonical hash

Not allowed:

- claim text change
- numeric change
- evidence addition/removal
- authority widening
- price/timing change
- business-quality state change
- UNKNOWN_LIMIT change

If model-visible content changes:
- stop with:
  `R2B_R6_MODEL_VIEW_CHANGED_BY_HASH_REPAIR`
- no model dispatch.

---

# 12. Blind fairness remains valid

Because the repair changes only canonical identity metadata for the same parsed object, it should not change the independent review source view.

Prove:

- blind source ZIP unchanged
- quality supplement unchanged
- economic/source fact set unchanged
- market contexts unchanged
- stock contexts unchanged

Require:

`BLIND_FAIRNESS_GATE = PASS_V2`

No V3 independent assessment is required for a pure identity/hash repair.

If any material model-visible economic fact changes:
- stop
- do not execute AI.

---

# 13. Reissue continuation input binding

Do not reuse the R5 whole-cohort binding blindly because Core results now exist and A dependency metadata is being repaired.

Create a new continuation binding, for example:

`ISSUED_R2B_R6_AFTER_CORE_FREEZE`

It must bind:

- original sealed source/run seed
- R5 generation ID:
  `20260928-r2b-r5-20260928T012541Z`
- exact accepted Market output hashes
- exact accepted Core output hashes
- repaired canonical catalog hash contract/version
- A request builders/policies/schemas
- B request builders/policies/schemas
- quality supplement hash
- UNKNOWN_LIMIT policy hash
- stored-price-rule binding
- neutral V2 fairness receipt
- independent-content unread state

Seal before first A call.

---

# 14. Reuse sealed Market outputs

R2B-R5 accepted:

- US Market call PASS
- KR Market call PASS

Do not rerun.

Verify exact:

- prompt SHA
- schema SHA
- raw output SHA
- accepted output SHA
- semantic validation receipt
- source binding

Carry these forward as immutable upstream model outputs.

---

# 15. Reuse sealed Core outputs

R2B-R5 accepted:

- 8/8 Core calls
- 22/22 subjects
- 21 evidence-based
- 1 UNKNOWN_LIMIT

Do not rerun.

Verify each batch:

- prompt SHA
- schema SHA
- raw output SHA
- accepted output SHA
- transport receipt
- semantic validator
- subject set

Carry forward exact frozen Core output.

No rewriting accepted Core text.

---

# 16. A execution

After Sections 6–15 PASS:

freeze A requests from:

- accepted R5 Core outputs
- repaired deterministic authority binding
- sealed source/business/price/technical evidence
- quality states
- security valuation basis
- market context
- stored-price-rule version ownership
- UNKNOWN_LIMIT state

Use existing batch topology.

Maximum A calls:

`8`

Rules:

- one attempt
- retry 0
- semantic retry 0
- repair 0
- fallback 0
- judge 0
- no selective rerun

Validate each accepted batch immediately.

All 22 A subjects must pass before B starts.

---

# 17. B execution

Only after complete A result is validated and frozen.

Maximum B calls:

`8`

Use:

- exact R5 Core freeze
- new R6 A freeze
- existing deterministic runtime materialization
- sealed source/market/technical context
- existing Holder policy
- SNDK UNKNOWN_LIMIT

Rules:

- one attempt
- retry 0
- semantic retry 0
- repair 0
- fallback 0
- judge 0
- no selective rerun

Require 22/22 validated.

---

# 18. Total model-call accounting

Historical R5 accepted upstream calls:

- Market = `2`
- Core = `8`

R2B-R6 new calls:

- Market = `0`
- Core = `0`
- A = max `8`
- B = max `8`

Cumulative Monitoring-AI dry-run call count on full success:

`26`

New R6 model calls on full success:

`16`

Do not describe R6 as 26 new calls.

---

# 19. Render 24 messages

After B 22/22:

render from:

- sealed R5 Market outputs
- sealed R5 Core outputs
- sealed R6 A outputs
- sealed R6 B outputs
- unchanged source packet / runtime deterministic fields

Required:

- US Market = 1
- US stocks = 14
- KR Market = 1
- KR stocks = 8
- total = `24`

All messages must bind the same source run seed.

---

# 20. Result-bundle provenance

The final Monitoring-AI result bundle must make stage provenance explicit:

## Market/Core

source generation:
`R2B-R5`

## A/B

source generation:
`R2B-R6 continuation`

## Data/source

same sealed REV8/REV10 packet

This is not cross-generation source stitching.

It is a bounded continuation from already frozen validated model-stage outputs after a deterministic local identity-contract repair.

Prove exact dependency hashes.

---

# 21. Do not expose partial Core judgments before final seal

Although Core outputs exist internally:

- independent reviewer must not receive them yet
- no comparison
- no partial decision summary
- no per-ticker Core verdict exposure

Reveal gate remains closed until the full Monitoring-AI 24-message bundle is sealed.

---

# 22. Monitoring-AI result bundle

Create a new immutable result bundle.

Suggested filename:

`thesis-monitor-20260928-r2b-r6-MONITORING_AI_RESULT.zip`

Include:

- REPORT.md
- summary.json
- R5 identity/SHA
- source identities
- repaired hash-owner contract
- Unicode/hash tests
- continuation binding
- inherited R5 Market/Core receipts or exact hash-linked copies
- new A/B requests/prompts/schemas/raw/accepted outputs
- stage validators
- 24 rendered messages
- message hashes
- cumulative and R6-new model call ledger
- anti-contamination receipt
- safety counters
- bundle manifest

Do not include independent assessment V1/V2 content.

---

# 23. Seal before comparison

Before comparison gate opens:

require:

- Monitoring-AI result ZIP finalized
- result SHA frozen
- all 24 messages frozen
- cumulative call ledger frozen
- source/stage binding frozen
- independent assessment content read = false

Generate neutral receipt:

`MONITORING_AI_RESULT_SEALED_READY_FOR_COMPARISON`

containing only:

- result filename/hash
- message count
- source packet hash
- V2 neutral receipt hash
- stage lineage
- no investment verdict text

Only then may the external independent V2 assessment be opened.

---

# 24. No comparison inside R2B-R6

Do not:

- compare Monitoring AI to independent V2
- score agreement
- alter thresholds
- rerun disagreements
- edit policies based on result

Return sealed output to Chat.

Comparison happens after this task.

---

# 25. Source/provider refresh

Hard zero:

- Kiwoom
- stock/market OHLCV
- SEC
- OpenDART
- KRX
- news
- Alpha Vantage
- Massive
- any source API

No data refresh.

---

# 26. Production side effects

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

# 27. Success terminal

`R2B_R6_MONITORING_AI_24_MESSAGE_PASS_READY_FOR_BLIND_COMPARISON`

Require:

- canonical Core→A catalog hash owner unified
- global source packet digest unchanged
- Unicode/mixed-script/tamper tests PASS
- all R5 Market/Core artifacts exact
- A input composition 22/22
- A calls 8/8 accepted
- B calls 8/8 accepted
- 24/24 rendered messages
- result bundle sealed
- independent assessment unread through seal
- provider refresh 0
- production side effects 0
- comparison-ready neutral receipt generated

---

# 28. Failure terminals

## Canonical hash contract gap

`R2B_R6_CANONICAL_CATALOG_HASH_GAP`

No model calls.

## R5 upstream artifact drift

`R2B_R6_UPSTREAM_MARKET_CORE_FREEZE_DRIFT`

No model calls.

## Model-visible content changed by repair

`R2B_R6_MODEL_VIEW_CHANGED_BY_HASH_REPAIR`

No model calls.

## A model failure

`R2B_R6_A_MODEL_FAILURE`

No B calls.

## B model failure

`R2B_R6_B_MODEL_FAILURE`

Preserve accepted A output.

## Render/validation failure

Use exact stage-specific terminal.

No retry/repair.

---

# 29. Required tests

## Hash ownership

- ASCII catalog
- Hangul catalog
- mixed Latin/Hangul catalog
- additional Unicode
- escaped/unescaped equivalent parsed object
- key-order invariance under canonical serializer
- semantically meaningful array reorder negative
- actual claim tamper negative
- wrong ref negative

## Whole cohort

- all 21 ordinary Core catalogs
- SNDK limit path
- 22/22 A input composition
- no source/policy view change

## Upstream freeze

- Market 2/2 exact hash
- Core 8/8 exact hash
- Core subject population 22/22
- SNDK limit validation exact

## A/B

- A 22/22
- B 22/22
- source-ref validation
- UNKNOWN_LIMIT
- business quality
- security valuation basis
- stored price rules

## Fairness

- V2 receipt exact
- blind source hash exact
- independent content unread
- no model-view economic change

## Repository

- full pytest
- Ruff
- git diff --check
- Investment Knowledge
- Chart Knowledge
- secret scan
- unchanged skip/xfail identity

---

# 30. Required result artifacts

At minimum:

- REPORT.md
- summary.json
- R5 result identity/SHA
- repository identities
- changed-file inventory

## Hash repair

- `core-to-a-catalog-hash-owner-matrix.json`
- serializer contract audit
- Unicode regression matrix
- before/after 22-subject catalog hash matrix
- parsed-object equality proof
- tamper-negative proof
- global source-hash invariance

## Continuation

- R5 Market freeze verification
- R5 Core freeze verification
- continuation model-input binding + SHA
- A 22-subject input hash matrix
- B 22-subject input hash matrix

## Model execution

- A call ledger
- B call ledger
- A/B raw + accepted outputs
- validators
- cumulative model ledger
- R6-new model ledger
- 24 rendered messages
- message inventory/hashes
- Monitoring-AI result ZIP identity/SHA
- neutral comparison-ready receipt

## Safety

- provider refresh 0
- production side effects 0
- independent content unread receipt
- validation logs
- secret scan
- bundle manifest

---

# 31. Final principle

The same parsed source-use catalog must have one canonical identity.

Do not normalize away Unicode and do not change the global full-source digest.

Fix only the Core→A source-use catalog hash to use the canonical serializer already owned by the source-use contract.

Then resume from the already-sealed successful Market/Core outputs rather than spending new model calls or introducing judgment variance.
