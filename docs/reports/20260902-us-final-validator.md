# US Final Validator

- terminal AI validation: `quality_rejected`
- terminal error: `runtime_message_quality_gate_failed`
- rejected AI sent: `False`
- fallback eligibility preserved: `True`
- runtime quality gate: `failed`
- runtime quality details: `{"final_language_errors": 1, "identity_prose_mismatch": 1, "max_repeat": 10, "rendered_heading_mismatch": 14, "repeated_sentences": 7, "template_skeleton_repeats": 9}`
- final stock state: `14 FALLBACK_ELIGIBLE`
- repair loop unbounded: `0`

The unchanged quality gate correctly blocked the AI set for repeated substantive prose plus rendered heading/identity/language defects. Thresholds were not relaxed.

- `US_FINAL_VALIDATION_PASS_COUNT = 0`
- `US_FINAL_VALIDATION_REJECT_COUNT = 14`
