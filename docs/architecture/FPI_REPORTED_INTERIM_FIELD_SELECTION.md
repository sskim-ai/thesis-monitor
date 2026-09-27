# Bounded FPI Reported-Interim Field Selection

REV5 is an opt-in extension of the existing reported financial projection and
stock source owner. Production dispatch and the default quarterly comparison
contract are unchanged.

## Ownership

- Exact statement table/caption/unit/cell lineage remains authoritative.
- Consolidated profit-or-loss captions and structural Renminbi/RMB units are
  supported generically. Canonical currency is CNY; no FX conversion occurs.
- An explicitly reported half-year may compare only to a compatible prior-year
  half-year. It is never materialized as a standalone quarter.
- Only existing exact revenue and operating-income row semantics are admitted.
  Unmapped profit/loss rows remain audit-only, including net income.
- Field selection uses economic periods and validated comparisons, not filing
  recency or amounts. A reviewed interim statement has priority over an
  unreviewed release for the identical field tuple. Ambiguous peers fail closed.
- Later explicitly nonfinancial filings do not supersede financial fields.
  Unknown later financial purpose and unavailable later field observations block
  the affected field. Unrelated fields can remain eligible.
- Exact embedded image assets inherit only the nonfinancial context of their
  captured parent IMG reference. Their contents are not interpreted, and they
  never supply financial facts.
- Historical acquisition defects remain in the audit. Only bounded document
  coverage defects wholly outside the selected field authority are scoped out;
  prior amounts must come from the selected statement's own comparative cells.

## Final Coverage Window

The generic owner permits exactly two windows of eight candidates from the same
sealed submissions inventory. Window two requires exhausted window one, no
financial source, no eligible phase-two exhibit, and additional sealed entries.
No new discovery, date expansion, overlapping window, or third window is allowed.

Window two freezes at most sixteen index/primary requests. After those terminate,
an independently frozen exhibit plan may admit at most three already-discovered
HTML/text/XML documents through the unchanged selector. Each logical request has
a 600-second timeout and at most two byte-identical transient retries. Maximum
total is 19 logical requests / 57 transport attempts. Semantic failures do not
retry; systemic identity/configuration/manifest/budget failures stop immediately.

Absence of financial evidence after both windows is a terminal coverage block,
not authorization for further crawling or omission of a monitored subject.

## Verification

`scripts/fpi_residual_window_proof.py` verifies immutable REV4/REV3/REV2 sources,
recomputes all 22 packets, and requires exact invariance of the 19 control results.
Network dispatch is separately frozen after exact-SHA full offline validation.
No model, render, send, production persistence, scheduler, deployment or remote
Git operations are performed by this campaign.
