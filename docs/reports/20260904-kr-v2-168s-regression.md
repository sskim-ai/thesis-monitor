# 2026-09-04 KR V2 168-Second Regression

## Deterministic clock proof

For a command starting at monotonic time `1000.0` with timeout `1800`:

- at `1168.3`, `1632` seconds remain
- at `2799.9`, `1` second remains
- at `2800.0`, the deadline is terminal

No outer interruption is authorized at the historical `168.3` second boundary.

## Real recurrence proof

The final KR TEST generation ran from `2026-09-04T13:09:30.487155Z` to
`2026-09-04T13:27:43.478741Z`, or `1092.99` seconds. It crossed the forensic
boundary by more than 15 minutes, maintained 19 claim renewals, accepted all
eight stock decisions, and delivered exactly once.

`PREMATURE_CHILD_INTERRUPT = 0`

`ACTIVE_CHILD_NO_CANDIDATE_TREATED_AS_FAILURE = 0`
