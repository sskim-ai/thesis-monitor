# NewBuyer B2 Shadow Contract

REV52 adds `newbuyer-qualified-valuation-context-v1` to the explicit artifact-only
`Execution.newbuyer_shadow_requests(settings)` entry point. It is not called by
`run()`, production dispatch, assessment persistence, or a renderer. The
`NEWBUYER_QUALIFIED_VALUATION_SHADOW` setting defaults to `false`. OFF returns before
reading any inputs. Neither ON nor OFF authorizes a model call or delivery.

## Ownership

- The caller supplies accepted, frozen Core/A/B and their original source generation.
- The adapter checks the existing valuation context, exact native snapshot identity,
  Core effect binding and dual raw/emitted source metadata binding. It uses the
  existing canonical metadata hash API, not a new serialization assumption.
- Current means current to that frozen source generation, not current wall-clock time.
- Original business claims, classification and Holder are read-only context. Digests
  cover the original Core, capability, A, B and entire B input; no upstream writes occur.
- Only the new NewBuyer output is model-authored. Exact numbers stay in source facts.

## Decision Paths

Active material business risk has first priority and exposes AVOID only, with the
exact complete current risk set. Timing and multiples cannot compensate it.

Otherwise an already-owned valid absolute-range discount retains its separate
`ABSOLUTE_FUNDAMENTAL_RANGE` path, `SOURCE_DETERMINISTIC` authority and
`VALID_FUNDAMENTAL_DISCOUNT` reason. The frozen option, eligible candidates,
VALUATION permissions, security-basis gate and current-price relation must agree.
This path has explicit precedence when both kinds of evidence exist. No multiple
is converted into an absolute range. Legacy OFF schemas and policies are untouched.

The additional B2 ATTRACTIVE capability requires frozen Overall BUY, positive Core
refs, no negative Core refs, no active risk and eligible valuation evidence. A
future model must then explicitly judge SUPPORTIVE with exact valuation/business
refs and `QUALIFIED_VALUATION_CONTEXT_SUPPORTIVE`. Evidence presence alone does not
assign that state. Economic correctness remains a later model-proof question.

Qualified PER and fPER remain separate evidence; their coexistence creates no
cheapness or growth relation. PBR is retained as context but the current adapter
has no asset-relevance owner, so it cannot independently anchor economic judgment.
Finnhub FY1 preserves USER_AUTHORIZED_PRODUCT_POLICY, not an official field-definition
claim. KIS FY1 retains dated house-research provenance, not consensus or NTM.

## WAIT and Timing

Every WAIT reason is a schema branch with a backend predicate. Valuation unresolved
means *judgment* unresolved even if facts exist. Confidence requires exact caution
or quality refs, or typed insufficient business evidence. NO_CLEAN_ENTRY requires
WAIT_FOR_ZONE and exact relation refs; ENTRY_TIMING_UNRESOLVED requires unresolved
timing. NEUTRAL/BURDENSOME reasons must use the same refs as the valuation judgment.
BUSINESS_MIXED and BUSINESS_GATE_NOT_MET are capability-bound. PRICE_NOT_FAVORABLE
is unavailable because no owned relation supplies it.

Timing uses only the uniquely selected eligible technical zone with exact current
price, date, currency, price basis and ENTRY permission. Inside inclusive boundaries
is FAVORABLE_NOW; outside is WAIT_FOR_ZONE; all identity/basis gaps are UNRESOLVED.
Timing is constant in the output schema and is not fair value or an execution order.
The symbolic presentation plan has separate attractiveness and timing slots, rejects
a bare BUY label and forbids production delivery. REV52 generates no stock messages.

The internal union schema is wrapped in a strict `new_buyer_shadow` root object
for future provider requests. The repository's existing provider-wire projection
removes unsupported `uniqueItems` and shares reference enums; its dialect scanner
must pass before a request is returned. Local validation still enforces uniqueness
and every semantic predicate. This is offline dialect parity, not a live API test.

## Rollback and Next Gate

Leave the flag OFF. No database migration, historical output rewrite, production
prompt update or user-visible change is required. Local replay tests reachability,
not desired ticker labels. REV53 requires separate bounded B-only model-proof
authorization and sealed outputs before blind comparison; it is not automatic.
