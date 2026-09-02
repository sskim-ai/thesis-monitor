# KRX Night D/W/M Aggregation

Contract: `krx-night-same-contract-dwm-v1`.

The resolver selects the nearest non-expired maturity from actual FINAL bars. Daily, weekly, and monthly frames then use that exact contract only. Weekly bars use XKRX Monday-to-Sunday sessions; monthly bars use XKRX sessions in the calendar month. The current incomplete week/month is `IN_PROGRESS`. A roll that begins after the period start is `SAME_CONTRACT_PARTIAL_PERIOD`; contracts are never spliced.

Returns use the immediately preceding completed same-contract week/month close only. Without a complete baseline, the bar remains usable but return is unavailable.
