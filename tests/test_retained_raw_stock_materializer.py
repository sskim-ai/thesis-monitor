from hashlib import sha256
import json
import zipfile

import pytest

from app.services.retained_raw_stock_materializer import (
    RetainedArchive, RetainedDependencyError, _relative, valuation_dependencies, dispatch_raw_dependency,
)


def archive(tmp_path, *, corrupt=False, extra=False, budget=1000):
    path = tmp_path / "retained.zip"
    raw = b'{"source":"retained"}'
    record = dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
    manifest = json.dumps({"files": {"raw.json": record}}).encode()
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("result/bundle-manifest.json", manifest)
        z.writestr("result/raw.json", b"X" * len(raw) if corrupt else raw)
        if extra:
            z.writestr("result/unmanifested.json", b"{}")
    return path, dict(archive_sha256=sha256(path.read_bytes()).hexdigest(),
        manifest_member="result/bundle-manifest.json",
        manifest_sha256=sha256(manifest).hexdigest(), max_selected_bytes=budget)


def test_verified_dependency_is_not_authority(tmp_path):
    path, args = archive(tmp_path)
    retained = RetainedArchive(path, **args)
    assert retained.json("raw.json", "owner_raw") == {"source": "retained"}
    retained.read("raw.json", "same_invocation_lookup")
    assert len(retained.ledger) == 1
    assert retained.ledger["raw.json"]["purposes"] == ["owner_raw", "same_invocation_lookup"]
    assert not hasattr(retained, "ownership")


@pytest.mark.parametrize("field,code", [
    ("archive_sha256", "retained_archive_sha_mismatch"),
    ("manifest_sha256", "retained_manifest_sha_mismatch"),
])
def test_wrong_external_pin(tmp_path, field, code):
    path, args = archive(tmp_path)
    args[field] = "0" * 64
    with pytest.raises(RetainedDependencyError) as exc:
        RetainedArchive(path, **args)
    assert exc.value.code == code


def test_manifest_rehash_does_not_hide_raw_drift(tmp_path):
    path, args = archive(tmp_path, corrupt=True)
    retained = RetainedArchive(path, **args)
    with pytest.raises(RetainedDependencyError) as exc:
        retained.read("raw.json", "negative")
    assert exc.value.code == "retained_member_hash"
    assert not retained.ledger


def test_extra_member_denied(tmp_path):
    path, args = archive(tmp_path, extra=True)
    with pytest.raises(RetainedDependencyError) as exc:
        RetainedArchive(path, **args)
    assert exc.value.code == "retained_manifest_membership"


def test_exact_missing_dependency(tmp_path):
    path, args = archive(tmp_path)
    retained = RetainedArchive(path, **args)
    with pytest.raises(RetainedDependencyError) as exc:
        retained.read("missing.body", "financial_raw")
    assert exc.value.code == "retained_dependency_missing"
    assert exc.value.member == "result/missing.body"


def test_budget_fails_before_read(tmp_path):
    path, args = archive(tmp_path, budget=1)
    retained = RetainedArchive(path, **args)
    with pytest.raises(RetainedDependencyError) as exc:
        retained.read("raw.json", "oversize")
    assert exc.value.code == "retained_dependency_budget"
    assert not retained.ledger


@pytest.mark.parametrize("value", ["", "/absolute", "../raw", "a/../raw", "a//raw", "./raw"])
def test_path_escape_denied(value):
    with pytest.raises(RetainedDependencyError, match="retained_path_invalid"):
        _relative(value)


def test_archive_symlink_denied(tmp_path):
    path, args = archive(tmp_path)
    link = tmp_path / "link.zip"
    link.symlink_to(path)
    with pytest.raises(RetainedDependencyError) as exc:
        RetainedArchive(link, **args)
    assert exc.value.code == "retained_archive_symlink"


def test_attempted_kr_listing_children_preserved_without_other_subjects():
    inventory = dict(provider="kiwoom", market_type="0",
        slots=["valuation:list:0", "valuation:basic:UNSEEN_KR"])
    results = {k: {} for k in ("valuation:list:0", "valuation:list:0:continuation:2",
        "valuation:list:0:continuation:3", "valuation:list:10:continuation:2")}
    assert valuation_dependencies(inventory, results) == set(inventory["slots"]) | {
        "valuation:list:0:continuation:2", "valuation:list:0:continuation:3"}


@pytest.mark.parametrize("status", ["PASS", "FAILED"])
def test_raw_dependency_follows_receipt_not_success(status):
    from types import SimpleNamespace
    descriptor = SimpleNamespace(raw_path="raw/normalized-failure.body")
    assert dispatch_raw_dependency(descriptor, dict(status=status, raw_sha256="a"*64)) == "dispatch/raw/normalized-failure.body"
    assert dispatch_raw_dependency(descriptor, dict(status=status, raw_sha256=None)) is None


def test_full22_subject_view_cannot_drop_shared_issuer():
    from tests.rev10_cohort_fixtures import plan_and_securities
    from app.services.canonical_source_replay import validate_subject_view
    plan, _ = plan_and_securities()
    assert validate_subject_view(plan, None) is None
    members = tuple(t for tickers in plan.universe.values() for t in tickers)
    assert validate_subject_view(plan, members) == set(members)
    with pytest.raises(ValueError, match="^stock_subject_view_full_cohort_dependency_contract_required$"):
        validate_subject_view(plan, ("IBM",))


@pytest.mark.parametrize("symbol", ["IBM", "GOOGL", "RXRX"])
def test_us14_view_is_symbol_independent_but_does_not_grant_authority(symbol):
    from tests.rev10_cohort_fixtures import plan_and_securities
    from app.services.unified_stock_acquisition import StockPlan
    from app.services.canonical_source_replay import validate_subject_view
    original, _ = plan_and_securities()
    data = original.model_dump(mode="json")
    data.update(contract="one-shot-us14-source-acquisition-v1",
        reads=[r for r in data["reads"] if r["market"] == "us"])
    plan = StockPlan.model_validate(data)
    assert validate_subject_view(plan, (symbol,)) == {symbol}
    assert len(plan.universe["us"]) == 14 and len(plan.reads) == 56
    with pytest.raises(ValueError, match="^stock_subject_view_not_in_original_plan$"):
        validate_subject_view(plan, (symbol, symbol))
