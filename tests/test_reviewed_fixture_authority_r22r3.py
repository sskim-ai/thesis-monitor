"""Real consumers, finite TEST_ONLY producers, no live dispatch or source grants."""
from copy import deepcopy
import asyncio
import json
import subprocess
import sys
from types import SimpleNamespace

import pytest

from app.services import reviewed_fixture_authority as owner
from app.services.accepted_decision_v2_runtime_service import (
    AcceptedV2ProductionContext, accepted_v2_fundamental_core_output_schema,
    accepted_v2_fundamental_core_prompt,
)
from app.services.business_delta_evidence_service import build_business_delta_evidence_view
from app.services.cross_market_decision_engine_service import DecisionEvidencePacket
from app.services.direction_timing_ownership_service import stage_alias_catalogs
from app.services.fixture_context_authority import reject_test_only_production
from app.services.legacy_context_authority import verify_legacy_context
from app.services.structured_autonomy_alias_service import build_evidence_alias_catalog, compact_alias_ai_context
from scripts.directional_core_price_timing_holdout import _owned_context


def fixture(kind):
    if kind == "financial":
        return owner.build_reviewed_owned_fixture("financial:FIC-FIN-05",generation="m12ap-fixture")
    if kind == "delta":
        return owner.build_reviewed_owned_fixture("delta:verified_comparison",delta_identity="DELTA-CAP")
    return owner.build_reviewed_owned_fixture("canary:us",synthetic_identity="SYNTHETIC_AUDIT",padding=0)


def projection(owned):
    if owned.backend_seal.purpose == "FROZEN_DELTA_SEMANTICS":
        catalog = build_evidence_alias_catalog(owned.source_packet)
        return catalog,compact_alias_ai_context(owned.source_packet,catalog,reviewed_fixture=owned)
    catalog = stage_alias_catalogs(owned)[0]
    return catalog,_owned_context(owned,catalog)


@pytest.mark.parametrize("kind",("financial","delta","canary"))
@pytest.mark.parametrize("change",("issuer","domain","price_triage","statement","catalog"))
def test_finite_fixture_rejects_semantic_tampering(kind,change):
    owned = fixture(kind)
    catalog, context = projection(owned)
    if change == "issuer":
        owned = owned.model_copy(update={"source_packet":owned.source_packet.model_copy(update={"ticker":"CALLER"})})
    elif change == "domain":
        first = owned.evidence[0].model_copy(update={"domain":"PRICE_CONTEXT"})
        owned = owned.model_copy(update={"evidence":(first,*owned.evidence[1:])})
    elif change == "price_triage":
        context = {**context,"triage_score":999,"current_price":987.654321}
    elif change == "statement":
        context = deepcopy(context)
        context["evidence"][0]["statement"] = "Caller invented recurring improvement."
    else:
        catalog = catalog.model_copy(update={"alias_map_sha256":"0"*64})
    with pytest.raises(ValueError,match="reviewed_fixture_"):
        build_business_delta_evidence_view(owned,catalog,context=context)


@pytest.mark.parametrize("kind",("financial","delta","canary"))
def test_live_test_owner_idempotency_revocation_and_production_denial(kind):
    owned = fixture(kind)
    assert fixture(kind) == owned
    catalog,context = projection(owned)
    first = build_business_delta_evidence_view(owned,catalog,context=context)
    assert build_business_delta_evidence_view(owned,catalog,context=context) == first
    with pytest.raises(ValueError,match="reviewed_fixture_consumer_forbidden"):
        verify_legacy_context(owned,scope="OWNED_EVIDENCE")
    for value in (owned,context,{"prompt":"Offline.\nDIRECTIONAL_CORE_CONTEXT:\n"+json.dumps([context],default=str)}):
        with pytest.raises(ValueError,match="production_test_only_fixture_forbidden"):
            reject_test_only_production(value)
    owner.revoke_reviewed_fixture(owned)
    with pytest.raises(ValueError,match="reviewed_fixture_unissued_revoked_or_changed"):
        build_business_delta_evidence_view(owned,catalog,context=context)
    fresh = fixture(kind)
    assert fresh.backend_seal.receipt_id != owned.backend_seal.receipt_id
    with pytest.raises(ValueError,match="reviewed_fixture_unissued_revoked_or_changed"):
        build_business_delta_evidence_view(owned,catalog,context=context)
    assert projection(fresh)[1] is not None


