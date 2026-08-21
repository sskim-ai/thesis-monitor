# Working-Capital User-Visible Kill Switch

## Configuration

The operating key is:

```text
WORKING_CAPITAL_USER_VISIBLE_MODE
```

Supported values are `OFF`, `SELECTIVE_INVENTORY`, `SELECTIVE_EXACT_TRADE_AR`, and
`SELECTIVE_INVENTORY_AND_EXACT_TRADE_AR`. Missing, blank, misspelled, or unknown values fail closed
to `OFF`.

Phase 9.1E leaves the setting absent or explicitly `OFF`. The resolved operating state must be
`OFF`.

## Disable Procedure

1. Set `WORKING_CAPITAL_USER_VISIBLE_MODE=OFF` in the operating environment.
2. Restart the imported runtime process with the existing service procedure.
3. Check `/health` without sending Telegram or running a Scheduled Task.
4. In a non-delivery smoke, verify `resolve_user_visible_mode()` and mode preflight both return
   `OFF`.

The next naturally created packet receives no user-visible working-capital enrichment. Existing
messages and immutable archives are never rewritten.

## Enablement Preflight

Do not set a selective mode until a separate enablement-only instruction confirms `LIVE_PASS` for
every requested metric family. The preflight must verify the Phase 9.1D packet/receipt evidence,
Fact and relation lineage, PIT/currentness, semantic/causal/numeric PASS, zero production influence,
and no open P0/material P1. A failed or incomplete gate forces the effective mode back to `OFF`.

Inventory and exact Trade AR are independently enableable. A combined mode requires both gates.

## Isolation

Turning this feature OFF does not disable:

- Phase 9.1B canonical facts;
- Phase 9.1C archive-only shadow consumption;
- Phase 9.1D detached runtime canary;
- Phase 9.0E selective cash-flow output.

It disables only future working-capital production enrichment. Phase 9.1E performs no enablement,
manual task, manual Telegram, Pilot mutation, DB mutation, or warning mutation.
