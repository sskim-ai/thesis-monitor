import argparse
import json
from datetime import date, datetime
from pathlib import Path

from sqlmodel import Session, select

from app.database import engine, init_db
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.models.security import ProviderCallTelemetry, SecurityMaster
from app.providers.registry import provider_statuses
from app.services.daily_digest import build_daily_digest
from app.services.daily_digest_renderer import render_daily_digest
from app.services.notification_service import _assessment_report


DEFAULT_EXPORT_DIR = (
    Path.home()
    / "Library"
    / "Mobile Documents"
    / "com~apple~CloudDocs"
    / "Thesis Monitor"
)


def _fenced(text: str) -> str:
    return f"```text\n{text.strip()}\n```"


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
        sections = [
            f"# {run_date.isoformat()} Thesis Monitor 전체 메시지",
            "",
            "실제 deterministic renderer 기준 검토본입니다. Telegram 분할 번호는 제외했습니다.",
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
                "| 종목 | 정식 재무 | 잠정실적 | 갱신 상태 | Consensus | Provider | 가격 | 이벤트 | 재무 | 역사 Valuation | Forward Valuation | 충돌 | Identity | Foreign | 남은 gap |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
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
                f"{snapshot.get('latest_preliminary_financial_period') or '없음'} | "
                f"{coverage.get('financial_freshness', 'unavailable')} | "
                f"{snapshot.get('consensus_status', coverage.get('consensus', 'unavailable'))} | "
                f"{snapshot.get('estimate_provider') or '없음'} | "
                f"{coverage.get('price_quality', 'unavailable')} | "
                f"{coverage.get('event_quality', 'unavailable')} | "
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
                "## 부록. Provider 커버리지",
                "",
                "| Provider | Endpoint | Enabled | Configured | 최근 시도 | 최근 성공 | 성공 | 실패 | 최근 오류 유형 | 테스트 ticker |",
                "|---|---|---|---|---|---|---:|---:|---|---:|",
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
            successes = [row.last_success_at for row in rows if row.last_success_at]
            errors = [row.error_type for row in rows if row.error_type]
            sections.append(
                f"| {provider} | {endpoint} | {status.enabled if status else True} | "
                f"{status.configured if status else True} | "
                f"{max(attempts).isoformat() if attempts else '미기록'} | "
                f"{max(successes).isoformat() if successes else '미기록'} | "
                f"{sum(row.success_count for row in rows)} | {sum(row.failure_count for row in rows)} | "
                f"{errors[-1] if errors else '없음'} | {len({row.ticker for row in rows})} |"
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
