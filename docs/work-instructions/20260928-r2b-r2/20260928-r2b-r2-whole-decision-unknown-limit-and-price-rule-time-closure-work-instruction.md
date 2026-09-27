# Thesis Monitor — R2B-R2
## Whole-Decision UNKNOWN_LIMIT Closure + Stored Price-Rule Time Ownership + Monitoring-AI Resume

**Purpose:** close the sole remaining Core policy blocker from R2B-R1 and proactively close the 20 non-Core stored-price-rule time-ownership gaps before A/B dispatch.

R2B-R2 must preserve the exact sealed source packet, the blind source ZIP, and the already-frozen external independent assessment. It must not read the independent assessment content before Monitoring-AI output is sealed.

The core product rule to implement is:

> A complete source packet with zero authorized directional facts is not an error and is not a balanced 5:5 investment verdict. It is a typed `UNKNOWN_LIMIT / OBSERVE` whole-decision state with no directional ratio and no inferred Holder action.

This must be generic. No SNDK-specific branch.

---

# 0. Newest SoT

Adopt R2B-R1 as the newest implementation/result SoT.

R2B-R1 result ZIP SHA-256:

`98c7e04458e5ec63c7ca7b5a198bd72e4b0f817998a20a921e0302e0cf6222e3`

Terminal:

`R2B_R1_ZERO_DIRECTIONAL_ENTITLEMENT_POLICY_DECISION_REQUIRED`

Repository:

- branch:
  `codex/r2b-r1-date-unknown-limit`
- base:
  `2829fd36ed9245b7c7199e134b531f7c9a0d226b`
- instruction:
  `00d25eadc59703198621183dad1154186258bab2`
- final tested local SHA:
  `98543a8778a0517a0b5c3da69f935c480f8ef302`
- operating main:
  `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`

Result integrity recheck:

- outer ZIP SHA matches sidecar
- internal bundle manifest: `61/61`
- missing: `0`
- hash/size mismatch: `0`
- extra manifest-scope files: `0`

R2B-R1 accepted results:

- source assembly:
  `22/22 PASS`
- date contract:
  `51/51 affected Core projections repaired`
- source date families:
  - `canonical:security_identity:current` = 22
  - `canonical:security_basis:current` = 22
  - `canonical:valuation:book_quality` = 7
- whole-cohort Core source preflight:
  `21/22 PASS`
- sole blocker:
  `SNDK`
- Market/Core/A/B actual calls:
  `0/0/0/0`
- previews:
  `0/24`
- provider refresh:
  `0`
- authority widened:
  `false`
- independent assessment content read:
  `false`
- reveal gate:
  `CLOSED`

Validation:

- focused:
  `119 PASS`
- full:
  `6069 PASS / 63 unchanged skips`
- Ruff/diff/Investment Knowledge/Chart Knowledge:
  PASS

Do not undo the R2B-R1 source-time repair.

---

# 1. Immutable source/blind identities

Use the exact existing source packet.

Source identities:

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

Blind source ZIP:

`thesis-monitor-20260927-r2b-BLIND_SOURCE_REVIEW.zip`

SHA-256:

`d705d36dabfa99f8d096a2bce4ddf996229680650cb09a45abffb5d7e9213ec3`

Neutral independent-freeze receipt:

`thesis-monitor-20260927-INDEPENDENT_FREEZE_RECEIPT.json`

SHA-256:

`f0f71fd39091369f280242d7a41af32a9cdbf3e0fa505fe2427f89b768eee26a`

Do not regenerate the blind bundle unless source-derived content changes—which this task does not authorize.

---

# 2. Anti-contamination hard rule

R2B-R2 may read only the neutral independent-freeze receipt.

It must not read, search, open, mount, parse, diff, summarize, or inject:

- `INDEPENDENT_BLIND_ASSESSMENT.json`
- `INDEPENDENT_BLIND_ASSESSMENT.md`
- `INDEPENDENT_BLIND_ASSESSMENT.zip`
- any independent market/stock verdict
- any independent BUY/SELL ratio
- any independent Overall/New Buyer/Holder output

