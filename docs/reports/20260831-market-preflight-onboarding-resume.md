# Market Preflight Onboarding Resume

Contract: `market-preflight-onboarding-resume-v1`.

The daily producer invokes a market-scoped, cached-only last-chance resume before freezing its packet universe. It uses an 8-second bounded timeout, never fetches the opposite market, and never blocks already-ready peers. A same market/date cutoff is persisted so repeated preflight cannot duplicate work.

Activation after the frozen packet cutoff is excluded from that packet. Preflight has no Telegram, assessment-history rewrite, or direct active-state authority.
