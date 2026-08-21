# Phase 9.1E Kill-Switch Audit

The code default for `WORKING_CAPITAL_USER_VISIBLE_MODE` is `OFF`; blank and invalid values also
resolve to `OFF`. A selective request cannot become effective without a passing metric-family gate.

Automated coverage proves:

- OFF keeps preview-selected contexts user-visible disabled;
- the same context can become eligible only after a complete `LIVE_PASS` gate and a matching
  selective mode;
- Inventory-only proof does not enable exact Trade AR;
- combined mode requires both family gates;
- natural failure or open P0 blocks enablement;
- OFF does not erase canonical, archive-shadow, runtime-canary, or cash-flow state.

The operating procedure is documented at
`docs/operations/WORKING_CAPITAL_USER_VISIBLE_KILL_SWITCH.md`. Phase 9.1E ends OFF and performs no
operator enablement action.
