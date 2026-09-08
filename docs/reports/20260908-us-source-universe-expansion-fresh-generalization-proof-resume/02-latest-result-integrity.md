# 02 Latest Result Integrity

| Field | Value |
| --- | --- |
| expected_name | `thesis-monitor-20260908-directional-core-boundary-calibration-repair-fresh-generalization-proof-report.zip` |
| expected_sha256 | `f0a41371e12127a891165860f3c44ce6af7d1b8dcd13d0c5b93570618a075e6a` |
| observed_sha256 | `ab330fa13a53775ecdd162f36f4f7afeda42415db03bd0c766c48bf3a2eaddac` |
| companion_sha256 | `ab330fa13a53775ecdd162f36f4f7afeda42415db03bd0c766c48bf3a2eaddac` |
| expected_vs_observed | `FAIL` |
| observed_vs_companion | `PASS` |
| zip_crc | `PASS` |
| zip_member_count | `434` |
| indexed_payload_count | `433` |
| hash_mismatch_count | `0` |
| size_mismatch_count | `0` |
| secret_scan_failure_count | `0` |
| status | `FAIL` |
| stop_reason | `LATEST_RESULT_BUNDLE_CHECKSUM_MISMATCH` |

The observed ZIP is internally coherent and agrees with its adjacent checksum file, but it is not the byte identity frozen by section 1 of the new instruction. Filename equality and internal integrity do not override the required whole-file SHA-256 gate.
