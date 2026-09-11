from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.directional_boundary_resolution_service import (
    AdjacentDirectionalBoundary,
    BoundaryAwareDirectionalCoreCandidate,
    BoundaryAwareDirectionalCoreBatch,
    resolve_adjacent_boundary,
)
from app.services.direction_timing_ownership_service import (
    CORE_OUTPUT_CONTRACT,
    DirectionalCoreBatch,
    DirectionalCoreCandidate,
)


M12AA_REPORTS = Path("docs/reports") / (
    "20260910-boundary-band-canary-policy-financial-framework-"
    "application-scope-full-sol-canary"
)


def _historical_core(ticker: str = "FIC-FIN-05") -> dict[str, object]:
    document = json.loads(
        next(M12AA_REPORTS.glob("50-*.json")).read_text(encoding="utf-8")
    )
    return next(row["core"] for row in document["rows"] if row["ticker"] == ticker)


def _candidate(
    *,
    buy: float,
    sell: float,
    direction: str,
    lean: str,
    other_buy: float,
    other_sell: float,
) -> BoundaryAwareDirectionalCoreCandidate:
    payload = _historical_core()
    payload.update(
        {
            "overall_direction": direction,
            "directional_balance": {"buy": buy, "sell": sell},
            "hold_lean": lean,
            "adjacent_boundary": {
                "status": "ADJACENT_BUCKETS_REASONABLE",
                "less_directional_balance": {"buy": other_buy, "sell": other_sell},
                "more_directional_balance": {"buy": buy, "sell": sell},
                "reason": "Both adjacent strengths remain supportable after the cited limit.",
                "evidence_refs": ["E1"],
            },
        }
    )
    return BoundaryAwareDirectionalCoreCandidate.model_validate(payload)


@pytest.mark.parametrize(
    ("raw", "other", "expected"),
    (
        ((4.0, 6.0, "SELL", "NOT_HOLD"), (4.5, 5.5), (4.5, 5.5, "HOLD", "SELL_LEAN")),
        ((6.5, 3.5, "BUY", "NOT_HOLD"), (6.0, 4.0), (6.0, 4.0, "BUY", "NOT_HOLD")),
        ((5.5, 4.5, "HOLD", "BUY_LEAN"), (5.0, 5.0), (5.0, 5.0, "HOLD", "NEUTRAL")),
    ),
)
def test_resolver_selects_less_directional_adjacent_balance(raw, other, expected) -> None:
    candidate = _candidate(
        buy=raw[0],
        sell=raw[1],
        direction=raw[2],
        lean=raw[3],
        other_buy=other[0],
        other_sell=other[1],
    )

    resolved, audit = resolve_adjacent_boundary(candidate, allowed_ref_ids=("E1",))

    assert (
        resolved.directional_balance.buy,
        resolved.directional_balance.sell,
        resolved.overall_direction,
        resolved.hold_lean,
    ) == expected
    assert audit.raw_state.directional_balance == candidate.directional_balance
    assert audit.resolved_state.directional_balance == resolved.directional_balance
    assert audit.status == "RESOLVED_TOWARD_5_0"


def test_legacy_candidate_and_batch_contract_are_unchanged() -> None:
    payload = _historical_core()
    legacy = DirectionalCoreCandidate.model_validate(payload)
    legacy_batch = DirectionalCoreBatch(
        contract=CORE_OUTPUT_CONTRACT,
        packet_id="legacy",
        candidates=(legacy,),
    )
    experimental = BoundaryAwareDirectionalCoreCandidate.model_validate(payload)

    assert legacy.model_dump(mode="json") == payload
    assert legacy_batch.contract == "directional-core-output-v1"
    assert experimental.adjacent_boundary == AdjacentDirectionalBoundary()
    assert BoundaryAwareDirectionalCoreBatch(
        packet_id="experimental", candidates=(experimental,)
    ).contract == "directional-core-boundary-output-v1"


def test_inactive_boundary_rejects_stray_metadata() -> None:
    with pytest.raises(ValidationError, match="inactive_boundary_metadata_forbidden"):
        AdjacentDirectionalBoundary(reason="stray")


def test_active_boundary_requires_complete_declaration() -> None:
    with pytest.raises(
        ValidationError, match="active_boundary_less_directional_balance_required"
    ):
        AdjacentDirectionalBoundary(
            status="ADJACENT_BUCKETS_REASONABLE",
            reason="reason",
            evidence_refs=("E1",),
        )


@pytest.mark.parametrize(
    ("other", "error"),
    (
        ((5.0, 5.0), "boundary_non_adjacent_balance"),
        ((3.5, 6.5), "boundary_endpoint_order_not_toward_5_0"),
    ),
)
def test_resolver_rejects_malformed_adjacency(other, error) -> None:
    candidate = _candidate(
        buy=4.0,
        sell=6.0,
        direction="SELL",
        lean="NOT_HOLD",
        other_buy=other[0],
        other_sell=other[1],
    )

    with pytest.raises(ValueError, match=error):
        resolve_adjacent_boundary(candidate, allowed_ref_ids=("E1",))


def test_resolver_rejects_invalid_evidence_reference() -> None:
    candidate = _candidate(
        buy=4.0,
        sell=6.0,
        direction="SELL",
        lean="NOT_HOLD",
        other_buy=4.5,
        other_sell=5.5,
    )

    with pytest.raises(ValueError, match="boundary_invalid_evidence_refs"):
        resolve_adjacent_boundary(candidate, allowed_ref_ids=("E2",))


def test_no_boundary_keeps_raw_core_unchanged() -> None:
    candidate = BoundaryAwareDirectionalCoreCandidate.model_validate(_historical_core())

    resolved, audit = resolve_adjacent_boundary(candidate, allowed_ref_ids=())

    assert resolved.model_dump(mode="json") == _historical_core()
    assert audit.status == "UNCHANGED"
    assert audit.raw_state == audit.resolved_state


def test_raw_preference_may_be_less_directional_endpoint() -> None:
    payload = _historical_core()
    payload.update(
        {
            "overall_direction": "HOLD",
            "directional_balance": {"buy": 4.5, "sell": 5.5},
            "hold_lean": "SELL_LEAN",
            "adjacent_boundary": {
                "status": "ADJACENT_BUCKETS_REASONABLE",
                "less_directional_balance": {"buy": 4.5, "sell": 5.5},
                "more_directional_balance": {"buy": 4.0, "sell": 6.0},
                "reason": "Both adjacent negative strengths remain supportable.",
                "evidence_refs": ["E1"],
            },
        }
    )
    candidate = BoundaryAwareDirectionalCoreCandidate.model_validate(payload)

    resolved, audit = resolve_adjacent_boundary(candidate, allowed_ref_ids=("E1",))

    assert audit.raw_state.directional_balance.buy == 4.5
    assert resolved.directional_balance.buy == 4.5
    assert resolved.overall_direction == "HOLD"
