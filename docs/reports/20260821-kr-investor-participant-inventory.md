# 2026-08-21 KR Investor Participant Inventory

## Source

- Provider path: OHLCV Analyst -> Kiwoom official investor-flow endpoints
- Natural packet: `2026-08-21-kr-run-31-27d43ced72a0`
- Read-only audit calls: 7 requests, 7 successes, 0 failures
- Paid/new provider: 0

## Actual Fields

| Role | Canonical participant | Provider field |
|---|---|---|
| top-level, visible | foreign | `foreign_net_buy_qty` |
| top-level, visible | institution total | `institution_net_buy_qty` |
| top-level, visible | individual | `individual_net_buy_qty` |
| top-level, omitted | other corporation | `other_corp_net_buy_qty` |
| top-level, omitted | domestic foreign | `domestic_foreign_net_buy_qty` |
| institution diagnostic | financial investment | `financial_investment_net_buy_qty` |
| institution diagnostic | insurance | `insurance_net_buy_qty` |
| institution diagnostic | investment trust | `investment_trust_net_buy_qty` |
| institution diagnostic | other finance | `other_finance_net_buy_qty` |
| institution diagnostic | bank | `bank_net_buy_qty` |
| institution diagnostic | pension/public funds | `pension_fund_net_buy_qty` |
| institution diagnostic | private fund | `private_fund_net_buy_qty` |
| institution diagnostic | government | `government_net_buy_qty` |

Foreign holding quantity/ratio and holding changes are position metrics, not flow participants.

The provider exposes no separate aggregate-all-participants field in the observed response. The five
top-level participant fields are mutually exclusive and summed once. Institution diagnostics equal
institution total in all 21 audited windows; adding both would double-count.

The original run-31 archive retained only the visible three values, not the full raw participant
occurrence. A bounded same-date read-only query found later source-occurrence corrections for
Samsung Electronics and Hanwha Aerospace. This is tracked as source drift, not transformed into the
immutable packet. SK hynix matched the packet in all nine visible actor/window cells.
