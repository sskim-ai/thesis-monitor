# Onboarding Retry Classification

| Class | Meaning | Behavior |
| --- | --- | --- |
| `RETRYABLE` | Transient provider, CLI, or validator path can succeed later | Persist failure stage and capped exponential retry |
| `WAIT_FOR_DATA` | Required canonical evidence is not yet available | Remain excluded and retry after a bounded delay |
| `REVIEW_REQUIRED` | Identity, basis, or irreconcilable evidence conflict | Stop automatic retries pending review |

Every attempt persists `attempt_count`, `last_attempt_at`, `next_retry_at`, `last_failure_stage`, origin, retry class, and a bounded safe error. Missing data is never converted to a passing placeholder. No unbounded loop or ticker exception exists.
