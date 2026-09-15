from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from enum import StrEnum

from app.services.business_delta_evidence_service import (
    BusinessDeltaEvidenceView,
    build_business_delta_evidence_view,
    validate_business_delta_candidate,
)
from app.services.configured_signal_evidence_service import (
    ConfiguredSignalEvidenceView,
    build_configured_signal_evidence_view,
    validate_configured_signal_field_ownership,
)
from app.services.cross_market_decision_engine_service import (
    DecisionEvidenceRef,
    FrozenModel,
)
from app.services.direction_timing_ownership_service import (
    OwnedEvidencePacket,
    financial_decision_context_for_owned,
)
from app.services.directional_financial_context_service import (
    FinancialSemanticValidation,
    QtdYtdConflictValidation,
    compact_financial_decision_context,
    validate_directional_financial_semantics,
    validate_qtd_ytd_conflict_semantics,
)
from app.services.market_expectation_evidence_service import (
    MarketExpectationEvidenceView,
    build_market_expectation_evidence_view,
    market_expectation_evidence_view_sha256,
    validate_market_expectation_candidate,
)
from app.services.structured_autonomy_alias_service import EvidenceAliasCatalog
from app.services.working_capital_checkpoint_binding_service import (
    WorkingCapitalCheckpointBindingView,
    build_working_capital_checkpoint_binding_view,
    validate_working_capital_checkpoint_bindings,
)


CONTRACT_VERSION = "directional-core-semantic-audit-v1"
ADAPTER_CONTRACT_VERSION = "owned-directional-core-semantic-adapter-v1"


class SemanticApplicability(StrEnum):
    APPLICABLE = "APPLICABLE"
    NOT_APPLICABLE_BY_LIFECYCLE = "NOT_APPLICABLE_BY_LIFECYCLE"
    APPLICABLE_WITH_EMPTY_VIEW = "APPLICABLE_WITH_EMPTY_VIEW"
    UNSUPPORTED_INPUT_ERROR = "UNSUPPORTED_INPUT_ERROR"


class SemanticServiceProvenance(FrozenModel):
    family: str
    applicability: SemanticApplicability
    canonical_module: str
    canonical_functions: tuple[str, ...]
    service_contracts: tuple[str, ...]
    called: bool
    hard_decision_source: str


class DirectionalCoreSemanticAudit(FrozenModel):
    contract: str = CONTRACT_VERSION
    adapter_contract: str = ADAPTER_CONTRACT_VERSION
    ticker: str
    lifecycle_mode: str
    applicability: dict[str, SemanticApplicability]
    financial_semantics: FinancialSemanticValidation
    qtd_ytd_semantics: QtdYtdConflictValidation
    configured_signal_semantics: dict[str, object]
    working_capital_semantics: dict[str, object]
    business_delta_semantics: dict[str, object]
    market_expectation_semantics: dict[str, object]
    semantic_service_provenance: tuple[SemanticServiceProvenance, ...]
    semantic_service_identity_sha256: str
    hard_errors: tuple[str, ...]
    valid: bool
    status: str


def _candidate_mapping(candidate: object) -> Mapping[str, object]:
    value = (
        candidate.model_dump(mode="json")
        if hasattr(candidate, "model_dump")
        else candidate
    )
    if not isinstance(value, Mapping):
        raise TypeError("directional_core_candidate_mapping_required")
    return value


def _skipped_result(
    *,
    family: str,
    applicability: SemanticApplicability,
) -> dict[str, object]:
    return {
        "contract": CONTRACT_VERSION,
        "family": family,
        "applicability": applicability.value,
        "errors": [],
        "valid": applicability
        != SemanticApplicability.UNSUPPORTED_INPUT_ERROR,
        "status": (
            "FAIL"
            if applicability == SemanticApplicability.UNSUPPORTED_INPUT_ERROR
            else applicability.value
        ),
    }


