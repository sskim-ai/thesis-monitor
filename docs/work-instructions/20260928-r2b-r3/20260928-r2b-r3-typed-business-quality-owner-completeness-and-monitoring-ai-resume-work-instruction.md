# Thesis Monitor — R2B-R3
## Typed Business-Quality Owner Completeness + Pass-A Materializer Parity + Monitoring-AI Resume

**Purpose:** close the exact A/New Buyer materialization gap discovered by R2B-R2 without fabricating quality refs, weakening validators, or changing source authority.

R2B-R2 already closed:

- whole-decision `UNKNOWN_LIMIT / OBSERVE`;
- the SNDK zero-direction policy;
- all 20 stored-price-rule thesis-version bindings;
- the 51 Core source-time mismatches;
- Core readiness 22/22.

The remaining blocker is:

`A_DETERMINISTIC_QUALITY_MATERIALIZATION_GAP`

for 14 subjects.

R2B-R3 must determine, from the sealed source graph and the accepted typed-quality contract, whether each missing `financial_quality` record is:

1. a **real deterministic owner-output gap** that can be reconstructed from already-captured source-owned financial quality inputs;
2. a **proven not-applicable state** under the existing quality contract; or
3. an **unresolved expected-record absence** that must remain fail-closed.

Do not simply map absence to `NONE`.
Do not permit `CONFIDENCE_ONLY` without owned reason/source lineage.
Do not create fake `canonical:financial_quality:*` refs.

If and only if the entire 22-subject Core/A/B input contract becomes valid, resume the actual Monitoring-AI dry run and generate the 24 messages.

No provider/source refresh is authorized.

---

# 0. Newest SoT

Adopt R2B-R2 as the newest result SoT.

R2B-R2 result ZIP SHA-256:

`eabff41aa2817a51ecfa23b683bc20ef82af3f3a21c212faa0f3fe1b16e98c3c`

Terminal:

`R2B_R2_WHOLE_COHORT_MODEL_INPUT_GAP`

Repository:

- branch:
  `codex/r2b-r2-whole-decision-limit`
- base:
  `98543a8778a0517a0b5c3da69f935c480f8ef302`
- instruction:
  `08773bc740413dcc18e271f71806c230f8a2d137`
- implementation:
  `1ad422c6f6243771740480411f927152ae2c7e7b`
- final:
  `9321a76b41b499879e75668348f84c2c1ad59a10`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

R2B-R2 result integrity independently rechecked:

- outer ZIP matches sidecar
- bundle manifest: `58/58`
- missing: `0`
- hash mismatch: `0`
- size mismatch: `0`
- extra manifest-scope files: `0`

Accepted R2B-R2 state:

- source assembly: `22/22`
- Core: `22/22`
- A/New Buyer: `8/22`
- B/Holder: `8/22`
- actual Market/Core/A/B calls: `0/0/0/0`
- actual AI messages: `0/24`
- UNKNOWN_LIMIT policy: `PASS`
- stored-price-rule version ownership:
  `20/20 PASS`
- canonical source-time contract:
  `565/565 PASS`
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
  `330 PASS`
- full:
  `6125 PASS / 63 unchanged skips`
- Ruff/diff/Investment Knowledge/Chart Knowledge:
  PASS

Do not undo these closures.

---

# 1. Immutable sealed source / blind identities

Use the exact existing sealed source graph.

- run seed:
  `df3b7f1102fcacd27b70e594fb58b139644a7ba1daa18620279bf1a455916bdc`
- US packet:
  `b2b603850e517c70d6a9a201b297952677d6542271f72db6f0eecbdebe09fdb1`
- KR packet:
  `d3081027ec1203a5af09adc590b13ca81dce3c049a65b988606a0d3311f74845`
- combined source:
  `c4fbc25ec81abe61c3981bfaa44204cc7e15cc252f25cbe6aedc6b2a1de9b44f`
- authority graph:
  `0b69d1913e139078ed42b0fb1c0b01928b065fd2d76863e3835622b3ee0992b6`

Blind source ZIP SHA-256:

`d705d36dabfa99f8d096a2bce4ddf996229680650cb09a45abffb5d7e9213ec3`

Neutral independent-freeze receipt SHA-256:

`f0f71fd39091369f280242d7a41af32a9cdbf3e0fa505fe2427f89b768eee26a`

