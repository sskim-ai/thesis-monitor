# 11 Wmt Price Provider Resilience Audit

| Field | Value |
| --- | --- |
| classification | ["SINGLE_PROVIDER_OUTAGE", "FALLBACK_NOT_CONFIGURED"] |
| contract | wmt-price-provider-resilience-audit-v1 |
| packet_created | True |
| provider | {"adjusted_request_count": 90, "cache_behavior": "no successful bars available for cache reuse", "canonical_provider": "kiwoom", "fallback_behavior": "no second canonical OHLCV provider configured", "http_status_counts": {"200": 0, "502": 120}, "request_observation_count": 120, "retry_layers": {"provider": "429-only retry; non-429 HTTP errors fail closed", "thesis_monitor": "up to monitor_retry_attempts, capped at 5"}, "unadjusted_request_count": 30, "upstream_endpoint": "/api/us/chart", "wrapper_endpoint": "/ohlcv"} |
| status | PASS |

Machine proof: `proofs/11-wmt-price-provider-resilience-audit.json`.
