# KR Sector Breadth Registry After Repair

Run-40 was replayed from the immutable packet without rewriting it.

```text
TOTAL_NUMERIC_PATHS        = 1,961
REGISTERED_PATHS           = 1,961
PROSE_ALLOWED              = 1,472
PROSE_DENIED               = 489
UNSUPPORTED                = 0

SECTOR_SUPPORTED_CANONICAL = 252
SECTOR_REGISTERED_SUPPORTED= 252
SECTOR_INTERNAL_ONLY       = 126
```

The four supported paths receive market/sector-specific labels and canonical count formatting. The
two limit paths are registered audit-only. A synthetic `experimental_component_count` remains
`UNSUPPORTED_BLOCKING`; numeric readiness correctly fails for that negative control.

