# START HERE — M12DS-R6-R5

R6-R4 found a decisive warning:

- usa06012 row-local cur_prc is indeed the DAILY ROW close.
- But the same 2026-09-22 close changed for 19/22 symbols between two acquisition
  contexts while O/H/L stayed identical.
- Therefore latest-row availability != settled regular-close finality.
- Existing 08:05-era receipts lack per-symbol raw evidence.
- KR post-close sector authority remains PASS.

This task makes the FINAL Kiwoom ownership decision.

Use existing Kiwoom usa20100 as qualification-only cross-context:
- cur_prc = current price
- base_close_pric = 전일종가

At the real 08:05/10/15/20 window compare:
- usa06012 target row
- usa20100 current/base close
- later historical finalized usa06012 row

Determine whether ANY existing Kiwoom field owns the just-completed regular close at
production time.

If yes:
bind exact owner -> full fresh Market/Core/A/B -> 24/24 messages.

If no:
stop `US_REGULAR_CLOSE_EXTERNAL_SOURCE_REQUIRED`.
Do not keep looping on usa06012 finality.

No Alpha Vantage.
No new provider.
No scheduler enable.
No production send.

Transport for model calls only:
600s + up to 2 byte-identical transient retries.
