import json
from datetime import date

from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from app.models.company import Company
from app.models.thesis import InvestmentThesis, ThesisAssessment
from app.models.watchlist import WatchlistItem
from app.services import monitoring_state_service
from app.services.monitoring_state_service import (
    build_peer_valuation_states,
    persist_monitoring_states,
    stable_zone_id,
)
from app.services.monitoring_service import assessment_to_read
from app.services.numeric_semantic_registry import build_numeric_registry


def _engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


def _valuation(
    assessment_date: date,
    *,
    pe: float = 10.0,
    pb: float = 1.5,
    pe_percentile: float = 50.0,
) -> str:
    return json.dumps(
        {
            "price_as_of": assessment_date.isoformat(),
            "ttm_eps": 10.0,
            "bvps": 50.0,
            "trailing_pe": pe,
            "trailing_pe_status": "value",
            "trailing_pe_basis_status": "directly_comparable",
            "trailing_pe_denominator_filing_date": "2026-06-30",
            "price_to_book": pb,
            "price_to_book_status": "value",
            "price_to_book_basis_status": "directly_comparable",
            "pbr_denominator_filing_date": "2026-06-30",
            "historical_comparability": "normal",
            "historical_pe_statistics": {
                "metric": "trailing_pe",
                "current_percentile": pe_percentile,
            },
            "historical_pb_statistics": {
                "metric": "price_to_book",
                "current_percentile": pe_percentile - 1,
            },
            "currency": "KRW",
        }
    )


def _price_context(assessment_date: date, price: float) -> str:
    support_center = price - 7_000
    resistance_center = price + 14_000
    return json.dumps(
        {
            "available": True,
            "decision": {
                "current_price": price,
                "currency": "KRW",
                "price_as_of": assessment_date.isoformat(),
                "price_state": (
                    "above_confirmation" if price >= 200_000 else "below_confirmation"
                ),
            },
            "supply": {
                "available": True,
                "as_of_date": assessment_date.isoformat(),
                "foreign_net_buy_qty": 10_613,
                "institution_net_buy_qty": 18_618,
                "foreign_net_buy_qty_5": 124_950,
                "institution_net_buy_qty_5": -115_229,
                "foreign_net_buy_qty_20": 174_664,
                "institution_net_buy_qty_20": 218_752,
                "quality": "verified",
            },
            "chart": {
                "quality": "fresh",
                "price_basis": "adjusted_close",
                "unavailable_fields": [],
                "structure": {
                    "algorithm_version": "ohlcv-structure-v2",
                    "zones": {
                        "active": [],
                        "support": [
                            {
                                "zone_low": support_center - 2_000,
                                "zone_high": support_center + 2_000,
                                "center": support_center,
                                "strength": "Medium",
                                "timeframe": "weekly",
                                "pivot_type": "low",
                                "pivot_dates": ["2026-07-01"],
                            }
                        ],
                        "resistance": [
                            {
                                "zone_low": resistance_center - 2_000,
                                "zone_high": resistance_center + 2_000,
                                "center": resistance_center,
                                "strength": "Strong",
                                "timeframe": "weekly",
                                "pivot_type": "high",
                                "pivot_dates": ["2026-07-24"],
                            }
                        ],
                    },
                    "risk_reward": {
                        "available": True,
                        "current_price": {
                            "entry": price,
                            "target": resistance_center - 2_000,
                            "invalidation": support_center - 8_000,
                            "ratio": round((resistance_center - 2_000 - price) / 15_000, 4),
                        },
                    },
                    "invalidation": {
                        "available": True,
                        "price": support_center - 8_000,
                        "chart_only": True,
                    },
                    "chart_state": {"state": "WAIT", "confidence": "medium"},
                },
            },
        }
    )


