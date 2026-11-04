"""Synthetic routing seals qualify planning only, never real identity."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import zipfile

import httpx
import pytest

from app.services.canonical_source_plan import kiwoom_request
from app.services.scoped_routing_identity import RoutingCatalogPin, ScopedSubject, SealedRoutingCatalog
from app.services.scoped_source_plan import (
    HistoryCounts, ScopedConfig, compile_scoped_source_plan,
    require_scoped_current_authority, validate_scoped_structure,
)
from app.services.sealed_fresh_dispatch import wire_identity
from app.services.unified_snapshot_contract import encoded
from app.services.unified_stock_acquisition import ROLES, UNIVERSE, make_reads

AT = datetime(2026, 10, 17, 15, tzinfo=timezone.utc)


def fixture_catalog(tmp_path, ticker="FUTURE", market="us", depositary=False, mutation=None, omit=None):
    security = dict(ticker=ticker, canonical_company_id="company-"+ticker,
        canonical_security_id="security-"+ticker, company_name="Synthetic fixture only",
        exchange="NASDAQ" if market=="us" else "KRX", country=market.upper(),
        cik="0000000123" if market=="us" else None, corp_code="00000123" if market=="kr" else None,
        security_type="ADS" if depositary else "common_stock",
        issuer_type="foreign_private_issuer" if depositary else "domestic_us" if market=="us" else "krx",
        identity_provider="fixture", identity_quality="inferred", updated_at="2026-10-01T00:00:00+00:00")
    security.update(mutation or {})
    if omit:
        security.pop(omit)
    member="static/security-lineage.json"
    raw=encoded({ticker:dict(security=security,source_generation="synthetic-history",
        role="IDENTITY_ONLY_NOT_CURRENT_FINANCIAL_EVIDENCE")})
    files={member:raw,"review-control-final/result.sha256":b"CONTROL_SET_SHA256 "+b"a"*64+b"\n"}
    manifest={n:dict(bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for n,v in files.items()}
    archive=tmp_path/(ticker+".zip")
    with zipfile.ZipFile(archive,"x") as z:
        for n,v in files.items():
            z.writestr(n,v)
        z.writestr("manifest.json",encoded(dict(files=manifest)))
    pin=RoutingCatalogPin(archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        member=member,member_sha256=hashlib.sha256(raw).hexdigest(),predecessor_control_sha256="a"*64)
    subject=ScopedSubject(ticker=ticker,market=market,security_id="security-"+ticker,
        issuer_id="0000000123" if market=="us" else "00000123",
        venue="NASDAQ" if market=="us" else "KRX",currency="USD" if market=="us" else "KRW")
    return SealedRoutingCatalog(archive=archive,pin=pin),subject,archive


def arguments(catalog,subject):
    counts=HistoryCounts(**{r:300 for r in ROLES})
    return dict(config=ScopedConfig(subjects=(subject,),kr_history=counts,us_history=counts,kr_max_pages=3),
        catalog=catalog,generation_id="scoped-offline-fixture",at=AT,code_sha="b"*40,
        provider_config_sha256="c"*64,enabled=True)


@pytest.mark.parametrize("ticker,market,depositary",[("FUTURE","us",False),("NVDA","us",False),
    ("654321","kr",False),("035420","kr",False),("UNSEENADR","us",True)])
def test_configuration_only_unseen_planning(tmp_path,ticker,market,depositary):
    catalog,subject,_=fixture_catalog(tmp_path,ticker,market,depositary)
    args=arguments(catalog,subject)
    plan=compile_scoped_source_plan(**args)
    proof=validate_scoped_structure(plan,**args)
    assert proof["structural_status"]=="PASS"
    assert proof["kr_logical_reads"]==10 and proof["us_market_dependency_instruments"]==22
    assert len(plan.stock_reads)==4 and {r.subject for r in plan.stock_reads}=={ticker}
    assert not plan.current_identity_authority and not plan.dispatch_allowed
    assert plan.identities[0].original_identity_quality=="inferred"
    assert plan.identities[0].source_generation=="synthetic-history"
    assert len(plan.price_pairs)==5 and all(not p.available for p in plan.price_pairs)
    with pytest.raises(ValueError,match="NOT_ADMITTED"):
        require_scoped_current_authority(plan)


def test_default_off(tmp_path):
    cat,subject,_=fixture_catalog(tmp_path)
    args=arguments(cat,subject)
    del args["enabled"]
    with pytest.raises(ValueError,match="feature_off"):
        compile_scoped_source_plan(**args)


@pytest.mark.parametrize("field,value",[("security_id","other"),("issuer_id","0000000999"),
    ("venue","NYSE"),("currency","KRW"),("market","kr"),("ticker","NOTINCATALOG")])
def test_exact_sealed_membership(tmp_path,field,value):
    cat,subject,_=fixture_catalog(tmp_path)
    subject=ScopedSubject.model_validate({**subject.model_dump(),field:value})
    with pytest.raises(ValueError,match="scoped_"):
        compile_scoped_source_plan(**arguments(cat,subject))


@pytest.mark.parametrize("field",[ "archive_sha256", "member_sha256", "predecessor_control_sha256"])
def test_archive_anchor_not_caller_rehash(tmp_path,field):
    cat,_,archive=fixture_catalog(tmp_path)
    pin=RoutingCatalogPin.model_validate({**cat.pin.model_dump(),field:"0"*64})
    with pytest.raises(ValueError,match="scoped_catalog_"):
        SealedRoutingCatalog(archive=archive,pin=pin)


@pytest.mark.parametrize("mutation",[dict(issuer_type="unknown"),dict(canonical_company_id=""),
    dict(updated_at="2027-01-01T00:00:00+00:00")])
def test_inherited_identity_owner_required(tmp_path,mutation):
    cat,subject,_=fixture_catalog(tmp_path,mutation=mutation)
    with pytest.raises(ValueError,match="identity_owner_denied|explicit_sealed_identity_fields_required"):
        compile_scoped_source_plan(**arguments(cat,subject))


@pytest.mark.parametrize("field",["security_type","identity_provider","identity_quality","updated_at"])
def test_no_model_defaults_for_missing_sealed_identity(tmp_path,field):
    cat,subject,_=fixture_catalog(tmp_path,omit=field)
    with pytest.raises(ValueError,match="explicit_sealed_identity_fields_required"):
        compile_scoped_source_plan(**arguments(cat,subject))


def test_declared_normalizer_drift_rejects(tmp_path,monkeypatch):
    from app.services import scoped_source_plan as module
    cat,subject,_=fixture_catalog(tmp_path)
    for name in module.OWNER_FILES:
        target=tmp_path/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((module.ROOT/name).read_bytes())
    monkeypatch.setattr(module,"ROOT",tmp_path)
    args=arguments(cat,subject)
    plan=compile_scoped_source_plan(**args)
    changed=tmp_path/"app/services/completed_session_current_price.py"
    changed.write_bytes(changed.read_bytes()+b"\n# changed fixture owner\n")
    with pytest.raises(ValueError,match="canonical_replay_mismatch"):
        validate_scoped_structure(plan,**args)


@pytest.mark.parametrize("mutation",["generation","identity_generation","owner","config","dependency",
    "pair_basis","pair_prior","price_available","dispatch","cursor","request","policy","consumer"])
def test_mutations_reject_at_structure_gate(tmp_path,mutation):
    cat,subject,_=fixture_catalog(tmp_path)
    args=arguments(cat,subject)
    plan=compile_scoped_source_plan(**args)
    data=deepcopy(plan.model_dump(mode="json"))
    if mutation=="generation":
        data["request_plan"]["generation_id"]="wrong"
    elif mutation=="identity_generation":
        data["identities"][0]["source_generation"]="wrong"
    elif mutation=="owner":
        data["owner_files_json"]="{}"
    elif mutation=="config":
        data["config"]["us_history"]["adjusted_daily"]=301
    elif mutation=="dependency":
        data["us_market_symbols"].pop()
    elif mutation=="pair_basis":
        data["price_pairs"][2]["basis"]="ADJUSTED_ETF_RETURN"
    elif mutation=="pair_prior":
        data["price_pairs"][0]["prior"]="2026-01-01"
    elif mutation=="price_available":
        data["price_pairs"][0]["available"]=True
    elif mutation=="dispatch":
        data["dispatch_allowed"]=True
    elif mutation=="cursor":
        row=next(d for d in data["request_plan"]["descriptors"] if d["page_ordinal"]==2)
        row["response_binding"]["parents"]=["kiwoom:auth"]
    elif mutation=="request":
        row=data["request_plan"]["descriptors"][1]
        wire=json.loads(row["request_json"])
        wire["body"]=encoded(dict(stk_cd="OTHER")).decode()
        row["request_json"]=encoded(wire).decode()
    elif mutation=="policy":
        data["request_plan"]["policy_schema_sha256"]="0"*64
    elif mutation=="consumer":
        data["request_plan"]["descriptors"][1]["consumer_role"]="core:direction"
    with pytest.raises(ValueError):
        validate_scoped_structure(data,**args)


def test_full_market_dependencies_and_cursor_owner(tmp_path):
    cat,subject,_=fixture_catalog(tmp_path)
    plan=compile_scoped_source_plan(**arguments(cat,subject))
    market=[d for d in plan.request_plan.descriptors if d.logical_request_id.startswith("us_market:")]
    assert len(market)==47
    assert sum(d.endpoint_operation=="usa10099" for d in market)==3
    assert len({d.subject for d in market if d.endpoint_operation=="usa06012"})==22
    for d in market:
        if d.endpoint_operation=="usa06012":
            assert d.response_binding is not None
            assert d.response_binding.kind==("KIWOOM_US_EXCHANGE" if d.page_ordinal==1 else "KIWOOM_CONTINUATION")
    kr=json.loads(plan.kr_market_reads_json)
    assert len(kr)==10 and sum(r["mandatory"] for r in kr)==6
    assert sum(r["api_id"]=="ka20009" for r in kr)==2


def test_original_fixed_universe_unchanged():
    universe={m:dict(eligible_subjects=list(ts)) for m,ts in UNIVERSE.items()}
    identities={t:dict(canonical_security_id="security-"+t,exchange="NASDAQ" if m=="us" else "KRX")
        for m,ts in UNIVERSE.items() for t in ts}
    counts={m:{r:300 for r in ROLES} for m in UNIVERSE}
    assert len(make_reads(universe,identities,at=AT,counts=counts))==88
    with pytest.raises(ValueError,match="canonical_universe_mismatch"):
        make_reads({"us":dict(eligible_subjects=["MU"])},identities,at=AT,counts=counts,us_only=True)


def test_original_wire_serialization_unchanged():
    body=dict(stk_cd="FUTURE",upd_stkpc_tp="1",stex_tp="ND",strt_dt="",exrt_appl_tp="0")
    original=httpx.Request("POST","https://api.kiwoom.com/api/us/chart",json=body,
        headers={"Content-Type":"application/json;charset=UTF-8","api-id":"usa06012",
        "authorization":"Bearer PLAN_CREDENTIAL","cont-yn":"N","next-key":""})
    assert wire_identity(original,("PLAN_CREDENTIAL",))==wire_identity(
        kiwoom_request("usa06012","/api/us/chart",body),("PLAN_CREDENTIAL",))
