from dataclasses import dataclass

from scripts import directional_financial_context_m12 as m12
from scripts.reviewed_financial_semantic_adapter_v1 import validate_m12au_financial_v1
from scripts.reviewed_configured_semantic_adapter_v1 import validate_m12au_configured_v1


TICKER = "FIC-FIN-01"
OCF_REF = "canonical:fictional:FIC-FIN-01:ocf-current"
PROXY_REF = "canonical:fictional:FIC-FIN-01:cash-conversion-current"
CONFIGURED_FCF_REF = "m12at:FIC-FIN-01:weaken"


@dataclass(frozen=True)
class _Candidate:
    payload: dict[str, object]

    def model_dump(self, *, mode: str) -> dict[str, object]:
        assert mode == "json"
        return self.payload


def _semantic(candidate: dict[str, object]):
    return validate_m12au_configured_v1(candidate)


def _with_material_anchor(candidate: dict[str, object]) -> dict[str, object]:
    return {
        "ticker": TICKER,
        "buy_drivers": [
            {
                "text": "동일 기간 대비 영업현금흐름이 개선됐다.",
                "evidence_refs": [OCF_REF],
            }
        ],
        **candidate,
    }


def test_future_configured_fcf_condition_is_not_rejected_by_case_checker() -> None:
    candidate = _with_material_anchor(
        {
            "business_reevaluation_down": [
                {
                    "text": (
                        "잉여현금흐름 감소와 순부채 증가가 함께 확인되면 "
                        "사업 논리를 하향 재평가한다."
                    ),
                    "evidence_refs": [CONFIGURED_FCF_REF],
                }
            ]
        }
    )

    errors = m12._case_semantic_errors(
        TICKER,
        _Candidate(candidate),
        selected_financial_refs={OCF_REF, PROXY_REF},
    )
    semantic = _semantic(candidate)

    assert "strong_quality_proxy_mislabeled_fcf" not in errors
    assert semantic.valid
    assert semantic.unsupported_current_fcf_claim_count == 0
    assert semantic.affirmative_proxy_as_fcf_violation_count == 0


def test_proxy_as_current_fcf_remains_a_hard_generic_failure() -> None:
    candidate = {
        "ticker": TICKER,
        "buy_drivers": [
            {
                "text": "잉여현금흐름이 증가했다.",
                "evidence_refs": [PROXY_REF],
            }
        ],
    }

    semantic = validate_m12au_financial_v1(candidate)

    assert not semantic.valid
    assert semantic.affirmative_proxy_as_fcf_violation_count == 1
    assert "ppe_only_cash_conversion_proxy_called_fcf" in semantic.errors


def test_not_fcf_disclaimer_remains_valid_for_proxy_evidence() -> None:
    candidate = {
        "ticker": TICKER,
        "earnings_estimate_context": {
            "text": (
                "이 지표는 현금 전환 대용치이며 관리 기준 "
                "잉여현금흐름이 아니다."
            ),
            "evidence_refs": [PROXY_REF],
        },
    }

    semantic = validate_m12au_financial_v1(candidate)

    assert semantic.valid
    assert semantic.explicit_not_fcf_disclaimer_count == 1
    assert semantic.affirmative_proxy_as_fcf_violation_count == 0


def test_unsupported_current_fcf_claim_remains_a_hard_generic_failure() -> None:
    candidate = {
        "ticker": TICKER,
        "buy_drivers": [
            {
                "text": "현재 FCF가 증가했다.",
                "evidence_refs": [OCF_REF],
            }
        ],
    }

    semantic = validate_m12au_financial_v1(candidate)

    assert not semantic.valid
    assert semantic.unsupported_current_fcf_claim_count == 1
    assert "unsupported_current_fcf_claim" in semantic.errors
