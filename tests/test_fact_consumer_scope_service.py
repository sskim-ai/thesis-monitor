from __future__ import annotations

from app.services.cross_market_decision_engine_service import (
    build_decision_evidence_packet,
)
from app.services.fact_consumer_scope_service import (
    FactConsumer,
    with_fact_consumer_scopes,
)
from app.services.numeric_semantic_registry import (
    build_numeric_registry,
    consumer_numeric_registry_coverage,
)


def _unsupported_fact(
    fact_id: str,
    *,
    scopes: tuple[FactConsumer, ...] | None = None,
    user_visible: bool | None = None,
) -> dict[str, object]:
    fact = {
        "fact_id": fact_id,
        "fact_type": "consumer_scope_fixture",
        "as_of_date": "2026-09-03",
        "fields": {"unsupported_amount": 123.0},
    }
    if scopes is None:
        return fact
    return with_fact_consumer_scopes(fact, scopes, user_visible=user_visible)


def _coverage(
    fact: dict[str, object],
    consumer: FactConsumer = FactConsumer.STOCK_V2,
) -> dict[str, object]:
    return consumer_numeric_registry_coverage(
        [{"name": "fixture", "registry": build_numeric_registry([fact])}],
        consumer=consumer,
    )


def test_archive_only_unsupported_fact_does_not_block_stock_v2() -> None:
    result = _coverage(
        _unsupported_fact("archive:only", scopes=(FactConsumer.ARCHIVE_ONLY,))
    )

    assert result["ready"] is True
    assert result["included_numeric_count"] == 0
    assert result["excluded_nonconsumer_fact_count"] == 1
    assert result["unsupported_included_numeric_count"] == 0
    assert result["excluded_nonconsumer"][0]["reason"] == "NOT_IN_CONSUMER_SCOPE"


def test_night_module_unsupported_fact_does_not_block_stock_v2() -> None:
    result = _coverage(
        _unsupported_fact(
            "night:module",
            scopes=(FactConsumer.NIGHT_FUTURES_MODULE,),
        )
    )

    assert result["ready"] is True
    assert result["excluded_nonconsumer_fact_count"] == 1


def test_hidden_stock_v2_fact_remains_strictly_validated() -> None:
    result = _coverage(
        _unsupported_fact(
            "hidden:stock",
            scopes=(FactConsumer.STOCK_V2,),
            user_visible=False,
        )
    )

    assert result["ready"] is False
    assert result["included_numeric_count"] == 1
    assert result["unsupported_included_numeric_count"] == 1
    assert result["excluded_nonconsumer_numeric_count"] == 0


def test_market_renderer_scope_is_independent_from_stock_v2() -> None:
    fact = _unsupported_fact(
        "market:renderer",
        scopes=(FactConsumer.MARKET_RENDERER,),
        user_visible=True,
    )

    stock_result = _coverage(fact)
    renderer_result = _coverage(fact, FactConsumer.MARKET_RENDERER)

    assert stock_result["ready"] is True
    assert stock_result["excluded_nonconsumer_fact_count"] == 1
    assert renderer_result["ready"] is False
    assert renderer_result["unsupported_included_numeric_count"] == 1


def test_unclassified_legacy_fact_preserves_strict_behavior() -> None:
    result = _coverage(_unsupported_fact("legacy:unclassified"))

    assert result["ready"] is False
    assert result["included_numeric_count"] == 1
    assert result["unsupported_included_numeric_count"] == 1
    assert result["excluded_nonconsumer_fact_count"] == 0


def test_stock_v2_prompt_projection_matches_consumer_scope() -> None:
    archive_fact = _unsupported_fact(
        "night:archive",
        scopes=(FactConsumer.ARCHIVE_ONLY, FactConsumer.NIGHT_FUTURES_MODULE),
        user_visible=False,
    )
    hidden_stock_fact = _unsupported_fact(
        "hidden:stock",
        scopes=(FactConsumer.STOCK_V2,),
        user_visible=False,
    )
    evidence = build_decision_evidence_packet(
        packet={
            "packet_id": "2026-09-03-us-run-consumer-scope",
            "market": "us",
            "assessment_date": "2026-09-03",
        },
        stock={
            "ticker": "TEST",
            "company_name": "Test Corp",
            "thesis": {"core_thesis": "테스트 논리", "time_horizon": "12-24개월"},
            "unknowns": [],
            "market_transmission": {},
            "current_price_context": {},
            "fact_catalog": [archive_fact, hidden_stock_fact],
            "data_cautions": [],
        },
    )
    refs = {row.ref_id for row in evidence.evidence}

    assert "canonical:night:archive" not in refs
    assert "canonical:hidden:stock" in refs

