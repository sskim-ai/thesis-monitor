# REV56B Current Security/Basis Applicability Coverage Audit

## Decision

Terminal: `R2B_R9_REV56B_SOURCE_OWNER_CONTRACT_GAP` (Outcome B).

The independent, non-executable coverage audit closes 21 of 22 frozen subjects.
The remaining subject is `003690`, specifically its unavailable
`CURRENT_FY1_FPER` slot. Nine required category cells are unresolved. Coverage
is **not** complete; `current_blocker_count = null`. No runtime coverage owner,
B2 v2 implementation, new model request or REV57 controller was created.

This is an applicability/provenance gap, not a conclusion that the security is
invalid or that NewBuyer should WAIT. The existing qualified PER remains valid.

## Repository Identity

| Identity | Exact SHA |
|---|---|
| Production code baseline | `45f4c53f6113575f91a067c423d471023cd4f560` |
| Exact local REV56A parent | `d472d4d3941b62bcc2435ac634e50467249e9983` |
| Instruction-first commit | `28b06e357461cf2a190bed4e774ef1a7e49be83b` |
| origin/main | `9b134350cd05c127b6dc866d34a477d95c54785c` |
| Protected operating checkout | `b610e6de0a8c33d199961e821ff1b130e1fa9ad4` |

Branch: `codex/r2b-r9-rev56b-current-security-basis-coverage-owner`.
Final local feature SHA is recorded in the result bundle's execution receipt.
No feature/main push, merge, deployment or operating checkout mutation.

## Immutable Inputs

REV56A ZIP SHA:
`2bb91614394290265e33d7a995b4f9a64be3ed7a1ea129a1551eacc73cc711ca`.
Sidecar, ZIP CRC and all 76 payload manifest entries passed, with no missing,
extra, duplicate, size-mismatched or hash-mismatched members.

Frozen source generations:

- US14: `rev46-us14-resume1-20261002T064847Z`.
- KR8: `rev47-kr8-20261002T114556Z`.

Current means current within these October 2 snapshots, not October 4 data.
The original 409 lineage artifacts and source input hashes are rechecked.
All eight KIS/native valuation contexts are reconstructed from original
receipts and exactly match the frozen context. No recollection occurred.

## Requirement And Producer Proof

The requirement matrix is built before dispositions, from metric-family
dataflow and hash-bound Security Master inputs. Neither the 26 historical
reachable-gap references nor blind labels determine category necessity.

The matrix covers 44 relevant valuation slots times 11 categories, plus 22
independent selected-business-quality cells: 506 cells total.

| Final cell disposition | Count |
|---|---:|
| Proven applicable, typed scoped decision | 308 |
| Proven non-applicable, positive non-consumption proof | 189 |
| Unresolved | 9 |

PER and FORWARD_PE/current FY1 fPER are the two relevant slots per subject.
PBR is excluded only under the unchanged B2 asset-relevance rule; every
cohort PBR has `asset_relevance_proven=false`. Research FY1 PER and FY1 EPS
are not standalone usable B2 facts. EPS remains a dependency of derived fPER.

Atomic provider ratios do not reprice against the current quote, reconstruct
EPS/shares, or convert reporting/price currencies. This is proven by the
producer and consumer code, not by numeric availability or an empty error list.
Currency-null Kiwoom identity receipts are never promoted to currency clearance.

Direct common-stock conversion non-applicability is additionally bound to
the exact producer input Security Master hash. ADR/depositary admission gates
remain applicable and their explicit denials remain metric scoped. A business
issuer bridge cannot qualify monitored-security per-share valuation.

Listing predicates are composed from typed provider receipts, their retrieval
time, the hash-bound input security and the existing producer predicate. This
proves the listing predicate only, not all share-class or basis properties.
For HUT, TSM and SKHY, returned exchange mismatch is separately provable.

The initial receipt-only inventory is preserved under `audit-attempt-1`.
Its compound listing/depositary gaps were narrowed using existing frozen
`locals.json` security input hashes. This was not a provider retry or a change
to any existing source, validator, model output or policy.

Native metric-as-of remains unknown where the provider did not supply it.
Retrieval time is only the provider-latest snapshot assessment boundary.
Finnhub FY1 is the existing `USER_AUTHORIZED_PRODUCT_POLICY`, not a claim
that an official Finnhub FY1 field definition was reproduced.

## Exact Remaining Gap

Affected metric slot:
`003690 / CURRENT_FY1_FPER` (unavailable slot, not a numeric fact ref).

The original KIS request is bound to security code and generation, returned
HTTP 200 with provider `rt_cd=0`, and has an empty `output3`. This independently
reproduces normal estimate unavailability; the source is not missing.

`kis_output3_protocol_owner.qualify` converts its `SemanticGap` to only
`state` and `value`. The frozen EPS owner therefore contains:

```json
{"state":"UNAVAILABLE_NO_KIS_RESEARCH_ESTIMATE","value":null}
```

`kis_current_fy1_owner.current_fper` returns `UNAVAILABLE_EPS` before attaching
the positive EPS security/date/receipt, price and corporate-action inputs.
The resulting receipt lacks a field-specific decision version, assessment
eligibility, effective time and source-receipt binding for those domains.
The outer source generation and acquisition timestamp cannot substitute for
unperformed field assessments. No estimate date, unit or period is invented.