through Monitoring-AI result sealing.

Add an explicit path/input allowlist and read audit.

Required output:

`independent_assessment_content_read = false`

through result sealing.

---

# 3. Exact remaining Core blocker

R2B-R1 proves:

- source assembly for SNDK:
  PASS
- SNDK directional authority refs:
  `0`
- SNDK persisted event allowed uses:
  `CONTEXT`
- event:
  `requires_review = true`
- reported financial:
  unavailable/denied
- authority widening:
  false

The existing claim-level semantics already support:

- `claim_type = UNKNOWN_LIMIT`
- `direction = OBSERVE`

But the whole decision schema does not.

Current failure:

`M12DS_R2_HOLDER_AXIS_CONTRACT_DEPENDENCY`

Reason:

> Every existing Holder branch requires an observed-business effect; there is no whole-decision neutral limitation branch.

Do not solve this by promoting CONTEXT.

---

# 4. Product policy — zero directional entitlement is a limitation state

Add a generic whole-decision mode equivalent to:

`UNKNOWN_LIMIT`

or repository-native naming.

Preconditions must require all:

1. complete stock source packet;
2. source authority graph PASS;
3. current price/technical mandatory inputs PASS;
4. directional authority count for `OVERALL_DIRECTION` == 0;
5. no eligible positive directional observation;
6. no eligible negative directional observation;
7. no eligible Holder support/risk/reduce observation;
8. zero entitlement is a verified source-use result—not a source assembly error;
9. denied/context-only evidence remains explicitly denied/context-only.

This state means:

> The system has insufficient source-authorized business direction to assign an investment direction.

It does **not** mean neutral fundamentals.

---

# 5. Distinguish UNKNOWN_LIMIT from balanced/neutral evidence

Do not encode zero evidence as:

- BUY:SELL = 5:5
- NEUTRAL because positives and negatives cancel
- HOLD
- WAIT because price looks inconvenient
- confidence = medium/low directional verdict

`UNKNOWN_LIMIT` is a different epistemic state.

Required distinctions:

## `EVIDENCE_BASED`
At least one authorized directional source exists.

Normal directional decision logic applies.

## `UNKNOWN_LIMIT`
No authorized directional source exists.

No positive/negative/neutral directional balance may be inferred.

---

# 6. Whole-decision schema shape

Audit the current R4-R4 → R3 → R2 schema chain and implement the smallest generic typed extension.

Recommended semantics:

- `decision_mode`:
  - `EVIDENCE_BASED`
  - `UNKNOWN_LIMIT`

For `UNKNOWN_LIMIT`, require:

- `overall = OBSERVE`
- `new_buyer = OBSERVE`
- `holder = OBSERVE`
- `directional_ratio = null`
- `directional_confidence = null` or an explicitly non-directional `NOT_ASSESSED`
- `limitation_reason` non-empty
- `unknowns` non-empty
- `required_next_evidence` non-empty
- no BUY/SELL/ADD/REDUCE/HOLD investment action inferred

Use repository-native types if equivalent.

Do not introduce `HOLD` as the neutral-limit Holder result.

`HOLD` implies a portfolio action stance; `OBSERVE` means no Holder action inference is authorized.

---

# 7. Overall semantics in UNKNOWN_LIMIT

Rendered/typed Overall must communicate:

- no directional investment conclusion
- source-authorized business direction unavailable
- context/technical observations may still exist
- no BUY:SELL ratio

Allowed semantic form:

`OBSERVE — directional evidence unavailable`

Do not state:

- neutral fundamentals
- balanced risks/opportunities
- thesis intact
- bullish/bearish
- 5:5

unless separate authorized evidence supports those claims.

---

# 8. New Buyer semantics in UNKNOWN_LIMIT

New Buyer axis must not become a directional entry recommendation.

Required typed state:

`OBSERVE`

Meaning:

