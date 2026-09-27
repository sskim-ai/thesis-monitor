# Thesis Monitor — R2B-R1
## Whole-Cohort Core Preflight Contract Closure + Blind-Safe Monitoring-AI Resume
### Fix undated metadata ownership and zero-directional-entitlement handling offline; then resume the same sealed-source 24-message dry run

**Purpose:** repair the two exact pre-model blockers found by the first R2B execution without recollecting source data, widening authority, or exposing the already-frozen independent assessment to Monitoring AI.

The source packet is already sealed. The independent assessment is also already frozen. R2B-R1 must use only a **neutral freeze receipt**, never the independent verdict content, and may dispatch Monitoring AI only after the entire 22-subject Core source-use preflight passes.

---

# 0. Newest SoT

## Source SoT

REV10 source ZIP SHA-256:

`5cd89052657b6d4d29d174415fa1ce3dd686ccf20a14ea342256feda28d9836a`

Sealed full-source identities:

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

No source refresh is authorized.

## First R2B execution

Blind source ZIP SHA-256:

`d705d36dabfa99f8d096a2bce4ddf996229680650cb09a45abffb5d7e9213ec3`

Monitoring-AI blocker-report ZIP SHA-256:

`72d1d9234af6158c649d34e536aa66e039ab7bd348fe9422b536d1315c9e5cf1`

Generation:

`20260927-r2b-blind-20260927T131042Z`

Controller commit:

`2829fd36ed9245b7c7199e134b531f7c9a0d226b`

Status:

`BLOCKED_BEFORE_MODEL`

Actual calls:

- Market = `0`
- Core = `0`
- A = `0`
- B = `0`
- rendered previews = `0/24`
- provider refresh = `0`

Do not classify the blocker ZIP as Monitoring-AI judgment output.

---

# 1. External blind assessment is already frozen

Neutral receipt SHA-256:

`f0f71fd39091369f280242d7a41af32a9cdbf3e0fa505fe2427f89b768eee26a`

The receipt proves only:

- blind source SHA:
  `d705d36dabfa99f8d096a2bce4ddf996229680650cb09a45abffb5d7e9213ec3`
- independent assessment JSON SHA:
  `95776285ba2653ec102517315f16259c7d9f0f314ab5af01b715308b87dda50b`
- independent assessment bundle SHA:
  `cf9c95657f4b3ade19a71f7e181e26dd6a5a8f75cfd5173027ac07448e87bd08`
- independent assessment was frozen before Monitoring-AI result inspection.

**Critical anti-contamination rule:**

R2B-R1 may read the neutral freeze receipt.

R2B-R1 must **not** read, mount, parse, summarize, copy, diff, inspect, or inject:

- the independent assessment JSON;
- the independent assessment Markdown;
- the independent assessment ZIP contents;
- any per-market or per-stock independent decision.

No prompt or validator may receive those decisions.

This remains true until the new Monitoring-AI result bundle is completely sealed.

---

# 2. Exact blocker A — frozen fact projection date mismatch

The first Core source-use preflight failed:

`frozen_fact_projection_mismatch`

Whole-cohort read-only diagnostic:

- affected subjects: `22/22`
- affected statements: `51`
- statement bytes:
  `IDENTICAL`
- financial/numeric value discrepancy:
  `NONE`

Affected canonical refs:

- `canonical:security_identity:current` — `22`
- `canonical:security_basis:current` — `22`
- `canonical:valuation:book_quality` — `7`

Observed contract mismatch:

- canonical `as_of_date`:
  empty string
- projected evidence `as_of`:
  `2026-09-27`

Producer location from blocker report:

`app/services/cross_market_decision_engine_service.py:693`

Consumer:

`scripts/m12ds_r2_judgment_policy.py:51`

Do not solve this by writing `2026-09-27` into the canonical source fact.

---

# 3. Separate three time concepts generically

Audit the typed fact/evidence schema and represent time ownership explicitly.

At minimum distinguish:

## `SOURCE_AS_OF`

A time/date owned by the original source fact.

For a fact with a real economic/source date:
- preserve it exactly;
- consumer equality remains strict.

## `UNDATED_DETERMINISTIC_METADATA`

Identity/basis/quality metadata whose canonical fact has **no intrinsic source as-of date**.

