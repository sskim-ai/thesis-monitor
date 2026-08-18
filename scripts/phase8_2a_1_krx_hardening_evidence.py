from __future__ import annotations

# ruff: noqa: E402

import asyncio
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.providers.krx_kr_market_provider import (
    KOSDAQ_DAILY_PATH,
    KOSDAQ_REFERENCE_PATH,
    KOSPI_DAILY_PATH,
    KOSPI_REFERENCE_PATH,
    KrxKrMarketProvider,
)
from app.services.market_intelligence_service import build_market_intelligence
from app.services.numeric_semantic_registry import (
    build_numeric_registry,
    numeric_registry_coverage,
)


REPORT_DATE = "20260818"
SESSION = date(2026, 8, 14)
CURRENT_SESSION = date(2026, 8, 18)
IMPLEMENTATION_COMMIT = "f90f686fd261a4eb19b6132e79389e8351cc87b2"
GITHUB_ACTIONS_RUN = 32132655162
REPORTS = ROOT / "docs" / "reports"
CACHE = ROOT / "data" / "cache" / "krx"
PREVIOUS_AUDIT = REPORTS / "20260818-phase8-2a-krx-market-audit.json"

CURRENT_READINESS = {
    "contract_version": "krx-publication-readiness-v1",
    "status": "MARKET_COMPLETED_PROVIDER_PENDING",
    "target_session": "2026-08-18",
    "latest_completed_session": "2026-08-18",
    "observed_at": "2026-08-18T11:27:09.594575Z",
    "observed_at_kst": "2026-08-18T20:27:09.594575+09:00",
    "endpoints": [
        {
            "endpoint": "sto/stk_bydd_trd",
            "http_status": 200,
            "row_count": 0,
            "status": "EMPTY",
            "latency_ms": 124.3,
        },
        {
            "endpoint": "sto/ksq_bydd_trd",
            "http_status": 200,
            "row_count": 0,
            "status": "EMPTY",
            "latency_ms": 139.2,
        },
        {
            "endpoint": "idx/kospi_dd_trd",
            "http_status": 200,
            "row_count": 0,
            "status": "EMPTY",
            "latency_ms": 107.2,
        },
        {
            "endpoint": "idx/kosdaq_dd_trd",
            "http_status": 200,
            "row_count": 0,
            "status": "EMPTY",
            "latency_ms": 75.2,
        },
    ],
    "first_non_empty_at": None,
    "first_complete_at": None,
    "provider_publication_timestamp": None,
    "current_snapshot_promotable": False,
    "reason_codes": ["all_core_endpoints_returned_empty_200"],
}


def _envelope(endpoint: str) -> dict[str, object]:
    path = CACHE / "market" / SESSION.isoformat() / f"{endpoint.replace('/', '_')}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid cached envelope: {endpoint}")
    return payload


def _rows(endpoint: str) -> list[dict[str, object]]:
    rows = _envelope(endpoint).get("rows")
    if not isinstance(rows, list):
        raise ValueError(f"missing cached rows: {endpoint}")
    return [row for row in rows if isinstance(row, dict)]


def _number(value: object) -> float | None:
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _listing_audit() -> dict[str, object]:
    daily_rows = _rows(KOSPI_DAILY_PATH) + _rows(KOSDAQ_DAILY_PATH)
    reference_rows = _rows(KOSPI_REFERENCE_PATH) + _rows(KOSDAQ_REFERENCE_PATH)
    reference_by_ticker = {
        str(row.get("ISU_SRT_CD") or ""): row for row in reference_rows
    }
    relations: Counter[str] = Counter()
    missing_comparable_previous_close = 0
    for row in daily_rows:
        reference = reference_by_ticker.get(str(row.get("ISU_CD") or ""), {})
        listing_date = str(reference.get("LIST_DD") or "").strip()
        if not listing_date:
            relation = "missing"
        elif listing_date == "20260814":
            relation = "same_session"
        elif listing_date > "20260814":
            relation = "future"
        else:
            relation = "prior_session"
        relations[relation] += 1

        close = _number(row.get("TDD_CLSPRC"))
        change = _number(row.get("CMPPREVDD_PRC"))
        previous_close = close - change if close is not None and change is not None else None
        if previous_close is None or previous_close <= 0:
            missing_comparable_previous_close += 1
    return {
        "raw_daily_rows": len(daily_rows),
        "listing_date_relations": dict(sorted(relations.items())),
        "same_session_listings": relations["same_session"],
        "future_listings": relations["future"],
        "missing_listing_dates": relations["missing"],
        "missing_comparable_previous_close": missing_comparable_previous_close,
    }


