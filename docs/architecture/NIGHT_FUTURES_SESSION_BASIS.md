# Night Futures Session Basis

Contract: `night-futures-session-basis-v1`

## Problem

Numeric provenance proves where a value came from; this contract also proves what trading session
and comparison basis the value means. A provider DAY return cannot be relabeled as a NIGHT return.

## Decision

Visible night-session change is:

```text
completed NIGHT-session price
- immediately preceding eligible DAY-session close/settlement
```

The backend performs the deterministic point and percentage calculations. AI and renderers do not
calculate or repair them.

KRX defines the night session as 18:00 through 06:00 and assigns its trading day by the 06:00 end.
The NIGHT row for trading date T is therefore paired with the preceding DAY session, normally T-1,
not with the later DAY row carrying T. See the [official KRX night-session rules](https://global.krx.co.kr/contents/GLB/02/0201/0201041004/GLB0201041004.jsp).

## Why

The previous same-`BAS_DD` pair was reverse chronological and produced a precise but semantically
wrong market signal. Explicit session and reference evidence prevents source labels from replacing
trading-session meaning.

## Required Evidence

Each promoted Fact must carry instrument, contract, exchange, `NIGHT` session type, session date,
reference `DAY` type/date/price, current price, change point/percent, as-of timestamp, provider,
source record identifiers, and exact source payload SHA256.

Current and reference contracts must match. Date alignment must use the exchange calendar and KRX
overnight trading-date semantics, including weekends, holidays and contract roll.

## Rejected Alternative

Provider change fields, same-date DAY/NIGHT pairs, user-observed values, AI corrections and renderer
calculations are not accepted as repairs when the comparison basis cannot be proved.

## Safety Constraint

Suppress the visible number when session or reference type is unknown, the reference is missing or
not earlier, contract identity differs, the session is stale, dates conflict, source identity/SHA is
missing, or the provider change-field basis is ambiguous. Missing values are never zero-filled.

Run-26's same-`BAS_DD` DAY/NIGHT pair is reverse chronological. Because the required 2026-08-19
NIGHT source row and exact raw payload could not be reconstructed, the retrospective result is
`UNAVAILABLE_BY_CONTRACT`.
