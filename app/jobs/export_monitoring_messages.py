import argparse
from datetime import date
from pathlib import Path

from sqlmodel import Session, select

from app.database import engine, init_db
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.services.daily_digest import build_daily_digest
from app.services.daily_digest_renderer import render_daily_digest
from app.services.notification_service import _assessment_report


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
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(sections) + "\n", encoding="utf-8")
    return len(assessments)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export rendered daily monitoring messages.")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--output")
    args = parser.parse_args()
    run_date = date.fromisoformat(args.date)
    output = Path(args.output or f"data/reports/{run_date}-monitoring-messages.md")
    count = export_messages(run_date, output)
    print(f"exported={count} output={output.resolve()}")


if __name__ == "__main__":
    main()
