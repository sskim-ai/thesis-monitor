# Track B — OHLC Normalization / Adjustment / Integrity Repair

Audit and repair only proven defects in:
- field mapping
- adjusted/unadjusted basis
- split/reverse-split handling
- W/M aggregation
- timezone/session normalization
- numeric serialization

Never:
- clip high/low
- swap fields heuristically
- interpolate OHLC
- copy previous values
- silently drop current bad bars and call them current

Preserve INVALID fail-closed.

Recompute all technical features only from validated repaired bars.
