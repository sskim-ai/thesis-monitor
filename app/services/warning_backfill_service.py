import hashlib
import json
import re
from datetime import date

from sqlmodel import Session, select

from app.models.event import CanonicalIssue, Event
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.services.event_identity import event_fingerprint


_TRUSTED = {"opendart", "sec_edgar", "company_ir"}
_NEGATIVE_TYPES = {
    "revenue_guidance_down", "margin_deterioration", "fcf_deterioration",
    "customer_loss", "capital_raise", "dilution", "accounting_issue",
    "debt_liquidity_risk", "earnings_miss", "production_delay",
}
_RESOLUTION = {
    "FCF": "FCF 흑자 전환과 반복 가능한 현금창출이 확인",
    "영업이익률": "영업이익률의 의미 있는 회복이 반복 확인",
    "마진": "마진의 의미 있는 회복이 반복 확인",
    "가이던스": "회사의 공식 가이던스 회복 확인",
    "고객": "고객 관계 또는 대체 수요의 회복이 확정 근거로 확인",
    "희석": "희석 영향 반영과 자본구조 안정이 확인",
    "부채": "부채·유동성 지표의 안정이 확인",
}


def _json_list(value: str | None) -> list[object]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _resolution(warning: str) -> str:
    return next(
        (text for marker, text in _RESOLUTION.items() if marker.lower() in warning.lower()),
        "반대 방향의 신뢰 가능한 확정 근거 확인",
    )


def _event_warning_facts(event: Event) -> list[str]:
    markers = (
        "유상증자", "전환사채", "희석", "적자", "감소", "하락", "악화",
        "이탈", "중단", "지연", "부채", "유동성", "회계", "guidance down",
        "margin", "negative fcf", "customer loss", "dilution",
    )
    warnings: list[str] = []
    for raw in _json_list(event.confirmed_facts):
        if not isinstance(raw, str) or not raw.strip():
            continue
        fact = raw.strip()
        lowered = fact.lower()
        if any(term in lowered for term in ("receipt number", "accession number", "document id")):
            continue
        if fact.startswith("OpenDART filing title:"):
            title = fact.split(":", 1)[1].strip()
            if any(marker in title.lower() for marker in markers):
                warnings.append(f"{title} 공시 확인")
            continue
        if fact.startswith("SEC EDGAR recent filing form:"):
            continue
        if any(marker in lowered for marker in markers):
            warnings.append(fact)
    if not warnings and any(marker in event.title.lower() for marker in markers):
        warnings.append(f"{event.title} 확인")
    return list(dict.fromkeys(warnings))


def _state(
    ticker: str,
    warning: str,
    opened: date,
    source: str,
    source_ids: list[str],
    warning_id: str | None = None,
) -> dict[str, object]:
    return {
        "warning_id": warning_id or hashlib.sha256(f"{ticker}|{warning}".encode()).hexdigest()[:16],
        "ticker": ticker,
        "warning": warning,
        "warning_type": "confirmed_fundamental",
        "opened_date": opened.isoformat(),
        "last_confirmed_date": opened.isoformat(),
        "status": "open",
        "resolution_condition": _resolution(warning),
        "source": source,
        "source_event_ids": source_ids,
    }


def _thesis_confirmed_warnings(thesis: InvestmentThesis) -> list[str]:
    text = thesis.core_thesis
    warnings: list[str] = []
    explicit_patterns = (
        (r"(?:현재(?:는)?[^.]{0,120})?(영업이익률 저하|자동차 마진 약화)", "영업이익률 저하 확인"),
        (r"(?:현재(?:는)?[^.]{0,140})?(FCF 적자)", "FCF 적자 확인"),
        (r"(?:확정|발생|현재)[^.]{0,80}(고객 이탈)", "주요 고객 이탈 확인"),
        (r"(?:확정|발생|현재)[^.]{0,80}(희석)", "주주가치 희석 확인"),
    )
    for pattern, warning in explicit_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        context = match.group(0)
        if any(term in context for term in ("가능성", "여부", "미증명", "확인 필요")):
            continue
        warnings.append(warning)
    return list(dict.fromkeys(warnings))


def backfill_confirmed_warning_states(
    session: Session,
    thesis: InvestmentThesis,
    as_of: date,
) -> list[dict[str, object]]:
    states: dict[str, dict[str, object]] = {}
    assessments = session.exec(
        select(ThesisAssessment)
        .where(ThesisAssessment.ticker == thesis.ticker, ThesisAssessment.assessment_date < as_of)
        .order_by(ThesisAssessment.assessment_date)
    ).all()
    for assessment in assessments:
        for raw in _json_list(assessment.warning_states):
            if isinstance(raw, dict) and raw.get("warning") and raw.get("status") in {"open", "escalated"}:
                states[str(raw["warning"])] = dict(raw)
        for raw in _json_list(assessment.open_confirmed_warnings or assessment.open_warnings):
            if isinstance(raw, str) and raw.strip():
                states.setdefault(
                    raw,
                    _state(thesis.ticker, raw, assessment.assessment_date, "assessment_history", []),
                )
    events = session.exec(
        select(Event)
        .where(Event.ticker == thesis.ticker, Event.date < as_of)
        .order_by(Event.date)
    ).all()
    for event in events:
        if event.provider not in _TRUSTED or event.event_type not in _NEGATIVE_TYPES:
            continue
        if event.issue_id:
            continue
        for fact in _event_warning_facts(event):
            states.setdefault(
                fact,
                _state(
                    thesis.ticker,
                    fact,
                    event.date,
                    "thesis_event",
                    [event_fingerprint(event)],
                ),
            )
    issues = session.exec(
        select(CanonicalIssue).where(
            CanonicalIssue.ticker == thesis.ticker,
            CanonicalIssue.economic_status == "open",
        )
    ).all()
    issue_labels = {
        "capital_raise": "유상증자에 따른 희석·자본조달 경제적 영향",
        "convertible_bond": "전환사채의 잠재 희석·자본조달 경제적 영향",
        "warrant": "신주인수권의 잠재 희석 영향",
        "dilution": "주당가치 희석 영향",
    }
    for issue in issues:
        warning = issue_labels.get(issue.issue_type, issue.title)
        states.setdefault(
            warning,
            _state(
                thesis.ticker,
                warning,
                issue.opened_date,
                "canonical_issue",
                _json_list(issue.event_ids),
                warning_id=issue.issue_key,
            ),
        )
    for warning in _thesis_confirmed_warnings(thesis):
        states.setdefault(
            warning,
            _state(thesis.ticker, warning, thesis.created_at.date(), "saved_thesis", []),
        )
    return list(states.values())
