import json
from datetime import date

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.models.event import Event
from app.models.financial import FinancialSnapshot
from app.models.macro import ThesisMacroImpact
from app.models.thesis import InvestmentThesis
from app.schemas.thesis import AssessmentStatus, PriceContext
from app.services.thesis_evaluation_service import evaluate_thesis
from app.services.event_identity import event_fingerprint
from app.services.event_materiality_service import treasury_stock_materiality


def _thesis() -> InvestmentThesis:
    return InvestmentThesis(
        ticker="TEST",
        version=1,
        core_thesis="A major customer supports recurring demand",
        strengthen_signals="[]",
        weaken_signals="[]",
        invalidation_signals=json.dumps(["major customer terminates all orders"]),
    )


def _event(provider: str) -> Event:
    return Event(
        ticker="TEST",
        date=date.today(),
        source="Company filing",
        provider=provider,
        title="Major customer terminates all orders",
        url="https://example.com/customer-termination",
        event_type="customer_loss",
        confirmed_facts=json.dumps(["Major customer terminated all orders"]),
        inferred_implications="[]",
        unknowns="[]",
        relevance_score=90,
        relevance_reason="customer loss",
        requires_review=True,
    )


def test_trusted_explicit_invalidation_deactivates() -> None:
    result = evaluate_thesis(_thesis(), [_event("sec_edgar")], PriceContext())

    assert result.status == AssessmentStatus.invalidated
    assert result.should_deactivate is True


def test_untrusted_invalidation_signal_requires_review_without_invalidation() -> None:
    result = evaluate_thesis(_thesis(), [_event("google_news_rss")], PriceContext())

    assert result.status == AssessmentStatus.needs_review
    assert result.should_deactivate is False


def test_initial_baseline_consumes_events_without_scoring_daily_delta() -> None:
    event = _event("sec_edgar")

    result = evaluate_thesis(
        _thesis(),
        [event],
        PriceContext(),
        assessment_mode="initial_baseline",
    )

    assert result.status == AssessmentStatus.no_material_change
    assert result.daily_change_severity == "none"
    assert result.earnings_estimate_impact == "unchanged"
    assert result.valuation_context.impact == "neutral"
    assert result.should_deactivate is False
    assert result.evidence[0]["direction"] == "baseline"
    assert result.used_event_fingerprints


def test_baseline_contract_name_and_amount_remain_from_the_same_event() -> None:
    event = Event(
        ticker="TEST",
        date=date.today(),
        source="OpenDART",
        provider="opendart",
        title="단일판매ㆍ공급계약체결",
        url="https://example.com/contract",
        event_type="large_order",
        confirmed_facts=json.dumps(
            [
                "DART text supply contract fact: contract_name = Data center project",
                "DART text supply contract fact: amount = 318,964,597,910",
                "DART text supply contract fact: counterparty = Verified Customer",
                "DART text supply contract fact: recent_sales_ratio = 12.4",
                "DART text supply contract fact: period = 2026-08-14 to 2028-12-31",
            ]
        ),
        relevance_score=85,
    )

    result = evaluate_thesis(
        _thesis(),
        [event],
        PriceContext(),
        assessment_mode="initial_baseline",
    )

    assert result.evidence[0]["contract_name"] == "Data center project"
    assert result.evidence[0]["contract_amount"] == 318_964_597_910
    assert result.evidence[0]["counterparty"] == "Verified Customer"
    assert result.evidence[0]["sales_ratio_pct"] == 12.4
    assert result.evidence[0]["contract_period"] == "2026-08-14 to 2028-12-31"


def test_treasury_stock_materiality_uses_share_and_purpose_context() -> None:
    isolated_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(isolated_engine)
    event = Event(
        ticker="010120",
        date=date(2026, 8, 12),
        source="OpenDART",
        provider="opendart",
        title="자기주식처분결정",
        url="https://example.com/treasury",
        event_type="capital_allocation",
        confirmed_facts=json.dumps(
            [
                "OpenDART treasury stock fact: shares = 32,520 shares",
                "OpenDART treasury stock fact: purpose = 임직원 성과보상",
            ],
            ensure_ascii=False,
        ),
    )
    with Session(isolated_engine) as session:
        session.add(
            FinancialSnapshot(
                ticker="010120",
                period="2026-Q2",
                snapshot_type="full_statement",
                common_shares_outstanding=29_700_000,
            )
        )
        session.commit()

        result = treasury_stock_materiality(session, event, 208_500)

    assert result is not None
    assert result.level == "immaterial"
    assert result.share_ratio_pct == pytest.approx(0.1095, abs=0.0001)
    assert result.share_denominator_source == "common_shares_outstanding"


@pytest.mark.parametrize(
    ("shares", "expected"),
    [(300_000, "review"), (700_000, "material")],
)
def test_treasury_stock_materiality_thresholds(shares: int, expected: str) -> None:
    isolated_engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(isolated_engine)
    event = Event(
        ticker="CAP",
        date=date(2026, 8, 12),
        source="OpenDART",
        provider="opendart",
        title="자기주식처분결정",
        url=f"https://example.com/{shares}",
        event_type="capital_allocation",
        confirmed_facts=json.dumps(
            [
                f"OpenDART treasury stock fact: shares = {shares:,} shares",
                "OpenDART treasury stock fact: purpose = 임직원 성과보상",
            ],
            ensure_ascii=False,
        ),
    )
    with Session(isolated_engine) as session:
        session.add(
            FinancialSnapshot(
                ticker="CAP",
                period="2026-Q2",
                snapshot_type="full_statement",
                common_shares_outstanding=30_000_000,
            )
        )
        session.commit()
        result = treasury_stock_materiality(session, event, 100_000)

    assert result is not None
    assert result.level == expected


