"""Finite fixture composition gates; no real/current economic grants."""
from dataclasses import asdict, replace
import pickle
import subprocess
import sys

import pytest

from app.services import reviewed_configured_composition as owner
from app.services.direction_timing_ownership_service import stage_alias_catalogs
from app.services.reviewed_fixture_authority import (
    build_reviewed_owned_fixture,
    revoke_reviewed_fixture,
)
from scripts import configured_signal_field_ownership_m12at as historical
from scripts import reviewed_configured_semantic_adapter_v1 as adapter


def child():
    return adapter.m12au_composition_v1()


def candidate(ref, field="business_reevaluation_down"):
    row = {"text": "Prospective condition only", "evidence_refs": [ref]}
    return {"ticker": "FIC-FIN-01", field: row if field == "risk_context" else [row]}


@pytest.mark.parametrize("subject,generation,consumer", [
    ("FIC-FIN-01", "m12au-test", owner.M12AU_CONSUMER),
    *[(f"FIC-FIN-{i:02d}", "m12at-deterministic-preflight", owner.SCHEMA_CONSUMER)
        for i in range(1, 5)],
])
def test_exact_original_occurrences_and_first_class_parent(subject, generation, consumer):
    parent = build_reviewed_owned_fixture("financial:" + subject, generation=generation)
    before = parent.model_dump_json()
    catalog_before = stage_alias_catalogs(parent)[0].model_dump_json()
    rows = historical._fictional_configured_refs(subject, generation)
    result = owner.issue_reviewed_configured_composition(parent, rows=rows,
        recipe_id=generation + ":" + subject, consumer=consumer)
    recipe = owner.verify_reviewed_configured_composition(result, consumer=consumer)
    assert result.parent.model_dump_json() == before
    assert result.configured_rows == rows
    assert parent.model_dump_json() == before
    assert stage_alias_catalogs(parent)[0].model_dump_json() == catalog_before
    assert recipe["parent_cutoff"] == "2026-09-09"
    assert recipe["definition_as_of"] == "2026-09-12"
    assert result.production_eligible is False
    assert recipe["allowed_uses"] == ["REEVALUATION", "RISK", "CONDITION"]
    recipe["configured_rows"].clear()
    assert len(owner.verify_reviewed_configured_composition(result, consumer=consumer)["configured_rows"]) == 3


def test_recipe_lookup_mutation_never_changes_backend_authority():
    current = child()
    changed = owner._recipes()[current.recipe_id]
    changed["consumers"].append("CORE_PROMPT")
    changed["configured_rows"][0]["statement"] = "Caller current fact"
    _, binding_copy = owner._binding(current.parent, current.configured_rows,
        current.recipe_id, current.consumer)
    binding_copy["consumers"].append("CORE_PROMPT")
    with pytest.raises(ValueError, match="consumer_forbidden"):
        owner.build_reviewed_configured_composition(current.parent,
            recipe_id=current.recipe_id, consumer="CORE_PROMPT")
    rows = (current.configured_rows[0].model_copy(update={"statement": "Caller current fact"}),
        *current.configured_rows[1:])
    with pytest.raises(ValueError, match="exact_occurrences_required"):
        owner.issue_reviewed_configured_composition(current.parent, rows=rows,
            recipe_id=current.recipe_id, consumer=current.consumer)
    assert child() is current


@pytest.mark.parametrize("change", ["extra", "missing", "order", "subject", "generation",
    "period", "statement", "source_ref", "value", "unit", "logical_condition"])
def test_exact_occurrence_gate_precedes_issuance(change):
    current = child()
    rows = current.configured_rows
    if change == "extra":
        rows += rows[:1]
    elif change == "missing":
        rows = rows[:-1]
    elif change == "order":
        rows = tuple(reversed(rows))
    else:
        field, value = {
            "subject": ("ref_id", "m12at:OTHER:strengthen"),
            "generation": ("logical_condition", rows[0].logical_condition.model_copy(update={"generation_id": "other"})),
            "period": ("as_of", "2026-09-09"), "statement": ("statement", "Currently fulfilled"),
            "source_ref": ("source_ref", "stock.fact_catalog.authorized"),
            "value": ("value", 987.654321), "unit": ("unit", "KRW"),
            "logical_condition": ("logical_condition", None),
        }[change]
        rows = (rows[0].model_copy(update={field: value}), *rows[1:])
    before = set(owner._ISSUED)
    with pytest.raises(ValueError, match="exact_occurrences_required"):
        owner.issue_reviewed_configured_composition(current.parent, rows=rows,
            recipe_id=current.recipe_id, consumer=current.consumer)
    assert set(owner._ISSUED) == before


