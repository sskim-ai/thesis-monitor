# Price Structure v3 Fib Family Dependency Audit

FIB_FAMILY_ENDPOINT_DEPENDENCY_REGISTRY = PASS

FIB_FAMILY_WITHOUT_ENDPOINT_DEPENDENCY = 0

| Family | Method | Endpoints | Formula | Version |
| --- | --- | --- | --- | --- |
| WAVE1_RETRACEMENT | WAVE1_RETRACEMENT | W0,W1 | W1-(W1-W0)*ratio | wave-fibonacci-deterministic-v3 |
| WAVE3_RETRACEMENT | WAVE3_RETRACEMENT | W2,W3 | W3-(W3-W2)*ratio | wave-fibonacci-deterministic-v3 |
| PRIMARY_CYCLE_RETRACEMENT | PRIMARY_CYCLE_RETRACEMENT | W0,W3 | W3-(W3-W0)*ratio | wave-fibonacci-deterministic-v3 |
| CURRENT_REBOUND | CURRENT_REBOUND | W3,W4 | W4+(W3-W4)*ratio | wave-fibonacci-deterministic-v3 |
| WAVE5_PROJECTION | WAVE1_MULTIPLE | W0,W1,W4 | W4+(W1-W0)*ratio | wave-fibonacci-deterministic-v3 |
| WAVE5_PROJECTION | WAVE3_MULTIPLE | W2,W3,W4 | W4+(W3-W2)*ratio | wave-fibonacci-deterministic-v3 |
| WAVE5_PROJECTION | SPAN03_MULTIPLE | W0,W3,W4 | W4+(W3-W0)*ratio | wave-fibonacci-deterministic-v3 |