def _result_errors(result: object) -> tuple[str, ...]:
    if hasattr(result, "errors"):
        return tuple(str(error) for error in result.errors)
    if isinstance(result, Mapping):
        errors = result.get("errors", ())
        if isinstance(errors, Sequence) and not isinstance(errors, (str, bytes)):
            return tuple(str(error) for error in errors)
    return ()


def _provenance(
    applicability: Mapping[str, SemanticApplicability],
) -> tuple[SemanticServiceProvenance, ...]:
    definitions = (
        (
            "financial_semantics",
            "app.services.directional_financial_context_service",
            ("validate_directional_financial_semantics",),
            ("directional-financial-semantic-validator-v1",),
        ),
        (
            "qtd_ytd_semantics",
            "app.services.directional_financial_context_service",
            ("validate_qtd_ytd_conflict_semantics",),
            ("directional-financial-qtd-ytd-validator-v1",),
        ),
        (
            "configured_signal_semantics",
            "app.services.configured_signal_evidence_service",
            (
                "build_configured_signal_evidence_view",
                "validate_configured_signal_field_ownership",
            ),
            (
                "configured-signal-evidence-view-v1",
                "configured-signal-field-validator-v1",
            ),
        ),
        (
            "working_capital_semantics",
            "app.services.working_capital_checkpoint_binding_service",
            (
                "build_working_capital_checkpoint_binding_view",
                "validate_working_capital_checkpoint_bindings",
            ),
            (
                "working-capital-checkpoint-binding-view-v1",
                "working-capital-checkpoint-typed-ref-binding-v1",
            ),
        ),
        (
            "business_delta_semantics",
            "app.services.business_delta_evidence_service",
            (
                "build_business_delta_evidence_view",
                "validate_business_delta_candidate",
            ),
            (
                "business-delta-evidence-capability-v1",
                "post-model-business-delta-validator-v2",
            ),
        ),
        (
            "market_expectation_semantics",
            "app.services.market_expectation_evidence_service",
            (
                "build_market_expectation_evidence_view",
                "validate_market_expectation_candidate",
            ),
            (
                "market-expectation-evidence-view-v1",
                "post-model-market-expectation-validator-v1",
            ),
        ),
    )
    return tuple(
        SemanticServiceProvenance(
            family=family,
            applicability=applicability[family],
            canonical_module=module,
            canonical_functions=functions,
            service_contracts=contracts,
            called=applicability[family]
            in {
                SemanticApplicability.APPLICABLE,
                SemanticApplicability.APPLICABLE_WITH_EMPTY_VIEW,
            },
            hard_decision_source=(
                "CANONICAL_SERVICE"
                if applicability[family]
                in {
                    SemanticApplicability.APPLICABLE,
                    SemanticApplicability.APPLICABLE_WITH_EMPTY_VIEW,
                }
                else applicability[family].value
            ),
        )
        for family, module, functions, contracts in definitions
    )


