# M12DS-R5-R2 Final Review + Message Coverage Feedback

## Final R5-R2 status

The approved-resume result is a full success.

Terminal:

`M12DS_R5_R2_CI_PORTABLE_MAIN_INTEGRATED_POST_MERGE_PASS`

Final main/origin-main:

`2097645892e30d84aba435416f98e7f9545a87fa`

Final tree:

`436e41a4fb718d5be5dfda85a9423b555e1deb23`

Candidate CI:
- exact SHA PASS
- GitHub Actions run 35739161546

Main CI:
- exact SHA PASS
- GitHub Actions run 35740058754

Validation on candidate, clean clone and main:
- focused: 1553/1553 PASS
- full: 5206 PASS / 63 existing skips / 0 failures

Production-semantic mismatch:
- 0

Exact accepted-message replay:
- 24/24
- combined SHA-256:
  `e31d7f40576981c1f25df662f0865e1eb58e97cdb3921f9ba42230d6ad8c026e`

Night-futures exact replay:
- KOSPI200 PASS
- KOSDAQ150 PASS

Production writes/sends/deploy/scheduler/broker mutations:
- 0

The initial R5-R2 report correctly stopped before freeze because the approved
`fetch-depth` workflow change was not yet represented in old exact-scope provenance.
The separately approved resume closed that scope and completed main integration.

## Newly promoted message-coverage requirements

The previous P2 market/message gaps are now explicit user requirements and should be
closed before new-ticker onboarding.

### 1. US market factual block

Restore user-visible, source-owned market data that previously disappeared because of
session-date/freshness eligibility:

- canonical US major indices already owned by the production packet/renderer
  (at minimum preserve current canonical SPY/QQQ/IWM rows when valid; do not replace a
  canonical cash-index owner with an ETF proxy if the former already exists);
- WTI;
- US Treasury 3Y / 5Y / 10Y / 30Y yields;
- existing 10Y breakeven may remain as an additional macro field.

This is not permission to render stale facts.

Fix the actual date/publication ownership:
- US exchange observations use exchange-local session date;
- FRED-style daily macro series use provider-specific expected publication date/lag,
  not an unconditional same-day freshness rule;
- holidays/weekends must be handled explicitly;
- unavailable data remains unavailable with reason.

### 2. Sector TOP3 / BOTTOM3

Restore deterministic user-facing sector ranking blocks for both US and KR messages.

- US: top +3 and bottom -3 from the canonical eligible sector universe for the same
  completed session.
- KR: preserve KOSPI/KOSDAQ taxonomy/venue ownership. Do not combine incomparable
  sector taxonomies merely to create one ranking. Render the prior owned venue-level
  TOP3/BOTTOM3 contract, or if no prior single owner exists, render KOSPI and KOSDAQ
  separately.

Ranking must be deterministic:
- numeric return;
- same session;
- eligibility;
- stable tie-break;
- not model-generated.

### 3. Stock technical support / resistance

Internal `active_support` and `active_resistance` remain available but final messages
currently expose only a tactical watch zone.

Restore explicit:
- technical support range;
- technical resistance range;

when each is valid.

Keep all three concepts distinct:
- fundamental entry/fair-value range;
- technical support/resistance;
- tactical watch zone.

Do not fabricate a missing side.

### 4. Night-futures D/W/M

Daily is working.

Weekly currently has valid IN_PROGRESS OHLC but is rendered as `자료 부족` because a
complete-period return is unavailable. Change presentation to show the in-progress
weekly aggregate and included/expected session count.

Monthly is genuinely incomplete because prior official night-session history for the
month is not fully present in the packet. Backfill the current selected contract's
official KRX night history from month start through the reference date, using the
official expected-session calendar.

Rules:
- official KRX remains machine authority;
- no Kiwoom substitution;
- no cross-contract mixing without an explicit continuous-series owner;
- missing past expected sessions are reported exactly;
- future sessions are not called missing;
- partial/in-progress OHLC may be rendered honestly;
- if return baseline is unavailable, say return is unresolved rather than replacing
  the whole W/M block with `자료 부족`.

### 5. Existing P2 cleanup

Close if semantics-neutral:
- P2-PRICE-ASOF-PARTIAL
- P2-WORDING-CONSISTENCY

The old `P2-US-MARKET-COVERAGE` becomes part of the explicit R6 acceptance scope.

## Sequence recommendation

Do not start M12DT onboarding yet.

Next:
`M12DS-R6_MARKET_MESSAGE_INFORMATION_COVERAGE_RESTORATION`

R6 should implement on a clean branch from current main, generate a new fresh
production-equivalent 24-message capture with sends disabled, and return the exact
messages for human review.

After approval:
- integrate R6 to main with standard CI/reproof;
- then start M12DT onboarding.
