# KR/US Bounded Quality Artifact Index

Date: 2026-08-26 KST
Instruction commit: `8cf5226ca0c5ae5553fb06b24399462ea3cf6088`
Implementation commit: `f2326c39485e600bca2cee15747deeb8465c5c8a`

## Report Bundle Inventory

| SHA-256 | Artifact |
|---|---|
| `037bdaf875078cd6fc964800dc5a3b427ecb1c3d174f78040006da8ba02aa0c8` | `docs/work-instructions/20260826-kr-market-digest-prioritization-us-entity-specific-synthesis-bounded-repair.md` |
| `eefcf76d93d5f2169f4acad760e7bd52085b32861d560927bd21ae8bbd14683f` | `docs/reports/20260826-kr-market-digest-prioritization-root-cause.md` |
| `71d5ee6d684f228ccdc0622b32ae0812b2e2467c247c707449077e9d9439ab4d` | `docs/reports/20260826-kr-market-digest-evidence-utilization-audit.md` |
| `18215db65f8311af9f253a49942e0565c7cc84b6e00087af7e371b63aa401029` | `docs/reports/20260826-us-entity-specific-synthesis-root-cause.md` |
| `b5b967e17308dad8767a5e166d0816b940abe943766f58aa7b3f77d5e051532b` | `docs/reports/20260826-us-cross-message-synthesis-specificity-audit.md` |
| `2aae783e2833eb287f2c595b76dfb0bca0ce4cd2f7e12e8e81ccb70d5a49eb31` | `docs/reports/20260826-kr-us-bounded-quality-exact-before-after.md` |
| `125bc06e2168bfe8f00f8214c81a07f21511fe1bf85a3369def63b9f84abcd57` | `docs/reports/20260826-kr-us-bounded-quality-safety-parity.md` |
| `1f8c516e0975cc1d18444be6cc71d81c1b665ee38f6cb28a161685122fd0e805` | `docs/reports/20260826-kr-us-bounded-quality-canary-simulation.md` |
| `0750dc68dc5a1b7c08d84e31c3ccf6b55501b7140a4c37cd40e1b3030962edb6` | `docs/reports/20260826-kr-us-bounded-quality-readiness.md` |
| `79d7ee8e5904e144ed3d09caf435ee9c10629c844fa5bd1101fb87ce206f3a8c` | `docs/reports/20260826-kr-us-bounded-quality-readiness.json` |
| `85ff0dcf6582cd8f05d5e3a72af27bee5984da1483e799ee68ce7c54a41c1d21` | `docs/reports/20260826-kr-us-bounded-quality-replay.json` |

The downloadable ZIP also contains a post-promotion completion report and a generated SHA-256
manifest. Those files are finalized only after the exact report commit, final main, operating SHA,
GitHub Actions status, and API health are known.

## Implementation Inventory

| SHA-256 | Artifact |
|---|---|
| `57f29f362b2162a68ff09b07de7477d42f8cc1aa0c8bce9d61d2efeb6f9c7cd2` | `app/services/kr_market_digest_quality_service.py` |
| `fdc8fb08c7636a508cabf874246b69c0f2ddd138297ab73b5104ded0635c347f` | `app/services/evidence_locked_free_analyst_service.py` |
| `0e1e2f12243945cc8744f7aefd7ad02877cac1b824fb362418d0096ebd8e1833` | `app/services/free_analyst_message_service.py` |
| `b2eacf5be1ba4537f640a4c65b2cd56bc95c300dca2a1912e45b247a73892c9e` | `app/services/free_analyst_production_integration_service.py` |
| `ddbf999df41858ca3c2b7d5d15f19e523e0cad230d0638222c72351d640a433c` | `app/services/adaptive_renderer_selector_service.py` |
| `6b8e759693684717153ddd7ca4fe59a52dc5ecb009cdaff8bd6781458ab46157` | `app/services/ai_assisted_delivery_service.py` |
| `7343e375fe9ff2ef1c659c7bd756996847554e2eced6a1334f4a32a226cb3e46` | `scripts/kiwoom_kr_enriched_replay.py` |
| `de9377f84c91b92201f73e3d565bff027a3dc80bf73ed373f0ad9e3fbc82f0ec` | `scripts/kr_us_bounded_quality_evidence.py` |
| `0ed1b65d3e76b6739c27296aefc8d7b837379ce31cd209b35f8e283b1b0024e8` | `tests/test_bounded_message_quality.py` |
| `850475bf3bf858b67ff3ec59e95897cc9822e14d2290702ce0fd4f48650bb4cb` | `docs/architecture/FREE_ANALYST_MESSAGE_QUALITY.md` |
| `7b7bb23b8c66bf8667bdf1461c7ec059e1f32f7fa8d5ac01f655969f47b2436e` | `docs/architecture/KR_MARKET_DIGEST_QUALITY.md` |
| `334bc695ce2599f9d9823974f778db96cdb4c783af3016993cd4b24b44928721` | `docs/architecture/FREE_ANALYST_CANARY_POLICY.md` |

`REPORT_SHA_CONSISTENCY = PASS`
