# Cash-Flow User-Visible Kill Switch

## Configuration

The operating key is:

```text
CASH_FLOW_USER_VISIBLE_MODE
```

Supported values:

```text
OFF
SELECTIVE_CURRENT_FORMAL_FULL_FCF
```

The code default is `OFF`. Blank, misspelled, or unknown values fail safe to `OFF`.

## Disable Procedure

1. In the configured operating checkout, change only the `.env` entry to:

   ```text
   CASH_FLOW_USER_VISIBLE_MODE=OFF
   ```

2. Restart the imported runtime process:

   ```bash
   launchctl kickstart -k gui/$(id -u)/com.seungsoo.thesis-monitor
   ```

3. Verify service health without sending a notification:

   ```bash
   curl -fsS http://127.0.0.1:8766/health
   ```

4. In a non-delivery settings smoke, verify `resolve_rollout_mode()` returns `OFF`.
5. Do not run a Scheduled Task or send a manual Telegram as proof.

The next naturally constructed packet contains no user-visible cash-flow Facts or prose. Previously
sent messages and immutable archives are not rewritten.

## Enable Procedure

Enable only after `CASH_FLOW_USER_VISIBLE_ROLLOUT_READY = YES`:

```text
CASH_FLOW_USER_VISIBLE_MODE=SELECTIVE_CURRENT_FORMAL_FULL_FCF
```

Restart the same service, verify `/health`, and run only a non-delivery selector/settings smoke. The
next natural US run is the first production proof. KR remains excluded.

## Verified Safety

Automated tests cover:

- default OFF and unknown-value fail-safe;
- SELECTIVE selection and OFF transition in one process;
- no stale selected context after OFF;
- no cash-flow Fact catalog entries or rendered block under OFF;
- per-ticker selector and renderer failure suppression;
- AI/fallback mismatch hard failure;
- unchanged-evidence suppression after a prior sent context;
- detached canary parity remaining observational.

Disabling this feature does not disable the canonical core, baseline-consistency repair, or detached
cash-flow runtime canary. It only removes user-visible selection.
