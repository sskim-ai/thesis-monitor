# Thesis Monitor — R2B-R4
## Quality-Supplement Blind Freeze Accepted → Execute Monitoring AI 24-Message Dry Run

**Purpose:** resume the already-ready 22-subject Monitoring-AI dry run after resolving R2B-R3's comparison-fairness gate.

R2B-R3 closed the typed quality owner and proves:

- Core input readiness `22/22`
- A/New Buyer actual materialization `22/22`
- B/Holder readiness `22/22`
- quality-owner applicability resolved `22/22`
- no unresolved owner gaps
- source packet unchanged
- model calls `0`

R2B-R3 stopped only because three source-derived quality diagnoses—CRCL, IBM, SKHY—were not present in the original blind source bundle. An independent blind assessment V2 has now been separately frozen **after receiving only that source-derived quality supplement and before any Monitoring-AI model output existed**.

R2B-R4 must verify only the neutral V2 freeze receipt, issue the whole-cohort model-input binding, execute the existing bounded Monitoring-AI plan, render the 24 dry-run messages, and seal the Monitoring-AI result bundle.

No source/provider refresh. No further source-policy repair is authorized inside R2B-R4.

---

# 0. Newest SoT

Adopt R2B-R3 as the newest implementation/source-use SoT.

R2B-R3 result ZIP SHA-256:

`16786785bd476eb2b6241fded2b0e1a92e3411bd807e45f8d6e1a06d94e52bf8`

Terminal:

`R2B_R3_BLIND_REVIEW_MATERIAL_SOURCE_VIEW_CHANGED`

Repository:

- branch:
  `codex/r2b-r3-typed-quality-owner`
- base:
  `9321a76b41b499879e75668348f84c2c1ad59a10`
- instruction:
  `e5ccd4cd606cd4ef00035ab39c695c8849233fe4`
- implementation:
  `476f7db98e72de5a7316ab4ac4af03031f8780d8`
- final:
  `d3761b155050abdb3aa0bf5c36c272adab725f16`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

R2B-R3 integrity:

- outer ZIP matches sidecar
- internal manifest entries: `78/78`
- missing: `0`
- hash mismatch: `0`
- size mismatch: `0`
- extra manifest-scope files: `0`

R2B-R3 accepted state:

- applicability:
  - PRESENT `7`
  - EXPECTED_OWNER_OUTPUT_RECONSTRUCTIBLE `14`
  - PROVEN_NOT_APPLICABLE `1`
- quality supplements:
  `14`
- unresolved quality-owner gaps:
  `0`
- Core ready:
  `22/22`
- A ready:
  `22/22`
- B ready:
  `22/22`
- source-input ready:
  `22/22`
- model input binding:
  `NOT_ISSUED_BLIND_SOURCE_DISCLOSURE_BLOCKED`
- actual Market/Core/A/B calls:
  `0/0/0/0`
- actual messages:
  `0/24`
- provider calls:
  `0`
- production side effects:
  `0`
- independent assessment content read:
  `false`
- reveal gate:
  `CLOSED`

Validation:

- focused:
  `520 PASS`
- full:
  `6155 PASS / 63 unchanged skips`
- Ruff / diff / Investment Knowledge / Chart Knowledge:
  PASS

Do not reopen the typed-quality owner in R2B-R4.

---

# 1. Immutable source identities

Preserve exact source packet:

- run seed:
  `df3b7f1102fcacd27b70e594fb58b139644a7ba1daa18620279bf1a455916bdc`
- US packet:
  `b2b603850e517c70d6a9a201b297952677d6542271f72db6f0eecbdebe09fdb1`
- KR packet:
  `d3081027ec1203a5af09adc590b13ca81dce3c049a65b988606a0d3311f74845`
- combined source:
  `c4fbc25ec81abe61c3981bfaa44204cc7e15cc252f25cbe6aedc6b2a1de9b44f`
- source authority graph:
  `0b69d1913e139078ed42b0fb1c0b01928b065fd2d76863e3835622b3ee0992b6`

Original blind source review ZIP:

`thesis-monitor-20260927-r2b-BLIND_SOURCE_REVIEW.zip`

SHA-256:

`d705d36dabfa99f8d096a2bce4ddf996229680650cb09a45abffb5d7e9213ec3`

Do not modify the original blind ZIP.

---

# 2. R2B-R3 deterministic quality supplement

Accepted supplement aggregate SHA-256:

`2d59748a3064a91d1ddcbbb68aefb90a961eaf4e9baa4334619c4e0db38f7edd`

Material blind-view additions identified by R2B-R3:

## CRCL

