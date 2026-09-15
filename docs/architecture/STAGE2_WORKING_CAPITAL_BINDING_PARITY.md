# Stage-2 Working-Capital Binding Parity

## Decision

The working-capital checkpoint contract remains claim-local. A condition that
names a selected inventory, trade-receivables, or trade-payables metric must
bind the corresponding typed financial alias in that condition's paired refs.
A generic working-capital condition must bind at least one selected typed
working-capital alias. Narrative, unknown, and contextual refs may supplement
that evidence but cannot replace it.

Stage 1 and the monolithic path continue to receive the existing projection.
Stage 2 receives a separate projection containing only its owned fields:

```text
fundamental_new_buyer.confirmation_business_condition
fundamental_holder.business_invalidation_condition
```

The existing post-compose validator is unchanged. The projection and prompt
make the already-enforced contract visible before generation; they do not
inject refs, rewrite candidates, or assign a positive or negative direction to
working-capital movements.

## Optional Audit Readiness

Optional lexical coverage and semantic validity are independent. An audit with
zero observed optional claims and zero semantic violations is semantically
valid, has `coverage_status = NO_OBSERVED_CLAIMS`, and is nonblocking. An
observed invalid claim remains a hard semantic failure. Mandatory positive
coverage belongs only in deterministic fixtures built to exercise that form.

## Proof Boundary

The change requires a new full fictional proof because Stage-2 model context
and prompt semantics changed. If the 12-call proof passes all objective hard
gates, a new 18-call active-monitored same-packet shadow may run. Decision
variance remains diagnostic. Provider refresh, production mutation, delivery,
remote push, main merge, deployment, and monitoring resume remain prohibited.
