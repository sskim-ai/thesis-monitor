# START HERE — M12DS-R6-R4

R6-R3-REV1 result:

- Kiwoom usa06012 official schema confirms:
  - 미국주식 일 차트
  - dated daily row
  - row-local cur_prc = 현재가(종가)
- Therefore DAILY ROW CLOSE semantic is already PASS.
- Remaining US issue: regular-session finality + actual 08:05/10/15/20 cutoff availability.
- Direct SPY/NA failure was wrong/unresolved exchange routing; do not repeat it.
- Alpha Vantage current account is insufficient; do not call Alpha in this task.
- KR post-close sector authority is PASS for both KOSPI/KOSDAQ, with exact parity and
  deterministic TOP3/BOTTOM3.

Next:
1. recover canonical Kiwoom exchange routing for all US ETF symbols;
2. search existing exact 08:05-era raw receipts first;
3. prove usa06012 completed daily row is not mutated by extended-hours, using official
   semantics + bounded cross-context evidence;
4. if historical cutoff evidence is absent, prepare/run a manual read-only observer at the
   next 08:05/10/15/20 window; do not enable schedulers;
5. after finality + cutoff PASS, full US universe + sector ranking;
6. carry fresh KR post-close owner;
7. fresh Market/Core/A/B;
8. exact 24/24 messages for human review.

Transport for model requests:
- 600s
- up to 2 byte-identical transient retries
- max 3 attempts

No Alpha Vantage.
No new provider.
No production send.
No main merge.
