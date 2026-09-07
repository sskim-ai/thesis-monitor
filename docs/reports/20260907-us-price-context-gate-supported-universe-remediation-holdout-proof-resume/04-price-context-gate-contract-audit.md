# 04 Price Context Gate Contract Audit

| Field | Value |
| --- | --- |
| code_paths | ["app/services/coldstart_source_assembly_service.py", "app/services/coldstart_fundamental_enrichment_service.py", "app/services/cross_market_decision_engine_service.py"] |
| contract | price-context-gate-contract-audit-v1 |
| decision_evidence_packet_requires_current_price | False |
| directional_core_requires_safe_technical_context | False |
| packet_rejected_before_stage_ownership | True |
| price_and_technical_are_conditional | True |
| price_timing_unavailable_path | DecisionCandidate.timing=INSUFFICIENT |
| pure_price_failure_was_relabelled_as_security_basis_block | True |
| status | PASS |

Machine proof: `proofs/04-price-context-gate-contract-audit.json`.
