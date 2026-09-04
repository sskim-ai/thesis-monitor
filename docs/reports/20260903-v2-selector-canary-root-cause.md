# V2 Selector and Canary Root Cause

The run-54 `V2_DECISION_SUPPRESSED_SAFE` result was not caused by the corrected daily-review
candidate and was not the cause of pending/retry invisibility.

The production packet had a valid accepted daily review, but no complete claim-bound accepted V2
artifact. The archive contained context, schema, and prompts; it did not contain the final accepted
V2 output and completion receipt required by the loader. The selector therefore suppressed all
eight decision blocks by contract.

The repair adds a persistent stage receipt (`accepted-v2-generation-stage-v1`) for context ready,
model path ready, each model invocation, each candidate batch, accepted artifact creation, and
safe suppression. It does not alter the model, prompt, adjudication, or validator thresholds.

During E2E, the real signed-in Codex path reached `gpt-5.6-sol` at `xhigh`, produced eight accepted
blocks, and exposed two additional integration defects: all-stock final-language errors in base
prose and archive scope filtering by adaptive-canary membership. Both were repaired without
weakening quality gates.
