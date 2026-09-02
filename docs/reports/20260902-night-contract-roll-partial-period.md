# Night Contract-Roll Partial Period

When the selected contract begins after the XKRX period start and another contract exists earlier in that period, status is `SAME_CONTRACT_PARTIAL_PERIOD`. It is never labeled full or FINAL. Missing elapsed constituents produce `PARTIAL_SAFE`; future expected sessions produce `IN_PROGRESS` rather than missing-data errors.
