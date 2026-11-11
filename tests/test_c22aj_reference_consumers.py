"""C22AJ changed boundaries only; retained real bodies, synthetic extra roles/CLI."""
import asyncio
from copy import deepcopy
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import socket
import zipfile

import httpx
import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.services.ohlcv_client import OhlcvClient
from app.services.provider_native_technical import build_provider_native_view
from app.services.dated_chart_reference import validate_reference
from app.services.onboarding_evidence_service import (
    build_initial_evidence, validate_initial_evidence, initial_evidence_fingerprint, ensure_initial_baseline,
)
from app.schemas.thesis import PriceContext, ValuationSnapshot
from app.services.unified_snapshot_contract import digest

ROOT = Path(__file__).resolve().parents[3]
SEALED = ROOT / 'maintenance/20261111-c22ai-v1/C22AI_V1_RUNTIME_CAP_REAL_CAMPAIGN_20261111_RESULT.zip'


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def deny(*args, **kwargs):
        raise PermissionError('C22AJ_TEST_NO_REAL_NETWORK_OR_MODEL')
    monkeypatch.setattr(socket.socket, 'connect', deny)
    monkeypatch.setattr(socket, 'create_connection', deny)
    monkeypatch.setattr(socket, 'getaddrinfo', deny)


def retained(ticker):
    with zipfile.ZipFile(SEALED) as archive:
        receipt = json.loads(archive.read(f'public-ohlcv-wire/{ticker}/ohlcv-01.response.json'))
        raw = archive.read(f'public-ohlcv-wire/{ticker}/ohlcv-01.body')
    assert hashlib.sha256(raw).hexdigest() == receipt['artifact_sha256']
    return raw, receipt


def client(ticker='MU', *, synthetic_roles=True):
    raw, receipt = retained(ticker)
    source = json.loads(raw)
    requests = []
    def send(request):
        requests.append(dict(request.url.params))
        period = request.url.params['periods']
        adjusted = request.url.params['adjusted'] == 'true'
        if period == 'daily' and adjusted:
            response = httpx.Response(200, content=raw)
            response.extensions['unified_source_receipt'] = ('retained', receipt)
            return response
        if not synthetic_roles:
            return httpx.Response(502, json={'SYNTHETIC_NO_ROLE': True})
        payload = deepcopy(source)
        payload['meta']['adjusted'] = adjusted
        dates = ['2026-10-19', '2026-10-26', '2026-11-02', '2026-11-09'] if period == 'weekly' else [
            '2026-08-03', '2026-09-01', '2026-10-01', '2026-11-02']
        payload['periods'] = {period: [dict(date=d, open=100, high=110, low=90, close=105,
            volume=1000, indicators={'RSI14': 57.25, 'MA33': None}) for d in dates]}
        return httpx.Response(200, json=payload)
    result = OhlcvClient(transport=httpx.MockTransport(send), campaign_no_retry=True)
    result.settings = Settings(_env_file=None, ohlcv_base_url='http://127.0.0.1:1')
    return result, receipt, requests


def price(ticker='MU', **kwargs):
    c, receipt, requests = client(ticker, **kwargs)
    value = asyncio.run(c.fetch_price_context(ticker, as_of=datetime.fromisoformat(receipt['received_at'])))
    return value, requests


@pytest.mark.parametrize('ticker', ['MU', '005930'])
def test_retained_daily_reference_replay_not_current_price(ticker):
    p, requests = price(ticker)
    reference = p.dated_reference_price
    assert reference and reference['reference_date'] == '2026-11-10'
    assert p.decision.current_price is None and p.decision.price_basis == 'unavailable'
    assert p.periods['daily'].actual_count == 999
    validate_reference(reference, p.dated_reference_evidence, ticker=ticker, market=reference['market'])
    assert all(r['include_indicators'] == 'true' for r in requests[:3])
    assert reference['allowed_use'] == ['ONBOARDING_TECHNICAL', 'PRICE_LOCATION']
    if ticker == '005930':
        raw, receipt = retained(ticker)
        rows, _, _ = OhlcvClient._decode_period_payload(json.loads(raw),ticker=ticker,period='daily',
            adjusted=True,response_body_sha256=receipt['artifact_sha256'])
        old = build_provider_native_view(ticker=ticker,market='kr',periods={'daily': rows},cutoff=date(2026,11,11))
        assert old.periods['daily'].completed_count == 0  # Original strict/default behavior preserved.