- `financial_hard_error`
- `sec_business_occurrence_conflict`
- business-quality effect:
  `CONFIDENCE_ONLY`
- supplement SHA:
  `55b5dfd7b0eeb9aad6d2022e9e70e43fa2576ddfdc8321c0fea39c47a587c82b`

## IBM

- `financial_hard_error`
- `sec_field_lineage_unverified`
- business-quality effect:
  `CONFIDENCE_ONLY`
- supplement SHA:
  `f9e20c580a8e6700a8ca109cad1e9c48a9c47659723c111268127e4171d1a097`

## SKHY

- `extreme_observation_uncorroborated`
- `financial_hard_error`
- `net_income_exceeds_revenue`
- `unusually_high_or_low_operating_margin`
- business-quality effect:
  `CONFIDENCE_ONLY`
- supplement SHA:
  `d0849a31c776fec6ed991969a42526a19b934ad499142c11aae8dfee23ec0242`

R2B-R4 must preserve these source-derived confidence limits.

Do not make them directional-negative evidence.

---

# 3. Independent blind assessment V2 has already been frozen

Neutral V2 freeze receipt:

`thesis-monitor-20260928-INDEPENDENT_FREEZE_RECEIPT_V2.json`

Expected SHA-256:

`9c9eec930400db3e7390984b6045e72961684e3db774eedd633b3f6fa1e9650d`

The receipt proves:

- original blind source SHA:
  `d705d36dabfa99f8d096a2bce4ddf996229680650cb09a45abffb5d7e9213ec3`
- quality supplement SHA:
  `2d59748a3064a91d1ddcbbb68aefb90a961eaf4e9baa4334619c4e0db38f7edd`
- parent V1 independent assessment SHA:
  `95776285ba2653ec102517315f16259c7d9f0f314ab5af01b715308b87dda50b`
- V2 independent assessment JSON SHA:
  `9a083de6bef2b5b0e617136e10a67eed00ff5cacffc79809825f2ea51d34557d`
- V2 independent assessment bundle SHA:
  `b025e86ba211fafe89d56be8268652c6482d589ea12e8510dbf040442e40ed77`
- Monitoring-AI model outputs seen before V2 freeze:
  `false`
- Monitoring-AI calls before V2 freeze:
  `Market/Core/A/B = 0/0/0/0`

R2B-R4 may read only this neutral receipt.

---

# 4. Anti-contamination hard gate

R2B-R4 must not open/read/search/mount/parse/diff/summarize:

- Independent Assessment V1 JSON/MD/ZIP
- Independent Assessment V2 JSON/MD/ZIP
- any independent market verdict
- any independent stock verdict
- any independent BUY/SELL ratio
- any independent Overall/New Buyer/Holder stance

until the new Monitoring-AI result bundle has been completely sealed.

Add filesystem/read audit.

Required through result seal:

`independent_assessment_content_read = false`

Only hash verification of the neutral V2 receipt is permitted.

---

# 5. Do not reopen source or quality policy

R2B-R4 is an execution task.

No changes authorized to:

- source packet
- source authority graph
- canonical business facts
- financial-quality-taint-v2
- quality reason mapping
- UNKNOWN_LIMIT
- stored-price-rule ownership
- security valuation basis
- SKHY issuer bridge
- CPNG anomaly semantics
- TSM/WRD/003690 source semantics
- Overall / New Buyer / Holder policy
- renderer policy

If a pre-model invariant unexpectedly fails:
- stop;
- report exact drift;
- do not repair inside R2B-R4.

---

# 6. Verify R2B-R3 22-subject readiness exactly

Re-run offline before model dispatch.

Require:

## Core

`22/22 PASS`

## A/New Buyer

`22/22 PASS`

Use actual deterministic materialization, not schema-only probes.

## B/Holder

`22/22 PASS`

## Quality applicability

- PRESENT 7
- RECONSTRUCTIBLE 14
- NOT_APPLICABLE 1
- unresolved 0

## UNKNOWN_LIMIT

SNDK generic limitation path PASS.

## Stored price rules

20/20 exact version ownership PASS.

## Source-time contract

all model-visible refs classified.

No eligible-subset dispatch.

---

# 7. Blind fairness gate is now satisfied

R2B-R3 stopped because the independent reviewer had not seen the quality supplement.

R2B-R4 may clear that gate only after exact V2 receipt verification.

Required:

- blind original SHA exact
- quality supplement SHA exact
- V2 neutral receipt SHA exact
- V2 frozen before AI calls
- current AI calls still 0
- independent content unread

Then set:

`BLIND_FAIRNESS_GATE = PASS_V2`

Do not infer any V2 decisions from hashes.

