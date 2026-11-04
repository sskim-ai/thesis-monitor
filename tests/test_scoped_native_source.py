"""Synthetic canonical-owner execution, not current source/model admission."""
from copy import deepcopy

import pytest

from app.services.scoped_native_source import owner_replay_plan, replay_scoped_stock
from app.services.scoped_source_plan import compile_scoped_source_plan
from tests.rev8_source_fixtures import fresh_inputs
from tests.test_scoped_source_plan import arguments, fixture_catalog
from tests.test_unified_stock_owner import freeze_hashes
from app.services.unified_snapshot_contract import digest


def inputs(tmp_path, ticker="NEWUS", market="us"):
    catalog, subject, _ = fixture_catalog(tmp_path, ticker, market,
        mutation={"identity_provider": "local", **({"cik": "0000001234"} if market == "us" else {})})
    if market == "us":
        subject = subject.model_copy(update={"issuer_id": "0000001234"})
    args = arguments(catalog, subject)
    scoped = compile_scoped_source_plan(**args)
    plan = owner_replay_plan(scoped, compiler_inputs=args, enabled=True)
    owner_inputs = fresh_inputs(tmp_path / "source", ticker, plan=plan,
        security_overrides=catalog.record(scoped.identities[0], at=args["at"]))
    for receipt in owner_inputs["technical_inputs"]["receipts"].values():
        for page in receipt["pages"]:
            page["response_continuation"] = {"cont_yn": "N", "next_key": ""}
    owner_inputs["technical_inputs"] = freeze_hashes(owner_inputs["technical_inputs"])
    return scoped, args, owner_inputs


@pytest.mark.parametrize("ticker,market", [("NEWUS", "us"), ("NVDA", "us"),
                                         ("654321", "kr"), ("035420", "kr")])
def test_config_only_actual_canonical_owner_call(tmp_path, ticker, market):
    scoped, args, data = inputs(tmp_path, ticker, market)
    result = replay_scoped_stock(scoped, compiler_inputs=args, ticker=ticker, owner_inputs=data, enabled=True)
    canonical = result["canonical_owner_result"]
    assert canonical["contract"] == "fresh-financial-stock-owner-v1"
    assert canonical["evidence_packet"] and canonical["ownership"]
    assert canonical["packet"]["stocks"][0]["ticker"] == ticker
    assert result["source_use"] == "NOT_ADMITTED"
    assert not result["model_dispatch_allowed"]
    assert "SEALED_NATIVE_RAW_PARSER_REPLAY" in result["missing_admission"]
    assert result["historical_identity_generation"] == "synthetic-history"


def test_default_off(tmp_path):
    scoped, args, data = inputs(tmp_path)
    with pytest.raises(ValueError, match="feature_off"):
        replay_scoped_stock(scoped, compiler_inputs=args, ticker="NEWUS", owner_inputs=data)


@pytest.mark.parametrize("mutation", ["prebuilt", "d01", "d02", "plan", "security", "issuer",
    "generation", "period", "missing_role", "raw", "normalized", "receipt",
    "security_type", "identity_quality", "updated_at", "local_identity"])
def test_no_packet_cast_or_owner_bypass(tmp_path, mutation):
    scoped, args, data = inputs(tmp_path)
    data = deepcopy(data)
    tech, fin = data["technical_inputs"], data["financial_inputs"]
    if mutation in {"prebuilt", "d01", "d02"}:
        data[mutation] = "PASS"
    elif mutation == "plan":
        tech["plan"] = tech["plan"].model_copy(update={"acquisition_id": "other"})
    elif mutation == "security":
        fin["plan"]["security"]["canonical_security_id"] = "other"
    elif mutation == "issuer":
        fin["plan"]["security"]["cik"] = "other"
    elif mutation in {"security_type", "identity_quality", "updated_at"}:
        fin["plan"]["security"][mutation] = {"security_type":"ETF", "identity_quality":"verified",
            "updated_at":"2026-10-02T00:00:00Z"}[mutation]
        fin["plan"]["identity_sha256"] = digest(fin["plan"]["security"])
    elif mutation == "local_identity":
        for role in tech["local_seed"]["roles"].values():
            for record in role["records"]:
                if record["table"] == "securitymaster":
                    record["record"]["issuer_type"] = "foreign_private_issuer"
        freeze_hashes(tech)
    elif mutation == "generation":
        fin["plan"]["run_id"] = "other"
    elif mutation == "period":
        fin["plan"]["cutoff"] = "2026-10-18T00:00:00+00:00"
    elif mutation == "missing_role":
        tech["receipts"].pop("adjusted_daily")
    elif mutation in {"raw", "normalized"}:
        tech["artifacts"]["adjusted_daily." + ("body" if mutation == "raw" else "json")] = b"{}"
    else:
        tech["receipts"]["adjusted_daily"]["pages"][0]["request"]["payload"]["stk_cd"] = "WRONG"
    identity_error = "sealed_identity_record_mismatch" if mutation in {
        "security_type", "identity_quality", "updated_at", "local_identity"} else None
    with pytest.raises((ValueError, KeyError), match=identity_error):
        replay_scoped_stock(scoped, compiler_inputs=args, ticker="NEWUS", owner_inputs=data, enabled=True)
