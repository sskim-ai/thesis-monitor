# Night Futures Session Date Contract

Contract: `night-futures-session-date-v2`

KRX night-futures `BAS_DD` identifies the completed night-session end date. The UI session date is
the preceding KRX regular business date. Mapping uses the XKRX business calendar and a 06:00 KST
completion boundary; weekends, Korean holidays, year boundaries, and observations before finality
are handled by the same calendar rule.

US regular-session date is retained as explicit packet metadata but does not hard-code the KRX
date. A row becomes ready only when the provider returns the mapped completed `BAS_DD` and all
existing validation/finality checks pass. A stale provider date remains
`SOURCE_LIMITATION_SAFE`; the renderer must not force it ready.

The contract changes date semantics only. Instrument mapping, values, source hierarchy, message
format, and non-night market data are unchanged.
