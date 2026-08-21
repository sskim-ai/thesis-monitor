# Phase 9.1E Implementation

Phase 9.1E starts from immutable instruction commit
`99f7e86f3ae40cc86a4865ef70dc89abf79d5a37`, then explicitly reconciles Track A main through merge
commit `ee78eb7f7eefd0ad2e7421528dd9518b04168e4f`. The implementation commit is
`a4f8570130d1fd33f802d391c6a196d1c5579278`.

Implemented:

- inert `WORKING_CAPITAL_USER_VISIBLE_MODE`, default/invalid `OFF`;
- `working-capital-user-visible-v1` preview context;
- `working-capital-user-visible-enable-gate-v1` family-level natural-proof gate;
- independent Inventory, exact Trade AR, and combined mode preflight;
- Phase 9.1D selector reuse with total-Inventory/exact-Trade-AR semantic guards;
- one-relation, one-number `business_earnings` preview;
- compatible-period Phase 9.0E cash-flow redundancy suppression;
- shared AI/fallback context identity and semantic/causal validation;
- deterministic archive evidence generator and 20-subject readiness JSON.

Production AI, fallback, Telegram, Public Action, snapshot, assessment DB, and warning lifecycle do
not import or consume the new service. Feature state remains `OFF`.

The archive result has 7 canary candidates and 5 lower-noise future previews: 3 Inventory and 2
exact Trade AR. MU and TSLA Inventory are suppressed because compatible Phase 9.0E cash-flow
context already owns the decision-relevant point and the WC relation resolves no additional
Unknown. Broad AR and all AP select zero.
