from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.jobs import accepted_decision_v2_runtime as runtime
from app.jobs.accepted_decision_v2_runtime import (
    V2CLIPathPreconditionError,
    _ClaimLeaseHeartbeat,
    _invoke_signed_in_codex,
    _paths,
    _signed_in_codex_bin,
)
from app.services.accepted_decision_v2_runtime_service import (
    STAGE2_MODEL_OUTPUT_CONTRACT,
    AcceptedV2FundamentalCoreBatch,
    AcceptedV2FundamentalCoreCandidate,
    accepted_v2_fundamental_core_batch_identity_manifest,
    accepted_v2_fundamental_core_output_schema,
    accepted_v2_fundamental_core_prompt,
    accepted_v2_fundamental_core_ref_catalog_manifest,
    accepted_v2_fundamental_core_sha256,
    accepted_v2_maturity_atomic_claim_catalog,
    accepted_v2_production_batch_schema_repair_prompt,
    accepted_v2_production_prompt,
    accepted_v2_production_repair_prompt,
    accepted_v2_stage2_output_schema,
    accepted_v2_stage2_ref_catalog_manifest,
    build_accepted_v2_production_context,
    validate_accepted_v2_candidate_ownership,
    validate_accepted_v2_fundamental_core,
    validate_accepted_v2_fundamental_core_batch_scope,
    validate_accepted_v2_maturity_atomic_identity,
)
from app.services.codex_network_transport_service import (
    NETWORK_READINESS_CONTRACT,
    CodexNetworkReadiness,
    CodexTransportError,
    CodexTransportFailureType,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket,
    DecisionEvidenceRef,
    EvidenceCategory,
    EvidenceClaim,
)
from app.services.directional_balance_service import DirectionalBalance
from app.services.logical_condition_service import (
    LogicalSeverity,
    source_logical_condition,
)
from app.services.preconfirmation_decision_v2_service import (
    PreconfirmationDecisionCandidate,
)
from app.services.evidence_maturity_pricing_service import (
    DriverEvidenceMaturity,
    EvidenceMaturity,
)
from app.services.three_axis_decision_service import (
    HolderDecisionAxis,
    NewBuyerDecisionAxis,
)


@pytest.fixture(autouse=True)
def _signed_in_codex_auth_reference(monkeypatch, tmp_path: Path) -> None:
    codex_home = tmp_path / "signed-in-codex-home"
    codex_home.mkdir()
    auth = codex_home / "auth.json"
    auth.write_text("{}\n", encoding="utf-8")
    auth.chmod(0o600)
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    monkeypatch.setattr(
        runtime,
        "probe_codex_network_readiness",
        lambda: CodexNetworkReadiness(
            contract=NETWORK_READINESS_CONTRACT,
            ready=True,
            host="chatgpt.com",
            port=443,
            attempts=1,
            resolved_address_count=2,
        ),
    )


def _packet() -> DecisionEvidencePacket:
    return DecisionEvidencePacket(
        packet_id="packet-v2-runtime",
        ticker="TEST",
        company_name="Test Company",
        market="us",
        assessment_date="2026-08-30",
        horizon="12-36 months",
        evidence=(
            DecisionEvidenceRef(
                ref_id="canonical:chart:daily",
                category=EvidenceCategory.PRICE_STRUCTURE,
                label="canonical chart",
                statement="canonical chart summary",
                as_of="2026-08-30",
                source_ref="fixture",
            ),
            DecisionEvidenceRef(
                ref_id="technical-feature:daily:rsi14",
                category=EvidenceCategory.PRICE_STRUCTURE,
                label="low-level feature",
                statement="redundant low-level feature",
                as_of="2026-08-30",
                source_ref="fixture",
            ),
        ),
        prohibited_claims=(),
        evidence_sha256="fixture",
    )


def _core(packet: DecisionEvidencePacket) -> AcceptedV2FundamentalCoreCandidate:
    return _fundamental_core(packet.ticker, packet.evidence[0].ref_id)


def _fundamental_packet(
    ticker: str,
    *refs: str,
    logical_condition: bool = False,
) -> DecisionEvidencePacket:
    return DecisionEvidencePacket(
        packet_id="packet-exact-ref",
        ticker=ticker,
        company_name=f"{ticker} Company",
        market="us",
        assessment_date="2026-09-15",
        horizon="12-36 months",
        evidence=tuple(
            DecisionEvidenceRef(
                ref_id=ref_id,
                category=EvidenceCategory.THESIS,
                label=f"{ticker} thesis",
                statement=f"{ticker} canonical thesis evidence",
                as_of="2026-09-15",
                source_ref="fixture",
                logical_condition=(
                    source_logical_condition(
                        subject=ticker,
                        generation_id="exact-ref-fixture",
                        evidence_ref=ref_id,
                        statement="현금전환 개선 또는 매출 성장",
                        severity=LogicalSeverity.STRENGTHENING,
                    )
                    if logical_condition and index == 0
                    else None
                ),
            )
            for index, ref_id in enumerate(refs)
        ),
        prohibited_claims=(),
        evidence_sha256=f"fixture-{ticker}",
    )


def _exact_ref_context():
    rxrx = _fundamental_packet(
        "RXRX",
        "decision-evidence:774e2e7f46d2025d7257",
        "decision-evidence:rxrx-second",
        logical_condition=True,
    )
    ibm = _fundamental_packet("IBM", "decision-evidence:ibm-owned")
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": rxrx.packet_id,
            "market": rxrx.market,
            "assessment_date": rxrx.assessment_date,
            "stocks": [{"ticker": "RXRX"}, {"ticker": "IBM"}],
        },
        claim_id="claim-exact-ref",
        evidence_packets=(rxrx, ibm),
    )
    return context


def _batch_identity_context():
    packets = tuple(
        _fundamental_packet(ticker, f"decision-evidence:{ticker.lower()}-owned")
        for ticker in ("GOOGL", "HUT", "IBM")
    )
    first = packets[0]
    return build_accepted_v2_production_context(
        packet={
            "packet_id": first.packet_id,
            "market": first.market,
            "assessment_date": first.assessment_date,
            "stocks": [{"ticker": packet.ticker} for packet in packets],
        },
        claim_id="claim-batch-identity",
        evidence_packets=packets,
    )


