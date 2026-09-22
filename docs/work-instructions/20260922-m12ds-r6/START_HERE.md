# START HERE — M12DS-R6

R5-R2 is fully integrated to main:
2097645892e30d84aba435416f98e7f9545a87fa

Before onboarding, restore the user-facing information that regressed from the
market/stock messages:

US market:
- major index block
- WTI
- Treasury 3Y / 5Y / 10Y / 30Y
- deterministic sector +TOP3 / -TOP3

KR market:
- deterministic sector +TOP3 / -TOP3 with proper KOSPI/KOSDAQ taxonomy ownership

Stocks:
- explicit technical support
- explicit technical resistance
- tactical watch zone remains separate
- fundamental range remains separate
- price as-of when source-owned

KRX night:
- daily unchanged
- weekly IN_PROGRESS OHLC must render instead of `자료 부족`
- monthly official KRX history backfill from month start through reference date
- same contract only
- expected-session calendar
- future dates not treated as missing
- no Kiwoom substitution

Do not change investment judgment policy.

After offline tests:
fresh current Market/Core/A/B -> exact 24 message capture -> human review.

No main merge in R6.
After approval integrate R6, then begin M12DT onboarding.
