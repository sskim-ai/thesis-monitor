# Monitoring Fact-ID Ownership Repair

`monitoring:risk_reward_transition` was absent from CORZ/WULF canonical fact catalogs. Their candidates made no transition numeric claim but retained a stale declaration. The candidate owner removed only that known unavailable declaration.

Suppressions: `[{"ticker": "CORZ", "fact_id": "monitoring:risk_reward_transition", "reason": "unavailable_rr_transition_declaration_without_claim"}, {"ticker": "WULF", "fact_id": "monitoring:risk_reward_transition", "reason": "unavailable_rr_transition_declaration_without_claim"}]`

Arbitrary unknown IDs remain untouched and continue to fail strict validation.
