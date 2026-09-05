# Cross-Market Validation and Infrastructure Matrix

| Case | Expected | Result |
|---|---|---|
| Healthy primary vs backup | Backup no-op | PASS |
| Stale primary reclaim | Bounded reclaim | PASS |
| Late AI after fallback | No duplicate | PASS |
| Terminal send plus late backup | No duplicate | PASS |
| Command timeout | Model child only | PASS |
| Authorized interruption | Terminal safe receipt | PASS |
| Benign typed repetition | Soft warning | PASS |
| Material repeated rationale | Semantic hard block | PASS |
| Weakening to invalidation escalation | Reject | PASS |
| Ineligible valuation evidence | Reject | PASS |
| Unsupported Unknown causal driver | Reject | PASS |
| `ANY_OF -> ALL_OF` | Reject | PASS |
| `ALL_OF -> ANY_OF` | Reject | PASS |
| One owned branch as example | Allow only non-exhaustive mode | PASS |

The focused logical-condition/production-policy suite passes 26 tests, related V2 integration regression passes 75 tests, the pre-existing targeted regression passes 350 tests, and the final full suite passes 2,227 tests. Real dedicated-sink E2E passes KR `1+8` and US `1+14`, with fallback and duplicates at zero.
