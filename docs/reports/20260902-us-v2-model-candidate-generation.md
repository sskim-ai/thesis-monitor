# US V2 Model and Candidate Generation

| Owner | Claim | Schema | Exists | Subprocess | Model reached | Response | Error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| codex-us-primary | afd76205-7401-4912-a8a6-4711fd214e1b | <OPERATING_ROOT>/data/ai_review/claims/2026-09-02-us-run-51-39a4d4eec53e--daily-review-v3.10--dc747fff8565--afd76205-7401-4912-a8a6-4711fd214e1b.decision-v2-schema.json | True | True | False | NO_MODEL_RESPONSE | CODEX_APP_SERVER_INITIALIZATION_FAILED_READONLY_STATE_DB |
| codex-us-backup | 47594101-6ad0-497e-962d-4c1b208f5fe4 | <OPERATING_ROOT>/data/ai_review/claims/2026-09-02-us-run-51-39a4d4eec53e--daily-review-v3.10--dc747fff8565--47594101-6ad0-497e-962d-4c1b208f5fe4.decision-v2-schema.json | True | True | False | NO_MODEL_RESPONSE | CODEX_APP_SERVER_INITIALIZATION_FAILED_READONLY_STATE_DB |

The repaired path contract succeeded: schema and prompt existed, the schema path was absolute at invocation, and no duplicated `claims/.../claims` path occurred. The Codex subprocess then failed before model transport because its state database was read-only, so there was no response, candidate, adjudication, accepted artifact, or receipt.

- `US_V2_SCHEMA_PATH_DUPLICATION = 0`
- `US_V2_MODEL_CALL_REACHED = FAIL`
- `US_V2_MODEL_CALL_REACHED_COUNT = 0`
- `US_V2_CANDIDATE_GENERATED_COUNT = 0`
- `ONE_US_CANDIDATE_ERROR_KILLS_BATCH = 0` (not reached)
