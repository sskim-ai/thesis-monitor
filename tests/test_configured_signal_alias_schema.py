from app.services.configured_signal_evidence_service import (
    CURRENT_DIRECTIONAL_REFERENCE_FIELDS,
    is_configured_signal_source_ref,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
)
from app.services.structured_autonomy_alias_service import (
    build_alias_constrained_batch_schema,
    build_evidence_alias_catalog,
)
from app.services.two_stage_directional_service import DirectionalCoreJudgment
from scripts.main_integration_two_stage_directional_m12ae_r2_runtime import (
    _candidate_schema,
)


def _packet() -> DecisionEvidencePacket:
    refs = (
        DecisionEvidenceRef(
            ref_id="current:fact",
            category=EvidenceCategory.EARNINGS,
            label="current",
            statement="current operating evidence",
            source_ref="stock.fact_catalog.current",
        ),
        DecisionEvidenceRef(
            ref_id="configured:weaken",
            category=EvidenceCategory.RISKS,
            label="논리 약화 조건",
            statement="순부채 증가",
            source_ref="stock.thesis.weaken_signals",
        ),
    )
    return DecisionEvidencePacket(
        packet_id="generation",
        ticker="TEST",
        company_name="Test",
        market="us",
        assessment_date="2026-09-12",
        horizon="6-24 months",
        evidence=refs,
        prohibited_claims=(),
        evidence_sha256="0" * 64,
    )


def _enum_for_ref(schema: dict[str, object], schema_ref: str) -> list[str]:
    key = schema_ref.removeprefix("#/$defs/")
    definition = schema["$defs"][key]
    return definition["enum"]


def test_current_fields_get_fenced_alias_definitions() -> None:
    catalog = build_evidence_alias_catalog(_packet())
    current_aliases = tuple(
        entry.alias
        for entry in catalog.entries
        if not is_configured_signal_source_ref(entry.source_ref)
    )
    constraints = {
        "TEST": {
            field: current_aliases for field in CURRENT_DIRECTIONAL_REFERENCE_FIELDS
        }
    }
    schema = build_alias_constrained_batch_schema(
        candidate_schema=_candidate_schema(DirectionalCoreJudgment),
        contract="directional-core-judgment-output-v1",
        packet_id="generation",
        aliases_by_ticker={"TEST": tuple(catalog.by_alias)},
        reference_aliases_by_ticker_field=constraints,
    )
    candidate = schema["properties"]["candidates"]["items"]["anyOf"][0]
    properties = candidate["properties"]
    anchor_ref = properties["material_directional_anchor_basis"]["items"]["$ref"]
    assert _enum_for_ref(schema, anchor_ref) == list(current_aliases)

    sell_ref = properties["sell_drivers"]["items"]["$ref"]
    sell_definition = schema["$defs"][sell_ref.removeprefix("#/$defs/")]
    evidence_ref = sell_definition["properties"]["evidence_refs"]["items"]["$ref"]
    assert _enum_for_ref(schema, evidence_ref) == list(current_aliases)

    future_ref = properties["business_reevaluation_down"]["items"]["$ref"]
    future_definition = schema["$defs"][future_ref.removeprefix("#/$defs/")]
    future_evidence_ref = future_definition["properties"]["evidence_refs"]["items"]["$ref"]
    assert set(_enum_for_ref(schema, future_evidence_ref)) == set(catalog.by_alias)
