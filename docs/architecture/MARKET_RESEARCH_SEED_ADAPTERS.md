# Market Research Seed Adapters

## Boundary

`market-research-seed-adapter-v1` provides market-specific vocabulary and primary-source hints to a
future common research engine. It contains no ticker rules, fixed queries, conclusions, numeric
Facts, or production side effects.

Common semantics remain source validation, entity validation, time validation, competing
hypotheses, negative evidence, and event attribution. KR and US differ only in source and session
vocabulary.

KR hints include disclosure, shareholder return, issuance, investor flow, KOSPI/KOSDAQ, sector,
governance, and policy categories, with OpenDART/KRX/issuer/regulator preference. US hints include
price moves, earnings/guidance, SEC filings, premarket/after-hours, sectors/peers, Treasury and macro
releases, analyst days, and regulation, with official-source preference.

Search discovery is not a numeric source. A discovered number must be verified against a supported
structured or primary source before it can become a canonical Fact.

