"""Synthetic raw fixtures for real owner-path integration; never live evidence."""

import asyncio
from datetime import date, timedelta

import httpx
from sqlmodel import Session, SQLModel, create_engine

from app.models.security import SecurityMaster
from app.models.thesis import InvestmentThesis
from app.models.watchlist import WatchlistItem
from app.services.bounded_financial_acquisition import BoundedReader, collect, make_plan
from app.services.unified_class_c_owners import project_local_seed
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_source_policy import UnifiedSourcePolicy
from app.services.unified_stock_anomaly_scope import materialize_source_components
from tests.test_bounded_financial_acquisition import filing, submission
from tests.test_external_api_accuracy import _companyfact_entry, _companyfacts_payload
from tests.test_residual_financial_semantics import html_statement
from tests.test_unified_stock_acquisition import plan as stock_plan_fixture
from tests.test_unified_stock_anomaly_scope import bars
from tests.test_unified_stock_owner import freeze_hashes


POLICY = UnifiedSourcePolicy(frozenset({'kiwoom', 'local', 'canonical_local', 'sec_edgar', 'sec_companyfacts',
                                      'sec_foreign_filing', 'opendart', 'sec_official_identity'}))


def fresh_inputs(root, ticker, *, current_only=False, conflict=False, insurance=False,
                 verified_identity=False, policy=POLICY, security_overrides=None, empty_financial=False):
    plan = stock_plan_fixture.__wrapped__()
    reads = [r for r in plan.reads if r.subject == ticker]
    market, session_key = reads[0].market, reads[0].latest_completed_session
    foreign = ticker in {'TSM', 'WRD', 'SKHY'}
    security = SecurityMaster(ticker=ticker, company_name='Synthetic ' + ticker,
        canonical_company_id='synthetic-issuer-' + ticker, canonical_security_id='security-' + ticker,
        exchange='NASDAQ' if market == 'us' else 'KRX', country='US' if market == 'us' else 'KR',
        cik='1234' if market == 'us' else None, corp_code='00123456' if market == 'kr' else None,
        issuer_type='foreign_private_issuer' if foreign else 'domestic_us' if market == 'us' else 'domestic_kr',
        security_type='common_stock', identity_provider='sec_edgar' if market == 'us' else 'opendart',
        identity_quality='verified' if verified_identity else 'partial',
        updated_at=plan.frozen_at)
    if security_overrides:
        security = SecurityMaster.model_validate({**security.model_dump(), **security_overrides})
    engine = create_engine('sqlite://')
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(security)
        session.add(WatchlistItem(ticker=ticker, company_name=security.company_name,
            exchange=security.exchange, created_at=plan.frozen_at, activated_at=plan.frozen_at))
        session.add(InvestmentThesis(ticker=ticker, version=1, core_thesis='Synthetic configured business',
                                     created_at=plan.frozen_at))
        session.commit()
        local = project_local_seed(session, market=market, session_key=session_key,
                                    cutoff=plan.frozen_at, policy=policy)
        identity = security.model_dump(mode='json')
    engine.dispose()
    receipts, artifacts, roles = {}, {}, {}
    for read in reads:
        rows = bars(400)
        delta = date.fromisoformat(session_key) - date.fromisoformat(rows[-1]['date'])
        for row in rows:
            row['date'] = (date.fromisoformat(row['date']) + delta).isoformat()
        roles[read.role] = rows
        raw, normalized = encoded({'return_code': 0, 'result_list': rows}), encoded(rows)
        name = read.role
        artifacts[name + '.body'], artifacts[name + '.json'] = raw, normalized
        request = dict(method='POST', route=read.route, api_id=read.api_id,
            payload=dict(stk_cd=ticker, upd_stkpc_tp=str(int(read.adjusted)), stex_tp=read.exchange))
        page = dict(provider='kiwoom', entry_id=read.entry_id, page_ordinal=1, request=request,
            request_sha256=digest(request), requested_at=(plan.frozen_at + timedelta(seconds=1)).isoformat(),
            received_at=(plan.frozen_at + timedelta(seconds=2)).isoformat(), artifact=name + '.body',
            source_sha256=sha256_bytes(raw), http_status=200)
        receipts[name] = dict(run_id=plan.run_id, acquisition_id=plan.acquisition_id,
            plan_sha256=digest(plan.model_dump(mode='json')), entry=read.model_dump(mode='json'),
            started_at=plan.frozen_at.isoformat(), completed_at=(plan.frozen_at + timedelta(seconds=3)).isoformat(),
            status='CAPTURED', pages=[page], normalized_artifact=name + '.json', normalized_sha256=sha256_bytes(normalized))
    components = materialize_source_components(ticker=ticker, market=market,
        cutoff=date.fromisoformat(session_key), observed_at=plan.frozen_at.isoformat(), roles=roles)
    technical = freeze_hashes(dict(plan=plan, ticker=ticker, receipts=receipts, artifacts=artifacts,
        local_seed=local, financial=None, components=components, policy=policy))
    fp = make_plan(identity, market=market, cutoff=plan.frozen_at, run_id=plan.run_id, all_subjects_fresh=True)
    f = filing('6-K' if foreign else '10-Q')
    f['accessionNumber'] = '0000001234-26-000001'
    row = {**_companyfact_entry(30, fp='Q2', start='2026-04-01', end='2026-06-30', filed='2026-08-01'),
           'accn': f['accessionNumber']}
    amount_rows = [row] if current_only else [row, dict(row, start='2025-04-01', end='2025-06-30', val=20)]
    concepts = {'Revenues': [dict(r, val=100 if r['start'].startswith('2026') else 80) for r in amount_rows],
                'OperatingIncomeLoss': amount_rows}
    if conflict:
        concepts['RevenueFromContractWithCustomerExcludingAssessedTax'] = [dict(r, val=10) for r in amount_rows]
    companyfacts = _companyfacts_payload('us-gaap', concepts)
    companyfacts['cik'] = 1234
    dart_rows = []
    for i, (account, label, amount, prior) in enumerate([
        ('ifrs-full_InsuranceRevenue' if insurance else 'ifrs-full_Revenue', '매출액', 100, 80), ('dart_OperatingIncomeLoss', '영업이익', 20, 15),
        ('ifrs-full_ProfitLoss', '당기순이익', 10, 8)]):
        dart_rows.append(dict(corp_code=fp['issuer'], rcept_no='20260814000001', bsns_year='2026', reprt_code='11012',
            fs_div='CFS', sj_div='CIS', account_id=account, account_nm=label, account_detail='-', ord=str(i+1),
            currency='KRW', thstrm_amount=str(amount), frmtrm_q_amount=str(prior),
            thstrm_nm='제 1 기 반기', frmtrm_q_nm='제 0 기 반기'))

    def respond(request):
        if market == 'kr':
            if request.url.path.endswith('list.json'):
                return httpx.Response(200, json={'status': '000', 'total_page': 1, 'list': [dict(
                    corp_code=fp['issuer'], stock_code=ticker, corp_name=security.company_name,
                    report_nm='반기보고서 (2026.06)', rcept_no='20260814000001', rcept_dt='20260814')]})
            return httpx.Response(200, json={'status': '000', 'list': dart_rows if request.url.params['fs_div'] == 'CFS' else []})
        if '/submissions/' in str(request.url):
            return httpx.Response(200, json={**submission([] if empty_financial else [f]), 'cik': 1234})
        if '/companyfacts/' in str(request.url):
            return httpx.Response(200, json={'cik': 1234, 'facts': {}} if empty_financial else companyfacts)
        if request.url.path.endswith('index.json'):
            return httpx.Response(200, json={'directory': {'item': [{'name': 'primary.htm'}]}})
        return httpx.Response(200, text=html_statement() if foreign else '<html>Synthetic filing</html>')

    reader = BoundedReader(fp, root, api_key='synthetic-no-credential', transport=httpx.MockTransport(respond))
    acquired = asyncio.run(collect(reader))
    return dict(technical_inputs=technical, financial_inputs=dict(plan=fp, acquisition=acquired,
        directory=root, receipts=reader.receipts, field_semantics=True))
