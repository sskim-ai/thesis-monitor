# FMP EPS Qualification

REV43 is an offline-only qualification script, not a production provider. It
does not import into runtime packets, derive fPER, call models, or send messages.

The documented `/stable/analyst-estimates` route uses the exact symbol,
`period=annual`, `page=0`, `limit=10`, and an in-memory `apikey`. Public request
receipts are constructed from an allowlist, never from an authenticated URL.
No profile, price, alternate-provider, or test-time network requests are allowed.

## Ownership

`PeriodOwner` independently binds a completed fiscal year and period end to an
issuer source available by retrieval time. Selection uses the earliest annual
forecast after that period, not the maximum date or retrieval calendar year.
Already-ended candidate dates and missing next-year periods fail closed. A
provider annual date is preserved, not represented as an exact future 52/53-week
filing date. MU and SNDK fiscal year labels need their actual issuer periods.

Every row must identify the requested symbol. The existing monitored listing
owner supplies security identity; FMP is not claimed to supply CIK. EPS currency
follows reported financials according to FMP documentation, not quote currency.
`BasisProof` requires separately reviewed currency and listed-share evidence,
bound to the exact response hash. ADS qualification additionally requires an
explicit ADS series basis and a depositary ratio source. Ratio alone is never a
conversion license. No FX or per-share arithmetic is performed here.

Negative and zero estimates remain valid when qualified. Denied EPS values stay
null. Provider forecast date is not consensus update time: estimate-as-of stays
null. Accounting basis remains unspecified. Synthetic tests do not assert
actual provider coverage or entitlement.

## Acquisition Boundary

Stage A freezes documentation, credential capability, period/security owners,
and offline tests. Stage B requests GOOGL, MU and TSM once each. An entitlement
failure in GOOGL or MU suppresses the remaining eleven requests. Valid absent
coverage is distinguished from an account-wide access failure, but it does not
satisfy the positive smoke gate. Stage C requires affirmative common-share
qualification and a frozen implementation.

The private dispatcher reserves calls before network dispatch and seals every
response immediately. Parser fixes replay sealed bytes. Normal cap is 16,
absolute cap 18; this implementation is stricter and never goes beyond 16.
Optional transport retries require no valid body, at most one per ticker and
two overall; default execution performs no retries. A closed sentinel prevents
resuming a failed entitlement gate accidentally.

## Licensing and Evidence

Official API functionality is evaluated only for the user's stated private,
single-person, noncommercial research. A credential is not entitlement or a
redistribution license. Terms restrict sharing/display and contain additional
copy/download limitations. No raw FMP data is committed or placed in a cloud
report; local sealed bytes remain separate. The result records hashes and typed
outcomes and explicitly notes this reproducibility boundary. Future display,
redistribution, or production integration requires a separate license review.

Sources: [API](https://site.financialmodelingprep.com/developer/docs/stable/financial-estimates),
[pricing](https://site.financialmodelingprep.com/pricing-plans),
[terms](https://site.financialmodelingprep.com/terms-of-service),
[authentication](https://site.financialmodelingprep.com/developer/docs/quickstart).
