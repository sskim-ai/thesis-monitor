"""Exact TEST_ONLY expectation recipe; never accepted source or Core authority."""
import pytest

from app.services import fixture_context_authority as authority
from app.services.cross_market_decision_engine_service import (
    DecisionEvidencePacket, EvidenceCategory,
)
from app.services.direction_timing_ownership_service import (
    EvidenceDomain, OwnedEvidencePacket, OwnedEvidenceRef, stage_alias_catalogs,
    validate_directional_core_ownership,
)
from app.services.legacy_context_authority import _seal_built_context, verify_legacy_context
from app.services.market_expectation_evidence_service import (
    MarketExpectationEvidenceView, MarketExpectationStructuredBasis,
    attach_market_expectation_evidence_view, build_market_expectation_evidence_view,
    validate_market_expectation_candidate,
)
from app.services.owned_evidence_derivative import restrict_owned_evidence
from app.services.structured_autonomy_alias_service import build_evidence_alias_catalog
from tests.test_market_expectation_evidence_service import _fixture_view, _ref


def _inputs(kind="conditional", *, issued=True):
    refs = (
        _ref("fixture:expectation", category=EvidenceCategory.EXPECTATIONS, label="market-expectation"),
        _ref("fixture:dependency", category=EvidenceCategory.UNKNOWN, label="unresolved-condition"),
        _ref("fixture:operating", category=EvidenceCategory.EARNINGS, label="operating-evidence"),
    )
    packet = DecisionEvidencePacket(packet_id="fixture:market-expectation", ticker="EXP-FIXTURE",
        company_name="Expectation Fixture", market="us", assessment_date="2026-09-12",
        horizon="12m", evidence=refs, prohibited_claims=(), evidence_sha256="fixture-market-expectation-sha")
    domains = (EvidenceDomain.MARKET_EXPECTATIONS, EvidenceDomain.DATA_QUALITY_LIMIT,
               EvidenceDomain.EARNINGS_FINANCIAL_CURRENT)
    owned = OwnedEvidencePacket(source_packet=packet, evidence=tuple(
        OwnedEvidenceRef(ref=ref, domain=domain) for ref, domain in zip(refs, domains, strict=True)))
    bases = ()
    if kind == "conditional":
        bases = (MarketExpectationStructuredBasis(expectation_ref=refs[0].ref_id,
                                                  dependency_refs=(refs[1].ref_id,)),)
    elif kind == "independent":
        bases = (MarketExpectationStructuredBasis(expectation_ref=refs[0].ref_id,
            independently_observed=True, independence_basis_refs=(refs[2].ref_id,)),)
    if issued:
        owned = authority.issue_market_expectation_fixture(owned, basis_kind=kind)
    return owned, build_evidence_alias_catalog(packet), bases


@pytest.mark.parametrize("kind", ("conditional", "independent", "unknown"))
def test_reviewed_recipe_semantic_pass_is_explicitly_test_only(kind):
    view, _, context, _ = _fixture_view(basis_kind=kind)
    restored = MarketExpectationEvidenceView.model_validate_json(view.model_dump_json())
    result = validate_market_expectation_candidate({"ticker": view.ticker}, restored)
    assert result["status"] == "PASS"
    assert result["validation_scope"] == "TEST_ONLY_MARKET_EXPECTATION_SEMANTICS"
    assert result["accepted_model_judgment"] is False
    assert result["production_eligible"] is False
    attached = attach_market_expectation_evidence_view(context, restored)
    assert attached["test_only_provenance"] == result["test_only_provenance"]
    assert attached["market_expectation_evidence_view"]["production_eligible"] is False


def test_none_and_unapproved_payload_do_not_gain_fixture_authority():
    owned, catalog, bases = _inputs(issued=False)
    with pytest.raises(ValueError, match="test_only_fixture_not_production_authority"):
        build_market_expectation_evidence_view(owned, catalog, structured_bases=bases)
    changed = owned.model_copy(update={"source_packet": owned.source_packet.model_copy(
        update={"ticker": "REAL_ISSUER"})})
    with pytest.raises(ValueError, match="fixture_context_unapproved_payload"):
        authority.issue_market_expectation_fixture(changed, basis_kind="conditional")
    with pytest.raises(ValueError, match="fixture_context_unapproved_recipe"):
        authority.issue_market_expectation_fixture(owned, basis_kind="production")


@pytest.mark.parametrize("target", ("payload", "catalog", "basis", "signature", "lifetime"))
def test_receipt_cannot_authorize_changed_recipe(target):
    owned, catalog, bases = _inputs()
    if target == "payload":
        owned = owned.model_copy(update={"sector_framework": "changed"})
    elif target == "catalog":
        catalog = catalog.model_copy(update={"alias_map_sha256": "0" * 64})
    elif target == "basis":
        bases = ()
    else:
        field = "signature" if target == "signature" else "owner_lifetime"
        owned = owned.model_copy(update={"backend_seal": owned.backend_seal.model_copy(
            update={field: "0" * 64})})
    with pytest.raises(ValueError, match="fixture_context_"):
        build_market_expectation_evidence_view(owned, catalog, structured_bases=bases)


