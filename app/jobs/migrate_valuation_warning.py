import json
from datetime import timedelta

from sqlmodel import Session, select

from app.database import engine, init_db
from app.models.financial import FinancialSnapshot
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.services.historical_valuation_service import filing_date, financial_period_end
from app.services.warning_backfill_service import backfill_confirmed_warning_states


def migrate(session: Session) -> dict[str, int]:
    financial_rows = session.exec(select(FinancialSnapshot)).all()
    date_updates = 0
    for row in financial_rows:
        period_end = financial_period_end(row)
        filed = filing_date(row)
        changed = False
        if row.financial_period_end != period_end:
            row.financial_period_end = period_end
            changed = True
        if row.filing_date != filed:
            row.filing_date = filed
            changed = True
        if row.financials_as_of != period_end:
            row.financials_as_of = period_end
            changed = True
        if changed:
            session.add(row)
            date_updates += 1

    warning_updates = 0
    theses = session.exec(
        select(InvestmentThesis)
        .where(InvestmentThesis.status == "active")
        .order_by(InvestmentThesis.ticker, InvestmentThesis.version.desc())
    ).all()
    latest_by_ticker: dict[str, InvestmentThesis] = {}
    for thesis in theses:
        latest_by_ticker.setdefault(thesis.ticker, thesis)
    for thesis in latest_by_ticker.values():
        assessment = session.exec(
            select(ThesisAssessment)
            .where(ThesisAssessment.ticker == thesis.ticker)
            .order_by(ThesisAssessment.assessment_date.desc())
        ).first()
        if assessment is None:
            continue
        baseline = backfill_confirmed_warning_states(
            session, thesis, assessment.assessment_date + timedelta(days=1)
        )
        try:
            current = json.loads(assessment.warning_states or "[]")
        except json.JSONDecodeError:
            current = []
        by_warning = {
            str(item.get("warning")): item
            for item in current
            if isinstance(item, dict) and item.get("warning")
        }
        for item in baseline:
            by_warning.setdefault(str(item.get("warning")), item)
        open_warnings = [
            str(item["warning"])
            for item in by_warning.values()
            if item.get("status") in {"open", "escalated"}
        ]
        if open_warnings != json.loads(assessment.open_confirmed_warnings or "[]"):
            assessment.warning_states = json.dumps(list(by_warning.values()), ensure_ascii=False)
            assessment.open_warnings = json.dumps(open_warnings, ensure_ascii=False)
            assessment.open_confirmed_warnings = json.dumps(open_warnings, ensure_ascii=False)
            session.add(assessment)
            warning_updates += 1
    session.commit()
    return {"financial_date_updates": date_updates, "warning_updates": warning_updates}


def main() -> None:
    init_db()
    with Session(engine) as session:
        print(json.dumps(migrate(session), ensure_ascii=False))


if __name__ == "__main__":
    main()
