# Track A — KR Local-First Digest Consumption Repair

## Objective

Repair only the KR afternoon/daily market-digest evidence consumption path.

Do not edit numeric registry ownership unless unavoidable for compilation.

## Required behavior

Priority:

```text
KOSPI/KOSDAQ direction
→ breadth
→ aggregate participant flow
→ size/style
→ material same-session sector
→ KR FX
→ prior/global macro as secondary
```

Run-40 facts were present but omitted. Acquisition must not be changed unless an actual defect is
proven.

## Hard gates

```text
KR_LOCAL_FIRST_DIGEST = PASS
MATERIAL_KR_LOCAL_EVIDENCE_LOSS = 0
PRIOR_US_BODY_REUSED_AS_KR_PRIMARY = 0
MARKET_FLOW_AS_FUNDAMENTAL_CHANGE = 0
SECTOR_RETURN_AS_SECTOR_BREADTH = 0
AI_FALLBACK_KR_EVIDENCE_OWNERSHIP_DIVERGENCE = 0
```

## Controls

Use immutable packet:

`2026-08-26-kr-run-40-706bc3003536`

Do not hard-code its values.

Do not emit concentration because run-40 reconciliation is unresolved.

Do not change Price Structure v3 or US Track A.

## Deliverables

Root cause, evidence ownership contract, exact before/after run-40 digest, evidence-utilization map,
focused tests, implementation SHA.