> No new-entry direction can be authorized from the available business-direction evidence.

Technical price context may be shown as context if already authorized for:

- `ENTRY`
- `PRICE_ENTRY_CONTEXT`

But it may not create a BUY recommendation when Directional Core is unavailable.

Do not convert:

“price is near support”

into:

“new buyer should buy”

without directional authority.

A price context may instead support wording equivalent to:

“price timing context exists, but entry direction is withheld pending qualified business-direction evidence.”

---

# 9. Holder semantics in UNKNOWN_LIMIT

This is the main missing policy.

Add a generic Holder limitation branch.

Required state:

`OBSERVE`

Meaning:

> No add/reduce/hold-action conclusion is source-authorized because no Holder-direction business evidence exists.

Do not emit:

- ADD
- REDUCE
- SELL
- BUY
- HOLD

as an investment action solely from zero directional evidence.

Existing position status does not itself create a Holder recommendation.

Allowed renderer semantics:

- “보유자 판단 보류”
- “사업 방향 근거 부족으로 증액/축소 판단을 유보”
- repository-equivalent wording

This is an epistemic limitation, not a trade instruction.

---

# 10. Context evidence under UNKNOWN_LIMIT

Context-only evidence may remain visible only under its exact allowed-use contract.

For SNDK:

the persisted event remains:

- `CONTEXT`
- `requires_review = true`

It remains prohibited for:

- `OVERALL_DIRECTION`
- `HOLDER_STANCE`
- `ENTRY`
- `VALUATION`
- `CONFIDENCE`
- `BUSINESS_CONTEXT`
- other currently prohibited uses

Do not change its authority record.

Do not treat the headline as confirmed contract value.

---

# 11. Technical evidence under UNKNOWN_LIMIT

Technical evidence remains independently source-owned.

It may describe:

- trend
- support/resistance
- volatility
- price position
- technical caution

within its existing allowed uses.

It must not bootstrap missing business direction.

In UNKNOWN_LIMIT:

- Price Timing may be informative;
- Directional Core remains unavailable;
- New Buyer/Holder remain OBSERVE unless an existing independent policy explicitly permits a non-directional technical-only action. REV10/R2B-R1 evidence does not prove such a policy; do not invent one here.

---

# 12. Upgrade/downgrade conditions in UNKNOWN_LIMIT

Do not write directional upgrade/downgrade conditions that assume a current direction.

Instead require source-specific evidence-resolution conditions.

Examples of allowed generic conditions:

- qualified current/prior reported financial comparison becomes available;
- a source-authorized business event gains directional entitlement under existing rules;
- current denied lineage becomes qualified.

Do not use a price threshold alone to resolve missing business direction.

---

# 13. Model prompt contract for UNKNOWN_LIMIT

The model-facing context must explicitly state:

- `decision_mode = UNKNOWN_LIMIT`
- directional authority refs = 0
- directional claims prohibited
- Holder action claims prohibited
- event/context refs remain context-only
- technical refs do not confer fundamental direction

The model may explain the limitation.

The model may not invent a direction.

Use a structured output schema that makes a directional ratio impossible/null in this mode.

Do not rely only on prose instructions.

---

# 14. Validator contract

Add strict validation for UNKNOWN_LIMIT.

Reject if any output contains:

- BUY/SELL directional ratio
- bullish/bearish Overall
- Holder ADD/REDUCE/HOLD action
- New Buyer BUY/SELL action
- directional confidence
- unauthorized context ref used directionally
- price-only evidence used as Directional Core

Require:

- mode is UNKNOWN_LIMIT
- Overall OBSERVE
- New Buyer OBSERVE
- Holder OBSERVE
- no directional ratio
- limitation evidence state
- source-use denials preserved

No semantic retry is authorized.

---

# 15. Renderer contract

The renderer must visibly distinguish:

## Neutral/balanced evidence
Normal evidence-based neutral decision.

versus

## UNKNOWN_LIMIT
No authorized directional evidence.

Do not render both as a generic “중립”.

