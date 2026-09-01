# OHLC Cache Forensics

No bar cache exists in thesis-monitor or ohlcv-analyst; the only related cache is the US symbol list. No purge or cache-version bump was needed. Packet raw fingerprints now retain invalid rows, closing the lineage gap. `BROAD_CACHE_PURGE_WITHOUT_CAUSE = 0` and `OLD_INCOMPATIBLE_OHLC_CACHE_REUSED = 0`.
