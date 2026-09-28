# Sealed Fresh Request Dispatch

REV11 adds an opt-in, unregistered transport boundary. It does not change REV10
analytical gates, source semantics, model policies, or renderers.

## Identity

`FreshRequestDescriptor` freezes a canonical public wire identity, generation,
logical request, role, subject, target period, page/document bounds, timeout,
retry limit, artifact path, and owner/config fingerprints. Nested request data
is immutable canonical JSON text. Credential values are not exported.

`ProviderPlan` rejects duplicate wire identities, cross-generation descriptors,
inconsistent budgets, and noncontiguous page declarations. Admission verifies
the exact accepted REV10 root receipt, mandatory role coverage, unresolved
roles, owner hashes, config hashes, and credential presence. A candidate is not
an executable final provider plan.

## Receipts

`SealedDispatcher` denies requests absent from the admitted whole plan before
transport, applies an overall per-attempt timeout, preserves failed responses,
and retries only the existing transport-transient classes without changing the
request. Authorization/secret failures latch a systemic stop. Independent
requests can continue after ordinary transport or normalization failure.

Plan, start, attempt, raw, normalization, role-binding, and final receipts are
written exclusively. `consume_bound_result` resolves the exact final receipt
hash and checks generation, descriptor, plan, request, raw, normalization, and
role-binding hashes. Retrieval time is distinct from source observation period.

Normalization is supplied by the registered owner in an isolated controller.
The unit test owner is fictional. Existing financial/market/stock owners are
not automatically registered by giving their filename or hash to a plan.
No production endpoint, scheduler, collector, or model route imports this module.

## Exactness Boundary

A finite envelope is not an exact set of requests:

- SEC current/prior accessions, primary documents and exhibits are selected
  from fresh submissions, index and document responses.
- OpenDART statement year/report-code selection follows its fresh filing list.
- Kiwoom page two and later require response-owned continuation keys.
- The native US market owner resolves exchange identity from symbol discovery.

Under REV11 sections 3 and 5 these response-derived child requests cannot be
created after any provider data has been observed. Guessing them, importing old
mutable selection, or silently reinterpreting a wildcard as an exact request
is forbidden. `r9_rev11_provider_inventory.py` therefore emits a diagnostic
inventory and `R2B_R9_REV11_PROVIDER_PLAN_GAP`, not a live plan.

The static subset includes first stock pages, SEC discovery/companyfacts,
bounded OpenDART discovery pages, KR single-response market reads, configured
FRED/EIA/ECOS requests and the finite KOSPI200 history window. These descriptors
are not dispatched independently of the missing mandatory roles.

KR global capability is unchanged. `MAX_KR_REQUEST_PAGES` names the existing
20-page bound without changing it. A request-local required cap needs verified
minimum rows per page plus consumer-completeness semantics. A maximum page
size or an owner heuristic is not such a proof; unknown remains unproven.

The next decision is operational, not analytical: authorize a specifically
bounded, response-bound child-request protocol, or provide an independently
sealed complete exact request set. REV11 does neither implicitly. Any later
protocol must retain issuer/window/selection rules, child-slot and attempt
limits, no widening, and provenance for every cursor/document selection.
