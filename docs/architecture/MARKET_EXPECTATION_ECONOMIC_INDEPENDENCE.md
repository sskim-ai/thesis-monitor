# Market Expectation Economic Independence

## Contract

`market-expectation-evidence-view-v1` is the canonical pre-model and
post-model contract for deciding where market-expectation evidence may be
used. Source category is provenance, not proof that an expectation is an
economically independent directional axis.

The view is built per ticker from the owned evidence packet, the frozen alias
catalog, and optional structured dependency metadata. It is attached to the
model context before generation and its exact hash is reused by validation.
No classifier derives independence from English or Korean wording.

## Roles

- `INDEPENDENT_DIRECTIONAL_SUPPORT`: a distinct, structured current basis is
  present. The ref may be used in material anchors, dominant evidence,
  drivers, and expectation context.
- `CONDITIONAL_CONTEXT_ONLY`: the expectation depends on an unresolved
  issuer-side condition. It may provide expectation/asymmetry context and may
  appear as an `OTHER_EVIDENCE` sell driver, but it cannot be a material anchor
  or independent dominant evidence.
- `ALREADY_REFLECTED_OR_COUNTERWEIGHT`: structured metadata says the condition
  is already reflected or is a counterweight. It remains context only.
- `INDEPENDENCE_UNKNOWN`: no safe structured independence basis exists. It is
  conservatively context only and is not treated as negative evidence.
- `NOT_MARKET_EXPECTATION`: all other evidence. Existing ownership and
  directional contracts continue to govern it.

## Enforcement

The Stage-1 and monolithic schemas are constrained per ticker. Only
anchor-eligible aliases may appear in `material_directional_anchor_basis` or
`dominant_evidence.evidence_refs`. Other claim fields retain the full alias
catalog, preserving legitimate context use.

Post-model validation consumes the same frozen view and rejects:

- context-only expectations used as material anchors;
- context-only expectations used as dominant evidence;
- context-only expectations used as a classified sell driver other than
  `OTHER_EVIDENCE`;
- any pre-model/post-model view identity mismatch.

The validator does not change directional balances, assign weights, parse
prose to infer dependency, or create ticker-specific policy.

## FIC-FIN-05

The fictional fixture explicitly links its market-expectation ref to the
unresolved refinancing-condition ref. This makes the expectation
`CONDITIONAL_CONTEXT_ONLY`. A SELL 6.0 remains valid when complete debt, thin
cash, and operating evidence carry the decision and the expectation is used
only as context or `OTHER_EVIDENCE`. The stopped M12AO candidate remains
invalid because the same conditional expectation was also selected as a
material anchor and dominant evidence.

## Active Universe

The frozen active packet set contains market-expectation evidence but no
dedicated structured independence/dependency field. Those expectations are
therefore `INDEPENDENCE_UNKNOWN` for M12AP. This is a metadata limitation, not
negative evidence, and it is reported separately from model or validator
failure.

## Boundaries

M12AP changes internal model context and per-call schema only. It does not
change the public schema, production renderer, scheduled monitoring,
assessment persistence, notifications, or deployment state. Business-delta,
PPE-only cash-conversion, financial temporal scope, Stage-2 language, and
two-stage ownership contracts remain authoritative and unchanged.
