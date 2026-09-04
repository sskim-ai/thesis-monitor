# 2026-09-04 KR/US Integration Conflict Audit

The branches shared a base but touched overlapping delivery, claim, quality, state, and documentation surfaces. Git merged both histories cleanly. Runtime replay then found a semantic integration issue: US typed-valuation hardening rejected six valid legacy KR interpretations.

The repair is bounded to deterministic semantic ownership:

- uniquely grounded historical P/B prose may acquire its canonical typed ref;
- uniquely grounded financial/book-quality unknown prose may acquire the matching quality ref;
- two exact neutral price/valuation summaries receive structural ownership;
- ambiguous directional multiple claims remain rejected;
- no message rewrite, threshold relaxation, or ticker/value hard-code exists.

Post-repair frozen KR, integrated KR TEST E2E, integrated US TEST E2E, focused tests, and full regression all pass. KR repair feature loss: `0`. US repair feature loss: `0`.
