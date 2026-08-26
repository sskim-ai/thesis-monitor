# Fib Family Endpoint Dependency

## Contract

`fib-family-endpoint-dependency-v1` is the machine-readable registry for every implemented v3
Fibonacci formula.

| Family | Method | Required endpoints |
| --- | --- | --- |
| WAVE1_RETRACEMENT | WAVE1_RETRACEMENT | W0, W1 |
| WAVE3_RETRACEMENT | WAVE3_RETRACEMENT | W2, W3 |
| PRIMARY_CYCLE_RETRACEMENT | PRIMARY_CYCLE_RETRACEMENT | W0, W3 |
| CURRENT_REBOUND | CURRENT_REBOUND | W3, W4 |
| WAVE5_PROJECTION | WAVE1_MULTIPLE | W0, W1, W4 |
| WAVE5_PROJECTION | WAVE3_MULTIPLE | W2, W3, W4 |
| WAVE5_PROJECTION | SPAN03_MULTIPLE | W0, W3, W4 |

Each registry entry binds the family, method, formula, wave-state applicability, source degree
role, and deterministic calculation version. Every generated Fibonacci reference echoes the
required endpoint labels and dependency contract.

Unknown families, formula drift, calculation-version drift, and endpoint mismatch fail closed.
