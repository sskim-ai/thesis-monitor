# 2026-08-31 KR V2 Message Quality

Evidence cutoff: 2026-08-31 17:38 KST. This is a read-only reconstruction of the natural run. No manual production job, send, retry, or database mutation was performed.

## Safe properties

- Korean fallback rendering: complete for 1 market + 8 stocks.
- Raw candidate exposure: 0; no candidate existed.
- Unadjudicated material decision exposure: 0.
- Empty visible sections: 0.
- 003690 prohibited self-transition wording present: `false`.
- Price Structure contract: PASS; valuation contract: PASS.
- Exact payload and exactly-once delivery: PASS.

## Material failure

No stock showed an explicit accepted V2 BUY/HOLD/SELL block, confidence, or selected timing. All eight messages were deterministic fallback output (`투자 논리: 유지` or onboarding baseline), not accepted V2 output. This is systematic V2 absence, which the instruction classifies as material P1.

```text
KR_003690_CHANGE_CONDITION_WORDING = PASS
KR_EMPTY_VISIBLE_SECTION_COUNT = 0
KR_V2_MESSAGE_QUALITY = FAIL
```
