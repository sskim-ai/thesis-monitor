# 2026-09-04 KR V2 Compatibility Ordering

The ordering contract is:

1. Explicit V2 terminal accepted: use explicit V2.
2. Explicit V2 active and inside its command window: keep waiting.
3. Explicit V2 terminal failed, suppressed, timed out, or reached a real send
   deadline: compatibility or deterministic fallback may proceed.

The KR Pilot renderer remains a valid AI-assisted compatibility path, but it is
not explicit V2 and cannot satisfy an explicit-V2 natural proof.

The real KR TEST run delivered market `1` and explicit V2 stocks `8`. Pilot and
deterministic fallback counts were both `0`. The healthy backup returned
`SAFE_NOOP_PRIMARY_ACTIVE`.

No compatibility path was removed and no delivery deadline was changed.