---

# 8. Issue whole-cohort model-input binding

After Sections 4–7 PASS, issue the previously withheld immutable binding.

At minimum include:

- source run-seed hash
- US/KR/full-source hashes
- source-authority graph hash
- quality supplement hash
- quality-owner implementation/version
- 22 decision modes
- 22 quality states/effects
- security valuation basis states
- stored-price-rule bindings
- visible refs
- denied refs
- prompt hashes
- internal schema hashes
- provider-wire schema hashes
- Core/A/B context hashes
- blind fairness receipt hash

Status:

`ISSUED_WHOLE_COHORT_READY`

No model call before this binding is sealed.

---

# 9. Frozen bounded Monitoring-AI execution plan

Use the existing accepted batch topology and model plan.

## Market

Maximum calls:

`2`

One US market, one KR market.

## Core

Maximum calls:

`8`

Use existing frozen subject batches.

## A

Maximum calls:

`8`

## B

Maximum calls:

`8`

Total maximum model calls:

`26`

Preserve current frozen provider/model configuration.

Expected model:

`GPT-5.6 Sol`

Expected reasoning effort:

existing frozen `xhigh` plan.

Per-call timeout:

`1200 seconds`

Retries:

- transport/model retry `0`
- semantic retry `0`
- schema repair `0`
- repair model `0`
- fallback model `0`
- judge `0`

Do not add selective reruns.

---

# 10. Execution ordering

Required order:

1. Market source contexts verified
2. run Market calls
3. run Core calls
4. validate/freeze complete Core result
5. run A calls using accepted Core/frozen deterministic context
6. validate/freeze complete A result
7. run B calls using accepted Core/A/deterministic context
8. validate/freeze complete B result
9. final policy consistency validation
10. render 24 previews
11. seal Monitoring-AI result bundle
12. only then open comparison gate

If the existing code's accepted ordering differs, preserve its exact dependency ordering while maintaining the no-partial-result contract.

No stage may use external independent verdicts.

---

# 11. Fail-fast versus whole-stage completion

Within a model batch:

- one attempt
- validate immediately

A hard semantic/schema/source-ref failure stops dependent later stages.

Do not fill failed subjects with:

- old outputs
- independent assessment
- prior production AI
- synthetic decisions

Preserve completed independent call receipts.

No selective rerun.

---

# 12. UNKNOWN_LIMIT remains non-directional

For SNDK:

- overall = OBSERVE
- new buyer = OBSERVE
- holder = OBSERVE
- ratio = null
- no directional confidence

The model may explain source limitation.

It may not promote the context-only event.

Validator must reject directional leakage.

No expectation about agreement with the independent assessment is passed to the model.

---

# 13. Business-quality effects remain confidence-only

For quality-limited subjects including:

- CRCL
- IBM
- SKHY
- existing 000660 / 005490 / 010120 / 012450 / 086280 cases

the deterministic typed quality state may affect confidence/caution according to existing policy.

It must not, by itself:

- downgrade Overall
- create Holder REDUCE/REVIEW
- create New Buyer AVOID
- create directional negative evidence

Preserve the accepted M12CR-R1 rules.

---

# 14. Security valuation basis remains separate

Unresolved security valuation basis may:

- block unsafe per-share valuation
- block fundamental entry materialization
- support New Buyer WAIT under existing policy

It cannot by itself:

- downgrade Overall
- create Holder REDUCE/REVIEW
- become business-quality evidence

No conflation.

---

# 15. Market messages

Render exactly:

- US market 1
- KR market 1

Use only sealed market source context.

If US market source still lacks directional change/breadth sufficient for a strong direction, the model must remain within source-authorized claims.

Do not infer from absolute index levels alone if not supported by the market contract.

---

# 16. Stock messages

Render:

- US14
- KR8

Total stock messages:

`22`

Each message must bind:

- ticker/security ID
- source packet hash
- model-input binding
- Core result
- A result
- B result
- exact source refs
- validator result
- rendered message hash

No source variation by message.

---

# 17. Required total output

Expected:

- market messages = 2
- stock messages = 22
- total = `24`

No Telegram send.

No recipient intent.

No production DB decision/warning write.

No scheduler mutation.

---

# 18. Monitoring-AI result bundle

Create a new immutable bundle with a distinct generation ID.

Suggested filename:

`thesis-monitor-20260928-r2b-r4-MONITORING_AI_RESULT.zip`

Include at minimum:

