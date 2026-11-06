# C13: complete gate visibility, not current runtime admission

Baseline: PR17, `3e4ec8a47478ceac7cda853788f2f751207dfb74`.
This offline audit adds focused boundary tests and review evidence only.
Application code and owner permissions are unchanged.

## Reproduced boundaries

- The original RequestPlan validator already requires each response-binding
  parent to precede its child, rejects missing parents/cycles/scope drift, and
  the original dispatcher resolves only verified same-plan parent receipts.
- On a TEST_ONLY copy of the exact retained KR graph, all 42 captured requests
  replay in parent-before-child order. The existing original Market drain closes
  seven remaining continuation slots through `skip_unselected`, without HTTP.
  Deliberately resolving continuation16 before the continuation15 no-I/O receipt
  reproduces the correct missing-parent denial. This is not proof of the old
  live caller's exact execution sequence; that original stack/state is absent.
- C12 US close outcomes replay unchanged: 13 qualified and IBM quality denied
  (`LOW_GT_CLOSE`). C10R and C12 IBM use the same target date and original
  signed-string field parser; the later literal response has an OHLC conflict.
  No mapping defect or provider-side cause is proven. Do not repair it with a
  uniform scale, adjacent row, old quote or last-price substitution.
- A revoked/serialized pending handle cannot issue a current price. A PENDING
  monitoring request remains excluded from production. Historical JSON cannot
  construct Technical or Native capability objects. One subject's scoped
  revocation does not revoke other research subjects.
- The November 4 Market target cannot satisfy November 5. Optional night or
  macro unavailability may be valid only through original bound availability
  and denial ownership; these fields are not made universally mandatory values.
- The Sol execution profile is distinct from the legacy ASTRA_ADJ economic
  policy label. The current Stage path binds the actual Sol profile; an older
  daily signature's Astra metadata is not a Sol execution receipt or grant.

## Why no application patch

The highest-impact blockers are legitimate PENDING/ACTIVE separation, expired
current capabilities, insufficient full-count history, source-quality denial,
financial occurrence/purpose gaps, per-security valuation basis, Market/PIT
time mismatch and an unsupported high model route. Existing tests reproduce
proper rejection, not a presently demonstrated common implementation defect.
Changing the original gates would manufacture authority. No speculative
dispatcher refactor, new adapter or ticker exception was added.

## Readiness levels

24 subjects are covered by the offline graph: 22 stocks and two Markets.
22 retained stock packets pass a recomputed field-state availability projection;
their prior 22 full-input and 14 changed-consumer Cold proofs remain inherited,
not newly issued rights. Two representative original consumers are freshly
replayed. All of these are dated/research-only. New model-ready input, current
economic admission and Strict READY remain zero. Market Parents remain 0/2,
Valuation Owners 0/22, and C12 completed closes remain 13/14 for 2026-11-05.

The next executable full22 graph is BLOCKED_UNRESOLVED. Exact retained Market
DAG templates and their original physical maxima are recorded separately from
unresolved current identities, document selections, PIT, availability and use
policy. A candidate per-provider estimate is not a newly frozen execution plan.
No aggregate live budget or preapproved source scope is invented.

Financial HTTP, operating registration SELECT, DB writes, investment model
calls, sends, orders, service/scheduler changes and deletion are all zero.
The original high STOP is preserved; medium remains untested, not unsupported.
No next revision is started automatically.
