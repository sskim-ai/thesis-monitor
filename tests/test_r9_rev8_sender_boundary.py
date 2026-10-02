import asyncio
from hashlib import sha256

import pytest

from app.services.accepted_decision_v2_service import render_accepted_v2_production
from app.services.detailed_stock_message_service import build_detailed_plan, final_detailed_audit
from scripts.m12ds_r4_offline_capture import capture_payload
from tests.test_r9_rev7_detailed_renderer import inputs as fixture_inputs


@pytest.fixture
def inputs():
    return fixture_inputs.__wrapped__()


@pytest.mark.parametrize('limit', [4096, 350])
def test_detailed_normal_survives_actual_prepare_chunk_send_boundary(inputs, limit):
    plan = build_detailed_plan(**inputs)
    rendered = render_accepted_v2_production(inputs['packet'], plan)
    payload = dict(type='thesis_assessment', ticker=plan.ticker, text=rendered.text, use_llm=False)
    captured = asyncio.run(capture_payload(payload, max_chars=limit))
    assert captured['prepared_text'] == rendered.text
    assert captured['prepared_text_sha256'] == sha256(rendered.text.encode()).hexdigest()
    assert captured['production_sends'] == captured['network_requests'] == captured['production_recipient_intents'] == 0
    assert final_detailed_audit(captured['prepared_text'], inputs['packet'], plan)['status'] == 'PASS'
    joined = '\n'.join(captured['chunks'])
    for heading in ('사업·실적', '현재 가격 구조', '수급·포지셔닝', 'Valuation'):
        assert heading in joined
    assert all(row.text in joined for row in plan.rows)
    assert all(sha256(chunk.encode()).hexdigest() == digest for chunk, digest in
               zip(captured['chunks'], captured['chunk_sha256'], strict=True))
