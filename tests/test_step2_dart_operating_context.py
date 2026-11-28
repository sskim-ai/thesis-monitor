"""OpenDART primary-statement context, including an issuer outside the operating roster."""
from copy import deepcopy
from datetime import timedelta
import json

import pytest

from app.services.bounded_financial_projection import reported_filing_context
from app.services.canonical_monitoring_input import economic_context, filing_observations, pass_a_filing_context
from app.services.detailed_stock_message_v2 import _cited_filing_rows
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest


PLAN = dict(provider='opendart', market='kr', ticker='654321', issuer='12345678', cutoff='2026-08-15T09:00:00+09:00',
            security=dict(canonical_company_id='example-issuer', canonical_security_id='example-common'))
FILING = dict(role='current', business_year=2026, report_code='11012', receipt_no='20260814001234',
              receipt_date='2026-08-14', report_name='[기재정정]반기보고서 (2026.06)',
              ticker=PLAN['ticker'], corp_code=PLAN['issuer'])
DOCUMENT = dict(artifact='current.body', filing=dict(role='current', basis='CFS', receipt_no=FILING['receipt_no']))
RND = dict(rcept_no=FILING['receipt_no'], corp_code=PLAN['issuer'], bsns_year='2026', reprt_code='11012',
           sj_div='CIS', account_id='ifrs-full_ResearchAndDevelopmentExpense', account_nm='연구개발비',
           account_detail='-', ord='8', currency='KRW', thstrm_amount='42,500', frmtrm_q_amount='15,000',
           thstrm_add_amount='92,500', frmtrm_add_amount='31,000')
BALANCE = dict(RND, sj_div='BS', account_id='ifrs-full_CurrentContractAssets', account_nm='유동계약자산',
               thstrm_amount='200', frmtrm_amount='180')


def project(root, rows, *, filing=FILING, docs=None, status='000', plan=PLAN):
    raw = json.dumps(dict(status=status, list=rows), ensure_ascii=False).encode()
    (root/'current.body').write_bytes(raw)
    return reported_filing_context(plan, dict(selected_filings=[filing], documents=[DOCUMENT] if docs is None else docs),
                                   root, [dict(artifact='current.body', raw_sha256=sha256_bytes(raw))])


def view(rows):
    packet = dict(stocks=[dict(ticker=PLAN['ticker'], reported_filing_context=rows, fact_catalog=[dict(
        fact_id='comparison:parent', fact_type='earnings_comparison', fields=dict(source_receipt=FILING['receipt_no']))])])
    return dict(ticker=PLAN['ticker'], packet=packet, projection=dict(fields=[]),
                valuation_view=dict(security_id=PLAN['security']['canonical_security_id']),
                selected_financial_owner=dict(owner_type='direct_opendart', issuer_identity=PLAN['issuer'],
                    monitored_security=PLAN['ticker'], selected_projection_sha256=digest(dict(fields=[]))))


def test_unregistered_example_reports_quarter_and_balance_without_extra_claims(tmp_path):
    rows = project(tmp_path, [RND, BALANCE, dict(RND, account_detail='제품 A', thstrm_amount='10'), RND])
    assert len(rows) == 3
    source = view(rows)
    economic = economic_context(source, dict(decision_evidence=[], source_use_projection=dict(source_permissions=[])), {})
    assert economic['relationships'] == []
    assert [r['ref_id'] for r in rows] == [r['ref_id'] for r in economic['observations']]
    amounts = [r['observation'] for r in rows]
    assert [(f['value'], f['period_start'], f['period_end'], f['source_column']) for f in amounts] == [
        (42500, '2026-04-01','2026-06-30','thstrm_amount'), (200,'2026-06-30','2026-06-30','thstrm_amount'),
        (15000,'2025-04-01','2025-06-30','frmtrm_q_amount')]
    assert all(f['unit']=='KRW' and f['statement_basis']=='consolidated' and not f['direction_eligible'] for f in amounts)
    ref = rows[1]['ref_id']
    ctx = dict(economic_context=economic)
    rendered, = _cited_filing_rows(ctx, dict(valuation_context=dict(business_evidence_refs=[ref])), source)
    assert '유동 계약자산 200 KRW' in rendered.text and '2026-06-30 기준' in rendered.text
    assert rendered.numeric_registry_keys == (ref+':fields.current_contract_assets',)
    assert not _cited_filing_rows(ctx, dict(valuation_context=dict(business_evidence_refs=[])), source)
    allowed = dict(eligible_non_price_evidence=[dict(ref_id='canonical:comparison:parent')],
                   source_use_projection=dict(source_permissions=[dict(ref_id='canonical:comparison:parent',
                                                                      allowed_uses=['PASS_A_ARCHETYPE'])]))
    assert pass_a_filing_context(source, allowed) == economic['observations']
    allowed['source_use_projection']['source_permissions'][0]['prohibited_uses'] = ['PASS_A_ARCHETYPE']
    assert not pass_a_filing_context(source, allowed)


