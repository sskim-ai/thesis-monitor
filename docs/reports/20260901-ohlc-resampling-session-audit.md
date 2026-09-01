# OHLC Resampling and Session Audit

Daily, weekly, and monthly rows are provider-native; thesis-monitor does not resample these bars. Invalid provider constituents are not dropped to create a valid aggregate. HUT's dated daily and weekly rows both carry the mutable current close, so both remain invalid. `AGGREGATION_IGNORES_INVALID_CONSTITUENT = 0`, `CROSS_SESSION_OHLC_AGGREGATION = 0`, and `IN_PROGRESS_BAR_AS_COMPLETED_TECHNICAL = 0`.
