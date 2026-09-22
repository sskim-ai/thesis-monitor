from __future__ import annotations

from copy import deepcopy

from scripts.m12cn_policy_contract import (
    CombinationRule,
    CompanyArchetype,
    Confidence,
    DataQualityEffect,
    DataQualityReasonClass,
    EntryBandStatus,
    EntryMethod,
    EntryRangeStatus,
    HolderReasonClass,
    NonWaitEntryBand,
    NonWaitEntryRange,
    NonWaitShadowCandidate,
    RuleId,
    ShadowBatchOutput,
    ThesisState,
    ValuationAffects,
    WaitEntryBand,
    WaitEntryRange,
    WaitShadowCandidate,
    batch_output_schema,
    build_entry_catalog,
    generic_policy_control_matrix,
    model_subject_payload,
    response_format_schema_completeness_scan,
    validate_shadow_candidate,
    wait_entry_component_control_matrix,
)
from scripts.m12cn_policy_shadow import classify_shadow_failure


def _packet() -> dict[str, object]:
    return {
        "ticker": "RENAMED",
        "company_name": "Renamed Co",
        "assessment_date": "2026-09-17",
        "technical_context_status": "eligible",
        "technical_context_quality": "high",
        "data_quality_cautions": [],
        "evidence": [
            {
                "ref_id": "core:business",
                "category": "business",
                "label": "business_quality",
                "statement": {"durability": "high"},
                "as_of": "2026-09-17",
            },
            {
                "ref_id": "canonical:valuation:current",
                "category": "valuation",
                "label": "valuation",
                "statement": {
                    "bvps": 100.0,
                    "currency": "USD",
                    "historical_comparability": "normal",
                    "historical_pb_statistics": {
                        "percentile_25": 1.2,
                        "percentile_50": 1.5,
                        "history_quality": "high",
                    },
                },
                "as_of": "2026-09-17",
            },
            {
                "ref_id": "canonical:valuation:book_quality",
                "category": "valuation",
                "label": "valuation_quality",
                "statement": {
                    "status": "passed",
                    "price_to_book_basis_status": "directly_comparable",
                },
                "as_of": "2026-09-17",
            },
            {
                "ref_id": "timing:price",
                "category": "price",
                "label": "price",
                "statement": {
                    "current_price": 180.0,
                    "currency": "USD",
                    "price_as_of": "2026-09-17",
                    "price_basis": "close",
                },
                "as_of": "2026-09-17",
            },
            {
                "ref_id": "timing:support",
                "category": "technical",
                "label": "chart_support_zone",
                "statement": {
                    "zone_low": 135.0,
                    "zone_high": 145.0,
                    "currency": "USD",
                    "role": "support_zone",
                },
                "as_of": "2026-09-17",
            },
        ],
    }


def _ownership() -> dict[str, object]:
    return {
        "ticker": "RENAMED",
        "core_ref_ids": [
            "core:business",
            "canonical:valuation:current",
            "canonical:valuation:book_quality",
        ],
        "timing_ref_ids": ["timing:price", "timing:support"],
        "expectation_valuation": {
            "valuation_refs": [
                "canonical:valuation:current",
                "canonical:valuation:book_quality",
            ]
        },
    }


def _catalog() -> dict[str, object]:
    entry = build_entry_catalog(_packet(), _ownership())
    return {
        "ticker": "RENAMED",
        "all_evidence_refs": [
            "canonical:valuation:book_quality",
            "canonical:valuation:current",
            "core:business",
            "timing:price",
            "timing:support",
        ],
        "core_evidence_refs": [
            "canonical:valuation:book_quality",
            "canonical:valuation:current",
            "core:business",
        ],
        "timing_evidence_refs": ["timing:price", "timing:support"],
        "valuation_evidence_refs": [
            "canonical:valuation:book_quality",
            "canonical:valuation:current",
        ],
        "material_disclosure_failure_refs": [],
        "positive_quality_refs": [],
        "claim_refs": ["maturity:RENAMED:buy:1"],
        "atomic_claims": [
            {
                "ticker": "RENAMED",
                "claim_ref": "maturity:RENAMED:buy:1",
                "claim": "durable business evidence",
                "parent_source_refs": ["core:business"],
            }
        ],
        "entry_catalog": entry,
    }