No source refresh.
No blind-bundle regeneration unless source-derived content actually changes—which is not authorized here.

---

# 2. Anti-contamination remains mandatory

R2B-R3 may read only the neutral independent-freeze receipt.

It must not read/open/search/mount/parse/diff/summarize:

- independent assessment JSON
- independent assessment Markdown
- independent assessment ZIP
- any independent per-stock verdict
- any independent ratio/stance

until the Monitoring-AI result bundle is completely sealed.

Required execution receipt:

`independent_assessment_content_read = false`

through Monitoring-AI result sealing.

---

# 3. Exact current blocker

R2B-R2's actual A materializer—not schema-only validation—found the blocker.

Affected subjects:

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
- TSM
- WRD
- WULF
- 003690

Count:

`14`

For all 14:

- `raw_quality_facts = []`
- `original_quality_authority = []`
- `adapter_removed_quality_refs = []`

Current deterministic projection:

- contract:
  `m12cr-r1-typed-quality-security-basis-v1`
- source presence:
  `EXPECTED_RECORD_ABSENT`
- state:
  `CONFIDENCE_ONLY`
- effect:
  `CONFIDENCE_ONLY`
- reason code:
  `expected_business_quality_record_absent`
- record ref:
  `null`
- source refs:
  `[]`
- status:
  `MAPPED_FAIL_CLOSED`

Legacy A semantic validator then correctly rejects:

`data_quality_effect_missing_reason_or_ref`

Do not disable this validator.

---

# 4. Historical typed-quality contract remains authoritative

Preserve the accepted M12CR-R1 design principles.

The quality architecture has three separate layers:

1. `BUSINESS_EVIDENCE_QUALITY`
2. `SECURITY_VALUATION_BASIS`
3. `DIRECTIONAL_DISCLOSURE_QUALITY`

Do not collapse them.

For `BUSINESS_EVIDENCE_QUALITY`:

- deterministic runtime owner
- states include:
  - `NONE`
  - `CONFIDENCE_ONLY`
- quality is not directional by itself
- mere ref existence is not the owner
- normal security identity is not business-quality evidence
- security/share-basis limitations are not business-quality limitations

Critical historical rule:

> If no applicable business-quality record exists, distinguish legitimately not-applicable/clean from expected quality evidence absent. Do not automatically equate absence with NONE or CONFIDENCE_ONLY without proving the source contract.

This rule is binding in R2B-R3.

Do not force the old snapshot's exact NONE/CONFIDENCE_ONLY distribution onto the new source cohort.

---

# 5. Build a 22-subject quality-owner applicability matrix first

Before code changes, produce:

`business-quality-owner-applicability-matrix.json`

For every subject include:

- ticker
- decision mode
- accepted business evidence class
- accepted financial provider/source family
- financial/business source periods
- canonical comparative fields actually consumed
- field-level quality/source-use states already present
- whether a canonical financial-quality owner is contractually expected
- existing canonical financial-quality record, if any
- source inputs needed to deterministically generate quality state
- whether those inputs exist in the sealed source corpus
- final classification:
  - `PRESENT`
  - `EXPECTED_OWNER_OUTPUT_RECONSTRUCTIBLE`
  - `PROVEN_NOT_APPLICABLE`
  - `EXPECTED_OWNER_OUTPUT_MISSING_UNRESOLVED`

No ticker-specific outcome coding.

---

# 6. Do not assume every financial comparison requires the same quality record

Audit the actual accepted financial/business source path for each subject.

Examples of possible evidence classes:

- formal financial statement comparison
- preliminary earnings comparison
- bounded SEC extracted financial comparison
- OpenDART formal comparison
- OpenDART preliminary comparison
- issuer-level bridged comparison
- source-owned event only
- UNKNOWN_LIMIT with no directional financial evidence

The canonical quality owner's applicability must follow the source contract.

Do not infer applicability from:
- ticker market
- current model mode
- desired A readiness
- whether the subject is currently blocked.

---

# 7. Reconstruct a missing quality record only from existing deterministic source inputs

If classification is:

`EXPECTED_OWNER_OUTPUT_RECONSTRUCTIBLE`

run the existing deterministic quality logic over the already-sealed inputs.

Do not invent a quality state directly in R2B-R3.