def _stage2_exact_ref_context():
    corz_core_ref = "decision-evidence:36090e913951b40587f1"
    corz = DecisionEvidencePacket(
        packet_id="packet-stage2-exact-ref",
        ticker="CORZ",
        company_name="CORZ Company",
        market="us",
        assessment_date="2026-09-15",
        horizon="12-36 months",
        evidence=(
            DecisionEvidenceRef(
                ref_id=corz_core_ref,
                category=EvidenceCategory.THESIS,
                label="CORZ thesis",
                statement="CORZ canonical thesis evidence",
                as_of="2026-09-15",
                source_ref="fixture",
                logical_condition=source_logical_condition(
                    subject="CORZ",
                    generation_id="stage2-exact-ref-fixture",
                    evidence_ref=corz_core_ref,
                    statement="현금전환 개선 또는 매출 성장",
                    severity=LogicalSeverity.STRENGTHENING,
                ),
            ),
            DecisionEvidenceRef(
                ref_id="canonical:chart:corz-daily",
                category=EvidenceCategory.PRICE_STRUCTURE,
                label="CORZ price timing",
                statement="CORZ canonical price timing evidence",
                as_of="2026-09-15",
                source_ref="fixture",
            ),
        ),
        prohibited_claims=(),
        evidence_sha256="fixture-CORZ",
    )
    ibm = DecisionEvidencePacket(
        packet_id=corz.packet_id,
        ticker="IBM",
        company_name="IBM Company",
        market="us",
        assessment_date=corz.assessment_date,
        horizon="12-36 months",
        evidence=(
            DecisionEvidenceRef(
                ref_id="decision-evidence:ibm-stage2-owned",
                category=EvidenceCategory.THESIS,
                label="IBM thesis",
                statement="IBM canonical thesis evidence",
                as_of="2026-09-15",
                source_ref="fixture",
            ),
            DecisionEvidenceRef(
                ref_id="canonical:chart:ibm-daily",
                category=EvidenceCategory.PRICE_STRUCTURE,
                label="IBM price timing",
                statement="IBM canonical price timing evidence",
                as_of="2026-09-15",
                source_ref="fixture",
            ),
        ),
        prohibited_claims=(),
        evidence_sha256="fixture-IBM",
    )
    return build_accepted_v2_production_context(
        packet={
            "packet_id": corz.packet_id,
            "market": corz.market,
            "assessment_date": corz.assessment_date,
            "stocks": [{"ticker": "CORZ"}, {"ticker": "IBM"}],
        },
        claim_id="claim-stage2-exact-ref",
        evidence_packets=(corz, ibm),
    )


def _schema_ref_enum(schema: dict[str, object]) -> tuple[str, ...]:
    return tuple(
        schema["$defs"]["EvidenceClaim"]["properties"]["evidence_refs"]["items"][
            "enum"
        ]
    )


def _schema_accepts_refs(schema: dict[str, object], refs: tuple[str, ...]) -> bool:
    return set(refs).issubset(_schema_ref_enum(schema))


def _stage2_schema_ref_enums(schema: dict[str, object]) -> dict[str, tuple[str, ...]]:
    definitions = schema["$defs"]
    fields = {
        "evidence_refs": definitions["EvidenceClaim"]["properties"]["evidence_refs"],
    }
    return {
        name: tuple(field["items"]["enum"])
        for name, field in fields.items()
    }


def _fundamental_core(ticker: str, ref_id: str) -> AcceptedV2FundamentalCoreCandidate:
    buy_claim = EvidenceClaim(
        text="검증된 사업 진전이 상방 선택지를 지지합니다.",
        evidence_refs=(ref_id,),
    )
    sell_claim = EvidenceClaim(
        text="같은 자료의 재무 위험이 하방 경계를 지지합니다.",
        evidence_refs=(ref_id,),
    )
    return AcceptedV2FundamentalCoreCandidate(
        ticker=ticker,
        decision="HOLD",
        directional_balance=DirectionalBalance(buy=5, sell=5),
        buy_drivers=(buy_claim,),
        sell_drivers=(sell_claim,),
        balance_summary="검증된 근거를 균형 있게 반영했습니다.",
        confidence="MEDIUM",
        decisive_reason=buy_claim,
        holder_axis=HolderDecisionAxis(stance="HOLDABLE", reason=buy_claim),
    )