def test_treasury_unknown_is_not_automatically_needs_review() -> None:
    event = Event(
        ticker="TEST",
        date=date.today(),
        source="OpenDART",
        provider="opendart",
        title="자기주식처분결정",
        url="https://example.com/unknown-treasury",
        event_type="capital_allocation",
        confirmed_facts=json.dumps(
            ["OpenDART treasury stock fact: purpose = 기타"], ensure_ascii=False
        ),
        relevance_score=80,
        requires_review=True,
    )
    fingerprint = event_fingerprint(event)

    result = evaluate_thesis(
        _thesis(),
        [event],
        PriceContext(),
        event_materiality={fingerprint: "unknown"},
    )

    assert result.status == AssessmentStatus.no_material_change


def test_genuine_dilution_is_not_treated_as_treasury_noise() -> None:
    isolated_engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(isolated_engine)
    event = Event(
        ticker="CAP",
        date=date.today(),
        source="OpenDART",
        provider="opendart",
        title="유상증자결정",
        url="https://example.com/capital-raise",
        event_type="capital_raise",
        confirmed_facts=json.dumps(
            ["OpenDART capital raise fact: new_shares = 1,000,000 shares"]
        ),
    )
    with Session(isolated_engine) as session:
        assert treasury_stock_materiality(session, event, 100_000) is None


def test_rejected_trusted_event_is_excluded_from_assessment() -> None:
    event = _event("sec_edgar")
    event.document_identity_status = "validated"
    event.identity_status = "rejected_company_mismatch"
    event.rejected_reason = "article_subject_is_different_security"

    result = evaluate_thesis(_thesis(), [event], PriceContext())

    assert result.status == AssessmentStatus.no_material_change
    assert result.should_deactivate is False
    assert result.evidence == []


def test_valuation_signal_is_separate_from_operating_thesis_status() -> None:
    thesis = _thesis()
    thesis.market_expectations = json.dumps(
        {"level": "elevated", "summary": "Strong growth is already expected"}
    )
    thesis.valuation_framework = json.dumps(
        {"primary_method": "forward P/E", "key_inputs": ["normalized EPS"]}
    )
    thesis.multiple_expansion_signals = json.dumps(["new customer production order"])
    event = Event(
        ticker="TEST",
        date=date.today(),
        source="Company filing",
        provider="sec_edgar",
        title="New customer production order confirmed",
        url="https://example.com/new-order",
        event_type="other",
        confirmed_facts=json.dumps(["New customer production order confirmed"]),
        inferred_implications="[]",
        unknowns="[]",
        relevance_score=70,
        relevance_reason="new order",
        requires_review=False,
    )

    result = evaluate_thesis(thesis, [event], PriceContext())

    assert result.status == AssessmentStatus.no_material_change
    assert result.valuation_context.impact == "expansion"
    assert result.valuation_context.market_expectation_level == "elevated"
    assert result.valuation_context.matched_expansion_conditions == [
        "new customer production order"
    ]


def test_macro_can_compress_valuation_without_weakening_business_thesis() -> None:
    thesis = _thesis()
    thesis.market_expectations = json.dumps(
        {"level": "very_high", "summary": "Growth is already highly expected"}
    )
    thesis.valuation_framework = json.dumps({"primary_method": "forward P/E"})
    macro = ThesisMacroImpact(
        ticker="TEST",
        thesis_version=1,
        assessment_date=date.today(),
        direction="neutral",
        magnitude=3,
        valuation_effect="weaken",
        rationale="Higher real yields raise the discount rate",
    )

    result = evaluate_thesis(thesis, [], PriceContext(), macro_impact=macro)

    assert result.status == AssessmentStatus.no_material_change
    assert result.valuation_context.impact == "compression"
    assert result.earnings_estimate_impact == "unchanged"


def test_good_earnings_with_very_high_expectations_is_new_expansion_evidence() -> None:
    thesis = _thesis()
    thesis.market_expectations = json.dumps(
        {"level": "very_high", "summary": "A strong earnings outcome is already expected"}
    )
    thesis.valuation_framework = json.dumps({"primary_method": "forward P/E"})
    thesis.strengthen_signals = json.dumps(["quarterly earnings beat"])
    event = Event(
        ticker="TEST",
        date=date.today(),
        source="Company filing",
        provider="sec_edgar",
        title="Quarterly earnings beat confirmed",
        url="https://example.com/earnings-beat",
        event_type="earnings_beat",
        confirmed_facts=json.dumps(["Revenue and operating profit beat guidance"]),
        inferred_implications="[]",
        unknowns="[]",
        relevance_score=70,
        relevance_reason="earnings beat",
    )

    result = evaluate_thesis(thesis, [event], PriceContext())

    assert result.status == AssessmentStatus.strengthened
    assert result.earnings_estimate_impact == "up"
    assert result.valuation_context.impact == "expansion"
