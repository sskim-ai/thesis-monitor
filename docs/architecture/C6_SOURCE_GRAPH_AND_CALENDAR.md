# Retained source graph and calendar-qualified indicator references

## Mandatory acquisition versus optional numeric availability

The original acquisition inventory marks the five publication Class-C roles
optional. Their value is optional; the original record/version and replayed
value-or-denial path is not replaced by an unbound empty fact. Required stock
chart attempts and run-fresh night acquisition cannot use optional denials.

`project_retained_publications` maps sealed publication rows into an isolated
in-memory MacroObservation table and invokes the original Class-C owners. It
checks the retained run, query/retrieval times, raw hashes and original receipts.
Derived memory IDs are not operating DB record IDs. The result is explicitly
historical and never qualifies a new production seed.

The canonical publication projection now preserves an explicit version-bound
denial when the original owner returns no eligible values. Empty values do not
permit altered role, version, eligible flag or projection hash. A captured
inventory with no Fed/cross-asset records establishes absence only within that
inventory, not a claim about an unqueried production registry.

`validate_fresh_context_generation` exposes the existing composition guard for
early offline diagnosis. The original composition calls that same guard. Old
Market components, stock captures and official publication runs must not be
joined by changing IDs, cutoff timestamps or hashes.

## Reuse the existing official dated calendar

Historical indicator segmentation previously used the uncorrected exchange
calendar. The existing opt-in dated-calendar policy already contains the
officially evidenced closures missing from that library. Passing this policy
to the KR daily segmentation fixes artificial gaps without inventing bars or
changing the original indicator formulas.

The new option is KR-daily-only, default disabled. Its derived cache contract
is `historical-original-indicator-projection-v2`; cache identity includes the
calendar policy and the projection binds the existing official table hash.
Original v1 caches remain immutable. Weekly/monthly labels and other markets
are unchanged. Latest snapshot/reference values still do not establish a
completed regular close, current timing, valuation, Native or send authority.

RETURN_20D/RETURN_60D on weekly or monthly data refer to 20/60 bars of that
timeframe. The original DRAWDOWN_52W implementation uses a 252-bar rolling
window; its name alone must not be translated into 52 calendar weeks for every
timeframe. Reference-period units are not authenticated price currencies.