Examples may include the currently affected identity/basis/book-quality refs only if code/schema audit proves they truly belong to this class.

Canonical source date remains empty/null according to existing canonical representation.

Do not synthesize an assessment date.

## `PROJECTION_AT`

When the evidence object was projected/built.

This may be `2026-09-27` for the frozen source proof, but it is **not SOURCE_AS_OF**.

Projection time must never masquerade as source ownership time.

Use repository naming conventions if equivalent typed concepts already exist.

---

# 4. Producer repair

Audit the evidence-builder path at/around:

`cross_market_decision_engine_service.py:693`

Required behavior:

### Canonical dated fact
- projected source `as_of` == canonical source `as_of`
- preserve strict equality

### Canonical undated metadata fact
- projected source `as_of` remains the same undated representation as canonical
- put projection/review time only in a separate projection metadata field if such metadata is required

Forbidden:

- `evidence.as_of = assessment_date` merely because canonical date is empty
- defaulting empty dates to current/proof date
- ticker-specific exceptions
- hardcoded list of 22 symbols

If existing schema cannot carry projection time separately:
- do not overload `as_of`;
- add the smallest generic typed metadata field necessary.

---

# 5. Consumer repair

Audit:

`scripts/m12ds_r2_judgment_policy.py:51`

Do not simply disable date checking.

Required generic rule:

## Intrinsically dated facts
Exact canonical/projected source date equality remains mandatory.

## Undated deterministic metadata
Require all of:

- canonical fact explicitly qualifies for undated-metadata contract;
- projected evidence preserves the canonical undated state;
- source/ref/hash/statement bytes match;
- projection timestamp, if present, is stored separately;
- no economic/source date is inferred.

If canonical is empty but the fact is not contractually undated:
- fail closed.

If projected evidence injects a date where canonical is undated:
- fail.

If canonical has a date and evidence drops it:
- fail.

---

# 6. Date-contract tests

At minimum prove:

1. undated security identity + separate projection time -> PASS
2. undated security basis + separate projection time -> PASS
3. undated book-quality metadata + separate projection time -> PASS where the canonical owner classifies it as undated
4. canonical dated fact exact match -> PASS
5. dated canonical -> empty projection -> FAIL
6. dated canonical -> different date -> FAIL
7. undated canonical -> injected assessment date in source-as-of -> FAIL
8. empty canonical with no undated-metadata classification -> FAIL
9. statement-byte/hash mismatch -> FAIL
10. wrong ticker/security ref -> FAIL

Re-run the whole-cohort preflight.

Expected blocker A closure requires:
- all affected 51 projections pass
- no other date contract is weakened.

---

# 7. Exact blocker B — SNDK zero directional source entitlement

Source assembly for SNDK is complete, but source-use audit finds:

- `OVERALL_DIRECTION` authorized refs:
  `0`
- persisted SNDK headline allowed uses:
  `CONTEXT`
- persisted event:
  `requires_review = true`
- reported financial source:
  unavailable/denied
- authority widening:
  forbidden

This is **not** a model failure.

Do not promote the SNDK headline to directional authority.

Do not fetch new news.

Do not invent a financial direction.

---

# 8. Reuse existing UNKNOWN_LIMIT / OBSERVE semantics if present

Audit the existing judgment-policy/schema/prompt contract for the already-established neutral limitation state, including any existing semantics equivalent to:

- `UNKNOWN_LIMIT`
- `OBSERVE`
- no directional evidence / explicit source limit

If such an accepted path exists, use it generically.

Required meaning:

> The complete source packet is valid, but no source-authorized fact can support positive or negative Overall Direction.

This is different from:
- missing/corrupt source packet;
- validator error;
- unavailable current price;
- authorization bug.

Do not add a new investment direction if an existing typed neutral/limited state already exists.

---

# 9. Source preflight contract for zero directional entitlement

Replace the unconditional concept:

`every subject must have >=1 OVERALL_DIRECTION ref`

with a typed two-path gate **only if this matches the existing UNKNOWN_LIMIT architecture**:

## Path A — directional evidence available

- at least one authorized directional ref;
- normal Core directional path.

## Path B — explicit zero-direction entitlement

Require all:

