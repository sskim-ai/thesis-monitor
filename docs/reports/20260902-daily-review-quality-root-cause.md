# Daily Review Quality Root Cause

The immutable run-51 candidate had 47 original validation errors. Four interacting causes explain
the failure:

1. The candidate carried semantic claim references while the frozen packet lacked the newer
   semantic-scope marker and valuation-scope assignment.
2. Numeric sentence normalization changed prose without changing matching typed exact spans.
3. Canonical one-number wrappers and repeated secondary prose were treated as substantive prose.
4. A depositary underlying-share ratio was mistaken for a common-stock identity assertion.

The repair upgrades legacy scope only in memory, synchronizes exact spans, suppresses only exact
secondary phrases repeated at least three times, and distinguishes a depositary ratio from listed
security identity. Schema strictness and quality thresholds are unchanged.