@pytest.mark.parametrize('bad', [
    dict(currency='USD'), dict(account_detail='사업부'), dict(sj_div='SCE'), dict(sj_div='CF'),
    dict(account_id='entity_CustomRAndD'), dict(thstrm_amount='NaN'), dict(thstrm_amount='10,42'),
    dict(corp_code='87654321'), dict(rcept_no='20260813000001'), dict(bsns_year='2025'),
    dict(reprt_code='11011'), dict(fs_div='OFS'),
])
def test_unqualified_rows_do_not_reach_model(tmp_path, bad):
    assert project(tmp_path, [dict(RND, **bad)]) == []


def test_ambiguous_missing_and_noncalendar_documents_have_no_extra_context(tmp_path):
    assert not project(tmp_path, [RND, dict(RND, thstrm_amount='398')])
    assert [r['observation']['value'] for r in project(tmp_path, [RND, dict(RND, frmtrm_q_amount='399')])] == [42500]
    assert not project(tmp_path, [RND], filing=dict(FILING, report_name='반기보고서 (2026.09)'))
    assert not project(tmp_path, [RND], filing=dict(FILING, receipt_date='2026-08-16'))
    assert not project(tmp_path, [RND], docs=[dict(DOCUMENT,filing=dict(DOCUMENT['filing'],basis='OFS'))])
    assert not project(tmp_path, [RND], docs=[dict(DOCUMENT,filing=dict(DOCUMENT['filing'],role='prior'))])
    assert not project(tmp_path, [RND], docs=[DOCUMENT, DOCUMENT])
    assert not project(tmp_path, [], status='013')
    annual = dict(FILING, report_name='사업보고서 (2025.12)',business_year=2025,report_code='11011')
    amounts = project(tmp_path, [dict(RND,bsns_year='2025',reprt_code='11011',frmtrm_amount='3400')], filing=annual)
    assert [(f['observation']['source_column'], f['observation']['period_role']) for f in amounts] == [
        ('thstrm_amount','full_year'),('frmtrm_amount','full_year')]


def test_opendart_context_stays_on_direct_issuer_and_registered_amount(tmp_path):
    rows = project(tmp_path, [RND])
    source = view(rows)
    assert len(filing_observations(source)) == 2
    for change in [dict(owner_type='issuer_business_bridge'),dict(bridge_receipt={'underlying':'654321'}),
                   dict(owner_type='direct_sec'),dict(issuer_identity='another'),dict(selected_projection_sha256='other')]:
        altered = deepcopy(source)
        altered['selected_financial_owner'].update(change)
        assert not filing_observations(altered)
    source['valuation_view']['security_id'] = 'other-listed-security'
    assert not filing_observations(source)
    rows[0]['numeric_registry_entry']['value'] += 1
    assert [r['ref_id'] for r in filing_observations(view(rows))] == [rows[1]['ref_id']]


def test_kr_regular_source_routes_context_through_canonical_core_a_b(tmp_path, monkeypatch):
    from app.services import canonical_subject_preflight as preflight
    from app.services.canonical_monitoring_source import prepare_monitoring_subject
    from app.services.canonical_source_inputs import fresh_authority_inputs
    from app.services.fresh_financial_stock_owner import assemble_fresh_stock
    from scripts.m12dr_financial_source_authority import build_source_authority
    from tests.rev8_source_fixtures import fresh_inputs
    from tests.rev10_source_fixtures import wire_clock
    from tests.test_reported_business_native_projection import window
    from tests.test_unified_stock_acquisition import plan as fixture_plan

    plan = fixture_plan.__wrapped__()
    with wire_clock(plan.frozen_at+timedelta(seconds=4)):
        inputs = fresh_inputs(tmp_path, '005930', verified_identity=True, plan=plan, dart_operating_rows=[
            dict(sj_div='CIS', account_id=RND['account_id'], account_nm='연구개발비', ord='17',
                 thstrm_amount='42500', frmtrm_q_amount='15000')])
    inputs.update(reported_comparison_business=True, source_window=window(plan))
    stock = assemble_fresh_stock(**inputs)
    refs = [r['ref_id'] for r in stock['packet']['stocks'][0]['reported_filing_context']]
    assert len(refs)==2
    authority = build_source_authority(**fresh_authority_inputs(stock, inputs))
    assert not set(refs) & {r['ref_id'] for r in authority['authority']['authority_records']}
    a_original, b_original = preflight.a_input, preflight.b_input
    observed = {}
    def a_input(*args, **kwargs):
        gate = a_original(*args, **kwargs)
        observed['a'] = [r['ref_id'] for r in gate['model_context']['filing_context_only']]
        return gate
    def b_input(*args, **kwargs):
        result = b_original(*args, **kwargs)
        observed['b'] = [r['ref_id'] for r in result[0]['economic_context']['observations']
                         if r['kind']=='REPORTED_OPERATING_CONTEXT_ONLY']
        return result
    monkeypatch.setattr(preflight, 'a_input', a_input)
    monkeypatch.setattr(preflight, 'b_input', b_input)
    readiness, prepared = prepare_monitoring_subject(stock=stock, authority=authority,
        local_seed=inputs['technical_inputs']['local_seed'],generation=plan.run_id)
    assert readiness['status']=='PASS'
    core = [r['ref_id'] for r in prepared['core_input']['economic_context']['observations']
            if r['kind']=='REPORTED_OPERATING_CONTEXT_ONLY']
    assert core == observed['a'] == observed['b'] == refs
