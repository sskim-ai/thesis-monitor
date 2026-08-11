from dataclasses import dataclass
import re

from sqlmodel import Session, select

from app.models.security import SecurityMaster
from app.providers.base import RawEvent
from app.services.security_master_service import SecurityMasterService
from app.services.corporate_action_terms import is_buyback_text


OFFICIAL_PROVIDERS = {"opendart", "sec_edgar", "company_ir", "mock"}
HIGH_RISK_TERMS = (
    "capital raise",
    "equity offering",
    "secondary offering",
    "convertible",
    "dilution",
    "유상증자",
    "전환사채",
    "guidance",
    "forecast",
    "가이던스",
    "accounting",
    "restatement",
)


@dataclass(frozen=True)
class RelevanceVerdict:
    accepted: bool
    status: str
    subject_company_id: str | None
    evidence: list[str]
    reason: str | None = None


def _contains(text: str, alias: str) -> bool:
    alias = alias.strip().lower()
    if not alias:
        return False
    if re.fullmatch(r"[a-z0-9]+", alias):
        return re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", text) is not None
    return alias in text


class EventRelevanceService:
    def __init__(self) -> None:
        self.security_service = SecurityMasterService()

    def validate(
        self,
        session: Session,
        raw_event: RawEvent,
        target: SecurityMaster,
    ) -> RelevanceVerdict:
        if raw_event.provider in OFFICIAL_PROVIDERS:
            return RelevanceVerdict(
                True,
                "official_identity",
                target.canonical_company_id,
                [f"official_provider:{raw_event.provider}"],
            )
        text = f"{raw_event.title} {raw_event.summary}".lower()
        target_hits = [
            alias
            for alias in self.security_service.aliases(target)
            if _contains(text, alias)
        ]
        if raw_event.subject_ticker and raw_event.subject_ticker.upper() != target.ticker:
            return RelevanceVerdict(
                False,
                "rejected_company_mismatch",
                None,
                [f"subject_ticker:{raw_event.subject_ticker.upper()}"],
                "article_subject_is_different_security",
            )
        if not target_hits:
            return RelevanceVerdict(
                False,
                "rejected_no_company_match",
                None,
                [],
                "target_company_not_mentioned",
            )

        title = raw_event.title.lower()
        target_title_hits = [alias for alias in target_hits if _contains(title, alias)]
        if any(term in title for term in HIGH_RISK_TERMS) and not target_title_hits:
            return RelevanceVerdict(
                False,
                "rejected_primary_subject_mismatch",
                None,
                [f"target_only_outside_headline:{','.join(target_hits[:3])}"],
                "material_action_headline_does_not_name_target_company",
            )
        other_hits: list[tuple[SecurityMaster, str, int]] = []
        for security in session.exec(
            select(SecurityMaster).where(SecurityMaster.ticker != target.ticker)
        ).all():
            for alias in self.security_service.aliases(security):
                if _contains(title, alias):
                    other_hits.append((security, alias, title.find(alias)))
                    break
        target_title_positions = [title.find(alias) for alias in target_title_hits]
        target_position = min(target_title_positions) if target_title_positions else 10_000
        if (
            other_hits
            and any(term in title for term in HIGH_RISK_TERMS)
            and min(hit[2] for hit in other_hits) < target_position
        ):
            subject = min(other_hits, key=lambda item: item[2])[0]
            return RelevanceVerdict(
                False,
                "rejected_primary_subject_mismatch",
                subject.canonical_company_id,
                [f"primary_subject:{subject.ticker}", f"target_mentions:{','.join(target_hits[:3])}"],
                "material_action_belongs_to_other_company",
            )
        return RelevanceVerdict(
            True,
            "validated_company_match",
            target.canonical_company_id,
            [f"company_match:{alias}" for alias in target_hits[:5]],
        )

    @staticmethod
    def clear_material_flags(raw_event: RawEvent) -> None:
        for name in (
            "guidance_changed",
            "revenue_guidance_changed",
            "margin_guidance_changed",
            "earnings_guidance_changed",
            "cash_flow_guidance_changed",
            "major_order_change",
            "production_delay",
            "fcf_impact_known",
            "material_customer_change",
            "dilution_risk",
            "debt_liquidity_risk",
            "accounting_issue",
            "regulatory_material",
            "buyback_candidate",
            "confirmed_buyback",
        ):
            setattr(raw_event, name, False)


def extract_structured_flags(raw_event: RawEvent) -> None:
    if not raw_event.identity_validated:
        return
    if raw_event.claim_actor_type in {"unknown", "media"}:
        from app.services.event_identity import attribute_claim_actor

        raw_event.claim_actor, raw_event.claim_actor_type = attribute_claim_actor(
            raw_event
        )
    text = f"{raw_event.title} {raw_event.summary}".lower()
    guidance_terms = ("guidance", "forecast", "outlook", "가이던스", "전망")
    revenue_terms = ("revenue", "sales", "매출")
    company_guidance_actor = raw_event.claim_actor_type in {
        "company_management",
        "company_official_filing",
    }
    if company_guidance_actor and any(term in text for term in guidance_terms):
        raw_event.guidance_changed = True
        if any(term in text for term in revenue_terms):
            raw_event.revenue_guidance_changed = True
    if company_guidance_actor and any(
        term in text for term in ("margin guidance", "margin outlook", "마진 전망")
    ):
        raw_event.margin_guidance_changed = True
    if is_buyback_text(text):
        raw_event.buyback_candidate = True
        raw_event.confirmed_buyback = raw_event.provider in OFFICIAL_PROVIDERS
