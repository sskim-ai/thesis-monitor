# Absolute Financial Direction Eligibility

R2B-R7 corrects source entitlement, not investment-policy thresholds.

`scripts/financial_direction_eligibility.py` is the shared typed owner used by
the current-source authority producer, derivative R2B authority, Core observation
builder, atomic-claim materializer and downstream capability validation.

Absolute current earnings amounts retain their original values, source metadata,
lineage and existing factual/context permissions. Their signs cannot grant
Overall, Holder, New Buyer execution-risk or Entry permissions. The derivative
records the explicit denial `ABSOLUTE_CURRENT_FINANCIAL_AMOUNT_NOT_DIRECTIONAL`.
No immutable source authority is rewritten and no permission is expanded.

Financial direction requires the existing validated comparative owner or the
existing explicit current/prior period compatibility contract. Generic period
compatibility still requires equal duration, period type, currency, unit, entity
and statement basis. The exact filing-occurrence comparative owner continues to
own qualified fiscal-calendar comparisons. No tolerance or comparison semantics
are introduced here. Missing prior values, incompatible bases and prohibited
source uses fail closed.

Core only emits directional propositions from eligible comparisons. Current
positive revenue, profit and losses do not emit directional propositions.
Atomic BULLISH/BEARISH claims require an eligible observed parent. NEUTRAL context
claims remain valid. This check uses typed source authority, not natural-language
keywords. Other source-ref/observation/ref-intersection rules remain enforced;
a mixed-reference claim does not gain permission just by attaching an unrelated
eligible ref.

When no authorized direction remains, the existing whole-decision UNKNOWN_LIMIT
contract applies: Overall/New Buyer/Holder OBSERVE; ratio/confidence null. It is
not a neutral investment opinion. The limitation catalog names comparable
financial evidence as the required next source, without inventing a prior value
or invalidating the current factual amount.

The only prompt correction restates this source rule; score bins, risk thresholds,
archetypes, valuation gates and Holder vocabulary are unchanged. Tests that used
current amounts as fixture directions now use explicit compatible comparisons;
the old absolute-amount assertions instead prove suppression. No skips are added.

`scripts/r2b_r7_offline_audit.py` verifies the sealed R6 ZIP and every manifest
member, recomputes all 22 modes, rejects invalid historical directional claims,
revalidates unaffected decisions, and captures deterministic corrected messages
under network/DB guards. It never dispatches models/providers or sends messages.
The new corpus is `POST_COMPARISON_SOURCE_POLICY_CORRECTED`, never relabeled as
the original blind result. R6 bytes remain immutable.

Calibration artifacts describe original R6 schemas, prompts, source constraints,
claims and choices. Independent labels are not inputs to the correction path.
Missing comparison artifacts must be reported as missing, never reconstructed
or claimed verified from the instruction's summary alone.
