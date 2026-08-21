# Night-Futures Session Regression

`night-futures-session-basis-v1` is unchanged. Regression tests preserve:

- expected NIGHT date from its 06:00 completion date;
- holiday/weekend traversal to the immediately preceding eligible XKRX DAY;
- same product, contract code, and maturity;
- no same-`BAS_DD` DAY substitution;
- deterministic NIGHT minus preceding-DAY change;
- provider-reported change cross-check;
- source-record and payload-SHA provenance;
- stale older pair suppression when the expected session is absent.

Focused night/session/morning tests: `61 passed`. Full suite: `1337 passed, 1 warning`. No pairing,
retry, deadline, readiness, or production rendering assertion changed to accommodate telemetry.