Required inputs must be source-owned and sufficient to reproduce the existing quality decision semantics, including as applicable:

- source/report type
- current/prior financial occurrences
- revenue / operating income / net income relations
- period/comparability state
- statement basis
- field-quality/taint state
- source-use result
- existing deterministic anomaly rules
- decision/version identity

If sufficient:

emit a real deterministic derived canonical quality fact with:

- canonical ticker/security/issuer ownership
- source period
- source type
- deterministic quality state
- reason codes
- decision version
- source input IDs/hashes
- derivation owner/version
- derived record hash
- canonical quality ref

Suggested canonical shape remains repository-native:

`canonical:financial_quality:<source-period>`

but only if produced by the legitimate canonical owner path.

Do not manufacture the ref in the A adapter.

---

# 8. Canonical quality generation must be upstream of A materialization

If a quality record is reconstructed:

- produce it in the canonical financial/source-quality owner layer;
- register it in the authority graph/catalog;
- expose its allowed/prohibited uses exactly as existing typed-quality evidence;
- only then let A's deterministic quality projection consume it.

Do not generate a synthetic A-only ref.

Do not let the A materializer become the quality owner.

---

# 9. Re-run original financial-quality validation unchanged where possible

Use the existing accepted deterministic validator/version when the required input contract is available.

Historical accepted decision version includes:

`financial-quality-taint-v2`

Do not change its thresholds/reason semantics merely to make the 14 pass.

For new SEC/OpenDART financial evidence, audit whether the generic bounded financial owner already computed field-level quality/source-use results sufficient for the canonical quality validator.

If source inputs are insufficient:
- classification remains unresolved;
- do not infer `verified_usable`.

---

# 10. `PROVEN_NOT_APPLICABLE` is not a fake clean record

Use `PROVEN_NOT_APPLICABLE` only if the source contract explicitly proves that no business-quality record applies to the evidence class.

Example shape:

- evidence class has no typed financial-quality domain by design;
- no quality-limited financial claim is being used;
- existing contract defines absence as legitimate.

For this state:

- do not create `canonical:financial_quality:*`
- do not create a fake reason/ref
- do not create `CONFIDENCE_ONLY`
- business-quality effect may be `NONE` / no-effect **only if the accepted contract explicitly owns that result**
- preserve an applicability receipt outside the financial-quality fact namespace

A's materializer must not inject a quality effect requiring a source ref when no quality effect exists.

Do not use this state as a convenience for the 14 blocked subjects.

---

# 11. `EXPECTED_OWNER_OUTPUT_MISSING_UNRESOLVED` remains fail-closed

If:

- a quality record is contractually expected;
- but the sealed source inputs cannot reproduce it;
- and no legitimate existing quality record exists;

then:

- do not map to NONE
- do not map to CONFIDENCE_ONLY
- do not generate fake ref
- do not call the model

Use a source/preflight blocker such as:

`EXPECTED_BUSINESS_QUALITY_OWNER_OUTPUT_MISSING`

This is an upstream source-owner completeness problem.

It must not be hidden inside A semantics.

---

# 12. Correct the current fail-closed projection semantics

The current R2B-R2 projection maps:

`EXPECTED_RECORD_ABSENT`
→ `CONFIDENCE_ONLY`
→ ref null
→ A validator failure.

Replace this with explicit source-presence semantics.

Required projection cases:

## `PRESENT`

### verified/clean state
- effect:
  `NONE`
- directional use:
  false
- preserve quality record ownership
- no confidence downgrade

### caution/denied/owned limitation state
- effect:
  `CONFIDENCE_ONLY`
- exact record ref required
- reason/reason_codes preserved
- directional use:
  false

## `PROVEN_NOT_APPLICABLE`

- effect:
  `NONE` / no effect
- no fabricated quality record
- exact applicability proof required
- no confidence downgrade

## `EXPECTED_OWNER_OUTPUT_MISSING_UNRESOLVED`

- no model-visible quality effect object
- subject preflight BLOCKED upstream
- explicit exact owner gap

Do not use ref absence as the mapping rule by itself.

---

# 13. Pass-A materializer contract

Audit the real existing Pass-A materialization path.

Required behavior:

## NONE / no quality effect

Do not inject a `data_quality_effect` requiring reason/ref.

