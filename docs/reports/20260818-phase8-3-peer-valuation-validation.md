# Phase 8.3 Peer / Sector Valuation Validation

## Repository

| Item | Result |
|---|---|
| Branch | `codex/phase-8-3-peer-sector-valuation` |
| Base | `b94f709eb146655a6a2e35377073727aee7cd7ca` |
| Master Workflow v3 sync | `82b95cd` |
| Implementation | `37a785448b2d9e7506beb2aef84e08e5bfb6e5fb` |
| Final documentation | resolve branch `HEAD` |
| Push | experimental branch only |
| Main merge | 0 |
| Operating deployment | 0 |
| DB migration | 0 |
| Telegram | 0 |
| Pilot mutation | 0 |
| Scheduled Task run/config change | 0 |
| Production Assist | OFF |

Operating `main` remains `e925ee05eabcc1e89c74dfb1ec0d2dabbb01729d`; Phase 8.3 is not
present in the operating checkout.

## Master Workflow Sync

The first commit synchronized all four persistent handoff artifacts before implementation. It
separated the operating Phase 8.5.x baseline, KRX 8.2A.x publication-observation branch, and Phase
8.3 development branch. KRX 20:27/21:02/21:06 empty-200 evidence remains publication timing
`UNKNOWN`, not a generalized T+1 conclusion. Natural AI-assisted delivery remains PARTIAL.

After implementation, persistent docs now classify Phase 8.3 as `STRONG PARTIAL`, validated
experimental and not deployed.

## Capability

The current provider is `validated_active_monitoring_assessments`, not the full market. The immutable
2026-08-18 archive has 20 assessments: 7 KR and 13 US.

| Metric source coverage | Count |
|---|---:|
| trailing PER value | 13 |
| trailing PER not meaningful | 5 |
| trailing PER unavailable | 2 |
| PBR value | 18 |
| PBR unavailable | 2 |
| consensus forward PER value | 9 |
| modeled forward PER value | 3 |
| modeled forward PBR value | 5 |
| safe user-visible peer states | 0 |

Raw multiple availability did not bypass taxonomy, issuer, date, basis, denominator, period, sample,
or industry gates. There is no broad point-in-time peer valuation provider in the repository.

## Contract Validation

`peer-sector-valuation-v1` and `verified-profile-peers-v2` add:

- verified taxonomy -> sub-industry -> industry selection;
- same-market preference and sector fallback as LOW/audit-only;
- reliable `canonical_company_id` issuer deduplication;
- subject `price_as_of` exchange-session alignment, including 2026-08-18 KST assessments using the
  completed 2026-08-17 XNYS session;
- negative EPS/equity, stale date, period mismatch, provider conflict, security identity, and
  ADR/share-basis exclusions;
- separate trailing, consensus-forward and modeled-forward distributions;
- median, mean, quartiles, IQR, range, relative multiple, premium/discount and peer percentile;
- HIGH >=5, MEDIUM 3-4, LOW <3 or broad-sector quality;
- industry guardrails and no automatic cheap/expensive conclusion.

Ticker-specific peer lists: 0. Renderer calculations: 0. AI calculations: 0.

## Mandatory Fixtures

### KR

Samsung, SK hynix, POSCO Holdings, Hyundai Glovis and Korean Re all fail closed with
`insufficient_verified_peer_universe`. SK hynix denied P/E remains denied. No US ADR is used to fill
a KR same-market sample. Steel PBR and insurance PBR are not converted into automatic cheap calls.

### US

- MU: technology sector fallback only, LOW and suppressed;
- TSM: depositary P/E/PBR basis unsafe and suppressed;
- TSLA: insufficient automotive peer sample;
- RXRX: biotech generic PER/PBR peer valuation not meaningful;
- CORZ: negative EPS and negative equity control;
- GOOGL: broad technology sector fallback LOW and suppressed.

## Statistics And Audit

Synthetic deterministic fixtures validate MEDIUM and HIGH samples, issuer duplicate weighting,
same-session comparison, stale and period exclusions, consensus/modeled separation, negative
denominators, provider/security conflicts, sector suppression and biotech suppression. Every
candidate preserves issuer/security IDs, taxonomy, metric value, as-of date, source, basis,
eligibility and exclusion reason in the audit.

The complete immutable audit is
[20260818-phase8-3-peer-audit.json](20260818-phase8-3-peer-audit.json).

## Numeric Provenance

Canonical summary fields extend `valuation:peer` with relative multiple and peer cross-sectional
percentile. New semantics are distinct for PER/PBR and never reuse own-history percentile:

- `peer_pe_relative_multiple` / `peer_pb_relative_multiple`;
- `peer_pe_cross_section_percentile` / `peer_pb_cross_section_percentile`.

Synthetic visible peer claims have exact `fact_id`, `field_path`, raw value, unit, semantic and binder
label coverage. Minimum typed peer sample is enforced at 3. Numeric provenance: `PASS`.

## Human Preview

KR and US archive-only previews compare the Phase 8.5.x baseline with Phase 8.3. Because no safe peer
Fact exists, all selected valuation blocks remain unchanged and no empty peer section is emitted.

- message character delta: 0 for selected valuation blocks;
- peer Fact dump: 0;
- sector fallback mislabeled as industry peer: 0;
- relative multiple used as automatic verdict: 0;
- biotech PER attractiveness: 0;
- insurance low-PBR cheap conclusion: 0;
- memory low trailing-PER cheap conclusion: 0.

Human quality: `PASS_FAIL_CLOSED`. The Preview does not claim that missing provider coverage is a new
investment insight.

## Validation

| Check | Result |
|---|---|
| Peer/monitoring focused | 22 passed |
| AI/typed/numeric/semantic focused | 252 passed |
| Industry reasoning focused | 47 passed |
| Security/valuation focused | 47 passed |
| Full pytest | 1,079 passed, 1 dependency deprecation warning |
| Ruff | PASS |
| Diff check | PASS |
| Investment Knowledge SHA | `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18` |
| Chart Knowledge SHA | `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b` |
| Public Action | 0.4.5 |
| operationId | 20/20 unique |
| Implementation GitHub Actions | run `32139654699`; exact SHA `37a785448b2d9e7506beb2aef84e08e5bfb6e5fb`; Test PASS; Lint PASS |
| Final branch GitHub Actions | exact final SHA result verified before final completion |

The warning is Starlette's existing `httpx` TestClient deprecation; it is unrelated to Phase 8.3.

## Natural And KRX Status

No newer natural US/KR artifact was available at phase start. Natural AI-assisted delivery remains
PARTIAL. KRX historical capability/universe/readiness contracts remain unchanged; 16:05, 08:05 and
T+1 roles remain `NOT_YET_PROVEN`, historical remains `SUPPORTED`, and KRX code remains experimental.

## Persistent Gaps

| Gap | Status |
|---|---|
| Peer/sector contract and safety | CLOSED experimental |
| Broad point-in-time peer provider | OPEN |
| User-visible active-universe peer coverage | OPEN; 0/20 |
| Industry taxonomy coverage | PARTIAL |
| KRX publication timing | PARTIAL |
| Natural AI-assisted delivery | PARTIAL |
| Cash conversion | PARTIAL/OPEN |
| Production evidence | INSUFFICIENT |

## Recommendation

First review the next natural US/KR AI-assisted result and the next exact-slot KRX publication
observation. Then decide whether a broad point-in-time peer provider has sufficient coverage, basis
quality, cost and rate-limit value to extend Phase 8.3. Do not promote an experimental feature whose
current safe user-visible coverage is zero merely because its contract tests pass. Any natural-live
operating blocker remains higher priority.