UNKNOWN_LIMIT output must make the limitation explicit.

Do not render `5:5`.

Do not convert OBSERVE to HOLD.

---

# 16. Generic tests for zero-direction policy

At minimum:

1. zero direction refs + complete source -> UNKNOWN_LIMIT PASS
2. zero direction refs + missing current price -> source FAIL, not UNKNOWN_LIMIT
3. zero direction refs + source authority error -> FAIL
4. context-only event -> remains context-only
5. technical-only context -> cannot produce Overall direction
6. UNKNOWN_LIMIT + BUY ratio -> FAIL
7. UNKNOWN_LIMIT + Holder HOLD -> FAIL
8. UNKNOWN_LIMIT + Holder REDUCE -> FAIL
9. UNKNOWN_LIMIT + New Buyer BUY -> FAIL
10. UNKNOWN_LIMIT + OBSERVE all axes -> PASS
11. one positive authorized direction ref -> normal evidence-based path, not UNKNOWN_LIMIT
12. one negative authorized direction ref -> normal evidence-based path
13. both positive/negative authorized refs -> normal evidence-based neutral/mixed path, not UNKNOWN_LIMIT
14. no ticker-specific branch
15. SNDK fixture follows generic result

---

# 17. Proactive A/B blocker — 20 undated stored-price-rule refs

R2B-R1 reports:

- canonical projection PASS:
  `545`
- remaining blocked undated non-Core refs:
  `20`

All 20 are:

`canonical:chart:stored_price_rules`

Canonical source:

`investment_thesis`

Example fields include:

- `confirmation_price`
- `invalidation_price`
- `support_zone_high`
- `support_zone_low`
- `warning_price`
- currency
- basis

Allowed uses include:

- `CONTEXT`
- `ENTRY`
- `PRICE_ENTRY_CONTEXT`

They are prohibited from:

- `OVERALL_DIRECTION`
- `HOLDER_STANCE`
- valuation/business direction

These are not deterministic identity metadata.

Do not classify them as `UNDATED_DETERMINISTIC_METADATA` merely to make them pass.

---

# 18. Stored price rules are versioned strategy metadata, if provable

Audit the canonical owner that creates:

`chart:stored_price_rules`

and the accepted Class-C:

`stored_thesis_and_business_metadata`

Determine whether each stored price-rule fact is exactly owned by a versioned investment-thesis record.

A rule may be admitted as versioned strategy metadata only if all are proven:

- exact security/ticker
- exact thesis/version record
- exact stored rule values
- currency/basis
- source/version hash
- record effective/as-of/version ownership
- no current price substitution
- no projection-date invention

Suggested generic source-time kind:

`VERSIONED_STRATEGY_METADATA`

or repository-equivalent.

---

# 19. No thesis-version ownership -> exclude from model input

If exact stored-price-rule version ownership cannot be proven:

- preserve the fact in the underlying packet if required for audit;
- mark its A/B source-use as unavailable/denied;
- exclude it from model-facing ENTRY / PRICE_ENTRY_CONTEXT evidence;
- do not assign `2026-09-27` as source date;
- do not block Core direction merely because an optional stored rule is unavailable.

Use exact denial:

`STORED_PRICE_RULE_TIME_OWNERSHIP_UNRESOLVED`

or repository-equivalent.

No missing-to-current-date.

---

# 20. Current technical price context remains separate

Do not confuse stored thesis price rules with current technical features.

Current technical features have their own:

- source bars
- as-of/session
- technical-context IDs
- price levels

If stored price rules are excluded for unresolved version time:

- current technical price context may still be used under its existing authority;
- no stored-rule value may leak through a copied summary/renderer field.

---

# 21. A/B readiness preflight before model dispatch

Before the first model call, run a full model-input readiness audit for all 22 subjects covering:

- Core directional source-use
- UNKNOWN_LIMIT mode
- A/New Buyer evidence
- B/Holder evidence
- stored-price-rule source-time ownership
- technical-context source time
- valuation evidence
- optional denied facts

