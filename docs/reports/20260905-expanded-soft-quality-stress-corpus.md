# Expanded Soft Quality Stress Corpus

Date: 2026-09-05 KST

Status: shadow-only; no production mutation or delivery.

Cases: `15` across `11` families. Source-owned label match: `100.0%`.

| Case | Family | Expected | Actual | Match |
|---|---|---|---|---|
| benign-heading | benign_repeated_headings | BENIGN_TEMPLATE_REPEAT | BENIGN_TEMPLATE_REPEAT | True |
| bound-numeric-wrapper | short_bound_numeric_wrapper_repetition | BENIGN_TEMPLATE_REPEAT | BENIGN_TEMPLATE_REPEAT | True |
| required-safety | short_safety_disclaimer_repetition | REQUIRED_SAFETY_REPEAT | REQUIRED_SAFETY_REPEAT | True |
| renderer-label | renderer_owned_repeated_phrase | RENDERER_OWNED_REPEAT | RENDERER_OWNED_REPEAT | True |
| short-factual | model_owned_short_factual_repetition | MODEL_OWNED_SUBSTANTIVE_REPEAT | MODEL_OWNED_SUBSTANTIVE_REPEAT | True |
| same-evidence-long | model_owned_long_substantive_rationale_repetition | MODEL_OWNED_SUBSTANTIVE_REPEAT | MODEL_OWNED_SUBSTANTIVE_REPEAT | True |
| different-evidence-long | long_cross_ticker_rationale_different_evidence | MATERIAL_SPAM_REPEAT | MATERIAL_SPAM_REPEAT | True |
| numeric-substitution-long | near_identical_rationale_numeric_substitutions | MATERIAL_SPAM_REPEAT | MATERIAL_SPAM_REPEAT | True |
| single-verbosity | verbosity | MODEL_OWNED_SUBSTANTIVE_REPEAT | MODEL_OWNED_SUBSTANTIVE_REPEAT | True |
| portfolio-boilerplate | boilerplate | MATERIAL_SPAM_REPEAT | MATERIAL_SPAM_REPEAT | True |
| korean-paraphrase-a | korean_paraphrase_diversity | MODEL_OWNED_SUBSTANTIVE_REPEAT | MODEL_OWNED_SUBSTANTIVE_REPEAT | True |
| korean-paraphrase-b | korean_paraphrase_diversity | MODEL_OWNED_SUBSTANTIVE_REPEAT | MODEL_OWNED_SUBSTANTIVE_REPEAT | True |
| holder-heading | benign_repeated_headings | BENIGN_TEMPLATE_REPEAT | BENIGN_TEMPLATE_REPEAT | True |
| safety-basis | short_safety_disclaimer_repetition | REQUIRED_SAFETY_REPEAT | REQUIRED_SAFETY_REPEAT | True |
| renderer-period | renderer_owned_repeated_phrase | RENDERER_OWNED_REPEAT | RENDERER_OWNED_REPEAT | True |
