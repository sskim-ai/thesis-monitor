# Consumer-Scope Negative Controls

Six focused controls pass:

1. Unsupported `ARCHIVE_ONLY` fact does not block `STOCK_V2`.
2. Unsupported `NIGHT_FUTURES_MODULE` fact does not block `STOCK_V2`.
3. Hidden unsupported `STOCK_V2` fact still fails readiness.
4. Visible `MARKET_RENDERER`-only fact is excluded from stock readiness but fails renderer
   readiness.
5. Unclassified unsupported legacy fact remains a strict failure.
6. V2 evidence includes the hidden stock fact and excludes the archival night fact.

`TRACK_A_CONSUMER_SCOPE_TESTS = PASS`