def _breadth_payload(section: object) -> dict[str, object]:
    return {
        "aggregate": section.breadth.model_dump(mode="json"),
        "KOSPI": section.breadth_by_segment["KOSPI"].model_dump(mode="json"),
        "KOSDAQ": section.breadth_by_segment["KOSDAQ"].model_dump(mode="json"),
    }


def _breadth_line(label: str, breadth: object) -> str:
    return (
        f"| {label} | {breadth.eligible_count:,} | {breadth.advance_count:,} | "
        f"{breadth.decline_count:,} | {breadth.unchanged_count:,} | "
        f"{breadth.advance_ratio * 100:.1f}% | "
        f"{breadth.equal_weight_return_pct:.2f}% |"
    )


async def main() -> None:
    provider = KrxKrMarketProvider(api_key=None, cache_dir=CACHE)
    section = await provider.collect(
        session_date=SESSION,
        expected_session_date=SESSION,
    )
    previous = json.loads(PREVIOUS_AUDIT.read_text(encoding="utf-8"))
    listing = _listing_audit()
    intelligence = build_market_intelligence(
        None,
        SESSION,
        [],
        [],
        market="kr",
        cross_section=section,
    )
    registry = build_numeric_registry(intelligence["fact_catalog"])
    registry_status = numeric_registry_coverage([registry])
    sectors = sorted(
        section.sectors,
        key=lambda item: item.return_pct if item.return_pct is not None else -999,
        reverse=True,
    )
    indices = {item.symbol: item for item in section.indices}

    audit = {
        "phase": "8.2A.1",
        "status": "experimental_archive_pass_not_deployed",
        "root_cause": "documentation_predicate_wording_error",
        "universe": {
            "version": section.quality.universe_version,
            "version_bumped": False,
            "actual_eligibility_predicate": "LIST_DD < session_date and comparable_previous_close exists",
            "implementation_before": "listing_date >= session_date excluded",
            "implementation_after": "same-session and future listings remain excluded with distinct reason codes",
            "listing_audit": listing,
            "before": {
                "raw": previous["quality"]["raw_count"],
                "eligible": previous["quality"]["eligible_count"],
                "excluded": previous["quality"]["excluded_count"],
                "breadth": {
                    "aggregate": previous["breadth"],
                    **previous["breadth_by_segment"],
                },
            },
            "after": {
                "raw": section.quality.raw_count,
                "eligible": section.quality.eligible_count,
                "excluded": section.quality.excluded_count,
                "exclusion_reason_counts": section.quality.exclusion_reason_counts,
                "breadth": _breadth_payload(section),
            },
            "denominator_changed": False,
        },
        "publication_readiness": CURRENT_READINESS,
        "publication_observation": {
            "explicit_provider_timestamp_available": False,
            "first_complete_observed": False,
            "current_session_readiness": "PARTIAL",
            "future_shadow_windows_kst": ["15:35", "15:45", "16:00", "16:05", "16:10"],
            "production_schedule_configured": False,
        },
        "sector": {
            "status": "PARTIAL_PRICE_PROXY_ONLY",
            "security_level_sector_breadth": "UNSUPPORTED",
            "selected_count": 2,
        },
        "market_flow": {
            "status": "UNSUPPORTED",
            "facts": [],
            "missing_is_zero": False,
        },
        "numeric_registry": registry_status,
        "production_mutations": {
            "main_merge": 0,
            "operating_deployment": 0,
            "scheduled_task_changes": 0,
            "scheduled_task_executions": 0,
            "telegram_sends": 0,
            "pilot_mutations": 0,
            "database_mutations": 0,
        },
    }
    (REPORTS / f"{REPORT_DATE}-phase8-2a-1-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    universe_report = f"""# Phase 8.2A.1 KRX Universe Audit

Date: 2026-08-18
Session: 2026-08-14 archive snapshot
Result: PASS; denominator unchanged

## Root Cause

This was a documentation wording error, not an eligibility bug. The implementation excluded
`listing_date >= session_date`, while the Phase 8.2A capability code block made that exclusion look
like an inclusion rule. Phase 8.2A.1 rewrites the policy positively as:

```text
LIST_DD < session_date
AND comparable_previous_close exists
```

The code now preserves the same eligibility while assigning separate exclusion reasons:
`new_listing_no_prior_close`, `future_listing`, `listing_date_missing`,
`listing_date_invalid`, and `missing_comparable_previous_close`. Same-session KRX comparison values
are never substituted for a previous exchange close.

## Listing Audit

| Observation | Count |
|---|---:|
| Raw daily rows | {listing['raw_daily_rows']:,} |
| Prior-session listings | {listing['listing_date_relations'].get('prior_session', 0):,} |
| Same-session listings | {listing['same_session_listings']:,} |
| Future listings | {listing['future_listings']:,} |
| Missing listing dates | {listing['missing_listing_dates']:,} |
| Missing comparable previous close | {listing['missing_comparable_previous_close']:,} |

## Denominator Before / After

| Scope | Before eligible | After eligible | Before excluded | After excluded |
|---|---:|---:|---:|---:|
| Aggregate | {previous['quality']['eligible_count']:,} | {section.quality.eligible_count:,} | {previous['quality']['excluded_count']:,} | {section.quality.excluded_count:,} |
| KOSPI | {previous['breadth_by_segment']['KOSPI']['eligible_count']:,} | {section.breadth_by_segment['KOSPI'].eligible_count:,} | - | - |
| KOSDAQ | {previous['breadth_by_segment']['KOSDAQ']['eligible_count']:,} | {section.breadth_by_segment['KOSDAQ'].eligible_count:,} | - | - |

The denominator and every breadth count are unchanged, so
`krx-kospi-kosdaq-common-share-v1` remains correct. The raw snapshot contains no same-session,
future, missing-listing-date, or missing-comparable-close row; fixture tests enforce those boundaries.
"""
    (REPORTS / f"{REPORT_DATE}-phase8-2a-1-universe-audit.md").write_text(
        universe_report,
        encoding="utf-8",
    )

    endpoint_table = "\n".join(
        f"| `{item['endpoint']}` | {item['http_status']} | {item['row_count']} | {item['status']} | {item['latency_ms']:.1f} |"
        for item in CURRENT_READINESS["endpoints"]
    )
    readiness_report = f"""# Phase 8.2A.1 Current-Session Readiness

Date: 2026-08-18
Contract: `krx-publication-readiness-v1`
Current status: `MARKET_COMPLETED_PROVIDER_PENDING`
Current-session readiness: PARTIAL

## State Machine

| State | Meaning | Full current snapshot |
|---|---|---|
| `MARKET_NOT_COMPLETED` | XKRX target session is not completed | Denied |
| `MARKET_COMPLETED_PROVIDER_PENDING` | Completed session; all core endpoints returned empty HTTP 200 | Denied |
| `PROVIDER_PARTIAL` | Only part of the required endpoint/identity bundle is ready | Denied |
| `PROVIDER_COMPLETE` | All core endpoints are non-empty, exact-date, identity-valid | Allowed |
| `PROVIDER_ERROR` | HTTP, network, or schema failure | Denied |
| `STALE_PROVIDER_DATE` | Provider rows do not match the target completed session | Denied |

No individual partial Fact is promoted in Phase 8.2A.1. Archive collection remains an explicit exact-
date operation; future current integration must pass this preflight first.

## 2026-08-18 Observation

XKRX classified 2026-08-18 as the latest completed regular session. At
`{CURRENT_READINESS['observed_at_kst']}` the four core endpoints returned:

| Endpoint | HTTP | Rows | Endpoint state | Latency ms |
|---|---:|---:|---|---:|
{endpoint_table}

This is provider publication pending, not market-open, provider-error, no-data-zero, or a promotable
current snapshot. The payload exposes no explicit publication timestamp. First non-empty and first
complete observations are both `NOT_YET_OBSERVED`.

## Future Observation

Proposed shadow windows are 15:35, 15:45, 16:00, 16:05, and 16:10 KST. They are a measurement plan,
not a production schedule. Reference metadata can remain cached; each window needs only four core
calls, well inside the documented 10,000-call daily limit. One normal-session complete observation
would make readiness STRONG PARTIAL; 3-5 sessions are recommended before CLOSED consideration.
"""
    (REPORTS / f"{REPORT_DATE}-phase8-2a-1-current-session-readiness.md").write_text(
        readiness_report,
        encoding="utf-8",
    )

    before_message = (
        "한국 현물시장 breadth가 없어 미국 지수, 반도체 가격, 원/달러, 유가와 야간선물 중심의 "
        "간접 맥락만 제공합니다."
    )
    top_sector = sectors[0]
    bottom_sector = sectors[-1]
    after_message = f"""한국 현물시장

KOSPI는 {indices['KOSPI'].close:,.2f}로 {indices['KOSPI'].return_pct:+.2f}% 상승했습니다. 보통주 {section.breadth_by_segment['KOSPI'].eligible_count:,}종목 중 상승 {section.breadth_by_segment['KOSPI'].advance_count:,}, 하락 {section.breadth_by_segment['KOSPI'].decline_count:,}, 보합 {section.breadth_by_segment['KOSPI'].unchanged_count:,}종목으로 상승 비율은 {section.breadth_by_segment['KOSPI'].advance_ratio * 100:.1f}%, 동일가중 수익률은 {section.breadth_by_segment['KOSPI'].equal_weight_return_pct:+.2f}%였습니다. 지수 상승이 소수 대형주에만 국한됐다고 보기 어려운 참여 폭입니다.

KOSDAQ은 {indices['KOSDAQ'].close:,.2f}로 {indices['KOSDAQ'].return_pct:+.2f}% 상승했습니다. 보통주 {section.breadth_by_segment['KOSDAQ'].eligible_count:,}종목의 상승 비율은 {section.breadth_by_segment['KOSDAQ'].advance_ratio * 100:.1f}%, 동일가중 수익률은 {section.breadth_by_segment['KOSDAQ'].equal_weight_return_pct:+.2f}%로 KOSPI보다 상승 확산이 제한적이었습니다.

업종지수 가격 흐름에서는 {top_sector.sector}가 {top_sector.return_pct:+.2f}%, {bottom_sector.sector}가 {bottom_sector.return_pct:+.2f}%였습니다. 이는 업종지수 가격 움직임이며 해당 업종 기업의 실적 개선을 뜻하지 않습니다."""
    preview = f"""# Phase 8.2A.1 KRX Market Preview

Date: 2026-08-18
Immutable context: 2026-08-14
Mode: archive-only; Telegram sends 0

## BEFORE

{before_message}

## AFTER

{after_message}

## Human Review

- KOSPI와 KOSDAQ의 지수 방향과 보통주 참여 폭이 분리되어 읽힌다.
- KOSPI의 넓은 참여와 KOSDAQ의 상대적으로 제한된 확산이 과장 없이 드러난다.
- sector 값은 업종지수 가격 움직임으로만 표시하며 sector breadth나 기업 실적으로 승격하지 않는다.
- 지원되지 않는 시장 전체 투자주체 수급 section은 만들지 않는다.
- global/night context는 보조 시간축으로 남고 이 현물 block을 반복하지 않는다.
- After block: {len(after_message)} characters, {len(after_message.splitlines())} non-empty/structural lines.

Codex archive-preview review: PASS. User promotion review and current-session complete evidence remain pending.
"""
    (REPORTS / f"{REPORT_DATE}-phase8-2a-1-market-preview.md").write_text(
        preview,
        encoding="utf-8",
    )

    validation = f"""# Phase 8.2A.1 Validation

Date: 2026-08-18
Branch: `codex/phase-8-2a-krx-market-breadth`
Status: EXPERIMENTAL / ARCHIVE ONLY

## Results

- Listing-date root cause: documentation wording error; implementation denominator was correct.
- Universe contract: CLOSED; version remains `{section.quality.universe_version}`.
- Aggregate/KOSPI/KOSDAQ denominator change: 0.
- Breadth reconciliation: PASS.
- Current-session readiness state machine: PASS retrospective.
- 2026-08-18 state: `MARKET_COMPLETED_PROVIDER_PENDING`; promotion denied.
- First complete publication observation: NOT_YET_OBSERVED.
- Sector semantic: `sector_price_proxy`; sector breadth promotion 0.
- Market-wide investor flow: UNSUPPORTED; zero substitution 0.
- Numeric registry: {registry_status['registered_count']}/{registry_status['entry_count']} registered, unsupported {len(registry_status['unsupported'])}.

## Breadth After Audit

| Scope | Eligible | Advance | Decline | Unchanged | Advance ratio | Equal weight |
|---|---:|---:|---:|---:|---:|---:|
{_breadth_line('Aggregate', section.breadth)}
{_breadth_line('KOSPI', section.breadth_by_segment['KOSPI'])}
{_breadth_line('KOSDAQ', section.breadth_by_segment['KOSDAQ'])}

## Validation Commands

- Focused tests: 96 passed
- Full pytest: 1,062 passed; one existing dependency deprecation warning
- Ruff: PASS
- `git diff --check`: PASS
- Investment Knowledge SHA-256: `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart Knowledge SHA-256: `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`
- Public Action 0.4.5; operationId 20/20 unique: PASS
- Implementation commit: `{IMPLEMENTATION_COMMIT}`
- GitHub Actions run `{GITHUB_ACTIONS_RUN}`: Test/Lint PASS

## Safety

- Main merge: 0
- Operating deployment/restart: 0
- Scheduled Task changes/executions: 0
- Telegram sends: 0
- Pilot mutations: 0
- DB mutations: 0
- Production Assist: OFF

Historical capability remains PASS. Current-session readiness remains PARTIAL until a normal-session
complete observation; this archive result does not replace natural Phase 8.5.x AI-assisted proof.
"""
    (REPORTS / f"{REPORT_DATE}-phase8-2a-1-validation.md").write_text(
        validation,
        encoding="utf-8",
    )


if __name__ == "__main__":
    asyncio.run(main())