def test_fundamental_core_exact_ref_schema_inventory_and_catalog_identity() -> None:
    context = _exact_ref_context()
    subjects = ("RXRX", "IBM")
    schema = accepted_v2_fundamental_core_output_schema(context, subjects=subjects)
    manifest = accepted_v2_fundamental_core_ref_catalog_manifest(
        context,
        subjects=subjects,
    )
    prompt = accepted_v2_fundamental_core_prompt(context, subjects=subjects)

    ref_paths: list[str] = []

    def inventory(value: object, path: str = "$") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if key in {"evidence_refs", "source_condition_ref", "leaf_ref"}:
                    ref_paths.append(child_path)
                inventory(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                inventory(child, f"{path}[{index}]")

    inventory(schema)
    assert ref_paths == [
        "$.$defs.ClaimLogicalCondition.properties.source_condition_ref",
        "$.$defs.ClaimLogicalLeaf.properties.leaf_ref",
        "$.$defs.EvidenceClaim.properties.evidence_refs",
    ]
    assert _schema_ref_enum(schema) == tuple(manifest["allowed_refs"])
    assert schema["$defs"]["ClaimLogicalCondition"]["properties"][
        "source_condition_ref"
    ]["enum"] == manifest["allowed_source_condition_refs"]
    assert schema["$defs"]["ClaimLogicalLeaf"]["properties"]["leaf_ref"][
        "enum"
    ] == manifest["allowed_leaf_refs"]
    assert f'"ref_catalog_hash":"{manifest["ref_catalog_hash"]}"' in prompt
    assert schema["$defs"]["EvidenceClaim"]["properties"]["text"].get("enum") is None
    assert "Evidence refs are identifiers." in prompt
    assert "Never synthesize, shorten, edit, guess, or repair an evidence ref." in prompt


def test_fundamental_core_schema_closes_dynamic_batch_and_identity() -> None:
    context = _batch_identity_context()
    subjects = ("GOOGL", "HUT", "IBM")
    schema = accepted_v2_fundamental_core_output_schema(context, subjects=subjects)
    properties = schema["properties"]
    cores = properties["cores"]
    ticker = schema["$defs"]["AcceptedV2FundamentalCoreCandidate"]["properties"][
        "ticker"
    ]

    assert cores["minItems"] == cores["maxItems"] == 3
    assert ticker["enum"] == list(subjects)
    assert properties["contract"]["const"] == "v2-accepted-fundamental-core-v1"
    assert properties["packet_id"]["const"] == context.packet_id
    assert properties["claim_id"]["const"] == context.claim_id
    assert properties["market"]["const"] == context.market
    assert properties["assessment_date"]["const"] == context.assessment_date

    manifest = accepted_v2_fundamental_core_batch_identity_manifest(
        context,
        subjects=subjects,
    )
    assert manifest["contract"] == "fundamental-core-batch-identity-v1"
    assert manifest["expected_subject_count"] == 3
    assert manifest["expected_tickers"] == list(subjects)
    assert len(str(manifest["ticker_domain_hash"])) == 64
    assert len(str(manifest["identity_contract_hash"])) == 64


def test_fundamental_core_schema_cardinality_is_generated_per_batch() -> None:
    context = _batch_identity_context()
    three = accepted_v2_fundamental_core_output_schema(
        context,
        subjects=("GOOGL", "HUT", "IBM"),
    )["properties"]["cores"]
    two = accepted_v2_fundamental_core_output_schema(
        context,
        subjects=("GOOGL", "HUT"),
    )["properties"]["cores"]

    assert (three["minItems"], three["maxItems"]) == (3, 3)
    assert (two["minItems"], two["maxItems"]) == (2, 2)


def test_fundamental_core_old_batch2_omission_fails_repaired_cardinality() -> None:
    context = _batch_identity_context()
    subjects = ("GOOGL", "HUT", "IBM")
    schema = accepted_v2_fundamental_core_output_schema(context, subjects=subjects)
    returned = ("GOOGL", "HUT")

    assert len(returned) < schema["properties"]["cores"]["minItems"]


def test_fundamental_core_prompt_closes_subject_completeness_and_order() -> None:
    prompt = accepted_v2_fundamental_core_prompt(
        _batch_identity_context(),
        subjects=("GOOGL", "HUT", "IBM"),
    )

    assert "Emit exactly one core for every supplied ticker" in prompt
    assert "in the same order as FUNDAMENTAL_CORE_CONTEXT" in prompt
    assert "Do not omit, duplicate, replace, or reorder subjects" in prompt


def test_fundamental_core_batch_scope_accepts_exact_three_and_two() -> None:
    context = _batch_identity_context()
    cores = tuple(
        _fundamental_core(ticker, f"decision-evidence:{ticker.lower()}-owned")
        for ticker in ("GOOGL", "HUT", "IBM")
    )
    batch = AcceptedV2FundamentalCoreBatch(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        cores=cores,
    )

    assert (
        validate_accepted_v2_fundamental_core_batch_scope(
            batch,
            context,
            subjects=("GOOGL", "HUT", "IBM"),
        )
        == ()
    )
    assert (
        validate_accepted_v2_fundamental_core_batch_scope(
            batch.model_copy(update={"cores": cores[:2]}),
            context,
            subjects=("GOOGL", "HUT"),
        )
        == ()
    )


@pytest.mark.parametrize(
    ("returned", "expected_error"),
    (
        (("GOOGL", "HUT"), "cardinality_mismatch:expected=3:returned=2"),
        (
            ("GOOGL", "HUT", "IBM", "IBM"),
            "cardinality_mismatch:expected=3:returned=4",
        ),
        (("GOOGL", "GOOGL", "HUT"), "duplicate_ticker:GOOGL"),
        (("GOOGL", "HUT", "TSLA"), "extra_ticker:TSLA"),
    ),
)
def test_fundamental_core_batch_scope_rejects_cardinality_and_ticker_set(
    returned: tuple[str, ...],
    expected_error: str,
) -> None:
    context = _batch_identity_context()
    batch = AcceptedV2FundamentalCoreBatch(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        cores=tuple(
            _fundamental_core(ticker, "decision-evidence:googl-owned")
            for ticker in returned
        ),
    )

    errors = validate_accepted_v2_fundamental_core_batch_scope(
        batch,
        context,
        subjects=("GOOGL", "HUT", "IBM"),
    )

    assert expected_error in errors


@pytest.mark.parametrize(
    ("field", "value", "expected_error"),
    (
        ("packet_id", "wrong-packet", "packet_id_mismatch"),
        ("claim_id", "wrong-claim", "claim_id_mismatch"),
        ("market", "kr", "market_mismatch"),
        ("assessment_date", "2026-09-14", "assessment_date_mismatch"),
    ),
)
def test_fundamental_core_batch_scope_rejects_top_level_identity(
    field: str,
    value: str,
    expected_error: str,
) -> None:
    context = _batch_identity_context()
    batch = AcceptedV2FundamentalCoreBatch(
        packet_id=context.packet_id,
        claim_id=context.claim_id,
        market=context.market,
        assessment_date=context.assessment_date,
        cores=tuple(
            _fundamental_core(ticker, f"decision-evidence:{ticker.lower()}-owned")
            for ticker in ("GOOGL", "HUT", "IBM")
        ),
    ).model_copy(update={field: value})

    assert expected_error in validate_accepted_v2_fundamental_core_batch_scope(
        batch,
        context,
        subjects=("GOOGL", "HUT", "IBM"),
    )


def test_fundamental_core_exact_ref_positive_fixtures() -> None:
    context = _exact_ref_context()
    schema = accepted_v2_fundamental_core_output_schema(
        context,
        subjects=("RXRX", "IBM"),
    )
    valid = "decision-evidence:774e2e7f46d2025d7257"
    second = "decision-evidence:rxrx-second"

    assert _schema_accepts_refs(schema, (valid,))
    assert _schema_accepts_refs(schema, (valid, second))
    ownership = {row.ticker: row for row in context.evidence_ownership}
    assert validate_accepted_v2_fundamental_core(
        _fundamental_core("RXRX", valid), ownership["RXRX"]
    ) == ()


@pytest.mark.parametrize(
    "invalid_ref",
    (
        "decision-evidence:774e2e7f46d2020d7257",
        "decision-evidence:774e2e7f46d2025d725",
        "decision-evidence:774e2e7f46d20255d7257",
        "decision-evidence:0123456789abcdef0123",
    ),
)
def test_fundamental_core_exact_ref_negative_fixtures(invalid_ref: str) -> None:
    context = _exact_ref_context()
    schema = accepted_v2_fundamental_core_output_schema(
        context,
        subjects=("RXRX", "IBM"),
    )

    assert not _schema_accepts_refs(schema, (invalid_ref,))


def test_batch_union_schema_keeps_cross_subject_semantic_ownership_hard_fail() -> None:
    context = _exact_ref_context()
    schema = accepted_v2_fundamental_core_output_schema(
        context,
        subjects=("RXRX", "IBM"),
    )
    ibm_ref = "decision-evidence:ibm-owned"
    ownership = {row.ticker: row for row in context.evidence_ownership}

    assert _schema_accepts_refs(schema, (ibm_ref,))
    assert validate_accepted_v2_fundamental_core(
        _fundamental_core("RXRX", ibm_ref), ownership["RXRX"]
    ) == (f"noncore_ref_in_fundamental_core:{ibm_ref}",)


def test_stage2_exact_ref_schema_inventory_and_catalog_identity() -> None:
    context = _stage2_exact_ref_context()
    schema = accepted_v2_stage2_output_schema(context, subjects=("CORZ", "IBM"))
    manifest = accepted_v2_stage2_ref_catalog_manifest(
        context,
        subjects=("CORZ", "IBM"),
    )
    core = _fundamental_core("CORZ", "decision-evidence:36090e913951b40587f1")
    prompt = accepted_v2_production_prompt(
        context,
        fundamental_cores=(core,),
        subjects=("CORZ",),
    )

    ref_paths: set[str] = set()

    def inventory(value: object, path: str = "$") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if key in {
                    "evidence_refs",
                    "supporting_evidence_refs",
                    "contradicting_evidence_refs",
                    "supporting_claim_refs",
                    "contradicting_claim_refs",
                    "source_condition_ref",
                    "leaf_ref",
                }:
                    ref_paths.add(child_path)
                inventory(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                inventory(child, f"{path}[{index}]")

    inventory(schema)
    assert ref_paths == {
        "$.$defs.ClaimLogicalCondition.properties.source_condition_ref",
        "$.$defs.ClaimLogicalLeaf.properties.leaf_ref",
        "$.$defs.DriverEvidenceMaturity.properties.contradicting_claim_refs",
        "$.$defs.DriverEvidenceMaturity.properties.supporting_claim_refs",
        "$.$defs.EvidenceClaim.properties.evidence_refs",
    }
    expected_refs = tuple(manifest["allowed_refs"])
    assert all(
        refs == expected_refs for refs in _stage2_schema_ref_enums(schema).values()
    )
    assert schema["$defs"]["ClaimLogicalCondition"]["properties"][
        "source_condition_ref"
    ]["enum"] == manifest["allowed_source_condition_refs"]
    assert schema["$defs"]["ClaimLogicalLeaf"]["properties"]["leaf_ref"][
        "enum"
    ] == manifest["allowed_leaf_refs"]
    corz_manifest = accepted_v2_stage2_ref_catalog_manifest(
        context,
        subjects=("CORZ",),
        fundamental_cores=(core,),
    )
    assert f'"ref_catalog_hash":"{corz_manifest["ref_catalog_hash"]}"' in prompt
    assert "Evidence refs are exact opaque identifiers." in prompt
    assert "Never edit, append, shorten, infer, synthesize, guess, or repair" in prompt


def test_stage2_atomic_claim_schema_and_prompt_are_bound_to_frozen_cores() -> None:
    context = _stage2_exact_ref_context()
    subjects = ("CORZ", "IBM")
    cores = (
        _fundamental_core("CORZ", "decision-evidence:36090e913951b40587f1"),
        _fundamental_core("IBM", "decision-evidence:ibm-stage2-owned"),
    )
    schema = accepted_v2_stage2_output_schema(
        context,
        subjects=subjects,
        fundamental_cores=cores,
    )
    manifest = accepted_v2_stage2_ref_catalog_manifest(
        context,
        subjects=subjects,
        fundamental_cores=cores,
    )
    maturity = schema["$defs"]["DriverEvidenceMaturity"]["properties"]
    expected = manifest["allowed_maturity_claim_refs"]

    assert expected
    assert maturity["supporting_claim_refs"]["items"]["enum"] == expected
    assert maturity["contradicting_claim_refs"]["items"]["enum"] == expected
    assert maturity["supporting_claim_refs"]["minItems"] == 1
    assert "minItems" not in maturity["contradicting_claim_refs"]
    prompt = accepted_v2_production_prompt(
        context,
        fundamental_cores=(cores[0],),
        subjects=("CORZ",),
    )
    corz_manifest = accepted_v2_stage2_ref_catalog_manifest(
        context,
        subjects=("CORZ",),
        fundamental_cores=(cores[0],),
    )
    assert corz_manifest["maturity_atomic_claim_count"] == 2
    assert all(
        row["parent_source_refs"] == ["decision-evidence:36090e913951b40587f1"]
        for row in corz_manifest["maturity_atomic_claims"]
    )
    assert (
        f'"maturity_atomic_claim_catalog_hash":"'
        f'{corz_manifest["maturity_atomic_claim_catalog_hash"]}"'
    ) in prompt
    assert "Absolute BULLISH/BEARISH polarity is metadata" in prompt


def test_m12cl_stage2_prompt_requires_atomic_support_without_ticker_targets() -> None:
    context = _stage2_exact_ref_context()
    core = _fundamental_core("CORZ", "decision-evidence:36090e913951b40587f1")

    prompt = accepted_v2_production_prompt(
        context,
        fundamental_cores=(core,),
        subjects=("CORZ",),
    )

    assert "supporting_claim_refs must contain at least one exact same-ticker" in prompt
    assert "do not emit that driver" in prompt
    assert "contradicting_claim_refs may be empty" in prompt
    assert "cannot substitute for a missing atomic claim identity" in prompt
    assert "WRD" not in prompt
    assert "WULF" not in prompt
    assert "repair model" not in prompt.lower()
    assert "retry" not in prompt.lower()


def test_stage2_prompt_states_canonical_preconfirmation_buy_invariant() -> None:
    context = _stage2_exact_ref_context()
    core = _fundamental_core("CORZ", "decision-evidence:36090e913951b40587f1")

    prompt = accepted_v2_production_prompt(
        context,
        fundamental_cores=(core,),
        subjects=("CORZ",),
    )

    assert "at least one decisive driver whose maturity is EARLY or PARTIAL" in prompt
    assert "set pre_confirmation_buy=true" in prompt
    assert "provide all six preconfirmation_buy_explanation claims" in prompt
    assert "pre_confirmation_buy=true may coexist with new_buyer_axis=WAIT" in prompt
    assert "holder_axis=HOLDABLE" in prompt
    assert "timing=UNFAVORABLE" in prompt
    assert "price confirmation is an entry/price check" in prompt
    assert "must never set or clear pre_confirmation_buy" in prompt


def test_fundamental_core_rejects_one_claim_with_conflicting_absolute_polarity() -> None:
    context = _stage2_exact_ref_context()
    ownership = {row.ticker: row for row in context.evidence_ownership}["CORZ"]
    ref_id = "decision-evidence:36090e913951b40587f1"
    claim = EvidenceClaim(text="동일 구조화 주장입니다.", evidence_refs=(ref_id,))
    core = AcceptedV2FundamentalCoreCandidate(
        ticker="CORZ",
        decision="HOLD",
        directional_balance=DirectionalBalance(buy=5, sell=5),
        buy_drivers=(claim,),
        sell_drivers=(claim,),
        balance_summary="동일 주장을 양쪽에 중복하지 않습니다.",
        confidence="MEDIUM",
        decisive_reason=claim,
        holder_axis=HolderDecisionAxis(stance="HOLDABLE", reason=claim),
    )

    errors = validate_accepted_v2_fundamental_core(core, ownership)

    assert any(
        error.startswith("fundamental_core_atomic_claim_identity_invalid:")
        for error in errors
    )


def test_old_corz_source_overlap_without_atomic_claims_fails_closed() -> None:
    parent = "decision-evidence:acea5134d19f8ded2449"
    core = _fundamental_core("CORZ", parent)
    row = DriverEvidenceMaturity(
        driver="높은 기대에 비해 실행과 현금흐름 검증이 덜 성숙하다.",
        decisive=True,
        maturity=EvidenceMaturity.MIXED,
        supporting_evidence_refs=("decision-evidence:expectations", parent),
        contradicting_evidence_refs=(parent,),
        what_remains_unproven=EvidenceClaim(
            text="현금흐름 전환은 아직 확인되지 않았습니다.",
            evidence_refs=("decision-evidence:expectations",),
        ),
        as_of="2026-09-15",
    )
    candidate = SimpleNamespace(driver_maturity=(row,))

    errors = validate_accepted_v2_maturity_atomic_identity(candidate, core)  # type: ignore[arg-type]

    assert "maturity_atomic_claim_identity_missing:0:supporting" in errors
    assert any(error.startswith("maturity_unproven_parent_source_overlap") for error in errors)
    assert len(accepted_v2_maturity_atomic_claim_catalog(core)) == 2


def test_stage2_typed_identity_and_runtime_owned_maturity_date_schema_are_closed() -> None:
    context = _stage2_exact_ref_context()
    subjects = ("CORZ", "IBM")
    schema = accepted_v2_stage2_output_schema(context, subjects=subjects)
    manifest = accepted_v2_stage2_ref_catalog_manifest(context, subjects=subjects)

    assert schema["properties"]["packet_id"]["const"] == context.packet_id
    assert schema["properties"]["contract"]["const"] == STAGE2_MODEL_OUTPUT_CONTRACT
    assert schema["properties"]["claim_id"]["const"] == context.claim_id
    assert schema["properties"]["market"]["const"] == context.market
    assert schema["properties"]["assessment_date"]["const"] == context.assessment_date
    for definition in (
        "AcceptedV2Adjudication",
        "AcceptedV2FundamentalCoreCandidate",
        "PreconfirmationDecisionCandidate",
    ):
        assert schema["$defs"][definition]["properties"]["ticker"]["enum"] == list(
            subjects
        )
    maturity = schema["$defs"]["DriverEvidenceMaturity"]
    assert "supporting_evidence_refs" not in maturity["properties"]
    assert "contradicting_evidence_refs" not in maturity["properties"]
    assert "as_of" not in maturity["properties"]
    assert "supporting_evidence_refs" not in maturity["required"]
    assert "contradicting_evidence_refs" not in maturity["required"]
    assert "as_of" not in maturity["required"]
    assert maturity["additionalProperties"] is False
    assert manifest["allowed_maturity_dates"]


def test_stage2_exact_ref_positive_fixtures() -> None:
    context = _stage2_exact_ref_context()
    schema = accepted_v2_stage2_output_schema(context, subjects=("CORZ", "IBM"))
    valid = "decision-evidence:36090e913951b40587f1"
    second = "canonical:chart:corz-daily"

    assert all(
        {valid}.issubset(refs)
        for refs in _stage2_schema_ref_enums(schema).values()
    )
    assert all(
        {valid, second}.issubset(refs)
        for refs in _stage2_schema_ref_enums(schema).values()
    )


@pytest.mark.parametrize(
    "invalid_ref",
    (
        "decision-evidence:36090e913951b40587f1d",
        "decision-evidence:36090e913951b40587f",
        "decision-evidence:36090e913951b40587e1",
        "decision-evidence:0123456789abcdef0123",
    ),
)
def test_stage2_exact_ref_negative_fixtures(invalid_ref: str) -> None:
    context = _stage2_exact_ref_context()
    schema = accepted_v2_stage2_output_schema(context, subjects=("CORZ", "IBM"))

    assert all(
        invalid_ref not in refs for refs in _stage2_schema_ref_enums(schema).values()
    )


def test_stage2_batch_union_keeps_cross_subject_ownership_hard_fail() -> None:
    context = _stage2_exact_ref_context()
    schema = accepted_v2_stage2_output_schema(context, subjects=("CORZ", "IBM"))
    corz_ref = "decision-evidence:36090e913951b40587f1"
    ibm_ref = "decision-evidence:ibm-stage2-owned"
    core = _fundamental_core("CORZ", corz_ref)
    candidate = PreconfirmationDecisionCandidate.model_construct(
        ticker="CORZ",
        fundamental_core_sha256=accepted_v2_fundamental_core_sha256(core),
        decision=core.decision,
        new_buyer_axis=NewBuyerDecisionAxis(
            stance="WAIT",
            reason=EvidenceClaim(
                text="IBM 근거를 잘못 참조했습니다.",
                evidence_refs=(ibm_ref,),
            ),
        ),
        holder_axis=core.holder_axis,
        directional_balance=core.directional_balance,
        buy_drivers=core.buy_drivers,
        sell_drivers=core.sell_drivers,
        balance_summary=core.balance_summary,
        confidence=core.confidence,
        decisive_reason=core.decisive_reason,
    )
    ownership = {row.ticker: row for row in context.evidence_ownership}

    assert all(
        ibm_ref in refs for refs in _stage2_schema_ref_enums(schema).values()
    )
    assert validate_accepted_v2_candidate_ownership(
        candidate,
        core,
        ownership["CORZ"],
    ) == (f"new_buyer_ref_outside_owned_evidence:{ibm_ref}",)


def test_production_prompt_keeps_canonical_chart_and_omits_low_level_features() -> None:
    packet = _packet()
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": packet.ticker}],
        },
        claim_id="claim-v2-runtime",
        evidence_packets=(packet,),
    )

    core_prompt = accepted_v2_fundamental_core_prompt(context)
    prompt = accepted_v2_production_prompt(
        context, fundamental_cores=(_core(packet),)
    )

    assert "canonical:chart:daily" in prompt
    assert "canonical:chart:daily" not in core_prompt
    assert "technical-feature:daily:rsi14" not in prompt
    assert '"claim_id":"claim-v2-runtime"' in prompt
    assert "Do not introduce or infer ROIC" in prompt
    assert "runtime owns driver_maturity source-evidence refs" in prompt
    assert "Do not emit or infer driver_maturity.as_of" in prompt
    assert "Every driver_maturity.as_of must be" not in prompt
    assert "in Stage-2-owned fields" in prompt
    assert "Frozen FUNDAMENTAL_CORE fields must still be copied exactly" in prompt
    assert "Do not modify frozen core text" in prompt
    assert (
        "post_confirmation_hold=true only when decision=HOLD and "
        "overall_maturity.maturity=CONFIRMED"
    ) in prompt
    assert "A HOLD decision alone does not imply post_confirmation_hold=true" in prompt
    assert "do not change the decision or maturity merely to satisfy this flag" in prompt


