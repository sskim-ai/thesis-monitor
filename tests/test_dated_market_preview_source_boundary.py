"""Focused C22M boundaries; simulated Cold at its exact I/O boundary only."""
from copy import deepcopy
import json
import pytest
from app.services.dated_research_model import digest
from app.services.dated_publication_previews import market_preview, _component_fields, check_lane_receipts


def sample(market='us'):
    value = dict(observations=[dict(series_code=s, unit='usd', market_session='us_regular',
        is_preliminary=False, observed_at='2026-11-05T00:00:00Z', change_pct=1.25,
        raw_payload=dict(return_basis='same_response_adjacent_adjusted_regular_closes')) for s in ('SPY','QQQ')])
    if market == 'kr':
        value = dict(indices=[dict(symbol='KOSPI',return_pct=1.5,source_ref='original:index')],
            breadth=dict(advance_count=3,decline_count=4,unchanged_count=1,eligible_count=8))
    return dict(market=market, full_market_parent=False,
        original_cold_status='ORIGINAL_COMPONENT_OWNER_COLD_PASS_NOT_FULL_PARENT',
        query_as_of='2026-11-05T21:10:00+00:00', completed_session='2026-11-05',value=value,
        original_bundle_sha256='a'*64, original_component_sha256='b'*64,value_sha256='c'*64)


def ledger(market='us'):
    return dict(market=market,candidate_session='2026-11-05',candidate_cutoff='2026-11-06T01:00:00+00:00',fields={})


def source(tmp_path, monkeypatch, reference):
    from app.services import dated_market_component_reference as original
    path=tmp_path/'bundle.json'
    path.write_text(json.dumps(dict(owner_proof=dict(qualification_cutoff='2026-11-05T21:15:00+00:00'))))
    monkeypatch.setattr(original,'read_dated_component',lambda *args,**kwargs:deepcopy(reference))
    return [dict(path=str(path),sha256=digest(path.read_bytes()))]


@pytest.mark.parametrize('mutation', ['fake','unit','future','value','owner'])
def test_external_pass_claim_cannot_become_original_field(tmp_path,monkeypatch,mutation):
    ref=sample(); bundles=source(tmp_path,monkeypatch,ref); l=ledger()
    row=_component_fields(ref,market='us',session=l['candidate_session'],cutoff=l['candidate_cutoff'],qualified_at='2026-11-05T21:15:00+00:00')['SPY_RETURN']
    if mutation=='fake': row['ref']='fake-ref'
    if mutation=='unit': row['unit']='USD'
    if mutation=='future': row['period']='2099-12-31'
    if mutation=='value': row['value']=999
    if mutation=='owner': row['original_owner_receipt_sha256']='e'*64
    l['fields']['SPY_RETURN']=row
    with pytest.raises(ValueError,match='original_owner_projection_required'):
        market_preview('us',ledger=l,source_bundles=bundles)


def test_no_original_replay_no_pass():
    l=ledger();l['fields']['US10Y']=dict(status='PASS',value=5.25,unit='%',period='2026-11-04',ref='fake')
    with pytest.raises(ValueError,match='original_owner_projection_required'): market_preview('us',ledger=l)


@pytest.mark.parametrize('market',['us','kr'])
def test_partial_original_fields_never_grant_market_judgment(tmp_path,monkeypatch,market):
    result=market_preview(market,ledger=ledger(market),source_bundles=source(tmp_path,monkeypatch,sample(market)))
    assert result['state']=='SOURCE_VERIFIED_FIELD_PREVIEW_ONLY'
    assert result['judgment'] is result['confidence'] is None
    assert result['full_market_parent'] is False
    assert 'PARTIAL_VERIFIED_FIELDS' in result['text'] and '자료 부족:' in result['text']


