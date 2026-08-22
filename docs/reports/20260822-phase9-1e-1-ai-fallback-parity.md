# Phase 9.1E.1 AI/Fallback Parity

The AI packet and deterministic fallback use the same `working-capital-user-visible-v1` context.
Parity is enforced for packet ID, context ID, metric family, semantic scope, balance date, relation
ID/family, direction, display value, selected Fact IDs, resolved Unknowns, suppression reasons and
enablement state.

## Replay Result

| Ticker | Context | Relation | Value | Result |
| --- | --- | --- | --- | --- |
| 000660 | `wc-visible-bc3c309c423612cee3c9ff4f` | `working-capital-relation:38a9a0707d38e538ccdb2e7e` | `2.1%p` | PASS |
| 005490 | `wc-visible-ae235ff7cfb910a67512307a` | `working-capital-relation:ab1a9a616bcd8d6023b2db06` | `7.1%p` | PASS |
| 005930 | `wc-visible-531cf0c8fc120019d6e6d34a` | `working-capital-relation:4b43f129a5c3b9dbca52fa29` | `35.8%p` | PASS |

AI/fallback mismatches: `0`. Each selected relation has six identical lineage Fact IDs on both
paths. Final packet IDs are aligned before the deterministic payload is archived or held. A parity
mismatch raises a hard delivery error instead of silently choosing one path.