def _assessment(
    ticker: str,
    assessment_date: date,
    price: float,
    *,
    pe: float = 10.0,
    pb: float = 1.5,
    pe_percentile: float = 50.0,
) -> ThesisAssessment:
    return ThesisAssessment(
        ticker=ticker,
        thesis_version=1,
        assessment_date=assessment_date,
        status="no_material_change",
        business_thesis_change="no_material_change",
        summary="unchanged",
        new_buyer_view="review",
        holder_view="review",
        price_view="review",
        risk_level="normal",
        assessment_state="final",
        price_context=_price_context(assessment_date, price),
        valuation_snapshot=_valuation(
            assessment_date,
            pe=pe,
            pb=pb,
            pe_percentile=pe_percentile,
        ),
    )


def test_stable_zone_identity_uses_pivot_provenance_not_daily_boundaries() -> None:
    first = {
        "timeframe": "weekly",
        "pivot_type": "low",
        "pivot_dates": ["2026-07-01", "2026-07-15"],
        "zone_low": 197_000,
        "zone_high": 205_000,
    }
    shifted = {**first, "zone_low": 198_000, "zone_high": 206_000}

    assert stable_zone_id(first, "support") == stable_zone_id(shifted, "support")
    assert stable_zone_id(first, "support") != stable_zone_id(first, "resistance")


def test_price_rule_lifecycle_and_daily_state_persist_without_rewriting_rule() -> None:
    engine = _engine()
    dates = (date(2026, 8, 12), date(2026, 8, 13), date(2026, 8, 14))
    prices = (199_700.0, 204_500.0, 211_000.0)
    percentiles = (88.0, 90.0, 92.8)
    with Session(engine) as session:
        session.add(Company(ticker="086280", company_name="현대글로비스", exchange="KRX"))
        session.add(
            InvestmentThesis(
                ticker="086280",
                version=1,
                core_thesis="transport",
                price_rules=json.dumps(
                    {
                        "confirmation_price": 200_000,
                        "support_zone_low": 176_000,
                        "support_zone_high": 180_000,
                        "invalidation_price": 176_000,
                    }
                ),
            )
        )
        session.commit()

        states = []
        for current_date, price, percentile in zip(dates, prices, percentiles, strict=True):
            assessment = _assessment(
                "086280",
                current_date,
                price,
                pe_percentile=percentile,
            )
            session.add(assessment)
            session.commit()
            session.refresh(assessment)
            persist_monitoring_states(session, [assessment], current_date)
            states.append(json.loads(assessment.price_context)["monitoring_state"])
        history_read = assessment_to_read(assessment)

    lifecycles = [
        state["current"]["price_structure"]["registered_rule_state"]["confirmation"][
            "state"
        ]
        for state in states
    ]
    assert lifecycles == ["not_reached", "crossed", "holding_above"]
    assert states[-1]["current"]["price_structure"]["active_support"]["zone_low"] == 202_000
    assert states[-1]["current"]["valuation"]["historical_pe_percentile"] == 92.8
    assert states[-1]["previous"]["valuation"]["historical_pe_percentile"] == 90.0
    assert states[-1]["delta"]["valuation_change"] == "more_expensive"
    registered = states[-1]["current"]["price_structure"]["registered_rule_state"]
    assert registered["support"]["zone_low"] == 176_000
    assert registered["support"]["relevance"] == "superseded_for_current_structure"
    assert registered["confirmation"]["automatically_promoted_to_support"] is False
    assert states[-1]["current"]["supply"]["transition"] == "short_term_divergence"
    assert history_read.price_context.monitoring_state["delta"]["valuation_change"] == (
        "more_expensive"
    )


def test_failed_breakout_is_price_state_not_thesis_invalidation() -> None:
    engine = _engine()
    with Session(engine) as session:
        session.add(Company(ticker="086280", company_name="현대글로비스", exchange="KRX"))
        session.add(
            InvestmentThesis(
                ticker="086280",
                version=1,
                core_thesis="transport",
                price_rules=json.dumps({"confirmation_price": 200_000}),
            )
        )
        session.commit()
        states = []
        for current_date, price in (
            (date(2026, 8, 12), 199_700.0),
            (date(2026, 8, 13), 204_500.0),
            (date(2026, 8, 14), 198_000.0),
        ):
            assessment = _assessment("086280", current_date, price)
            session.add(assessment)
            session.commit()
            persist_monitoring_states(session, [assessment], current_date)
            states.append(json.loads(assessment.price_context)["monitoring_state"])

    confirmation = states[-1]["current"]["price_structure"][
        "registered_rule_state"
    ]["confirmation"]
    assert confirmation["state"] == "failed_breakout"
    assert confirmation["automatically_promoted_to_support"] is False
    assert states[-1]["delta"]["confirmation_transition"] == (
        "crossed_to_failed_breakout"
    )