def test_bounded_repair_prompt_names_errors_and_keeps_exact_identity() -> None:
    packet = _packet()
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": packet.ticker}],
        },
        claim_id="claim-v2-runtime",
        evidence_packets=(packet,),
    )
    candidate = PreconfirmationDecisionCandidate.model_construct(ticker=packet.ticker)

    prompt = accepted_v2_production_repair_prompt(
        context,
        fundamental_core=_core(packet),
        ticker=packet.ticker,
        rejected_candidate=candidate,
        validation_errors=("unsupported_metric_or_inference",),
    )

    assert "BOUNDED_VALIDATOR_REPAIR" in prompt
    assert "unsupported_metric_or_inference" in prompt
    assert '"claim_id":"claim-v2-runtime"' in prompt


def test_bounded_repair_prompt_explains_temporal_and_hold_contracts() -> None:
    packet = _packet()
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": packet.ticker}],
        },
        claim_id="claim-v2-runtime",
        evidence_packets=(packet,),
    )
    candidate = PreconfirmationDecisionCandidate.model_construct(ticker=packet.ticker)

    prompt = accepted_v2_production_repair_prompt(
        context,
        fundamental_core=_core(packet),
        ticker=packet.ticker,
        rejected_candidate=candidate,
        validation_errors=(
            "future_maturity_evidence:cash conversion",
            "postconfirmation_hold_without_confirmed_maturity",
        ),
    )

    assert "not later than assessment_date" in prompt
    assert "runtime derives driver_maturity.as_of" in prompt
    assert "post_confirmation_hold=false" in prompt
    assert "postconfirmation_hold_explanation=null" in prompt


