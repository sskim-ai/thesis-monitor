# Night Date-Convention Next Scope

`NEXT_REPAIR_CLASS = MORE_EVIDENCE_REQUIRED`

No production repair is justified by the current proof. The bounded follow-up is:

1. Re-query the same official service for `BAS_DD=20260902` only after publication evidence indicates rows exist.
2. Compare KOSPI200 202609 NIGHT exact OHLC to 1061.00/1061.40/1031.30/1040.50 and repeat the KOSDAQ150 control.
3. If exact parity is established, design a separate `provider_trading_date`, `session_start_date`, `session_end_date`, and `user_display_session_date` contract in a new repair task.
4. If the row exists but differs, investigate session-bar and contract/adjustment definitions before changing code.

Until then, preserve current fail-closed behavior. Do not patch history, overload `reference_date`, or infer the missing row from Kiwoom percentages.

`CODE_CHANGE_DURING_DATE_PROOF = 0`

`MAIN_MERGE = 0`
