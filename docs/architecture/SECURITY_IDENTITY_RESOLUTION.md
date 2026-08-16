# Authoritative Security Identity Resolution

## Boundary

Security identity is a prerequisite for any valuation that depends on a per-security or
per-share denominator. A missing ADR flag, a local default, or a provider result selected only by
ticker is not proof that the listed instrument is a common share.

`security-identity-v2` keeps four states:

| State | Meaning | Security-basis valuation |
| --- | --- | --- |
| `verified_depositary` | Affirmative ADR/ADS evidence | Allowed only when the current-security denominator, share basis, and currency also pass |
| `verified_non_depositary` | Affirmative common/ordinary-security evidence | Provider-native multiples may proceed through the remaining lineage gates |
| `conflict` | Material evidence disagrees | Denied |
| `unknown` | Evidence is insufficient | Denied |

Identity and valuation eligibility remain separate. A verified ADS ratio proves the instrument
relationship; it does not authorize an EPS conversion, FX conversion, PER reconstruction, or
premium/discount calculation.

## Source Trust

Sources are ranked for resolution, while conflicting raw evidence is retained.

| Tier | Source | Permitted effect |
| --- | --- | --- |
| A | SEC filing, issuer filing, official exchange or issuer listing | May establish authoritative identity |
| B | Deterministically matched reference provider | May establish identity only after a unique instrument match |
| C | Explicit Watchlist/operator assertion with provenance date; exact KRX listing assertion | May establish the asserted identity |
| D | Inferred ticker class, default `domestic_us`, default `common_stock`, legacy boolean | Audit evidence only; never establishes verified identity |

An explicit Watchlist issuer assertion requires its stored creation timestamp and listing exchange.
An exact KRX assertion requires a six-digit ticker, KR country, KRX/KOSPI/KOSDAQ exchange,
`krx` issuer type, and common-security type. Legacy `local+openfigi` fields, including an affirmative
depositary type, FIGI, or ADR identifier, remain Tier D unless a higher-tier identity record verifies
them. They cannot create either verified state or unlock a multiple.

The packet records both the SecurityMaster record tier and the effective verification tier. This
prevents a Tier C assertion from being presented as an authoritative Tier A source.

## OpenFIGI Canonicalization

`openfigi-candidate-selection-v2` removes first-row fallback. Every returned candidate is audited
against ticker, issuer name, exchange/MIC, share class, market sector, security type, and stable
FIGI identifiers.

1. Only a unique exact instrument is selected.
2. Candidate ordering cannot change the result.
3. Equal eligible candidates are `ambiguous`; no SecurityMaster write occurs.
4. Ticker, issuer, exchange, class, sector, or type mismatches are rejected with reasons.
5. All candidates and rejection reasons are stored in `ProviderResponseCache`.
6. A Tier B result cannot overwrite Tier A identity; it is cached as audit-only.

This prevents the historical GOOGL CEDEAR candidate and IBM commercial-paper candidate from being
accepted as the Nasdaq/NYSE equity merely because they appeared first.

## Official Ingestion

`OfficialSecurityIdentityService` accepts structured evidence produced by reusable SEC cover-page
or ADS prospectus parsers. The evidence stores field-level value, source tier, provider, source URL,
filing accession or registration number, as-of date, verification status, and resolution reason.

Inline XBRL normally binds ticker, security title, and exchange in one context. If a filing splits
the ticker and title across contexts, the parser joins them only when one ticker exchange and one
title-only row resolve to the same canonical exchange. Any ambiguity fails closed.

The ingestion command is dry-run by default:

```bash
python -m app.jobs.security_identity_remediation \
  --evidence-json docs/reports/<official-evidence>.json
```

`--apply` is reserved for the separately approved production remediation. The operation returns
before/after state and a rollback snapshot, is idempotent, and becomes a no-op when the exact
authoritative identity is already present. Conflicting Tier A evidence is cached without overwrite.

## GOOGL And SKHY

GOOGL is verified from Alphabet's SEC cover page as Nasdaq Class A common stock. The old OpenFIGI
CEDEAR result is retained as rejected evidence. Its trailing PER, consensus fPER, PBR, and historical
percentiles return only because their independent financial and denominator lineage also passes.

SKHY is verified from the final 424(b)(4) prospectus as a Nasdaq ADS. The filing states that one ADS
represents `0.1` common share and identifies KRX `000660`. The ratio direction is stored as
`ordinary_shares_per_adr`. PER, PBR, fPER, and historical percentiles remain withheld because the
current provider values do not prove a compatible current-ADS denominator/share/currency basis.
No conversion or premium calculation is performed.

The ratio direction is metadata with its own fail-closed boundary. It is recorded only when the
identity is `verified_depositary`, the ratio is positive, a ratio source exists, and verified field
provenance confirms both the ratio and `ordinary_shares_per_adr` direction. Verified common stock,
unknown or conflicting identity, and depositary identity without a proven ratio all store a null
direction. A default direction must never be attached merely because the field exists in the
contract.

## Packet, Binder, Validator, Fallback

The AI packet recomputes compatibility fields from the canonical identity, so legacy
`resolved_security_type` or `is_depositary_security` values cannot contradict the v2 state.
Identity metadata is exposed as the homogeneous `security_identity:current` Fact. Current-security
denominator, share, and currency status is exposed separately as `security_basis:current`; a
verified ADS identity must not be described as unverified merely because a multiple is withheld.

Identity-ineligible numeric registry rows have `prose_allowed=false`, no display value, and no
approved variants. Binder references, raw numeric prose, qualitative multiple inference, and mixed
aggregate valuation bypasses remain fail-closed. A concrete number-free identity Unknown is allowed.

Deterministic fallback uses the same quality boundary. It retains independent price, chart, volume,
issuer financial, and KR supply facts while withholding unverified multiples and their cheap/expensive
interpretations. Persisted retry and single-delivery behavior are unchanged.

## Contracts

- No ticker-specific production branch; named securities are fixtures or evidence files only.
- No database migration or Public Action change.
- Output schema remains 4.
- Renderer performs no semantic rewrite.
- Historical packets and archives remain immutable.
- Production uses this contract under `daily-review-v3.10`. Phase 7.2.8 hardening remains isolated
  on its review branch until separate merge and deployment approval.

## Natural Live Reconciliation

The 2026-08-16 natural packet resolved TSM and WRD as `unknown`. Their production SecurityMaster
rows were `local+openfigi`, `identity_quality=inferred`, Tier D, and had no authoritative identity
cache. A prior isolated cross-section had promoted the same legacy affirmative fields to
`verified_depositary`; that result is superseded. Runtime `unknown` is the correct fail-closed state,
and their multiples remain withheld. No production identity remediation was performed in Phase
7.2.7 or Phase 7.2.8.

Phase 7.2.8 extends the boundary through the final rendered payload. `verified_depositary` may use
ADR/ADS wording only when that state is canonical; `verified_non_depositary` may use verified common
share wording; `unknown` and `conflict` must use neutral current-security wording. Identity and
current-security denominator/share/currency basis remain independent. Authoritative depositary-ratio
prose additionally requires a positive ratio, direction, and verified Tier A field provenance.
Fallback follows the same matrix.
