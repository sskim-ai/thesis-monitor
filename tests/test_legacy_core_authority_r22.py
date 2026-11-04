"""Offline projection integrity only; fixtures are not independent real owners."""
from copy import deepcopy

import pytest

from app.services import accepted_decision_v2_runtime_service as runtime
from app.services import legacy_context_authority as authority
from app.services.direction_timing_ownership_service import (
    EvidenceDomain,
    build_owned_evidence_packet,
    financial_decision_context_for_owned,
    stage_alias_catalogs,
)
from tests.test_core_input_source_isolation_r21 import (
    _daily_stock,
    _financial_stock,
    _isolated_data as _isolated_data,
    _native,
    _packet,
)


def _consumer(name, context):
    if name == "stage2_prompt":
        return runtime.accepted_v2_production_prompt(context, fundamental_cores=())
    if name == "materialize":
        return runtime.materialize_accepted_v2_stage2_output(context, {})
    if name == "output_validator":
        return runtime.validate_accepted_v2_production_output(context, None)
    return getattr(runtime, name)(context)


CONSUMERS = (
    "accepted_v2_fundamental_core_prompt",
    "accepted_v2_fundamental_core_ref_catalog",
    "accepted_v2_fundamental_core_ref_catalog_manifest",
    "accepted_v2_fundamental_core_output_schema",
    "accepted_v2_fundamental_core_batch_identity_manifest",
    "accepted_v2_stage2_ref_catalog_manifest",
    "accepted_v2_stage2_output_schema",
    "stage2_prompt", "materialize", "output_validator",
)


@pytest.mark.parametrize("consumer", CONSUMERS)
def test_public_context_ref_expansion_rejected_before_consumption(consumer):
    view = _native(_packet(_daily_stock()))
    raw = view.context.model_dump(mode="json")
    event_refs = [row.ref_id for row in view.evidence.evidence
                  if row.ref_id.startswith("canonical:event:")]
    assert event_refs
    assert not set(event_refs) & set(raw["evidence_ownership"][0]["core_ref_ids"])
    raw["evidence_ownership"][0]["core_ref_ids"] += event_refs
    forged = runtime.AcceptedV2ProductionContext.model_validate(raw)
    with pytest.raises(ValueError, match="legacy_context_backend_seal_mismatch"):
        _consumer(consumer, forged)


@pytest.mark.parametrize("mode", ("clone", "deep_clone", "serialize", "construct"))
def test_altered_financial_context_cannot_reuse_issued_seal(mode):
    context = _native(_packet(_financial_stock())).context
    if mode in {"clone", "deep_clone"}:
        forged = context.model_copy(update={"claim_id": "different-invocation"},
                                    deep=mode == "deep_clone")
    else:
        raw = context.model_dump(mode="json")
        raw["claim_id"] = "different-invocation"
        if mode == "serialize":
            forged = runtime.AcceptedV2ProductionContext.model_validate(raw)
        else:
            forged = runtime.AcceptedV2ProductionContext.model_construct(**raw)
    with pytest.raises(ValueError, match="legacy_context_backend_seal"):
        runtime.accepted_v2_fundamental_core_prompt(forged)


@pytest.mark.parametrize("ticker", ("UNSEEN_US_R22", "UNSEEN_KR_R22", "UNSEEN_ADS_R22"))
def test_unchanged_context_roundtrip_and_idempotent_lookup(ticker):
    stock = _financial_stock()
    stock["ticker"] = ticker
    view = _native(_packet(stock))
    restored = runtime.AcceptedV2ProductionContext.model_validate_json(
        view.context.model_dump_json())
    assert runtime.accepted_v2_fundamental_core_prompt(restored) == view.prompt
    assert runtime.accepted_v2_fundamental_core_prompt(restored) == view.prompt
    assert runtime.accepted_v2_fundamental_core_ref_catalog(restored)


@pytest.mark.parametrize("field", ("owner_lifetime", "payload_sha256", "signature"))
def test_public_seal_reconstruction_cannot_mint_authority(field):
    raw = _native(_packet(_financial_stock())).context.model_dump(mode="json")
    raw["backend_seal"][field] = "0" * 64
    forged = runtime.AcceptedV2ProductionContext.model_validate(raw)
    with pytest.raises(ValueError, match="legacy_context_backend_seal_mismatch"):
        runtime.accepted_v2_fundamental_core_prompt(forged)


def test_missing_seal_and_different_parent_fail_closed(monkeypatch):
    context = _native(_packet(_financial_stock())).context
    with pytest.raises(ValueError, match="legacy_context_backend_seal_required"):
        runtime.accepted_v2_fundamental_core_prompt(
            context.model_copy(update={"backend_seal": None}))
    monkeypatch.setattr(authority, "_SIGNING_KEY", b"different-offline-parent-key")
    with pytest.raises(ValueError, match="legacy_context_backend_seal_mismatch"):
        runtime.accepted_v2_fundamental_core_prompt(context)


@pytest.mark.parametrize("consumer", (stage_alias_catalogs, financial_decision_context_for_owned))
def test_alias_reclassification_cannot_expand_sealed_owned_projection(consumer):
    stock = _daily_stock()
    view = _native(_packet(stock))
    owned = build_owned_evidence_packet(view.evidence, stock=stock)
    expanded = tuple(row.model_copy(update={"domain": EvidenceDomain.BUSINESS_CURRENT})
                     if row.ref.ref_id.startswith("canonical:event:") else row
                     for row in owned.evidence)
    assert expanded != owned.evidence
    with pytest.raises(ValueError, match="legacy_context_backend_seal_mismatch"):
        consumer(owned.model_copy(update={"evidence": expanded}))


@pytest.mark.parametrize("scopes", (["ARCHIVE_ONLY"], ["MARKET_RENDERER"], [],
                                   ["UNDECLARED_CONSUMER"], ["STOCK_V2", 17]))
def test_financial_primary_must_belong_to_current_consumer(scopes):
    stock = _financial_stock()
    view = _native(_packet(stock))
    supplied_stock = deepcopy(stock)
    supplied_stock["fact_catalog"][0]["consumer_scopes"] = scopes
    with pytest.raises(ValueError, match="fundamental_financial_consumer_membership_required"):
        build_owned_evidence_packet(view.evidence, stock=supplied_stock)


def test_financial_source_is_preserved_for_authorized_synthetic_scope():
    stock = _financial_stock()
    stock["fact_catalog"][0]["consumer_scopes"] = ["STOCK_V2"]
    view = _native(_packet(stock))
    owned = build_owned_evidence_packet(view.evidence, stock=stock)
    core, _ = stage_alias_catalogs(owned)
    assert core
    assert "246813579.25" in view.prompt


@pytest.mark.parametrize("availability", ("available", "trusted", {"ready": True}))
def test_unknown_price_availability_enum_rejected_before_prompt(availability):
    stock = _financial_stock()
    stock["current_price_context"] = {"availability": availability, "current_price": 987.654321}
    with pytest.raises(ValueError, match="fundamental_price_availability_invalid"):
        _native(_packet(stock))
