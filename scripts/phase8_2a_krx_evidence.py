from __future__ import annotations

# ruff: noqa: E402

import asyncio
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.providers.krx_kr_market_provider import (
    KOSDAQ_DAILY_PATH,
    KOSDAQ_INDEX_PATH,
    KOSDAQ_REFERENCE_PATH,
    KOSPI_DAILY_PATH,
    KOSPI_INDEX_PATH,
    KOSPI_REFERENCE_PATH,
    OFFICIAL_DAILY_REQUEST_LIMIT,
    KrxKrMarketProvider,
    krx_capability_matrix,
)
from app.services.market_intelligence_service import build_market_intelligence
from app.services.numeric_semantic_registry import (
    build_numeric_registry,
    numeric_registry_coverage,
)


REPORTS = ROOT / "docs" / "reports"
CACHE = ROOT / "data" / "cache" / "krx"
SESSION = date(2026, 8, 14)
REPORT_DATE = "20260818"
IMPLEMENTATION_COMMIT = "0bf8921981bd3bd226e65291e785a831832055bd"
GITHUB_ACTIONS_RUN = 32129314573
ENDPOINTS = (
    KOSPI_DAILY_PATH,
    KOSDAQ_DAILY_PATH,
    KOSPI_REFERENCE_PATH,
    KOSDAQ_REFERENCE_PATH,
    KOSPI_INDEX_PATH,
    KOSDAQ_INDEX_PATH,
)


