# OHLCV Cache Versioning

The production Thesis Monitor OHLCV client and the Kiwoom chart provider do not persist a bar cache.
The provider has only a US symbol-list cache, which cannot alter OHLC values. Packet-owned bars are
immutable run evidence rather than a reusable provider cache.

Consequently the 2026-09-01 malformed rows were not inserted by cache serialization and no cache
purge or version bump is required. A future normalized-bar cache must key provider, security,
timeframe, session, adjustment mode, schema version, and normalization contract. Changing field or
adjustment semantics must change that version; incompatible entries must never be reused silently.