def test_exact_receipt_wrong_purpose_pid_and_revocation_fail(monkeypatch):
    owned, catalog, bases = _inputs()
    view = build_market_expectation_evidence_view(owned, catalog, structured_bases=bases)
    with pytest.raises(ValueError, match="fixture_context_consumer_forbidden"):
        authority.verify_market_expectation_fixture(owned, catalog, bases, consumer="CORE")
    with monkeypatch.context() as patch:
        patch.setattr(authority, "_PID", -1)
        with pytest.raises(ValueError, match="fixture_context_owner_process_mismatch"):
            view.model_context()
        with pytest.raises(ValueError, match="fixture_context_owner_process_mismatch"):
            authority.issue_market_expectation_fixture(_inputs(issued=False)[0], basis_kind="conditional")
    authority.revoke_market_expectation_fixture(owned)
    for consume in (lambda: view.model_context(),
                    lambda: build_market_expectation_evidence_view(owned, catalog, structured_bases=bases)):
        with pytest.raises(ValueError, match="fixture_context_unissued_revoked_or_changed"):
            consume()


@pytest.mark.parametrize("strip", (False, True))
def test_default_core_signer_and_derivative_reject_even_stripped_fixture(strip):
    owned, _, _ = _inputs()
    if strip:
        owned = owned.model_copy(update={"backend_seal": None})
    operations = (
        lambda: verify_legacy_context(owned, scope="OWNED_EVIDENCE"),
        lambda: _seal_built_context(owned, scope="OWNED_EVIDENCE"),
        lambda: owned.core_refs,
        lambda: stage_alias_catalogs(owned),
        lambda: validate_directional_core_ownership(owned, None),
        lambda: restrict_owned_evidence(owned, retained_refs=("fixture:operating",),
                                       purpose="REQUEST_REF_RESTRICTION"),
    )
    for consume in operations:
        with pytest.raises(ValueError, match="test_only_fixture_not_production_authority"):
            consume()


def test_stripped_or_mutated_semantic_view_cannot_be_promoted():
    view, _, _, _ = _fixture_view(basis_kind="independent")
    raw = view.model_dump(mode="json")
    raw.pop("test_only_provenance")
    raw["contract"] = "market-expectation-evidence-view-v1"
    stripped = MarketExpectationEvidenceView.model_validate(raw)
    with pytest.raises(ValueError, match="fixture_context_provenance_required"):
        validate_market_expectation_candidate({"ticker": stripped.ticker}, stripped)
    changed = view.model_copy(update={"ticker": "REAL_ISSUER"})
    with pytest.raises(ValueError, match="fixture_context_semantic_projection_mismatch"):
        changed.model_context()
    with pytest.raises(ValueError, match="test_only_fixture_not_production_authority"):
        _seal_built_context(view)


def test_accepted_output_rejects_fixture_before_output_consumption():
    from app.services.accepted_decision_v2_runtime_service import (
        AcceptedV2EvidenceOwnership, AcceptedV2ProductionContext, validate_accepted_v2_production_output,
    )
    from app.services.expectation_valuation_interaction_service import interaction_from_packet

    owned, _, _ = _inputs()
    packet = owned.source_packet
    context = AcceptedV2ProductionContext(packet_id=packet.packet_id, claim_id="fixture-claim",
        market=packet.market, assessment_date=packet.assessment_date, source_packet_sha256="0" * 64,
        selected_subjects=(packet.ticker,), evidence_packets=(packet,),
        evidence_ownership=(AcceptedV2EvidenceOwnership(ticker=packet.ticker,
            core_ref_ids=("fixture:operating",), timing_ref_ids=(),
            expectation_valuation=interaction_from_packet(packet)),), prepared_at="2026-09-12T00:00:00+00:00")
    with pytest.raises(ValueError, match="test_only_fixture_not_production_authority"):
        validate_accepted_v2_production_output(context, None)


def test_normal_view_serialization_keeps_legacy_shape():
    from app.services.market_expectation_evidence_service import MarketExpectationEvidenceItem

    view = MarketExpectationEvidenceView(ticker="NORMAL", items=(MarketExpectationEvidenceItem(
        alias="E01", canonical_ref="canonical:normal", source_ref="stock.fact_catalog.normal",
        role="NOT_MARKET_EXPECTATION", reason="NOT_MARKET_EXPECTATION",
        material_anchor_eligible=True, dominant_evidence_eligible=True),))
    assert set(view.model_dump(mode="json")) == {"contract", "ticker", "items"}
    assert set(view.model_context()) == {"contract", "expectations"}
