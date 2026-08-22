# US AI RR Ownership Audit

Primary owner: `price_context`; primary prose slot: `price_positioning.text`.

`runtime_specificity_plan.price_fact_ownership` is now a catalog-derived
allowlist for current price, support, resistance, RR, transition, invalidation,
and confirmation. It does not calculate a second RR.

CORZ, HUT, and WULF had unavailable current RR and no canonical RR Fact in the
immutable packet. The repaired replay removes only the invalid declaration;
all canonical price/support/resistance facts and text remain available. The
quality receipt reports `current_rr_violation_count=0`.

Available-RR fixtures retain the exact canonical RR ID. Unavailable-RR fixtures
expose it only under `unavailable_fact_ids`. Missing or wrong ownership remains
a validator failure.