Require no unclassified source-time evidence is visible to A/B prompts.

For each subject produce:

- Core readiness
- New Buyer readiness
- Holder readiness
- decision mode
- visible evidence refs
- denied evidence refs
- source-time state
- exact blocker

No eligible-subset dispatch.

All 22 must be prompt/schema-ready.

---

# 22. Blind bundle/source invariance

The economic/source data is unchanged.

Verify exact:

Blind source ZIP SHA:

`d705d36dabfa99f8d096a2bce4ddf996229680650cb09a45abffb5d7e9213ec3`

Source packet hashes from Section 1.

Policy/schema changes may create new model-view hashes.

They must not mutate:

- raw source values
- canonical source authority
- blind source ZIP
- current stock packet source hashes

unless an explicit evidence-view derivative is separately hash-linked.

---

# 23. Reissue exact model-input binding

After whole-cohort Core/A/B readiness passes:

create a new immutable model-input binding that records:

- source packet/run-seed hashes
- policy/schema hashes
- source-time projection contract
- 22 per-subject decision modes
- visible ref sets
- denied ref sets
- stored-price-rule inclusion/exclusion decisions
- prompt/schema hashes

This binding supersedes the blocked R2B-R1 preflight view only.

It does not replace the source packet seal.

---

# 24. Model dispatch conditions

Only dispatch if all hold:

- blind ZIP verified
- neutral external freeze receipt verified
- independent assessment content unread
- source packet hashes verified
- Core/A/B whole-cohort readiness `22/22`
- no authority widened
- no unclassified model-visible source-time refs
- UNKNOWN_LIMIT validator PASS
- new model-input binding sealed

If not:
- actual Market/Core/A/B calls remain 0.

---

# 25. Monitoring-AI bounded call plan

Use the existing R2B frozen bounded plan unless a direct implementation incompatibility is proven:

- Market: max `2`
- Core: max `8`
- A: max `8`
- B: max `8`
- model: existing GPT-5.6 Sol configuration
- reasoning effort: existing frozen xhigh configuration
- per-call max time: `1200s`
- transport retries: `0`
- semantic retries: `0`
- fallback: `0`
- judge: `0`
- provider refresh: `0`

No partial dispatch.

No old candidate fill.

---

# 26. 24-message result requirement

On successful execution:

- US market = `1`
- US stocks = `14`
- KR market = `1`
- KR stocks = `8`
- total = `24`

All messages bind the same sealed source packet.

Subjects in UNKNOWN_LIMIT still receive a rendered message, but it explicitly reports limitation rather than a fabricated directional verdict.

---

# 27. Monitoring-AI result isolation

Create a new Monitoring-AI result bundle.

Do not overwrite:

- first R2B blocker bundle
- R2B-R1 blocker bundle
- blind source bundle
- independent assessment bundle

Monitoring-AI result bundle may contain:

- actual model outputs
- normalized outputs
- validators
- 24 rendered previews
- message hashes
- model-call receipts
- model-input binding hashes
- source hashes

It must not contain independent assessment content.

---

# 28. Reveal gate

Monitoring-AI result bundle must be fully sealed before:

- opening the external independent assessment;
- comparing decisions;
- producing disagreement analysis.

Execution must output:

`independent_assessment_content_read = false`

through Monitoring-AI result seal.

Then set a separate post-seal state:

`MONITORING_AI_RESULT_SEALED_READY_FOR_COMPARISON`

Do not perform comparison in model prompting.

---

# 29. No provider refresh / production effects

Source/provider refresh:

`0`

Hard zero:

- Kiwoom
- OHLCV
- SEC
- OpenDART
- KRX
- news
- Alpha Vantage
- Massive
- any source API

Production side effects:

- Telegram = 0
- recipient intent = 0
- production DB writes = 0
- scheduler mutation = 0
- broker = 0
- deploy = 0
- main merge = 0
- push = 0
- restart = 0

---

# 30. Success terminal

