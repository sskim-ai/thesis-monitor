# SR Timeframe Fallback Provenance

Local classification is `AVAILABLE_LOCAL`. Daily may fall back to weekly then monthly;
weekly may fall back to monthly. A fallback is `AVAILABLE_HIGHER_TF_FALLBACK` and preserves
`requested_timeframe`, `source_timeframe`, and `fallback_reason`. It is never relabeled as a local
level. No confirmed side and insufficient history have separate explicit states.
