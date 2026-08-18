import json
from datetime import date

from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.models.company import Company
from app.models.security import SecurityMaster
from app.models.thesis import ThesisAssessment
from app.services.peer_sector_valuation_service import build_peer_valuation_states
from app.services.numeric_semantic_registry import build_numeric_registry


ASSESSMENT_DATE = date(2026, 8, 18)
PRICE_DATE = "2026-08-17"


def _engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


def _valuation(
    pe: float = 10.0,
    pb: float = 1.5,
    *,
    price_date: str = PRICE_DATE,
    eps: float = 10.0,
    bvps: float = 50.0,
    forward_pe: float = 12.0,
    forward_source: str = "consensus_forward",
    period_end: str = "2026-06-30",
    basis_conflict: bool = False,
) -> str:
    return json.dumps(
        {
            "price_as_of": price_date,
            "ttm_eps": eps,
            "bvps": bvps,
            "trailing_pe": pe if eps > 0 else None,
            "trailing_pe_status": "value" if eps > 0 else "not_meaningful",
            "trailing_pe_source": "derived",
            "trailing_pe_basis_status": "directly_comparable",
            "trailing_pe_denominator_period_end": period_end,
            "trailing_pe_denominator_filing_date": "2026-08-01",
            "price_to_book": pb if bvps > 0 else None,
            "price_to_book_status": "value" if bvps > 0 else "not_meaningful",
            "price_to_book_source": "derived",
            "price_to_book_basis_status": "directly_comparable",
            "pbr_denominator_period_end": period_end,
            "pbr_denominator_filing_date": "2026-08-01",
            "forward_eps": 8.0,
            "forward_pe": forward_pe,
            "forward_pe_status": "value",
            "forward_pe_source": forward_source,
            "forward_pe_basis_status": "directly_comparable",
            "forward_pe_input_period": "FY1",
            "trailing_pe_basis_conflict": basis_conflict,
            "multiple_basis_conflicts": ["trailing_pe"] if basis_conflict else [],
        }
    )


def _assessment(ticker: str, valuation: str) -> ThesisAssessment:
    return ThesisAssessment(
        ticker=ticker,
        thesis_version=1,
        assessment_date=ASSESSMENT_DATE,
        status="no_material_change",
        summary="summary",
        new_buyer_view="observer",
        holder_view="holder",
        price_view="price",
        risk_level="normal",
        valuation_snapshot=valuation,
    )


def _seed(
    session: Session,
    rows: list[tuple[str, str]],
    *,
    taxonomy: dict[str, str | None] | None = None,
    industries: dict[str, str] | None = None,
    issuer_ids: dict[str, str] | None = None,
    identity_warnings: dict[str, list[str]] | None = None,
) -> tuple[list[ThesisAssessment], object]:
    taxonomy = taxonomy or {ticker: "shipping" for ticker, _ in rows}
    industries = industries or {
        ticker: "Transportation and Logistics" for ticker, _ in rows
    }
    issuer_ids = issuer_ids or {ticker: f"issuer:{ticker}" for ticker, _ in rows}
    identity_warnings = identity_warnings or {}
    assessments: list[ThesisAssessment] = []
    for ticker, valuation in rows:
        session.add(
            Company(
                ticker=ticker,
                company_name=ticker,
                exchange="NYSE",
                industry=industries[ticker],
                sector="Industrials",
            )
        )
        session.add(
            SecurityMaster(
                canonical_company_id=issuer_ids[ticker],
                canonical_security_id=f"security:{ticker}",
                ticker=ticker,
                exchange="NYSE",
                country="US",
                company_name=ticker,
                security_type="common_stock",
                issuer_type="domestic_us",
                identity_quality="verified",
                identity_provider="fixture_identity",
                identity_warnings=json.dumps(identity_warnings.get(ticker, [])),
            )
        )
        assessment = _assessment(ticker, valuation)
        assessments.append(assessment)
        session.add(assessment)
    session.commit()

    def profile_reader(ticker: str, _data_dir: object) -> dict[str, object]:
        return {
            "quality": "verified",
            "taxonomy_key": taxonomy[ticker],
            "industry": industries[ticker],
            "sector": "Industrials",
        }

    return assessments, profile_reader


