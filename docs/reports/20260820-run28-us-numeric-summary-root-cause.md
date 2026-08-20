# Run-28 US Numeric Summary Root Cause

Date: 2026-08-20  
Packet: `2026-08-20-us-run-28-9024def294e6`

## Immutable Outcome

The AI candidate passed the earlier semantic, numeric, and final-language boundaries but the final
runtime receipt failed with `runtime_message_quality_gate_failed`. AI delivery was zero. The
deterministic fallback delivered 14/14 with zero pending. Original packet, candidate, receipt,
delivery artifacts, DB, and Pilot state were read-only.

## Root Cause

The workflow instruction required at least two earnings anchors. Sparse US packets therefore copied
`valuation:current` TTM EPS and BVPS into `business_earnings`. The business section then opened with
one portfolio-wide `현재 확인된 핵심 숫자는` scaffold. The typed audit found
`9` valuation-owned
business claims and one arity-independent repeated numeric-summary family.

Separately, `runtime_specificity_plan` treated every numerical RR improvement or deterioration as a
material candidate. Ten stocks rendered a standalone previous-RR/current-RR tuple. The old text-only
normalizer also merged WULF's current-PBR/historical-percentile tuple into the same bare numeric
shape even though its owner and economic relation differed.

## Repair

- Business numeric minimum: removed; actual `earnings:*` revenue/income/margin retained.
- Valuation TTM EPS/BVPS filler: suppressed; company-specific Unknown retained.
- RR pair: 6 material transition occurrences integrated into their price transition;
  4 non-material occurrences suppressed.
- Skeleton identity: section + owner + numeric semantic types + relation + text shape.
- Generic business summary: separately detected across one-, two-, and three-number arities.
- Duplicate threshold, gate, RR formula, chart structure, and zone exception: unchanged.
