# Track A — Night Futures Friday→Saturday Session/Acquisition Audit

Use the 2026-08-29 morning evidence:

```text
expected canonical session = 2026-08-29
08:06 / 08:10 / 08:15 / 08:20
→ source returned 2026-08-28 only
```

Capture raw source responses and prove whether the date is start-date, end-date, business-date, or publication-date.

Audit ordinary weekday transitions plus Friday→Saturday.

Root-cause must be one of:
upstream non-publication, provider acquisition loss, source-date convention mismatch, normalizer bug, cache delay, other/unknown.

Do not force renderer visibility.
