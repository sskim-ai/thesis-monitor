# Phase 7.2.6 Production Remediation Runbook

## Status

This is a plan only. Phase 7.2.6 did not write the operating database, restart services, change
Scheduled Tasks, send Telegram, or change Pilot counters.

## Preconditions

1. The Phase 7.2 experimental branch has separate approval to merge and deploy.
2. The operating checkout is clean and aligned to the approved main commit.
3. A consistent operating database backup and exact `SecurityMaster` row snapshots exist.
4. Each evidence file still points to an accessible official SEC filing.
5. Production Assist remains disabled.

## Evidence Set

The isolated regression used authoritative SEC evidence for GOOGL and SKHY. CORZ, HUT, IBM, and
WULF were also resolved from official cover pages because the strict v2 trust boundary correctly
refused to preserve their inferred or historically mis-selected local identities. This avoids
restoring them through defaults.

- `20260815-phase7-2-6-googl-official-identity-evidence.json`
- `20260815-phase7-2-6-skhy-official-identity-evidence.json`
- `20260815-phase7-2-6-corz-official-identity-evidence.json`
- `20260815-phase7-2-6-hut-official-identity-evidence.json`
- `20260815-phase7-2-6-ibm-official-identity-evidence.json`
- `20260815-phase7-2-6-wulf-official-identity-evidence.json`

CRCL, MU, RXRX, SNDK, and TSLA retained explicit Watchlist issuer assertions. TSM and WRD retained
affirmative depositary evidence, but their current-security multiple gates remain independent.

## Procedure

For each approved evidence file, run the command without `--apply` first:

```bash
python -m app.jobs.security_identity_remediation \
  --evidence-json docs/reports/<evidence-file>.json
```

Confirm the exact ticker row, before/after fields, official URL/accession, and rollback snapshot.
Only then repeat with `--apply`. Re-run the same command afterward and require
`no_op_already_authoritative`.

After all approved rows are applied, rebuild an isolated US packet and require:

- GOOGL `verified_non_depositary`, Class A common stock.
- SKHY `verified_depositary`, ratio `0.1`, direction `ordinary_shares_per_adr`.
- SKHY PER/PBR/fPER still withheld until current-ADS denominator/share/currency basis is verified.
- All 13 active US stocks present.
- Binder and validator PASS with no manual binding.
- No FX, ADR EPS, or premium/discount calculation.

## Rollback

Every dry-run output contains the previous row as `rollback_snapshot`. If the approved application
does not match the plan, stop before packet generation and restore only through the existing
operational database recovery procedure. Do not use ad hoc SQL or rewrite historical packets.

## Isolated Proof

The copied database began at SHA-256
`23451ab3ac99b08b203c6dd736f31aac1ced1f1603be2a387d2ce2a0d22018a1`.
All six official identity ingestions changed only the copied database. A second identical ingestion
was a no-op. See the individual evidence JSON files and
`20260815-phase7-2-6-isolation-audit.json`.
