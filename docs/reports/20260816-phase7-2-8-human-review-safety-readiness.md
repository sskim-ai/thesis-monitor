# Phase 7.2.8 Human-Review Safety Readiness

## Status

Phase 7.2.8 is an isolated correction on
`codex/phase-7-2-7-live-quality-reconciliation`. Production remains at
`ff577e4a31d19f855d2f5c1ccb2eb10567244dc8`, policy `daily-review-v3.10`,
Pilot KR 2/5 and US 2/5, AI mode `shadow`, and Production Assist disabled.
This branch is not merged or deployed. Its Previews remain pending direct human approval.

The natural US packet `2026-08-16-us-run-20-6c15d0003955` remains an immutable,
exactly-once operational success with separate human-quality **FAIL** status. It is not
Production Assist evidence. No operational counter or archive was changed.

## Corrected Phase 7.2.7 Conclusion

The Phase 7.2.7 KR regression reused a v3.9 artifact from 2026-08-15, when KR was closed.
It therefore could not prove that current v3.10 financial-quality eligibility remained intact.
That Preview is retained as failed review evidence and is superseded for this acceptance question
by the current-code packet documented below.

## Root Causes And Repairs

| Area | Root cause | Deterministic repair |
| --- | --- | --- |
| SK Hynix financial leakage | retrospective selection / packet / financial quality | fresh v3.10 packet; denied direct earnings and dependent PE lineage stay unavailable |
| Market labels | canonicalization / numeric provenance / instrument identity | source-aware instrument labels; unknown instruments cannot use a first-label fallback |
| Zone endpoints | numeric provenance / formatter / role binding | required `lower` and `upper` roles with role-specific canonical labels |
| Identity prose | security identity / reasoning / validation | verified, unknown, and conflict states have separate prose contracts; rendered payload is audited |
| US section heading | renderer / knowledge routing | structural market-aware heading: KR supply, US volume and positioning |
| RR comparison | reasoning / numeric provenance / validation | direction words require occurrence-level previous/current or registered delta provenance |
| Korean particles | reasoning / quality audit | the binder rejects incorrect postpositions, including invalid connective combinations after a full numeric phrase |
| Repetition | reasoning / quality audit | substantive exact repeats, repeated template skeletons, generic next checks, and generic Unknowns are hard checks |

No ticker-specific production branch, broad renderer rewrite, validator relaxation, manual numeric
binding, database migration, or schema change was introduced.

## Current KR v3.10 Selection

- Selected assessment date: `2026-08-14`
- Run: `17`
- Phase/finality: `after_hours/final`
- Selection reason: latest eligible completed KR deterministic assessment; 2026-08-15 was closed
- Source database consistent-copy SHA-256:
  `06fc9e5f1f178d441a758bc37882730b4d5fe35efbc74d3a5ffd71d2c4a930b0`
- Current-code packet: `2026-08-14-kr-run-17-006189184b28`
- Provider/network calls: `0`
- Active/packet/output/rendered stocks: `7/7/7/7`

The seven tickers are `000660`, `003690`, `005490`, `005930`, `010120`, `012450`,
and `086280`. The packet applies schema 4, `daily-review-v3.10`,
`financial-quality-taint-v2`, and `security-identity-v2` from the current branch.

For SK Hynix, 13 user-facing entries are denied across direct earnings, growth/margin,
TTM EPS, trailing and modeled-forward PE, and historical PE. Independent price, OHLCV,
foreign/institutional 1-day/5-day/20-day supply, and verified book-value/PBR lineage remain usable.
The Preview contains no denied numeric or qualitative leakage.

## US Corrected Retrospective

The immutable live packet is the source; the isolated experiment packet is
`2026-08-16-us-run-20-a48638e987ce`.

| Check | Result |
| --- | --- |
| Completeness | market 1 + stocks 13 |
| Logical Telegram messages | 14 |
| Automatic bindings | 171 |
| Manual/rejected bindings | 0 / 0 |
| Formatter errors / unresolved placeholders | 0 / 0 |
| Full validator | PASS, 0 errors |
| Label/source/instrument/zone/particle mismatches | 0 |
| CRCL transition contradiction | 0 |
| Unsupported RR comparison | 0 |
| Identity/prose mismatch | 0 |
| US KR-style supply horizon | 0/13 |
| Unsupported US investor flow | 0 |
| Observer/holder distinct | 13/13 |
| Substantive repeat across 3+ stocks | 0 |
| Template skeleton repeat across 5+ stocks | 0 |

