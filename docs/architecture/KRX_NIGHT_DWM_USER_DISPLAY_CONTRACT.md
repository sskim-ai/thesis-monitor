# KRX Night D/W/M User Display Contract

Contract source: `krx-night-same-contract-dwm-v1`.

The user projection keeps contract identity separate from timeframe. A maturity such as `202609` identifies the selected near-month contract; daily, weekly, and monthly identify aggregation windows.

Daily displays open, close, gap percent, and return percent. Both percentages use the same validated preceding regular DAY close. Gap is `(night open / DAY close - 1) * 100`; return is `(night close / DAY close - 1) * 100`. Missing or invalid DAY baseline leaves both values unavailable.

Weekly and monthly display open, close, and return. Aggregation and the previous completed-period baseline use the exact selected contract only. No baseline produces `자료 부족`; an unfinished current period is labeled `진행중`. High and low remain canonical quality fields but are not user-visible.

No raw history, near-month selection, XKRX calendar rule, or return policy is changed by this projection.
