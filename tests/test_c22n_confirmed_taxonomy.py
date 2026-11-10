from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest
from app.services.confirmed_sector_taxonomy import VERSION, US_BROAD, render_confirmed_sectors
from app.services.dated_market_legacy_adapter import render_retained_component_sectors
from app.services.unified_snapshot_contract import digest

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / 'maintenance/20261110-c22m-v1/C22M_V1_SOURCE_FIELD_RECOVERY_AND_E2E_PLAN.zip'
ARCHIVE_SHA = 'd0e1e948425d231ac450803ac960533083ef7ceb04fa50a0072ee545aa429ff5'


def reference(market):
    return json.loads((ROOT / f'maintenance/20261106-c15/C15_{market.upper()}_DATED_SOURCE_REFERENCE.json').read_bytes())


def seal_value(r):
    r['value_sha256'] = digest(r['value'])
    return r


@pytest.mark.parametrize('market,counts', [('us', [11]), ('kr', [22, 21])])
def test_original_custody_rank_and_auxiliary(market, counts):
    result = render_retained_component_sectors(archive_path=ARCHIVE, archive_sha256=ARCHIVE_SHA,
        reference_path=ROOT / f'maintenance/20261106-c15/C15_{market.upper()}_DATED_SOURCE_REFERENCE.json',
        market=market, enabled=True, taxonomy_version=VERSION)
    assert [v['ranking'] for v in result['candidate_counts'].values()] == counts
    assert result['coverage'] == 'PASS'
    assert result['full_market_parent'] is False and result['NO_SEND']
    ranked = [f['fields'] for f in result['source_view']['fact_catalog']]
    if market == 'us':
        assert {r['series_code'] for r in ranked} == set(US_BROAD)
        assert len(result['auxiliary']) == 1 and 'SOXX' in result['auxiliary'][0]['text']
    else:
        assert not any(r['sector'] in {'제조', '대형주', '중형주', '소형주'} for r in ranked)
        assert sum(r['sector'] == '전기/전자' for r in ranked) == 2
        assert any(r['sector'] == '금융' and r['market_scope'] == 'KOSDAQ' for r in ranked)
    for scope in result['candidate_counts']:
        items = [i for i in result['selected_items'] if i['proof']['venue'] == scope]
        assert len(items) == 2
        assert set(items[0]['fact_ids']).isdisjoint(items[1]['fact_ids'])
    assert result['text_sha256'] == hashlib.sha256(result['text'].encode()).hexdigest()


@pytest.mark.parametrize('field,value', [('unit', 'krw'), ('market_session', 'overnight'), ('observed_at', '2026-11-04T00:00:00Z'), ('raw_payload', {'return_basis': 'unadjusted'})])
def test_watch_obeys_same_numeric_source_checks(field, value):
    r = reference('us')
    row = next(x for x in r['value']['observations'] if x['series_code'] == 'SOXX')
    row[field] = value
    with pytest.raises(ValueError):
        render_confirmed_sectors(seal_value(r))


@pytest.mark.parametrize('mutation', ['name', 'venue', 'taxonomy', 'source_ref', 'duplicate'])
def test_kr_classification_laundering_rejected(mutation):
    r = reference('kr')
    row = next(x for x in r['value']['sectors'] if x['sector_code'] == '027')
    if mutation == 'duplicate':
        r['value']['sectors'].append(deepcopy(row))
    else:
        field, value = {'name': ('sector', '전기/전자'), 'venue': ('market_scope', 'US'),
            'taxonomy': ('taxonomy', 'forged'), 'source_ref': ('source_ref', 'forged:2026-11-06')}[mutation]
        row[field] = value
    with pytest.raises(ValueError):
        render_confirmed_sectors(seal_value(r))


def test_unknown_code_quarantined_not_name_approved():
    r = reference('kr')
    row = deepcopy(r['value']['sectors'][3])
    row.update(sector_code='999', source_ref='kiwoom:ka20003:KOSPI:999:2026-11-06')
    r['value']['sectors'].append(row)
    result = render_confirmed_sectors(seal_value(r))
    assert result['classification_ledger'][-1]['category'] == 'INELIGIBLE_UNCLASSIFIED'


def test_less_than_six_no_auxiliary_padding():
    r = reference('us')
    r['value']['observations'] = [x for x in r['value']['observations'] if x['series_code'] in (*US_BROAD[:5], 'SOXX')]
    result = render_confirmed_sectors(seal_value(r))
    assert result['coverage'] == 'PARTIAL_SECTOR_COVERAGE'
    assert all(not x['fact_ids'] for x in result['selected_items'])
    assert len(result['auxiliary']) == 1


def test_ties_deterministic_and_no_parent_overlap():
    r = reference('kr')
    for row in r['value']['sectors']:
        row['return_pct'] = 0.0
    a = render_confirmed_sectors(seal_value(r))
    r['value']['sectors'].reverse()
    b = render_confirmed_sectors(seal_value(r))
    assert a['text'] == b['text']
    assert a['selected_items'] == b['selected_items']
    assert all(f['fields']['sector_code'] != '021' for f in a['source_view']['fact_catalog'])


def test_public_custody_rejects_rehashed_source_mutation(tmp_path):
    r = reference('us')
    next(x for x in r['value']['observations'] if x['series_code'] == 'SOXX')['change_pct'] = 99
    p = tmp_path / 'forged.json'
    p.write_text(json.dumps(seal_value(r)))
    with pytest.raises(ValueError, match='original_value_binding'):
        render_retained_component_sectors(archive_path=ARCHIVE, archive_sha256=ARCHIVE_SHA,
            reference_path=p, market='us', enabled=True, taxonomy_version=VERSION)


def test_v2_opt_in_and_unknown_version():
    kwargs = dict(archive_path=ARCHIVE, archive_sha256=ARCHIVE_SHA,
        reference_path=ROOT / 'maintenance/20261106-c15/C15_US_DATED_SOURCE_REFERENCE.json', market='us')
    with pytest.raises(ValueError, match='default_off'):
        render_retained_component_sectors(**kwargs, taxonomy_version=VERSION)
    with pytest.raises(ValueError, match='unknown_version'):
        render_retained_component_sectors(**kwargs, enabled=True, taxonomy_version='forged')


def test_auxiliary_metric_guard_and_null_not_invented():
    r = reference('kr')
    row = next(x for x in r['value']['sectors'] if x['sector_code'] == '138')
    row['metric_role'] = 'forged'
    with pytest.raises(ValueError, match='auxiliary_basis'):
        render_confirmed_sectors(seal_value(r))
    row['metric_role'] = 'actual_sector_breadth'
    row['return_pct'] = None
    result = render_confirmed_sectors(seal_value(r))
    assert not any(x['binding']['raw_symbol'] == '138' for x in result['auxiliary'])


def test_watch_value_exact_and_no_broad_laundering():
    r = reference('us')
    original = next(x for x in r['value']['observations'] if x['series_code'] == 'SOXX')
    original['category'] = 'US_BROAD_SECTOR'
    result = render_confirmed_sectors(seal_value(r))
    watch = result['auxiliary'][0]['binding']
    assert watch['return_pct'] == original['change_pct'] and watch['unit'] == 'percent'
    assert watch['source_row_sha256'] == digest(original)
    assert watch['session'] == '2026-11-05'
    assert all(f['fields']['series_code'] != 'SOXX' for f in result['source_view']['fact_catalog'])
