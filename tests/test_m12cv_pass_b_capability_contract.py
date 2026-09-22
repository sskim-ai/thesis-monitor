from __future__ import annotations

from copy import deepcopy

import pytest
from scripts.websocket_timeout_runtime_review_first_a_closeout import validate_json_schema

from scripts.m12cs_r1_provider_schema import (
    project_provider_wire_schema,
    scan_provider_structured_output_schema,
)
from scripts.m12cv_pass_b_capability_contract import (
    build_pass_b_capability_catalog,
    capability_pass_b_batch_schema,
    capability_prompt_template,
    pass_b_capability_validator_parity_matrix,
    validate_capability_selection,
)
from scripts.m12cr_shadow_contract import validate_future_pass_b_shape
from scripts.m12da_source_use_contract import (
    SourceUse,
    build_source_use_projection,
    frozen_source_authority,
)


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


def _source_use(
    catalog: dict[str, object],
    *,
    restricted_ref: str = "core:thesis",
) -> dict[str, object]:
    authority = frozen_source_authority(
        ticker="RENAMED",
        ref_id=restricted_ref,
        source_type="restricted_context",
        source_scope="context_only",
        allowed_uses=[SourceUse.CONTEXT, SourceUse.EARNINGS_QUALITY_CONTEXT],
        prohibited_uses=[
            SourceUse.PASS_A_ARCHETYPE,
            SourceUse.PASS_A_VALUATION_TIER,
            SourceUse.OVERALL_DIRECTION,
            SourceUse.HOLDER_STANCE,
            SourceUse.NEW_BUYER_EXECUTION_RISK,
        ],
        denial_reasons=["source_scope_does_not_authorize_decision"],
        authority_basis="deterministic_test_authority",
    )
    return build_source_use_projection(
        ticker="RENAMED",
        input_generation_id="frozen-generation",
        catalog=catalog,
        source_authorities=[authority],
    )


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


def test_protected_archetype_without_material_business_evidence_never_forces_buy() -> None:
    catalog = _catalog(with_risk=False)
    catalog["atomic_claims"] = []
    catalog["claim_refs"] = ["claim:bull"]
    capability = build_pass_b_capability_catalog(
        context=_context(),
        catalog=catalog,
        pass_a=_pass_a("DURABLE_FRANCHISE"),
        policy_option=_option(),
    )
    assert capability["overall"]["allowed_values"] == ["BUY", "HOLD", "SELL"]
    assert capability["overall"]["support_state"] == "UNDER_SUPPORTED"
    assert capability["overall"]["excluded_branches"] == []


def test_restricted_source_is_removed_from_capability_without_forcing_a_label() -> None:
    catalog = _catalog(with_risk=True)
    source_use = _source_use(catalog)
    capability = build_pass_b_capability_catalog(
        context=_context(),
        catalog=catalog,
        pass_a=_pass_a("DURABLE_FRANCHISE"),
        policy_option=_option(),
        source_use_view=source_use,
    )
    assert capability["evidence_classes"]["material_business_claim_refs"] == []
    assert capability["evidence_classes"]["material_risk_claim_refs"] == []
    assert capability["holder"]["branches"] == [
        {
            "stance": "HOLDABLE",
            "reason_classes": ["NOT_APPLICABLE"],
            "allowed_evidence_refs": [],
            "prerequisite": "always_admissible_baseline",
        }
    ]
    assert capability["overall"]["allowed_values"] == ["BUY", "HOLD", "SELL"]
    assert capability["overall"]["support_state"] == "UNDER_SUPPORTED"


def test_final_selection_gate_rejects_restricted_ref_even_with_permissive_capability() -> None:
    capability, catalog = _capability(with_risk=True)
    source_use = _source_use(catalog)
    output = _output(reason_class="FUNDAMENTAL_RANGE_POSITION")
    validation = validate_capability_selection(
        output,
        subjects=("RENAMED",),
        catalogs={"RENAMED": catalog},
        capabilities={"RENAMED": capability},
        source_use_views={"RENAMED": source_use},
    )
    assert validation["status"] == "FAIL"
    assert any(
        "PB_SOURCE_USE_OVERALL_SOURCE_USE_REF_FORBIDDEN" in row for row in validation["errors"]
    )


def test_independent_risk_remains_eligible_when_restricted_context_is_present() -> None:
    catalog = _catalog(with_risk=True)
    catalog["all_evidence_refs"].append("core:independent-risk")
    independent = _claim("claim:independent-risk", "BEARISH")
    independent["parent_source_refs"] = ["core:independent-risk"]
    catalog["atomic_claims"].append(independent)
    catalog["claim_refs"].append("claim:independent-risk")
    source_use = _source_use(catalog)
    capability = build_pass_b_capability_catalog(
        context=_context(),
        catalog=catalog,
        pass_a=_pass_a("DURABLE_FRANCHISE"),
        policy_option=_option(),
        source_use_view=source_use,
    )
    assert capability["evidence_classes"]["material_business_claim_refs"] == [
        "claim:independent-risk"
    ]
    assert capability["evidence_classes"]["material_risk_claim_refs"] == ["claim:independent-risk"]


