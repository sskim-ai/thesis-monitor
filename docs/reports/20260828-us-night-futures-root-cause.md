# US Night Futures Root Cause

The run-43 packet retained the canonical night-futures sidecar, but no current overnight
directional row was eligible. The prior concise US message had no dedicated deterministic section.
The new renderer consumes the existing sidecar and omits the whole section when no safe row exists.

`EMPTY_NIGHT_FUTURES_SECTION = 0`
`PRIOR_NIGHT_FUTURES_AS_CURRENT = 0`
`RUN43_RESULT = OMITTED_SAFE`
