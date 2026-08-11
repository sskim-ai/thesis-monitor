import hashlib
import json
import re
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models.event import CanonicalIssue, Event
from app.models.financial import FinancialSnapshot
from app.services.corporate_action_terms import (
    buyback_authorization_amount,
    is_buyback_text,
)
from app.services.event_identity import event_fingerprint


_ACTION_TYPES = {
    "capital_raise",
    "convertible_bond",
    "warrant",
    "dilution",
    "buyback",
    "share_retirement",
    "dividend",
    "stock_split",
    "reverse_split",
    "capital_reduction",
}


def _json_list(value: str | None) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _fact_number(facts: list[str], labels: tuple[str, ...]) -> float | None:
    for fact in facts:
        if not any(label in fact for label in labels):
            continue
        match = re.search(r"=\s*([-\d,]+(?:\.\d+)?)", fact)
        if match:
            return float(match.group(1).replace(",", ""))
    return None


def _execution_status(title: str) -> str:
    lowered = title.lower()
    if any(term in lowered for term in ("취소", "철회", "cancel")):
        return "cancelled"
    if any(term in lowered for term in ("발행결과", "발행실적", "완료", "result", "completed")):
        return "completed"
    if any(term in lowered for term in ("정정", "변경", "amend", "updated")):
        return "updated"
    if any(term in lowered for term in ("발행가", "pricing", "확정")):
        return "priced"
    return "announced"


def _issue_type(event: Event) -> str | None:
    if event.event_type in _ACTION_TYPES:
        return event.event_type
    text = event.title.lower()
    if "유상증자" in text or "equity offering" in text:
        return "capital_raise"
    if "전환사채" in text or "convertible" in text:
        return "convertible_bond"
    if "신주인수권" in text or "warrant" in text:
        return "warrant"
    if event.buyback_candidate or event.confirmed_buyback or is_buyback_text(text):
        return "buyback"
    if "소각" in text or "share retirement" in text:
        return "share_retirement"
    if "배당" in text or "dividend" in text:
        return "dividend"
    if "reverse split" in text or "주식병합" in text:
        return "reverse_split"
    if "stock split" in text or "주식분할" in text:
        return "stock_split"
    if "감자" in text or "capital reduction" in text:
        return "capital_reduction"
    return None


