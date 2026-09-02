# Track B — Same-Contract Night Weekly / Monthly Aggregator

Resolve near-month using the existing roll policy.

Do not splice contracts.

For reference date D and selected contract C:
- Daily = D's valid NIGHT daily bar for C
- Weekly = same-contract valid NIGHT daily bars in D's XKRX week
- Monthly = same-contract valid NIGHT daily bars in D's XKRX month

Weekly/monthly:
O first / H max / L min / C last.

Label incomplete current week/month as IN_PROGRESS.

If contract roll means the contract did not cover the whole week/month:
label SAME_CONTRACT_PARTIAL_PERIOD.

Do not invent prior-week/prior-month return baselines.
Do not drop invalid constituents silently.

Run-51 screenshot control:
KOSPI200 202609, 2026/09/01:
O1061.00 H1061.40 L1031.30 C1040.50.
Compare, do not force.
