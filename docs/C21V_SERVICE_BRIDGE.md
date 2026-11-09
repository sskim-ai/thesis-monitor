# C21V: staged service bridge, no deployment

The Analyst companion patch adds a request-local sync sender to the real
FastAPI handler -> OhlcvService -> KiwoomAuth/KiwoomClient path. General routes
retain their old defaults. A protected GET without private enrollment cannot
fall back to the unmetered route. No new enrollment HTTP endpoint exists.

The host adapter resolves original OperatorApproval and ProspectiveOwner state,
and requires additional explicit native-GET consent for the exact typed plan.
It pins the companion service implementation before accepting its opaque
enrollment. Public JSON, a V1 Parent and a caller callback cannot mint a root.

## Implemented boundaries

- One cohort sender: authentication, lookup, chart continuation and KR flows.
- Atomic cap immediately before a physical attempt, within the existing Lane
  slot; no retry, redirect or default HTTP transport in offline tests.
- Sticky stop on physical/envelope/page/concurrent failure. Source proof binds
  query, nonce, body, page hashes, cumulative count, account/app-key identity,
  issuer/caller, generation and loaded implementation/config fingerprints.
- The account hash identifies an application key, NOT an investment account.
- The host preserves raw response replay, then checks the existing completed
  projection. It never repairs dates, manufactures finality or grants price,
  valuation, model or investment-direction rights.

## Explicit limitations

No current original registration was read or issued, no LIVE root was minted,
and no service was installed/restarted. The bootstrap implemented here accepts
an actual private service enrollment object in the same trusted process. It
does NOT yet transport an opaque enrollment between the separately installed
Analyst and Monitor processes. In particular its PID check deliberately denies
a foreign-process handle. Both repositories use the `app` package namespace;
they are not silently co-imported or renamed to pretend this is solved.

The existing external checkout has uncommitted host-Lane/maintenance wrappers.
This companion branch is based on pinned GitHub HEAD, not a replacement for
that checkout. Before installation, integrate those wrappers without nesting
the same Lane slot around the protected sender. No such installation is
authorized here. The existing configured Lane is mandatory for LIVE enrollment;
it is not initialized or reset by the bridge.

Actual KR service bars omit completion/settled-close provenance in OhlcvBar.
The unchanged completion owner therefore denies them. The synthetic US fixture
has a later chart row and demonstrates only the original historical-finality
rule for 2026-11-06, not a fresh settled close. No finality marker is fabricated.

These limitations prevent claiming a live-ready two-market canary or complete
host enrollment. The service-side implementation and offline wire tests are
useful, but overall C21V remains PARTIAL. Default OFF, NO-SEND, READY 0/22.
