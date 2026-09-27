from copy import deepcopy
import json
from types import SimpleNamespace
import zipfile

import pytest

from scripts import r2b_sealed_blind_preflight as subject


@pytest.mark.parametrize("field", ["overall_direction", "buy_drivers", "model_output", "previous_assessment"])
def test_blind_stock_rejects_downstream_labels(field):
    with pytest.raises(ValueError, match="downstream_output_forbidden"):
        subject.source_only_stock({"packet": {field: "synthetic"}}, {})


def test_blind_stock_rejects_nested_serialized_candidate():
    with pytest.raises(ValueError, match="downstream_output_forbidden"):
        subject.source_only_stock({"packet": {"source": json.dumps({"ai_verdict": "synthetic"})}}, {})


def archive_fixture(tmp_path, manifest_override=None):
    data = b'{"fact":1}'
    manifest = {"facts.json": {"sha256": subject.sha(data), "bytes": len(data)}}
    if manifest_override:
        manifest["facts.json"].update(manifest_override)
    path = tmp_path / "source.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("facts.json", data)
        archive.writestr("bundle-manifest.json", json.dumps(manifest))
    return path, manifest


def test_archive_exact_hash_and_manifest(tmp_path):
    path, manifest = archive_fixture(tmp_path)
    assert subject.read_verified_archive(path, subject.sha(path.read_bytes())) == manifest


def test_archive_wrong_zip_sha_rejected(tmp_path):
    path, _ = archive_fixture(tmp_path)
    with pytest.raises(ValueError, match="source_zip_sha_mismatch"):
        subject.read_verified_archive(path, "0" * 64)


@pytest.mark.parametrize("override", [{"sha256": "0" * 64}, {"bytes": 99}])
def test_archive_wrong_entry_rejected(tmp_path, override):
    path, _ = archive_fixture(tmp_path, override)
    with pytest.raises(ValueError, match="source_artifact_hash_mismatch"):
        subject.read_verified_archive(path, subject.sha(path.read_bytes()))


def test_source_gate_reuses_existing_policy_without_widening_context(monkeypatch):
    metadata = {"ref_id": "canonical:event:synthetic", "category": "earnings",
                "statement": '{"revenue":123}', "as_of": "2026-09-01"}
    evidence = {"evidence": [metadata]}
    stock = {"ticker": "SYNTHETIC", "market": "us", "status": "PASS", "ownership": {},
             "packet": {"stocks": [{"ticker": "SYNTHETIC", "fact_catalog": []}]},
             "evidence_packet": evidence, "financial_state": {"status": "UNAVAILABLE"}}
    authority = {"authority": {"authority_records": [{"ref_id": metadata["ref_id"],
        "authority_state": "RESOLVED", "allowed_uses": ["CONTEXT"], "prohibited_uses": ["OVERALL_DIRECTION"]}]}}
    original = deepcopy(authority)
    owned = SimpleNamespace(core_refs={metadata["ref_id"]},
        source_packet=SimpleNamespace(model_dump=lambda **_: evidence))
    monkeypatch.setattr(subject, "OwnedEvidencePacket", SimpleNamespace(model_validate=lambda _: owned))
    receipt = subject.stock_preflight(stock, authority)
    assert receipt["source_assembly_status"] == "PASS"
    assert receipt["status"] == "BLOCKED"
    assert receipt["observed_propositions"] == 0
    assert receipt["directional_authority_refs"] == []
    assert authority == original


def test_exact_universe_required():
    with pytest.raises(ValueError, match="exact_two_markets_required"):
        subject.cohort_preflight({"packets": {"us": {}}})


def test_blind_projection_does_not_include_ownership_policy_or_modify_source():
    stock = {"packet": {"market": "us", "stocks": []}, "ownership": {"private": "policy"},
             "financial_bindings": {}, "financial_state": {"denial": "unavailable"},
             "source_graph": {}, "numeric_registry_graph": [], "evidence_reference_graph": {}}
    original = deepcopy(stock)
    result = subject.source_only_stock(stock, {"authority": {"authority_records": []}})
    assert "ownership" not in result
    assert result["financial_state"] == {"denial": "unavailable"}
    assert stock == original
