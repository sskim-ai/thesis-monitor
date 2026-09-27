# FPI Discovered Exhibit Phase 2

Contract: `FPI_DISCOVERED_EXHIBIT_PHASE2` (opt-in source proof only).

## Authority

The first phase has a frozen candidate/index/primary request manifest. Its sealed
result ZIP and member manifest bind exact discovery diagnostics to captured SEC
responses. Phase 2 replays the existing exhibit selector against those bytes.
Only already-discovered, selector-eligible same-issuer/accession documents enter
a new immutable manifest. No network lookup participates in manifest generation.

`SEC_FPI_MAX_PHASE2_EXHIBIT_DOCS_PER_SUBJECT = 3` is a uniform resource ceiling,
fixed before network access. It accommodates three captured-source exhibit
references without allowing an open-ended crawl. It is not a coverage target.
Duplicates do not consume slots; overflow remains
`FPI_PHASE2_EXHIBIT_BOUND_EXHAUSTED`, never a reason to raise the cap.

Supported path types: HTML, XML and text. Response MIME must independently be a
supported text type. Image/PDF/OCR documents cannot supply financial evidence.

## Frozen Execution

The plan binds parent/security/issuer/accession identity, phase-1 ZIP and receipt
hashes, original filing metadata, exact URL, request identity/order, inspection
purpose, timeout and retry budget. Each individual request manifest is frozen
before any provider call. No response-dependent URL is followed.

Execution is sequential. This implementation attempts every frozen entry; it
does not implement the optional qualified-selection early-stop optimization.
Independent per-document failure does not terminate other planned entries.
Timeout is 600 seconds with at most two byte-identical transient retries.
No identity, period, purpose, schema, quality or other semantic retries occur.
4xx provider denials are non-retried document failures in this opt-in phase;
the original reader's production/default authorization-stop behavior is unchanged.
Identity, secret/config, manifest and budget drift stop the phase.

## Financial Consumption

Verified source bytes enter the existing purpose classifier, economic-period
selector, foreign occurrence parser, comparison quality owner and complete stock
owner. No new concept mapping, issuer exception, magnitude ranking, period
inference or quality threshold is introduced. Historical unresolved acquisition
denials remain unless the existing owner actually resolves them. New phase-2
transport/type/budget incompleteness remains visible and cannot authorize PASS.

An empty phase-2 manifest generates a zero-call receipt. If phase-1 financial
purpose remains unavailable, the combined bounded blocker is
`NO_FINANCIAL_PURPOSE_SOURCE_WITHIN_PHASE1_AND_NO_PHASE2_ELIGIBLE_EXHIBIT`.

## Non-Effects

No production dispatch registration, financial persistence, new discovery,
OpenDART/OHLCV/Alpha/Massive, model, Market/Core/A/B, message renderer, Telegram,
scheduler or deployment action. Nineteen qualified REV3 subjects are exact
result/packet controls. All 22 are replayed offline before and after acquisition.
Fewer than 22 complete subjects cannot authorize the subsequent 24-message run.
