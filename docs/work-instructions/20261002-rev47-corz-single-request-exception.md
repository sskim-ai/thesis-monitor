# REV47 CORZ Request Exception

On 2026-10-02 the user approved the assistant's explicit request for exactly
one additional CORZ usa20590 historical-price query after the original response
was lost to a local capture error.

- Preserve the original failure report and all successful control responses.
- The additional CORZ query uses the same exact security/exchange and
  `base_dt=20261001`. No CORZ semantic retry or further discretionary request.
- Retain the new response before validation. Never repeat HUT, WRD, GOOGL or TSLA.
- Only after the five-control gate passes, execute the original REV47 Stage B
  and subsequent conditional source/model/KR/main sequence.
- Count the failed original CORZ capture as a real provider request. The accepted
  exception is an additional request, not a transport retry or an erased attempt.
- All other original REV47 boundaries remain unchanged.
