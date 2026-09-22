# M12DS-R6 Information Coverage

Status: LOCAL IMPLEMENTATION, fresh proof and human review pending. No deployment.
Instruction commit: `cfb6f939858a2b87be70c4f46a4b51eaf068aee5`.
Accepted policy baseline: `2097645892e30d84aba435416f98e7f9545a87fa`.

## Ownership

- US index rows remain the existing SPY/QQQ/IWM ETF proxies. Levels use USD, not
  cash-index points. The market OHLCV owner selects the actual completed XNYS
  session row and its immediate previous session. It never shifts a future date.
  Explicit finality or the existing provider-native historical-row finality is required.
- Corrected completed observations retain the superseded occurrence in raw evidence.
- FRED remains the numeric source for WTI and Treasury 3Y/5Y/10Y/30Y. The official
  series publication page supplies the expected latest observation, publication
  timestamp and next release date. Cached/missing/overdue metadata fails closed.
  H.15's release clock is 16:15 America/New_York; WTI has no verified clock and
  therefore fails closed from the start of its next declared release date.
- Daily observation frequency does not imply daily publication. The verified
  WTI metadata on 2026-09-22 declared observation 2026-09-15, publication September
  16 and next release September 23. No arbitrary age threshold is introduced.
- Current-context permission does not rewrite `today_signal_eligible`, important
  changes, stock feedback, or accepted judgment policy. It is source-receipt bound.
- Broad US sector ETF returns are ranked separately from the SOXX subindustry
  proxy. KR uses the existing sector applicability classifier and separate
  KOSPI/KOSDAQ universes. Rank by same-session numeric return, ties by canonical
  fact ID. TOP/BOTTOM means relative ranking, not necessarily positive/negative sign.
- Stock quote as-of and active support/resistance consume `current_price_context`.
  Partial aggregate chart availability does not hide a valid timestamp or the
  available side. Missing sides remain unresolved. Neither side replaces
  fundamental entry or tactical watch, and accepted decisions are unchanged.
- KRX month backfill is explicitly opt-in for this isolated proof. It uses the
  existing official endpoint, raw-response cache, normalization and same-contract
  aggregation. It does not activate additional production scheduler requests.
- Weekly/monthly OHLC remains visible when return-baseline evidence is absent.
  Included/elapsed sessions and exact missing dates are shown; future sessions
  never count as missing. Daily formatting is unchanged.

## Verification Boundary

All restored numbers use deterministic typed claim ownership and source hashes.
Market AI prose remains numeric-free. `m12ds_r6_market` extends current-context
eligibility only; stock policy, model, effort, schema and bounded transport are
the accepted R4-R4 owners. R6 must freeze after full offline validation and before
new source/inference. No old candidate is substituted for a fresh result.

The historical scope guard permits only the exact receipt-projection insertion
and individually hashed R6 source-owner changes descending from the instruction
commit. Any further byte change is rejected. Old scope failures remain failures
for unrelated owners; no global allowlist or threshold relaxation is added.

## Official Publication References

- https://www.federalreserve.gov/releases/h15/
- https://fred.stlouisfed.org/series/DGS10
- https://fred.stlouisfed.org/series/DCOILWTICO
- https://www.eia.gov/dnav/pet/pet_pri_spt_s1_d.htm

Final acceptance requires new fresh Market2/Core8/A8/B8 completion, exact 24
production-renderer captures, all coverage/lineage checks and human review.
Main merge, push, deployment and all production side effects remain forbidden.