`R2B_R2_MONITORING_AI_24_MESSAGE_PASS`

Require:

- whole-decision UNKNOWN_LIMIT generic policy PASS
- no SNDK authority widening
- stored-price-rule time audit complete
- all model-visible refs time-owned or explicitly denied
- whole-cohort Core/A/B readiness 22/22
- new exact model-input binding
- actual Monitoring-AI dispatch
- 24/24 rendered messages
- independent assessment unread through result seal
- provider refresh 0
- production side effects 0

---

# 31. Partial terminals

## Neutral whole-decision policy cannot close

`R2B_R2_UNKNOWN_LIMIT_WHOLE_DECISION_GAP`

Model calls = 0.

## Stored price-rule ownership cannot be safely resolved

If exclusion still leaves all 22 prompt-ready:

- proceed with explicit denials.

If one or more subjects become prompt-incomplete:

`R2B_R2_STORED_PRICE_RULE_TIME_OWNERSHIP_GAP`

Model calls = 0.

## A/B whole-cohort readiness gap

`R2B_R2_WHOLE_COHORT_MODEL_INPUT_GAP`

Return every subject/ref.

No partial dispatch.

## Model-stage failure

If source/preflight passed and actual model dispatch began:

use an exact model-stage terminal.

Do not reclassify as source failure.

---

# 32. Required validation

## UNKNOWN_LIMIT
- schema union/mode tests
- Overall OBSERVE
- New Buyer OBSERVE
- Holder OBSERVE
- null ratio
- no directional confidence
- context authority invariant
- normal evidence-based paths unchanged
- SNDK generic fixture

## Stored price rules
- thesis-version binding positive
- wrong thesis version negative
- altered price rule negative
- no source-version -> deny/exclude
- projection date cannot become source date
- technical source remains independent
- all 20 audited

## Whole-cohort model readiness
- Core 22
- New Buyer 22
- Holder 22
- source-time classifications
- visible/denied ref matrices
- no eligible-subset dispatch

## Anti-contamination
- external assessment files not read
- neutral receipt only
- no verdict leakage into prompt/model artifacts

## Repository
- R2B-R1 date regressions
- prior source/authority regressions
- full pytest
- Ruff
- git diff --check
- Investment Knowledge
- Chart Knowledge
- secret scan
- unchanged skip/xfail identity

---

# 33. Required result bundle

Return immutable ZIP + `.sha256` containing at minimum:

- `REPORT.md`
- `summary.json`
- R2B-R1 result identity/SHA
- source identities
- repository identities
- changed-file inventory

## UNKNOWN_LIMIT policy
- old/new whole-decision contract
- decision-mode schema
- Holder neutral-limit contract
- New Buyer neutral-limit contract
- renderer contract
- validator matrix
- positive/negative tests
- SNDK entitlement invariance

## Stored price rules
- 20-ref inventory
- canonical source rows
- thesis-version ownership matrix
- source-time classification
- included vs denied matrix
- A/B visible-ref matrix

## Preflight
- 22-subject Core readiness
- 22-subject New Buyer readiness
- 22-subject Holder readiness
- exact model-input binding + SHA
- blind/source invariance receipts
- anti-contamination receipt

## AI execution
If successful:
- model call receipts
- actual Market/Core/A/B counts
- 24-message inventory
- 24 message hashes
- Monitoring-AI result bundle identity/SHA
- result-sealed comparison-ready receipt

## Safety
- provider refresh = 0
- production side effects = 0
- validation logs
- secret scan
- bundle manifest

---

# 34. Final principle

“No authorized directional evidence” is not the same as “neutral evidence”.

The system must be able to say **OBSERVE / UNKNOWN_LIMIT** without inventing a BUY:SELL ratio or Holder action.

Likewise, an undated stored price rule is not current simply because the model is running today. It must be tied to an exact thesis version or excluded from model-visible timing evidence.

Only after both contracts are explicit may Monitoring AI be allowed to produce the 24-message dry run.