def _not_applicable_band() -> NonWaitEntryBand:
    return NonWaitEntryBand(
        status=EntryBandStatus.NOT_APPLICABLE,
        candidate_id=None,
        low=None,
        high=None,
        currency=None,
        evidence_refs=(),
    )


def _resolved_candidate() -> WaitShadowCandidate:
    catalog = _catalog()
    option = catalog["entry_catalog"]["resolved_options"][1]
    return WaitShadowCandidate(
        ticker="RENAMED",
        company_archetype=CompanyArchetype.STRUCTURAL_CYCLICAL_LEADER,
        archetype_confidence=Confidence.HIGH,
        archetype_evidence_refs=("core:business",),
        archetype_rationale="구조적 경쟁력과 순환 노출을 함께 반영했습니다.",
        overall_direction="BUY",
        new_buyer="WAIT",
        holder="HOLDABLE",
        decision_confidence=Confidence.MEDIUM,
        decisive_supporting_claim_refs=("maturity:RENAMED:buy:1",),
        decisive_contradicting_claim_refs=(),
        thesis_state=ThesisState.INTACT,
        data_quality_effect=DataQualityEffect.NONE,
        data_quality_reason_class=DataQualityReasonClass.NOT_APPLICABLE,
        data_quality_reason=None,
        data_quality_evidence_refs=(),
        holder_reason_class=HolderReasonClass.NOT_APPLICABLE,
        holder_reason="보유 논리를 훼손하는 근거가 없습니다.",
        holder_reason_evidence_refs=("core:business",),
        entry_range=WaitEntryRange(
            entry_range_status=EntryRangeStatus.ENTRY_RANGE_RESOLVED,
            entry_option_id=option["entry_option_id"],
            current_price=180.0,
            current_price_as_of="2026-09-17",
            current_price_ref="timing:price",
            preferred_entry_low=option["preferred_entry_low"],
            preferred_entry_high=option["preferred_entry_high"],
            distance_to_band_pct=option["distance_to_band_pct"],
            fundamental_entry_band=WaitEntryBand.model_validate(option["fundamental_entry_band"]),
            tactical_entry_band=WaitEntryBand.model_validate(option["tactical_entry_band"]),
            method=EntryMethod(option["method"]),
            combination_rule=CombinationRule(option["combination_rule"]),
            valuation_basis_refs=tuple(option["valuation_basis_refs"]),
            technical_basis_refs=tuple(option["technical_basis_refs"]),
            assumptions=tuple(option["assumptions"]),
            unresolved_inputs=(),
            re_evaluate_conditions=("가격 또는 가치평가 근거가 바뀔 때",),
        ),
        valuation_affects=(ValuationAffects.NEW_BUYER,),
        rule_trace=(
            RuleId.ARCHETYPE_WEIGHTING,
            RuleId.EVIDENCE_OWNERSHIP,
            RuleId.THESIS_ENTRY_SEPARATION,
            RuleId.WAIT_ENTRY_RANGE,
            RuleId.NO_ARBITRARY_DISCOUNT,
            RuleId.FUNDAMENTAL_TACTICAL_COMBINATION,
        ),
        policy_summary="장기 논리는 유효하지만 현재 가격에서는 진입을 기다립니다.",
    )


def _contains_key(value: object, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_contains_key(child, key) for child in value.values())
    if isinstance(value, list):
        return any(_contains_key(child, key) for child in value)
    return False


def test_generic_policy_controls_and_identity_equivalence_pass() -> None:
    matrix = generic_policy_control_matrix()

    assert matrix["status"] == "PASS"
    assert matrix["control_count"] >= 10
    assert matrix["identity_renamed_equivalence"] == "PASS"
    assert matrix["ticker_or_name_policy_mapping_count"] == 0


def test_entry_catalog_uses_exact_evidence_math_and_not_arbitrary_discount() -> None:
    catalog = build_entry_catalog(_packet(), _ownership())

    assert catalog["current_price"]["value"] == 180.0
    fundamental = catalog["fundamental_candidates"][0]
    assert fundamental["method"] == "BOOK_VALUE_MULTIPLE"
    assert fundamental["low"] == 120.0
    assert fundamental["high"] == 150.0
    overlap = catalog["resolved_options"][1]
    assert overlap["preferred_entry_low"] == 135.0
    assert overlap["preferred_entry_high"] == 145.0
    assert overlap["combination_rule"] == "OVERLAP_INTERSECTION"
    assert overlap["distance_to_band_pct"] == -19.444444


