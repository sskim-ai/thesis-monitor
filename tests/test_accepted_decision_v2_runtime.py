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
    AcceptedV2FundamentalCoreCandidate,
    accepted_v2_fundamental_core_output_schema,
    accepted_v2_fundamental_core_prompt,
    accepted_v2_fundamental_core_ref_catalog_manifest,
    accepted_v2_fundamental_core_sha256,
    accepted_v2_production_batch_schema_repair_prompt,
    accepted_v2_production_prompt,
    accepted_v2_production_repair_prompt,
    accepted_v2_stage2_output_schema,
    accepted_v2_stage2_ref_catalog_manifest,
    build_accepted_v2_production_context,
    validate_accepted_v2_candidate_ownership,
    validate_accepted_v2_fundamental_core,
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
    return AcceptedV2FundamentalCoreCandidate.model_construct(ticker=packet.ticker)


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
        "supporting_evidence_refs": definitions["DriverEvidenceMaturity"][
            "properties"
        ]["supporting_evidence_refs"],
        "contradicting_evidence_refs": definitions["DriverEvidenceMaturity"][
            "properties"
        ]["contradicting_evidence_refs"],
    }
    return {
        name: tuple(field["items"]["enum"])
        for name, field in fields.items()
    }


def _fundamental_core(ticker: str, ref_id: str) -> AcceptedV2FundamentalCoreCandidate:
    claim = EvidenceClaim(
        text="검증된 사업 근거가 중립 판단을 지지합니다.",
        evidence_refs=(ref_id,),
    )
    return AcceptedV2FundamentalCoreCandidate(
        ticker=ticker,
        decision="HOLD",
        directional_balance=DirectionalBalance(buy=5, sell=5),
        buy_drivers=(claim,),
        sell_drivers=(claim,),
        balance_summary="검증된 근거를 균형 있게 반영했습니다.",
        confidence="MEDIUM",
        decisive_reason=claim,
        holder_axis=HolderDecisionAxis(stance="HOLDABLE", reason=claim),
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
        "$.$defs.DriverEvidenceMaturity.properties.contradicting_evidence_refs",
        "$.$defs.DriverEvidenceMaturity.properties.supporting_evidence_refs",
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
    )
    assert f'"ref_catalog_hash":"{corz_manifest["ref_catalog_hash"]}"' in prompt
    assert "Evidence refs are exact opaque identifiers." in prompt
    assert "Never edit, append, shorten, infer, synthesize, guess, or repair" in prompt


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
    assert "Do not state or infer ROIC" in prompt
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

    assert "never later than assessment_date" in prompt
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
            "candidates.0.driver_maturity.2:value_error:maturity_reference_polarity_overlap",
        ),
    )

    assert "BOUNDED_BATCH_SCHEMA_REPAIR" in prompt
    assert "maturity_reference_polarity_overlap" in prompt
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
