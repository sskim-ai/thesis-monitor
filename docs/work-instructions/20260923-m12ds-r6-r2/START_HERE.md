# START HERE — M12DS-R6-R2

R6-R1-REV1 correctly stopped before inference.

What is now proven:

- US raw current bars exist for 21/22 symbols.
- The latest bar fails only because settled regular-session close/finality is not owned.
- XLC separately hit HTTP 502 / upstream token 429.
- KR sector parser works; the 12:53 KST response is 09/23 intraday and cannot own the
  09/22 completed sector session.
- KR stock adjusted_intraday basis is fixed and validated 8/8.
- Full pytest 5291 PASS / 63 existing skips.
- model calls 0 / production mutations 0.

Next:

1. resolve actual production US/KR market-message cutoff from scheduler/config;
2. bind US latest completed session to an existing approved settled-close route;
3. bind KR sector source according to real production timing:
   - post-close current-only route with closed-session parity proof, or
   - approved historical target-date sector route if execution can be pre-close;
4. no new external provider without user approval;
5. preserve price basis, night D/W/M, support/resistance;
6. show lagged WTI only as clearly dated latest-available information, never as current
   direction evidence;
7. require full information gate;
8. fresh Market/Core/A/B;
9. exact 24/24 final message capture.

Transport:
- 600s per attempt
- first + up to 2 byte-identical transient retries
- max 3 attempts total
- no semantic/schema/source/security retry

No main merge in this task.
