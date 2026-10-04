# KIS No-Estimate Availability Sidecar

REV56C is offline and default-off. No collector, prompt, model schema, B2 v1
stance function, production entrypoint, or existing valuation receipt changes.

## Observed Availability

`scripts/kis_no_estimate_owner.py` exposes a versioned
`KISResearchEstimateAvailabilityAssessmentV1`. Its sole negative observation is
that an exact request returned successfully without a usable research estimate
at its recorded retrieval time. It does not assert an estimate effective date,
EPS, currency, forecast period, share basis, or negative investment meaning.

Inputs bind the original raw body and request/response receipt to the sealed
plan, requested code, canonical security, generation, and aware start/end times.
Validation recomputes the receipt from those inputs, not from a supplied status.
Missing source/temporal bindings fail closed. No network client is present.

The deliberately narrow `KISResearchEstimateObservedNormalEmptyShapeV1` requires
HTTP 200, JSON content type, the exact endpoint transaction ID, `rt_cd=0`,
`msg_cd=MCA00000`, no continuation, all expected containers, and the observed
blank/zero `output1` together with empty `output2/3/4`. Empty `output3` alone is
insufficient. Missing containers, extra fields, positive identity/estimate data,
or a different empty shape do not acquire normal-empty authority.

`REQUEST_BOUND_NEGATIVE_AVAILABILITY_OBSERVATION` is explicitly distinct from
positive provider-returned security identity. A successful empty observation
leaves returned estimate identity unavailable. Positive estimates require the
existing EPS owner, including its source/security/retrieval binding; the new
sidecar does not recreate or replace that owner.

## Prerequisite Scope

`CurrentFY1FperPrerequisiteScopeV1` in
`scripts/newbuyer_fper_prerequisite_scope.py` validates the negative owner and
reproduces the unchanged old `UNAVAILABLE_EPS` receipt. A pinned, reviewed AST
prefix proves that `current_fper` returns before consuming EPS value/security/
period/unit/date, price, or action inputs. Changed pre-return code fails closed.

The versioned `newbuyer-unavailable-fper-category-requirements-v2` narrows only
the unavailable metric path:

- `SECURITY_IDENTITY`: exact requested-security observation, not a positive
  estimate identity or share-class clearance.
- `PROVIDER_SECURITY_BINDING`: exact request/response association, not a
  provider security snapshot.
- `VALUATION_SOURCE_QUALITY`: the typed research-estimate availability decision.
- Remaining downstream categories: non-consumption on this short-circuit path,
  not global irrelevance or a current qualified/denied state.

Producer semantics can own N/A only. A current denial comes from the frozen
source observation. An owner-less or malformed response cannot establish the
prerequisite and cannot turn downstream gaps into N/A.

## Coverage And Census

Coverage overlay changes only unresolved cells in the matching generation,
security, and `CURRENT_FY1_FPER` slot. Already resolved cells remain exact.
The census runs only after complete coverage and derives entries from typed
applicable denials. It deduplicates the exact owner/reason/scope/input tuple;
distinct owner receipts are not guessed economically equivalent.

The no-estimate denial is metric-scoped: it blocks this fPER value, not native
PER, other valuation metrics, business quality, or global NewBuyer resolution.
No global blocker is promoted by this task. Legacy confidence/context refs
retain their previous entitlement. B2 v2 requires a separate instruction.

## Frozen Reproof

The REV56C reproof preserves 497 previously resolved cells and closes the nine
unresolved unavailable-fPER cells: three current observation domains and six
short-circuit N/A domains. Total coverage is 506 cells over 22 subjects. Seven
positive KIS paths and the independently qualified native PER remain unchanged.

The KIS request plan and stock master have different currency projections
(`KRW` versus null in the observed empty case). They are joined only by exact
code, canonical security, and generation. The plan currency is never promoted
to estimate-currency authority. The new estimate currency/unit remains null.
