# CORZ / HUT OR-AND Regression

The historical CORZ and HUT findings both originated from source invalidation conditions containing alternatives: contract cancellation/large reduction **or** repeated construction failure. The writer had narrowed these to joint requirements.

The repair is generic. Source conditions are materialized as `ANY_OF` before the writer and passed through the canonical evidence packet. A claim declaring `FULL` must copy the exact condition tree; changing it to `ALL_OF` fails with `logical_condition_full_semantic_mismatch`. One branch remains legal only when declared `NON_EXHAUSTIVE_EXAMPLE`.

Regression results cover `ANY_OF -> ALL_OF`, `ALL_OF -> ANY_OF`, branch deletion, cross-condition mixing, severity mutation, subject/generation ownership, full round-trip, and non-exhaustive examples. `CORZ_TICKER_EXCEPTION = 0`; `HUT_TICKER_EXCEPTION = 0`.
