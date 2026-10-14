"""Exercise the fixed adapter without replacing the real owner verifier."""

from datetime import date

import pytest

from app.services import reviewed_fixture_authority as owner
from app.services.direction_timing_ownership_service import (
    EvidenceDomain,
    OwnedEvidencePacket,
    stage_alias_catalogs,
)
from scripts import reviewed_financial_semantic_adapter_v1 as adapter


OCF_REF = "canonical:fictional:FIC-FIN-01:ocf-current"


def _parent():
    return owner.build_reviewed_owned_fixture(
        "financial:FIC-FIN-01", generation="m12au-test"
    )


def _candidate():
    return {
        "ticker": "FIC-FIN-01",
        "buy_drivers": [
            {"text": "Operating cash flow improved.", "evidence_refs": [OCF_REF]}
        ],
    }


def _supply_parent(monkeypatch, parent):
    def produce(recipe_id, **parameters):
        assert recipe_id == "financial:FIC-FIN-01"
        assert parameters == {"generation": "m12au-test"}
        return parent

    monkeypatch.setattr(adapter, "build_reviewed_owned_fixture", produce)


def _expect_rejected(monkeypatch, parent, error):
    _supply_parent(monkeypatch, parent)

    def unexpected_semantic_call(*args, **kwargs):
        raise AssertionError("Rejected parent reached the semantic checker")

    monkeypatch.setattr(
        adapter, "validate_directional_financial_semantics", unexpected_semantic_call
    )
    with pytest.raises(ValueError, match=f"^{error}$"):
        adapter.validate_m12au_financial_v1(_candidate())


def test_exact_parent_preserves_refs_catalog_order_and_semantic_consumer(monkeypatch):
    parent = _parent()
    before = parent.model_dump_json()
    catalog, _ = stage_alias_catalogs(parent)
    candidate = _candidate()
    calls = []
    semantic = adapter.validate_directional_financial_semantics

    def observe(value, **kwargs):
        calls.append((value, kwargs))
        return semantic(value, **kwargs)

    _supply_parent(monkeypatch, parent)
    monkeypatch.setattr(adapter, "validate_directional_financial_semantics", observe)
    result = adapter.validate_m12au_financial_v1(candidate)

    assert result.valid
    assert result.configured_signal_count == 0
    assert calls == [
        (
            candidate,
            {
                "supplied_refs": tuple(row.ref for row in parent.evidence),
                "allowed_ref_ids": tuple(catalog.by_ref),
                "sector_framework": parent.sector_framework,
            },
        )
    ]
    assert parent.model_dump_json() == before
    assert parent.backend_seal.purpose == "FROZEN_FINANCIAL_SEMANTICS"


@pytest.mark.parametrize(
    "change",
    (
        "statement",
        "source_ref",
        "ref_id",
        "issuer",
        "period",
        "domain",
        "missing_parent_receipt",
        "off_purpose",
        "pid",
        "lifetime",
    ),
)
def test_tampered_parent_is_rejected_at_adapter_before_semantics(change, monkeypatch):
    parent = _parent()
    error = "reviewed_fixture_unissued_revoked_or_changed"
    if change == "issuer":
        parent = parent.model_copy(
            update={
                "source_packet": parent.source_packet.model_copy(
                    update={"ticker": "FIC-FIN-02"}
                )
            }
        )
    elif change == "missing_parent_receipt":
        parent = parent.model_copy(update={"backend_seal": None})
        error = "reviewed_fixture_receipt_required"
    elif change in {"off_purpose", "pid", "lifetime"}:
        key, value = {
            "off_purpose": ("purpose", "FROZEN_CORE_SCHEMA_SEMANTICS"),
            "pid": ("owner_pid", -1),
            "lifetime": ("owner_lifetime", "expired-or-foreign-lifetime"),
        }[change]
        parent = parent.model_copy(
            update={"backend_seal": parent.backend_seal.model_copy(update={key: value})}
        )
        if change == "off_purpose":
            error = "reviewed_fixture_consumer_forbidden"
    else:
        row = next(row for row in parent.evidence if row.ref.ref_id == OCF_REF)
        ref = row.ref
        if change == "domain":
            row = row.model_copy(update={"domain": EvidenceDomain.PRICE_CONTEXT})
        else:
            if change == "period":
                period = ref.financial_context.period.model_copy(
                    update={"end": date(2026, 6, 29)}
                )
                ref = ref.model_copy(
                    update={
                        "financial_context": ref.financial_context.model_copy(
                            update={"period": period}
                        )
                    }
                )
            else:
                ref = ref.model_copy(update={change: "caller-controlled"})
            row = row.model_copy(update={"ref": ref})
        parent = parent.model_copy(
            update={
                "evidence": tuple(
                    row if item.ref.ref_id == OCF_REF else item
                    for item in parent.evidence
                ),
                "source_packet": parent.source_packet.model_copy(
                    update={
                        "evidence": tuple(
                            ref if item.ref_id == OCF_REF else item
                            for item in parent.source_packet.evidence
                        )
                    }
                ),
            }
        )
    _expect_rejected(monkeypatch, parent, error)


@pytest.mark.parametrize(
    "recipe,generation",
    (
        ("financial:FIC-FIN-02", "m12au-test"),
        ("financial:FIC-FIN-01", "m12bi-test"),
    ),
    ids=("other-approved-issuer", "other-approved-generation"),
)
def test_other_valid_parent_does_not_expand_adapter_scope(
    recipe, generation, monkeypatch
):
    parent = owner.build_reviewed_owned_fixture(recipe, generation=generation)
    owner.verify_reviewed_owned_fixture(parent, consumer="FINANCIAL_CONTEXT")
    _expect_rejected(monkeypatch, parent, "m12au_financial_parent_contract_mismatch")


def test_copied_parent_requires_its_still_live_receipt(monkeypatch):
    parent = _parent()
    copied = OwnedEvidencePacket.model_validate_json(parent.model_dump_json())
    _supply_parent(monkeypatch, copied)
    assert adapter.validate_m12au_financial_v1(_candidate()).valid

    owner.revoke_reviewed_fixture(parent)
    _expect_rejected(
        monkeypatch, copied, "reviewed_fixture_unissued_revoked_or_changed"
    )


def test_candidate_cannot_change_issuer_or_supply_owner(monkeypatch):
    def unexpected_producer(*args, **kwargs):
        raise AssertionError("Invalid candidate requested a parent")

    monkeypatch.setattr(adapter, "build_reviewed_owned_fixture", unexpected_producer)
    with pytest.raises(ValueError, match="^m12au_financial_candidate_identity_mismatch$"):
        adapter.validate_m12au_financial_v1({**_candidate(), "ticker": "FIC-FIN-02"})
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        adapter.validate_m12au_financial_v1(_candidate(), parent={})


def test_adapter_does_not_admit_unapproved_configured_extension():
    candidate = {
        "ticker": "FIC-FIN-01",
        "business_reevaluation_down": [
            {
                "text": "Reassess the business later.",
                "evidence_refs": ["m12at:FIC-FIN-01:weaken"],
            }
        ],
    }
    result = adapter.validate_m12au_financial_v1(candidate)
    assert not result.valid
    assert result.invalid_financial_reference_count == 1
    assert "invalid_financial_evidence_reference" in result.errors
    assert result.configured_signal_count == 0
