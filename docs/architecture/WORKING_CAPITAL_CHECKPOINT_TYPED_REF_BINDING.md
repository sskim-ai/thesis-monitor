# Working-Capital Checkpoint Typed-Ref Binding

## Contract

`working-capital-checkpoint-typed-ref-binding-v1` preserves claim-local financial
grounding. A directional checkpoint claim that names a selected inventory,
trade-receivables, or trade-payables metric must cite that metric's selected
`TYPED_FINANCIAL` alias in the same claim. A generic working-capital checkpoint
must cite at least one selected working-capital typed alias.

Narrative and sector-context references may supplement the typed evidence. They
cannot substitute for it, and a typed reference attached to another output field
does not ground the checkpoint claim.

## Model-Facing View

`working-capital-checkpoint-binding-view-v1` projects only selected working-capital
facts and their model-visible aliases. It records canonical identities internally
for post-model audit but keeps model instructions focused on aliases. The same
view is attached to monolithic and Stage-1 contexts. Its model-visible checkpoint
list excludes the two Stage-2-owned stance conditions so their names cannot leak
into Stage 1; hard validation still covers the full existing checkpoint surface.

The existing checkpoint paths remain unchanged:

- `core_investment_judgment`
- `dominant_evidence`
- `risk_context`
- `business_reevaluation_up`
- `business_reevaluation_down`
- `fundamental_new_buyer.confirmation_business_condition`
- `fundamental_holder.business_invalidation_condition`
- `buy_drivers`
- `sell_drivers`

## Enforcement Choice

Conditional JSON Schema enforcement is not used. The Codex Structured Output
dialect does not expose a local, hosted-equivalent capability probe that can prove
support for claim-text-dependent `if` / `then` / `contains` constraints without a
model call. The portable architecture is therefore:

1. deterministic binding view,
2. one generic model instruction shared by monolithic and Stage 1,
3. existing hard financial grounding validation,
4. an additional metric-specific, claim-local typed-ref audit.

The model-facing hooks are installed during deterministic preflight so the new
generation freezes the binding view and prompt. The additional hard audit hook
starts only for that new proof; it does not retroactively reclassify upstream
historical replay gates under a contract they did not use.

This does not mutate generated candidates and does not assign positive or negative
direction to working-capital balances.

## Safety Boundary

The contract does not change the public schema, Stage-2 schema, renderer,
production runtime, stored assessment, monitoring schedule, or delivery path.
Unsupported working-capital metrics are not synthesized, and `AR` / `AP` are not
treated as lexical cues without structural evidence.
