"""Fetch nomination is separate from economic period and financial authority."""
import asyncio
from copy import deepcopy
from datetime import datetime, timezone

import httpx
import pytest

from app.services.bounded_financial_acquisition import collect, make_plan, sec_selection
from app.services.bounded_financial_projection import project, verify_capture
from app.services.sec_current_financial_candidates import NOMINATED_CONTRACT
from app.services.sec_fpi_financial_purpose import candidate_inventory, classify_document
from app.services.sealed_financial_reader import SealedFinancialReader
from app.services.sealed_financial_slots import financial_slots
from app.services.sealed_response_binding import ResponseBinding
from app.services.unified_snapshot_contract import digest, encoded
from tests.test_r9_rev11_response_slots import run_slots
from tests.test_r9_rev11_sealed_dispatch import CONFIG, OWNER


def fixture(cik='123', ticker='UNSEEN'):
    identity = dict(ticker=ticker, canonical_company_id='issuer', canonical_security_id='security',
        identity_provider='local', cik=cik, issuer_type='foreign_private_issuer')
    kwargs = dict(market='us', cutoff=datetime(2026, 10, 21, tzinfo=timezone.utc),
                  run_id='fresh-1', exact_financial_owner=True)
    p = make_plan(identity, **kwargs)
    f = dict(form='6-K', accessionNumber=f'{int(cik):010d}-26-000001',
             primaryDocument='source.htm', filingDate='2026-08-18', reportDate='2026-08-18')
    newer = {**f, 'accessionNumber': f'{int(cik):010d}-26-000002',
             'primaryDocument': 'later.htm', 'filingDate': '2026-10-14', 'reportDate': '2026-10-14'}
    nomination = dict(issuer=p['issuer'], run_id=p['run_id'], cutoff=p['cutoff'],
        base_plan_sha256=digest(p), historical_discovery_sha256='a'*64,
        historical_receipt_sha256='b'*64, authorizing_instruction_sha256='c'*64, filings=[f])
    payload = dict(cik=cik, filings=dict(recent={k:[f[k], newer[k]] for k in f}, files=[]))
    return identity, kwargs, p, nomination, payload


def nominated(cik='123', ticker='UNSEEN'):
    identity, kwargs, _, n, payload = fixture(cik, ticker)
    return make_plan(identity, **kwargs, fpi_nomination=n), payload


@pytest.mark.parametrize('cik,ticker', [('123','UNSEEN'), ('456','OTHER_FPI'), ('789','ADS_TEST')])
def test_exact_metadata_nomination_without_economic_authority(cik, ticker):
    p, payload = nominated(cik, ticker)
    chosen = sec_selection(payload, p)
    inv = candidate_inventory(payload, p)
    assert len(chosen) == 1 and chosen[0]['reportDate'] == '2026-08-18'
    assert p['maximum_logical_requests'] == 14
    assert inv['current_financial_plan']['contract'] == NOMINATED_CONTRACT
    assert inv['current_financial_plan']['outside_bound'][0]['purpose'] == 'NOT_INSPECTED_PURPOSE_UNKNOWN'
    assert inv == candidate_inventory(deepcopy(payload), deepcopy(p))
    doc = classify_document(b'<html>unknown</html>',
        url=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{chosen[0]['accessionNumber'].replace('-', '')}/source.htm",
        filing=chosen[0], plan=p)
    assert doc['purpose'] == 'UNKNOWN_PURPOSE' and not doc['financial_authority']
    assert not doc['economic_periods']


@pytest.mark.parametrize('field,value', [('issuer','0000000999'), ('run_id','wrong'), ('cutoff','2026-10-20'),
    ('base_plan_sha256','0'*64), ('historical_discovery_sha256','invalid'),
    ('historical_receipt_sha256',''), ('authorizing_instruction_sha256','invalid'),
    ('purpose','CORE_DIRECTION')])
def test_nomination_binding_rejects(field, value):
    identity, kwargs, _, n, _ = fixture()
    n[field] = value
    with pytest.raises(ValueError):
        make_plan(identity, **kwargs, fpi_nomination=n)


@pytest.mark.parametrize('field,value', [('accessionNumber','0000000123-26-999999'),
    ('primaryDocument','other.htm'), ('filingDate','2026-08-19'), ('reportDate','2026-06-30'), ('form','6-K/A')])
def test_nomination_exact_current_membership(field, value):
    identity, kwargs, _, n, payload = fixture()
    n['filings'][0][field] = value
    p = make_plan(identity, **kwargs, fpi_nomination=n)
    with pytest.raises(ValueError, match='nomination_not_exact_current_discovery_member'):
        sec_selection(payload, p)


@pytest.mark.parametrize('mutation', ['duplicate','too_many','path','outside','form','unknown_contract','wrong_payload_cik'])
def test_bounds_and_source_identity(mutation):
    identity, kwargs, _, n, payload = fixture()
    if mutation == 'duplicate': n['filings'] *= 2
    if mutation == 'too_many': n['filings'] *= 3
    if mutation == 'path': n['filings'][0]['primaryDocument'] = '../outside.htm'
    if mutation == 'outside': n['filings'][0]['filingDate'] = '2024-01-01'
    if mutation == 'form': n['filings'][0]['form'] = '10-Q'
    with pytest.raises(ValueError):
        p = make_plan(identity, **kwargs, fpi_nomination=n)
        if mutation == 'unknown_contract': p['fpi_candidate_contract'] = 'forged'
        if mutation == 'wrong_payload_cik': payload['cik'] = '456'
        sec_selection(payload, p)