@pytest.mark.parametrize("change",("receipt","pid","lifetime","generation","source_time","extra_ref"))
def test_owner_identity_changes_fail_before_catalog(change,monkeypatch):
    owned = fixture("canary")
    if change in {"receipt","pid","lifetime"}:
        key,value = {"receipt":("receipt_id","0"*64),"pid":("owner_pid",-1),"lifetime":("owner_lifetime","caller")}[change]
        owned = owned.model_copy(update={"backend_seal":owned.backend_seal.model_copy(update={key:value})})
    elif change == "generation":
        owned = owned.model_copy(update={"source_packet":owned.source_packet.model_copy(update={"packet_id":"another"})})
    elif change == "source_time":
        owned = owned.model_copy(update={"source_packet":owned.source_packet.model_copy(update={"assessment_date":"2099-01-01"})})
    else:
        owned = owned.model_copy(update={"evidence":(*owned.evidence,owned.evidence[0])})
    with pytest.raises(ValueError,match="reviewed_fixture_"):
        stage_alias_catalogs(owned)


@pytest.mark.parametrize("recipe,parameters",(
    ("financial:FIC-FIN-01",{"generation":"caller-generation"}),
    ("canary:us",{"synthetic_identity":"SYNTHETIC_CALLER","padding":0}),
    ("canary:kr",{"synthetic_identity":"SYNTHETIC_AUDIT","padding":0}),
    ("canary:us",{"synthetic_identity":"SYNTHETIC_AUDIT","padding":1}),
    ("delta:verified_comparison",{"delta_identity":"DELTA-CAP-01"}),
))
def test_parameter_syntax_is_not_authority(recipe,parameters):
    with pytest.raises(ValueError,match="reviewed_fixture_"):
        owner.build_reviewed_owned_fixture(recipe,**parameters)


def core_fixture():
    args = deepcopy(owner._recipes()["recipes"]["core:exact"]["arguments"])
    args["evidence_packets"] = tuple(DecisionEvidencePacket.model_validate(p) for p in args["evidence_packets"])
    return owner.build_reviewed_core_fixture(**args)


def test_core_fixture_schema_semantics_are_not_production_acceptance():
    context = core_fixture()
    assert core_fixture() == context
    schema = accepted_v2_fundamental_core_output_schema(context)
    prompt = accepted_v2_fundamental_core_prompt(context)
    assert schema["properties"]["cores"]["minItems"] == 2
    for value in (context,schema,{"prompt":prompt}):
        with pytest.raises(ValueError,match="production_test_only_fixture_forbidden"):
            reject_test_only_production(value)
    with pytest.raises(ValueError,match="reviewed_fixture_consumer_forbidden"):
        verify_legacy_context(context)
    with pytest.raises(ValueError):
        AcceptedV2ProductionContext.model_validate(context.model_dump(mode="json"))
    owner.revoke_reviewed_fixture(context)
    with pytest.raises(ValueError,match="reviewed_fixture_unissued_revoked_or_changed"):
        accepted_v2_fundamental_core_output_schema(context)
    fresh=core_fixture()
    assert fresh.backend_seal.receipt_id != context.backend_seal.receipt_id
    assert accepted_v2_fundamental_core_output_schema(fresh)
    with pytest.raises(ValueError,match="reviewed_fixture_unissued_revoked_or_changed"):
        accepted_v2_fundamental_core_output_schema(context)


def test_direct_legacy_cli_rejects_fixture_before_state_or_worker(tmp_path,monkeypatch):
    from app.jobs import accepted_decision_v2_runtime as job
    calls = []
    monkeypatch.setattr(job,"prepare_codex_runtime_state",lambda *a,**kw:calls.append("state"))
    context = core_fixture()
    prompt,schema = tmp_path/"prompt.txt",tmp_path/"schema.json"
    prompt.write_text(accepted_v2_fundamental_core_prompt(context))
    schema.write_text(json.dumps(accepted_v2_fundamental_core_output_schema(context)))
    for official in (None,object()):
        with pytest.raises(ValueError,match="production_test_only_fixture_forbidden"):
            job._invoke_signed_in_codex(codex_bin="not-executable",prompt=prompt,schema=schema,
                output=tmp_path/"absent"/"output.json",log=tmp_path/"absent"/"log.txt",
                cwd=tmp_path,timeout=1,state_namespace="test-only",official_shadow=official)
    assert not calls and not (tmp_path/"absent").exists()


def test_fixture_expected_dependencies_cannot_be_promoted_to_independence():
    from app.services.market_expectation_evidence_service import MarketExpectationStructuredBasis,build_market_expectation_evidence_view
    owned = fixture("financial")
    catalog,_ = projection(owned)
    refs = {entry.label:entry.canonical_ref for entry in catalog.entries}
    forged = MarketExpectationStructuredBasis(expectation_ref=refs["market-expectation"],
        independently_observed=True,independence_basis_refs=(refs["remaining-unknown"],))
    with pytest.raises(ValueError,match="reviewed_fixture_expectation_basis_changed"):
        build_market_expectation_evidence_view(owned,catalog,structured_bases=(forged,))