def audit_directional_core_semantics(
    candidate: object,
    *,
    supplied_refs: Sequence[DecisionEvidenceRef],
    allowed_ref_ids: Sequence[str],
    required_qtd_ytd_ref_ids: Sequence[str],
    sector_framework: object,
    configured_signal_view: ConfiguredSignalEvidenceView,
    working_capital_view: WorkingCapitalCheckpointBindingView,
    business_delta_view: BusinessDeltaEvidenceView | None,
    market_expectation_view: MarketExpectationEvidenceView | None,
    applicability: Mapping[str, SemanticApplicability],
    lifecycle_mode: str,
) -> DirectionalCoreSemanticAudit:
    """Aggregate canonical semantic services without re-deriving their rules."""

    payload = _candidate_mapping(candidate)
    ticker = str(payload.get("ticker") or "")
    required_families = {
        "financial_semantics",
        "qtd_ytd_semantics",
        "configured_signal_semantics",
        "working_capital_semantics",
        "business_delta_semantics",
        "market_expectation_semantics",
    }
    if set(applicability) != required_families:
        raise ValueError("directional_core_semantic_applicability_matrix_incomplete")

    financial = validate_directional_financial_semantics(
        payload,
        supplied_refs=supplied_refs,
        allowed_ref_ids=allowed_ref_ids,
        sector_framework=sector_framework,
    )
    qtd_ytd = validate_qtd_ytd_conflict_semantics(
        payload,
        supplied_refs=supplied_refs,
        required_ref_ids=required_qtd_ytd_ref_ids,
    )
    configured = validate_configured_signal_field_ownership(
        payload,
        configured_signal_view,
    ).model_dump(mode="json")
    working_capital = validate_working_capital_checkpoint_bindings(
        payload,
        working_capital_view,
    )

    business_applicability = applicability["business_delta_semantics"]
    if business_applicability in {
        SemanticApplicability.APPLICABLE,
        SemanticApplicability.APPLICABLE_WITH_EMPTY_VIEW,
    }:
        if business_delta_view is None:
            business_delta = _skipped_result(
                family="business_delta_semantics",
                applicability=SemanticApplicability.UNSUPPORTED_INPUT_ERROR,
            )
            business_delta["errors"] = ["CANONICAL_BUSINESS_DELTA_VIEW_REQUIRED"]
        else:
            business_delta = validate_business_delta_candidate(
                payload,
                business_delta_view,
            )
    else:
        business_delta = _skipped_result(
            family="business_delta_semantics",
            applicability=business_applicability,
        )

    expectation_applicability = applicability["market_expectation_semantics"]
    if expectation_applicability in {
        SemanticApplicability.APPLICABLE,
        SemanticApplicability.APPLICABLE_WITH_EMPTY_VIEW,
    }:
        if market_expectation_view is None:
            market_expectation = _skipped_result(
                family="market_expectation_semantics",
                applicability=SemanticApplicability.UNSUPPORTED_INPUT_ERROR,
            )
            market_expectation["errors"] = [
                "CANONICAL_MARKET_EXPECTATION_VIEW_REQUIRED"
            ]
        else:
            market_expectation = validate_market_expectation_candidate(
                payload,
                market_expectation_view,
                pre_model_view_sha256=market_expectation_evidence_view_sha256(
                    market_expectation_view
                ),
            )
    else:
        market_expectation = _skipped_result(
            family="market_expectation_semantics",
            applicability=expectation_applicability,
        )

    results: tuple[object, ...] = (
        financial,
        qtd_ytd,
        configured,
        working_capital,
        business_delta,
        market_expectation,
    )
    unsupported = tuple(
        f"unsupported_semantic_input:{family}"
        for family, state in applicability.items()
        if state == SemanticApplicability.UNSUPPORTED_INPUT_ERROR
    )
    hard_errors = tuple(
        dict.fromkeys(
            error
            for error in (
                *(error for result in results for error in _result_errors(result)),
                *unsupported,
            )
        )
    )
    provenance = _provenance(applicability)
    identity = hashlib.sha256(
        json.dumps(
            [row.model_dump(mode="json") for row in provenance],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    return DirectionalCoreSemanticAudit(
        ticker=ticker,
        lifecycle_mode=lifecycle_mode,
        applicability=dict(applicability),
        financial_semantics=financial,
        qtd_ytd_semantics=qtd_ytd,
        configured_signal_semantics=configured,
        working_capital_semantics=working_capital,
        business_delta_semantics=business_delta,
        market_expectation_semantics=market_expectation,
        semantic_service_provenance=provenance,
        semantic_service_identity_sha256=identity,
        hard_errors=hard_errors,
        valid=not hard_errors,
        status="PASS" if not hard_errors else "FAIL",
    )


def audit_owned_directional_core_semantics(
    candidate: object,
    *,
    owned: OwnedEvidencePacket,
    catalog: EvidenceAliasCatalog,
    lifecycle_mode: str,
    include_working_capital: bool = True,
    include_business_delta: bool = True,
    include_market_expectation: bool = True,
) -> DirectionalCoreSemanticAudit:
    """Adapt owned evidence into canonical views, then run the shared audit."""

    payload = _candidate_mapping(candidate)
    ticker = str(payload.get("ticker") or "")
    packet = owned.source_packet
    if ticker != packet.ticker or catalog.ticker != packet.ticker:
        raise ValueError("directional_core_semantic_owner_ticker_mismatch")
    if catalog.generation != packet.packet_id:
        raise ValueError("directional_core_semantic_catalog_generation_mismatch")

    supplied_refs = tuple(row.ref for row in owned.evidence)
    financial_context = financial_decision_context_for_owned(owned)
    selected_financial_refs = (
        tuple(item.evidence_id for item in financial_context.evidence_items)
        if financial_context is not None
        else ()
    )
    aliases_by_ref = {
        entry.canonical_ref: entry.alias for entry in catalog.entries
    }
    compact_financial = compact_financial_decision_context(
        financial_context,
        aliases_by_ref=aliases_by_ref,
    )
    checkpoint_context: dict[str, object] = {}
    if compact_financial is not None:
        checkpoint_context["financial_decision_context"] = compact_financial
    working_capital_view = (
        build_working_capital_checkpoint_binding_view(
            ticker=ticker,
            context=checkpoint_context,
            alias_to_canonical_ref={
                entry.alias: entry.canonical_ref for entry in catalog.entries
            },
        )
        if include_working_capital
        else WorkingCapitalCheckpointBindingView(ticker=ticker)
    )
    configured_signal_view = build_configured_signal_evidence_view(
        ticker=ticker,
        supplied_refs=supplied_refs,
    )
    business_delta_view = (
        build_business_delta_evidence_view(owned, catalog)
        if include_business_delta
        else None
    )
    market_expectation_view = (
        build_market_expectation_evidence_view(owned, catalog)
        if include_market_expectation
        else None
    )
    financial_refs = tuple(
        ref for ref in supplied_refs if ref.financial_context is not None
    )
    applicability = {
        "financial_semantics": (
            SemanticApplicability.APPLICABLE
            if financial_refs
            else SemanticApplicability.APPLICABLE_WITH_EMPTY_VIEW
        ),
        "qtd_ytd_semantics": (
            SemanticApplicability.APPLICABLE
            if selected_financial_refs
            else SemanticApplicability.APPLICABLE_WITH_EMPTY_VIEW
        ),
        "configured_signal_semantics": (
            SemanticApplicability.APPLICABLE
            if configured_signal_view.items
            else SemanticApplicability.APPLICABLE_WITH_EMPTY_VIEW
        ),
        "working_capital_semantics": (
            SemanticApplicability.APPLICABLE
            if working_capital_view.selected_working_capital_items
            else SemanticApplicability.APPLICABLE_WITH_EMPTY_VIEW
        ),
        "business_delta_semantics": (
            SemanticApplicability.APPLICABLE
            if include_business_delta
            else SemanticApplicability.NOT_APPLICABLE_BY_LIFECYCLE
        ),
        "market_expectation_semantics": (
            SemanticApplicability.NOT_APPLICABLE_BY_LIFECYCLE
            if not include_market_expectation
            else SemanticApplicability.APPLICABLE
            if market_expectation_view is not None
            and market_expectation_view.expectation_items
            else SemanticApplicability.APPLICABLE_WITH_EMPTY_VIEW
        ),
    }
    return audit_directional_core_semantics(
        payload,
        supplied_refs=supplied_refs,
        allowed_ref_ids=tuple(catalog.by_ref),
        required_qtd_ytd_ref_ids=selected_financial_refs,
        sector_framework=owned.sector_framework,
        configured_signal_view=configured_signal_view,
        working_capital_view=working_capital_view,
        business_delta_view=business_delta_view,
        market_expectation_view=market_expectation_view,
        applicability=applicability,
        lifecycle_mode=lifecycle_mode,
    )
