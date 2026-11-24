"""Selected original Source lineage over unchanged per-role economic owners.

Each child has its own run/session/cutoff. This type is not a Full22 production
binding and is never constructed from a compact report or a public receipt.
"""
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import Field, model_serializer, model_validator

from app.services.canonical_source_composition import SourceRunBinding
from app.services.market_session import korea_market_session, us_market_session
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest,encoded
from app.services.selected_source_plan import UsNightPolicy, US_NIGHT_EXCLUDED, US_NIGHT_OPTIONAL, excluded_night_receipt, us_night_excluded, us_night_optional

CONTRACT='selected-original-source-run-binding-v1'
GRAPH='selected-original-source-authority-graph-v1'
CODE=('app/services/selected_source_composition.py','app/services/selected_source_plan.py',
    'app/services/selected_source_registration.py','app/services/selected_source_context.py',
    'app/services/selected_source_dispatch.py','app/services/selected_stock_replay.py',
    'app/services/selected_kis_sources.py','app/services/selected_market_collection.py',
    'app/services/selected_source_preparation.py','app/services/selected_run_lifecycle.py',
    'app/services/scoped_monitoring_research.py','app/services/production_model_profile.py',
    'app/services/research_no_send_run.py','app/services/onboarding_readiness_service.py',
    'app/services/minimal_class_c_export.py','app/services/unified_persisted_projection.py',
    'app/services/prospective_class_c_owner.py','app/services/production_source_transport.py',
    'app/jobs/production_kis_worker.py','scripts/kr8_kis_integration.py',
    'app/services/canonical_source_replay.py')


def code_fingerprints():
    root=Path(__file__).resolve().parents[2]
    return {n:sha256_bytes((root/n).read_bytes()) for n in CODE}


class SelectedSourceRunBinding(SourceRunBinding):
    contract: Literal['selected-original-source-run-binding-v1']=CONTRACT
    execution_purpose: Literal['MANUAL_SHADOW_UNSENT','ROUTINE_US_NO_SEND_SOURCE']='MANUAL_SHADOW_UNSENT'
    master_id: str=Field(min_length=1)
    child_id: str=Field(min_length=1)
    market: Literal['us','kr']
    subjects: tuple[str,...]=Field(min_length=1,max_length=100)
    target_session: str
    request_plan_sha256: str=Field(pattern=r'^[a-f0-9]{64}$')
    registration_receipt_sha256: str=Field(pattern=r'^[a-f0-9]{64}$')
    selected_code_sha256: str=Field(pattern=r'^[a-f0-9]{64}$')
    fresh_stock_owner_set_sha256: str=Field(pattern=r'^[a-f0-9]{64}$')
    raw_owner_bindings: dict[str,str]
    us_night_policy: UsNightPolicy = 'ORIGINAL_CURRENT_PROBE_ONLY'

    @model_serializer(mode='wrap')
    def original_wire_unless_night_excluded(self, handler):
        value = handler(self)
        if self.us_night_policy == 'ORIGINAL_CURRENT_PROBE_ONLY':
            value.pop('us_night_policy', None)
        return value

    @property
    def universe(self):return {self.market:self.subjects}
    @property
    def fresh_mode(self):return True
    @property
    def us_only(self):return self.market=='us'
    @property
    def kr_only(self):return self.market=='kr'
    @property
    def cohort_metadata(self):return dict(contract=CONTRACT,execution_purpose=self.execution_purpose)

    @model_validator(mode='after')
    def selected_binding(self):
        if self.us_night_policy == US_NIGHT_OPTIONAL and self.market != 'us':
            raise ValueError('selected_us_optional_night_binding_mismatch')
        if self.us_night_policy == US_NIGHT_EXCLUDED and (
                self.market != 'us' or self.run_acquisitions.get('night') != digest(None)
                or self.night_publication_receipt_sha256 != digest(None)):
            raise ValueError('selected_us_night_exclusion_binding_mismatch')
        if self.execution_purpose == 'ROUTINE_US_NO_SEND_SOURCE' and self.market != 'us':
            raise ValueError('selected_routine_source_binding_us_only')
        session=(us_market_session if self.market=='us' else korea_market_session)(self.started_at)
        if (self.parent_run_id!=self.child_id or self.master_id==self.child_id
                or tuple(sorted(set(self.subjects)))!=self.subjects
                or self.target_session!=session.latest_completed_regular_session_date.isoformat()
                or set(self.raw_owner_bindings)!=set(self.subjects)
                or any(len(h)!=64 or any(c not in '0123456789abcdef' for c in h) for h in self.raw_owner_bindings.values())
                or self.universe_sha256!=digest(self.universe)):
            raise ValueError('selected_source_child_session_or_raw_binding')
        return self


