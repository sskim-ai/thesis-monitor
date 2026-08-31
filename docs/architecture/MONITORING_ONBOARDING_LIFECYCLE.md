# Monitoring Onboarding Lifecycle

Contract: `monitoring-onboarding-readiness-v1`.

## States

`PENDING_ONBOARDING -> READY -> ACTIVE` is the only activation path. A failed or incomplete subject remains `PENDING_ONBOARDING` or `ONBOARDING_FAILED`; an explicitly stopped subject is `INACTIVE`.

Monitoring intent and production eligibility are separate:

```text
monitoring_requested = true
onboarding_state = PENDING_ONBOARDING
production_eligible = false
```

The coordinator in `onboarding_readiness_service.py` is the only code that can promote a subject after the canonical validator passes. Registration never writes `active=true` first. Retry is idempotent and preserves thesis and assessment history.

## Invariant

```text
ACTIVE => onboarding_ready && production_eligible
```

The backward-compatible SQLite migration only adds columns. The deployment repair audits legacy rows immediately: complete rows are reconciled to `ACTIVE`, incomplete legacy-active rows become `PENDING_ONBOARDING`, and historical inactive rows remain `INACTIVE`.