If the schema has an optional/no-effect representation, use it.

Do not inject:

- empty reason
- null ref into a ref-required effect
- synthetic `NOT_APPLICABLE` ref.

## CONFIDENCE_ONLY

Require:

- owned typed quality state
- exact source/canonical quality ref
- reason/reason codes
- confidence-only use
- no directional authority

Legacy validator should continue to reject unowned CONFIDENCE_ONLY effects.

---

# 14. Do not weaken legacy semantic validation

Preserve:

`data_quality_effect_missing_reason_or_ref`

as an error when a confidence-limiting effect lacks owned support.

Add new validation for:

- unexpected quality record absence reaching the materializer
- fake quality refs
- wrong source period
- wrong subject
- wrong provider/owner
- quality effect used directionally
- security valuation basis confused with business quality

The solution is upstream completeness / explicit no-effect—not validator bypass.

---

# 15. Audit all 22, not only the 14

R2B-R3 must produce a full current quality matrix.

For each ticker report:

- source presence
- raw quality fact
- canonical quality ref
- financial quality state
- reason codes
- business-evidence quality effect
- source refs
- directional use
- security valuation basis state
- final Pass-A quality materialization status

Preserve currently working examples.

At minimum:

## Existing PRESENT controls

Subjects with existing quality records must retain their semantics.

Examples from R2B-R2 include:

- `000660`:
  denied -> `CONFIDENCE_ONLY`
  with exact quality ref and reason codes

- `005490`, `010120`, `012450`, `086280`:
  existing caution/quality semantics must not be changed arbitrarily

- `005930`, `047810`:
  verified usable -> `NONE`

Do not force these through a new absence path.

## SNDK

SNDK UNKNOWN_LIMIT remains independently valid.

Do not promote its event or invent financial quality simply because raw quality is absent.

Its A/B readiness must remain valid under the already-accepted UNKNOWN_LIMIT policy.

---

# 16. Special audit — 003690

003690's insurance-revenue semantic repair previously required re-running financial quality after canonical revenue mapping.

R2B-R3 must trace whether that quality decision was:

- actually produced and lost from the current canonical fact graph; or
- never materialized as a canonical quality record.

Use the already-sealed source.

If reconstructible:
- run the same generic financial-quality owner.

No ticker-specific `003690` fix.

No relaxed insurance thresholds.

---

# 17. Special audit — new bounded SEC subjects

For the US subjects whose comparative business evidence was created through the bounded SEC owner, determine whether that owner produces enough field-quality/source-use state to run the canonical business-quality validator.

Do not assume SEC formal filing implies `verified_usable`.

Check exact:

- report/form authority
- period compatibility
- field occurrence lineage
- statement basis
- quality/taint diagnostics
- current/prior pair status

If the quality owner needs an input the bounded SEC graph does not contain:
- surface the exact missing owner/input.

Do not infer clean.

---

# 18. Special audit — SKHY issuer-level bridge

SKHY's issuer-level business evidence is bridged from the same legal issuer's OpenDART source.

Quality ownership must follow the original issuer-level source fact.

Do not:

- create a new SEC quality record
- convert 000660 denied sibling fields to usable
- transfer security-level valuation/price quality
- widen per-share/valuation bridge.

If the bridged revenue comparison carries sufficient issuer-level quality ownership:
- preserve its original source identity through the bridge.

If not:
- block quality owner completeness exactly.

---

# 19. Source authority registration

Any reconstructed canonical quality fact must be added to the source-authority graph with:

- authority origin:
  deterministic source projection/validation
- source family:
  typed quality
- source scope:
  context/confidence only
- allowed uses:
  exactly the existing typed-quality uses
- prohibited uses:
  Overall Direction / Holder Stance / Entry / Valuation and all other existing prohibitions
- source period
- source metadata hash
- subject/issuer ownership
- derivation inputs

Do not widen authority.

---

# 20. Source packet / blind bundle mutation rule

The raw/economic source packet must remain unchanged.

If R2B-R3 legitimately derives missing canonical quality metadata from source inputs that were already sealed:

- produce a **derived evidence-view supplement** with its own hash;
- do not rewrite the blind source ZIP;
- do not change raw source artifact hashes;
- do not represent derived quality metadata as newly acquired provider data.

The blind source ZIP remains:

`d705d36dabfa99f8d096a2bce4ddf996229680650cb09a45abffb5d7e9213ec3`

If the independent evaluator would materially need newly derived quality metadata to have made the blind judgment fairly:
- stop before model dispatch;
- report:
  `BLIND_REVIEW_MATERIAL_SOURCE_VIEW_CHANGED`
- do not contaminate comparison.

A purely deterministic quality annotation already implied by the source may be permitted only if the blind bundle contained the underlying source facts and no new economic information is introduced. Document this decision.

---

# 21. Re-run actual A materialization for all 22

Do not rely on schema-only PASS.

For all 22:

- build actual future Pass-A schema/context
- run actual deterministic A materialization
- run legacy semantic validation
- require `22/22 PASS`

Produce:

- schema status
- materialization status
- quality projection
- quality source refs
- exact errors

No synthetic A result is counted as Monitoring AI output.

---

# 22. Re-run B/Holder readiness after A

B remains dependent on successful A materialization.

Only after A `22/22 PASS`:

- run actual deterministic B input/context transformation readiness
- validate Holder input contract
- require `22/22 PASS`

Preserve:

- UNKNOWN_LIMIT SNDK Holder OBSERVE
- security valuation basis not treated as Holder direction
- business-quality CONFIDENCE_ONLY not used as Holder downgrade by itself.

---

# 23. Whole-cohort model-input readiness gate

Before any model call require:

- Core:
  `22/22 PASS`
- A/New Buyer:
  `22/22 PASS`
- B/Holder:
  `22/22 PASS`
- UNKNOWN_LIMIT:
  PASS
- stored price-rule ownership:
  PASS / explicitly unavailable where accepted
- all model-visible source-time refs:
  classified
- quality-owner applicability:
  all 22 resolved
- no fake refs
- no authority widening
- blind/source hashes verified
- independent assessment unread

No eligible-subset dispatch.

---

# 24. New model-input binding

After full readiness:

issue an immutable model-input binding containing:

- source run-seed/packet hashes
- authority graph hash
- derived quality supplement hash, if any
- policy/schema hashes
- 22 decision modes
- 22 quality states
- visible/denied refs
- A/B materialization hashes
- stored-price-rule bindings
- prompt/schema hashes

Status must be:

`ISSUED_WHOLE_COHORT_READY`

before model dispatch.

---

# 25. Monitoring-AI dispatch

Only after Section 23/24 pass.

Use the existing bounded R2B model plan:

- Market: max `2`
- Core: max `8`
- A: max `8`
- B: max `8`
- model configuration:
  existing frozen GPT-5.6 Sol plan
- reasoning effort:
  existing frozen xhigh
- per-call max:
  `1200s`
- transport retries:
  `0`
- semantic retries:
  `0`
- fallback:
  `0`
- judge:
  `0`
- provider refresh:
  `0`

No partial dispatch.

No old model candidates.

---

# 26. Required 24-message output

On successful execution:

- US market:
  `1`
- US14:
  `14`
- KR market:
  `1`
- KR8:
  `8`
- total:
  `24`

All messages bind the same sealed source packet and the exact new model-input binding.

UNKNOWN_LIMIT subjects render the limitation state rather than fabricated direction.

---

# 27. Monitoring-AI result bundle isolation

Create a new result generation.

Do not overwrite:

- original blocker report
- R2B-R1 report
- R2B-R2 report
- blind source ZIP
- independent assessment bundle

Monitoring-AI result bundle contains only:

- actual Market/Core/A/B outputs
- validators
- 24 rendered previews
- source/model-input binding hashes
- message hashes
- model-call receipts

Independent assessment content remains absent.

---

# 28. Reveal gate / later comparison

Through Monitoring-AI result sealing require:

`independent_assessment_content_read = false`

After result bundle is sealed:

- comparison gate may open
- independent assessment may then be revealed
- do not revise the already-frozen independent assessment

Comparison itself is a later review step.

---

# 29. No provider refresh / production side effects

Hard zero:

- Kiwoom
- stock OHLCV
- SEC
- OpenDART
- KRX
- news
- Alpha Vantage
- Massive
- other source APIs

Production side effects hard zero:

- Telegram
- recipient intent
- production DB decisions/warnings
- scheduler mutation
- broker
- deploy
- main merge
- push
- restart