def test_bounded_batch_schema_repair_keeps_scope_and_strict_errors() -> None:
    packet = _packet()
    context = build_accepted_v2_production_context(
        packet={
            "packet_id": packet.packet_id,
            "market": packet.market,
            "assessment_date": packet.assessment_date,
            "stocks": [{"ticker": packet.ticker}],
        },
        claim_id="claim-v2-runtime",
        evidence_packets=(packet,),
    )

    prompt = accepted_v2_production_batch_schema_repair_prompt(
        context,
        fundamental_cores=(_core(packet),),
        subjects=(packet.ticker,),
        rejected_output={"candidates": [{"ticker": packet.ticker}]},
        validation_errors=(
            "candidates.0.driver_maturity.2:value_error:"
            "maturity_atomic_claim_polarity_overlap",
        ),
    )

    assert "BOUNDED_BATCH_SCHEMA_REPAIR" in prompt
    assert "maturity_atomic_claim_polarity_overlap" in prompt
    assert '"subjects":["TEST"]' in prompt
    assert '"claim_id":"claim-v2-runtime"' in prompt


def test_signed_in_codex_bin_prefers_explicit_executable(
    monkeypatch, tmp_path: Path
) -> None:
    executable = tmp_path / "codex"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    executable.chmod(0o755)
    monkeypatch.setenv("CODEX_CLI_BIN", str(executable))

    assert _signed_in_codex_bin() == str(executable)


