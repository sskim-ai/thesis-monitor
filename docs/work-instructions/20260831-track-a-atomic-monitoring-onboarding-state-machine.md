# Track A — Atomic Monitoring Onboarding State Machine

Implement/normalize lifecycle:

PENDING_ONBOARDING
→ READY
→ ACTIVE

Failure:
ONBOARDING_FAILED / PENDING safe state

Required before ACTIVE:
- identity
- security master
- company profile
- investment logic
- initial evidence
- initial baseline assessment
- decision readiness

ACTIVE must imply readiness PASS.

Registration intent may exist while production eligibility remains false.

No ticker-specific bypass.
Idempotent retries.