@pytest.mark.parametrize("kind",("financial","delta","canary"))
def test_derived_business_projection_stays_exact_live_and_marked(kind):
    from app.services.business_delta_evidence_service import (
        BusinessDeltaCapability, business_delta_evidence_view_sha256,
        business_delta_property_enums, validate_business_delta_candidate,
        build_business_delta_constrained_batch_schema,
    )
    from app.services.direction_timing_ownership_service import DirectionalCoreCandidate
    owned = fixture(kind)
    catalog, context = projection(owned)
    view = build_business_delta_evidence_view(owned,catalog,context=context)
    again = build_business_delta_evidence_view(owned,catalog,context=context)
    assert business_delta_evidence_view_sha256(view) == business_delta_evidence_view_sha256(again)
    schema = build_business_delta_constrained_batch_schema(candidate_schema=DirectionalCoreCandidate.model_json_schema(),
        contract="test",packet_id="test",aliases_by_ticker={view.ticker:tuple(catalog.by_alias)},views={view.ticker:view})
    for value in (view.model_context(),schema):
        with pytest.raises(ValueError,match="production_test_only_fixture_forbidden"):
            reject_test_only_production(value)
    changed = view.model_copy(update={"capability":BusinessDeltaCapability.INPUT_AMBIGUOUS})
    consumers = (lambda v:v.model_context(),business_delta_evidence_view_sha256,
        lambda v:business_delta_property_enums({v.ticker:v}),lambda v:validate_business_delta_candidate({},v))
    for consumer in consumers:
        with pytest.raises(ValueError,match="reviewed_fixture_view_projection_mismatch"):
            consumer(changed)
        with pytest.raises(ValueError,match="reviewed_fixture_view_parent_required"):
            consumer(view.model_copy(update={"test_only_provenance":None,"contract":"business-delta-evidence-capability-v1"}))
    owner.revoke_reviewed_fixture(owned)
    for consumer in consumers:
        with pytest.raises(ValueError,match="reviewed_fixture_unissued_revoked_or_changed"):
            consumer(view)


def test_reviewed_expectation_projection_cannot_outlive_or_change_parent():
    from app.services.market_expectation_evidence_service import build_market_expectation_evidence_view,market_expectation_evidence_view_sha256
    owned=fixture("financial")
    catalog,_=projection(owned)
    view=build_market_expectation_evidence_view(owned,catalog)
    assert view.model_context()["test_only_provenance"]["provenance"]=="TEST_ONLY"
    market_expectation_evidence_view_sha256(view)
    altered=view.model_copy(update={"items":(view.items[0].model_copy(update={"reason":"CALLER"}),*view.items[1:])})
    with pytest.raises(ValueError,match="reviewed_fixture_view_projection_mismatch"):
        altered.model_context()
    owner.revoke_reviewed_fixture(owned)
    with pytest.raises(ValueError,match="reviewed_fixture_unissued_revoked_or_changed"):
        market_expectation_evidence_view_sha256(view)


@pytest.mark.parametrize("kind",("financial","delta","canary"))
def test_alias_parent_omission_cannot_strip_fixture_authority(kind,monkeypatch):
    owned=fixture(kind)
    catalog=build_evidence_alias_catalog(owned.source_packet)
    monkeypatch.setattr(owner,"_RESERVED_REFS",set())
    with pytest.raises(ValueError,match="fixture_context_verified_alias_path_required"):
        compact_alias_ai_context(owned.source_packet,catalog)


@pytest.mark.parametrize("delimiter",("DIRECTIONAL_CORE_CONTEXT","PRICE_TIMING_CONTEXT"))
def test_canary_prompt_alone_denied_with_plain_schema_before_dispatch(delimiter,tmp_path,monkeypatch):
    from app.jobs import accepted_decision_v2_runtime as job
    owned=fixture("canary")
    _,context=projection(owned)
    assert "test_only_provenance" not in context
    prompt,schema=tmp_path/"prompt.txt",tmp_path/"schema.json"
    prompt.write_text("Offline.\n"+delimiter+":\n"+json.dumps([context]))
    schema.write_text('{"type":"object"}')
    calls=[]
    monkeypatch.setattr(job,"prepare_codex_runtime_state",lambda *a,**kw:calls.append("state"))
    monkeypatch.setattr(owner,"_RESERVED_REFS",set())
    with pytest.raises(ValueError,match="production_test_only_fixture_forbidden"):
        job._invoke_signed_in_codex(codex_bin="not-executable",prompt=prompt,schema=schema,
            output=tmp_path/"absent"/"out",log=tmp_path/"absent"/"log",cwd=tmp_path,timeout=1,state_namespace="fixture")
    assert not calls and not (tmp_path/"absent").exists()


