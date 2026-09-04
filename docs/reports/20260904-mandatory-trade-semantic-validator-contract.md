# Mandatory Trade Semantic Validator Contract

Mandatory buy, sell, reduce, and stop-loss directives remain blocked. Negated, comparative, and reassessment wording is allowed only when it does not issue an order.

| Check | Result |
| --- | --- |
| Nonmandatory regression cases | `5/5 PASS` |
| Mandatory directive cases | `8/8 BLOCKED` |
| Threshold weakening | `0` |
| Judgment logic change | `0` |
