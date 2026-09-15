from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.services.cross_market_decision_engine_service import EvidenceClaim
from app.services.three_axis_decision_service import (
    HolderDecisionAxis,
    NewBuyerDecisionAxis,
    ThreeAxisDecision,
    render_three_axis_header,
)


def _claim(ref_id: str, text: str) -> EvidenceClaim:
    return EvidenceClaim(text=text, evidence_refs=(ref_id,))


@pytest.mark.parametrize(
    ("direction", "new_buyer", "holder"),
    (
        ("BUY", "WAIT", "HOLDABLE"),
        ("SELL", "AVOID", "HOLDABLE"),
        ("HOLD", "ATTRACTIVE", "REVIEW"),
        ("BUY", "AVOID", "REDUCE"),
    ),
)
def test_renderer_preserves_independent_structured_axes(
    direction: str,
    new_buyer: str,
    holder: str,
) -> None:
    decision = ThreeAxisDecision(
        overall_direction=direction,
        new_buyer=NewBuyerDecisionAxis(
            stance=new_buyer,
            reason=_claim("timing", "진입 조건을 별도로 판단했습니다."),
        ),
        holder=HolderDecisionAxis(
            stance=holder,
            reason=_claim("fundamental", "보유 근거를 별도로 판단했습니다."),
        ),
    )

    rendered = render_three_axis_header(decision)

    assert rendered[0] == f"종합 방향: {direction}"
    assert f"({new_buyer})" in rendered[1]
    assert f"({holder})" in rendered[2]


def test_review_copy_means_reexamine_not_automatic_sell() -> None:
    decision = ThreeAxisDecision(
        overall_direction="HOLD",
        new_buyer=NewBuyerDecisionAxis(
            stance="WAIT",
            reason=_claim("timing", "추가 확인을 기다립니다."),
        ),
        holder=HolderDecisionAxis(
            stance="REVIEW",
            reason=_claim("risk", "중요한 사업 위험을 다시 점검합니다."),
        ),
    )

    holder_line = render_three_axis_header(decision)[2]

    assert holder_line == "보유자: 보유 근거 재검토 (REVIEW)"
    assert "매도" not in holder_line


def test_three_axes_cannot_reuse_one_reason_as_a_template() -> None:
    same = _claim("shared", "같은 문장을 두 축에 재사용했습니다.")

    with pytest.raises(ValidationError, match="three_axis_reason_reuse"):
        ThreeAxisDecision(
            overall_direction="HOLD",
            new_buyer=NewBuyerDecisionAxis(stance="WAIT", reason=same),
            holder=HolderDecisionAxis(stance="HOLDABLE", reason=same),
        )
