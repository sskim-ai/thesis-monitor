"""Synthetic, offline B2 price/session connections; no source or model calls."""
from copy import deepcopy

import pytest

from app.services.entry_price_basis import frame_matches_price
from app.services.new_buyer_base_contract import timing
from app.services.new_buyer_input_owner import tactical_catalog
from app.services.unified_snapshot_contract import digest


SESSION = '2026-11-23'
ZONE = 'canonical:chart:structure:nearest_supports:1'


def _context(timeframe='weekly', *, legacy=False):
    bar_date = SESSION if legacy else {'weekly': '2026-11-16', 'monthly': '2026-10-01'}[timeframe]
    frame = dict(quality='available', currency='USD', price_basis='adjusted',
                 timeframe=timeframe, candle=dict(close=100 if legacy else 93))
    if not legacy:
        frame.update(completed_bar_only=True, evaluation_as_of=SESSION)
    rows = [
        dict(ref_id='canonical:price:current', as_of=SESSION, label='current_price',
             statement=dict(current_price=100, currency='USD', price_basis='adjusted_close',
                            price_as_of=SESSION)),
        dict(ref_id='canonical:chart:daily', as_of=SESSION, label='daily',
             statement=dict(quality='available', currency='USD', price_basis='adjusted',
                            candle=dict(close=100))),
        dict(ref_id='canonical:chart:' + timeframe, as_of=bar_date, label=timeframe,
             statement=frame),
        dict(ref_id=ZONE, as_of=SESSION, label='chart_support_zone',
             statement=dict(timeframe=timeframe, currency='USD', zone_low=90, zone_high=110)),
    ]
    return dict(current_price=dict(value=100, currency='USD', basis='adjusted_close',
                                   as_of=SESSION, ref_id='canonical:price:current'),
        decision_evidence=rows,
        source_use_projection=dict(source_permissions=[dict(ref_id=r['ref_id'], allowed_uses=['ENTRY'])
                                                         for r in rows]),
        r2_eligible_range_catalog=dict(tactical_candidates=[dict(candidate_id='support', low=90,
            high=110, currency='USD', evidence_refs=[ZONE])]))


def _timing(context):
    return timing(dict(ticker='SYN', security_id='SYN_SECURITY',
        selected_tactical_candidate='support', current_price=context['current_price'],
        tactical_catalog=tactical_catalog(context, 'SYN', 'SYN_SECURITY')))


@pytest.mark.parametrize('timeframe', ['weekly', 'monthly'])
def test_completed_multiframe_support_uses_current_daily_quote(timeframe):
    context = _context(timeframe)
    before = deepcopy(context)
    result = _timing(context)
    assert (result['state'], result['relation']) == ('FAVORABLE_NOW', 'INSIDE')
    row = tactical_catalog(context, 'SYN', 'SYN_SECURITY')[0]
    assert row['as_of'] == SESSION
    assert row['basis_proofs'][0]['chart_sha256'] == digest(context['decision_evidence'][2])
    assert context == before
    # The same helper consumes source timeframe data without relabeling its bar.
    chart = context['decision_evidence'][2]
    raw = dict(chart['statement'], as_of_date=chart['as_of'])
    assert frame_matches_price(raw, timeframe=timeframe, frame_as_of=chart['as_of'],
                               price=context['current_price'], session=SESSION)


def test_legacy_same_session_frame_remains_compatible_but_not_a_dated_reference():
    context = _context(legacy=True)
    assert _timing(context)['state'] == 'FAVORABLE_NOW'
    context['decision_evidence'][2]['as_of'] = '2026-11-16'
    assert _timing(context)['state'] == 'UNRESOLVED'
    context['decision_evidence'][2]['as_of'] = SESSION
    context['decision_evidence'][2]['statement']['quality'] = 'UNCONFIRMED'
    assert _timing(context)['state'] == 'UNRESOLVED'


def test_explicit_incomplete_marker_overrides_metadata_and_legacy_paths():
    for legacy in (False, True):
        context = _context(legacy=legacy)
        frame = context['decision_evidence'][2]['statement']
        frame['bar_state'] = 'PARTIAL'
        assert _timing(context)['state'] == 'UNRESOLVED'
        del frame['bar_state']
        frame['candle']['completion_state'] = 'UNCONFIRMED'
        assert _timing(context)['state'] == 'UNRESOLVED'


@pytest.mark.parametrize('gap', ['daily_close', 'daily_session', 'incomplete', 'wrong_evaluation',
                                'frame_basis', 'frame_currency', 'stale_support', 'permission'])
def test_completed_multiframe_still_requires_bound_current_price_and_owned_support(gap):
    context = _context()
    daily, chart, support = context['decision_evidence'][1:]
    if gap == 'daily_close':
        daily['statement']['candle']['close'] = 99
    elif gap == 'daily_session':
        daily['as_of'] = '2026-11-20'
    elif gap == 'incomplete':
        chart['statement']['completed_bar_only'] = False
    elif gap == 'wrong_evaluation':
        chart['statement']['evaluation_as_of'] = '2026-11-20'
    elif gap == 'frame_basis':
        chart['statement']['price_basis'] = 'unadjusted'
    elif gap == 'frame_currency':
        chart['statement']['currency'] = 'KRW'
    elif gap == 'stale_support':
        support['as_of'] = chart['as_of']
    else:
        context['source_use_projection']['source_permissions'][-1]['allowed_uses'] = ['DISPLAY']
    assert _timing(context)['state'] == 'UNRESOLVED'