def test_missing_dynamic_support_does_not_reuse_registered_support_for_rr() -> None:
    engine = _engine()
    assessment_date = date(2026, 8, 14)
    with Session(engine) as session:
        session.add(Company(ticker="086280", company_name="현대글로비스", exchange="KRX"))
        thesis = InvestmentThesis(
            ticker="086280",
            version=1,
            core_thesis="transport",
            price_rules=json.dumps(
                {
                    "confirmation_price": 200_000,
                    "support_zone_low": 176_000,
                    "support_zone_high": 180_000,
                }
            ),
        )
        session.add(thesis)
        assessment = _assessment("086280", assessment_date, 211_000.0)
        context = json.loads(assessment.price_context)
        structure = context["chart"]["structure"]
        structure["zones"] = {"active": [], "support": [], "resistance": []}
        structure["risk_reward"] = {
            "available": False,
            "reason": "meaningful_support_unavailable",
        }
        structure["invalidation"] = {
            "available": False,
            "reason": "meaningful_support_unavailable",
        }
        assessment.price_context = json.dumps(context)
        session.add(assessment)
        session.commit()
        persist_monitoring_states(session, [assessment], assessment_date)
        state = json.loads(assessment.price_context)["monitoring_state"]["current"]

    price = state["price_structure"]
    assert price["active_support"]["available"] is False
    assert price["risk_reward"]["available"] is False
    assert price["registered_rule_state"]["support"] == {
        "zone_low": 176_000.0,
        "zone_high": 180_000.0,
        "relevance": "background",
    }


def test_supply_state_preserves_one_five_twenty_day_transitions() -> None:
    def state(
        one_day: tuple[int, int],
        five_day: tuple[int, int],
        twenty_day: tuple[int, int],
    ) -> dict[str, object]:
        return monitoring_state_service._supply_state(  # noqa: SLF001
            {
                "available": True,
                "foreign_net_buy_qty": one_day[0],
                "institution_net_buy_qty": one_day[1],
                "foreign_net_buy_qty_5": five_day[0],
                "institution_net_buy_qty_5": five_day[1],
                "foreign_net_buy_qty_20": twenty_day[0],
                "institution_net_buy_qty_20": twenty_day[1],
            }
        )

    all_positive = state((1, 1), (2, 2), (3, 3))
    short_negative = state((-1, -1), (-2, -2), (3, 3))
    medium_negative = state((1, 1), (-2, -2), (-3, -3))

    assert all_positive["transition"] == "aligned"
    assert all_positive["medium_term"] == "joint_buying"
    assert short_negative["one_day"]["state"] == "joint_selling"
    assert short_negative["transition"] == "short_term_divergence"
    assert medium_negative["one_day"]["state"] == "joint_buying"
    assert medium_negative["short_term"] == "joint_selling"
    assert medium_negative["medium_term"] == "joint_selling"


def test_targeted_replay_keeps_full_active_peer_universe(monkeypatch) -> None:
    monkeypatch.setattr(
        monitoring_state_service,
        "read_profile_provenance",
        lambda ticker, _data_dir: {
            "quality": "verified",
            "taxonomy_key": "shipping",
        },
    )
    engine = _engine()
    assessment_date = date(2026, 8, 14)
    with Session(engine) as session:
        assessments = []
        for ticker, pe in (
            ("TARGET", 10.0),
            ("PEER1", 6.0),
            ("PEER2", 8.0),
            ("PEER3", 10.0),
        ):
            session.add(
                Company(
                    ticker=ticker,
                    company_name=ticker,
                    exchange="NYSE",
                    industry="Transportation and Logistics",
                )
            )
            session.add(WatchlistItem(ticker=ticker, company_name=ticker, active=True))
            session.add(
                InvestmentThesis(ticker=ticker, version=1, core_thesis="transport")
            )
            assessment = _assessment(ticker, assessment_date, 100.0, pe=pe)
            assessments.append(assessment)
            session.add(assessment)
        session.commit()

        persist_monitoring_states(session, assessments, assessment_date)
        persist_monitoring_states(session, [assessments[0]], assessment_date)
        peer = json.loads(assessments[0].price_context)["monitoring_state"]["current"][
            "peer_valuation"
        ]

    assert peer["available"] is True
    assert peer["metrics"]["trailing_pe"]["sample_count"] == 3