def test_resolved_wait_must_copy_runtime_option_exactly() -> None:
    candidate = _resolved_candidate()

    assert validate_shadow_candidate(candidate, _catalog()) == ()
    changed = candidate.model_copy(
        update={
            "entry_range": candidate.entry_range.model_copy(update={"preferred_entry_low": 134.0})
        }
    )
    assert "resolved_entry_low_not_exact" in validate_shadow_candidate(changed, _catalog())


def test_unresolved_wait_rejects_fabricated_numbers() -> None:
    candidate = _resolved_candidate()
    unresolved = candidate.entry_range.model_copy(
        update={
            "entry_range_status": EntryRangeStatus.ENTRY_RANGE_UNRESOLVED,
            "entry_option_id": None,
            "preferred_entry_low": 150.0,
            "preferred_entry_high": None,
            "distance_to_band_pct": None,
            "fundamental_entry_band": WaitEntryBand(
                status=EntryBandStatus.UNRESOLVED,
                candidate_id=None,
                low=None,
                high=None,
                currency=None,
                evidence_refs=(),
            ),
            "tactical_entry_band": WaitEntryBand(
                status=EntryBandStatus.UNRESOLVED,
                candidate_id=None,
                low=None,
                high=None,
                currency=None,
                evidence_refs=(),
            ),
            "method": EntryMethod.UNRESOLVED,
            "combination_rule": CombinationRule.UNRESOLVED,
            "valuation_basis_refs": (),
            "technical_basis_refs": (),
            "assumptions": (),
            "unresolved_inputs": ("fundamental valuation input",),
        }
    )
    invalid = candidate.model_copy(update={"entry_range": unresolved})

    assert "unresolved_entry_has_preferred_numbers" in validate_shadow_candidate(
        invalid, _catalog()
    )


def test_holder_review_cannot_be_supported_only_by_valuation() -> None:
    candidate = _resolved_candidate().model_copy(
        update={
            "holder": "REVIEW",
            "holder_reason_class": HolderReasonClass.THESIS_UNCERTAINTY,
            "holder_reason_evidence_refs": ("canonical:valuation:current",),
        }
    )

    assert "review_supported_only_by_valuation" in validate_shadow_candidate(candidate, _catalog())


def test_data_quality_limitation_is_not_directional_without_explicit_ref() -> None:
    candidate = _resolved_candidate().model_copy(
        update={
            "data_quality_effect": DataQualityEffect.DIRECTIONAL_NEGATIVE,
            "data_quality_reason_class": DataQualityReasonClass.MATERIAL_DISCLOSURE_FAILURE,
            "data_quality_reason": "공급자 제한을 부정적 근거로 사용했습니다.",
            "data_quality_evidence_refs": ("core:business",),
        }
    )

    assert "unsupported_directional_negative_data_quality" in (
        validate_shadow_candidate(candidate, _catalog())
    )


def test_material_disclosure_negative_requires_catalog_owned_ref() -> None:
    catalog = _catalog()
    catalog["material_disclosure_failure_refs"] = ["core:business"]
    candidate = _resolved_candidate().model_copy(
        update={
            "data_quality_effect": DataQualityEffect.DIRECTIONAL_NEGATIVE,
            "data_quality_reason_class": DataQualityReasonClass.MATERIAL_DISCLOSURE_FAILURE,
            "data_quality_reason": "경제적으로 중대한 공시 실패가 확인됐습니다.",
            "data_quality_evidence_refs": ("core:business",),
        }
    )

    assert "unsupported_directional_negative_data_quality" not in (
        validate_shadow_candidate(candidate, catalog)
    )


def test_batch_schema_has_no_unique_items_keyword() -> None:
    schema = batch_output_schema(
        generation_id="generation",
        packet_id="packet",
        market="us",
        assessment_date="2026-09-17",
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )

    assert not _contains_key(schema, "uniqueItems")
    assert not _contains_key(schema, "default")
    assert not _contains_key(schema, "discriminator")
    assert not _contains_key(schema, "oneOf")
    assert "contract" in schema["required"]
    assert schema["properties"]["candidates"]["minItems"] == 1
    assert schema["properties"]["candidates"]["maxItems"] == 1


