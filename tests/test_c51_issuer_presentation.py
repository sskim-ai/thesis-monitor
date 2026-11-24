"""Issuer comparison display uses the existing accepted business relationship."""
from copy import deepcopy
from types import SimpleNamespace

from app.services.detailed_stock_message_service import _localized_earnings_line
from app.services.issuer_business_bridge import bind_comparison, identity_bridge
from app.services.unified_snapshot_contract import digest
from tests.test_issuer_business_bridge import comparison, fixture


def case():
    bridge = identity_bridge(**fixture())
    original = comparison()
    original['fields'].update(direction='higher', prior_period_end='2025-06-30',
                              statement_basis='consolidated')
    fact = bind_comparison({**deepcopy(original), 'fact_id': 'projected'}, original,
                           bridge, source_result_sha256='original-source')
    text = ('Reported revenue is higher versus the source-owned comparable period; '
            'source period 2026-06-30. Recurrence is not established by this observation.')
    evidence = SimpleNamespace(ref_id='comparison', label='earnings_comparison',
        as_of='2026-06-30', source_ref='stock.fact_catalog.projected',
        source_time=SimpleNamespace(subject_ticker='FICADR', canonical_fact_sha256=digest(fact)))
    packet = SimpleNamespace(market='us', ticker='FICADR', evidence=[evidence])
    source = dict(packet=dict(stocks=[dict(fact_catalog=[fact])]),
        issuer_business_bridge=bridge, source_graph={'projected': dict(fact_sha256=digest(fact))})
    return text, packet, source


def test_accepted_issuer_comparison_is_localized_without_changing_financial_scope():
    text, packet, source = case()
    before = deepcopy(source)
    rendered = _localized_earnings_line(text, packet=packet, source=source, refs=['comparison'])
    assert '동일 발행사 본주(123456)의 회사 재무 기준' in rendered
    assert '2026-06-30' in rendered and '2025-06-30' in rendered
    assert '매출액' in rendered and '증가' in rendered
    assert '이어질지는 확인할 수 없습니다' in rendered
    assert source == before
    assert not source['issuer_business_bridge']['SECURITY_VALUATION_BRIDGE_ELIGIBLE']


def test_unrelated_security_cannot_relabel_issuer_comparison():
    text, packet, source = case()
    source['issuer_business_bridge']['security_ticker'] = 'OTHER'
    assert _localized_earnings_line(text, packet=packet, source=source, refs=['comparison']) == text
