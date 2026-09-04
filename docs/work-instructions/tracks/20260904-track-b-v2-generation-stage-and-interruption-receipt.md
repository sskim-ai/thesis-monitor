# Track B — V2 Generation Stage + Interruption Receipt

Use persisted V2 generation state so the outer waiter can distinguish:
STARTED / MODEL_ACTIVE / CANDIDATE_PERSISTED / VALIDATING /
ACCEPTED / SUPPRESSED / FAILED / INTERRUPTED / TERMINAL equivalents.

If SIGINT/SIGTERM/authorized cancellation occurs:
- do not leave ambiguous in-progress state
- write a claim/generation-bound terminal receipt
- preserve fallback/compatibility eligibility
- do not partially deliver V2
- no traceback-only terminal state

Target state contracts include:
accepted-v2-generation-stage-v1
v2-accepted-production-receipt-v1
