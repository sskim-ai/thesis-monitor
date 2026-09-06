# Dual-Market Source Coverage and New-Issuer Holdout Ownership Proof

## Result

The bounded source diagnostic completed for both markets.

```text
DUAL_MARKET_SOURCE_STATUS = US_FAIL_KR_PASS
readiness = NOT_READY_US_SOURCE_COVERAGE_BLOCKED
next_scope = BOUNDED_US_SOURCE_COVERAGE_REMEDIATION
```

The previous orchestration defect is closed: the US shortfall did not abort the KR
diagnostic. Because the US target remained below four, no final 16-issuer cohort,
source lock, precommit, or real model invocation was created.

## Repository

| Field | Value |
| --- | --- |
| Base | `cdc48a903d86f208e7af71c08b56dbceaf83de89` |
| Work-instruction commit | `c28e723bce23bde43458ac7444c53ee4e5526cd7` |
| Final implementation commit | `f3dbc139e5d5500194abfddba3dad9d5014135f6` |
| Branch | `codex/20260907-dual-market-source-coverage-new-issuer-holdout-ownership-proof` |
| Prior exposure registry | 61 canonical issuers |
| Exclusion set | 70 tickers |
| Forensic ZIP integrity | `PASS` (`c8836835...bc3b4`) |

Changes are limited to experiment tooling, tests, the work instruction, and generated
reports. Production investment semantics and runtime delivery were not changed.

## US Coverage

| Ticker | Candidate | Result | Failure class | Evidence |
| --- | --- | --- | --- | --- |
| NVDA | Initial | Eligible | N/A | Official profile, SEC companyfacts, and packet assembly passed |
| JPM | Initial | Blocked | `PIPELINE_COVERAGE_GAP` | SEC facts contain regulatory/sector tags, but the canonical required family is not mapped |
| WMT | Initial | Blocked | `SOURCE_ABSENCE` | Current price/as-of and safe technical context were unavailable |
| BRK-B | Initial | Blocked | `PIPELINE_COVERAGE_GAP` | SEC facts contain insurance/sector tags, but the canonical required family is not mapped |
| MSFT | Reserve | Eligible | N/A | Official profile, SEC companyfacts, and packet assembly passed |

```text
target = 4
attempted = 5
source_sufficient = 2
source_insufficient = 3
pipeline_coverage_gap = 2
source_absence = 1
unknown_failure = 0
US_SOURCE_TARGET_STATUS = FAIL
```

The next repair should remain US-only. JPM and BRK-B need bounded
regulatory/sector-family normalization coverage; WMT needs current price/technical
source recovery or a precommitted replacement from an expanded supported US universe.

## KR Coverage

The first 11 candidates passed. `094800` failed because a supported current OpenDART
formal financial statement was unavailable. The first reserve, `415380`, passed and
filled the twelfth slot.

Eligible KR candidates:

```text
142210 060900 002680 035420 216050 100700
001530 487580 038870 342870 060230 415380
```

```text
target = 12
attempted = 13
source_sufficient = 12
source_insufficient = 1
pipeline_coverage_gap = 0
source_absence = 1
unknown_failure = 0
KR_SOURCE_TARGET_STATUS = PASS
```

KR coverage is adequate under the frozen policy and should not be rerun during a
US-only remediation unless its source inputs materially change.

## Provider Audit

| Provider path | Requests | Success | Cache hits |
| --- | ---: | ---: | ---: |
| US official profiles | 5 | 5 | N/A |
| SEC companyfacts | 5 | 5 | 0 |
| KR official profiles | 13 | 13 | N/A |
| OpenDART statement operations | 37 | 12 candidate-level successes | 0 |
| Base OHLCV requests on eligible packets | 42 | 42 | 0 |

No paid provider was added. All source activity was bounded, official/read-only, or
existing canonical market-data assembly.

## Model And Safety Gate

```text
new_holdout_cohort = NOT_CREATED
new_source_generation_id = NOT_CREATED
new_source_lock = NOT_CREATED
FIRST = NOT_RUN
A = NOT_RUN
B = NOT_RUN
C = NOT_RUN
real_holdout_model_invocation_count = 0
real_holdout_model_calls_while_source_target_failed = 0
holdout_output_exposure_state = UNEXPOSED
```

Production effects:

```text
main_merge = 0
production_db_mutation = 0
production_scheduler_change = 0
production_telegram_send = 0
monitoring_registration_calls = 0
live_structured_autonomy_activation = 0
live_v2_change = 0
night_futures_code_mutation = 0
```

## Validation

| Check | Result |
| --- | --- |
| Focused source/holdout tests | `24 passed` |
| Full pytest | `2609 passed` |
| Ruff | `PASS` |
| `git diff --check` | `PASS` |
| Proof JSON count | 60 |
| Artifact index | `PASS` |
| Hash mismatches | 0 |
| Size mismatches | 0 |
| Secret-scan failures | 0 |

Machine-readable authority lives under `proofs/`, especially artifacts 07 through
14 and `60-program-completion.json`.