def _states(
    rows: list[tuple[str, str]],
    **kwargs: object,
) -> dict[str, dict[str, object]]:
    engine = _engine()
    with Session(engine) as session:
        assessments, reader = _seed(session, rows, **kwargs)
        return build_peer_valuation_states(
            session,
            assessments,
            ASSESSMENT_DATE,
            profile_reader=reader,
            data_dir="unused",
        )


def test_same_exchange_session_peer_statistics_are_point_in_time() -> None:
    states = _states(
        [
            ("TARGET", _valuation(10.0, 1.5)),
            ("PEER1", _valuation(6.0, 0.8)),
            ("PEER2", _valuation(8.0, 1.0)),
            ("PEER3", _valuation(10.0, 1.2)),
        ]
    )
    state = states["TARGET"]
    pe = state["metrics"]["trailing_pe"]

    assert state["contract"] == "peer-sector-valuation-v1"
    assert state["assessment_date"] == "2026-08-18"
    assert state["as_of_date"] == PRICE_DATE
    assert state["sample_quality"] == "MEDIUM"
    assert pe["available"] is True
    assert pe["median"] == 8.0
    assert pe["company_relative_multiple"] == 1.25
    assert pe["company_vs_median_pct"] == 25.0
    assert pe["company_cross_section_percentile"] == 75.0


def test_stale_peer_is_excluded_from_same_session_sample() -> None:
    states = _states(
        [
            ("TARGET", _valuation()),
            ("PEER1", _valuation(6.0)),
            ("PEER2", _valuation(8.0)),
            ("PEER3", _valuation(10.0, price_date="2026-08-14")),
        ]
    )
    state = states["TARGET"]
    assert state["metrics"]["trailing_pe"]["available"] is False
    assert state["metrics"]["trailing_pe"]["sample_count"] == 2
    excluded = state["audit"]["metrics"]["trailing_pe"]["excluded"]
    assert {item["reason"] for item in excluded} == {"stale_metric"}


def test_same_issuer_share_classes_have_one_distribution_weight() -> None:
    rows = [
        ("TARGET", _valuation()),
        ("CLASSA", _valuation(6.0)),
        ("CLASSC", _valuation(6.2)),
        ("PEER2", _valuation(8.0)),
        ("PEER3", _valuation(10.0)),
    ]
    issuer_ids = {ticker: f"issuer:{ticker}" for ticker, _ in rows}
    issuer_ids["CLASSA"] = "issuer:alphabet"
    issuer_ids["CLASSC"] = "issuer:alphabet"
    state = _states(rows, issuer_ids=issuer_ids)["TARGET"]

    assert state["metrics"]["trailing_pe"]["sample_count"] == 3
    assert state["audit"]["duplicate_issuer_exclusions"] == {
        "CLASSC": "same_issuer_duplicate"
    }


def test_broad_sector_fallback_is_audit_only_low_quality() -> None:
    rows = [
        ("TARGET", _valuation()),
        ("PEER1", _valuation(6.0)),
        ("PEER2", _valuation(8.0)),
        ("PEER3", _valuation(10.0)),
    ]
    taxonomy = {ticker: f"taxonomy_{ticker}" for ticker, _ in rows}
    industries = {ticker: f"industry_{ticker}" for ticker, _ in rows}
    state = _states(rows, taxonomy=taxonomy, industries=industries)["TARGET"]
    pe = state["metrics"]["trailing_pe"]

    assert state["group_basis"] == "sector"
    assert state["available"] is False
    assert pe["available"] is False
    assert pe["audit_available"] is True
    assert pe["reason"] == "broad_fallback_low_quality"


def test_forward_consensus_and_modeled_samples_never_mix() -> None:
    states = _states(
        [
            ("TARGET", _valuation(forward_pe=15.0)),
            ("PEER1", _valuation(forward_pe=9.0)),
            ("PEER2", _valuation(forward_pe=12.0)),
            ("PEER3", _valuation(forward_pe=18.0)),
        ]
    )
    metrics = states["TARGET"]["metrics"]

    assert metrics["forward_pe_consensus"]["available"] is True
    assert metrics["forward_pe_consensus"]["median"] == 12.0
    assert metrics["forward_pe_modeled"]["available"] is False
    assert metrics["forward_pe_modeled"]["sample_count"] == 0


