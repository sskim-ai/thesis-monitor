# Track B — Daily-Review Quality Convergence

## Run-51 evidence

Initial:
- SCHEMA_EXTRA_FIELD 14
- VALUATION_INTERPRETATION_BINDING 33

Terminal numeric:
- automatic 124
- manual/rejected/unresolved 0/0/0

Final quality:
- rendered_heading_mismatch 14
- repeated_sentences 7
- max_repeat 10
- template_skeleton_repeats 9
- identity_prose_mismatch 1
- final_language_errors 1

## Required

Build exact per-ticker/per-span ownership ledger.

Fix root causes:
- one schema contract, no unknown-field validator relaxation
- valuation interpretation remains provenance-safe
- deterministic renderer owns headings/company identity where appropriate
- distinguish mandated structural skeleton from substantive repeated prose
- do not lower substantive repeat thresholds
- bounded correction only on failing spans
- rerun numeric/semantic/valuation/quality validation after correction

Daily-review must never override a valid V2 accepted plan.

## Target

Run-51 immutable replay:
- schema PASS
- numeric PASS
- valuation PASS
- heading mismatch 0
- substantive repeated sentences 0
- identity mismatch 0
- language errors 0
- quality PASS
