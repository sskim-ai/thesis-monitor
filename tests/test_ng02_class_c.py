"""Synthetic boundary diagnostics, never real current Class-C authority."""

from copy import deepcopy
import pytest
from app.services.unified_local_seed_bridge import local_owner
from app.services.unified_snapshot_contract import digest, encoded
from test_unified_stock_owner import source as source_fixture


@pytest.fixture
def seed():
    s = source_fixture.__wrapped__()
    return deepcopy(s["local_seed"]), s["plan"].frozen_at, s["policy"]


def invoke(d, at, policy):
    return [
        local_owner(
            role=role, market="us", session_key="2026-09-25", policy=policy
        ).project_and_validate(encoded(d), at)
        for role in d["roles"]
    ]


def test_original_owner_synthetic_replay_not_real_authority(seed):
    d, at, policy = seed
    before = deepcopy(d)
    assert all(p.eligible for p in invoke(d, at, policy))
    assert d == before
    assert d["production_seed_qualified"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        "wrong_market",
        "wrong_session",
        "wrong_contract",
        "fingerprint",
        "duplicate_record",
        "record_id",
        "role_version",
        "after_cutoff_thesis",
        "wrong_security_ticker",
        "inactive_registration",
        "forged_eligible",
        "prior_assessment",
        "wrong_exchange",
    ],
)
def test_actual_local_owner_rejects_invalid_frozen_records(seed, mutation):
    d, at, policy = seed
    roles = d["roles"]
    security = roles["security_identity"]["records"][0]
    thesis = next(
        r
        for r in roles["stored_thesis_and_business_metadata"]["records"]
        if r["table"] == "investmentthesis"
    )
    if mutation == "wrong_market":
        d["market"] = "kr"
    elif mutation == "wrong_session":
        d["session"] = "2020-01-01"
    elif mutation == "wrong_contract":
        d["contract"] = "caller-approved"
    elif mutation == "fingerprint":
        d["owner_fingerprints"] = {}
    elif mutation == "duplicate_record":
        roles["security_identity"]["records"].append(deepcopy(security))
    elif mutation == "record_id":
        security["record_id"] = "999"
    elif mutation == "role_version":
        roles["security_identity"]["version"] = "0" * 64
    elif mutation == "after_cutoff_thesis":
        thesis["record"]["created_at"] = "2099-01-01T00:00:00Z"
    elif mutation == "wrong_security_ticker":
        security["record"]["ticker"] = "WRONG"
    elif mutation == "inactive_registration":
        roles["universe"]["records"][0]["record"]["active"] = False
    elif mutation == "forged_eligible":
        roles["universe"]["eligible"] = False
    elif mutation == "prior_assessment":
        roles["universe"]["records"][0]["record"]["latest_status"] = "BUY"
    elif mutation == "wrong_exchange":
        security["record"]["exchange"] = "KOSPI"
    if mutation != "role_version":
        for role in roles.values():
            role["version"] = digest(role["records"])
    with pytest.raises(ValueError):
        invoke(d, at, policy)


@pytest.mark.parametrize("mutation", ["declared_cutoff", "original_record_digest"])
def test_diagnostic_local_owner_is_not_external_source_authenticator(seed, mutation):
    d, at, policy = seed
    if mutation == "declared_cutoff":
        d["cutoff"] = "2000-01-01T00:00:00+00:00"
    else:
        d["roles"]["security_identity"]["records"][0]["original_record_sha256"] = (
            "0" * 64
        )
    for role in d["roles"].values():
        role["version"] = digest(role["records"])
    # Strict diagnostic expectation: keep a failure visible if the inner owner
    # relies on an outer authenticated freeze rather than checking these fields.
    with pytest.raises(ValueError):
        invoke(d, at, policy)
