# 11-kr-issuer-count-root-cause-and-reconciliation

| Field | Value |
| --- | --- |
| prior_fields | {"canonical_issuer_count": 2411, "remaining_unseen_supported_issuer_count": 2460} |
| root_cause | canonical_issuer_key removed every non-[a-z0-9] character from Korean names; empty names fell back to ticker while digit-bearing/ASCII fragments collided. The whole count collapsed 2539 securities to 2411 pseudo-name keys. During exclusion, 48 true excluded KR issuers plus 31 unrelated name-key collisions removed 79 securities, yielding 2460. |
| flawed_name_key_count_reproduced | 2411 |
| prior_remaining_security_rows_reproduced | 2460 |
| true_explicit_excluded_kr_issuer_count | 48 |
| false_exclusion_collision_count | 31 |
| kr_raw_reference_rows | 2539 |
| kr_supported_security_count | 2539 |
| kr_supported_issuer_count | 2539 |
| kr_unseen_supported_issuer_count | 2491 |
| issuer_key_namespace | OPENDART_CORP_CODE |
| membership_path | evidence/membership/kr-reference-membership.jsonl |
| kr_count_reconciliation_status | PASS |
| status | PASS |