def test_holder_only_permission_does_not_depend_on_new_buyer_permission() -> None:
    catalog = _catalog(with_risk=True)
    authority = frozen_source_authority(
        ticker="RENAMED",
        ref_id="core:thesis",
        source_type="holder_only_risk",
        source_scope="holder_only",
        allowed_uses=[SourceUse.CONTEXT, SourceUse.HOLDER_STANCE],
        prohibited_uses=[
            SourceUse.OVERALL_DIRECTION,
            SourceUse.NEW_BUYER_EXECUTION_RISK,
        ],
        denial_reasons=["new_buyer_use_not_authorized"],
        authority_basis="deterministic_test_authority",
    )
    source_use = build_source_use_projection(
        ticker="RENAMED",
        input_generation_id="frozen-generation",
        catalog=catalog,
        source_authorities=[authority],
    )
    capability = build_pass_b_capability_catalog(
        context=_context(),
        catalog=catalog,
        pass_a=_pass_a("DURABLE_FRANCHISE"),
        policy_option=_option(),
        source_use_view=source_use,
    )
    assert {row["stance"] for row in capability["holder"]["branches"]} == {
        "HOLDABLE",
        "REVIEW",
        "REDUCE",
    }
    assert ("WAIT", "EXECUTION_OR_THESIS_RISK") not in _branch_pairs(capability)


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


@pytest.mark.parametrize(
    "field", ["decisive_supporting_claim_refs", "decisive_contradicting_claim_refs"]
)
@pytest.mark.parametrize("polarity", ["BULLISH", "BEARISH"])
def test_decisive_schema_excludes_context_without_changing_catalog(field, polarity) -> None:
    catalog = _catalog()
    restricted = _claim("claim:new-context", polarity)
    restricted["parent_source_refs"] = ["context:restricted"]
    catalog["atomic_claims"].append(restricted)
    catalog["claim_refs"].append(restricted["claim_ref"])
    catalog["all_evidence_refs"].append("context:restricted")
    before = deepcopy(catalog)
    projection = _source_use(catalog, restricted_ref="context:restricted")
    capability = build_pass_b_capability_catalog(
        context=_context(),
        catalog=catalog,
        pass_a=_pass_a(),
        policy_option=_option(),
        source_use_view=projection,
    )
    schema = capability_pass_b_batch_schema(
        subjects=("RENAMED",), catalogs={"RENAMED": catalog}, capabilities={"RENAMED": capability}
    )
    item = schema["properties"]["decisions"]["properties"]["RENAMED"]["properties"][field]
    assert not validate_json_schema(["claim:bull"], item)
    assert not validate_json_schema(["claim:bear"], item)
    assert validate_json_schema(["claim:new-context"], item)
    assert validate_json_schema(["claim:bull", "claim:new-context"], item)
    assert catalog == before
    assert set(item["items"]["enum"]) == set(
        capability["evidence_classes"]["material_business_claim_refs"]
    )


def test_empty_overall_support_blocks_request_instead_of_lowering_minimum() -> None:
    capability, catalog = _capability()
    capability["evidence_classes"]["material_business_claim_refs"] = []
    with pytest.raises(ValueError, match="capability_schema_overall_support_empty"):
        capability_pass_b_batch_schema(
            subjects=("RENAMED",),
            catalogs={"RENAMED": catalog},
            capabilities={"RENAMED": capability},
        )


def test_schema_rejects_wrong_subject_capability() -> None:
    capability, catalog = _capability()
    capability["ticker"] = "OTHER"
    with pytest.raises(ValueError, match="capability_schema_subject_mismatch"):
        capability_pass_b_batch_schema(
            subjects=("RENAMED",),
            catalogs={"RENAMED": catalog},
            capabilities={"RENAMED": capability},
        )


def _disjointness_case(*, single_ref: bool = False):
    capability, catalog = _capability(high=80.0, tactical=False, with_risk=not single_ref)
    schema = capability_pass_b_batch_schema(
        subjects=("RENAMED",),
        catalogs={"RENAMED": catalog},
        capabilities={"RENAMED": capability},
    )
    return capability, catalog, schema, _output(reason_class="FUNDAMENTAL_RANGE_POSITION")


def test_disjoint_decisive_selections_remain_accepted() -> None:
    capability, catalog, schema, output = _disjointness_case()
    output["decisions"]["RENAMED"]["decisive_contradicting_claim_refs"] = ["claim:bear"]
    wire, _ = project_provider_wire_schema(schema)
    assert not validate_json_schema(output, schema)
    assert not validate_json_schema(output, wire)
    assert (
        validate_capability_selection(
            output,
            subjects=("RENAMED",),
            catalogs={"RENAMED": catalog},
            capabilities={"RENAMED": capability},
        )["status"]
        == "PASS"
    )


