# R5F-R2A-REV1 Source Receipt and Acquisition Classes

Status: `M12DS_R6_R5F_R2A_SOURCE_RECEIPT_OWNER_GAP_REMAINS`.
This local, prospective change does not register a production adapter. Source,
AI, message, promotion and scheduler gates remain closed. The previous R2
result is preserved, not replaced with a passing source-cohort claim.

## Frozen Classification

`UNIFIED_ACQUISITION_CLASSES.json` was committed before implementation. It
declares 24 owner-derived role families, mandatory/optional status, original
freshness rules and retry policy. Per-symbol/per-timeframe expansion belongs
to the eventual concrete source adapter, not the AI prompt.

- A: recollect the whole required query-time price set for each attempt.
- B: acquire once in the run; keep original publication/session/acquisition.
- C: reuse exact persisted versions only after existing owner eligibility.
- D: explicit optional denial with no source value, zero, or fallback.

Optional A/B/C failure may produce D without changing the frozen intended
role. Mandatory A cannot become optional. No new freshness day threshold is
introduced. A historical night artifact is not a current-run B acquisition.

## Implemented

`unified_source_observer` is an explicit constructor dependency of
`OhlcvClient`. The frozen per-read plan contains exact symbol/period/adjustment,
target session, role and request budget. Every actual HTTP attempt is recorded,
including transport errors, HTTP errors and malformed-content refetches.
Intent, response bytes, response receipt and normalization receipt are separate
exclusive files. Headers, authentication material and exception text are not
exported. Secret-bearing response bodies are withheld and fail closed.

The existing decoder and OHLC integrity inspector own normalization. Gateway
source metadata must match the planned symbol/provider/adjustment; hidden or
undeclared upstream providers are rejected. A normalization receipt is
explicitly NOT completed-session authority or production source qualification.
`unified_source_replay` independently checks dates/basis/identity/request/raw/
normalized binding. It now rejects mock providers and ancestor symlinks too.

`unified_source_composition` seals B/C/D into immutable run bytes and hashes
the Class C seed separately. Every A/B input needs a bound acquisition receipt,
not mutable caller timestamps. Current owner projection/eligibility is replayed
from named artifacts at each cutoff; B/C source identity and owner-code hash
cannot change. Each A attempt supplies its entire role set. All components are
bound into the final snapshot hash. There is no caller packet patch, implicit
price cache, network, model, notification or production registration here.
`model_dispatch_qualified` is always false until separate adapter qualification.

The closed opt-in source policy applies to provider registry output, cached
financial rows, Alpha estimates/shares/overview and dividend/capital-return
selection. Valuation opt-in consumption does not refresh SEC/Finnhub/Alpha or
reuse historical statistics and event-driven freshness caches. Those owners
need independently scoped projection before they may be re-enabled. KR FX is
denied before existing-briefing reuse, DB reads/writes or notification dispatch.
Without an observer/policy argument, existing behavior remains unchanged.

## Evidence Limits and Open Owner Gaps

| Owner surface | State | Required next closure |
|---|---|---|
| Stock adjusted D/W/M and raw valuation read | Opt-in wire/normalization mechanism implemented | Expand real plan and verify full market/session/finality gates in a complete source cohort |
| US market OHLCV collector | Not yet instrumented | Its independent client discards responses; bind exact role observations to the shared observer and temporal owner |
| Kiwoom local indices/sectors/flow pagination | Not yet instrumented | Separate OAuth secret surface, every data retry/page, and completed page-set normalization receipts; current service archive aggregates successful responses only |
| Run-fresh news/calendar/breadth/night | Not yet run-bound | Thread run acquisition identity through distinct provider interfaces; capture failures as well as selected artifacts, preserving original times |
| Versioned universe/security/thesis/financial/macro seed | Composition mechanism only | Implement real owner projections and per-item eligibility. Existing financial freshness owner mutates ORM state, so isolate or split that owner before read-only seeding |
| Nested event/cache policy propagation | Not yet end-to-end | CollectionService does not pass opt-in policy; cached Event consumers remain outside this new boundary. No concrete source adapter may invoke them until filtered/denied |

These are cross-owner interface/side-effect boundaries, not missing normalized
hashes that can be reconstructed after the fact. Broad owner redesign or full
reacquisition was not used to manufacture closure. Synthetic tests prove
mechanics, not provider or live-cohort parity. No real production Class C seed
is claimed: the exported seed and A/B/C packets are labelled synthetic.

Three genuine KRX response files are verified against their original byte
hash receipts, then replayed through the existing parser and fetch-telemetry
owner at the ORIGINAL timestamp. Both product observations reproduce exactly.
This proves saved-artifact ownership only, not current-run night acquisition.

## Regression Accounting

The initial full suite found six historical scope/fixture expectation failures.
The exact four newly changed legacy owner paths are now explicitly listed as
historical drift; historical audits still return FAIL. The portable ancestry
fixture now loads actual reviewed-root blobs, not today's modified files.
Historical pins/attestation, decision thresholds, prompts, schemas and validator
acceptance rules are unchanged. No new skip/xfail was introduced.

## Next Handoff

Close the owner gaps above in a bounded R2A follow-up. Only then start R5F-R2B:
one complete genuine US14/KR8 source cohort, A/B/C acquisition composition,
concrete source adapter qualification, existing downstream owner bridge and
US15 + KR9 message proof. Keep scheduler inactive. R5F-R3 cutover is not ready.

This task: provider/model/Telegram/broker calls zero; production decision,
warning, notification, scheduler mutations zero; push/deploy/restart zero.
Deliver report ZIP plus SHA only, with all evidence inside the ZIP.
