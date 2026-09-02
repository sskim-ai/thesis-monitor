# Night Futures KRX Calendar Mapping

`night-futures-session-date-v2` uses the XKRX calendar and 06:00 KST finality boundary. It emits
the KRX regular business date, night-session end date, provider `BAS_DD`, UI start date, and an
independent US session date.

Focused tests cover normal sessions, weekends, Korean holidays, year boundaries, pre-06:00
observations, and a deliberately mismatched US session date. No rule hard-codes the KRX date to
the US session.

- KRX business-calendar mapping: `PASS`
- Finality gate: `PASS`
- Observation-date default: `0`
- US-session hard-code: `0`
