# Fictional Case FCF Prospective Scope

## Status

M12AU aligns the `FIC-FIN-01` proof-harness assertion with the repository's
claim-local financial semantic validator. It is local-only and does not change
model prompts, model schemas, evidence views, production behavior, or monitoring
schedules.

## Root Cause

The original M12 fixture rejected any `FCF` or `잉여현금흐름` token anywhere in
the `FIC-FIN-01` candidate. That was a conservative guard against labeling the
fixture's `ocf_less_ppe_capex` cash-conversion proxy as FCF, but it ignored the
claim field, sibling evidence references, temporal role, and negation.

After M12AN and M12AR, `directional-financial-semantic-validator-v1` owns those
semantics. It classifies each claim independently and distinguishes:

- current affirmative or numeric FCF attribution;
- PPE proxy-as-FCF attribution;
- unsupported current FCF claims;
- prospective reevaluation, confirmation, and invalidation conditions;
- explicit not-FCF disclaimers.

The legacy ticker-specific global token assertion was therefore a duplicated,
less precise semantic engine.

## Decision

M12AU selects Option B: retire only the `FIC-FIN-01` global FCF token assertion.
All other fixture-specific checks remain intact. The generic claim-local
financial validator is the single authoritative FCF semantic engine.

The following behavior is required:

- a configured future FCF condition in `business_reevaluation_down` passes;
- a configured holder invalidation condition referring to FCF passes;
- an explicit not-FCF disclaimer bound to the PPE proxy passes;
- a current claim that calls the PPE proxy FCF hard-fails;
- an unsupported current FCF claim hard-fails;
- configured-only refs remain barred from current drivers and material anchors;
- current net-debt claims still require complete current net-debt evidence.

## Proof Boundary

The repair is confined to the offline fictional case checker. M12AU requires a
new 12-call, 8-subject fictional proof because M12AT's model-facing configured
signal field fencing completed only one call. If those hard gates pass, M12AU
runs a new 18-call same-packet shadow over the active monitored universe.

No prior generation is continued or stitched. No selective rerun, wrapper
retry, provider refresh, production send, database mutation, scheduler mutation,
remote push, main merge, deployment, or automatic monitoring resume is allowed.
