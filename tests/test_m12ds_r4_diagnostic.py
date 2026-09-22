import asyncio
import hashlib
import json

import pytest

from scripts.m12ds_r4_offline_capture import capture_payload
from scripts.m12ds_r4_source_diagnostic import diagnose


def source_fixture():
    def concept(value):
        return {'units': {'USD': [{'fy': 2026, 'fp': 'Q2', 'filed': '2026-08-05',
            'start': '2026-04-01', 'end': '2026-06-30', 'form': '10-Q', 'accn': 'filing', 'val': value}]}}
    payload = {'cik': '1234567890', 'facts': {'us-gaap': {
        'Revenues': concept(800), 'RevenueFromContractWithCustomerExcludingAssessedTax': concept(50),
        'OperatingIncomeLoss': concept(90)}}}
    sha = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    snapshot = {'ticker': 'FICTIONAL', 'fiscal_year': 2026, 'period_type': 'H1',
        'filing_date': '2026-08-05', 'financial_period_end': '2026-06-30', 'source_filing_id': 'filing',
        'revenue': None, 'operating_income': 90, 'raw_financial_fields': json.dumps([{'source_payload_sha256': sha}])}
    return payload, snapshot


def test_conflicting_revenue_preserved_not_selected_or_promoted():
    result = diagnose(*source_fixture())
    assert result['fields']['revenue']['error'] == 'sec_business_occurrence_conflict'
    assert len(result['fields']['revenue']['peer_occurrences']) == 2
    assert result['fields']['operating_income']['error'] is None
    assert result['source_promotion'] is False
    assert result['packet_rewritten'] is False


def test_diagnostic_cannot_substitute_updated_source():
    payload, snapshot = source_fixture()
    payload['cik'] = '9999999999'
    with pytest.raises(ValueError, match='differs_from_collected_source'):
        diagnose(payload, snapshot)


@pytest.mark.parametrize('text', ['plain text', '한글 본문\n\n줄바꿈\n', 'sign -1.25% USD 1,234.00'])
def test_capture_exact_bytes_no_newline_rewrite(text):
    result = asyncio.run(capture_payload({'text': text, 'use_llm': False}))
    assert result['prepared_text'] == text
    assert result['prepared_text_sha256'] == hashlib.sha256(text.encode()).hexdigest()
    assert result['production_sends'] == result['network_requests'] == result['production_recipient_intents'] == 0
    assert result['chunk_sha256'] == [hashlib.sha256(t.encode()).hexdigest() for t in result['chunks']]


def test_capture_uses_production_chunk_headers():
    from app.services.notification_service import _render_telegram_chunk, split_telegram_text
    text = '\n'.join(f'line {i} with repeated text' for i in range(50))
    result = asyncio.run(capture_payload({'text': text, 'use_llm': False}, max_chars=200))
    chunks = split_telegram_text(text, 200)
    assert len(chunks) > 1
    assert result['chunks'] == [_render_telegram_chunk(t, i, len(chunks)) for i, t in enumerate(chunks)]
    assert result['sink_invocations'] == len(chunks)


@pytest.mark.parametrize('value', [True, None, 'false', 0])
def test_capture_refuses_model_enabled_or_ambiguous_payload(value):
    with pytest.raises(ValueError, match='requires_no_llm'):
        asyncio.run(capture_payload({'text': 'do not dispatch', 'use_llm': value}))