- stock packet otherwise complete;
- source authority graph PASS;
- current price/technical required inputs PASS;
- zero directional refs is a verified source-use result, not an owner failure;
- every denied directional source is explicit;
- context-only refs remain context-only;
- typed state = existing `UNKNOWN_LIMIT`/equivalent.

Then Core may proceed only under the existing neutral-limit policy.

If the repository has **no accepted neutral-limit policy** for this case:
- do not invent one;
- terminal:
  `ZERO_DIRECTIONAL_ENTITLEMENT_POLICY_DECISION_REQUIRED`.

---

# 10. SNDK model/source constraints

Even after blocker B is closed, the following remains forbidden:

- persisted headline -> `OVERALL_DIRECTION`
- headline -> valuation
- headline -> confirmed contract amount
- headline -> official financial result
- context event -> confidence upgrade unsupported by source
- financial direction invented from current price/technicals

The event may remain visible only under its existing allowed-use contract.

Monitoring AI must be able to state uncertainty/insufficient business direction without converting the event into a positive or negative fundamental claim.

---

# 11. Do not hardcode an expected SNDK verdict

R2B-R1 must **not** hardcode:

- BUY
- SELL
- HOLD
- WAIT
- any ratio

as the expected Monitoring-AI answer.

The repair is about source-use entitlement, not forcing agreement with the external independent assessment.

Only enforce the existing neutral-limit/source-authority semantics.

---

# 12. Whole-cohort preflight before any model call

After A and B repairs:

run the exact whole-cohort source-use preflight across all 22.

No eligible-subset dispatch.

Require:

- `22/22` source-use preflight PASS
- source packet hashes unchanged
- authority graph unchanged except projection/date semantic metadata if legitimately required
- no source authority widened
- SNDK directional-ref count remains `0`
- SNDK explicit neutral-limit state accepted by contract
- no old candidate/model result consumed

If any subject fails:
- Market/Core/A/B actual calls remain `0`.

---

# 13. Blind bundle invariance

Reuse/verify the already sealed blind source review:

`thesis-monitor-20260927-r2b-BLIND_SOURCE_REVIEW.zip`

SHA-256:

`d705d36dabfa99f8d096a2bce4ddf996229680650cb09a45abffb5d7e9213ec3`

Do not regenerate it merely because the preflight implementation changed, unless the **source-derived blind content** itself legitimately changes.

The metadata date fix must not modify economic/source facts.

If blind content changes unexpectedly:
- stop and explain;
- do not dispatch models.

---

# 14. Neutral external-freeze receipt

Consume only:

`thesis-monitor-20260927-INDEPENDENT_FREEZE_RECEIPT.json`

Expected SHA-256:

`f0f71fd39091369f280242d7a41af32a9cdbf3e0fa505fe2427f89b768eee26a`

The receipt contains no investment decisions.

It may change:

`external_review = AWAITING_INDEPENDENT_FREEZE`

to an execution-gate state equivalent to:

`INDEPENDENT_FREEZE_RECEIVED`

only after exact hash verification.

No independent judgment content may be loaded.

---

# 15. Monitoring-AI execution after preflight PASS

Only after:

- blind source SHA verified;
- neutral independent-freeze receipt verified;
- whole-cohort source preflight `22/22 PASS`;
- no source authority widening;

run the actual Monitoring AI.

Use the existing frozen bounded dispatch plan unless code audit proves the plan itself is invalid:

- Market calls: max `2`
- Core calls: max `8`
- A calls: max `8`
- B calls: max `8`
- reasoning configuration: existing frozen Sol/xhigh plan
- per-call max time: existing `1200s`
- transport retries: `0`
- semantic retries: `0`
- fallback: `0`
- judge: `0`
- provider refresh: `0`

No partial market/stock dispatch.

No old candidate fill.

---

# 16. Expected rendered set

On successful model execution:

- US market = `1`
- US stocks = `14`
- KR market = `1`
- KR stocks = `8`
- total = `24`

All outputs must bind the same sealed source packet/run-seed/authority graph.

No data recollection.

---

# 17. Monitoring-AI bundle remains separate

Create a new result bundle only after actual model dispatch.

It must contain:

- actual Market/Core/A/B outputs
- validators
- rendered 24 previews
- source-use receipts
- source/run-seed hashes
- message hashes
- call counters

It must not contain the external independent assessment content.

Do not overwrite the blocker-report ZIP.

Use a new generation/result identity.

---

# 18. Reveal/comparison sequence

After Monitoring-AI result bundle is sealed:

1. external independent assessment remains immutable;
2. Monitoring-AI result may now be revealed;
3. compare against the frozen independent assessment;
4. do not revise the independent assessment before comparison.

The comparison is a later review artifact, not part of model prompting.

---

# 19. No provider/source refresh

R2B-R1 network/provider data calls:

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
- any source API = 0

The only possible network/model traffic after preflight PASS is the already-authorized model dispatch.

---

# 20. Production side effects

Hard zero:

- Telegram send
- recipient intent
- production DB decision/warning writes
- scheduler mutation
- notification mutation
- broker action
- deploy
- service restart
- main merge
- push

This remains a dry run.

---

# 21. Completion terminals

## Full success

`R2B_R1_MONITORING_AI_24_MESSAGE_PASS`

Require:

- date contract repaired generically
- whole cohort preflight `22/22`
- SNDK authority not widened
- neutral-limit semantics valid
- independent freeze receipt verified without reading verdict content
- actual Monitoring AI calls executed
- rendered previews `24/24`
- provider refresh `0`
- production side effects `0`
- separate Monitoring-AI result bundle sealed

## Date contract remains open

`R2B_R1_METADATA_DATE_CONTRACT_GAP_REMAINS`

Model calls remain `0`.

## Zero-direction policy unavailable

`R2B_R1_ZERO_DIRECTIONAL_ENTITLEMENT_POLICY_DECISION_REQUIRED`

Model calls remain `0`.

## Other source-use failure

`R2B_R1_WHOLE_COHORT_SOURCE_PREFLIGHT_GAP`

Return every subject/ref blocker.

No partial dispatch.

## Model-stage failure after valid preflight

Use an exact model-stage terminal and preserve the preflight PASS proof.

Do not mislabel as source failure.

---

# 22. Validation

Required:

## Metadata date
- producer tests
- consumer tests
- undated-metadata metamorphic tests
- strict dated-fact regressions
- all 51 affected projections

## SNDK
- zero-direction entitlement typed-state test
- context authority unchanged
- event `requires_review` preserved
- no directional ref created
- no financial direction fabricated

## Whole cohort
- 22/22 preflight
- source hashes unchanged
- authority graph integrity
- blind ZIP exact hash
- neutral freeze receipt exact hash

## Anti-contamination
- prove independent assessment bundle/content was not opened by R2B-R1 execution
- prove no independent verdict strings enter prompts, validators, candidates or model artifacts

## Repository
- previous source/authority regressions
- full pytest
- Ruff
- `git diff --check`
- Investment Knowledge
- Chart Knowledge
- secret scan
- unchanged skip/xfail identity

---

# 23. Required result bundle

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- first R2B blocker-report identity/SHA
- source REV10 identities
- repository identities
- changed-file inventory

## Date closure
- canonical/projected time-contract matrix
- affected 51-ref before/after
- producer/consumer trace
- positive/negative tests

## SNDK
- directional entitlement audit
- context-only authority invariance
- neutral-limit contract proof or exact policy blocker
- no authority widening receipt

## Blind safety
- blind ZIP verification
- neutral independent-freeze receipt verification
- anti-contamination receipt
- explicit:
  `independent_assessment_content_read = false`
  through model-result sealing

## Execution
- whole-cohort preflight matrix
- model call plan
- actual Market/Core/A/B counters
- 24 preview inventory/hashes if successful
- separate Monitoring-AI result bundle identity

## Safety
- provider refresh `0`
- production side effects `0`
- validation
- secret scan
- bundle manifest

---

# 24. Final principle

Do not fix missing source dates by inventing dates.

Do not fix missing SNDK directional authority by promoting context.

The correct closure is:

- preserve intrinsic source time separately from projection time;
- preserve explicit zero-direction evidence as an honest typed limitation if the existing policy supports it;
- then let Monitoring AI operate on the same sealed source packet without ever seeing the independent review that will later be used to evaluate it.
