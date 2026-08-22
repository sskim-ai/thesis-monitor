# 2026-08-22 US Natural Production Review

## Scope and identity

- Evidence cutoff: `2026-08-22 09:30 KST`
- Packet: `2026-08-22-us-run-32-dde10ec6c9eb`
- Packet generated: `2026-08-22 08:20:04 KST`
- Policy/schema: `daily-review-v3.10` / output schema `4`
- Monitored stocks: 13; expected messages: 14 including the market digest
- Canonical production result: `deterministic_fallback`, sent `14/14`, pending `0`, failed `0`, duplicate `0`
- Terminal/Telegram dispatch time: `2026-08-22 08:40:04.711679 KST`
- Delivery-result SHA-256: `e88e6ef439acfee7dafb9c7e768e241ef7bba894ae4439cfe1855b5728ae6089`
- Exactly once: PASS. Pilot session is terminal `sent=true`; delivery IDs are unique `236..249`; the retry job later reported no pending AI delivery.

## Primary and backup path

The primary claim (`00f4d860-8091-40cd-8abd-3c9c18853376`) produced two rejected candidates at 08:24 and 08:26. The backup claim (`c9e25d2f-8b36-4679-af92-64467a40b916`, owner `codex-us-backup`, claimed 08:31:16 KST) produced two more rejected candidates at 08:42 and 08:50. The deterministic fallback became canonical at 08:40 because no validated AI output existed by the fallback deadline. The later backup artifacts could not supersede the terminal delivery and were archived as rejected evidence.

| Attempt | Path | Candidate completion | Validation completion | Numeric | Downstream result |
|---|---|---:|---:|---|---|
| 1 | primary | 08:24:30 | 08:25:06 | PASS, 122 auto / 0 rejected | REJECTED, 56 contract/semantic errors |
| 2 | primary correction | 08:26:37 | 08:26:51 | FAIL, 116 auto / 9 rejected | REJECTED before validated output |
| 3 | backup | 08:42:14 | 08:43:03 | FAIL, 125 auto / 1 rejected | REJECTED after fallback terminal |
| 4 | backup correction | 08:50:11 | 08:51:08 | PASS, 129 auto / 0 rejected | REJECTED, 21 contract/semantic errors |

No candidate reached a validated outbox artifact, so standalone runtime-quality and final-language PASS receipts are `NOT_REACHED`. The production fallback renderer completed safely and is the exact sent artifact.

## Exact hard errors

### Attempt 1, 56

```text
CORZ:cash_flow_primary_fact_not_declared
CORZ:cash_flow_business_owner_fact_missing
CORZ:cash_flow_primary_numeric_claim_count
CORZ:cash_flow_ppe_scope_label_missing
CORZ:cash_flow_ytd_label_missing
CORZ:resolved_cash_flow_unknown_retained
CRCL:cash_flow_primary_fact_not_declared
CRCL:cash_flow_business_owner_fact_missing
CRCL:cash_flow_primary_numeric_claim_count
CRCL:cash_flow_ppe_scope_label_missing
CRCL:cash_flow_ytd_label_missing
CRCL:resolved_cash_flow_unknown_retained
CRCL:cash_flow_valuation_owner_misuse
GOOGL:unsupported_cash_flow_metric
GOOGL:cash_flow_primary_fact_not_declared
GOOGL:cash_flow_business_owner_fact_missing
GOOGL:cash_flow_primary_numeric_claim_count
GOOGL:cash_flow_ppe_scope_label_missing
GOOGL:cash_flow_fiscal_period_label_missing
GOOGL:cash_flow_ytd_label_missing
GOOGL:resolved_cash_flow_unknown_retained
IBM:cash_flow_primary_fact_not_declared
IBM:cash_flow_business_owner_fact_missing
IBM:cash_flow_primary_numeric_claim_count
IBM:cash_flow_ppe_scope_label_missing
IBM:cash_flow_ytd_label_missing
MU:cash_flow_primary_fact_not_declared
MU:cash_flow_business_owner_fact_missing
MU:cash_flow_primary_numeric_claim_count
MU:cash_flow_ppe_scope_label_missing
MU:cash_flow_ytd_label_missing
MU:resolved_cash_flow_unknown_retained
RXRX:cash_flow_primary_fact_not_declared
RXRX:cash_flow_business_owner_fact_missing
RXRX:cash_flow_primary_numeric_claim_count
RXRX:cash_flow_ppe_scope_label_missing
RXRX:cash_flow_ytd_label_missing
SNDK:cash_flow_primary_fact_not_declared
SNDK:cash_flow_business_owner_fact_missing
SNDK:cash_flow_primary_numeric_claim_count
SNDK:cash_flow_ppe_scope_label_missing
SNDK:resolved_cash_flow_unknown_retained
TSLA:cash_flow_primary_fact_not_declared
TSLA:cash_flow_business_owner_fact_missing
TSLA:cash_flow_primary_numeric_claim_count
TSLA:cash_flow_ppe_scope_label_missing
TSLA:cash_flow_fiscal_period_label_missing
TSLA:cash_flow_ytd_label_missing
TSLA:resolved_cash_flow_unknown_retained
WULF:cash_flow_primary_fact_not_declared
WULF:cash_flow_business_owner_fact_missing
WULF:cash_flow_primary_numeric_claim_count
WULF:cash_flow_ppe_scope_label_missing
WULF:cash_flow_fiscal_period_label_missing
WULF:cash_flow_ytd_label_missing
WULF:resolved_cash_flow_unknown_retained
```

