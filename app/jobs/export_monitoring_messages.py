import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

from sqlmodel import Session, select

from app.database import engine, init_db
from app.models.thesis import InvestmentThesis, MonitorRun, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.models.security import ProviderCallTelemetry, SecurityMaster
from app.models.event import CanonicalIssue, Event
from app.providers.registry import provider_statuses
from app.services.daily_digest import build_daily_digest
from app.services.daily_digest_renderer import render_daily_digest
from app.services.notification_service import _assessment_report
from app.services.financial_freshness_service import FinancialFreshnessService
from app.services.event_identity import source_document_id_from_url
from app.services.provider_telemetry_service import summarize_provider_run


DEFAULT_EXPORT_DIR = Path(__file__).resolve().parents[2] / "docs" / "reports"


def _fenced(text: str) -> str:
    return f"```text\n{text.strip()}\n```"


def _foreign_filing_audit_row(ticker: str, coverage: dict[str, object]) -> str:
    availability_labels = {
        "full": "충분",
        "partial": "부분",
        "unavailable": "미확보",
    }
    latest_result_labels = {
        "parsed": "재무표 parsing 성공",
        "validation_failed": "재무표 검증 실패",
        "not_financial_exhibit": "재무 실적표 아님",
        "document_fetch_failed": "문서 fetch 실패",
        "exhibit_not_found": "Exhibit 미발견",
        "financial_table_not_found": "재무표 미발견",
        "unsupported_format": "지원하지 않는 형식",
        "unavailable": "확인 불가",
    }
    discovery = availability_labels.get(
        str(coverage.get("filing_discovery_coverage")), "확인 불가"
    )
    document = availability_labels.get(
        str(coverage.get("document_fetch_coverage")), "확인 불가"
    )
    exhibit = availability_labels.get(
        str(coverage.get("exhibit_discovery_coverage")), "확인 불가"
    )
    prior_parse = (
        "과거 parsing 성공"
        if coverage.get("any_foreign_statement_parsed")
        else "과거 parsing 성공 없음"
    )
    latest_raw = str(
        coverage.get("latest_foreign_filing_parse_result")
        or coverage.get("foreign_latest_filing_result")
        or "unavailable"
    )
    latest = f"최신 filing {latest_result_labels.get(latest_raw, latest_raw)}"
    period = str(coverage.get("latest_foreign_financial_period") or "없음")
    mapping = (
        "ADR/per-share mapping 확보"
        if coverage.get("per_share_mapping_coverage") == "full"
        else "ADR/per-share mapping 미확보"
    )
    valuation = str(coverage.get("valuation_coverage") or "unavailable")
    return (
        f"| {ticker} | Filing 발견 {discovery} | 문서 fetch {document} | "
        f"Exhibit 발견 {exhibit} | {prior_parse} | {latest} | {period} | "
        f"{mapping} | Valuation {valuation} |"
    )


