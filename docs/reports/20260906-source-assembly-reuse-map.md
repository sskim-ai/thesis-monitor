# Source Assembly Reuse Map

| Gate | Value |
| --- | --- |
| components | [{"adapter": "generic CSV/AST inventory adapter", "component": "ohlcv_analyst SymbolResolver registries", "input": "ticker/security identity", "output": "canonical market/exchange/name/sector identity", "reuse": "UNCHANGED_READ_ONLY_SOURCE"}, {"adapter": "none", "component": "OhlcvClient.fetch_price_context", "input": "ticker/as_of", "output": "price/chart/packet-owned technical context", "reuse": "UNCHANGED_NO_DB_SESSION"}, {"adapter": "cold-start packet envelope", "component": "financial/numeric/security basis validators", "input": "canonical fact catalog", "output": "DecisionEvidencePacket", "reuse": "UNCHANGED"}, {"adapter": "dynamic cohort batching only", "component": "Structured Autonomy alias/prompt/schema/validator/renderer", "input": "DecisionEvidencePacket", "output": "validated shadow decision", "reuse": "HASH_FROZEN_UNCHANGED"}] |
| contract | "source-assembly-reuse-map-v1" |
| new_paid_provider | 0 |
| new_website_scraper | 0 |