def test_closed_week_month_buckets_caps_and_native_numbers_unchanged():
    p, requests = price()
    assert p.periods['weekly'].actual_count == p.periods['monthly'].actual_count == 3
    view = p.technical_context_payload()['native_view']['periods']
    assert view['weekly']['completed_as_of'] == '2026-11-02'
    assert view['monthly']['completed_as_of'] == '2026-10-01'
    assert view['weekly']['indicators']['RSI14'] == 57.25
    assert view['weekly']['indicators']['MA33'] is None
    assert requests[0]['count'] == '1000' and requests[1]['count'] == '700' and requests[2]['count'] == '300'
    assert not any(row.get('bar_state') == 'FINAL' for row in view['weekly']['rows'])


@pytest.mark.parametrize('change', ['ticker', 'currency', 'hash', 'value', 'cutoff', 'future_observation', 'duplicate'])
def test_reference_corruption_and_future_dates_rejected(change):
    p, _ = price()
    ref, proof = deepcopy(p.dated_reference_price), deepcopy(p.dated_reference_evidence)
    as_of = ref['observed_at']
    if change == 'ticker': ref['ticker'] = 'OTHER'
    if change == 'currency': ref['currency'] = 'KRW'
    if change == 'hash': ref['source_response_sha256'] = '0' * 64
    if change == 'value': ref['value'] = float('nan')
    if change == 'cutoff': proof['analysis_cutoff'] = '2099-01-01'
    if change == 'future_observation': as_of = '2026-11-10T00:00:00+00:00'
    if change == 'duplicate':
        payload = json.loads(proof['response_body'])
        payload['periods']['daily'].append(payload['periods']['daily'][0])
        proof['response_body'] = json.dumps(payload)
    with pytest.raises((ValueError, TypeError)):
        validate_reference(ref,proof,ticker='MU',market='us',as_of=as_of)


def setup_evidence(tmp_path):
    from app.models.watchlist import WatchlistItem
    from app.models.thesis import InvestmentThesis
    import app.models
    engine = create_engine('sqlite://',poolclass=StaticPool,connect_args={'check_same_thread': False})
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    item = WatchlistItem(ticker='MU',company_name='Synthetic issuer',exchange='NASDAQ',active=False)
    thesis = InvestmentThesis(ticker='MU',version=1,core_thesis='SYNTHETIC_DEMAND_NOT_PRIVATE',
        market_expectations='{"level":"balanced"}',status='active')
    session.add_all([item, thesis]); session.commit()
    c, receipt, _ = client()
    class Collector:
        async def collect_events(self, *args): return []
    class Valuation:
        async def fetch(self, *args, **kwargs): return ValuationSnapshot(currency='USD')
    evidence = asyncio.run(build_initial_evidence(session,item,as_of=datetime.fromisoformat(receipt['received_at']),
        acquire=True,collection_service=Collector(),price_client=c,valuation_service=Valuation()))
    return engine,session,item,thesis,evidence


def test_initial_evidence_baseline_packet_rule_and_valuation_consume_reference(tmp_path):
    from app.services.onboarding_decision_service import build_onboarding_decision_evidence_packet
    from app.services.thesis_evaluation_service import _build_price_decision
    engine, session, item, thesis, evidence = setup_evidence(tmp_path)
    try:
        assert evidence['current_price'] is None
        assert validate_initial_evidence(evidence,ticker='MU',thesis_version=1) == (True, None)
        baseline = ensure_initial_baseline(session,item,evidence,as_of=datetime.fromisoformat(evidence['as_of']))
        session.commit()
        packet = build_onboarding_decision_evidence_packet(session,item,evidence)
        refs = [r for r in packet.evidence if r.label == 'dated_reference_price']
        assert len(refs) == 1 and 'DATED_TECHNICAL_REFERENCE' in refs[0].statement
        assert 'response_body' not in packet.model_dump_json()
        stored = PriceContext.model_validate(json.loads(baseline.price_context))
        assert stored.dated_reference_price == evidence['dated_reference_price']
        decision = _build_price_decision(thesis, stored)
        assert decision.current_price is None and '실시간/비수정 현재가 아님' in decision.current_position
        valuation = json.loads(baseline.valuation_snapshot)
        assert valuation.get('forward_pe') is None and valuation.get('per') is None
        assert baseline.assessment_state == 'final'
    finally:
        session.close(); engine.dispose()