@pytest.mark.parametrize("change", ["detached", "wrong_parent", "generation", "cutoff", "basis", "recipe", "consumer"])
def test_parent_and_invocation_binding(change):
    current = child()
    parent, recipe, consumer = current.parent, current.recipe_id, current.consumer
    error = "reviewed_fixture_unissued_revoked_or_changed"
    if change == "detached":
        parent = parent.model_copy(update={"backend_seal": None})
        error = "reviewed_fixture_receipt_required"
    elif change == "wrong_parent":
        parent = build_reviewed_owned_fixture("financial:FIC-FIN-02", generation="m12au-test")
        error = "configured_composition_parent_binding_mismatch"
    elif change == "generation":
        parent = build_reviewed_owned_fixture("financial:FIC-FIN-01", generation="m12at-deterministic-preflight")
        error = "configured_composition_parent_binding_mismatch"
    elif change == "cutoff":
        parent = parent.model_copy(update={"source_packet": parent.source_packet.model_copy(update={"assessment_date": "2026-09-12"})})
        assert parent.model_dump(mode="json")["source_packet"]["assessment_date"] == "2026-09-12"
    elif change == "basis":
        parent = parent.model_copy(update={"sector_framework": "financial"})
    elif change == "recipe":
        recipe, error = "unregistered", "configured_composition_unregistered_recipe"
    else:
        consumer, error = "CORE_PROMPT", "configured_composition_consumer_forbidden"
    before = set(owner._ISSUED)
    with pytest.raises(ValueError, match=error):
        owner.issue_reviewed_configured_composition(parent, rows=current.configured_rows,
            recipe_id=recipe, consumer=consumer)
    assert set(owner._ISSUED) == before


@pytest.mark.parametrize("field", ["buy_drivers", "sell_drivers", "dominant_evidence",
    "core_investment_judgment", "earnings_estimate_context", "unknown_future_field"])
def test_future_refs_cannot_promote_current_or_unreviewed_fields(field):
    current = child()
    with pytest.raises(ValueError, match="prospective_only"):
        adapter.validate_m12au_composition_v1(current, candidate(current.configured_rows[1].ref_id, field))


def test_material_anchor_membership_and_nested_laundering():
    current = child()
    ref = current.configured_rows[1].ref_id
    for payload, error in [
        ({"ticker": "FIC-FIN-01", "material_directional_anchor_basis": [ref]}, "prospective_only"),
        (candidate("store-only-not-request-member"), "request_membership"),
        ({"ticker": "OTHER", "risk_context": {"evidence_refs": [ref]}}, "candidate_identity_mismatch"),
        ({"ticker": "FIC-FIN-01", "risk_context": {"unreviewed": {"evidence_refs": [ref]}}}, "prospective_only"),
    ]:
        with pytest.raises(ValueError, match=error):
            adapter.validate_m12au_composition_v1(current, payload)


def test_live_lookup_revocation_parent_liveness_and_retry():
    current = child()
    assert child() is current
    owner.verify_reviewed_configured_composition(current, consumer=current.consumer)
    owner.revoke_reviewed_configured_composition(current)
    with pytest.raises(ValueError, match="unissued_revoked_or_changed"):
        adapter.validate_m12au_composition_v1(current, candidate(current.configured_rows[1].ref_id))
    replacement = child()
    assert replacement.receipt_id != current.receipt_id
    revoke_reviewed_fixture(replacement.parent)
    with pytest.raises(ValueError, match="reviewed_fixture_unissued_revoked_or_changed"):
        owner.verify_reviewed_configured_composition(replacement, consumer=replacement.consumer)
    assert child().parent_receipt_id != replacement.parent_receipt_id


def test_field_membership_does_not_replace_configured_role_eligibility():
    current = child()
    with pytest.raises(ValueError, match="future_role_forbidden"):
        adapter.validate_m12au_composition_v1(current,
            candidate(current.configured_rows[0].ref_id, "risk_context"))
    with pytest.raises(ValueError, match="future_role_forbidden"):
        adapter.validate_m12au_composition_v1(current, candidate(current.configured_rows[2].ref_id))


