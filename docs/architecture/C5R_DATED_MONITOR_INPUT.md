# Dated monitor input: no new source-use authority

`app.services.dated_monitor_input` reads sealed historical indicator caches. It
does not load a Provider, recalculate indicators, issue an Owner, or invoke AI.
Its input record and role metadata must come from a separately verified seal,
not a newly constructed hash chosen to fit changed payloads.

The reader checks compressed byte hashes, canonical projection hashes, original
identity, canonical security, role/timeframe, adjusted basis, generation, aware
observation time, source hashes, sealed metadata and unchanged denial flags.
Symlinks are rejected. Latest cached values and field-specific history limits
remain separate from completed-session/current-price authority. Unadjusted
weekly data is a separate source reference, not another adjusted technical vote.

The preview requires the complete 22-by-4 role set and two market references.
Different source generations and market-local dates remain explicit. All
production, full Market Parent, model, technical-signal, Native, Strict and send
flags remain false. Nothing installs this optional preview into a live path.

## Official sources remain original

FRED supplies rates, real rates, credit, VIX, WTI, broad USD and liquidity series.
EIA supplies weekly inventories, production and utilization, not WTI prices.
ECOS requires original source-period proof for daily USDKRW display. Retrieval
time is not release time, and display eligibility is not directional authority.

KRX retains its original NIGHT close minus preceding eligible XKRX DAY close,
same product/contract/maturity, source hashes, provider crosscheck and finality.
The configured product remains KOSPI200 only. Same-contract D/W/M retains partial
period states. Class-C ohlcv_analyst cross-assets are not KRX official futures.

Source-only component passes, official publication replay, and optional night
eligibility do not create a full Market Parent. That still requires the original
same-run binding, whole stock/financial cohort, Class-C publications and original
consumer rights. A preview must not fabricate an economic packet or registry to
force `vnext_unified_judgment.build_bundle` acceptance.

Focused tests cover read-only custody and denial preservation. Existing sealed
indicator calculations and Source-only acquisition tests need not be repeated.