def raw_owner_binding(inputs):
    financial=inputs['financial_inputs']
    binding=dict(technical=inputs['technical_inputs']['receipts'],financial=financial['receipts'])
    issuer=financial.get('issuer_business')
    if issuer and 'dependency' in issuer['source_inputs']:
        aux=issuer['source_inputs']
        binding['issuer_business']=dict(dependency=aux['dependency'], plan_sha256=digest(aux['plan']),
            owner_receipts_sha256=digest(aux['receipts']), official_identity_sha256=issuer['official_identity_sha256'])
    return digest(binding)


def selected_market_packet(native):
    """Compose exact original pages, including a separately bounded flow view."""
    import json
    from app.services.unified_source_composition import _resolve,read_bound_artifact
    from app.services.unified_aggregate_receipt import AggregateReceipt,verify_aggregate
    from app.services.unified_aggregate_owners import kiwoom_aggregate_owner
    from app.services.unified_kiwoom_observer import KiwoomRead
    packet=dict(run_id=native['run_id'],attempt_id=native['attempt_id'],
        attempt_started_at=native['start'].isoformat(),cutoff=native['cutoff'].isoformat(),component=_resolve(**native))
    if native['role'].market!='kr':return packet
    item=native['item'];owner=native['owners'][native['role'].owner]
    receipt=AggregateReceipt.model_validate(json.loads(read_bound_artifact(native['root'],
        item.receipt_artifact,item.receipt_sha256)))
    graph=verify_aggregate(native['root'],receipt,policy=native['policy'],cutoff=native['cutoff'],
        completion_observed_at=owner.page_completion_observed_at)
    reads=tuple(KiwoomRead.model_validate(r) for r in json.loads(graph.plan)['reads'])
    flows=kiwoom_aggregate_owner(role=native['role'],observed_at=datetime.fromisoformat(packet['component']['original_source_time']),
        max_pages=max(r.max_pages for r in reads),max_requests_per_page=1,policy=native['policy'],
        consumer_complete=True,aggregate_flows_only=True,selected_reads=reads)
    try:
        value=flows.project_aggregate_and_validate(graph,native['cutoff']).value
    except ValueError:
        packet['aggregate_flows']=dict(status='OPTIONAL_UNAVAILABLE',value=None,
            denial='AGGREGATE_FLOW_ROWS_NOT_QUALIFIED')
    else:
        packet['aggregate_flows']=dict(status='AVAILABLE_AGGREGATE_ONLY',value=value,
            original_receipt_sha256=item.receipt_sha256,owner_contract=flows.contract,
            original_source_time=packet['component']['original_source_time'],value_sha256=digest(value))
    return packet


