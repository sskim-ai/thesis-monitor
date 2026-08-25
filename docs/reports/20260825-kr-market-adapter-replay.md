# KR Market Adapter Replay

- Source: immutable run-38 packet, no archive rewrite
- Assessment cutoff: `2026-08-25T07:06:11.582752+00:00`
- Repaired valuation candidate: hard validation `PASS`, errors `0`
- Expected slots: digest `1` plus stocks `7`
- Delivery performed by replay: `0`

## Adapter Result

| Field | Result |
| --- | --- |
| Local indices | `0`, explicit unavailable |
| Breadth | `UNKNOWN` |
| Size/sector | `0`, explicit unavailable |
| Market-wide flow | `0`, explicit unavailable |
| Deterministic local relations | `0` |
| Session | `after_hours`, final |
| Provider publication | `UNKNOWN` in packet; no zero substitution |

The common candidate remains reachable after the Stage A valuation-ref repair. The adapter adds no
unsupported number to digest or stock previews, and deterministic fallback remains available.

- `KR_MARKET_ADAPTER_VALUE_ADD = NO_MATERIAL_VALUE`
- Reason: the immutable packet has no new domestic structured context to consume.
- Safety value: the adapter makes that absence explicit without blocking delivery.