@pytest.mark.parametrize(
    ("schema_relative", "cwd_relative", "io_relative"),
    (
        (False, False, False),
        (True, True, False),
        (True, False, False),
        (True, True, True),
    ),
)
def test_signed_in_codex_invocation_normalizes_path_permutations(
    monkeypatch,
    tmp_path: Path,
    schema_relative: bool,
    cwd_relative: bool,
    io_relative: bool,
) -> None:
    relative_dir = Path("data/ai_review/claims")
    absolute_dir = tmp_path / relative_dir
    absolute_dir.mkdir(parents=True)
    prompt_absolute = absolute_dir / "claim.prompt.txt"
    schema_absolute = absolute_dir / "claim.schema.json"
    output_absolute = absolute_dir / "claim.output.json"
    log_absolute = absolute_dir / "claim.log"
    prompt_absolute.write_text("prompt", encoding="utf-8")
    schema_absolute.write_text("{}", encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["cwd"] = kwargs["cwd"]
        Path(command[command.index("-o") + 1]).write_text("{}", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(runtime, "_repository_root", lambda: tmp_path)
    monkeypatch.setattr(runtime.subprocess, "run", fake_run)

    _invoke_signed_in_codex(
        codex_bin="/bin/echo",
        prompt=(relative_dir / prompt_absolute.name) if io_relative else prompt_absolute,
        output=(relative_dir / output_absolute.name) if io_relative else output_absolute,
        log=(relative_dir / log_absolute.name) if io_relative else log_absolute,
        schema=(relative_dir / schema_absolute.name) if schema_relative else schema_absolute,
        cwd=relative_dir if cwd_relative else absolute_dir,
        timeout=30,
        state_namespace="test-path-normalization",
    )

    command = captured["command"]
    assert isinstance(command, list)
    assert Path(command[command.index("--output-schema") + 1]) == schema_absolute
    assert Path(command[command.index("-o") + 1]) == output_absolute
    assert captured["cwd"] == absolute_dir
    assert output_absolute.read_text(encoding="utf-8") == "{}"


def test_signed_in_codex_missing_schema_fails_before_subprocess(
    monkeypatch,
    tmp_path: Path,
) -> None:
    relative_dir = Path("data/ai_review/claims")
    absolute_dir = tmp_path / relative_dir
    absolute_dir.mkdir(parents=True)
    (absolute_dir / "claim.prompt.txt").write_text("prompt", encoding="utf-8")
    called = False

    def fake_run(*args, **kwargs):
        nonlocal called
        called = True
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(runtime, "_repository_root", lambda: tmp_path)
    monkeypatch.setattr(runtime.subprocess, "run", fake_run)

    with pytest.raises(
        V2CLIPathPreconditionError,
        match="schema_exists",
    ):
        _invoke_signed_in_codex(
            codex_bin="/bin/echo",
            prompt=relative_dir / "claim.prompt.txt",
            output=relative_dir / "claim.output.json",
            log=relative_dir / "claim.log",
            schema=relative_dir / "missing.schema.json",
            cwd=relative_dir,
            timeout=30,
            state_namespace="test-missing-schema",
        )

    assert called is False


def test_signed_in_codex_invocation_creates_canonical_write_directories(
    monkeypatch,
    tmp_path: Path,
) -> None:
    relative_claims = Path("data/ai_review/claims")
    relative_outbox = Path("data/ai_review/outbox")
    claims = tmp_path / relative_claims
    claims.mkdir(parents=True)
    (claims / "claim.prompt.txt").write_text("prompt", encoding="utf-8")
    (claims / "claim.schema.json").write_text("{}", encoding="utf-8")

    def fake_run(command, **kwargs):
        Path(command[command.index("-o") + 1]).write_text("{}", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(runtime, "_repository_root", lambda: tmp_path)
    monkeypatch.setattr(runtime.subprocess, "run", fake_run)

    _invoke_signed_in_codex(
        codex_bin="/bin/echo",
        prompt=relative_claims / "claim.prompt.txt",
        output=relative_outbox / "claim.output.json",
        log=relative_outbox / "logs" / "claim.log",
        schema=relative_claims / "claim.schema.json",
        cwd=relative_claims,
        timeout=30,
        state_namespace="test-write-directories",
    )

    assert (tmp_path / relative_outbox / "claim.output.json").is_file()
    assert (tmp_path / relative_outbox / "logs" / "claim.log").is_file()


def test_signed_in_codex_retries_one_transient_transport_failure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    claims = tmp_path / "data/ai_review/claims"
    claims.mkdir(parents=True)
    prompt = claims / "claim.prompt.txt"
    schema = claims / "claim.schema.json"
    output = claims / "claim.output.json"
    log = claims / "claim.log"
    prompt.write_text("prompt", encoding="utf-8")
    schema.write_text("{}", encoding="utf-8")
    run_count = 0

    def fake_run(command, **kwargs):
        nonlocal run_count
        run_count += 1
        if run_count == 1:
            kwargs["stdout"].write(
                "failed to connect to websocket: stream disconnected before completion"
            )
            return SimpleNamespace(returncode=1)
        Path(command[command.index("-o") + 1]).write_text("{}", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(runtime, "_repository_root", lambda: tmp_path)
    monkeypatch.setattr(runtime.subprocess, "run", fake_run)
    monkeypatch.setattr(runtime.time, "sleep", lambda _: None)

    telemetry = _invoke_signed_in_codex(
        codex_bin="/bin/echo",
        prompt=prompt,
        output=output,
        log=log,
        schema=schema,
        cwd=claims,
        timeout=30,
        state_namespace="test-transport-retry",
    )

    assert run_count == 2
    assert telemetry == {
        "contract": NETWORK_READINESS_CONTRACT,
        "network_probe_attempts": 2,
        "transport_attempts": 2,
        "retry_recovered": True,
    }
    assert "transport attempt 1/2" in log.read_text(encoding="utf-8")


def test_signed_in_codex_network_preflight_failure_never_starts_subprocess(
    monkeypatch,
    tmp_path: Path,
) -> None:
    claims = tmp_path / "data/ai_review/claims"
    claims.mkdir(parents=True)
    prompt = claims / "claim.prompt.txt"
    schema = claims / "claim.schema.json"
    prompt.write_text("prompt", encoding="utf-8")
    schema.write_text("{}", encoding="utf-8")
    called = False

    def fake_run(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(runtime, "_repository_root", lambda: tmp_path)
    monkeypatch.setattr(runtime.subprocess, "run", fake_run)
    monkeypatch.setattr(
        runtime,
        "probe_codex_network_readiness",
        lambda: CodexNetworkReadiness(
            contract=NETWORK_READINESS_CONTRACT,
            ready=False,
            host="chatgpt.com",
            port=443,
            attempts=3,
            resolved_address_count=0,
            failure_type=CodexTransportFailureType.DNS_FAILURE,
            failure_history=(
                CodexTransportFailureType.DNS_FAILURE,
            )
            * 3,
        ),
    )

    with pytest.raises(
        CodexTransportError,
        match="DNS_FAILURE:attempts=3",
    ):
        _invoke_signed_in_codex(
            codex_bin="/bin/echo",
            prompt=prompt,
            output=claims / "claim.output.json",
            log=claims / "claim.log",
            schema=schema,
            cwd=claims,
            timeout=30,
            state_namespace="test-network-preflight-failure",
        )

    assert called is False


def test_unknown_issuer_fails_fast_without_wrapper_retry(monkeypatch, tmp_path: Path) -> None:
    claims = tmp_path / "data/ai_review/claims"
    claims.mkdir(parents=True)
    prompt = claims / "claim.prompt.txt"
    schema = claims / "claim.schema.json"
    prompt.write_text("prompt", encoding="utf-8")
    schema.write_text("{}", encoding="utf-8")
    run_count = 0

    def fake_run(command, **kwargs):
        nonlocal run_count
        run_count += 1
        kwargs["stdout"].write("invalid peer certificate: UnknownIssuer")
        return SimpleNamespace(returncode=1)

    monkeypatch.setattr(runtime, "_repository_root", lambda: tmp_path)
    monkeypatch.setattr(runtime.subprocess, "run", fake_run)

    with pytest.raises(CodexTransportError) as error:
        _invoke_signed_in_codex(
            codex_bin="/bin/echo",
            prompt=prompt,
            output=claims / "claim.output.json",
            log=claims / "claim.log",
            schema=schema,
            cwd=claims,
            timeout=30,
            state_namespace="test-unknown-issuer",
        )

    assert run_count == 1
    assert error.value.failure_type == CodexTransportFailureType.TLS_CERTIFICATE_UNKNOWN_ISSUER
    assert error.value.raw_diagnostic_token == "UnknownIssuer"


def test_claim_heartbeat_renews_while_caller_is_blocked(monkeypatch) -> None:
    renewal_count = 0

    def renew(*args, **kwargs):
        nonlocal renewal_count
        renewal_count += 1
        return SimpleNamespace(status="renewed", heartbeat_count=renewal_count)

    monkeypatch.setattr(runtime, "renew_ai_review_claim", renew)
    heartbeat = _ClaimLeaseHeartbeat(
        packet_id="packet",
        claim_id="claim",
        owner="primary",
        fencing_token="claim",
        interval_seconds=0.01,
    )

    with heartbeat:
        assert heartbeat._thread.is_alive()
        time.sleep(0.035)

    assert renewal_count >= 3
    assert heartbeat.ownership_lost is False


def test_run50_natural_claim_paths_use_one_canonical_repository_root(
    monkeypatch,
    tmp_path: Path,
) -> None:
    claim_id = "44ef5bbe-2ae7-427e-bf00-ec2c8e8983a1"
    packet_id = "2026-09-01-kr-run-50-a601ddc0620a"
    final_relative = Path(
        "data/ai_review/outbox/"
        f"{packet_id}--daily-review-v3.10--dc747fff8565.json"
    )
    monkeypatch.setattr(runtime, "_repository_root", lambda: tmp_path)

    paths = _paths({"final_output_path": str(final_relative)}, claim_id)
    expected_claims_dir = tmp_path / "data/ai_review/claims"
    expected_schema = expected_claims_dir / (
        f"{final_relative.stem}--{claim_id}.decision-v2-schema.json"
    )

    assert paths["schema"] == expected_schema
    assert paths["schema"].is_absolute()
    assert str(paths["schema"]).count("data/ai_review/claims") == 1

    expected_claims_dir.mkdir(parents=True)
    paths["prompt"].write_text("prompt", encoding="utf-8")
    paths["schema"].write_text("{}", encoding="utf-8")
    paths["temp"].parent.mkdir(parents=True)
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["cwd"] = kwargs["cwd"]
        Path(command[command.index("-o") + 1]).write_text("{}", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(runtime.subprocess, "run", fake_run)
    _invoke_signed_in_codex(
        codex_bin="/bin/echo",
        prompt=paths["prompt"],
        output=paths["temp"],
        log=paths["log"],
        schema=paths["schema"],
        cwd=Path("data/ai_review/claims"),
        timeout=30,
        state_namespace=claim_id,
    )

    command = captured["command"]
    assert isinstance(command, list)
    assert Path(command[command.index("--output-schema") + 1]) == expected_schema
    assert captured["cwd"] == expected_claims_dir