def validate_composition(seed,*,stock_inputs,market_inputs,composition_metadata,fresh_context_inputs):
    seed=SelectedSourceRunBinding.model_validate(seed)
    if (composition_metadata is None or fresh_context_inputs is None
            or composition_metadata.get('selected_code_fingerprints')!=code_fingerprints()
            or digest(code_fingerprints())!=seed.selected_code_sha256
            or composition_metadata.get('selected_request_plan_sha256')!=seed.request_plan_sha256
            or composition_metadata.get('selected_registration_receipt_sha256')!=seed.registration_receipt_sha256
            or fresh_context_inputs['publications'].get('market_scope')!='SELECTED_'+seed.market.upper()
            or (fresh_context_inputs['night'] is None)!=(seed.market=='kr' or seed.us_night_policy==US_NIGHT_EXCLUDED)
            or set(stock_inputs)!=set(seed.subjects) or set(market_inputs)!={seed.market}):
        raise ValueError('selected_source_context_or_code_scope')
    for ticker,value in stock_inputs.items():
        if set(value)!={'fresh_financial_binding'}:
            raise ValueError('selected_original_fresh_binding_required')
        item=value['fresh_financial_binding'];tech=item['technical_inputs'];fin=item['financial_inputs']
        if (tech['plan'].planning_only or tech['plan'].universe!=seed.universe or tech['plan'].run_id!=seed.child_id
                or tech['plan'].frozen_at!=seed.started_at
                or any(r.latest_completed_session!=seed.target_session for r in tech['plan'].reads)
                or fin['plan']['run_id']!=seed.child_id
                or datetime.fromisoformat(fin['plan']['cutoff'])!=seed.started_at
                or fin['plan']['security']['canonical_security_id']!=next(r.canonical_security_id for r in tech['plan'].reads if r.subject==ticker)
                or raw_owner_binding(item)!=seed.raw_owner_bindings[ticker]):
            raise ValueError('selected_stock_raw_or_security_drift')
    native=market_inputs[seed.market].get('native_aggregate')
    if (native is None or native['run_id']!=seed.child_id or native['role'].market!=seed.market
            or native['role'].session!=seed.target_session):
        raise ValueError('selected_original_market_child_session')
    return seed


