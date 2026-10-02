# R2B-R7 Absolute Financial Direction Guard

## Decision

**R2B_R7_ABSOLUTE_CURRENT_DIRECTION_GUARD_PASS**

The objective source-policy repair and sealed R6 offline audit pass. The required
post-seal comparison ZIP was not available locally: its expected SHA is recorded
below, but its contents and hash are **not verified**. Therefore the complete
cross-review comparison audit is pending that artifact, not claimed complete.

No model/provider calls, policy calibration, production changes, or GitHub push.
The new corpus is **POST_COMPARISON_SOURCE_POLICY_CORRECTED**, not the original
blind result. All original R6 bytes remain unchanged.

## Repository

- Branch: `codex/r2b-r7-absolute-financial-direction`
- Base R6: `ad24ba92e8a7d8494a62c5e90a8321fba9c5230d`
- Instruction-first commit: `7140f09f05f12e5b214f4511663a858a8b29d2ed`
- Initial implementation: `651cadc11f6189f0d9f5d13c0426e4e9a56fe32d`
- Final tested implementation: `174af2b0a0cef373c85a9a27fe22604839c8acf9`
- Final report-only commit: recorded in bundled `repository-identities.json`.
- Operating: `b610e6de0a8c33d199961e821ff1b130e1fa9ad4`, unchanged and clean.
- Main merge / remote push / deploy / restart: 0. GitHub Actions not run.

## Objective Repair

`absolute-financial-direction-eligibility-v1` owns the generic additional guard.
Current-only financial amount signs cannot authorize Overall, Holder, Entry, or
New Buyer execution-risk direction. Existing factual/context uses remain.

The guard narrows the source-use derivative before Core, removes the historical
amount-sign observation fallback, and rechecks directional atomic claims during
materialization and capability construction. It accepts compatible comparative
observations using the existing comparison owner, including its fiscal-calendar
lineage. No periods, prior values, or economic semantics were invented.

Polarity is validated against typed source entitlement, not prose keywords.
BULLISH/BEARISH without any direction-eligible parent fails. NEUTRAL context
remains valid. A mixed claim with a valid directional parent remains subject to
the existing exact-parent/intersection and effect rules.

The old coverage adapter now distinguishes valid absolute-only context from
unusable source quality. No quality denial or investment threshold was relaxed.

## All-Subject Result

Programmatic scan: 22 subjects; invalid directional claims: **3**, across **2**
subjects. These counts are observed proof results, not policy constants.

| Subject | Invalid claims | R6 Overall / score | Corrected Overall / Buyer / Holder |
|---|---:|---|---|
| 005930 | 2: positive current revenue and operating income | BUY / 6.5 | OBSERVE / OBSERVE / OBSERVE |
| 047810 | 1: positive current operating income | HOLD / 5.5 | OBSERVE / OBSERVE / OBSERVE |

Both reach zero authorized directional refs. The existing deterministic
UNKNOWN_LIMIT contract therefore clears Buy/Sell scores and confidence to null.
Underlying financial facts remain available in the frozen packet and report;
technical information stays context, not a substitute for business direction.
No new Core/A/B candidate was generated.

- Unaffected stock subjects: **20/20**, including unchanged SNDK UNKNOWN_LIMIT.
- Unaffected ordinary Core/A/B: **19/19**, exact claims and decisions retained;
  capabilities revalidated, ignoring only the new source-binding identity.
- Original messages reused byte-for-byte: **22/22** (20 stocks + 2 markets).
- Corrected corpus: **24/24** (22 stocks + 2 markets), 2 deterministic changes.
- Corrected decision modes: 19 ordinary + 3 UNKNOWN_LIMIT.
- Comparative observations and original source hashes: unchanged.

## Descriptive Policy Audit

The following counts describe **original R6**, not the corrected population.
No independent labels entered the repair or were used as expected outputs.

### Execution-Dependent Growth

| Subject | Overall / score | New Buyer | Holder | SELL permitted? |
|---|---|---|---|---|
| CPNG | HOLD / 4.5 | AVOID | REVIEW | Yes |
| HUT | HOLD / 5.5 | AVOID | REVIEW | Yes |
| WULF | HOLD / 4.5 | AVOID | REVIEW | Yes |

CPNG/HUT used both positive and negative observed refs. WULF used verified
deterioration but selected INSUFFICIENT_DIRECTIONAL_EVIDENCE. Current contracts
permit SELL for comparative deterioration; they do not force it. Active adverse
risk without compensating valuation independently restricts Buyer/Holder.

Audit-only ambiguity: `m12ds_r2_schemas.decision_schema` always offers the
insufficient-evidence HOLD branch, and `m12ds_r2_judgment_policy.validate_decision`
does not require zero directional refs for that reason. WULF demonstrates that
this wording can coexist with negative-only directional evidence. Whether the
reason means insufficient quantity or insufficient decisiveness needs a separate
product-policy decision. No new SELL rule, veto, or calibration was added here.

