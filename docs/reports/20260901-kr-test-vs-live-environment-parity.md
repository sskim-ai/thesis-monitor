# KR Test Versus Live Environment Parity

## First divergence

`PASSING_TEST_VS_LIVE_FIRST_DIVERGENCE = V2_CLI_OUTPUT_SCHEMA_PATH_RESOLUTION`

| Dimension | Passing 22/22 preflight | Natural live |
| --- | --- | --- |
| Helper | `_invoke_signed_in_codex` | `_invoke_signed_in_codex` |
| Model / effort | `gpt-5.6-sol` / `xhigh` | configured same; model not reached |
| CWD | absolute `/private/tmp/.../kr` | relative `data/ai_review/claims` |
| Schema argument | absolute `/private/tmp/.../output.schema.json` | relative `data/ai_review/claims/...schema.json` |
| Effective schema | exists | duplicated path, missing |
| Technical context | FULL 8/8 | FULL 8/8 |
| Candidate result | 8 generated, 8 accepted | 0 generated |

The preflight accepted an absolute `--output-dir`, so `schema=output_dir/output.schema.json` was absolute even when the subprocess cwd was that directory. Natural `_paths()` preserved the claim's repository-relative `final_output_path`, then passed the derived relative schema together with `cwd=schema.parent`.

The same Python environment, signed-in CLI selector, model constants, and read-only sandbox were used. State DB warnings occurred in both modes and were non-terminal in the passing control. No feature flag, provider, scheduler user, or network difference is needed to explain the failure.

`UNEXPLAINED_TEST_LIVE_ENVIRONMENT_DIVERGENCE = 0`
