# CORZ V2 Root-Cause Trace

`evidence → candidate → adjudication → accepted → selector → renderer → validator → delivery`

1. CORZ was eligible and present in the immutable packet.
2. The natural V2 generator entered `accepted_decision_v2_runtime.prepare_context`.
3. Local OHLCV fetch raised `httpcore.ConnectError`; no CORZ candidate was created.
4. Adjudication and packet-bound acceptance were never reached.
5. The separate AI prose candidate was rejected by validation.
6. Backend selected deterministic fallback.
7. The fallback payload was delivered once and matched archive/ledger text exactly.

Prior control: `HOLD`. Visible explicit decision: `NO`.

`CORZ_V2_STATUS = FALLBACK_RENDERER_ROUTE`
