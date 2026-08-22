# Phase 9.1E.1 Kill Switch Verification

The single operating key is `WORKING_CAPITAL_USER_VISIBLE_MODE`. Missing, blank or invalid values
resolve to `OFF`. `OFF` removes all user-visible working-capital context from both AI and fallback
while retaining 9.1B canonical evidence, 9.1C shadow consumption, the 9.1D canary and Phase 9.0E
cash flow.

## Verified Procedure

1. Set `WORKING_CAPITAL_USER_VISIBLE_MODE=OFF`.
2. Restart `com.seungsoo.thesis-monitor` only when the imported runtime needs it.
3. Check `/health` without a manual Telegram or Scheduled Task.
4. Confirm mode resolution and enablement preflight return `OFF`.
5. Preserve all immutable receipts and archives.

The selective Inventory mode cannot bypass the machine gate. Trade AR and combined modes are
rejected by rollout policy even if configured. Feature-OFF packet and fallback hashes match the
previous operating implementation exactly.

Kill switch: `PASS`.