def test_new_thesis_version_resets_registered_rule_lifecycle_memory() -> None:
    engine = _engine()
    with Session(engine) as session:
        session.add(Company(ticker="086280", company_name="현대글로비스", exchange="KRX"))
        session.add(
            InvestmentThesis(
                ticker="086280",
                version=1,
                core_thesis="transport v1",
                price_rules=json.dumps({"confirmation_price": 200_000}),
            )
        )
        thesis_v2 = InvestmentThesis(
            ticker="086280",
            version=2,
            core_thesis="transport v2",
            price_rules=json.dumps({"confirmation_price": 200_000}),
        )
        session.add(thesis_v2)
        previous = _assessment("086280", date(2026, 8, 13), 204_500.0)
        previous.price_context = json.dumps(
            {
                **json.loads(previous.price_context),
                "monitoring_state": {
                    "current": {
                        "price_structure": {
                            "current_price": 204_500.0,
                            "active_support": {"available": False},
                            "registered_rule_state": {
                                "confirmation": {"state": "retest_in_progress"}
                            },
                        }
                    }
                },
            }
        )
        current = _assessment("086280", date(2026, 8, 14), 211_000.0)
        current.thesis_version = 2
        session.add(previous)
        session.add(current)
        session.commit()

        state = monitoring_state_service.build_monitoring_state(
            session,
            current,
            thesis_v2,
            {"available": False, "reason": "peer_unavailable"},
        )

    confirmation = state["current"]["price_structure"]["registered_rule_state"][
        "confirmation"
    ]
    assert confirmation["state"] == "holding_above"
    assert confirmation["state"] != "retest_held"


def test_peer_valuation_uses_verified_same_market_peers_and_median(monkeypatch) -> None:
    monkeypatch.setattr(
        monitoring_state_service,
        "read_profile_provenance",
        lambda ticker, _data_dir: {
            "quality": "verified",
            "taxonomy_key": "shipping",
        },
    )
    engine = _engine()
    assessment_date = date(2026, 8, 14)
    with Session(engine) as session:
        assessments = []
        for ticker, pe, pb in (
            ("TARGET", 10.0, 1.5),
            ("PEER1", 6.0, 0.8),
            ("PEER2", 8.0, 1.0),
            ("PEER3", 10.0, 1.2),
        ):
            session.add(
                Company(
                    ticker=ticker,
                    company_name=ticker,
                    exchange="NYSE",
                    industry="Transportation and Logistics",
                    sector="Industrials",
                )
            )
            assessment = _assessment(ticker, assessment_date, 100.0, pe=pe, pb=pb)
            assessments.append(assessment)
            session.add(assessment)
        session.commit()

        state = build_peer_valuation_states(
            session, assessments, assessment_date
        )["TARGET"]

    assert state["available"] is True
    assert state["group_basis"] == "taxonomy"
    assert state["metrics"]["trailing_pe"]["median"] == 8.0
    assert state["metrics"]["trailing_pe"]["company_vs_median_pct"] == 25.0
    assert state["metrics"]["price_to_book"]["median"] == 1.0
    assert state["metrics"]["price_to_book"]["sample_count"] == 3