### Action and Score Compression

- New Buyer: WAIT 14, AVOID 7, ATTRACTIVE 0; plus SNDK OBSERVE.
- All 21 ordinary subjects lack a resolved fundamental entry range/compensating
  discount. WAIT rows use VALUATION_UNRESOLVED; AVOID rows use active adverse
  risk without compensation. Security basis is separately unresolved. Technical
  support cannot replace those missing qualifications.
- Holder: HOLDABLE 14, REVIEW 7; plus SNDK OBSERVE. ADD is absent from contract
  vocabulary. REDUCE requires PERSISTENT_OR_IMPAIRED support, while the current
  provider Core schema exposes CONTEXT_ONLY/ACTIVE_MATERIAL_RISK and the current
  adapter lacks a realized-impairment source owner. This is partly a structural
  capability restriction, not simply a model preference in this sample.
- Observed scores: 4.5..7.5. Actual schema bins span 0..10 in half-point steps;
  neither the schema nor validator mandates the observed narrow range. The
  independent range 2..8 is stated by the instruction but not independently
  checked against the missing comparison report.

### Large-Cap Matrix

| Subject | R6 Overall | Score | Buyer | Holder | Confidence | Quality effect |
|---|---|---:|---|---|---|---|
| GOOGL | BUY | 6.5 | WAIT | HOLDABLE | MEDIUM | NONE |
| MU | BUY | 7.5 | WAIT | HOLDABLE | MEDIUM | NONE |
| TSM | BUY | 7.5 | WAIT | HOLDABLE | MEDIUM | NONE |
| SKHY | BUY | 6.5 | WAIT | HOLDABLE | LOW | CONFIDENCE_ONLY |
| 000660 | HOLD | 5.5 | WAIT | HOLDABLE | LOW | CONFIDENCE_ONLY |
| 005930 | BUY | 6.5 | WAIT | HOLDABLE | LOW | NONE |

005930 is corrected to all-axis OBSERVE in R7. SKHY/000660 carry financial-quality
denials in their typed quality envelope; those are confidence/source-coverage
constraints, not a reason to loosen investment thresholds. Their selected
individually qualified business evidence remains governed by its own authority.

Possible future product choices, not implemented recommendations: retain separate
axes; improve qualified valuation/security coverage; explicitly review downside
aggregation; design a broader Holder action vocabulary with new evidence gates.

## Validation

At clean implementation `174af2b0`:

- Focused: **717 passed**.
- Full pytest: **6,222 passed**, **63 skipped**, 0 failures, 3 existing warnings.
- Skip/xfail identities: identical to R6; no added skip or threshold relaxation.
- New guard matrix: 27 tests covering signs, comparative direction, basis/period
  mismatch, source denial, polarity, mixed refs, recovery, and neutral facts.
- Ruff / diff check / Investment Knowledge / Chart Knowledge: PASS.
- Initial full run: 5 failures from legacy current-only coverage assertions.
  Their expectations were reconciled without weakening binding or quality checks;
  the cohort-ready unit test still tests its schema-gate boundary separately.
- Both initial and final receipts are retained. Final report-only diff contains
  no executable change. Secret-scan and archive manifest are generated at seal.

## Provenance and Limits

R6 result ZIP (verified, all 815 members):
`c2578c352831f5240e83ca6c6d9ac81957adfc89bd0cabe0f38f960f003648a3`

R6 combined source packet:
`c4fbc25ec81abe61c3981bfaa44204cc7e15cc252f25cbe6aedc6b2a1de9b44f`

Independent V2 ZIP and JSON (hash-verified unchanged; judgments not interpreted):
`b025e86ba211fafe89d56be8268652c6482d589ea12e8510dbf040442e40ed77`
`9a083de6bef2b5b0e617136e10a67eed00ff5cacffc79809825f2ea51d34557d`

Missing post-seal comparison ZIP expected SHA, **not verified**:
`8002957138129ec4d31bb9880c5d038de0114a60206a5248c293efa45334504f`

Bounded follow-up: obtain that exact ZIP, verify identity, then append a read-only
comparison audit. No new model calls or policy retuning are needed for that step.

## Safety and Delivery

Model / provider / Alpha Vantage / Telegram / recipient intent / broker / production
DB writes / warning or notification mutation / scheduler changes / deploy / restart /
main merge / push: **0**. Network guard observed 0 attempted calls during offline proof.
Operating config, DB file hashes, and scheduler state are compared from immediately
before the final offline proof through sealing; this is not claimed as a full-task
historical snapshot. Local report commits only.

The deliverable is one secret-scanned ZIP plus its SHA file. iCloud root and
`Thesis Monitor` copies use standing user authorization; `icloud-delivery.json`
records destination readback hashes and per-file upload flags after sealing.
