# Korean Price-Token Boundary Root Cause

The prior pattern searched raw `주가`/`종가` substrings without a left Hangul boundary. It therefore read `수주가 ... 회복` as stock-price `주가 ... 회복`. The repaired detector recognizes a finite price-subject vocabulary only at string start or after a non-Hangul delimiter, then requires a nearby technical action. No ticker-specific exception or negative-word-only bypass exists.

Boundary detector: `PASS`. Ticker-specific exceptions: `0`.