def test_original_sealed_collect_and_replay(tmp_path):
    p, payload = nominated()
    slots = financial_slots(p, owner='test-owner', owner_sha256=OWNER, config_sha256=CONFIG)
    run = run_slots(tmp_path, slots)
    calls = []
    def respond(req):
        calls.append(str(req.url))
        if 'submissions' in req.url.path: return httpx.Response(200, json=payload)
        if 'companyfacts' in req.url.path: return httpx.Response(200, json={'cik':'123','facts':{}})
        if req.url.path.endswith('index.json'): return httpx.Response(200, json={'directory':{'item':[]}})
        return httpx.Response(200, content=b'<html>unknown purpose, no financial authority</html>')
    reader = SealedFinancialReader(p, tmp_path/'native', dispatcher=run,
        transport=httpx.MockTransport(respond), user_agent='PLAN_CREDENTIAL')
    capture = asyncio.run(collect(reader))
    verify_capture(p, capture, reader.output, reader.receipts)
    result = project(p, capture, reader.output, reader.receipts, field_semantics=True)
    assert result == project(p, capture, reader.output, reader.receipts, field_semantics=True)
    assert len(calls) == 4 and 'companyfacts' in calls[1]
    assert len(slots) == 14 and len(run.results) == 4
    assert not result['comparisons']
    assert result['fpi_purpose']['uncaptured_window'][0]['filingDate'] == '2026-10-14'
    altered = deepcopy(capture)
    altered['current_candidate_plan']['candidates'] = []
    with pytest.raises(ValueError, match='candidate_plan_replay'):
        project(p, altered, reader.output, reader.receipts, field_semantics=True)
    (run.root/slots[0].raw_path).write_bytes(b'{}')
    with pytest.raises(ValueError, match='artifact_hash_mismatch'):
        run.resolve(slots[2].logical_request_id)


def test_response_binding_reconstructs_exact_nomination_and_rejects_widened_limits():
    p, _ = nominated()
    ResponseBinding(kind='SEC_PRIMARY', parents=('discovery',), policy_json=encoded(p).decode(), policy_sha256=digest(p))
    p['limits']['current'] += 1
    with pytest.raises(ValueError):
        ResponseBinding(kind='SEC_PRIMARY', parents=('discovery',), policy_json=encoded(p).decode(), policy_sha256=digest(p))


def test_legacy_frozen_plan_retains_original_replay():
    _, _, p, _, payload = fixture()
    assert sec_selection(payload, p) == []


def test_two_interim_plus_one_annual_and_no_additional_window():
    from app.services.bounded_fpi_followup import make_followup_plan
    from app.services.fpi_coverage_window import make_window_plan
    identity, kwargs, _, n, payload = fixture()
    recent = payload['filings']['recent']
    n['filings'].append({k:v[1] for k,v in recent.items()})
    annual = dict(form='20-F', accessionNumber='0000000123-26-000003',
                  primaryDocument='annual.htm', filingDate='2026-03-15', reportDate='2025-12-31')
    for k in recent: recent[k].append(annual[k])
    p = make_plan(identity, **kwargs, fpi_nomination=n)
    assert len(sec_selection(payload, p)) == 3
    followup = make_followup_plan(p, encoded(payload), [])
    assert followup['limits']['current'] == 3 and len(followup['exact_requests']) == 6
    with pytest.raises(ValueError, match='no_additional_coverage_window'):
        make_window_plan(p, encoded(payload), [], None, None)


@pytest.mark.parametrize('status', [403])
def test_companyfacts_denial_stops_before_index(tmp_path, status):
    from app.services.bounded_financial_acquisition import SystemicStop
    p, payload = nominated()
    slots = financial_slots(p, owner='test-owner', owner_sha256=OWNER, config_sha256=CONFIG)
    run = run_slots(tmp_path, slots)
    calls=[]
    def respond(req):
        calls.append(str(req.url))
        if 'submissions' in req.url.path: return httpx.Response(200,json=payload)
        return httpx.Response(status,content=b'Access denied')
    reader = SealedFinancialReader(p,tmp_path/'native',dispatcher=run,
        transport=httpx.MockTransport(respond),user_agent='PLAN_CREDENTIAL')
    with pytest.raises(SystemicStop): asyncio.run(collect(reader))
    assert len(calls)==2 and 'companyfacts' in calls[-1]


@pytest.mark.parametrize('reverse', [False,True])
def test_duplicate_annual_accession_is_not_input_order_authority(reverse):
    p,payload=nominated()
    annual=dict(form='20-F',accessionNumber='0000000123-26-000003',primaryDocument='one.htm',
                filingDate='2026-03-15',reportDate='2025-12-31')
    rows=[annual,{**annual,'primaryDocument':'two.htm'}]
    if reverse: rows.reverse()
    for row in rows:
        for k in row: payload['filings']['recent'][k].append(row[k])
    with pytest.raises(ValueError,match='duplicate_accession'): sec_selection(payload,p)
