from __future__ import annotations

from copy import deepcopy

from scripts.m12cs_r1_provider_schema import (
    project_provider_wire_schema,
    scan_provider_structured_output_schema,
)
from scripts.m12cv_pass_b_capability_contract import (
    build_pass_b_capability_catalog,
    capability_pass_b_batch_schema,
    pass_b_capability_validator_parity_matrix,
    validate_capability_selection,
)
from scripts.m12cr_shadow_contract import validate_future_pass_b_shape


def _claim(claim_ref: str, polarity: str) -> dict[str, object]:
    return {
        "claim_ref": claim_ref,
        "ticker": "RENAMED",
        "claim": {
            "text": "검증된 일반화 사업 근거입니다.",
            "polarity": polarity,
            "reason_role": "FUNDAMENTAL",
            "logical_condition": None,
        },
        "parent_source_refs": ["core:thesis"],
    }


def _catalog(*, with_risk: bool = True, tactical: bool = True) -> dict[str, object]:
    claims = [_claim("claim:bull", "BULLISH")]
    if with_risk:
        claims.append(_claim("claim:bear", "BEARISH"))
    candidates = []
    if tactical:
        candidates.append(
            {
                "ticker": "RENAMED",
                "candidate_id": "tactical:one",
                "low": 70.0,
                "high": 80.0,
                "currency": "USD",
                "evidence_refs": ["timing:support"],
            }
        )
    return {
        "ticker": "RENAMED",
        "all_evidence_refs": [
            "core:thesis",
            "canonical:valuation",
            "canonical:price",
            "canonical:security_basis:current",
            "timing:support",
        ],
        "core_evidence_refs": ["core:thesis", "canonical:valuation"],
        "timing_evidence_refs": ["canonical:price", "timing:support"],
        "valuation_evidence_refs": ["canonical:valuation"],
        "claim_refs": [str(row["claim_ref"]) for row in claims],
        "atomic_claims": claims,
        "entry_catalog": {
            "ticker": "RENAMED",
            "current_price": {
                "value": 90.0,
                "as_of": "2026-09-17",
                "currency": "USD",
                "ref_id": "canonical:price",
            },
            "tactical_candidates": candidates,
            "unresolved_policy": {"tactical_unresolved_reason": "unavailable"},
        },
    }


def _pass_a(archetype: str = "DURABLE_FRANCHISE") -> dict[str, object]:
    return {"ticker": "RENAMED", "archetype": archetype}


def _option(*, resolved: bool = True, high: float = 100.0) -> dict[str, object]:
    return {
        "ticker": "RENAMED",
        "status": "RESOLVED" if resolved else "UNRESOLVED",
        "low": 80.0 if resolved else None,
        "high": high if resolved else None,
        "currency": "USD" if resolved else None,
        "evidence_refs": ["canonical:valuation"] if resolved else [],
        "unresolved_reasons": [] if resolved else ["METHOD_UNAVAILABLE"],
    }


def _context(*, security_resolved: bool = True, tactical: bool = True) -> dict[str, object]:
    catalog = _catalog(tactical=tactical)
    return {
        "ticker": "RENAMED",
        "current_price": deepcopy(catalog["entry_catalog"]["current_price"]),
        "tactical_candidates": deepcopy(catalog["entry_catalog"]["tactical_candidates"]),
        "security_valuation_basis_state": {
            "state": "RESOLVED" if security_resolved else "UNRESOLVED",
            "new_buyer_price_resolution_use_allowed": security_resolved,
            "source_refs": ["canonical:security_basis:current"],
        },
    }


def _capability(
    *,
    resolved: bool = True,
    high: float = 100.0,
    security_resolved: bool = True,
    with_risk: bool = True,
    tactical: bool = True,
    archetype: str = "DURABLE_FRANCHISE",
) -> tuple[dict[str, object], dict[str, object]]:
    catalog = _catalog(with_risk=with_risk, tactical=tactical)
    capability = build_pass_b_capability_catalog(
        context=_context(security_resolved=security_resolved, tactical=tactical),
        catalog=catalog,
        pass_a=_pass_a(archetype),
        policy_option=_option(resolved=resolved, high=high),
    )
    return capability, catalog


def _branch_pairs(capability: dict[str, object]) -> set[tuple[str, str]]:
    return {
        (str(row["stance"]), str(row["reason_class"]))
        for row in capability["new_buyer"]["branches"]
    }


def _output(*, reason_class: str) -> dict[str, object]:
    return {
        "decisions": {
            "RENAMED": {
                "overall_direction": "BUY",
                "directional_buy_score": 6.0,
                "decision_confidence": "MEDIUM",
                "decisive_supporting_claim_refs": ["claim:bull"],
                "decisive_contradicting_claim_refs": [],
                "thesis_state": "INTACT",
                "holder_decision": {
                    "holder": "HOLDABLE",
                    "reason_class": "NOT_APPLICABLE",
                    "reason": "핵심 논리를 훼손하는 근거가 없습니다.",
                    "evidence_refs": [],
                },
                "new_buyer_decision": {
                    "new_buyer": "WAIT",
                    "reason_class": reason_class,
                    "reason": "결정 가능한 조건을 기다립니다.",
                    "evidence_refs": ["canonical:valuation"],
                    "tactical_choice": "UNRESOLVED",
                    "re_evaluate_conditions": ["조건을 재확인합니다."],
                },
                "policy_summary": "세 축을 분리해 판단했습니다.",
            }
        }
    }


