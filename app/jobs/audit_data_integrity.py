import json

from sqlmodel import Session, select

from app.database import engine, init_db
from app.models.event import CanonicalIssue, Event
from app.models.watchlist import WatchlistItem
from app.services.issue_identity_audit_service import IssueIdentityAuditService


def run() -> dict[str, object]:
    init_db()
    service = IssueIdentityAuditService()
    results: list[dict[str, object]] = []
    with Session(engine) as session:
        tickers = [
            item.ticker
            for item in session.exec(
                select(WatchlistItem)
                .where(WatchlistItem.active.is_(True))
                .order_by(WatchlistItem.ticker)
            ).all()
        ]
        for ticker in tickers:
            changed = service.audit(session, ticker)
            invalid_documents = list(
                session.exec(
                    select(Event).where(
                        Event.ticker == ticker,
                        Event.document_identity_status.in_(
                            ("invalid", "invalid_mismatch")
                        ),
                    )
                ).all()
            )
            invalid_issues = list(
                session.exec(
                    select(CanonicalIssue).where(
                        CanonicalIssue.ticker == ticker,
                        CanonicalIssue.provenance_status == "invalid_provenance",
                    )
                ).all()
            )
            results.append(
                {
                    "ticker": ticker,
                    "changed_or_invalidated": changed,
                    "invalid_document_count": len(invalid_documents),
                    "invalid_issue_count": len(invalid_issues),
                }
            )
        session.commit()
    return {
        "ticker_count": len(results),
        "invalid_document_count": sum(
            int(item["invalid_document_count"]) for item in results
        ),
        "invalid_issue_count": sum(int(item["invalid_issue_count"]) for item in results),
        "tickers": results,
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