def test_null_null_and_reference_price_consumer_tampering_rejected(tmp_path):
    engine, session, _, _, evidence = setup_evidence(tmp_path)
    try:
        evidence.pop('dated_reference_price'); evidence.pop('dated_reference_evidence')
        evidence['fingerprint'] = initial_evidence_fingerprint(evidence)
        assert validate_initial_evidence(evidence,ticker='MU',thesis_version=1)[1] == 'initial_evidence_current_price_missing'
        evidence['dated_reference_price'] = evidence['price_context']['dated_reference_price']
        evidence['dated_reference_evidence'] = evidence['price_context']['dated_reference_evidence']
        evidence['price_context']['decision']['current_price'] = evidence['dated_reference_price']['value']
        evidence['fingerprint'] = initial_evidence_fingerprint(evidence)
        assert not validate_initial_evidence(evidence,ticker='MU',thesis_version=1)[0]
    finally:
        session.close(); engine.dispose()


def test_price_consumer_rejects_other_issuer_valid_reference(tmp_path):
    from app.models.thesis import InvestmentThesis
    from app.services.thesis_evaluation_service import _build_price_decision
    value, _ = price('005930')
    thesis = InvestmentThesis(ticker='MU', core_thesis='SYNTHETIC')
    with pytest.raises(ValueError, match='source_replay_mismatch'):
        _build_price_decision(thesis, value)


def test_actual_onboarding_packet_never_promotes_reference_to_core_fact(tmp_path):
    from app.services.onboarding_decision_service import build_onboarding_decision_evidence_packet
    from app.services.accepted_decision_v2_runtime_service import (
        build_accepted_v2_production_context, accepted_v2_fundamental_core_output_schema,
    )
    engine, session, item, _, evidence = setup_evidence(tmp_path)
    try:
        packet = build_onboarding_decision_evidence_packet(session, item, evidence)
        context = build_accepted_v2_production_context(packet={'packet_id': packet.packet_id,
            'market': packet.market, 'assessment_date': packet.assessment_date, 'stocks': [{'ticker': item.ticker}]},
            claim_id='SYNTHETIC_NO_BUSINESS_SOURCE', evidence_packets=(packet,))
        assert context.evidence_ownership[0].core_ref_ids == ()
        with pytest.raises(ValueError, match='v2_fundamental_core_ref_catalog_empty'):
            accepted_v2_fundamental_core_output_schema(context)
    finally:
        session.close(); engine.dispose()


def test_old_terminal_campaign_unchanged_and_new_profile_slots_are_separate():
    from app.services.campaign_runtime_cap import RuntimeCap
    old = ROOT / 'maintenance/20261111-c22ai-v1/live-run-budget.jsonl'
    before = hashlib.sha256(old.read_bytes()).hexdigest()
    binding = json.loads((old.parent / 'LIVE_WORKER_BINDING.json').read_bytes())
    cap = RuntimeCap(binding)
    assert cap.state()['total'] == 28
    with pytest.raises(ValueError,match='EXPIRED_OR_STOPPED'):
        cap.require_current()
    assert hashlib.sha256(old.read_bytes()).hexdigest() == before
    from app.services.official_codex_shadow_transport_service import command_prefix
    from app.services.vnext_execution_profile import SOL_HIGH_V1
    argv = command_prefix(SOL_HIGH_V1)
    assert argv[argv.index('-m')+1] == 'gpt-6.1-sol'
    assert 'model_reasoning_effort="high"' in argv