def export_messages(run_date: date, output: Path) -> int:
    init_db()
    with Session(engine) as session:
        digest = render_daily_digest(
            build_daily_digest(session, run_date),
            include_stock_details=False,
        )
        assessments = list(
            session.exec(
                select(ThesisAssessment)
                .where(ThesisAssessment.assessment_date == run_date)
                .order_by(ThesisAssessment.ticker)
            ).all()
        )
        monitor_run = session.exec(
            select(MonitorRun).where(
                MonitorRun.run_date == run_date,
                MonitorRun.run_type == "daily",
            )
        ).first()
        run_started_at = (
            monitor_run.started_at
            if monitor_run
            else datetime.combine(run_date, datetime.min.time(), tzinfo=timezone.utc)
        )
        active_tickers = {item.ticker for item in session.exec(select(WatchlistItem).where(WatchlistItem.active.is_(True))).all()}
        events = list(session.exec(select(Event).where(Event.ticker.in_(active_tickers))).all())
        dart_identity_mismatches = [
            event
            for event in events
            if event.provider == "opendart"
            and event.document_identity_status not in {"invalid", "invalid_mismatch"}
            and source_document_id_from_url(event.url)
            and source_document_id_from_url(event.url) != event.source_document_id
        ]
        invalid_dart_documents = [
            event
            for event in events
            if event.provider == "opendart"
            and event.document_identity_status in {"invalid", "invalid_mismatch"}
        ]
        invalidated_issues = list(
            session.exec(
                select(CanonicalIssue).where(
                    CanonicalIssue.ticker.in_(active_tickers),
                    CanonicalIssue.provenance_status == "invalid_provenance",
                )
            ).all()
        )
        us_premarket_date_mismatches = 0
        for assessment in assessments:
            if assessment.ticker.isdigit() or assessment.market_session != "pre_market":
                continue
            try:
                snapshot = json.loads(assessment.valuation_snapshot or "{}")
            except json.JSONDecodeError:
                snapshot = {}
            if snapshot.get("exchange_trade_date") != snapshot.get("latest_completed_regular_session_date"):
                us_premarket_date_mismatches += 1
        sections = [
            f"# {run_date.isoformat()} Thesis Monitor 전체 메시지",
            "",
            "실제 deterministic renderer 기준 검토본입니다. Telegram 분할 번호는 제외했습니다.",
            "",
            "## 검증 요약",
            "",
            f"- 활성 종목 assessment: {len(assessments)}/14",
            f"- 미국 장전 종가 날짜 불일치: {us_premarket_date_mismatches}건",
            f"- OpenDART URL/receipt 불일치: {len(dart_identity_mismatches)}건",
            f"- 과거 이력에서 식별자 불일치로 격리된 OpenDART 문서: {len(invalid_dart_documents)}건",
            f"- 출처 검증 실패로 비활성화된 canonical issue: {len(invalidated_issues)}건",
            "",
            "## 1. 시장환경 및 포트폴리오 종합",
            "",
            _fenced(digest),
        ]
        for index, assessment in enumerate(assessments, start=2):
            watchlist_item = session.exec(
                select(WatchlistItem).where(WatchlistItem.ticker == assessment.ticker)
            ).first()
            thesis = session.exec(
                select(InvestmentThesis).where(
                    InvestmentThesis.ticker == assessment.ticker,
                    InvestmentThesis.version == assessment.thesis_version,
                )
            ).first()
            company_name = (
                watchlist_item.company_name if watchlist_item else assessment.ticker
            )
            message, _context = _assessment_report(assessment, company_name, thesis)
            sections.extend(
                [
                    "",
                    f"## {index}. {company_name}({assessment.ticker})",
                    "",
                    _fenced(message),
                ]
            )
        sections.extend(
            [
                "",
                "## 부록. 14종목 데이터 커버리지",
                "",
                "| 종목 | 정식 재무 | Full availability/freshness | 잠정실적 | 잠정 freshness | 갱신 상태 | Consensus | Provider | 가격 | 이벤트 | 격리/거절 감사 | 재무 | 역사 Valuation | Forward Valuation | 충돌 | Identity | Foreign | 남은 gap |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for assessment in assessments:
            try:
                snapshot = json.loads(assessment.valuation_snapshot or "{}")
            except json.JSONDecodeError:
                snapshot = {}
            coverage = snapshot.get("data_coverage", {}) if isinstance(snapshot, dict) else {}
            if not isinstance(coverage, dict):
                coverage = {}
            security = session.exec(
                select(SecurityMaster).where(SecurityMaster.ticker == assessment.ticker)
            ).first()
            reasons = coverage.get("reason_codes", [])
            gap = ", ".join(str(item) for item in reasons) if isinstance(reasons, list) and reasons else "없음"
            sections.append(
                f"| {assessment.ticker} | {snapshot.get('latest_full_financial_period') or '없음'} | "
                f"{coverage.get('full_financial_availability', 'unavailable')}/"
                f"{coverage.get('full_financial_freshness', 'unavailable')} | "
                f"{snapshot.get('latest_preliminary_financial_period') or '없음'} | "
                f"{coverage.get('preliminary_financial_freshness', 'unavailable')} | "
                f"{coverage.get('financial_freshness', 'unavailable')} | "
                f"{snapshot.get('consensus_status', coverage.get('consensus', 'unavailable'))} | "
                f"{snapshot.get('estimate_provider') or '없음'} | "
                f"{coverage.get('price_quality', 'unavailable')} | "
                f"{coverage.get('event_quality', 'unavailable')} | "
                f"{coverage.get('quarantined_event_count', 0)}/"
                f"{coverage.get('rejected_candidate_count', 0)} | "
                f"{coverage.get('financial_quality', 'unavailable')} | "
                f"{coverage.get('historical_valuation_quality', 'unavailable')} | "
                f"{coverage.get('forward_valuation_quality', 'unavailable')} | "
                f"{snapshot.get('consensus_disagreement', False)} | "
                f"{coverage.get('identity_mapping', security.identity_quality if security else 'unavailable')} | "
                f"{coverage.get('filing_discovery_coverage', 'not_applicable')}/"
                f"{coverage.get('statement_parsing_coverage', 'not_applicable')}/"
                f"{coverage.get('per_share_mapping_coverage', 'not_applicable')} | {gap} |"
            )
        sections.extend(
            [
                "",
                "## 부록. Warning provenance 감사",
                "",
                "| 종목 | 경고 | 개시일 | Source | Source date | Event type | Provenance | Backfill |",
                "|---|---|---|---|---|---|---|---|",
            ]
        )
        for assessment in assessments:
            try:
                warning_states = json.loads(assessment.warning_states or "[]")
            except json.JSONDecodeError:
                warning_states = []
            for state in warning_states if isinstance(warning_states, list) else []:
                if not isinstance(state, dict) or state.get("status") not in {"open", "escalated"}:
                    continue
                sections.append(
                    f"| {assessment.ticker} | {str(state.get('warning', '')).replace('|', '/')} | "
                    f"{state.get('opened_date') or '확인 불가'} | "
                    f"{state.get('source_provider') or state.get('source') or '확인 불가'} | "
                    f"{state.get('source_date') or '확인 불가'} | "
                    f"{state.get('source_event_type') or '확인 불가'} | "
                    f"{state.get('provenance_status') or 'unverified'} | "
                    f"{bool(state.get('backfilled_warning'))} |"
                )
        if not any(
            json.loads(item.warning_states or "[]")
            for item in assessments
            if item.warning_states
        ):
            sections.append("| - | 현재 open warning 없음 | - | - | - | - | - | - |")

        sections.extend(
            [
                "",
                "### 출처 검증 실패로 비활성화된 기존 issue",
                "",
                "| 종목 | Issue type | Issue | 현재 상태 | Provenance |",
                "|---|---|---|---|---|",
            ]
        )
        if invalidated_issues:
            for issue in invalidated_issues:
                sections.append(
                    f"| {issue.ticker} | {issue.issue_type} | {issue.title.replace('|', '/')} | "
                    f"{issue.status}/{issue.economic_status} | {issue.provenance_status} |"
                )
        else:
            sections.append("| - | - | 제외된 issue 없음 | - | - |")

        sections.extend(
            [
                "",
                "## 부록. Financial freshness 감사",
                "",
                "| 종목 | 정식 재무 | 잠정실적 | 최신 material event | Freshness | PER 분모 | PBR 분모 | 설명 |",
                "|---|---|---|---|---|---|---|---|",
            ]
        )
        for assessment in assessments:
            try:
                snapshot = json.loads(assessment.valuation_snapshot or "{}")
            except json.JSONDecodeError:
                snapshot = {}
            coverage = snapshot.get("data_coverage", {}) if isinstance(snapshot, dict) else {}
            freshness = FinancialFreshnessService().assess(
                session, assessment.ticker, as_of=run_date
            )
            sections.append(
                f"| {assessment.ticker} | {snapshot.get('latest_full_financial_period') or '없음'} | "
                f"{snapshot.get('latest_preliminary_financial_period') or '없음'} | "
                f"{freshness.latest_material_event_date or '없음'} | "
                f"{freshness.status} | "
                f"{snapshot.get('trailing_pe_denominator_period_end') or '확인 불가'} | "
                f"{snapshot.get('pbr_denominator_period_end') or '확인 불가'} | "
                f"{str(coverage.get('overall_quality_reason', '') if isinstance(coverage, dict) else '').replace('|', '/')} |"
            )

        sections.extend(
            [
                "",
                "## 부록. Price session 감사",
                "",
                "| 종목 | Session | Exchange trade date | Latest completed session | Price basis | Observed timezone |",
                "|---|---|---|---|---|---|",
            ]
        )
        for assessment in assessments:
            try:
                snapshot = json.loads(assessment.valuation_snapshot or "{}")
            except json.JSONDecodeError:
                snapshot = {}
            sections.append(
                f"| {assessment.ticker} | {assessment.market_session} | "
                f"{snapshot.get('exchange_trade_date') or snapshot.get('price_as_of') or '확인 불가'} | "
                f"{snapshot.get('latest_completed_regular_session_date') or '확인 불가'} | "
                f"{snapshot.get('price_basis') or 'unavailable'} | "
                f"{snapshot.get('price_observed_timezone') or '확인 불가'} |"
            )

        sections.extend(
            [
                "",
                "## 부록. Foreign filing parsing 감사",
                "",
                "| 종목 | Filing discovery | Document fetch | Exhibit discovery | 과거 statement parse | 최신 filing 결과 | 최신 정규화 재무 | ADR/per-share | Valuation coverage |",
                "|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for assessment in assessments:
            try:
                snapshot = json.loads(assessment.valuation_snapshot or "{}")
            except json.JSONDecodeError:
                snapshot = {}
            coverage = snapshot.get("data_coverage", {}) if isinstance(snapshot, dict) else {}
            if not isinstance(coverage, dict) or coverage.get("filing_discovery_coverage") == "not_applicable":
                continue
            sections.append(_foreign_filing_audit_row(assessment.ticker, coverage))
        sections.extend(
            [
                "",
                "## 부록. Provider 커버리지",
                "",
                "| Provider | Endpoint | Enabled | Configured | 현재 실행 상태 | 현재 시도 | 현재 성공 | 현재 실패 | 현재 Skip | Lifetime 성공/실패/Skip | 최근 시도 | 최근 오류/Skip 사유 | 테스트 ticker |",
                "|---|---|---|---|---|---:|---:|---:|---:|---|---|---|---:|",
            ]
        )
        status_by_name = {status.name: status for status in provider_statuses()}
        telemetry_rows = list(
            session.exec(
                select(ProviderCallTelemetry).order_by(
                    ProviderCallTelemetry.provider,
                    ProviderCallTelemetry.endpoint,
                    ProviderCallTelemetry.ticker,
                )
            ).all()
        )
        grouped: dict[tuple[str, str], list[ProviderCallTelemetry]] = {}
        for row in telemetry_rows:
            grouped.setdefault((row.provider, row.endpoint), []).append(row)
        all_keys = set(grouped)
        all_keys.update((name, "미기록") for name in status_by_name if not any(key[0] == name for key in grouped))
        for provider, endpoint in sorted(all_keys):
            rows = grouped.get((provider, endpoint), [])
            status = status_by_name.get(provider)
            attempts = [row.attempted_at for row in rows if row.attempted_at]
            errors = [
                row.error_reason or row.error_type
                for row in rows
                if row.error_reason or row.error_type
            ]
            summary = summarize_provider_run(rows, run_started_at)
            sections.append(
                f"| {provider} | {endpoint} | {status.enabled if status else True} | "
                f"{status.configured if status else True} | "
                f"{summary['current_run_status']} | "
                f"{summary['current_run_attempts']} | {summary['current_run_successes']} | "
                f"{summary['current_run_failures']} | {summary['current_run_skips']} | "
                f"{summary['lifetime_successes']}/{summary['lifetime_failures']}/{summary['lifetime_skips']} | "
                f"{max(attempts).isoformat() if attempts else '미기록'} | "
                f"{errors[-1] if errors else next((row.skip_reason for row in reversed(rows) if row.skip_reason), '없음')} | "
                f"{len({row.ticker for row in rows})} |"
            )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(sections) + "\n", encoding="utf-8")
    return len(assessments)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export rendered daily monitoring messages.")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--output")
    args = parser.parse_args()
    run_date = date.fromisoformat(args.date)
    output = Path(
        args.output
        or DEFAULT_EXPORT_DIR
        / f"{datetime.now():%Y%m%d-%H%M%S}-{run_date}-monitoring-messages.md"
    )
    count = export_messages(run_date, output)
    print(f"exported={count} output={output.resolve()}")


if __name__ == "__main__":
    main()