def test_batch_schema_is_recursively_complete_for_response_format() -> None:
    schema = batch_output_schema(
        generation_id="generation",
        packet_id="packet",
        market="us",
        assessment_date="2026-09-17",
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )

    scan = response_format_schema_completeness_scan(schema)
    assert scan["status"] == "PASS"
    assert scan["array_without_items_count"] == 0
    assert scan["strict_object_error_count"] == 0
    non_wait_band = schema["$defs"]["NonWaitEntryBand"]["properties"]
    non_wait_entry = schema["$defs"]["NonWaitEntryRange"]["properties"]
    zero_length_arrays = [
        non_wait_band["evidence_refs"],
        non_wait_entry["assumptions"],
        non_wait_entry["re_evaluate_conditions"],
        non_wait_entry["technical_basis_refs"],
        non_wait_entry["unresolved_inputs"],
        non_wait_entry["valuation_basis_refs"],
    ]
    assert all(item["minItems"] == 0 for item in zero_length_arrays)
    assert all(item["maxItems"] == 0 for item in zero_length_arrays)
    assert all(item["items"] == {"type": "string"} for item in zero_length_arrays)


def test_r1_missing_items_negative_control_reports_all_six_paths() -> None:
    schema = batch_output_schema(
        generation_id="generation",
        packet_id="packet",
        market="us",
        assessment_date="2026-09-17",
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )
    band = schema["$defs"]["NonWaitEntryBand"]["properties"]
    entry = schema["$defs"]["NonWaitEntryRange"]["properties"]
    del band["evidence_refs"]["items"]
    for field in (
        "assumptions",
        "re_evaluate_conditions",
        "technical_basis_refs",
        "unresolved_inputs",
        "valuation_basis_refs",
    ):
        del entry[field]["items"]

    scan = response_format_schema_completeness_scan(schema)
    assert scan["status"] == "FAIL"
    assert scan["array_without_items_count"] == 6
    assert set(scan["array_without_items_paths"]) == {
        "$defs.NonWaitEntryBand.properties.evidence_refs",
        "$defs.NonWaitEntryRange.properties.assumptions",
        "$defs.NonWaitEntryRange.properties.re_evaluate_conditions",
        "$defs.NonWaitEntryRange.properties.technical_basis_refs",
        "$defs.NonWaitEntryRange.properties.unresolved_inputs",
        "$defs.NonWaitEntryRange.properties.valuation_basis_refs",
    }


def test_shadow_failure_classifier_uses_raw_provider_schema_error(tmp_path) -> None:
    log = tmp_path / "transport.log"
    log.write_text(
        '{"error":{"type":"invalid_request_error","code":"invalid_json_schema"},"status":400}',
        encoding="utf-8",
    )

    assert (
        classify_shadow_failure(RuntimeError("OTHER_TRANSPORT_FAILURE:attempts=1"), log)
        == "SCHEMA_REJECTED_PRE_INFERENCE"
    )


def test_model_payload_excludes_prior_accepted_and_decision_identity() -> None:
    context = {
        "evidence_packets": [_packet()],
        "evidence_ownership": [_ownership()],
        "prior_accepted": [
            {
                "ticker": "RENAMED",
                "decision": "SELL",
                "accepted_decision_id": "forbidden-id",
            }
        ],
    }
    core = {
        "ticker": "RENAMED",
        "decision": "BUY",
        "holder_axis": {"stance": "HOLDABLE"},
    }
    payload = model_subject_payload(
        context=context,
        frozen_core=core,
        catalog=_catalog(),
    )
    serialized = str(payload)

    assert "prior_accepted" not in serialized
    assert "accepted_decision_id" not in serialized
    assert "forbidden-id" not in serialized
    assert deepcopy(core) == payload["frozen_fundamental_core"]