def test_unresolved_fundamental_excludes_range_and_keeps_unresolved() -> None:
    capability, _ = _capability(resolved=False)
    pairs = _branch_pairs(capability)
    assert ("WAIT", "FUNDAMENTAL_RANGE_POSITION") not in pairs
    assert ("WAIT", "FUNDAMENTAL_UNRESOLVED") in pairs


def test_resolved_above_range_exposes_range_position() -> None:
    capability, _ = _capability(high=80.0)
    assert ("WAIT", "FUNDAMENTAL_RANGE_POSITION") in _branch_pairs(capability)


def test_unresolved_security_basis_excludes_unsafe_attractive() -> None:
    capability, _ = _capability(security_resolved=False)
    assert ("ATTRACTIVE", "ATTRACTIVE_WITHIN_RANGE") not in _branch_pairs(capability)


def test_tactical_reason_requires_eligible_surface() -> None:
    capability, _ = _capability(tactical=False)
    assert ("WAIT", "TACTICAL_TIMING") not in _branch_pairs(capability)


def test_risk_branches_require_material_bearish_evidence() -> None:
    without_risk, _ = _capability(with_risk=False)
    assert ("WAIT", "EXECUTION_OR_THESIS_RISK") not in _branch_pairs(without_risk)
    assert ("AVOID", "EXECUTION_OR_THESIS_RISK") not in _branch_pairs(without_risk)
    assert [row["stance"] for row in without_risk["holder"]["branches"]] == ["HOLDABLE"]

    with_risk, _ = _capability(with_risk=True)
    assert ("WAIT", "EXECUTION_OR_THESIS_RISK") in _branch_pairs(with_risk)
    assert ("AVOID", "EXECUTION_OR_THESIS_RISK") in _branch_pairs(with_risk)
    assert {row["stance"] for row in with_risk["holder"]["branches"]} == {
        "HOLDABLE",
        "REVIEW",
        "REDUCE",
    }


def test_protected_archetype_without_material_business_evidence_excludes_nonbuy() -> None:
    catalog = _catalog(with_risk=False)
    catalog["atomic_claims"] = []
    catalog["claim_refs"] = ["claim:bull"]
    capability = build_pass_b_capability_catalog(
        context=_context(),
        catalog=catalog,
        pass_a=_pass_a("DURABLE_FRANCHISE"),
        policy_option=_option(),
    )
    assert capability["overall"]["allowed_values"] == ["BUY"]


def test_execution_dependent_growth_preserves_broader_directional_surface() -> None:
    capability, _ = _capability(
        with_risk=False,
        archetype="EXECUTION_DEPENDENT_GROWTH",
    )
    assert capability["overall"]["allowed_values"] == ["BUY", "HOLD", "SELL"]


def test_archived_invalid_wait_shape_is_caught_by_capability_before_materialization() -> None:
    capability, catalog = _capability(resolved=False)
    output = _output(reason_class="FUNDAMENTAL_RANGE_POSITION")
    old_shape = validate_future_pass_b_shape(
        output,
        subjects=("RENAMED",),
        catalogs={"RENAMED": catalog},
    )
    new_validation = validate_capability_selection(
        output,
        subjects=("RENAMED",),
        catalogs={"RENAMED": catalog},
        capabilities={"RENAMED": capability},
    )
    assert old_shape["status"] == "PASS"
    assert new_validation["status"] == "FAIL"
    assert "RENAMED:PB_CAP_NEW_BUYER_BRANCH_FORBIDDEN" in new_validation["errors"]


def test_provider_wire_schema_preserves_single_scalar_and_supported_dialect() -> None:
    capability, catalog = _capability()
    schema = capability_pass_b_batch_schema(
        subjects=("RENAMED",),
        catalogs={"RENAMED": catalog},
        capabilities={"RENAMED": capability},
    )
    row = schema["properties"]["decisions"]["properties"]["RENAMED"]
    assert "directional_buy_score" in row["properties"]
    assert "directional_balance" not in row["properties"]
    wire, _ = project_provider_wire_schema(schema)
    scan = scan_provider_structured_output_schema(wire)
    assert scan["status"] == "PASS"
    assert scan["keyword_counts"].get("uniqueItems", 0) == 0


def test_renamed_identity_produces_same_nonidentity_capability() -> None:
    capability, catalog = _capability()
    renamed_context = _context()
    renamed_context["ticker"] = "OTHER"
    renamed_catalog = deepcopy(catalog)
    renamed_catalog["ticker"] = "OTHER"
    for row in renamed_catalog["atomic_claims"]:
        row["ticker"] = "OTHER"
    renamed_pass_a = _pass_a()
    renamed_pass_a["ticker"] = "OTHER"
    renamed_option = _option()
    renamed_option["ticker"] = "OTHER"
    renamed = build_pass_b_capability_catalog(
        context=renamed_context,
        catalog=renamed_catalog,
        pass_a=renamed_pass_a,
        policy_option=renamed_option,
    )
    assert {key: value for key, value in capability.items() if key != "ticker"} == {
        key: value for key, value in renamed.items() if key != "ticker"
    }


def test_parity_matrix_keeps_only_model_dependent_cross_references_downstream() -> None:
    matrix = pass_b_capability_validator_parity_matrix()
    assert matrix["status"] == "PASS"
    assert matrix["deterministic_branch_rules_left_as_model_cross_reference"] == 0
    assert matrix["unresolved_requires_chat_count"] == 0
