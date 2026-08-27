# Track A — KR Daily 1200 Provider Capability Audit

## Objective

Prove whether the current KR daily OHLCV provider can retrieve history older than its 1000-row per-request cap.

Audit:

```text
pagination
cursor
offset
before/end-date
date windows
existing cache history
```

Safe probe controls:

```text
000660
005930
010120
```

Do not guess.

## Required result

Exactly one:

```text
EXACT_1200_SUPPORTED_BY_PAGINATION
EXACT_1200_SUPPORTED_BY_DATE_WINDOW
EXACT_1200_SUPPORTED_BY_EXISTING_CACHE_LAYER
PROVIDER_HARD_LIMIT_NO_OLDER_WINDOW
PROVIDER_SUPPORT_UNVERIFIED
```

`PROVIDER_SUPPORT_UNVERIFIED` is not PASS.

No provider switch and no synthetic history.
