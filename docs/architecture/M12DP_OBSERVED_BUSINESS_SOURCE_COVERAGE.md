# Observed Business Source Coverage

`scripts/m12dp_observed_business_coverage.py` is a nonproduction, no-network gate.
It consumes the existing M12DK exact current-source authority result; it does
not grant new permissions or alter the accepted M12DO B raw/view binding.

The input consists of a same-generation source packet, evidence packet,
catalog, exact raw metadata, frozen binding and separately frozen issuer
resolver receipt. SEC ticker-to-CIK and OpenDART stock-to-corp-code resolvers
prove issuer association independently of ADR ratios or per-share valuation.
No cross-listing financial transfer is performed by this gate.

Every active subject needs at least one observed earnings source whose entire
exposed row has verified field lineage and existing `OVERALL_DIRECTION`
authority. Configured thesis/conditions, expectations, quality, working
capital, market, technical and valuation context cannot fill that requirement.
Unknown source families remain nondecisive. This implementation recognizes only
the observed source families already supported by M12DK; it is not a new KPI,
cash-flow or event-authority adapter.

The evaluator visits the whole registry cohort even after an individual failure.
Missing numerical facts and unusable lineage remain separate states. A source
binding error is a separate terminal, not missing coverage. The result preserves
reporting periods, source/field receipts, denied reasons and exact issuer
bindings. A verified older report is never relabeled as a current-session fact.

An individual ready subject cannot authorize any model call. Even complete
coverage only permits the next offline authority-aware Core schema gate; this
module always returns `allow_model_calls=false`. A failed whole-cohort gate must
stop before Core/A/B. No partial candidate, selective model invocation, inference
retry, source permission widening or historical claim reparenting is allowed.

M12DP's collected cohort stopped at source coverage (13/22 ready). Therefore the
authority-aware Core schema/prompt adapter, new blind handoff, atomic-claim gate
and Core/A/B inference were not reached or certified by this task. The old blind
comparison and sealed AI outputs remain historical and unopened.
