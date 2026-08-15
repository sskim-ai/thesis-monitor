# Phase 7.2.6 Authoritative Identity Readiness

## Status

- Branch: `codex/phase-7-2-relational-reasoning`
- Production main: `4ce7bb29d8698efa2ad1d31ce80f6e75efa411f8`
- Experimental policy: `daily-review-v3.10`
- Production policy: `daily-review-v3.9`
- Schema / structure / Pilot / renderer: `4` / `v2` / `v3` / `v3`
- Actual Pilot: KR `2/5`, US `1/5`
- Production Assist: disabled
- Main merge / operating deployment / task transition: not performed

The Phase 7.2.5 production documentation merge is preserved in experimental merge commit
`0e1a780b9b2e74697314871240b5762865cd3b82`.

Phase 7.2.6 implementation commits are:

- `a7515a47799c1f91c2b122785b780f1d7d0884c8` - authoritative trust, ingestion, and candidate selection
- `cc9d4f9948ec62724e8335e5622eb1ae750b7765` - conservative affirmative depositary compatibility
- `dc545e519c106a5b2ae47312c15526a4fbc3fc56` - packet and fallback provenance alignment
- `6ecbdf1e0d4fbb9d552901599033c7077ead3364` - deterministic split-context SEC cover-page resolution

The final branch commit and its exact GitHub Actions run are reported after the documentation
artifact commit is pushed; no self-predicted commit identifier is stored in this document.

## Root Cause And Fix

The old OpenFIGI path could accept the first ticker/name candidate. It stored a GOOGL CEDEAR and an
IBM commercial-paper instrument instead of the listed equity. Separately, inferred `domestic_us`
and `common_stock` defaults could be treated as verified non-depositary identity. SKHY's official
ADS identity and ratio were absent.

`security-identity-v2` now distinguishes authoritative, deterministic reference, explicit local,
and inferred/default evidence. OpenFIGI selects only one exact ticker/exchange/name/class/type
instrument, preserves the full candidate audit, and writes nothing on ambiguity. Official SEC
ingestion has field-level provenance, dry-run, rollback state, authoritative precedence, and
idempotent no-op behavior.

## Official Results

GOOGL is verified as Alphabet Class A common stock on Nasdaq from SEC accession
`0001652044-26-000071`. The isolated packet restores current PER `12.4x`, market-expected fPER
`19.29x`, and historical PER percentile `13%` because their independent lineage passes.

SKHY is verified as a Nasdaq ADS from registration `333-296987` and accession
`0001193125-26-299963`. One ADS represents `0.1` common share, stored with direction
`ordinary_shares_per_adr`. The current price `$166.33` and 20-day volume ratio `0.43x` remain.
PER, PBR, fPER, and historical percentile remain withheld because the current-ADS denominator,
share basis, and currency basis are not verified. No conversion or premium calculation occurred.

## US Retrospective

- New packet: `2026-08-15-us-run-18-a578d851c997`
- Completeness: market 1 plus stocks `13/13/13/13`
- Automatic / manual bindings: `161 / 0`
- Rejected bindings / formatter errors / unresolved placeholders: `0 / 0 / 0`
- Full validator: PASS, `0` errors
- Changed messages versus Phase 7.2.5: GOOGL and SKHY only
- Preview SHA-256: `b06819b9b7459a170a292f9a85bcd1f9fbd43991c6e332f1f514f5d4ceddabf3`

The pre-identity baseline had 162 bindings. GOOGL's three safe valuation claims return; SKHY's one
consensus fPER claim remains withheld, for a net result of 161. The Phase 7.2.5 safe conflict pair
still passes unchanged. The earlier unsafe pair remains rejected with four identity errors and no
unrelated errors.

## KR Regression

- Packet: `2026-08-14-kr-run-17-99bbafd73ab7`
- Completeness: market 1 plus stocks `7/7/7/7`
- Automatic / manual bindings: `141 / 0`
- Full validator: PASS, `0` errors
- Logical Telegram payload comparison: byte-identical across all eight messages
- Candidate Preview SHA-256: `3724ed999fc7bbc88796c82b33f6c041d072d23ebd470deb7d58faf2d8e55b0d`

The exact KRX listing assertion preserves existing KR identity without weakening the US default
rule. SK hynix financial taint, safe PBR, current price structure, and 1/5/20-day supply remain
unchanged.

## Safety

- Telegram sends: `0`
- Operating DB/archive/assessment writes: `0`
- Pilot mutations: `0`
- Scheduled Task changes: `0`
- Production main or operating checkout changes: `0`
- Production Assist changes: `0`
- Historical packet rewrites: `0`
- FX, ADR EPS, or premium calculations: `0`

The isolated source database SHA-256 remains
`23451ab3ac99b08b203c6dd736f31aac1ced1f1603be2a387d2ce2a0d22018a1`.

## Artifacts

- [Architecture](../architecture/SECURITY_IDENTITY_RESOLUTION.md)
- [Full US Preview](20260815-us-v310-authoritative-identity-preview.md)
- [US before/after](20260815-phase7-2-6-us-before-after.json)
- [US identity cross-section](20260815-phase7-2-6-us-identity-cross-section.json)
- [US numeric binding](20260815-phase7-2-6-us-numeric-binding.json)
- [US validator](20260815-phase7-2-6-us-validation.json)
- [Old packet replay](20260815-phase7-2-6-old-packet-replay.json)
- [OpenFIGI candidate audit](20260815-phase7-2-6-openfigi-candidate-audit.json)
- [GOOGL official evidence](20260815-phase7-2-6-googl-official-identity-evidence.json)
- [SKHY official evidence](20260815-phase7-2-6-skhy-official-identity-evidence.json)
- [CORZ official evidence](20260815-phase7-2-6-corz-official-identity-evidence.json)
- [HUT official evidence](20260815-phase7-2-6-hut-official-identity-evidence.json)
- [IBM official evidence](20260815-phase7-2-6-ibm-official-identity-evidence.json)
- [WULF official evidence](20260815-phase7-2-6-wulf-official-identity-evidence.json)
- [Full KR Preview](20260814-kr-v310-authoritative-identity-regression-preview.md)
- [KR byte comparison](20260814-phase7-2-6-kr-byte-comparison.json)
- [KR numeric binding](20260814-phase7-2-6-kr-numeric-binding.json)
- [KR validator](20260814-phase7-2-6-kr-validation.json)
- [Fallback matrix](20260815-phase7-2-6-fallback-matrix.json)
- [Isolation audit](20260815-phase7-2-6-isolation-audit.json)
- [Production remediation runbook](20260815-phase7-2-6-production-remediation-runbook.md)

## Remaining Gaps

1. Production SecurityMaster rows are intentionally unchanged. The official identity remediation
   must be separately approved and applied before v3.10 activation.
2. SKHY provider multiples remain a safe Unknown until current-ADS denominator/share/currency
   basis is verified. The official ratio alone is not enough.
3. TSM and WRD retain conservative affirmative depositary evidence, but their unverified
   current-security multiples remain withheld. CRCL and SNDK receive no invented missing metadata.
4. Phase 7.2 still requires explicit Work approval, main merge, production deployment, Scheduled
   Task transition, and a natural Live Pilot.
