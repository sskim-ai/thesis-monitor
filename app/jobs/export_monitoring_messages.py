import argparse
import json
from datetime import date, datetime
from pathlib import Path

from sqlmodel import Session, select

from app.database import engine, init_db
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.event import CanonicalIssue
from app.models.financial import DataBackfillState, DividendHistory
from app.models.watchlist import WatchlistItem
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
                "| 종목 | 재무 이력 | 최신성 | 배당 | 자본행위 | 역사적 Valuation | Forward | Foreign filing | 남은 gap |",
                "|---|---:|---|---|---|---|---|---|---|",
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
            state = session.get(DataBackfillState, assessment.ticker)
            dividends = session.exec(
                select(DividendHistory).where(DividendHistory.ticker == assessment.ticker)
            ).all()
            issues = session.exec(
                select(CanonicalIssue).where(CanonicalIssue.ticker == assessment.ticker)
            ).all()
            pe_stats = snapshot.get("historical_pe_statistics") or {}
            pb_stats = snapshot.get("historical_pb_statistics") or {}
            history_years = max(
                float(pe_stats.get("lookback_years") or 0) if isinstance(pe_stats, dict) else 0,
                float(pb_stats.get("lookback_years") or 0) if isinstance(pb_stats, dict) else 0,
            )
            forward = (
                f"fPER {snapshot.get('forward_pe_status', 'unavailable')} / "
                f"fPBR {snapshot.get('forward_price_to_book_status', 'unavailable')}"
            )
            reasons = coverage.get("reason_codes", [])
            gap = ", ".join(str(item) for item in reasons) if isinstance(reasons, list) and reasons else "없음"
            financial_history = (
                f"{state.backfill_years_available:.1f}년" if state else "확인 불가"
            )
            sections.append(
                f"| {assessment.ticker} | {financial_history} | "
            )
            sections[-1] += (
                f"{coverage.get('financial_freshness', 'unavailable')} | "
                f"{len(dividends)}건 | {len(issues)}건 | {history_years:.1f}년 | "
                f"{forward} | {coverage.get('foreign_filing', 'not_applicable')} | {gap} |"
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
