"""Opt-in display taxonomy, after retained component custody verification.

Mappings use the original Kiwoom venue/code/name tuples, not name-only filters.
They classify observations, never issue a Market Parent or investment permission.
"""
from collections import Counter
from copy import deepcopy
import hashlib
from math import isfinite

from app.services.unified_snapshot_contract import digest

VERSION = 'sector-universe-user-confirmed-v2'
US_BROAD = ('XLB', 'XLC', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY')
KR_NAMES = {
    'KOSPI': dict(zip(
        '002 003 004 005 006 007 008 009 010 011 012 013 014 015 016 017 018 019 020 021 024 025 026 027 028 029 030 603 604 605'.split(),
        '대형주|중형주|소형주|음식료/담배|섬유/의류|종이/목재|화학|제약|비금속|금속|기계/장비|전기/전자|의료/정밀기기|운송장비/부품|유통|전기/가스|건설|운송/창고|통신|금융|증권|보험|일반서비스|제조|부동산|IT 서비스|오락/문화|변동성지수|코스피고배당50|코스피배당성장50'.split('|')
    )),
    'KOSDAQ': dict(zip(
        '103 106 107 108 110 111 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 138 139 140 141 142 143 144 145 150 151 160 165'.split(),
        '일반서비스|제조|건설|유통|운송/창고|금융|음식료/담배|섬유/의류|종이/목재|출판/매체복제|화학|제약|비금속|금속|기계/장비|전기/전자|의료/정밀기기|운송장비/부품|기타제조|통신|IT 서비스|KOSDAQ 100|KOSDAQ MID 300|KOSDAQ SMALL|오락/문화|코스닥 우량기업|코스닥 벤처기업|코스닥 중견기업|코스닥 신성장기업|KOSDAQ 150|코스닥글로벌지수|F-KOSDAQ150|F-KOSDAQ150인버스'.split('|')
    )),
}
SIZE_CODES = {'KOSPI': ('002', '003', '004', '604', '605'),
              'KOSDAQ': ('138', '139', '140', '142', '143', '144', '145', '150', '151')}
PARENT_CODES = {'KOSPI': '027', 'KOSDAQ': '106'}
REGISTRY = dict(version=VERSION, us_broad=US_BROAD, us_watch=('SOXX',),
                kr_names=KR_NAMES, size_codes=SIZE_CODES, parent_codes=PARENT_CODES,
                unresolved={'KOSPI': ('021', '603'), 'KOSDAQ': ('160', '165')})
REGISTRY_SHA256 = digest(REGISTRY)


def classify_row(row, market):
    """Internal classification only; source custody must be verified upstream."""
    if market == 'us':
        code = row['series_code']
        if code in US_BROAD:
            return 'US_BROAD_SECTOR', 'confirmed_broad_11'
        if code == 'SOXX':
            return 'US_SEMICONDUCTOR_WATCH', 'semiconductor_not_broad_sector'
        return 'INELIGIBLE_UNCLASSIFIED', 'not_configured_sector'
    scope, code = row.get('market_scope'), row.get('sector_code')
    if scope not in KR_NAMES or row.get('taxonomy') != 'kiwoom-sector-index-v1':
        raise ValueError('confirmed_sector_venue_or_taxonomy')
    if code not in KR_NAMES[scope]:
        return 'INELIGIBLE_UNCLASSIFIED', 'unknown_sector_code'
    if row['sector'] != KR_NAMES[scope][code]:
        raise ValueError('confirmed_sector_code_name_mismatch')
    if code == PARENT_CODES[scope]:
        return 'KR_BROAD_PARENT_MANUFACTURING', 'parent_manufacturing_excluded'
    if code in SIZE_CODES[scope]:
        return 'KR_SIZE_STYLE_INDEX', 'size_style_not_industry'
    if code in REGISTRY['unresolved'][scope]:
        return 'INELIGIBLE_UNCLASSIFIED', ('financial_parent_child_overlap_unresolved'
            if scope == 'KOSPI' and code == '021' else 'non_industry_index')
    return 'KR_DETAILED_INDUSTRY', 'original_independent_detailed_code'


def render_confirmed_sectors(reference):
    """Called only after original archive/raw/value pin checks in the adapter."""
    from app.services.dated_market_legacy_adapter import component_sector_source, _render_component_sectors
    # Preserve all original numeric/session/basis checks before filtering ranks.
    component_sector_source(reference)
    market, session = reference['market'], reference['completed_session']
    key = 'observations' if market == 'us' else 'sectors'
    projected = deepcopy(reference)
    projected['value'][key] = []
    ledger, auxiliary, seen = [], [], set()
    for row in reference['value'][key]:
        scope = 'US' if market == 'us' else row['market_scope']
        code = row['series_code'] if market == 'us' else row['sector_code']
        if market == 'us' and code not in (*US_BROAD, 'SOXX'):
            continue
        if (scope, code) in seen:
            raise ValueError('confirmed_sector_duplicate_code')
        seen.add((scope, code))
        category, reason = classify_row(row, market)
        value = row['change_pct'] if market == 'us' else row['return_pct']
        valid = value is not None and not isinstance(value, bool) and isinstance(value, (int, float)) and isfinite(value)
        if market == 'kr':
            if row.get('source_ref') != f'kiwoom:ka20003:{scope}:{code}:{session}':
                raise ValueError('confirmed_sector_row_source_binding')
            if row.get('metric_role') not in {'actual_sector_breadth', 'sector_price_proxy'}:
                raise ValueError('confirmed_sector_auxiliary_basis')
            valid = valid and row.get('listed_count', 0) > 0
        binding = dict(provider='kiwoom_rest', venue=scope, raw_symbol=code,
            source_taxonomy='configured-sector-etf-proxies' if market == 'us' else row['taxonomy'],
            registry_version=VERSION, registry_sha256=REGISTRY_SHA256,
            source_row_sha256=digest(row), component_sha256=reference['original_component_sha256'],
            bundle_sha256=reference['original_bundle_sha256'], session=session,
            metric_basis=row['raw_payload']['return_basis'] if market == 'us' else row['metric_role'],
            unit='percent', return_pct=value, category=category, reason=reason, numeric_available=valid)
        ledger.append(binding)
        if valid and category in {'US_BROAD_SECTOR', 'KR_DETAILED_INDUSTRY'}:
            projected['value'][key].append(deepcopy(row))
        elif valid and category in {'US_SEMICONDUCTOR_WATCH', 'KR_SIZE_STYLE_INDEX'}:
            label = '반도체 관심 업종(별도)' if market == 'us' else '규모별 지수(별도)'
            name = code if market == 'us' else row['sector']
            auxiliary.append(dict(binding=binding, text=f'{scope} {label} {name}: {value:+.2f}% · {session} · source-row {digest(row)}'))
    # This is an internal filtered view of an already verified original value,
    # not an alternate original receipt or a supplied value-hash authority.
    projected['value_sha256'] = digest(projected['value'])
    result = _render_component_sectors(projected)
    auxiliary.sort(key=lambda x: (x['binding']['venue'], x['binding']['raw_symbol']))
    result.update(contract=VERSION, registry=REGISTRY, registry_sha256=REGISTRY_SHA256,
                  classification_ledger=ledger, auxiliary=auxiliary,
                  original_value_sha256=reference['value_sha256'], projection_value_sha256=projected['value_sha256'])
    counts = Counter(f['fields'].get('market_scope', 'US') for f in result['source_view']['fact_catalog'])
    result['candidate_counts'] = {venue: dict(original=sum(x['venue'] == venue for x in ledger),
        categories=dict(Counter(x['category'] for x in ledger if x['venue'] == venue)), ranking=counts[venue])
        for venue in (('US',) if market == 'us' else ('KOSPI', 'KOSDAQ'))}
    result['coverage'] = 'PASS' if all(v['ranking'] >= 6 for v in result['candidate_counts'].values()) else 'PARTIAL_SECTOR_COVERAGE'
    result['text'] += '\n'.join(x['text'] for x in auxiliary) + '\n'
    result['text_sha256'] = hashlib.sha256(result['text'].encode()).hexdigest()
    return result