def test_peer_valuation_fails_closed_for_small_or_invalid_sample(monkeypatch) -> None:
    monkeypatch.setattr(
        monitoring_state_service,
        "read_profile_provenance",
        lambda ticker, _data_dir: {
            "quality": "verified",
            "taxonomy_key": "shipping",
        },
    )
    engine = _engine()
    assessment_date = date(2026, 8, 14)
    with Session(engine) as session:
        assessments = []
        for ticker in ("TARGET", "PEER1", "PEER2"):
            session.add(
                Company(
                    ticker=ticker,
                    company_name=ticker,
                    exchange="NYSE",
                    industry="Transportation and Logistics",
                    sector="Industrials",
                )
            )
            assessment = _assessment(ticker, assessment_date, 100.0)
            assessments.append(assessment)
            session.add(assessment)
        session.commit()

        state = build_peer_valuation_states(
            session, assessments, assessment_date
        )["TARGET"]

    assert state == {
        "available": False,
        "reason": "insufficient_verified_peer_universe",
        "provider": "validated_active_monitoring_assessments",
        "minimum_sample": 3,
        "profile_quality": "verified",
    }


def test_peer_metric_excludes_loss_stale_and_unverified_security_basis() -> None:
    assessment_date = date(2026, 8, 14)
    base = json.loads(_valuation(assessment_date))

    loss = {**base, "trailing_pe": -2.0}
    stale = {**base, "price_as_of": "2026-08-13"}
    unsafe_adr = {**base, "trailing_pe_basis_status": "insufficient_metadata"}
    negative_book = {**base, "bvps": -1.0}

    assert monitoring_state_service._metric_value(  # noqa: SLF001
        loss, "trailing_pe", assessment_date
    ) == (None, "non_positive_or_missing_denominator")
    assert monitoring_state_service._metric_value(  # noqa: SLF001
        stale, "trailing_pe", assessment_date
    ) == (None, "stale_or_mismatched_price_date")
    assert monitoring_state_service._metric_value(  # noqa: SLF001
        unsafe_adr, "trailing_pe", assessment_date
    ) == (None, "security_or_share_basis_not_comparable")
    assert monitoring_state_service._metric_value(  # noqa: SLF001
        negative_book, "price_to_book", assessment_date
    ) == (None, "non_positive_or_missing_bvps")


def test_biotech_profile_does_not_force_peer_pe(monkeypatch) -> None:
    monkeypatch.setattr(
        monitoring_state_service,
        "read_profile_provenance",
        lambda ticker, _data_dir: {
            "quality": "verified",
            "taxonomy_key": "biotechnology",
        },
    )
    engine = _engine()
    assessment_date = date(2026, 8, 14)
    with Session(engine) as session:
        assessments = []
        for ticker in ("TARGET", "PEER1", "PEER2", "PEER3"):
            session.add(
                Company(
                    ticker=ticker,
                    company_name=ticker,
                    exchange="NASDAQ",
                    industry="Biotechnology",
                    sector="Healthcare",
                )
            )
            assessment = _assessment(ticker, assessment_date, 100.0)
            assessments.append(assessment)
            session.add(assessment)
        session.commit()

        state = build_peer_valuation_states(
            session, assessments, assessment_date
        )["TARGET"]

    assert state["metrics"]["trailing_pe"] == {
        "available": False,
        "sample_count": 0,
        "reason": "industry_metric_not_primary",
    }
    assert state["metrics"]["price_to_book"]["available"] is True


def test_peer_numeric_semantics_are_explicit_and_fail_closed() -> None:
    registry = build_numeric_registry(
        [
            {
                "fact_id": "valuation:peer",
                "fact_type": "peer_valuation",
                "fields": {
                    "pe_median": 8.4,
                    "pb_median": 1.1,
                    "company_pe_vs_median_pct": 22.3,
                    "company_pb_vs_median_pct": 39.0,
                    "pe_sample_count": 12,
                },
            }
        ]
    )
    by_path = {item["field_path"]: item for item in registry}

    assert by_path["fields.pe_median"]["semantic_type"] == "peer_pe_multiple"
    assert by_path["fields.pb_median"]["semantic_type"] == "peer_pb_multiple"
    assert (
        by_path["fields.company_pe_vs_median_pct"]["semantic_type"]
        == "peer_pe_relative_pct"
    )
    assert by_path["fields.pe_sample_count"]["prose_allowed"] is False