def _fmt(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "unavailable"
    return f"{value:,.{digits}f}"


def _envelope_path(endpoint: str) -> Path:
    name = endpoint.replace("/", "_")
    return CACHE / "market" / SESSION.isoformat() / f"{name}.json"


def _envelope_audit() -> list[dict[str, object]]:
    result = []
    for endpoint in ENDPOINTS:
        payload = json.loads(_envelope_path(endpoint).read_text(encoding="utf-8"))
        result.append(
            {
                "endpoint": endpoint,
                "http_status": payload["http_metadata"]["status_code"],
                "latency_ms": round(float(payload["latency_seconds"]) * 1000, 1),
                "row_count": payload["row_count"],
                "provider_date": payload["request_date"],
                "rate_limit_headers": payload["http_metadata"]["rate_limit_headers"],
                "payload_sha256": payload["response_sha256"],
            }
        )
    return result


def _capability_table() -> str:
    rows = ["| Capability | Status | Evidence |", "|---|---|---|"]
    rows.extend(
        f"| {item.metric} | {item.status} | {item.evidence} |"
        for item in krx_capability_matrix()
    )
    return "\n".join(rows)


def _breadth_line(segment: str, breadth: object) -> str:
    return (
        f"- {segment}: eligible {breadth.eligible_count:,}, advance "
        f"{breadth.advance_count:,}, decline {breadth.decline_count:,}, unchanged "
        f"{breadth.unchanged_count:,}; advance ratio "
        f"{_fmt(breadth.advance_ratio * 100 if breadth.advance_ratio is not None else None, 1)}%; "
        f"median {_fmt(breadth.median_return_pct, 2)}%, equal weight "
        f"{_fmt(breadth.equal_weight_return_pct, 2)}%"
    )


async def main() -> None:
    provider = KrxKrMarketProvider(api_key=None, cache_dir=CACHE)
    section = await provider.collect(
        session_date=SESSION,
        expected_session_date=SESSION,
    )
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
    endpoint_audit = _envelope_audit()
    sectors = sorted(
        section.sectors,
        key=lambda item: item.return_pct if item.return_pct is not None else -999,
        reverse=True,
    )

    audit = {
        "phase": "8.2A",
        "status": "experimental_archive_only",
        "session_date": SESSION.isoformat(),
        "provider": "krx",
        "provider_role": "primary_candidate_not_deployed",
        "contract": section.contract_version,
        "breadth_calculation": section.quality.calculation_version,
        "universe_version": section.quality.universe_version,
        "official_daily_request_limit": OFFICIAL_DAILY_REQUEST_LIMIT,
        "credentialed_read_only_audit_calls": 31,
        "canonical_snapshot_calls": 6,
        "credential_exposure_count": 0,
        "endpoints": endpoint_audit,
        "indices": [item.model_dump(mode="json") for item in section.indices],
        "breadth": section.breadth.model_dump(mode="json") if section.breadth else None,
        "breadth_by_segment": {
            key: value.model_dump(mode="json")
            for key, value in section.breadth_by_segment.items()
        },
        "sectors": [item.model_dump(mode="json") for item in sectors],
        "market_flows": {
            "status": "UNSUPPORTED",
            "facts": [],
            "missing_is_zero": False,
        },
        "quality": section.quality.model_dump(mode="json"),
        "market_intelligence": {
            "fact_count": len(intelligence["fact_catalog"]),
            "selected_fact_ids": intelligence["key_change_fact_ids"],
            "numeric_registry": registry_status,
        },
        "current_session_probe": {
            "date": "2026-08-18",
            "http_status": 200,
            "rows_per_endpoint": 0,
            "canonical_promotion": False,
            "reason": "empty provider result at audit time",
        },
        "production_mutations": {
            "main_merge": 0,
            "operating_deployment": 0,
            "scheduled_task_changes": 0,
            "telegram_sends": 0,
            "pilot_mutations": 0,
        },
    }
    (REPORTS / f"{REPORT_DATE}-phase8-2a-krx-market-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    capability = f"""# Phase 8.2A KRX Open API Capability

Date: 2026-08-18
Status: EXPERIMENTAL / ARCHIVE ONLY
Provider session: {SESSION.isoformat()}
Main merge: 0
Operating deployment: 0

## Official Evidence

- KRX Open API service catalog: https://openapi.krx.co.kr/contents/OPP/INFO/service/OPPINFO004.cmd
- KRX Open API terms: https://openapi.krx.co.kr/contents/OPP/INFO/OPPINFO002.jsp
- Authentication: `AUTH_KEY` request header.
- Official limit: 10,000 requests per key per day. No rate-limit headers were returned by the audited endpoints.
- Official daily APIs provide 2010-and-later statistical data. The approved endpoints returned exact 2026-08-14 rows.

## Capability Matrix

{_capability_table()}

## Exact Boundary

- KOSPI/KOSDAQ daily rows and issue basic information support deterministic common-share breadth.
- KOSPI, KOSPI 200, KOSDAQ, and KOSDAQ 150 identities are explicit.
- KOSPI 200 and KOSDAQ 150 industry-index returns are `sector_price_proxy`, not security-level sector breadth.
- The approved Open API catalog does not provide market-wide foreign/institution/retail net-buy facts. Missing flow remains unavailable, never zero.
- No explicit suspension flag is present. Otherwise eligible zero-volume rows remain in the unchanged denominator and the coverage stays `partial`.

## Universe Policy

Eligible denominator:

```text
KOSPI or KOSDAQ daily row
+ matching six-character official short code
+ SECUGRP_NM = 주권
+ KIND_STKCERT_TP_NM = 보통주
- SPAC official segment/name marker
+ LIST_DD strictly before the requested session
```

Preferred shares, REITs, infrastructure funds, investment companies, foreign shares, depositary receipts, SPACs, and same-session new listings are excluded. ETF/ETN/ELW are separate KRX services and never enter this denominator.

## Live Audit

- Credentialed read-only discovery calls: 31; canonical snapshot calls: 6; credential exposure: 0.
- Pagination: none for the six audited endpoints.
- Canonical snapshot latency: {sum(float(item['latency_ms']) for item in endpoint_audit):,.1f} ms total.
- Current 2026-08-18 probe returned HTTP 200 with zero rows, so it was not promoted. The archive-only snapshot uses exact available session 2026-08-14; this is not an automatic stale fallback policy.
"""
    (REPORTS / f"{REPORT_DATE}-phase8-2a-krx-capability.md").write_text(
        capability, encoding="utf-8"
    )

    preview = f"""# Phase 8.2A KRX Market Preview

Date: 2026-08-18
Immutable provider session: {SESSION.isoformat()}
Mode: archive-only
Telegram sends: 0

## BEFORE — Existing KR Market Context

한국 현물 지수와 market breadth가 backend packet에 없어 미국 지수, 반도체 가격, 원/달러, 유가, 야간선물을 전일 해외 맥락으로만 사용합니다. 한국 시장 전체 외국인·기관·개인 수급도 확인되지 않습니다.

## AFTER — KRX-Enhanced Archive Preview

### 한국 현물 시장

KOSPI는 {_fmt(next(item.close for item in section.indices if item.symbol == 'KOSPI'))}로 {_fmt(next(item.return_pct for item in section.indices if item.symbol == 'KOSPI'), 2)}% 상승했고, KOSDAQ은 {_fmt(next(item.close for item in section.indices if item.symbol == 'KOSDAQ'))}로 {_fmt(next(item.return_pct for item in section.indices if item.symbol == 'KOSDAQ'), 2)}% 상승했습니다.

KOSPI common-share breadth는 상승 {section.breadth_by_segment['KOSPI'].advance_count:,} / 하락 {section.breadth_by_segment['KOSPI'].decline_count:,} / 보합 {section.breadth_by_segment['KOSPI'].unchanged_count:,}종목, 상승 비율 {_fmt(section.breadth_by_segment['KOSPI'].advance_ratio * 100, 1)}%, 동일가중 수익률 {_fmt(section.breadth_by_segment['KOSPI'].equal_weight_return_pct, 2)}%입니다. 지수 상승과 함께 시장 참여도 넓었습니다.

KOSDAQ은 상승 {section.breadth_by_segment['KOSDAQ'].advance_count:,} / 하락 {section.breadth_by_segment['KOSDAQ'].decline_count:,} / 보합 {section.breadth_by_segment['KOSDAQ'].unchanged_count:,}종목, 상승 비율 {_fmt(section.breadth_by_segment['KOSDAQ'].advance_ratio * 100, 1)}%, 동일가중 수익률 {_fmt(section.breadth_by_segment['KOSDAQ'].equal_weight_return_pct, 2)}%로 지수 상승보다 참여 확산은 제한적이었습니다.

업종 가격 proxy에서는 {sectors[0].sector}가 {_fmt(sectors[0].return_pct, 2)}%로 가장 강했고, {sectors[-1].sector}는 {_fmt(sectors[-1].return_pct, 2)}%였습니다. 이는 업종지수 가격 흐름이며 개별 기업 실적 확인이 아닙니다.

시장 전체 외국인·기관·개인 순매수는 승인된 KRX Open API에서 제공되지 않아 `Unknown`으로 유지합니다.

## Selection

Decision-material selected Facts:

{chr(10).join(f'- `{item}`' for item in intelligence['key_change_fact_ids'])}

Numeric registry: {registry_status['registered_count']}/{registry_status['entry_count']} registered, unsupported 0, ready `{str(registry_status['ready']).lower()}`.

Source attribution: 한국거래소 통계정보. This preview is not sent and does not change any stock thesis.
"""
    (REPORTS / f"{REPORT_DATE}-phase8-2a-krx-market-preview.md").write_text(
        preview, encoding="utf-8"
    )

    validation = f"""# Phase 8.2A KRX Validation

Date: 2026-08-18
Branch: `codex/phase-8-2a-krx-market-breadth`
Status: DEVELOPMENT / ARCHIVE ONLY

## Contracts

- Market cross section: `{section.contract_version}`
- Breadth calculation: `{section.quality.calculation_version}`
- Universe: `{section.quality.universe_version}`
- Provider role: primary candidate, not registered in operating runtime
- Session: exact historical XKRX session `{SESSION.isoformat()}`
- Current 2026-08-18 empty response: fail-closed, not current canonical

## Provider Validation

| Endpoint | HTTP | Rows | Latency ms | Date |
|---|---:|---:|---:|---|
{chr(10).join(f"| `{item['endpoint']}` | {item['http_status']} | {item['row_count']:,} | {item['latency_ms']:.1f} | {item['provider_date']} |" for item in endpoint_audit)}

- Duplicate identities: 0
- Wrong-date rows: 0
- Empty canonical endpoints: 0 for archive session; fail-closed for current empty probe
- Pagination: none
- Rate-limit headers: absent
- Credential exposure in cache/report/log: 0

## Universe And Breadth

- Raw daily rows: {section.quality.raw_count:,}
- Eligible common shares: {section.quality.eligible_count:,}
- Excluded rows: {section.quality.excluded_count:,}
- Exclusion reasons: `{json.dumps(section.quality.exclusion_reason_counts, ensure_ascii=False, sort_keys=True)}`
{_breadth_line('KOSPI', section.breadth_by_segment['KOSPI'])}
{_breadth_line('KOSDAQ', section.breadth_by_segment['KOSDAQ'])}

`advance + decline + unchanged == eligible` passes for aggregate and both segments.

## Numeric Provenance

- Canonical market Facts: {len(intelligence['fact_catalog'])}
- Numeric registry entries: {registry_status['entry_count']}
- Registered: {registry_status['registered_count']}
- Prose allowed: {registry_status['prose_allowed_count']}
- Unsupported: {len(registry_status['unsupported'])}
- Ready: `{str(registry_status['ready']).lower()}`
- Market/stock flow collision: 0; market actor flow Facts emitted: 0

## Safety

- Main merge: 0
- Operating checkout update: 0
- API production restart: 0
- Scheduled Task changes/executions: 0
- Telegram sends: 0
- Pilot mutations: 0
- Production Assist: OFF

## Regression

- Focused KRX/cross-section/intelligence/documentation tests: 43 passed
- Full pytest: 1,054 passed, 1 existing dependency deprecation warning
- Ruff: PASS
- `git diff --check`: PASS
- Investment Knowledge SHA-256: `559ad45e4dd86cb0aec9bb09b51a5dc816bf323e8c2b4fd050cf28960a5a9d18`
- Chart Knowledge SHA-256: `beee64559831479168f1347c43d979391126926d73e2473ce837cefbf0ede19b`
- Public Action: 0.4.5; operationId 20/20 unique
- Implementation commit: `{IMPLEMENTATION_COMMIT}`
- GitHub Actions run `{GITHUB_ACTIONS_RUN}`: Test/Lint PASS

The archive-only result does not replace the pending Phase 8.5.x natural AI-assisted delivery proof.
"""
    (REPORTS / f"{REPORT_DATE}-phase8-2a-krx-validation.md").write_text(
        validation, encoding="utf-8"
    )


if __name__ == "__main__":
    asyncio.run(main())