- REPORT.md
- summary.json
- model-input binding
- Market inputs/prompts/schemas/raw outputs/validated outputs/call receipts
- Core inputs/prompts/schemas/raw outputs/validated outputs/call receipts
- A inputs/prompts/schemas/raw outputs/validated outputs/call receipts
- B inputs/prompts/schemas/raw outputs/validated outputs/call receipts
- 24 rendered previews
- message inventory/hashes
- source/hash binding
- quality supplement binding
- validator outputs
- model-call ledger
- anti-contamination receipt
- safety counters
- bundle manifest

Do not include independent assessment V1/V2 content.

---

# 19. Result seal before reveal

Before opening comparison gate:

- result bundle complete
- result bundle SHA frozen
- all 24 message hashes frozen
- call ledger frozen
- source/model binding frozen
- independent assessment content read = false

Then emit a small neutral receipt:

`MONITORING_AI_RESULT_SEALED_READY_FOR_COMPARISON`

containing:

- result ZIP filename/hash
- message count
- source packet hash
- V2 neutral receipt hash
- no investment verdict content

Only after this receipt exists may independent V2 assessment content be opened.

---

# 20. Do not perform comparison inside R2B-R4

R2B-R4 ends when the Monitoring-AI output is sealed.

Do not:

- compare to V1
- compare to V2
- score agreement
- alter model policy
- alter thresholds
- rerun disagreements

Return both result bundle and neutral comparison-ready receipt to Chat.

Comparison is a separate review step.

---

# 21. Network/provider policy

Source/provider calls:

`0`

Specifically:

- Kiwoom = 0
- OHLCV = 0
- SEC = 0
- OpenDART = 0
- KRX = 0
- news = 0
- Alpha Vantage = 0
- Massive = 0
- any source refresh = 0

Only model API calls authorized by the frozen execution plan are allowed.

---

# 22. Production side effects

Hard zero:

- Telegram
- recipient intent
- production DB decisions
- production DB warnings
- scheduler mutation
- notification mutation
- broker
- deploy
- main merge
- remote push
- service restart

This is a sealed-source dry run.

---

# 23. Success terminal

`R2B_R4_MONITORING_AI_24_MESSAGE_PASS_READY_FOR_BLIND_COMPARISON`

Require:

- R2B-R3 22/22 readiness reproduced
- V2 blind fairness gate PASS
- model-input binding issued
- actual Monitoring AI calls executed
- all required stage validators PASS
- 24/24 rendered messages
- result bundle sealed
- independent assessment content unread through seal
- provider refresh 0
- production side effects 0
- neutral comparison-ready receipt generated

---

# 24. Failure terminals

## Pre-model drift

`R2B_R4_PREMODEL_CONTRACT_DRIFT`

Use if R2B-R3 readiness or source/hash invariants no longer reproduce.

Model calls = 0.

## Blind fairness receipt failure

`R2B_R4_BLIND_V2_FREEZE_RECEIPT_INVALID`

Model calls = 0.

## Market model failure

`R2B_R4_MARKET_MODEL_FAILURE`

Preserve actual call receipt.

## Core failure

`R2B_R4_CORE_MODEL_FAILURE`

No A/B dispatch.

## A failure

`R2B_R4_A_MODEL_FAILURE`

No B dispatch.

## B failure

`R2B_R4_B_MODEL_FAILURE`

Preserve accepted prior stage outputs.

## Final render/validator failure

Use exact stage-specific terminal.

No retry/repair.

---

# 25. Validation before dispatch

Required offline:

- exact source hashes
- R2B-R3 quality supplement hash
- 22 quality applicability states
- Core 22/22
- A actual materialization 22/22
- B readiness 22/22
- UNKNOWN_LIMIT
- stored price rules
- provider-wire schemas
- anti-contamination read audit
- V2 receipt verification

Then execute.

---

# 26. Validation after execution

Required:

- model call ledger exact
- no retry
- no fallback
- all source refs valid
- all stage schemas valid
- policy consistency valid
- 24 message count exact
- every message hash
- no independent verdict content in prompts/results
- provider refresh 0
- production side effects 0
- secret scan
- bundle manifest

Do not require agreement with the independent assessment.

---

# 27. Required deliverables

Return:

1. Monitoring-AI result ZIP
2. result ZIP `.sha256`
3. neutral comparison-ready receipt JSON
4. closeout REPORT/summary inside result bundle

Do **not** return the independent assessment V2 content as part of the result bundle.

---

# 28. Final principle

The source/quality contract is now ready.

The only reason R2B-R3 did not run Monitoring AI was that the independent reviewer had not yet seen three source-derived confidence diagnostics.

That fairness gap is now closed by an independently sealed V2 assessment.

R2B-R4 must therefore execute the Monitoring AI exactly once on the sealed source and quality view, without learning what the independent reviewer concluded.
