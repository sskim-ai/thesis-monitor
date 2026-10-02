# Same Legal Issuer Business Evidence Bridge

Contract: `same-legal-issuer-business-evidence-bridge-v1`.
This is an opt-in offline extension of the bounded financial stock owner.
Production dispatch, database identity reconciliation and valuation are unchanged.

## Identity

The current supported relationship is an authoritative SEC depositary identity
whose explicit ordinary-share identifier matches the source KRX security.
The existing qualified identity archive is frozen by hash. Its provider, tier,
CIK, instrument, underlying, exchange, accession, source URL, temporal and
field-level provenance must agree with the target security. A captured official
OpenDART listing response, replayed with its acquisition receipts, must identify
exactly the source security and corporation. Seed resolver output is insufficient.
Name equality, economic similarity and parent/subsidiary relationships are not
accepted crosswalks. Other identity source relationships remain unsupported.

Different internal company IDs are retained, not overwritten. A versioned legal
issuer crosswalk binds the two provider issuer IDs and exact identity receipts.
Missing master ratio/underlying values are never backfilled. Conflicting nonempty
IDs or identity warnings fail closed. A separately qualified historical identity
may establish issuer business ownership without granting any share conversion.

## Evidence

The original source stock owner is replayed, not trusted by its PASS label.
Only its selected and consumed reported revenue/operating-income/net-income
comparisons may be projected. Original quality, current/prior occurrence,
filing, period, currency, caution and source-use ownership are preserved.
The constructor remains `comparative_facts`; the original OpenDART issuer and
source ticker remain in its fields. An explicit
`ISSUER_LEVEL_CROSS_SECURITY_EVIDENCE` chain adds target security, legal issuer,
bridge receipt, original fact hash and source result hash.

The broader scope matrix describes possible issuer-level financial/event scope;
it does not implement new event, cash-flow or balance-sheet projection routes.
Denied originals stay denied, absolute context is not promoted to comparison,
and pre-existing native comparison ownership cannot be overwritten.

## Security Isolation

Only detached comparison facts and their existing numeric/evidence projections
are added. The target's existing stock fields and original facts remain identical.
Price, OHLCV, technicals, support/resistance, flows, share counts, EPS, PE/PB,
market capitalization, yields and valuation denominators never cross this bridge.
Per-share and valuation bridge eligibility are always false under this contract.

## Qualification

The 22-subject source proof is distinct from current live source qualification,
whole market packet assembly and AI/message validation. A source-only business
bridge PASS cannot by itself authorize a run, message, deployment or integration.
The separate full-source prequalification audit must retain unresolved market
or composition gaps. Raw evidence and receipts are local artifacts only.
