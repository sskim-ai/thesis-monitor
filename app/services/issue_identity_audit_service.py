import json
from dataclasses import dataclass

from sqlmodel import Session, select

from app.models.event import CanonicalIssue, Event
from app.providers.base import RawEvent
from app.services.capital_action_service import CapitalActionService
from app.services.event_relevance_service import EventRelevanceService
from app.services.security_master_service import SecurityMasterService
from app.services.event_identity import (
    event_fingerprint,
    event_has_valid_document_identity,
    source_document_id_from_facts,
    source_document_id_from_url,
)


_OFFICIAL_PROVIDERS = {"opendart", "sec_edgar", "company_ir"}
_EXPECTED_EVENT_TYPES = {
    "capital_raise": {"capital_raise"},
    "convertible_bond": {"convertible_bond"},
    "warrant": {"warrant"},
    "dilution": {"dilution", "capital_raise", "convertible_bond", "warrant"},
    "buyback": {"buyback", "capital_allocation"},
    "share_retirement": {"share_retirement"},
    "dividend": {"dividend"},
    "stock_split": {"stock_split"},
    "reverse_split": {"reverse_split"},
    "capital_reduction": {"capital_reduction"},
}


@dataclass(frozen=True)
class WarningProvenanceAudit:
    ticker: str
    issue_key: str
    issue_type: str
    valid: bool
    source_event_ids: list[str]
    source_titles: list[str]
    reason: str


class IssueIdentityAuditService:
    def audit_document_identity(self, session: Session, ticker: str) -> int:
        invalid = 0
        events = list(
            session.exec(
                select(Event).where(
                    Event.ticker == ticker,
                    Event.provider.in_(("opendart", "sec_edgar")),
                )
            ).all()
        )
        for event in events:
            try:
                facts = json.loads(event.confirmed_facts or "[]")
            except json.JSONDecodeError:
                facts = []
            fact_id = (
                source_document_id_from_facts([str(item) for item in facts])
                if isinstance(facts, list)
                else None
            )
            url_id = source_document_id_from_url(event.url)
            identifiers = [
                item for item in (url_id, fact_id, event.source_document_id) if item
            ]
            if not identifiers:
                continue
            if len(set(identifiers)) == 1:
                event.source_document_id = identifiers[0]
                event.document_identity_status = "validated"
            else:
                invalid += 1
                event.document_identity_status = "invalid_mismatch"
                event.identity_validated = False
                event.requires_review = False
                event.relevance_score = 0
                event.classification_override_reason = "source_document_identity_mismatch"
                event.rejected_reason = "source_document_identity_mismatch"
            session.add(event)
        session.flush()
        return invalid

    def audit_provenance(
        self, session: Session, ticker: str
    ) -> list[WarningProvenanceAudit]:
        events = list(session.exec(select(Event).where(Event.ticker == ticker)).all())
        by_fingerprint = {event_fingerprint(event): event for event in events}
        results: list[WarningProvenanceAudit] = []
        for issue in session.exec(
            select(CanonicalIssue).where(CanonicalIssue.ticker == ticker)
        ).all():
            source_ids = [
                str(item)
                for item in json.loads(issue.event_ids or "[]")
                if str(item)
            ]
            linked = [by_fingerprint[item] for item in source_ids if item in by_fingerprint]
            expected = _EXPECTED_EVENT_TYPES.get(issue.issue_type, {issue.issue_type})
            valid_events = [
                event
                for event in linked
                if event.provider in _OFFICIAL_PROVIDERS
                and event.event_type in expected
                and event_has_valid_document_identity(event)
            ]
            valid = bool(valid_events)
            reason = "official_source_and_event_type_match" if valid else "no_matching_official_source"
            if valid:
                issue.provenance_status = "valid"
                issue.official_verification_status = "verified"
            else:
                issue.provenance_status = "invalid_provenance"
                issue.official_verification_status = "invalid"
                issue.status = "invalidated_source"
                issue.execution_status = "cancelled"
                issue.economic_status = "resolved"
                issue.warnings = json.dumps(
                    ["출처 event 유형 또는 공식성 검증에 실패해 현재 경고에서 제외했습니다."],
                    ensure_ascii=False,
                )
                for event in linked:
                    if event.provider not in _OFFICIAL_PROVIDERS:
                        event.classification_override_reason = "invalidated_issue_provenance"
                        event.dilution_risk = False
                        event.requires_review = False
                        event.relevance_score = 0
                        event.relevance_reason = "canonical issue provenance invalidated"
                        if event.event_type in {
                            "capital_raise",
                            "convertible_bond",
                            "warrant",
                            "dilution",
                        }:
                            event.event_type = "non_thesis_noise"
                        session.add(event)
            session.add(issue)
            results.append(
                WarningProvenanceAudit(
                    ticker=ticker,
                    issue_key=issue.issue_key,
                    issue_type=issue.issue_type,
                    valid=valid,
                    source_event_ids=source_ids,
                    source_titles=[event.title for event in linked],
                    reason=reason,
                )
            )
        session.flush()
        return results

    def audit(self, session: Session, ticker: str) -> int:
        invalid_document_count = self.audit_document_identity(session, ticker)
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
            self.audit_provenance(session, ticker)
            return invalid_document_count
        target = SecurityMasterService().ensure(session, ticker)
        relevance = EventRelevanceService()
        capital = CapitalActionService()
        invalidated_issue_keys: set[str] = set()
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
                if event.issue_id:
                    invalidated_issue_keys.add(event.issue_id)
            session.add(event)
        session.flush()
        provenance = self.audit_provenance(session, ticker)
        invalidated_issue_keys.update(
            item.issue_key for item in provenance if not item.valid
        )
        return invalid_document_count + len(invalidated_issue_keys)
