# Decision Change Condition Rendering

Contract: `decision-aware-change-condition-v1`

Upgrade and downgrade conditions are evidence-backed reassessment triggers, not automatic trade
rules. They describe when the current analytical decision should be reviewed.

The renderer validates the current accepted decision before prose is exposed:

- BUY cannot be raised to BUY.
- HOLD cannot be lowered to HOLD.
- SELL cannot be lowered to SELL.
- A same-decision condition must refer to confidence, timing, or risk rather than a false
  top-level transition.

Legacy wording is normalized without changing the accepted decision or evidence references. For
example, `보유 판단으로 낮추고` under an accepted HOLD becomes `HOLD 확신을 낮추고`. Genuine
BUY/HOLD/SELL transitions remain explicit only when they point to a different top-level decision.

The production renderer accepts only a ready `accepted_decision_plan`; candidate-only wording and
shadow labels are not eligible for delivery.
