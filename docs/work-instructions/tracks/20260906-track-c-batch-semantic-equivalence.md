# Track C — Batch Semantic Equivalence

Determine whether batch means:
TRANSPORT_ONLY_GROUPING
or
MODEL_CONTEXT_COUPLED.

If splitting changes model context, it is NOT transport-only.

To call a split semantically equivalent, prove per-subject:
prompt SHA unchanged
schema SHA unchanged
model/effort unchanged
evidence aliases unchanged
source packet unchanged.

If equivalence cannot be proven, do not split while reusing the current holdout.