### Attempt 2, 9

```text
CORZ:numeric_fact_ref_redundant_authored_label:corz_cf_primary:business_earnings.text:free_cash_flow_ppe
CRCL:numeric_fact_ref_redundant_authored_label:crcl_cf_primary:business_earnings.text:free_cash_flow_ppe
GOOGL:numeric_fact_ref_redundant_authored_label:googl_cf_primary:business_earnings.text:free_cash_flow_ppe
IBM:numeric_fact_ref_redundant_authored_label:ibm_cf_primary:business_earnings.text:free_cash_flow_ppe
MU:numeric_fact_ref_redundant_authored_label:mu_cf_primary:business_earnings.text:free_cash_flow_ppe
RXRX:numeric_fact_ref_redundant_authored_label:rxrx_cf_primary:business_earnings.text:free_cash_flow_ppe
SNDK:numeric_fact_ref_redundant_authored_label:sndk_cf_primary:business_earnings.text:free_cash_flow_ppe
TSLA:numeric_fact_ref_redundant_authored_label:tsla_cf_primary:business_earnings.text:free_cash_flow_ppe
WULF:numeric_fact_ref_redundant_authored_label:wulf_cf_primary:business_earnings.text:free_cash_flow_ppe
```

### Attempt 3, 1

```text
GOOGL:numeric_fact_ref_raw_postposition:googl_rr_cur:price_positioning.text
```

### Attempt 4, 21

```text
CORZ:interpretation_unknown_fact_ids:chart:structure:risk_reward:current_price
CORZ:cash_flow_fiscal_period_label_missing
CORZ:cash_flow_ytd_label_missing
CRCL:cash_flow_fiscal_period_label_missing
CRCL:cash_flow_ytd_label_missing
GOOGL:cash_flow_fiscal_period_label_missing
GOOGL:cash_flow_ytd_label_missing
HUT:interpretation_unknown_fact_ids:chart:structure:risk_reward:current_price
IBM:cash_flow_fiscal_period_label_missing
IBM:cash_flow_ytd_label_missing
MU:cash_flow_fiscal_period_label_missing
MU:cash_flow_ytd_label_missing
RXRX:cash_flow_fiscal_period_label_missing
RXRX:cash_flow_ytd_label_missing
SNDK:cash_flow_fiscal_period_label_missing
SNDK:cash_flow_fy_label_missing
TSLA:cash_flow_fiscal_period_label_missing
TSLA:cash_flow_ytd_label_missing
WULF:interpretation_unknown_fact_ids:chart:structure:risk_reward:current_price
WULF:cash_flow_fiscal_period_label_missing
WULF:cash_flow_ytd_label_missing
```

## Production review

The fallback preserved all 14 messages and safely exposed canonical FCF for nine selected stocks. No wrong period, scope, currency, status mutation, valuation mutation, duplicate send, or unresolved delivery was found. The production AI path nevertheless has an open material P1: four natural candidates failed the current cash-flow/label contract, including three current-price RR Fact-ID errors in the final attempt. This did not become a user-visible correctness issue because the fallback gate worked.

Exact sent text and actual dispatch order are in `20260822-us-natural-sent-message-bundle.md`.