The nine unresolved categories are:

1. SECURITY_IDENTITY
2. SECURITY_CLASS_OR_LISTING
3. PRICE_TO_SECURITY_BINDING
4. VALUATION_SECURITY_BASIS
5. VALUATION_CURRENCY_BASIS
6. SHARE_OR_DENOMINATOR_BASIS
7. VALUATION_HORIZON_OR_PERIOD
8. PROVIDER_SECURITY_BINDING
9. VALUATION_SOURCE_QUALITY

This does not deny the separately qualified native PER or the independent
current price/technical path. The missing EPS branch cannot be declared
fully assessed just because it exits early. Producer non-consumption proof
does not itself manufacture a current QUALIFIED or DENIED field decision.

Bounded next repair: preserve a versioned, source-hash-bound missing-estimate
assessment with exact request/security/generation/time; explicitly distinguish
assessed absence from deferred downstream domains. Define and test any
prerequisite-short-circuit applicability rule before changing coverage. Replay
the same frozen raw response offline; no recollection or value invention is
needed to design that contract. B2 v2 and model reproof remain gated.

## Cohort And Diagnostics

| Subject | Qualified relevant metrics | Typed unavailable/denied slots | Coverage |
|---|---:|---:|---|
| CORZ | 0 | 2 | Complete |
| CPNG | 0 | 2 | Complete |
| CRCL | 2 | 0 | Complete |
| GOOGL | 2 | 0 | Complete |
| HUT | 0 | 2 | Complete |
| IBM | 2 | 0 | Complete |
| MU | 2 | 0 | Complete |
| RXRX | 0 | 2 | Complete |
| SKHY | 0 | 2 | Complete |
| SNDK | 2 | 0 | Complete |
| TSLA | 2 | 0 | Complete |
| TSM | 0 | 2 | Complete |
| WRD | 0 | 2 | Complete |
| WULF | 0 | 2 | Complete |
| 000660 | 2 | 0 | Complete |
| 003690 | 1 | 0; one unresolved FY1 slot | Incomplete |
| 005490 | 2 | 0 | Complete |
| 005930 | 2 | 0 | Complete |
| 010120 | 1 | 1 | Complete |
| 012450 | 2 | 0 | Complete |
| 047810 | 1 | 1 | Complete |
| 086280 | 2 | 0 | Complete |

Coverage complete is not investment eligibility or BUY approval. Explicitly
denied metric routes can be completely assessed, while a missing assessment
cannot. Usable valuation evidence exists for 14 subjects; no stance changed.

- 003690: native PER preserved; FY1 missing-owner path is the sole coverage gap.
- 012450: native PER plus dated KIS fPER preserved; no target stance imposed.
- GOOGL: qualified atomic PER/forwardPE remain independent of reconstructed
  denominator unavailability; no EPS reverse calculation or same-session repricing.
- 010120: native PER denial does not invalidate its independent KIS FY1 fPER.
  No global valuation blocker is emitted.
- 047810: existing active-risk AVOID-only behavior is preserved independently
  of qualified KIS valuation evidence.
- SKHY: issuer business quality and monitored-security ADR/native valuation
  denials are distinct; the issuer bridge grants no valuation transfer.

The audit enumerates 62 category-level partial blocker candidates, not 62
distinct economic risks or an exhaustive blocker census. Overlapping identity
categories may reference the same source denial. None is enabled. The exhaustive
`current_blocker_count` remains null, and no global blocker is emitted.
Business-quality candidate denials (000660 and SKHY) do not become valuation
state. Per-subject all-metrics-invalid proofs and surviving qualified refs are
reported separately.

## Authority And Validation

All 22 accepted v1 outputs, 168 executable branch probes, Core claims/effects,
Pass A, Overall, score, Holder, valuation facts, current price and timing remain
unchanged. Seven active-risk subjects remain AVOID-only. All 95 legacy context
references are preserved with `UNRESOLVED_PENDING_BACKEND_COVERAGE`; no semantic
reclassification, supersession or veto-entitlement change occurred.

Price/technical inputs are audited separately. The existing US stale daily
technical limitations remain intact and are not repaired by a current raw quote.
No receipt grants new timing eligibility.

Focused validation includes missing owners, empty blocker lists, positive
atomic non-consumption, qualified alternate metrics, all-invalid proof,
legacy-prose isolation, missing decision/time/eligibility, prohibition on using
producer semantics alone for a current verdict, and no ticker-specific logic.
Exact test counts and final hashes are appended to the immutable result report.

Two unused imports in the report harness were removed after initial Ruff
inspection; the original findings are preserved. No runtime code changed.
Full pytest and Hosted CI are not claimed PASS and are not required for this
Outcome B preimplementation stop under instruction section 29.

Model/provider/source/message/Telegram calls, production DB/WAL writes,
scheduler mutations, deployment/restart, operating mutation, main merge and
remote pushes are all zero. Initial Git fetch is the only repository network
phase. Result delivery is separately authorized to iCloud `Thesis Monitor`
only, as one secret-scanned ZIP and one SHA sidecar.
