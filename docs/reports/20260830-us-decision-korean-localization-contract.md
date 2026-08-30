# US Decision Korean Localization Contract

US localization now starts at the structured `DecisionCandidate`, before message-quality validation and rendering. Every non-empty user-facing claim must contain Korean context. English remains allowed for tickers, framework names, and proper nouns inside a Korean sentence.

Validation covers timing, decisive reason, HOLD boundaries, supporting/opposing evidence, BUY/SELL polarity claims, neutral context, unknowns, and upgrade/downgrade conditions. The rule is enforced in both output validation and canary-block rendering, so a stored English candidate cannot bypass the gate.

The signed-in Codex CLI replay used `gpt-5.6-sol` with `model_reasoning_effort="xhigh"`. Same-evidence decision, confidence, horizon, timing, BUY refs, SELL refs, and change-condition refs were preserved for all four subjects.

- `POSTHOC_FREEFORM_TRANSLATION_AS_SOURCE_OF_TRUTH = 0`
- `LOCALIZATION_CHANGED_DECISION_SEMANTICS = 0`
- `LOCALIZATION_NUMERIC_BINDING_MISMATCH = 0`
- `US_DECISION_MIXED_LANGUAGE_CORE_FIELDS = 0`
- `ORDER_COMMAND_LANGUAGE = 0`
- `ORDER_SIZING_OUTPUT = 0`