def test_canary_denial_survives_new_interpreter_without_issuance():
    owned=fixture("canary")
    _,context=projection(owned)
    code="""import json,sys
from app.services import reviewed_fixture_authority as owner
from app.services.fixture_context_authority import reject_test_only_production
assert not owner._ISSUED and not owner._RESERVED_REFS
value=json.load(sys.stdin)
try:
    reject_test_only_production(value)
except ValueError as exc:
    assert str(exc)=='production_test_only_fixture_forbidden'
    print('DENIED_WITHOUT_ISSUANCE')
else:
    raise AssertionError('unmarked canary escaped')
"""
    result=subprocess.run([sys.executable,"-B","-c",code],input=json.dumps({"prompt":"Offline.\nPRICE_TIMING_CONTEXT:\n"+json.dumps([context])}),text=True,capture_output=True,timeout=30,check=False)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()=="DENIED_WITHOUT_ISSUANCE"


@pytest.mark.parametrize("kind",("financial","delta","canary"))
@pytest.mark.parametrize("carrier",("context","derived_view"))
def test_reviewed_fixture_real_bridge_and_transport_deny_before_effects(kind,carrier,tmp_path,monkeypatch):
    from app.services.production_runtime_bridge import ProductionRuntimeBridgeV1
    from tests.test_production_model_transport import invocation,payload,transport
    owned=fixture(kind)
    catalog,context=projection(owned)
    if carrier=="derived_view":
        context=build_business_delta_evidence_view(owned,catalog,context=context).model_context()
    value=payload("CORE")
    value["input"]=context
    value["prompt"]="Offline.\nDIRECTIONAL_CORE_CONTEXT:\n"+json.dumps(context)
    item,workers=transport(invocation.__wrapped__(tmp_path,monkeypatch),tmp_path)
    before=deepcopy(item.counts),item.total
    calls=[]
    async def request(*args,**kwargs):
        calls.append("model")
        raise AssertionError("fixture reached model")
    bridge=ProductionRuntimeBridgeV1(settings=None,sources=None,model=SimpleNamespace(request=request),delivery=None,clock=None)
    with pytest.raises(ValueError,match="production_test_only_fixture_forbidden"):
        asyncio.run(item.request(value,model="gpt-5.6-sol",effort="xhigh",timeout=600,stage="CORE"))
    with pytest.raises(ValueError,match="production_test_only_fixture_forbidden"):
        asyncio.run(bridge._invoke(None,"CORE",dict(batch=1,subjects=[owned.source_packet.ticker],payload=value),tmp_path/"dispatch"))
    assert not calls and not workers and (item.counts,item.total)==before
    assert not item.runtime_root.exists() and not (tmp_path/"dispatch").exists()


@pytest.mark.parametrize("recipe",("direction","direction-leading","transition","transition-delta"))
def test_packet_fixture_explicit_alias_parent_cannot_be_unsealed_or_wrong_consumer(recipe):
    owned=owner.build_reviewed_owned_fixture("packet:"+recipe)
    catalog=build_evidence_alias_catalog(owned.source_packet)
    with pytest.raises(ValueError,match="reviewed_fixture_consumer_forbidden"):
        compact_alias_ai_context(owned.source_packet,catalog,reviewed_fixture=owned)
    for seal in (None, {"contract":"unissued"}):
        unsealed=owned.model_copy(update={"backend_seal":seal})
        with pytest.raises(ValueError,match="reviewed_fixture_receipt_required"):
            compact_alias_ai_context(owned.source_packet,catalog,reviewed_fixture=unsealed)