@pytest.mark.parametrize('kind',['session','cutoff','unit','parent'])
def test_original_component_semantics_and_binding_still_required(tmp_path,monkeypatch,kind):
    ref=sample();l=ledger()
    if kind=='session': l['candidate_session']='2026-11-06'
    if kind=='cutoff': l['candidate_cutoff']='2026-11-05T21:12:00+00:00'
    if kind=='unit': ref['value']['observations'][0]['unit']='index'
    if kind=='parent': ref['full_market_parent']=True
    with pytest.raises(ValueError): market_preview('us',ledger=l,source_bundles=source(tmp_path,monkeypatch,ref))


def test_failed_original_owner_cannot_be_replaced_by_external_json(tmp_path,monkeypatch):
    from app.services import dated_market_component_reference as original
    def reject(*args,**kwargs): raise ValueError('original_raw_receipt_mismatch')
    monkeypatch.setattr(original,'read_dated_component',reject)
    with pytest.raises(ValueError,match='original_raw_receipt_mismatch'):
        market_preview('us',ledger=ledger(),source_bundles=[dict(path=str(tmp_path/'fake'),sha256='f'*64)])


def test_original_ordered_child_contract_remains_ordered():
    p=dict(market='us',session='2026-11-05',cutoff='2026-11-06T01:00:00+00:00',fingerprint='p',child_hashes=['a','b'])
    c=[dict(market='us',session=p['session'],parent_fingerprint='p',available_at='2026-11-05T22:00:00+00:00',raw_sha256=x) for x in ('a','b')]
    assert check_lane_receipts(market='us',session=p['session'],cutoff=p['cutoff'],parent=p,children=c)['full_parent_issued'] is False
    with pytest.raises(ValueError,match='child_hash_mismatch'):
        check_lane_receipts(market='us',session=p['session'],cutoff=p['cutoff'],parent=p,children=c[::-1])


@pytest.mark.parametrize('case',['older_macro','wrong_unit','future_period','late_capture'])
def test_macro_vintage_uses_original_publication_owner(tmp_path,monkeypatch,case):
    from app.services import fresh_publication_replay as original
    from app.services.dated_publication_previews import _publication_fields
    def put(name,value):
        p=tmp_path/name;p.parent.mkdir(exist_ok=True);p.write_text(json.dumps(value));return digest(p.read_bytes())
    pins={'freeze.json':put('freeze.json',dict(started_at='2026-11-01T00:00:00+00:00',as_of='2026-11-01T01:00:00+00:00')),
        'capture.json':put('capture.json',dict(ended_at='2026-11-01T02:00:00+00:00'))}
    for p in ('fred','eia','ecos'):
        put(p+'/body.json',{})
        pins[p+'/capture-summary.json']=put(p+'/capture-summary.json',dict(receipts=[dict(run_id='test',artifact='body.json',artifact_sha256=digest(b'{}'))]))
    receipt=dict(received_at='2026-11-01T02:00:00+00:00',artifact_sha256=digest(b'{}'))
    row=dict(series_code='DGS10',unit='percent',value=4.5,observed_at='2026-10-30T00:00:00+00:00',
        raw_payload=dict(publication_context=dict(display_eligible=True,direction_eligible=False,response_sha256=digest(b'{}'))))
    if case=='wrong_unit':row['unit']='USD'
    if case=='future_period':row['observed_at']='2099-12-31T00:00:00+00:00'
    if case=='late_capture':receipt['received_at']='2099-12-31T00:00:00+00:00'
    monkeypatch.setattr(original,'replay_fresh_publications',lambda **kwargs:dict(providers={'fred':dict(value={'observations':[row]},original_receipts=[receipt],value_sha256='d'*64)}))
    capture=dict(root=str(tmp_path),files=pins)
    if case=='older_macro':
        value=_publication_fields(capture,market='us',cutoff='2026-11-05T00:00:00+00:00')['US10Y']
        assert value['period']=='2026-10-30' and value['is_session_price'] is False
    else:
        with pytest.raises(ValueError):_publication_fields(capture,market='us',cutoff='2026-11-05T00:00:00+00:00')