---

# 30. Completion terminals

## Full success

`R2B_R3_MONITORING_AI_24_MESSAGE_PASS`

Require:

- quality-owner applicability resolved 22/22
- no absence→clean shortcut
- no ref-less CONFIDENCE_ONLY
- actual A materialization 22/22
- B readiness 22/22
- whole-cohort Core/A/B readiness 22/22
- model-input binding issued
- actual Monitoring-AI dispatch
- 24/24 rendered messages
- independent assessment unread through result seal
- provider refresh 0
- production side effects 0

## True upstream quality-owner gap remains

`R2B_R3_TYPED_QUALITY_OWNER_GAP`

Use when at least one expected quality record cannot be generated from the sealed source inputs.

Return exact:

- ticker
- evidence class
- source period
- expected quality owner
- missing input
- why NOT_APPLICABLE is not valid

Model calls remain 0.

## Quality applicability itself unresolved

`R2B_R3_QUALITY_APPLICABILITY_CONTRACT_GAP`

Use when the source contract cannot determine whether a quality record should exist.

Do not guess.

## A materializer/validator parity gap after valid quality ownership

`R2B_R3_A_MATERIALIZER_PARITY_GAP`

Do not weaken the legacy validator.

## Blind-review material source view changed

`R2B_R3_BLIND_REVIEW_MATERIAL_SOURCE_VIEW_CHANGED`

Use only if the proposed derived quality metadata introduces economic/source information the blind evaluator did not receive.

No model dispatch.

## Model-stage failure

If source/preflight passes and actual model dispatch begins, use exact model-stage terminal.

Do not call it source failure.

---

# 31. Required validation

## Applicability
- PRESENT quality record
- PROVEN_NOT_APPLICABLE
- EXPECTED owner output reconstructible
- EXPECTED owner output missing unresolved
- no ref-cardinality ownership

## Quality derivation
- verified usable -> NONE
- caution/denied -> CONFIDENCE_ONLY with ref
- reason codes preserved
- wrong subject/period/source -> fail
- security basis cannot become business quality
- directional authority remains false

## Materializer
- NONE/no effect path
- CONFIDENCE_ONLY owned effect
- ref-less confidence effect fails
- unresolved missing owner blocked upstream
- all 22 actual A materialization
- all 22 B readiness

## Special
- 003690
- bounded SEC subjects
- SKHY issuer bridge
- 000660 denied fields
- SNDK UNKNOWN_LIMIT
- 005930/047810 verified usable controls

## Blind safety
- blind ZIP exact
- neutral independent-freeze receipt exact
- independent assessment content unread
- derived quality supplement economic-content audit

## Repository
- R2B-R1/R2 regressions
- prior source/authority regressions
- full pytest
- Ruff
- `git diff --check`
- Investment Knowledge
- Chart Knowledge
- secret scan
- unchanged skip/xfail identity

---

# 32. Required result bundle

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- R2B-R2 identity/SHA
- source identities
- repository identities
- changed-file inventory

## Quality ownership
- `business-quality-owner-applicability-matrix.json`
- source-class / applicability matrix
- raw quality input matrix
- reconstructed canonical quality records, if any
- derivation receipts
- not-applicable receipts
- unresolved owner-gap receipts
- authority registrations
- full 22 quality matrix

## A/B readiness
- actual A materialization matrix
- legacy semantic-validation receipts
- B/Holder readiness matrix
- Core/A/B whole-cohort readiness
- exact blockers

## Blind/source invariance
- blind ZIP verification
- source packet invariance
- derived quality supplement hash if any
- independent-assessment read audit

## Model binding/execution
If ready:
- model-input binding + SHA
- Market/Core/A/B call receipts
- 24 preview inventory
- 24 message hashes
- Monitoring-AI result bundle identity/SHA
- result-sealed comparison-ready receipt

## Safety
- provider refresh 0
- production side effects 0
- validation logs
- secret scan
- bundle manifest

---

# 33. Final principle

A missing quality record is not automatically clean and not automatically confidence-limiting.

First prove whether the quality owner applies.

If it applies, produce the real deterministic quality output from sealed source inputs or remain blocked.

If it provably does not apply, represent no quality effect without inventing a ref.

Only after that distinction is explicit may Pass A materialize and Monitoring AI run.
