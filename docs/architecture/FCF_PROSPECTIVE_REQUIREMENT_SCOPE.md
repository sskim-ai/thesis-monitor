# FCF Prospective Requirement Scope

## Contract

M12BG adds `fcf-prospective-requirement-v1` to the post-model financial
semantic validator. It does not change prompts, model schemas, evidence
projection, working-capital views, the final user schema, or production
delivery.

The contract separates two identities that previously collapsed together:

1. The field semantic role, such as current thesis or market-expectation
   context.
2. The clause-local temporal and polarity role of an FCF mention.

A current-context field can therefore contain a future proof requirement
without claiming that FCF has already improved.

## Prospective Requirements

Bounded Korean and English modality families classify as
`PROSPECTIVE_VERIFICATION_REQUIREMENT`. Examples include an outcome that
must translate into FCF, FCF improvement that must be demonstrated, and FCF
proof that is still needed.

These clauses do not require a current safe FCF fact solely because they are
stored in a current-context field. They remain subject to all other grounding,
ownership, expectation-independence, and configured-signal validators.

## Hard Precedence

The requirement classification never overrides a current numeric claim,
current magnitude or state, or affirmative current fulfillment. Claims that
FCF is positive, negative, weak, insufficient, improved, deteriorated, or a
specific amount still require safe current FCF evidence.

The only safe current FCF evidence families remain `free_cash_flow` and
`reported_free_cash_flow`. OCF, OCF less PPE, cash generation, and generic
cash-flow language do not become FCF evidence.

## Directional Eligibility

Prospective requirement language is contextual, not current directional
evidence. It cannot independently serve as a buy driver, sell driver, or
dominant evidence. Material-anchor reference ownership remains enforced by
the existing configured-signal and anchor validators. A core judgment may
state that further FCF proof is needed, provided it does not assert current
FCF or use the requirement as the current directional anchor.

## Proof Policy

The exact immutable M12BF context-01 output is re-audited without candidate
editing. The complete M12BD 24-row Stage-1 and 24-row Stage-2 proof is also
re-audited under the repaired classifier. M12BD can be reused with zero new
fictional calls only when every model-facing semantic hash is unchanged.

A new monitored shadow generation is mandatory. Any objective hard semantic
failure stops the generation with no selective rerun, candidate edit, or
post-generation hotfix.

## Production Firewall

M12BG is local and shadow-only. Provider fetches, database mutations,
monitoring changes, notifications, production sends, remote pushes, main
merges, and deployments are prohibited. Paused schedules remain paused.