@pytest.mark.parametrize("single_ref", [True, False])
def test_hard_overlap_rejection_is_never_salvaged(single_ref) -> None:
    _, catalog, schema, output = _disjointness_case(single_ref=single_ref)
    output["decisions"]["RENAMED"]["decisive_contradicting_claim_refs"] = ["claim:bull"]
    before = deepcopy(output)
    validation = validate_future_pass_b_shape(
        output, subjects=("RENAMED",), catalogs={"RENAMED": catalog}
    )
    assert "RENAMED:PB_CLAIM_REF_OVERLAP" in validation["errors"]
    assert output == before
    wire, _ = project_provider_wire_schema(schema)
    assert bool(validate_json_schema(output, wire)) is single_ref


@pytest.mark.parametrize("polarity", ["BULLISH", "BEARISH"])
@pytest.mark.parametrize("ticker", ["RENAMED", "UNRELATED"])
def test_single_complete_role_universe_forces_only_empty_contradiction(polarity, ticker) -> None:
    capability, catalog, _, output = _disjointness_case(single_ref=True)
    capability["ticker"] = catalog["ticker"] = ticker
    catalog["atomic_claims"][0]["ticker"] = ticker
    catalog["atomic_claims"][0]["claim"]["polarity"] = polarity
    schema = capability_pass_b_batch_schema(
        subjects=(ticker,), catalogs={ticker: catalog}, capabilities={ticker: capability}
    )
    output["decisions"] = {ticker: output["decisions"]["RENAMED"]}
    properties = schema["properties"]["decisions"]["properties"][ticker]["properties"]
    assert properties["decisive_supporting_claim_refs"]["minItems"] == 1
    opposing = properties["decisive_contradicting_claim_refs"]
    assert opposing["minItems"] == opposing["maxItems"] == 0
    assert not validate_json_schema([], opposing)
    assert validate_json_schema(["claim:bull"], opposing)
    wire, _ = project_provider_wire_schema(schema)
    assert scan_provider_structured_output_schema(wire)["status"] == "PASS"
    assert not validate_json_schema(output, wire)
    assert (
        validate_future_pass_b_shape(output, subjects=(ticker,), catalogs={ticker: catalog})[
            "status"
        ]
        == "PASS"
    )


def test_multi_ref_schema_keeps_complete_authorized_sets_in_both_roles() -> None:
    capability, catalog, schema, _ = _disjointness_case()
    properties = schema["properties"]["decisions"]["properties"]["RENAMED"]["properties"]
    allowed = set(capability["evidence_classes"]["material_business_claim_refs"])
    assert allowed == {"claim:bull", "claim:bear"}
    assert capability["evidence_classes"]["material_risk_claim_refs"] == ["claim:bear"]
    for name in ("decisive_supporting_claim_refs", "decisive_contradicting_claim_refs"):
        assert set(properties[name]["items"]["enum"]) == allowed
        assert properties[name]["maxItems"] == 2
    assert set(catalog["claim_refs"]) == allowed


@pytest.mark.parametrize(
    "field,ref,expected",
    [
        ("decisive_supporting_claim_refs", "claim:bull", "PB_SUPPORT_REF_DUPLICATE"),
        ("decisive_contradicting_claim_refs", "claim:bear", "PB_CONTRADICTION_REF_DUPLICATE"),
    ],
)
def test_duplicate_within_a_decisive_role_remains_rejected(field, ref, expected) -> None:
    _, catalog, _, output = _disjointness_case()
    output["decisions"]["RENAMED"][field] = [ref, ref]
    result = validate_future_pass_b_shape(
        output, subjects=("RENAMED",), catalogs={"RENAMED": catalog}
    )
    assert f"RENAMED:{expected}" in result["errors"]


@pytest.mark.parametrize(
    "field", ["decisive_supporting_claim_refs", "decisive_contradicting_claim_refs"]
)
def test_unoffered_decisive_ref_rejected_by_schema_and_hard_owner(field) -> None:
    _, catalog, schema, output = _disjointness_case()
    output["decisions"]["RENAMED"][field] = ["claim:another-subject"]
    wire, _ = project_provider_wire_schema(schema)
    assert validate_json_schema(output, wire)
    assert (
        validate_future_pass_b_shape(output, subjects=("RENAMED",), catalogs={"RENAMED": catalog})[
            "status"
        ]
        == "FAIL"
    )


def test_prompt_disjointness_is_generic_and_preserves_existing_axes() -> None:
    prompt = capability_prompt_template()
    assert (
        "Supporting and contradicting claim-ref sets for the same decision must be disjoint"
        in prompt
    )
    assert "the opposing array must remain empty" in prompt
    assert "recast a claim merely to fill both arrays" in prompt
    assert "Overall, New Buyer, Holder" in prompt
    assert "CPNG" not in prompt
