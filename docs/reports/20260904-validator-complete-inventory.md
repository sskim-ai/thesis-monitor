# Validator Complete Inventory

Date: 2026-09-04 KST

Status: shadow-only; no production mutation.

Inventory scope contains `64` logical enforcement families. Unique IDs: `64`. Coverage: `100%`; unclassified: `0`.

| Rule | Source | Current | New class | New owner | Gate |
|---|---|---|---|---|---|
| `schema.output_shape` | `app/schemas/ai_review.py:AIDailyReviewOutput` | hard | HARD_DETERMINISTIC | deterministic schema | unchanged hard gate |
| `numeric.fact_identity` | `app/services/numeric_provenance_service.py:bind_numeric_fact_references` | hard | HARD_DETERMINISTIC | numeric registry | unchanged hard gate |
| `numeric.value_exactness` | `app/services/numeric_provenance_service.py:bind_numeric_fact_references` | hard | HARD_DETERMINISTIC | numeric registry | unchanged hard gate |
| `numeric.semantic_unit` | `app/services/numeric_semantic_registry.py:resolve_numeric_semantic` | hard | HARD_DETERMINISTIC | numeric registry | unchanged hard gate |
| `numeric.currency_security_basis` | `app/services/numeric_semantic_registry.py:resolve_numeric_semantic` | hard | HARD_DETERMINISTIC | numeric registry | unchanged hard gate |
| `numeric.bound_label_source` | `app/services/ai_reasoning_quality_service.py:_numeric_label_quality_report` | hard | HARD_DETERMINISTIC | numeric binder | remain hard; detach from style aggregate |
| `numeric.postposition` | `app/services/ai_reasoning_quality_service.py:_numeric_label_quality_report` | hard | SOFT_QUALITY | AI writer quality | soft warning or one rewrite |
| `numeric.cross_section_repetition` | `app/services/ai_reasoning_quality_service.py:_numeric_fact_repetition_report` | hard | SOFT_QUALITY | AI writer quality | soft warning unless ownership is contradictory |
| `numeric.primary_owner` | `app/services/ai_reasoning_quality_service.py:_numeric_primary_ownership_report` | hard | HARD_DETERMINISTIC | structured semantic planner | unchanged hard gate |
| `numeric.business_valuation_owner` | `app/services/ai_reasoning_quality_service.py:_business_numeric_ownership_report` | hard | SEMANTIC_HARD | structured semantic planner | hard only on explicit metadata mismatch |
| `semantic.evidence_exists` | `app/services/semantic_decision_service.py:semantic_claim_reference_errors` | hard | HARD_DETERMINISTIC | structured semantic planner | unchanged hard gate |
| `semantic.evidence_section_fencing` | `app/services/semantic_decision_service.py:semantic_claim_reference_errors` | hard | HARD_DETERMINISTIC | structured semantic planner | unchanged hard gate |
| `semantic.denied_fact_echo` | `app/services/semantic_decision_service.py:semantic_claim_reference_errors` | hard | SEMANTIC_HARD | structured semantic planner | migrate lexical ownership to claim metadata |
| `semantic.valuation_scope` | `app/services/semantic_decision_service.py:valuation_context_reference_errors` | hard | SEMANTIC_HARD | structured semantic planner | hard on explicit scope contradiction |
| `semantic.typed_valuation` | `app/services/semantic_decision_service.py:typed_valuation_scope_error` | hard | SEMANTIC_HARD | structured semantic planner | unchanged semantic hard gate |
| `semantic.holder_observer` | `app/services/semantic_decision_service.py:observer_holder_semantic_error` | hard | SEMANTIC_HARD | structured decision fields | hard only on material contradiction |
| `quality.exact_sentence_repeat` | `app/services/ai_reasoning_quality_service.py:relational_reasoning_quality_report` | hard | SOFT_QUALITY | AI writer quality | soft by default; material spam separately reviewed |
| `quality.typed_skeleton_repeat` | `app/services/ai_reasoning_quality_service.py:relational_reasoning_quality_report` | hard | SOFT_QUALITY | AI writer quality | taxonomy plus one bounded rewrite |
| `quality.generic_methodology` | `app/services/ai_reasoning_quality_service.py:relational_reasoning_quality_report` | hard | SOFT_QUALITY | AI writer quality | soft warning |
| `quality.generic_numeric_summary` | `app/services/ai_reasoning_quality_service.py:relational_reasoning_quality_report` | hard | SOFT_QUALITY | AI writer quality | soft warning |
| `quality.next_unknown_repeat` | `app/services/ai_reasoning_quality_service.py:relational_reasoning_quality_report` | hard | SOFT_QUALITY | AI writer quality | soft warning or rewrite |
| `quality.watch_next_overlap` | `app/services/ai_reasoning_quality_service.py:_watch_next_overlap_report` | hard | SOFT_QUALITY | AI writer quality | soft warning |
| `quality.observer_holder_distinct_wording` | `app/services/ai_reasoning_quality_service.py:relational_reasoning_quality_report` | hard | SOFT_QUALITY | AI writer quality | soft unless structured stances contradict |
| `quality.us_kr_supply_language` | `app/services/ai_reasoning_quality_service.py:relational_reasoning_quality_report` | hard | SEMANTIC_HARD | structured semantic planner | hard on semantic family mismatch; wording itself soft |
| `quality.supply_grounding` | `app/services/ai_reasoning_quality_service.py:relational_reasoning_quality_report` | hard | HARD_DETERMINISTIC | evidence ownership | unchanged hard gate |
| `quality.financial_period` | `app/services/ai_reasoning_quality_service.py:relational_reasoning_quality_report` | hard | HARD_DETERMINISTIC | financial lineage | unchanged hard gate |
| `quality.valuation_evidence` | `app/services/ai_reasoning_quality_service.py:relational_reasoning_quality_report` | hard | HARD_DETERMINISTIC | valuation lineage | unchanged hard gate |
| `quality.message_completeness` | `app/services/ai_reasoning_quality_service.py:relational_reasoning_quality_report` | hard | HARD_DETERMINISTIC | delivery integrity | unchanged hard gate |
| `quality.rendered_heading` | `app/services/ai_reasoning_quality_service.py:relational_reasoning_quality_report` | hard | SOFT_QUALITY | thin renderer | soft unless schema is unparseable |
| `quality.identity_prose` | `app/services/ai_reasoning_quality_service.py:relational_reasoning_quality_report` | hard | SEMANTIC_HARD | structured security identity | hard on structured identity contradiction |
| `quality.internal_lexicon` | `app/services/ai_reasoning_quality_service.py:_final_rendered_language_report` | hard | SOFT_QUALITY | thin renderer | soft warning or rewrite |
| `quality.korean_grammar` | `app/services/ai_reasoning_quality_service.py:_final_rendered_language_report` | hard | SOFT_QUALITY | AI writer quality | soft warning |
| `financial.raw_mapping` | `app/services/financial_validation.py:validate_event_financials` | hard | HARD_DETERMINISTIC | financial lineage | unchanged hard gate |
| `financial.period_basis` | `app/services/financial_validation.py:validate_event_financials` | hard | HARD_DETERMINISTIC | financial lineage | unchanged hard gate |
| `financial.attribution` | `app/services/financial_validation.py:validate_event_financials` | hard | HARD_DETERMINISTIC | financial lineage | unchanged hard gate |
| `financial.quality_taint` | `app/services/financial_quality_service.py:build_financial_quality_state` | hard | HARD_DETERMINISTIC | financial lineage | unchanged hard gate |
| `financial.book_coherence` | `app/services/financial_quality_service.py:_book_valuation_coherence` | hard | HARD_DETERMINISTIC | financial lineage | unchanged hard gate |
| `price.current_context` | `app/services/current_price_context_service.py:select_current_price_context` | hard | HARD_DETERMINISTIC | price lineage | unchanged hard gate |
| `price.fallback_context` | `app/services/current_price_context_service.py:fallback_price_context_errors` | hard | HARD_DETERMINISTIC | price lineage | unchanged hard gate |
| `price.structure_numeric` | `app/services/price_structure_v3_renderer_service.py:validate_price_structure_render` | hard | HARD_DETERMINISTIC | price structure lineage | unchanged hard gate |
| `price.legacy_token` | `app/services/price_structure_v3_renderer_service.py:detect_legacy_technical_tokens` | hard | SEMANTIC_HARD | structured render occurrence | hard only when a structured stale occurrence is identified |
| `market.us_evidence_utilization` | `app/services/market_evidence_utilization_validator_service.py:validate_us_market_evidence_utilization` | hard | SEMANTIC_HARD | structured semantic planner | hard on material required-slot contradiction |
| `market.kr_evidence_utilization` | `app/services/market_evidence_utilization_validator_service.py:validate_kr_market_evidence_utilization` | hard | SEMANTIC_HARD | structured semantic planner | hard on material required-slot contradiction |
| `market.us_payload_identity` | `app/services/us_market_message_quality_service.py:quality_result_matches_received_payload` | hard | HARD_DETERMINISTIC | delivery integrity | unchanged hard gate |
| `market.us_wording_quality` | `app/services/us_market_message_quality_service.py:validate_us_market_message_payload` | hard | SOFT_QUALITY | AI writer and thin renderer | split structural completeness from soft wording |
| `decision.evidence_ownership` | `app/services/cross_market_decision_engine_service.py:validate_decision_candidate` | hard | HARD_DETERMINISTIC | decision evidence packet | unchanged hard gate |
| `decision.numeric_fencing` | `app/services/cross_market_decision_engine_service.py:validate_decision_candidate` | hard | HARD_DETERMINISTIC | numeric registry | unchanged hard gate |
| `decision.trade_contradiction` | `app/services/preconfirmation_decision_v2_service.py:validate_preconfirmation_candidate` | hard | SEMANTIC_HARD | structured semantic planner | hard only on explicit mandatory contradiction |
| `decision.confirmation_condition` | `app/services/accepted_decision_v2_service.py:decision_change_condition_errors` | hard | SEMANTIC_HARD | structured decision fields | migrate condition type from prose to metadata |
| `decision.accepted_candidate` | `app/services/accepted_decision_v2_service.py:validate_accepted_v2_decision` | hard | HARD_DETERMINISTIC | accepted-decision owner | unchanged hard gate |
| `decision.accepted_render` | `app/services/accepted_decision_v2_service.py:validate_accepted_v2_render` | hard | HARD_DETERMINISTIC | thin renderer | unchanged hard gate |
| `decision.accepted_message_quality` | `app/services/accepted_decision_v2_service.py:accepted_message_quality` | hard | SEMANTIC_HARD | split numeric binder and soft reviewer | numeric remains hard; repetition becomes soft |
| `decision.consistency` | `app/services/accepted_decision_consistency_service.py:audit_accepted_decision_consistency` | hard | HARD_DETERMINISTIC | accepted-decision owner | unchanged hard gate |
| `decision.polarity` | `app/services/decision_canary_service.py:decision_polarity_errors` | hard | SEMANTIC_HARD | structured semantic planner | hard on explicit polarity mismatch |
| `decision.localization` | `app/services/decision_canary_service.py:decision_korean_localization_errors` | hard | SOFT_QUALITY | AI writer quality | soft warning or rewrite |
| `free_analyst.claim_ownership` | `app/services/evidence_locked_free_analyst_service.py:_validate_claim_ownership` | hard | HARD_DETERMINISTIC | structured semantic planner | unchanged hard gate |
| `free_analyst.synthesis` | `app/services/evidence_locked_free_analyst_service.py:validate_free_analyst_analysis` | hard | SEMANTIC_HARD | structured semantic planner | hard on explicit unsupported inference |
| `free_analyst.rendered_safety` | `app/services/evidence_locked_free_analyst_service.py:rendered_safety_report` | hard | SEMANTIC_HARD | thin renderer | split hard binding from soft prose |
| `free_analyst.novelty` | `app/services/evidence_locked_free_analyst_service.py:novel_synthesis_report` | hard | SOFT_QUALITY | AI writer quality | soft quality only |
| `delivery.claim_fencing` | `app/services/ai_assisted_delivery_service.py:_same_analysis_generation` | hard | HARD_DETERMINISTIC | delivery state machine | unchanged hard gate |
| `delivery.receipt_integrity` | `app/services/ai_assisted_delivery_service.py:_persisted_quality_integrity_errors` | hard | HARD_DETERMINISTIC | delivery state machine | unchanged hard gate |
| `delivery.exactly_once` | `app/services/ai_assisted_delivery_service.py:_session_deliveries` | hard | HARD_DETERMINISTIC | delivery state machine | unchanged hard gate |
| `delivery.terminal_immutability` | `app/services/accepted_decision_v2_runtime_service.py:advance_accepted_v2_state` | hard | HARD_DETERMINISTIC | delivery state machine | unchanged hard gate |
| `delivery.orphan_reconciliation` | `app/services/notification_delivery_integrity_service.py:inspect_kr_orphan_incident` | hard | HARD_DETERMINISTIC | delivery state machine | unchanged hard gate |
