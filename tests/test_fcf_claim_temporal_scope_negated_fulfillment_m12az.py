from __future__ import annotations

import pytest

from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
    EvidenceCategory,
)
from app.services.directional_financial_context_service import (
    CURRENT_FULFILLMENT_POLARITY_CONTRACT,
    FCF_TEMPORAL_CLAIM_SPAN_CONTRACT,
    CurrentFulfillmentPolarity,
    current_fulfillment_polarity,
    fcf_temporal_claim_spans,
    financial_claim_row_requires_current_fcf_evidence,
    financial_claim_rows,
    validate_directional_financial_semantics,
)
from app.services.financial_framework_claim_service import (
    CLAIM_SPAN_CONTRACT_VERSION,
    financial_frameworks_in_text,
)
from app.services.logical_condition_service import CheckpointMetric


def _configured_ref(
    *,
    statement: str = "FCF 감소와 순부채 증가가 동반",
    metric_refs: tuple[CheckpointMetric, ...] = (CheckpointMetric.FCF,),
) -> DecisionEvidenceRef:
    return DecisionEvidenceRef(
        ref_id="configured:fcf",
        category=EvidenceCategory.RISKS,
        label="설정된 미래 논리 조건",
        statement=statement,
        source_ref="stock.thesis.weaken_signals",
        metric_refs=metric_refs,
    )


def _candidate(text: str, ref: DecisionEvidenceRef) -> dict[str, object]:
    return {"risk_context": {"text": text, "evidence_refs": [ref.ref_id]}}


def _validate(text: str, ref: DecisionEvidenceRef | None = None):
    supplied = ref or _configured_ref()
    return validate_directional_financial_semantics(
        _candidate(text, supplied),
        supplied_refs=(supplied,),
        allowed_ref_ids=(supplied.ref_id,),
    )


def _requires_current(text: str, ref: DecisionEvidenceRef | None = None) -> bool:
    supplied = ref or _configured_ref()
    row = financial_claim_rows(_candidate(text, supplied))[0]
    return financial_claim_row_requires_current_fcf_evidence(
        row,
        evidence_by_ref={supplied.ref_id: supplied},
    )


def test_m12az_contract_versions_are_frozen() -> None:
    assert FCF_TEMPORAL_CLAIM_SPAN_CONTRACT == "fcf-temporal-claim-span-v1"
    assert CURRENT_FULFILLMENT_POLARITY_CONTRACT == "current-fulfillment-polarity-v1"


@pytest.mark.parametrize(
    "prefix",
    (
        "경쟁에 따른 가격결정력 압박 가능성이 있다.",
        "운전자본 흡수가 이어질 수 있다.",
        "최근 분기 흑자가 지속 가능한 회복을 보장하지 않는다.",
        "비영업 지원이 반복되지 않을 수 있다.",
    ),
)
def test_exact_m12ay_failures_are_prospective_after_local_scope(prefix: str) -> None:
    text = (
        f"{prefix} 잉여현금흐름 감소와 순부채 증가의 동반 확인은 약화 조건이고 "
        "지속적인 음의 영업현금흐름은 무효화 조건이나, "
        "현재 충족된 사실은 아니다."
    )

    result = _validate(text)
    assert result.valid, result
    assert result.unsupported_current_fcf_claim_count == 0
    assert not _requires_current(text)

    row = financial_claim_rows(_candidate(text, _configured_ref()))[0]
    spans = fcf_temporal_claim_spans(row)
    assert len(spans) == 1
    assert spans[0].contract == FCF_TEMPORAL_CLAIM_SPAN_CONTRACT
    assert spans[0].span_contract == CLAIM_SPAN_CONTRACT_VERSION
    assert "잉여현금흐름" in spans[0].local_clause_text
    assert "영업현금흐름" not in spans[0].local_clause_text
    assert "현재 충족된 사실은 아니다" not in spans[0].local_clause_text


@pytest.mark.parametrize(
    "text",
    (
        "FCF 감소는 약화 조건이나 현재 충족된 사실은 아니다.",
        "FCF 감소는 무효화 조건이지만 아직 충족되지 않았다.",
        "FCF 감소는 하향 조건이며 현재 확인된 사실은 아니다.",
        "FCF decline is a downside condition but is not currently fulfilled.",
        "FCF 감소는 하향 조건이지만 아직 충족되지 않았다.",
    ),
)
def test_negated_configured_fcf_conditions_are_prospective(text: str) -> None:
    result = _validate(text)
    assert result.valid, result
    assert not _requires_current(text)


@pytest.mark.parametrize(
    "text",
    (
        "현재 FCF가 감소했다.",
        "FCF가 이미 악화됐다.",
        "현재 FCF는 음수다.",
        "FCF는 100이다.",
        "FCF 감소가 확인됐다.",
        "현재 FCF 감소가 확인됐다.",
        "약화 조건이 현재 충족된 사실은 아니다. 다만 FCF는 이미 감소했다.",
        "현재 조건이 충족된 사실은 아니지만 FCF는 100이다.",
        "현재 충족되지는 않았다고 했지만 FCF 감소는 이미 확인됐다.",
        "FCF 감소는 조건이고 현재 충족됐다.",
        "the condition is not currently fulfilled, but FCF has already declined.",
    ),
)
def test_negation_does_not_immunize_separate_current_fcf_claim(text: str) -> None:
    result = _validate(text)
    assert not result.valid, text
    assert "unsupported_current_fcf_claim" in result.errors
    assert _requires_current(text)


@pytest.mark.parametrize(
    ("text", "expected"),
    (
        (
            "현재 충족된 사실은 아니다.",
            CurrentFulfillmentPolarity.NEGATED_CURRENT_FULFILLMENT,
        ),
        (
            "아직 충족되지 않았다.",
            CurrentFulfillmentPolarity.NEGATED_CURRENT_FULFILLMENT,
        ),
        (
            "is not currently fulfilled",
            CurrentFulfillmentPolarity.NEGATED_CURRENT_FULFILLMENT,
        ),
        (
            "조건은 현재 충족된 사실은 아니지만 FCF는 이미 감소했다.",
            CurrentFulfillmentPolarity.AFFIRMATIVE_CURRENT_FULFILLMENT,
        ),
        (
            "현재 조건을 검토한다.",
            CurrentFulfillmentPolarity.CURRENT_SCOPE_MARKER_ONLY,
        ),
        ("향후 조건이다.", CurrentFulfillmentPolarity.NONE),
    ),
)
def test_current_fulfillment_polarity_is_local(
    text: str,
    expected: CurrentFulfillmentPolarity,
) -> None:
    assert current_fulfillment_polarity(text) == expected


def test_fcf_and_ocf_remain_separate_in_one_field() -> None:
    text = (
        "FCF 감소는 약화 조건이고 음의 OCF는 무효화 조건이나, "
        "현재 둘 다 충족된 사실은 아니다."
    )
    result = _validate(text)
    assert result.valid, result
    assert not _requires_current(text)

    row = financial_claim_rows(_candidate(text, _configured_ref()))[0]
    spans = fcf_temporal_claim_spans(row)
    assert len(spans) == 1
    assert spans[0].local_clause_text == "FCF 감소는 약화 조건"
    assert "OCF" not in spans[0].local_clause_text


def test_general_financial_framework_surface_stays_closed_to_fcf() -> None:
    assert financial_frameworks_in_text("FCF 감소와 순부채 증가가 동반") == {
        "net_debt"
    }
    assert financial_frameworks_in_text("free cash flow declines") == set()
