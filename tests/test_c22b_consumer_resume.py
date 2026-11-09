import hashlib,json,os,signal,subprocess,sys
from copy import deepcopy
from datetime import date
from pathlib import Path
import pytest
from scripts.native_dwm_batch import read_history
from app.services.ohlcv_client import OhlcvClient
from app.services.provider_native_technical import build_provider_native_view
from app.services.packet_owned_technical_context_service import build_native_packet_context
from app.services.cross_market_decision_engine_service import build_decision_evidence_packet,validate_decision_candidate,render_shadow_decision
from test_cross_market_decision_engine import _packet_and_candidate
from test_provider_native_technical import raw_payload,fixture_completion


def test_killed_process_only_sealed_roles_resume_and_partial_or_changed_reject(tmp_path):
    stock=dict(symbol='TEST',market='us',receipts=[dict(timeframe='daily',status='DATED_TECHNICAL_ANALYSIS_READY',body_sha256=hashlib.sha256(b'{}').hexdigest())])
    folder=tmp_path/'us-TEST';(folder/'daily').mkdir(parents=True)
    (folder/'daily/response.body').write_bytes(b'{}')
    (folder/'daily/receipt.json').write_text(json.dumps(stock['receipts'][0]))
    files={str(p.relative_to(folder)):dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in folder.rglob('*') if p.is_file()}
    seal=folder/'STOCK_SEAL.json';seal.write_text(json.dumps(dict(stock=stock,files=files)))
    progress=dict(GETs=1,physical_HTTP=2,physical_count_confirmed=True,securities=[stock],stock_seals={'us-TEST':hashlib.sha256(seal.read_bytes()).hexdigest()})
    (tmp_path/'PROGRESS.json').write_text(json.dumps(progress))
    # A real child reads the durable seal, then dies without a SUMMARY.
    code='import os,signal;from scripts.native_dwm_batch import read_history;read_history('+repr(str(tmp_path))+');os.kill(os.getpid(),signal.SIGKILL)'
    child=subprocess.run([sys.executable,'-c',code],env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1])),capture_output=True)
    assert child.returncode==-signal.SIGKILL and not (tmp_path/'SUMMARY.json').exists()
    ledger,roles=read_history(tmp_path);assert ledger['GETs']==1 and set(roles)=={('TEST','daily')}
    (tmp_path/'PROGRESS.json').write_text(json.dumps(dict(progress,in_flight_role=['TEST','weekly'])))
    with pytest.raises(ValueError,match='outcome_unknown'):read_history(tmp_path)
    (tmp_path/'PROGRESS.json').write_text(json.dumps(progress))
    (folder/'daily/response.body').write_bytes(b'changed')
    with pytest.raises(ValueError,match='sealed_file_changed'):read_history(tmp_path)


def test_dated_native_RSI_exact_citation_without_generic_penalty_or_new_authority():
    payload=raw_payload('TEST','us','daily',85);raw=json.dumps(payload).encode()
    rows=OhlcvClient._decode_period_payload(payload,ticker='TEST',period='daily',adjusted=True,response_body_sha256=hashlib.sha256(raw).hexdigest())[0]
    view=build_provider_native_view(ticker='TEST',market='us',periods={'daily':rows},cutoff=date(2026,11,6),completion_verifier=fixture_completion)
    context=build_native_packet_context(view=view,session='regular',as_of='2026-11-06')
    packet=build_decision_evidence_packet(packet=dict(packet_id='C22B_test',market='us',assessment_date='2026-11-06'),stock=dict(ticker='TEST'),technical_context=context)
    assert packet.technical_context_status=='PARTIAL_SAFE'
    assert not any('technical_context_limit:PARTIAL_SAFE' in c for c in packet.data_quality_cautions)
    assert not view.current_price_qualified and not view.strict_ready
    ref=next(r for r in packet.evidence if r.label=='daily:provider-native:RSI14')
    assert ref.numeric_prose_eligible and ref.value=='47.123456789' and ref.as_of=='2026-11-06'
    labels={r.label for r in packet.evidence}
    assert 'daily:provider-native:MACD_OSC_320_640_9' not in labels
    assert 'daily:provider-native:MA288' not in labels
    base,candidate=_packet_and_candidate()
    merged=packet.model_copy(update={'evidence':(*base.evidence,*packet.evidence)})
    candidate=candidate.model_copy(update={'selected_numeric_fact_refs':(ref.ref_id,),'horizon':packet.horizon})
    assert validate_decision_candidate(merged,candidate).valid
    assert '47.123456789' in render_shadow_decision(merged,candidate).text
    with pytest.raises(ValueError,match='ticker_mismatch'):
        build_decision_evidence_packet(packet=dict(packet_id='other',market='us',assessment_date='2026-11-06'),stock=dict(ticker='FOREIGN'),technical_context=context)
    with pytest.raises(ValueError,match='date_mismatch'):
        build_decision_evidence_packet(packet=dict(packet_id='past',market='us',assessment_date='2026-01-01'),stock=dict(ticker='TEST'),technical_context=context)
