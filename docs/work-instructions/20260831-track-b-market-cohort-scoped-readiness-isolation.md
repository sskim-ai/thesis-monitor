# Track B — Market/Cohort-Scoped Readiness Isolation

Production readiness is scoped to:
market + session + packet cutoff + eligible ACTIVE/READY subjects.

KR readiness must not inspect/block on incomplete US subjects.
US readiness must not inspect/block on incomplete KR subjects.

Within one market, a single subject-level onboarding failure must fail closed for that subject while ready peers continue.

Freeze an immutable packet-universe snapshot at cutoff.

V2 candidate generation consumes that snapshot, not the global active universe.
