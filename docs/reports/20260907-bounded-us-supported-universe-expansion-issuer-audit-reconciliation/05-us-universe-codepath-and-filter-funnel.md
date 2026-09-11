# 05-us-universe-codepath-and-filter-funnel

| Field | Value |
| --- | --- |
| old_codepath | scripts/unseen_source_assembly_coldstart.py::_us_identities -> AST literal US_EXCHANGE_BY_TICKER |
| provider_capability_codepath | ohlcv-analyst OhlcvService._resolve_symbol -> KiwoomProvider.resolve_us_symbol -> official provider ND/NY/NA stock lists |
| raw_listing_rows | 13188 |
| identity_resolution_counts | {"IDENTITY_RESOLVED": 7155, "IDENTITY_UNRESOLVED": 6033} |
| routing_status_counts | {"ROUTING_CANDIDATE": 5095, "ROUTING_SUPPORTED": 52, "ROUTING_UNSUPPORTED": 8041} |
| eligibility_reason_counts | 14 keys; sha256=fc43c2dd3ea0c1698f065e6205c35c772b502cf9dd4b743103b4131bdfa9cee9 |
| route_candidate_issuer_count | 5110 |
| historical_static_discovery_registry_was_bottleneck | 1 |
| actual_generic_provider_route_already_existed | 1 |
| status | PASS |