class CapitalActionService:
    def reconcile_identity(
        self, session: Session, event: Event
    ) -> CanonicalIssue | None:
        if not event.issue_id or not event.identity_status.startswith("rejected"):
            return None
        issue = session.exec(
            select(CanonicalIssue).where(CanonicalIssue.issue_key == event.issue_id)
        ).first()
        if issue is None:
            return None
        valid_linked_event = session.exec(
            select(Event).where(
                Event.issue_id == issue.issue_key,
                Event.id != event.id,
                Event.identity_validated.is_(True),
                Event.event_type != "non_thesis_noise",
            )
        ).first()
        if valid_linked_event is not None:
            return issue
        issue.status = "resolved"
        issue.execution_status = "cancelled"
        issue.economic_status = "resolved"
        issue.warnings = json.dumps(
            ["Security identity mismatch로 잘못 연결된 문서여서 경제적 경고에서 제외했습니다."],
            ensure_ascii=False,
        )
        issue.updated_at = datetime.now(timezone.utc)
        session.add(issue)
        event.issue_id = None
        event.corporate_action_id = None
        session.add(event)
        return issue

    def canonicalize(self, session: Session, event: Event) -> CanonicalIssue | None:
        if event.event_type == "non_thesis_noise":
            return None
        if event.provider in {"google_news_rss", "naver_news", "newsapi"} and not event.identity_validated:
            return None
        action_type = _issue_type(event)
        if action_type is None:
            return None
        existing = list(
            session.exec(
                select(CanonicalIssue)
                .where(
                    CanonicalIssue.ticker == event.ticker,
                    CanonicalIssue.issue_type == action_type,
                )
                .order_by(CanonicalIssue.latest_event_date.desc())
            ).all()
        )
        issue = next(
            (
                item for item in existing
                if abs((event.date - item.latest_event_date).days) <= 366
                and item.execution_status != "cancelled"
            ),
            None,
        )
        if issue is None:
            seed = f"{event.ticker}|{action_type}|{event.date:%Y-%m}"
            issue_key = hashlib.sha256(seed.encode()).hexdigest()[:20]
            issue = CanonicalIssue(
                ticker=event.ticker,
                issue_key=issue_key,
                issue_type=action_type,
                opened_date=event.date,
                updated_date=event.date,
                latest_event_date=event.date,
                title=f"{action_type} 경제적 영향",
            )
        facts = _json_list(event.confirmed_facts)
        new_shares = _fact_number(
            facts,
            ("capital raise fact: new_shares", "convertible bond fact: convertible_shares"),
        ) or event.dilution_amount
        proceeds = _fact_number(
            facts,
            ("capital raise fact: amount", "convertible bond fact: amount"),
        ) or event.financing_amount
        if action_type == "buyback":
            new_shares = _fact_number(
                facts,
                ("treasury stock fact: shares", "buyback fact: shares"),
            )
            proceeds = _fact_number(
                facts,
                ("treasury stock fact: amount", "buyback fact: amount"),
            ) or buyback_authorization_amount(
                f"{event.title} {event.raw_summary or ''}"
            )
        previous = session.exec(
            select(FinancialSnapshot)
            .where(FinancialSnapshot.ticker == event.ticker)
            .order_by(FinancialSnapshot.filing_date.desc())
        ).first()
        pre_shares = (
            previous.common_shares_outstanding
            if previous and previous.common_shares_outstanding
            else issue.pre_action_share_count
        )
        issue.pre_action_share_count = pre_shares
        issue.new_shares = new_shares or issue.new_shares
        if pre_shares is not None and issue.new_shares is not None:
            issue.post_action_share_count = (
                pre_shares - issue.new_shares
                if action_type in {"buyback", "share_retirement"}
                else pre_shares + issue.new_shares
            )
        issue.dilution_pct = (
            issue.new_shares / pre_shares * 100
            if pre_shares and issue.new_shares is not None
            else None
        )
        if action_type in {"buyback", "share_retirement"} and pre_shares and issue.new_shares:
            issue.dilution_pct = -(issue.new_shares / pre_shares * 100)
        issue.proceeds = proceeds or issue.proceeds
        issue.execution_status = _execution_status(event.title)
        issue.status = (
            "updated"
            if issue.id
            else "candidate"
            if action_type == "buyback" and not event.confirmed_buyback
            else "opened"
        )
        if action_type == "buyback":
            issue.official_verification_status = (
                "verified"
                if event.confirmed_buyback
                else issue.official_verification_status
                if issue.official_verification_status == "verified"
                else "candidate"
            )
        if issue.execution_status == "completed":
            issue.status = "confirmed"
        elif issue.execution_status == "cancelled":
            issue.status = "resolved"
            issue.economic_status = "resolved"
        else:
            issue.economic_status = (
                "monitoring"
                if action_type in {"buyback", "share_retirement", "dividend", "stock_split"}
                else "open"
            )
        issue.updated_date = event.date
        issue.latest_event_date = max(issue.latest_event_date, event.date)
        ids = _json_list(issue.event_ids)
        fingerprint = event_fingerprint(event)
        if fingerprint not in ids:
            ids.append(fingerprint)
        issue.event_ids = json.dumps(ids)
        warnings = []
        if issue.dilution_pct is None and action_type in {
            "capital_raise",
            "convertible_bond",
            "warrant",
            "dilution",
        }:
            warnings.append("신주 수와 기존 주식수의 일관된 기준이 부족해 희석률 정량화를 보류합니다.")
        issue.warnings = json.dumps(warnings, ensure_ascii=False)
        issue.updated_at = datetime.now(timezone.utc)
        session.add(issue)
        session.flush()
        event.issue_id = issue.issue_key
        event.corporate_action_id = issue.issue_key
        session.add(event)
        return issue
