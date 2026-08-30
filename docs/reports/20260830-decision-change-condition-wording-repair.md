# Decision Change Condition Wording Repair

Contract: `decision-aware-change-condition-v1`

The old renderer could preserve a phrase such as `보유 판단으로 낮추고` under an already accepted
HOLD decision. That is a false HOLD-to-HOLD downgrade. Normalization now uses confidence, timing,
or risk language for same-decision movement and the validator rejects BUY-to-BUY upgrades,
HOLD-to-HOLD downgrades, and SELL-to-SELL downgrades.

The production renderer consumes only a ready accepted plan. It does not expose candidate labels,
shadow labels, automatic trade rules, or rejected candidate conditions.

Gates:

- `SELF_TRANSITION_WORDING = 0`
- `CHANGE_CONDITION_AS_AUTOMATIC_TRADE_RULE = 0`
- `WORDING_REPAIR_CHANGED_ACCEPTED_DECISION = 0`
