from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.services.unified_snapshot_contract import digest, encoded
from app.services.whole_source_code_owner_registry import (
    WholeSourceCodeOwnerRegistry, verify_fresh_code_identity,
)
from app.services.unified_full_source_cohort import FreshFullSourceRunSeed, compose_full_source
from app.services.unified_stock_acquisition import UNIVERSE

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def registry():
    return WholeSourceCodeOwnerRegistry.freeze(ROOT)


def metadata(registry):
    return dict(code_owner_registry=registry.model_dump(mode="json"),
                code_fingerprints=registry.fingerprints)


def verify(registry, value):
    return verify_fresh_code_identity(ROOT, metadata=value, code_sha256=registry.sha256,
                                     authority_sha256=registry.sha256)


def test_exact_owner_role_hash_and_deterministic_order(registry):
    assert len(registry.entries) == 27
    assert all(e.mandatory and e.role for e in registry.entries)
    assert verify(registry, metadata(registry)) == registry
    raw = registry.model_dump(mode="json")
    raw["entries"].reverse()
    reordered = WholeSourceCodeOwnerRegistry.model_validate(raw)
    assert reordered == registry
    assert reordered.sha256 == registry.sha256
    assert registry.seed_bindings == dict(code_config_sha256=registry.sha256,
                                         source_authority_contract_sha256=registry.sha256)


@pytest.mark.parametrize("index", range(27))
def test_each_owner_is_mandatory(registry, index):
    raw = metadata(registry)
    raw["code_owner_registry"]["entries"].pop(index)
    with pytest.raises(ValueError, match="exact_set"):
        verify(registry, raw)


@pytest.mark.parametrize("mutation", ["extra", "duplicate", "path_escape", "role", "hash", "optional"])
def test_typed_entry_negatives(registry, mutation):
    raw = metadata(registry)
    entries = raw["code_owner_registry"]["entries"]
    if mutation in ("extra", "duplicate"):
        entry = deepcopy(entries[0])
        if mutation == "extra":
            entry["path"] = "app/services/unknown.py"
        entries.append(entry)
    else:
        key, value = dict(path_escape=("path", "../escape.py"), role=("role", "unowned"),
                          hash=("file_sha256", "0"*64), optional=("mandatory", False))[mutation]
        entries[0][key] = value
    with pytest.raises(ValueError):
        verify(registry, raw)


@pytest.mark.parametrize("mutation", ["old13", "extra17", "hash", "missing_registry", "legacy_registry",
                                     "stale_seed", "stale_authority"])
def test_producer_metadata_fails_closed(registry, mutation):
    raw = metadata(registry)
    code, authority = registry.sha256, registry.sha256
    if mutation == "old13":
        for name in ("selected_financial_owner", "latest_published_fx", "current_effective_technical"):
            raw["code_fingerprints"].pop("app/services/" + name + ".py")
    elif mutation == "extra17":
        raw["code_fingerprints"]["unknown.py"] = "0"*64
    elif mutation == "hash":
        raw["code_fingerprints"][registry.entries[0].path] = "0"*64
    elif mutation == "missing_registry":
        raw.pop("code_owner_registry")
    elif mutation == "legacy_registry":
        raw["code_owner_registry"] = WholeSourceCodeOwnerRegistry.freeze(ROOT, profile="legacy").model_dump(mode="json")
    elif mutation == "stale_seed":
        code = "0"*64
    else:
        authority = "0"*64
    with pytest.raises(ValueError):
        verify_fresh_code_identity(ROOT, metadata=raw, code_sha256=code, authority_sha256=authority)


def test_missing_changed_and_symlink_files(registry, tmp_path):
    for entry in registry.entries:
        target = tmp_path / entry.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / entry.path).read_bytes())
    assert registry.verify(tmp_path, fingerprints=registry.fingerprints, expected_sha256=registry.sha256) == registry
    target = tmp_path / registry.entries[0].path
    target.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="identity_mismatch"):
        registry.verify(tmp_path, fingerprints=registry.fingerprints, expected_sha256=registry.sha256)
    target.unlink()
    with pytest.raises(ValueError, match="missing_file"):
        WholeSourceCodeOwnerRegistry.freeze(tmp_path)
    target.symlink_to(ROOT / registry.entries[0].path)
    with pytest.raises(ValueError, match="symlink"):
        WholeSourceCodeOwnerRegistry.freeze(tmp_path)


