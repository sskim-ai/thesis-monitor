# Confirmation Validator Semantic Repair

The prior guard rejected isolated words such as `지지`, `가격`, and `support`. The repair detects narrow stock-price phrase combinations instead, while preserving the global numeric-prose prohibition and evidence ownership checks. Judgment ordering, balance thresholds, HOLD lean, buyer/holder stance, and renderer structure are unchanged.

Generic business-word false positives: `1`. Technical ownership leaks: `0`.

The fresh run exposed a remaining Korean token-boundary defect: `수주가 ... 현금흐름이 회복` contains the substring `주가 ... 회복`, so the detector rejected business order/cash-flow language. The candidate was not changed or rerun.
