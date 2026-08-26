# User Reference Engine Availability

The bounded-repair ZIP contains only the exact work instruction. It does not contain
`codex_stock_wave_engine(1).zip`, and no sanitized reference implementation exists under
`docs/reference/user-wave-engine/`.

```text
USER_REFERENCE_ENGINE_AVAILABLE = NO
REFERENCE_METHOD_COMPARISON = NOT_OBSERVED
severity = P2
```

The supplied endpoint example is retained only as a benchmark. The repaired generator independently
surfaces the 2023 W0 candidate and does not force a byte-level or endpoint match.
