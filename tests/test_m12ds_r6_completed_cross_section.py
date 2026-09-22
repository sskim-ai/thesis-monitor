from datetime import date, datetime, timezone
from types import SimpleNamespace

import pytest

from app.services import ai_review_service as packets
from app.services.market_cross_section_service import MarketCrossSection, MarketCrossSectionQuality, MarketIndexFact
from app.services.market_intelligence_service import build_market_intelligence


@pytest.mark.parametrize('market,cutoff,expected', [
    ('kr', '2026-09-23T00:28:00+09:00', '2026-09-22'),
    ('kr', '2026-09-21T07:00:00+09:00', '2026-09-18'),
    ('kr', '2026-09-22T16:00:00+09:00', '2026-09-22'),
    ('us', '2026-09-23T00:28:00+09:00', '2026-09-21'),
])
def test_packet_loads_completed_cross_section_not_host_date(monkeypatch, market, cutoff, expected):
    stamp = datetime.fromisoformat(cutoff)
    db = SimpleNamespace(exec=lambda query: SimpleNamespace(first=lambda: None))
    monkeypatch.setattr(packets, 'build_daily_digest', lambda *a, **k: None)

    def selected(actual_market, session_date, *, cutoff):
        assert actual_market == market
        assert str(session_date) == expected
        assert cutoff == stamp
        raise RuntimeError('verified_source_date')

    monkeypatch.setattr(packets, 'load_structured_market_context', selected)
    with pytest.raises(RuntimeError, match='verified_source_date'):
        packets._market_packet(db, stamp.date(), market, [], generated_at=stamp)


@pytest.mark.parametrize('selected,source,fresh,expected', [
    ('2026-09-22', '2026-09-22', 'fresh', True),
    ('2026-09-22', '2026-09-21', 'fresh', False),
    ('2026-09-24', '2026-09-24', 'fresh', False),
    ('2026-09-22', '2026-09-22', 'stale', False),
])
def test_cross_section_fact_keeps_source_session(selected, source, fresh, expected):
    section = MarketCrossSection(market='KR', session_date=date.fromisoformat(source),
        as_of=datetime(2026, 9, 22, 15, tzinfo=timezone.utc),
        indices=[MarketIndexFact(symbol='KOSPI', label='KOSPI', close=100, return_pct=1)],
        quality=MarketCrossSectionQuality(provider='kiwoom_rest', provider_role='shadow',
            coverage='full', freshness=fresh, universe_version='fixture',
            raw_count=1, eligible_count=1, excluded_count=0), source_payload_sha256='a' * 64)
    result = build_market_intelligence(None, date(2026, 9, 23), [], [], market='kr',
        cross_section=section, cross_section_session_date=date.fromisoformat(selected))
    facts = [f for f in result['fact_catalog'] if f['fact_type'] == 'market_cross_section_index']
    assert bool(facts) == expected
    if expected:
        assert facts[0]['as_of_date'] == source
        assert facts[0]['fields']['close'] == 100