@pytest.mark.parametrize("recipe",("direction","direction-leading","transition","transition-delta"))
@pytest.mark.parametrize("kind",("business","market"))
def test_packet_view_json_stripping_does_not_erase_source_lineage(recipe,kind):
    from app.services.business_delta_evidence_service import BusinessDeltaEvidenceView,business_delta_evidence_view_sha256,business_delta_property_enums,validate_business_delta_candidate
    from app.services.market_expectation_evidence_service import MarketExpectationEvidenceView,build_market_expectation_evidence_view,market_expectation_evidence_view_sha256
    owned=owner.build_reviewed_owned_fixture("packet:"+recipe)
    catalog=stage_alias_catalogs(owned)[0]
    if kind=="business":
        view=build_business_delta_evidence_view(owned,catalog)
        model=BusinessDeltaEvidenceView
        contract="business-delta-evidence-capability-v1"
        consumers=(lambda v:v.model_context(),business_delta_evidence_view_sha256,
            lambda v:business_delta_property_enums({v.ticker:v}),lambda v:validate_business_delta_candidate({},v))
    else:
        view=build_market_expectation_evidence_view(owned,catalog)
        model=MarketExpectationEvidenceView
        contract="market-expectation-evidence-view-v1"
        consumers=(lambda v:v.model_context(),market_expectation_evidence_view_sha256)
    view.model_context()
    serialized=json.loads(view.model_dump_json())
    serialized.pop("test_only_provenance")
    serialized["contract"]=contract
    stripped=model.model_validate(serialized)
    for revoke in (False,True):
        if revoke:
            owner.revoke_reviewed_fixture(owned)
        for consumer in consumers:
            with pytest.raises(ValueError,match="reviewed_fixture_view_parent_required"):
                consumer(stripped)
        with pytest.raises(ValueError,match="production_test_only_fixture_forbidden"):
            reject_test_only_production(serialized)
    code="""import json,sys
from app.services import reviewed_fixture_authority as owner
from app.services.fixture_context_authority import reject_test_only_production
assert not owner._ISSUED and not owner._RESERVED_REFS
try:
    reject_test_only_production(json.load(sys.stdin))
except ValueError as exc:
    assert str(exc)=='production_test_only_fixture_forbidden'
else:
    raise AssertionError('stripped packet lineage escaped')
"""
    result=subprocess.run([sys.executable,"-B","-c",code],input=json.dumps(serialized),text=True,capture_output=True,timeout=30,check=False)
    assert result.returncode==0,result.stderr


@pytest.mark.parametrize("recipe",("direction","direction-leading","transition","transition-delta"))
def test_competing_raw_carrier_fields_cannot_hide_packet_fixture(recipe,tmp_path,monkeypatch):
    from tests.test_production_model_transport import invocation,payload,transport
    packet=deepcopy(owner._recipes()["recipes"]["packet:"+recipe]["payload"]["source_packet"])
    variants=[]
    for items in ([],None,"unrelated",[{"canonical_ref":"unrelated","source_ref":"unrelated"}]):
        variants.append({**deepcopy(packet),"items":items})
    for canonical in (None,"unrelated"):
        changed=deepcopy(packet)
        for row in changed["evidence"]:
            row["canonical_ref"]=canonical
        variants.append(changed)
    item,workers=transport(invocation.__wrapped__(tmp_path,monkeypatch),tmp_path)
    before=deepcopy(item.counts),item.total
    monkeypatch.setattr(owner,"_RESERVED_REFS",set())
    for variant in variants:
        with pytest.raises(ValueError,match="production_test_only_fixture_forbidden"):
            reject_test_only_production(variant)
        value=payload("CORE")
        value["input"]=variant
        value["prompt"]="Offline.\nFROZEN_CONTEXT:\n"+json.dumps(variant)
        with pytest.raises(ValueError,match="production_test_only_fixture_forbidden"):
            asyncio.run(item.request(value,model="gpt-5.6-sol",effort="xhigh",timeout=600,stage="CORE"))
    assert not workers and (item.counts,item.total)==before and not item.runtime_root.exists()
    code="""import json,sys
from app.services import reviewed_fixture_authority as owner
from app.services.fixture_context_authority import reject_test_only_production
from app.services.production_model_transport import render_prompt
assert not owner._ISSUED and not owner._RESERVED_REFS
for value in json.load(sys.stdin):
    payload={'input':value,'response_schema':{'type':'object'},'prompt':'Offline.\\nFROZEN_CONTEXT:\\n'+json.dumps(value)}
    for call in (lambda:reject_test_only_production(value),lambda:render_prompt(payload,'CORE')):
        try:
            call()
        except ValueError as exc:
            assert str(exc)=='production_test_only_fixture_forbidden'
        else:
            raise AssertionError('competing carrier fields hid fixture lineage')
"""
    result=subprocess.run([sys.executable,"-B","-c",code],input=json.dumps(variants),text=True,capture_output=True,timeout=30,check=False)
    assert result.returncode==0,result.stderr
    ordinary=deepcopy(packet)
    ordinary["ticker"]="UNSEEN_NONFIXTURE_IDENTITY"
    assert not owner._has_packet_fixture_lineage(ordinary)
    for row in packet["evidence"]:
        row["source_ref"]="unrelated-source"
    assert not owner._has_packet_fixture_lineage(packet)
