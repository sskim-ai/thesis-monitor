# NYSE Breadth Source Audit

`NYSE_BREADTH_SOURCE = UNAVAILABLE`

NasdaqTrader `otherlisted.txt` documents exchange code `N = NYSE`, but it is listing-identity
metadata rather than breadth. Source definitions: https://nasdaqtrader.com/Trader.aspx?id=SymbolDirDefs.

No free official structured NYSE breadth source passed the v1 audit, and the repository does not
have complete same-session EOD coverage for every deterministically eligible NYSE security.
Therefore no sampled universe, extrapolation, or custom NYSE breadth is promoted.