def test_symlink_parent_denied(tmp_path):
    (tmp_path / "app").symlink_to(ROOT / "app", target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        WholeSourceCodeOwnerRegistry.freeze(tmp_path)


def test_historical_consumer13_rejects_legitimate_producer16(registry):
    historical16 = set(registry.fingerprints) - {
        "app/services/fpi_filing_document_graph.py", "app/services/sec_logical_cell_reference.py",
        "app/services/security_valuation_basis.py",
        "app/services/provider_native_valuation_snapshot.py",
        "app/services/provider_native_valuation_acquisition.py",
        "app/services/provider_valuation_calibration_context.py",
        *[e.path for e in registry.entries if e.role.startswith('market_')]}
    assert len(historical16) == 16
    historical13 = historical16 - {
        "app/services/selected_financial_owner.py", "app/services/latest_published_fx.py",
        "app/services/current_effective_technical.py"}
    assert len(historical13) == 13
    assert set(registry.fingerprints) != historical13
    assert verify(registry, metadata(registry)) == registry


@pytest.mark.parametrize("mutation", ["old13", "extra17", "hash"])
def test_composer_rejects_bad_identity_before_source_consumption(registry, mutation):
    from tests.test_unified_live_source_cohort import seed
    raw = metadata(registry)
    if mutation == "old13":
        for name in list(raw["code_fingerprints"])[:3]:
            raw["code_fingerprints"].pop(name)
    elif mutation == "extra17":
        raw["code_fingerprints"]["extra.py"] = "0"*64
    else:
        raw["code_fingerprints"][registry.entries[0].path] = "0"*64
    inventory = json.loads((ROOT / "docs/operations/UNIFIED_ACQUISITION_CLASSES.json").read_bytes())
    raw.update(inventory=inventory, allowed_providers=["fixture"])
    base = seed().model_dump()
    base.update(**registry.seed_bindings, inventory_sha256=digest(inventory),
                universe_sha256=digest(UNIVERSE), source_policy_sha256=digest(["fixture"]))
    fresh = FreshFullSourceRunSeed(**base, fresh_stock_owner_set_sha256="a"*64)
    with pytest.raises(ValueError, match="code_contract_identity"):
        compose_full_source(seed=fresh, market_inputs={}, stock_inputs={}, authority_inputs={},
            version_set={}, optional_denials={}, issuer_bridge={}, composition_metadata=raw,
            fresh_context_inputs={})


def test_actual_production_whole_inputs_composer_and_replay_parity(tmp_path, monkeypatch, registry):
    # Substitute transport captures only. The production metadata/seed builder,
    # stock owners, composer and both replay passes remain real.
    from scripts import r9_rev11_replay as production
    from tests.rev10_cohort_fixtures import stocks, markets, night, START, QUERY, RUN, POLICY_ALL
    from tests.rev10_source_fixtures import event_inputs
    from tests.test_r9_rev8_fresh_publications import publication_sources
    from app.services.unified_run_artifacts import durable_bytes

    inputs = stocks(tmp_path / "stocks")
    event_inputs(tmp_path / "wulf-fresh", inputs=inputs["WULF"], persisted=False)
    market = markets(tmp_path / "markets")
    pubs = publication_sources(START, RUN, as_of=QUERY)
    pubs["policy"] = POLICY_ALL
    context = dict(publications=pubs, night=night(tmp_path / "night"))
    for m, tickers in UNIVERSE.items():
        durable_bytes(tmp_path / ("class-c/local-" + m + ".json"),
                      encoded(inputs[tickers[0]]["technical_inputs"]["local_seed"]) + b"\n", exclusive=True)
    monkeypatch.setattr(production, "stock_inputs", lambda *args: (inputs, {}))
    monkeypatch.setattr(production, "market_inputs", lambda *args: market)
    monkeypatch.setattr(production, "publication_inputs", lambda *args: context)
    frozen = dict(generation_id=RUN, sessions=dict(us="2026-09-22", kr="2026-09-23"))
    args, first, receipt = production.replay_twice(tmp_path, frozen, {}, POLICY_ALL)
    assert args["composition_metadata"]["code_fingerprints"] == registry.fingerprints
    assert args["composition_metadata"]["code_owner_registry"] == registry.model_dump(mode="json")
    assert args["seed"].code_config_sha256 == registry.sha256
    assert args["seed"].source_authority_contract_sha256 == registry.sha256
    assert receipt["replay_equal"] and receipt["first_sha256"] == receipt["second_sha256"]
    identity = receipt["code_owner_registry_identity"]
    assert {v for k, v in identity.items() if k.endswith("_registry_sha256")} == {registry.sha256}
    assert len(first["authority_graph"]["stocks"]) == 22
    from app.services.unified_run_artifacts import durable_json
    durable_json(tmp_path / "production-builder-parity.json", receipt, exclusive=True)
