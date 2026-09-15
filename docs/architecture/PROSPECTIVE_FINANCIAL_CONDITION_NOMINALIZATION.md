# Prospective Financial Condition Nominalization

## Status

- Contract: `prospective-financial-condition-nominalization-v1`
- Phase: M12AW
- Scope: post-model directional financial semantic validation
- Model prompt, schema, and evidence views: unchanged

## Problem

The financial claim-span contract already isolates a financial clause from mixed
`risk_context` prose. A remaining false rejection occurred when a configured
future condition used a nominal predicate instead of a verbal conditional:

```text
현금창출 저하와 순부채 증가의 동반 확인은 추가 하향 조건이다.
```

The local clause describes what would constitute a downside condition. It does
not assert that the condition has occurred.

## Decision

A local `risk_context` financial claim is classified as
`PROSPECTIVE_RISK_SCENARIO` when all of these conditions hold:

1. The clause has a bounded event/change/confirmation plus condition, criterion,
   or trigger shape.
2. A configured weaken or invalidation reference supports the same financial
   framework.
3. The local claim has no current-fulfillment or current-magnitude assertion.
4. The nominal form has no current numeric assertion.

Korean and English nominal forms are recognized separately. The word `조건`
or `condition` alone is never sufficient.

## Precedence

Current evidence requirements take precedence over nominal condition handling.
This includes:

- explicit current language such as `현재`, `이미`, or `now`;
- completed changes such as `증가했다`, `확인됐다`, or `has occurred`;
- a condition explicitly described as already fulfilled;
- current magnitude language such as high net debt; and
- current numeric assertions.

A narrowly bounded anaphoric suffix such as `현재 이미 충족됐다` is associated
with the immediately preceding nominal condition even when clause extraction
separates it after a connective. Unrelated current prose elsewhere in the field
does not taint the isolated financial clause.

## Fail-Closed Boundaries

- A nominal condition without framework-relevant configured support remains
  `UNKNOWN_OR_AMBIGUOUS` and requires current evidence.
- A configured reference for a different financial framework cannot authorize
  the claim.
- A current claim followed by a condition label remains current.
- A numeric nominal assertion remains a current numeric claim unless an existing
  explicit conditional contract independently applies.
- Existing FCF, business-delta, market-expectation, financial-sector, Stage-2,
  and configured-signal ownership contracts are unchanged.

## Examples

Supported with matching configured evidence:

```text
순부채 증가 확인이 하향 재평가 조건이다.
순부채 증가의 발생은 무효화 조건이다.
confirmation of worsening net debt is a reevaluation trigger.
```

Current or fail-closed:

```text
순부채 증가가 확인됐다.
순부채가 증가했고 이는 하향 조건이다.
현재 순부채가 높다는 점이 하향 조건이다.
순부채 증가는 하향 조건이다.  # no configured support
```