def test_non_wait_requires_not_applicable_entry_shape() -> None:
    candidate = _resolved_candidate()
    payload = candidate.model_dump(mode="python", exclude={"new_buyer", "entry_range"})
    non_wait = NonWaitShadowCandidate(
        **payload,
        new_buyer="ATTRACTIVE",
        entry_range=NonWaitEntryRange(
            entry_range_status=EntryRangeStatus.NOT_APPLICABLE,
            entry_option_id=None,
            current_price=None,
            current_price_as_of=None,
            current_price_ref=None,
            preferred_entry_low=None,
            preferred_entry_high=None,
            distance_to_band_pct=None,
            fundamental_entry_band=_not_applicable_band(),
            tactical_entry_band=_not_applicable_band(),
            method=EntryMethod.NOT_APPLICABLE,
            combination_rule=CombinationRule.NOT_APPLICABLE,
            valuation_basis_refs=(),
            technical_basis_refs=(),
            assumptions=(),
            unresolved_inputs=(),
            re_evaluate_conditions=(),
        ),
    )

    assert validate_shadow_candidate(non_wait, _catalog()) == ()


def test_wait_entry_component_control_matrix_covers_all_required_cases() -> None:
    matrix = wait_entry_component_control_matrix()

    assert matrix["status"] == "PASS"
    assert matrix["control_count"] == 12
    assert all(row["status"] == "PASS" for row in matrix["rows"])


def test_schema_discriminates_wait_and_structurally_forbids_not_applicable() -> None:
    schema = batch_output_schema(
        generation_id="generation",
        packet_id="packet",
        market="us",
        assessment_date="2026-09-17",
        subjects=("RENAMED",),
        catalogs={"RENAMED": _catalog()},
    )

    items = schema["properties"]["candidates"]["items"]
    assert {branch["$ref"] for branch in items["anyOf"]} == {
        "#/$defs/WaitShadowCandidate",
        "#/$defs/NonWaitShadowCandidate",
    }
    assert "discriminator" not in items
    assert set(schema["$defs"]["WaitEntryBand"]["properties"]["status"]["enum"]) == {
        "RESOLVED",
        "UNRESOLVED",
    }
    assert schema["$defs"]["NonWaitEntryBand"]["properties"]["status"]["const"] == "NOT_APPLICABLE"


def test_wait_tactical_not_applicable_fails_before_semantic_validation() -> None:
    candidate = _resolved_candidate().model_dump(mode="json")
    candidate["entry_range"]["entry_range_status"] = "ENTRY_RANGE_UNRESOLVED"
    candidate["entry_range"]["entry_option_id"] = None
    candidate["entry_range"]["preferred_entry_low"] = None
    candidate["entry_range"]["preferred_entry_high"] = None
    candidate["entry_range"]["distance_to_band_pct"] = None
    candidate["entry_range"]["fundamental_entry_band"] = {
        "status": "UNRESOLVED",
        "candidate_id": None,
        "low": None,
        "high": None,
        "currency": None,
        "evidence_refs": [],
    }
    candidate["entry_range"]["tactical_entry_band"] = {
        "status": "NOT_APPLICABLE",
        "candidate_id": None,
        "low": None,
        "high": None,
        "currency": None,
        "evidence_refs": [],
    }
    candidate["entry_range"]["method"] = "UNRESOLVED"
    candidate["entry_range"]["combination_rule"] = "UNRESOLVED"
    candidate["entry_range"]["valuation_basis_refs"] = []
    candidate["entry_range"]["technical_basis_refs"] = []
    candidate["entry_range"]["assumptions"] = []

    payload = {
        "contract": "m12cn-r2-investment-policy-shadow-v3",
        "generation_id": "generation",
        "packet_id": "packet",
        "market": "us",
        "assessment_date": "2026-09-17",
        "candidates": [candidate],
    }
    try:
        ShadowBatchOutput.model_validate(payload)
    except ValueError:
        pass
    else:
        raise AssertionError("WAIT + tactical NOT_APPLICABLE must fail structurally")


def test_fundamental_only_option_marks_tactical_as_unresolved() -> None:
    catalog = build_entry_catalog(_packet(), _ownership())
    fundamental_only = next(
        option
        for option in catalog["resolved_options"]
        if option["combination_rule"] == "FUNDAMENTAL_ONLY"
    )

    assert fundamental_only["tactical_entry_band"]["status"] == "UNRESOLVED"
    assert fundamental_only["unresolved_inputs"] == [
        "no supplied tactical candidate was safely selected"
    ]