def build_inputs(root,frozen,outcome,policy,*,prospective_owners,master_id):
    from app.services.canonical_source_replay import stock_inputs,market_inputs,publication_inputs,read
    from app.services.canonical_source_inputs import fresh_authority_inputs
    from app.services.fresh_financial_stock_owner import assemble_fresh_stock
    from app.services.fresh_publication_replay import replay_fresh_publications
    from app.services.unified_sealed_context import replay_night
    from app.services.unified_source_composition import _resolve
    from app.services.selected_source_plan import decode_stock_plan,SCOPE
    from app.services.selected_source_registration import local_seed
    from app.services import prospective_class_c_owner as registration
    from app.services.whole_source_code_owner_registry import WholeSourceCodeOwnerRegistry
    if frozen.get('scope')!=SCOPE or not master_id:
        raise ValueError('selected_whole_explicit_scope_required')
    plan=decode_stock_plan(frozen)
    if plan.planning_only or set(prospective_owners or {})!={plan.market}:
        raise ValueError('selected_whole_current_registration_required')
    owner=prospective_owners[plan.market]
    local=local_seed(owner,stock=plan,policy=policy)
    _,reg=registration._state(owner)
    if frozen['registration_receipt_sha256']!=digest(reg):
        raise ValueError('selected_registration_frozen_receipt_drift')
    inputs,errors=stock_inputs(root,frozen,policy,outcome,prospective_owners=prospective_owners)
    if errors or set(inputs)!=set(plan.subjects):
        raise ValueError('selected_whole_original_stock_incomplete')
    markets=market_inputs(root,frozen,outcome,policy)
    context=publication_inputs(root,frozen,outcome,policy)
    excluded=us_night_excluded(frozen)
    optional=us_night_optional(frozen)
    pub=replay_fresh_publications(**context['publications'])
    night=None if context['night'] is None else replay_night(**context['night'])
    rows={t:assemble_fresh_stock(**i) for t,i in inputs.items()}
    native={m:selected_market_packet(v['native_aggregate']) for m,v in markets.items()}
    versions={f'class-c/local-{plan.market}.json':sha256_bytes(encoded(local)+b'\n')}
    root_code=Path(__file__).resolve().parents[2]
    inventory=read(root_code/'docs/operations/UNIFIED_ACQUISITION_CLASSES.json')
    registry=WholeSourceCodeOwnerRegistry.freeze(root_code,profile='fresh_us14' if plan.market=='us' else 'fresh_kr8')
    bridges=dict(bindings={t:s['issuer_business_bridge'] for t,s in rows.items() if s.get('issuer_business_bridge')},
        security_valuation_transfer=False,per_share_transfer=False)
    denials=dict(kr_market_investor_flows=dict(status='OPTIONAL_UNAVAILABLE',value=None,
        denial='DETAIL_NOT_CAPTURED_OR_COMPLETED_DATE_NOT_QUALIFIED',run_id=plan.run_id))
    if excluded:
        denials['night_futures']=excluded_night_receipt(plan.run_id)
    if native.get('kr',{}).get('aggregate_flows',{}).get('status')=='AVAILABLE_AGGREGATE_ONLY':
        denials['kr_market_investor_flows']=dict(status='AVAILABLE_AGGREGATE_ONLY',
            value_sha256=native['kr']['aggregate_flows']['value_sha256'],run_id=plan.run_id,
            concentration='UNAVAILABLE',stock_contribution='UNAVAILABLE')
    seed=SelectedSourceRunBinding(parent_run_id=plan.run_id,child_id=plan.run_id,master_id=master_id,
        execution_purpose=frozen.get('execution_purpose','MANUAL_SHADOW_UNSENT'),
        us_night_policy=US_NIGHT_EXCLUDED if excluded else US_NIGHT_OPTIONAL if optional else 'ORIGINAL_CURRENT_PROBE_ONLY',
        market=plan.market,subjects=plan.subjects,target_session=frozen['sessions'][plan.market],started_at=plan.frozen_at,
        source_policy_sha256=digest(sorted(policy.allowed_providers)),inventory_sha256=digest(inventory),
        **registry.seed_bindings,universe_sha256=digest(plan.universe),
        attempts={m:n['attempt_id'] for m,n in native.items()},attempt_hashes={m:digest(n) for m,n in native.items()},
        run_acquisitions=dict(stock=digest(plan.model_dump(mode='json')),publications=digest(pub),night=digest(None) if night is None else night['value_sha256']),
        class_c_version_set_sha256=digest(versions),stock_cohort_hashes={plan.market:digest(rows)},
        night_publication_receipt_sha256=digest(None) if night is None else digest(dict(probe=night['original_receipts'],history=night.get('history_receipts',[]))),
        optional_denial_set_sha256=digest(denials),skhy_issuer_bridge_sha256=digest(bridges),
        fresh_stock_owner_set_sha256=digest({t:digest(dict(technical_plan=plan.model_dump(mode='json'),financial_plan=i['financial_inputs']['plan'])) for t,i in inputs.items()}),
        request_plan_sha256=digest(frozen['plan']),registration_receipt_sha256=digest(reg),
        selected_code_sha256=digest(code_fingerprints()),raw_owner_bindings={t:raw_owner_binding(i) for t,i in inputs.items()})
    metadata=dict(inventory=inventory,allowed_providers=sorted(policy.allowed_providers),
        code_fingerprints=registry.fingerprints,code_owner_registry=registry.model_dump(mode='json'),
        selected_code_fingerprints=code_fingerprints(),selected_request_plan_sha256=digest(frozen['plan']),
        selected_registration_receipt_sha256=digest(reg))
    from app.services.latest_published_fx import display_receipt
    from app.services.market_session import korea_market_session
    metadata['fx_display_receipt']=display_receipt(pub,korea_market_session(plan.frozen_at).latest_completed_regular_session_date.isoformat())
    return dict(seed=seed,market_inputs=markets,stock_inputs={t:dict(fresh_financial_binding=i) for t,i in inputs.items()},
        authority_inputs={t:fresh_authority_inputs(rows[t],i) for t,i in inputs.items()},version_set=versions,
        optional_denials=denials,issuer_bridge=bridges,composition_metadata=metadata,fresh_context_inputs=context)


def project_market(packet,binding,graph,*,expected_authority_sha256):
    from app.services.canonical_market_projection import _project_market_context
    seed=SelectedSourceRunBinding.model_validate(binding)
    if graph.get('contract')!=GRAPH or set(graph['markets'])!={seed.market}:
        raise ValueError('selected_market_graph_contract_required')
    return _project_market_context(packet,seed.model_dump(mode='json'),graph,
        expected_authority_sha256=expected_authority_sha256,
        execution_metadata=dict(runtime_envelope_contract=CONTRACT,execution_purpose=seed.execution_purpose))
