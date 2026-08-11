import json

from sqlmodel import Session, select

from app.models.event import CanonicalIssue, Event
from app.providers.base import RawEvent
from app.services.capital_action_service import CapitalActionService
from app.services.event_relevance_service import EventRelevanceService
from app.services.security_master_service import SecurityMasterService


class IssueIdentityAuditService:
    def audit(self, session: Session, ticker: str) -> int:
        open_issue_keys = [
            issue.issue_key
            for issue in session.exec(
                select(CanonicalIssue).where(
                    CanonicalIssue.ticker == ticker,
                    CanonicalIssue.economic_status == "open",
                )
            ).all()
        ]
        if not open_issue_keys:
            return 0
        target = SecurityMasterService().ensure(session, ticker)
        relevance = EventRelevanceService()
        capital = CapitalActionService()
        resolved = 0
        for event in session.exec(
            select(Event).where(
                Event.ticker == ticker,
                Event.issue_id.in_(open_issue_keys),
                Event.provider.in_(("google_news_rss", "naver_news", "newsapi")),
            )
        ).all():
            raw = RawEvent(
                ticker=event.ticker,
                company_name=None,
                date=event.date,
                source=event.source,
                title=event.title,
                url=event.url,
                summary=event.raw_summary or event.title,
                provider=event.provider,
                confirmed_facts=json.loads(event.confirmed_facts or "[]"),
            )
            verdict = relevance.validate(session, raw, target)
            if verdict.accepted:
                continue
            event.identity_validated = False
            event.identity_status = verdict.status
            event.subject_company_id = verdict.subject_company_id
            event.relevance_evidence = json.dumps(verdict.evidence, ensure_ascii=False)
            event.rejected_reason = verdict.reason
            event.event_type = "non_thesis_noise"
            event.dilution_risk = False
            event.guidance_changed = False
            event.revenue_guidance_changed = False
            event.margin_guidance_changed = False
            event.requires_review = False
            event.relevance_score = 0
            event.relevance_reason = verdict.reason or "identity_mismatch"
            if capital.reconcile_identity(session, event) is not None:
                resolved += 1
            session.add(event)
        session.flush()
        return resolved