@pytest.mark.parametrize("subject", [f"FIC-FIN-{i:02d}" for i in range(1, 5)])
def test_each_context0_model_projection_parent_binding(subject):
    generation = "m12at-deterministic-preflight"
    parent = build_reviewed_owned_fixture("financial:" + subject, generation=generation)
    composition = owner.build_reviewed_configured_composition(parent,
        recipe_id=generation + ":" + subject, consumer=owner.MODEL_VIEW_CONSUMER)
    catalog, _ = stage_alias_catalogs(parent)
    context = historical.capability.m12.holdout._owned_context(parent, catalog)
    output = adapter.configured_model_projection_v1(composition, context)
    assert output["parent_context"] == context
    assert [row["ref_id"] for row in output["future_configured_conditions"]] == [
        row.ref_id for row in historical._fictional_configured_refs(subject, generation)]
    with pytest.raises(ValueError, match="parent_context_mismatch"):
        adapter.configured_model_projection_v1(composition, {**context, "unadmitted": 987.654321})
    with pytest.raises(ValueError, match="consumer_forbidden"):
        owner.verify_reviewed_configured_composition(composition, consumer=owner.SCHEMA_CONSUMER)
    with pytest.raises(ValueError, match="live_capability_required"):
        owner.verify_reviewed_configured_composition(output, consumer=owner.MODEL_VIEW_CONSUMER)


def test_copy_serialized_and_foreign_registry_not_authority(monkeypatch):
    current = child()
    for forged in (asdict(current), replace(current), pickle.loads(pickle.dumps(current))):
        with pytest.raises(ValueError, match="live_capability_required|unissued_revoked_or_changed"):
            owner.verify_reviewed_configured_composition(forged, consumer=current.consumer)
    with monkeypatch.context() as patch:
        patch.setattr(owner, "_ISSUED", {})
        with pytest.raises(ValueError, match="unissued_revoked_or_changed"):
            owner.verify_reviewed_configured_composition(current, consumer=current.consumer)
    with monkeypatch.context() as patch:
        patch.setattr(owner, "_PID", -1)
        with pytest.raises(ValueError, match="process_mismatch"):
            owner.verify_reviewed_configured_composition(current, consumer=current.consumer)
    code = """import pickle,sys
from app.services.reviewed_configured_composition import verify_reviewed_configured_composition
c=pickle.loads(sys.stdin.buffer.read())
try:
    verify_reviewed_configured_composition(c, consumer=c.consumer)
except ValueError as e:
    assert 'unissued_revoked_or_changed' in str(e)
    print('FOREIGN_INTERPRETER_REJECTED')
else:
    raise AssertionError('foreign interpreter accepted')
"""
    result = subprocess.run([sys.executable, "-B", "-c", code], input=pickle.dumps(current),
        capture_output=True, timeout=30, check=False)
    assert result.returncode == 0, result.stderr.decode()
    assert result.stdout.strip() == b"FOREIGN_INTERPRETER_REJECTED"


def test_model_and_schema_consume_only_reviewed_context0():
    audit = adapter.m12at_schema_impact_v1()
    assert audit["status"] == "PASS"
    assert len(audit["configured_model_surface_rows"]) == 3
    assert all(not row["configured_signal"]["current_directional_driver_eligible"]
        for row in audit["configured_model_surface_rows"])
    assert all(not row["configured_signal"]["material_anchor_eligible"]
        for row in audit["configured_model_surface_rows"])
    for field in ("earnings_estimate_context", "material_directional_anchor_basis"):
        assert set(audit["configured_aliases"]).isdisjoint(historical._schema_ref_values(audit["schema"], field))
    current = child()
    with pytest.raises(ValueError, match="consumer_forbidden"):
        adapter.configured_model_projection_v1(current, audit["parent_context"])
    for index in range(5, 9):
        subject = f"FIC-FIN-{index:02d}"
        parent = build_reviewed_owned_fixture("financial:" + subject, generation="m12at-deterministic-preflight")
        with pytest.raises(ValueError, match="unregistered_recipe"):
            owner.build_reviewed_configured_composition(parent,
                recipe_id="m12at-deterministic-preflight:" + subject, consumer=owner.SCHEMA_CONSUMER)
