"""Generic format and typed-denial regression, without real-security exceptions."""
from datetime import date
import json

import pytest

from scripts import kis_current_fy1_owner as p
from scripts import kis_exact_action_guard as g
from scripts.kis_fy1_semantic_owner import SemanticGap
from test_kis_exact_action_guard import docs, family, guard, page, row
from test_kis_current_fy1_owner import eps, price_inputs


@pytest.mark.parametrize('fmt', ['%Y%m%d', '%Y-%m-%d', '%Y.%m.%d', '%Y/%m/%d'])
@pytest.mark.parametrize('separator', [None, '~', ' ~ ', '\t~\t'])
def test_exact_formats_and_boundary_only_intervals(fmt, separator):
    first, last = date(2026, 4, 8), date(2026, 4, 12)
    value = first.strftime(fmt)
    if separator is not None:
        value += separator + last.strftime(fmt)
    assert g._dates(value) == ([first] if separator is None else [first, last])


@pytest.mark.parametrize('value', [
    '26/04/13', '04/13/2026', '2026/13/01', '2026/04/12 ~ 2026/04/08',
    '2026/04', '04/13', '2026/4/13', '2026/04/3', '2026/02/29', '2026/04/31',
    '2026/04/13 trailing', '2026/04/13T00:00:00', '2026/04/08~',
    '2026/04/08~2026-04-12', '2026-04-08~2026/04/12', '2026/04/08~04/12',
    '2026/04/08~2026/04/09~2026/04/12', '0000/04/13', '', None, 20260413,
])
def test_invalid_partial_mixed_or_reversed_dates_never_normalized(value):
    with pytest.raises(SemanticGap):
        g._dates(value)


def test_leap_date_and_equal_interval_preserve_exact_boundaries():
    assert g._dates('2024/02/29') == [date(2024, 2, 29)]
    assert g._dates('2026/04/13~2026/04/13') == [date(2026, 4, 13)] * 2


@pytest.mark.parametrize('variant', g.VARIANTS)
@pytest.mark.parametrize(('value', 'expected'), [
    ('2026/08/27', 'WHOLLY_ON_OR_BEFORE_ESTIMATE'),
    ('2026/04/08 ~ 2026/04/12', 'WHOLLY_ON_OR_BEFORE_ESTIMATE'),
    ('2026/10/01', 'WHOLLY_AFTER_PRICE'),
    ('2026/08/28', 'CRITICAL_WINDOW_DATE'),
    ('2026/09/30', 'CRITICAL_WINDOW_DATE'),
    ('2026/08/27~2026/08/28', 'CRITICAL_WINDOW_DATE'),
    ('2026/08/26~2026/10/01', 'STRADDLING_ACTION_PROCESS'),
])
def test_slash_critical_window_boundary_all_variants(variant, value, expected):
    result = g.event_decision(variant, row(variant, value), '2026-08-27', '2026-09-30',
                              docs()['actions'][variant]['columns'])
    assert result['classification'] == expected
    assert result['blocks'] is (expected in {'CRITICAL_WINDOW_DATE', 'STRADDLING_ACTION_PROCESS'})
    assert result['errors'] == [] and result['effective_date_inferred'] is False


def test_mixed_owned_fields_are_kept_separate_without_invented_effective_date():
    source = row() | {'record_date': '20260409', 'list_dt': '2026/04/13',
                      'td_stop_dt': '2026/04/08 ~ 2026/04/12'}
    result = g.event_decision('rev_split', source, '2026-08-27', '2026-09-30',
                              docs()['actions']['rev_split']['columns'])
    assert result['classification'] == 'WHOLLY_ON_OR_BEFORE_ESTIMATE'
    assert result['blocks'] is False and result['raw'] == source
    assert result['parsed_relevant_dates'] == {
        'record_date': ['2026-04-09'], 'list_dt': ['2026-04-13'],
        'td_stop_dt': ['2026-04-08', '2026-04-12']}


@pytest.mark.parametrize('variant', g.VARIANTS)
@pytest.mark.parametrize('kind', ['unresolved', 'proven', 'straddling', 'incomplete'])
def test_typed_denial_propagates_through_arithmetic_owner(variant, kind):
    source = row(variant) | {g.DATE_FIELDS[variant][-1]: 'not-a-date'}
    if kind == 'proven':
        source['record_date'] = '2026/08/01'
    elif kind == 'straddling':
        source = row(variant) | {g.DATE_FIELDS[variant][1]: 'not-a-date',
                                 g.DATE_FIELDS[variant][-1]: '2026/10/01'}
    fam = family(variant, [page(variant, [source], status='F' if kind == 'incomplete' else 'E')])
    actions = guard(**{variant: fam})
    expected, denied = {
        'unresolved': (g.UNRESOLVED, 'UNAVAILABLE_CORPORATE_ACTION_DATE_UNRESOLVED'),
        'proven': (g.EVENT, 'UNAVAILABLE_POST_ESTIMATE_SHARE_UNIT_CHANGE'),
        'straddling': (g.EVENT, 'UNAVAILABLE_POST_ESTIMATE_SHARE_UNIT_CHANGE'),
        'incomplete': (g.INCOMPLETE, 'UNAVAILABLE_CORPORATE_ACTION_SOURCE_INCOMPLETE'),
    }[kind]
    assert actions['state'] == expected
    assert actions['query_status'] == ('INCOMPLETE' if kind == 'incomplete' else 'COMPLETE')
    assert fam['row_audits'][0]['errors']
    result = p.current_fper(eps(), p.price_receipt(**price_inputs()), actions)
    assert result['state'] == denied
    assert result['value'] is result['display_value'] is result['exact_quotient'] is None
    p.validate_current_fper(json.loads(json.dumps(result)), eps(), p.price_receipt(**price_inputs()), actions)


def test_separate_parsed_event_wins_over_unresolved_row_without_hiding_errors():
    unresolved = row() | {'list_dt': 'unknown'}
    proven = row(day='2026/08/01')
    for rows in ([unresolved, proven], [proven, unresolved]):
        actions = guard(rev_split=family(pages=[page(rows=rows)]))
        assert actions['state'] == g.EVENT
        assert any(e['classification'] == 'AMBIGUOUS_EXACT_SECURITY_ACTION' for e in actions['events'])
        assert any(e['errors'] for e in actions['events'])


def test_missing_family_is_source_gap_not_unresolved_date():
    actions = guard(rev_split=family(pages=[]))
    assert actions['state'] == g.INCOMPLETE
