# Prospective Financial Monitoring Obligation

Contract: `prospective-financial-monitoring-obligation-v1`

## Purpose

This contract distinguishes a supported instruction to monitor a possible future financial condition from an assertion that the condition exists now. It extends the clause-local temporal classification established by `financial-framework-claim-span-v1` and preserves `prospective-financial-condition-nominalization-v1`.

## Eligibility

A local financial claim in `risk_context` is a `PROSPECTIVE_RISK_SCENARIO` only when all of the following hold:

1. The clause uses a bounded monitoring-obligation form such as `감시해야 한다`, `모니터링해야 한다`, `주시할 필요가 있다`, `추적해야 한다`, `점검해야 한다`, or an equivalent English obligation.
2. Framework-relevant configured weaken or invalidation evidence supports the monitored condition.
3. The local clause contains no current magnitude assertion.
4. The local clause contains no current fulfillment assertion.
5. The local clause contains no current numeric assertion.

The monitoring token alone is never sufficient.

## Precedence

Current evidence semantics take precedence over monitoring language. For example, `현재 순부채가 높아 감시해야 한다` remains a current directional claim, and `순부채 증가가 확인돼 주시해야 한다` remains a fulfilled current claim. A clause mixing a current magnitude with future monitoring remains current or fails closed when it cannot be split safely.

## Evidence Safety

Configured support must concern the same detected financial framework. Unrelated configured signals do not qualify. The contract does not alter net-debt completeness, current FCF safety, working-capital grounding, QTD/YTD rules, ADR basis rules, configured-signal field ownership, model prompts, schemas, or renderers.

## Failure Behavior

Unsupported or ambiguous monitoring prose remains `UNKNOWN_OR_AMBIGUOUS` and continues to require current evidence. The validator does not infer fulfillment from the model repeating a configured condition.