def test_biotech_generic_pe_and_pbr_are_suppressed() -> None:
    rows = [(ticker, _valuation()) for ticker in ("TARGET", "P1", "P2", "P3")]
    taxonomy = {ticker: "biotech" for ticker, _ in rows}
    industries = {ticker: "Biotechnology and Pharmaceuticals" for ticker, _ in rows}
    state = _states(rows, taxonomy=taxonomy, industries=industries)["TARGET"]

    assert state["available"] is False
    assert state["interpretation_contract"]["rule"] == "peer_valuation_not_meaningful"
    assert state["metrics"]["trailing_pe"]["reason"] == (
        "industry_metric_not_meaningful"
    )
    assert state["metrics"]["price_to_book"]["reason"] == (
        "industry_metric_not_meaningful"
    )


def test_negative_eps_and_equity_are_explicit_exclusions() -> None:
    states = _states(
        [
            ("TARGET", _valuation()),
            ("LOSS", _valuation(eps=-1.0)),
            ("NEGBOOK", _valuation(bvps=-1.0)),
            ("PEER3", _valuation()),
            ("PEER4", _valuation()),
        ]
    )
    audit = states["TARGET"]["audit"]["metrics"]
    pe_reasons = {item["ticker"]: item["reason"] for item in audit["trailing_pe"]["excluded"]}
    pb_reasons = {
        item["ticker"]: item["reason"] for item in audit["price_to_book"]["excluded"]
    }

    assert pe_reasons["LOSS"] == "negative_eps"
    assert pb_reasons["NEGBOOK"] == "negative_equity"


def test_period_and_provider_conflicts_are_excluded() -> None:
    states = _states(
        [
            ("TARGET", _valuation()),
            ("OLDPERIOD", _valuation(period_end="2025-06-30")),
            ("CONFLICT", _valuation(basis_conflict=True)),
            ("PEER3", _valuation()),
            ("PEER4", _valuation()),
        ]
    )
    excluded = states["TARGET"]["audit"]["metrics"]["trailing_pe"]["excluded"]
    reasons = {item["ticker"]: item["reason"] for item in excluded}

    assert reasons["OLDPERIOD"] == "period_mismatch"
    assert reasons["CONFLICT"] == "provider_conflict"


def test_security_identity_conflict_is_excluded() -> None:
    rows = [
        ("TARGET", _valuation()),
        ("UNSAFE", _valuation()),
        ("PEER2", _valuation()),
        ("PEER3", _valuation()),
        ("PEER4", _valuation()),
    ]
    state = _states(
        rows,
        identity_warnings={"UNSAFE": ["issuer mapping mismatch"]},
    )["TARGET"]
    excluded = state["audit"]["metrics"]["trailing_pe"]["excluded"]
    reasons = {item["ticker"]: item["reason"] for item in excluded}

    assert state["metrics"]["trailing_pe"]["sample_count"] == 3
    assert reasons["UNSAFE"] == "security_identity_conflict"


def test_peer_relative_semantics_have_distinct_numeric_paths() -> None:
    registry = build_numeric_registry(
        [
            {
                "fact_id": "valuation:peer",
                "fact_type": "peer_valuation",
                "fields": {
                    "company_pe_relative_multiple": 1.25,
                    "company_pb_relative_multiple": 0.8,
                    "company_pe_cross_section_percentile": 87.5,
                    "company_pb_cross_section_percentile": 25.0,
                },
            }
        ]
    )
    semantics = {item["field_path"]: item["semantic_type"] for item in registry}

    assert semantics["fields.company_pe_relative_multiple"] == (
        "peer_pe_relative_multiple"
    )
    assert semantics["fields.company_pb_relative_multiple"] == (
        "peer_pb_relative_multiple"
    )
    assert semantics["fields.company_pe_cross_section_percentile"] == (
        "peer_pe_cross_section_percentile"
    )
    assert semantics["fields.company_pb_cross_section_percentile"] == (
        "peer_pb_cross_section_percentile"
    )
