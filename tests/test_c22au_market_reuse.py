"""Market-only continuity on the original local seal; no live Stock authority."""
from copy import deepcopy
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.accepted_market_replay import AcceptedMarketOrigin, verify_market_replay
from app.services.model_execution_plan import CohortSubject, FrozenCohort, compile_model_plan
from app.services.production_monitoring_session import ProductionMonitoringSession
from app.services.research_no_send_run import PreparedResearchBridge
from app.services.research_request_storage import load_stage_request
from app.services.unified_snapshot_contract import digest


@pytest.fixture(scope='module')
def archived():
    local = os.environ.get('C22AU_ARCHIVED_MARKET')
    if not local:
        pytest.skip('Explicit local archived MARKET fixture required')
    root = Path(local)
    old_run = 'C22AQ_KR_EXEC_20261112T130813Z'
    directory = root/'recovery-1/private-live/no-send'/old_run/'market'
    origin = AcceptedMarketOrigin(root/'TM_C22AQ_V1_RECOVERY1_RESULT_20261112.zip',
        'de3b3607f1c21d1c506c898e5aed31d925ae34a59801ccfc39c458abba343794',
        directory, Path('/private/tmp/c22aq-sol-high-20261112T130813Z/invocation-ledger')/old_run/'events.jsonl')
    response = json.loads((directory/'response.json').read_bytes())
    request = load_stage_request(directory/'request.json',expected_logical_sha256=response['request_sha256'])
    item = json.loads((directory/'canonical/sealed/requests/market/kr/batch-01/request-receipt.json').read_bytes())
    return origin, request['snapshot'], item


def new_snapshot(snapshot, source, *, changed_cohort):
    old = snapshot['child_binding']
    run = 'C22AU_OFFLINE_MARKET_ONLY'
    subjects = snapshot['collection']['production_envelope']['subjects']
    binding = dict(old,run_id=run,consumed_source_sha256=digest(source))
    cohort = None
    if changed_cohort:
        # A test double only for the current owner boundary. No real CORE or authority.
        cohort = FrozenCohort(run,old['source_generation'],old['assessment_date'],old['effective_at'],old['cutoff'],
            tuple(CohortSubject('kr',t,'offline:'+t,old['cutoff'],digest(t)) for t in subjects),
            (('kr',digest('test-only')),),digest('test-only-feature-scope'))
        binding.update(cohort_sha256=cohort.sha256,
            plan_sha256=compile_model_plan(cohort,topology='CANONICAL_PRODUCTION').sha256)
    return dict(child_binding=binding,collection=dict(monitoring_input=source,
        production_envelope=dict(subjects=subjects,generation_id=run))),cohort


def test_only_stock_receipt_drift_reuses_original_market(archived):
    origin, old, item = archived
    source = deepcopy(old['collection']['monitoring_input'])
    source['coverage']['offline_custody_change'] = 'test-only'
    source['census']['offline_custody_change'] = 'test-only'
    ticker = next(iter(source['stocks']))
    source['stocks'][ticker]['baseline_sha256'] = digest('changed')
    source['prepared'][ticker]['offline_custody_change'] = 'test-only'
    view = source['markets']['kr']['views']['display']['origin']
    view.update(authority_sha256=digest('new stock graph'),source_packet_sha256=digest('new packet'))
    new,cohort = new_snapshot(old,source,changed_cohort=True)
    calls = []
    session = SimpleNamespace(source=source,gen=new['child_binding']['run_id'],market='kr',
        source_gen=cohort.source_generation,_frozen_cohort=cohort,_verify_native_source=lambda:calls.append('checked'))
    row,lineage = verify_market_replay(origin,snapshot=new,session=session,item=item)
    assert calls==['checked'] and row['raw_sha256']==lineage['output_sha256']
    assert lineage['new_model_invocations']==0 and lineage['origin_execution']!=lineage['continuation_execution']
    session._frozen_cohort = None
    with pytest.raises(ValueError,match='current_cohort_source_required'):
        verify_market_replay(origin,snapshot=new,session=session,item=item)


@pytest.mark.parametrize('change,reason',[
    ('component_sha256','market_input_source_drift'),
    ('directional_refs','market_input_source_drift'),
    ('cutoff','origin_scope_drift'),
    ('snapshot_sha','consumed_source_hash_drift'),
    ('owner','test_owner_not_current'),
    ('prompt','canonical_acceptance_or_payload_drift'),
    ('journal','origin_journal_drift'),
])
def test_market_or_current_owner_drift_still_rejected(archived,tmp_path,change,reason):
    origin, old, item = archived
    source = deepcopy(old['collection']['monitoring_input'])
    if change in ('component_sha256','directional_refs'):
        display_origin = source['markets']['kr']['views']['display']['origin']
        display_origin[change] = 'f'*64 if change=='component_sha256' else []
    new,cohort = new_snapshot(old,source,changed_cohort=True)

    def check_source():
        if change=='owner':
            raise ValueError('test_owner_not_current')

    session = SimpleNamespace(source=source,gen=new['child_binding']['run_id'],market='kr',
        source_gen=cohort.source_generation,_frozen_cohort=cohort,_verify_native_source=check_source)
    if change=='cutoff':
        new['child_binding']['cutoff']='2026-11-13T00:00:00+00:00'
    elif change=='snapshot_sha':
        new['child_binding']['consumed_source_sha256']='0'*64
    elif change=='prompt':
        item = dict(item,payload=dict(item['payload'],prompt='Changed MARKET prompt'))
    elif change=='journal':
        from dataclasses import replace
        bad = tmp_path/'other.jsonl'
        bad.write_text('{}\n')
        origin = replace(origin,invocation_journal=bad)
    with pytest.raises(ValueError,match=reason):
        verify_market_replay(origin,snapshot=new,session=session,item=item)


def test_original_market_acceptance_to_final_renderer(archived,tmp_path):
    origin, old, _ = archived
    source = old['collection']['monitoring_input']
    new,_ = new_snapshot(old,source,changed_cohort=False)
    session = ProductionMonitoringSession(tmp_path,market='kr',generation_id=old['child_binding']['run_id'],
        source=source,source_generation_id=old['child_binding']['source_generation'])
    # No stock methods are called with this historical view.
    session.gen = new['child_binding']['run_id']
    item, = session.build('MARKET')
    accepted,_ = verify_market_replay(origin,snapshot=new,session=session,item=item)
    session.accept('MARKET',item,accepted['output'])
    body = origin.seal.parent.parent/'20261112-c22ao-v1/private-live/source/kr/dispatch/raw/ecos:USDKRW/source.body'
    bridge = object.__new__(PreparedResearchBridge)
    bridge._retained_kr_ecos_body = body.read_text()
    message = bridge._render_market(session)
    assert message['message_id']=='MARKET_KR'
    assert all(x in message['text'] for x in ('1,330.70','837.45','1,483.47','비교 자료 미확보',
        'KOSPI 상대 강세 TOP3','KOSDAQ 상대 약세 BOTTOM3'))