The binding count is 13 above the natural live count of 158 because each stock now grounds its
volume/positioning section with one canonical 20-day volume-ratio claim. CRCL consistently uses
`failed_breakout_to_not_reached`; it describes the current RR without claiming unsupported
improvement. SKHY remains a verified ADS with official ratio metadata, while its unverified
current-security denominator/share/currency multiples remain withheld.

TSM and WRD remain `unknown`. Production contains Tier C watchlist issuer metadata and Tier D
inferred `local+openfigi` SecurityMaster rows, but no authoritative identity cache. The Phase 7.2.6
cross-section had over-promoted that evidence. The corrected Preview uses neutral current-security
language and performs no ADR ratio, FX, EPS, or premium calculation.

## KR Corrected Retrospective

| Check | Result |
| --- | --- |
| Completeness | market 1 + stocks 7 |
| Logical Telegram messages | 8 |
| Automatic bindings | 141 |
| Manual/rejected bindings | 0 / 0 |
| Formatter errors / unresolved placeholders | 0 / 0 |
| Full validator | PASS, 0 errors |
| SK Hynix denied leakage | 0 |
| Numeric 1-day/5-day/20-day coverage | 7/7 stocks, both investor classes |
| Qualitative-only rows counted as coverage | 0 |
| Heading | KR supply, 0 mismatches |
| Observer/holder distinct | 7/7 |
| Substantive/template repeat hard failures | 0 / 0 |

Repeated KR six-horizon numeric layout, canonical zone endpoints, and the registered-rule warning
are explicitly classified structural safety contracts. Their linked facts and exception reasons are
recorded in the quality audit; generic next checks and Unknowns remain zero.

## Binder, Validator, And Fallback

Both markets use automatic binding only. Numeric registry ownership includes the instrument-aware
label, formatted value, source, unit, endpoint role, and exact occurrence. Missing or reversed zone
roles, redundant authored labels, unsupported comparisons, identity assertions, and invalid Korean
postpositions reject rather than being rewritten.

The deterministic fallback audit covers all 13 US and seven KR stocks. SK Hynix denied financial
leakage is zero; TSM/WRD definitive identity leakage is zero; neutral per-security basis warnings
remain. Persisted retry and single-delivery regressions remain covered. Telegram sends were zero.

## Isolation

The before and after hashes are identical:

| Artifact | SHA-256 |
| --- | --- |
| Live US packet | `83b33aa94f5c5428adb9cb7b0a6810142829ea2fa091c65265d7ec0c40180ec0` |
| Validated live output | `2b3fc7047fb716ea3535c3d2a94652e58ebc129e0ac65e8b6d7e6f91bcc5f621` |
| Archive completion marker | `ddce83e262e85e74d8459bb2d82795b5cd0b014699823a41e4aebaaa838179b6` |
| Pilot state | `4f8600322a5b08a9eb58708dbf9146854dd4b4f40b5ccd345892de8fdb064076` |
| Operating database | `419f8d2f7cc875b5379477f0ecc8582f85f49320c7a650158c5960c795bcc5d5` |

Telegram sends, operating DB writes, assessment changes, archive changes, Pilot changes,
Scheduled Task changes, API restarts, operating checkout changes, main merges, and Production
Assist changes are all zero.

## Artifacts

- [US full Preview](20260816-phase7-2-8-us-corrected-telegram-preview.md)
- [US numeric binding](20260816-phase7-2-8-us-numeric-binding.json)
- [US validator](20260816-phase7-2-8-us-validation.json)
- [US label/instrument audit](20260816-phase7-2-8-us-label-instrument-audit.json)
- [US quality audit](20260816-phase7-2-8-us-quality-audit.json)
- [KR full Preview](20260814-phase7-2-8-kr-current-v310-telegram-preview.md)
- [KR numeric binding](20260814-phase7-2-8-kr-numeric-binding.json)
- [KR validator](20260814-phase7-2-8-kr-validation.json)
- [KR label/instrument audit](20260814-phase7-2-8-kr-label-instrument-audit.json)
- [KR financial-quality audit](20260814-phase7-2-8-kr-financial-quality-audit.json)
- [KR supply audit](20260814-phase7-2-8-kr-supply-horizon-audit.json)
- [Identity and comparison audit](20260816-phase7-2-8-identity-comparative-audit.json)
- [Fallback audit](20260816-phase7-2-8-fallback-audit.json)
- [Isolation audit](20260816-phase7-2-8-isolation-audit.json)

## Remaining Gaps

1. Work must directly review both full Previews before any main merge or deployment.
2. TSM and WRD require separately approved authoritative identity ingestion to move from `unknown`.
3. The corrected branch has not been exercised by a natural Scheduled Task; that requires a later
   approved deployment.
4. KR local index, breadth, and market-wide investor-flow facts remain unavailable and are kept as
   concrete Unknowns.
