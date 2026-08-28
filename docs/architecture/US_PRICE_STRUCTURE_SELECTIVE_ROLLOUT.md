# US Price Structure Selective Rollout

Contract: `us-price-structure-selective-rollout-v1`

The US rollout consumes `price_structure_v3` for the active monitored US/foreign universe. It
renders backend-owned current-session support/resistance only when market, security basis,
currency, completed-bar, selection, proximity, and renderer validation all pass. Fibonacci content
is optional and appears only when family consensus is safe.

The declared structure `as_of` must equal `coverage.daily.actual_end_date` whenever both are
present. A mismatch is `daily_history_as_of_mismatch`: current and legacy price claims are removed
from the candidate, while separately labeled stored price-rule history may remain. This is a
generic session guard, not a ticker exception.

The rollout does not create target prices or stop prices. Current structural zones and historical
registered rules remain separate ownership surfaces. Unsupported subjects fail closed without
blocking safe peers.
