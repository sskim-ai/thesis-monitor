"""Visibility-only market selection, bound to the unchanged internal fact catalog."""

from datetime import date
from math import isclose
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.macro.providers.market import MARKET_SYMBOLS
from app.services.market_numeric_claim_service import digest, number, numeric_catalog
from app.services.macro_source_time import CONTRACT as TIME_CONTRACT

CONTRACT = 'market-selected-display-v1'
US_SECTORS = tuple(k for k, v in MARKET_SYMBOLS.items() if v == 'sector')
US_MACRO = ('DGS3', 'DGS5', 'DGS10', 'DGS30', 'DFII10', 'T10YIE', 'DCOILWTICO', 'VIXCLS')


class DisplayBinding(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    fact_id: str
    field_path: str
    value: float
    unit: str
    registry_row_sha256: str
    fact_sha256: str


class DisplayItem(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    block_id: str
    display_order: int
    label: str
    fact_ids: tuple[str, ...] = ()
    bindings: tuple[DisplayBinding, ...] = ()
    observation_dates: tuple[str, ...] = ()
    required: bool = True
    status: Literal['AVAILABLE', 'UNAVAILABLE']
    unavailable_policy: str = '자료 부족'
    format_id: str
    text: str
    proof: dict = {}


class MarketDisplayPlan(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    contract: Literal['market-selected-display-v1'] = CONTRACT
    market: Literal['us', 'kr']
    assessment_date: str
    completed_session: str
    internal_source_sha256: str
    eligible_refs: tuple[str, ...]
    items: tuple[DisplayItem, ...]


def build_display_plan(source, *, market, assessment_date, eligible_refs):
    session = source.get('session') or {}
    completed = session.get('latest_completed_regular_session_date')
    if (market not in {'us', 'kr'} or date.fromisoformat(completed) > date.fromisoformat(assessment_date)
            or session.get('market', market) != market
            or session.get('assessment_date', assessment_date) != assessment_date):
        raise ValueError('display_session_mismatch')
    facts = source.get('fact_catalog') or []
    by_id = {f['fact_id']: f for f in facts}
    if len(by_id) != len(facts):
        raise ValueError('display_duplicate_fact')
    registry = {}
    for row in source.get('numeric_registry') or []:
        key = (row['fact_id'], row['field_path'])
        if key in registry:
            raise ValueError('display_duplicate_registry_key')
        registry[key] = row
    eligible = set(eligible_refs)
    items = []

    def bind(fact, field, units):
        fields = fact['fields']
        row = registry.get((fact['fact_id'], 'fields.' + field), {})
        if (fact['fact_id'] not in eligible or not number(fields.get(field))
                or row.get('registered') is not True or row.get('prose_allowed') is not True
                or row.get('scope') not in {'market', 'both'} or row.get('unit') not in units
                or row.get('value') != fields[field]):
            return None
        return DisplayBinding(fact_id=fact['fact_id'], field_path='fields.' + field,
            value=fields[field], unit=row['unit'], registry_row_sha256=digest(row), fact_sha256=digest(fact))

    def add(block, label, rows=(), bindings=(), *, text=None, proof=None, formatter='canonical-two-decimal'):
        available = text is not None
        items.append(DisplayItem(block_id=block, display_order=len(items), label=label,
            fact_ids=tuple(r['fact_id'] for r in rows), bindings=tuple(bindings),
            observation_dates=tuple(sorted({r['as_of_date'] for r in rows})),
            status='AVAILABLE' if available else 'UNAVAILABLE', format_id=formatter,
            text=text if available else label + ': 자료 부족', proof=proof or {}))

    def current(fact):
        f = fact['fields']
        return (fact['fact_id'] in eligible and fact['as_of_date'] == completed
                and not f.get('source_unavailable') and not f.get('renderer_only')
                and f.get('quality', 'fresh') in {'fresh', 'verified'}
                and f.get('today_signal_eligible') is not False)

    def unique_series(series):
        found = [f for f in facts if f['fields'].get('series_code') == series]
        if len(found) > 1:
            raise ValueError('ambiguous_display_series:' + series)
        return found[0] if found else None

    add('header', '시장', text=('미국' if market == 'us' else '한국') + ' 시장 · ' + completed,
        proof={'session_sha256': digest(session)}, formatter='source-session-date')
    if market == 'us':
        for series in ('SPY', 'QQQ', 'IWM'):
            fact = unique_series(series)
            fields = fact['fields'] if fact else {}
            bindings = [bind(fact, k, units) for k, units in (
                ('close', {'USD'}), ('previous_close', {'USD'}),
                ('change_value', {'USD'}), ('return_pct', {'pct', 'percent'}))] if fact else []
            valid = (fact and current(fact) and all(bindings) and len(bindings) == 4
                and fields['previous_close'] > 0 and fields.get('currency') == 'USD'
                and isclose(fields['close'] - fields['previous_close'], fields['change_value'], abs_tol=1e-9)
                and isclose((fields['close'] / fields['previous_close'] - 1) * 100, fields['return_pct'], abs_tol=1e-9))
            add('indices', series, [fact] if valid else [], bindings if valid else [],
                text=(f"{series}: {fields['close']:,.2f} USD · {fields['change_value']:+.2f} USD "
                      f"({fields['return_pct']:+.2f}%)") if valid else None)

    def macro(series):
        fact = unique_series(series)
        fields = fact['fields'] if fact else {}
        publication = fields.get('publication_context') or {}
        key, units, suffix = ('value', {'KRW'}, '원') if series == 'USDKRW' else (
            ('price_usd_per_barrel', {'USD_per_barrel'}, 'USD/배럴') if series == 'DCOILWTICO' else
            ('level', {'index', 'points', 'point'}, '') if series == 'VIXCLS' else
            ('level_pct', {'pct', 'percent'}, '%'))
        binding = bind(fact, key, units) if fact else None
        valid = bool(fact and binding and publication.get('contract') == TIME_CONTRACT
            and publication.get('latest_available_at_query_time') is True
            and publication.get('display_eligible') is True
            and publication.get('observation_date') == fact['as_of_date']
            and fact['as_of_date'] <= assessment_date
            and publication.get('response_sha256')
            and (series != 'USDKRW' or publication.get('observation_precision') == 'daily'))
        label = fields.get('label', series)
        text = f"{label}: {binding.value:,.2f}{suffix} ({fact['as_of_date']} 관측)" if valid else None
        bindings = [binding] if valid else []
        if valid and series == 'USDKRW':
            change = bind(fact, 'change_pct', {'pct', 'percent'})
            if change and fields.get('today_signal_eligible') is True:
                bindings.append(change)
                text += f' · {change.value:+.2f}%'
        add('fx' if series == 'USDKRW' else 'macro', label, [fact] if valid else [], bindings, text=text,
            proof={'publication_context_sha256': digest(publication)} if valid else {})

    if market == 'us':
        for series in US_MACRO:
            macro(series)
    add('judgment', '시장 판단', text='', formatter='accepted-numeric-free-narrative')

    for venue in (('US',) if market == 'us' else ('KOSPI', 'KOSDAQ')):
        candidates = []
        identities = set()
        for fact in facts:
            fields = fact['fields']
            correct_scope = (fact['fact_type'] == 'market_sector' and fields.get('series_code') in US_SECTORS
                             if market == 'us' else fact['fact_type'] == 'market_cross_section_sector'
                             and fields.get('market_scope') == venue
                             and fields.get('taxonomy') == 'kiwoom-sector-index-v1'
                             and fields.get('metric_role') in {'sector_price_proxy', 'actual_sector_breadth'})
            if not correct_scope or not current(fact):
                continue
            binding = bind(fact, 'return_pct', {'pct', 'percent'})
            if binding:
                identity = fields.get('series_code') if market == 'us' else fields.get('sector_code')
                if not identity or identity in identities:
                    raise ValueError('ambiguous_display_sector:' + venue)
                identities.add(identity)
                candidates.append((fact, binding))
        ordered = sorted(candidates, key=lambda pair: (-pair[1].value, pair[0]['fact_id']))
        proof = dict(venue=venue, session=completed,
            taxonomy='configured-sector-etf-proxies' if market == 'us' else 'kiwoom-sector-index-v1',
            qualified_universe_fact_ids=sorted(f['fact_id'] for f, _ in ordered),
            tie_break='canonical_fact_id_ascending')
        for ranking, selected in (('TOP3', ordered[:3]), ('BOTTOM3', sorted(ordered[-3:], key=lambda x: (x[1].value, x[0]['fact_id'])))):
            if len(ordered) < 6:
                add('sectors', venue + ' ' + ranking, proof=proof)
                continue
            values = [f"{f['fields'].get('sector') or f['fields'].get('label')}: {b.value:+.2f}%" for f, b in selected]
            add('sectors', venue + ' ' + ranking, [f for f, _ in selected], [b for _, b in selected],
                text=venue + ' ' + ranking + ' · ' + ' / '.join(values), proof=proof)

    if market == 'kr':
        macro('USDKRW')
    else:
        catalog = numeric_catalog(source, market=market, assessment_date=assessment_date, eligible_refs=eligible)
        night = [c for c in catalog['claims'] if c['claim_type'] == 'OFFICIAL_NIGHT']
        if len(night) > 1:
            raise ValueError('configured_night_display_ambiguous')
        add('night', '한국 야간선물 · KOSPI200', text=('한국 야간선물 · KOSPI200\n' + night[0]['rendered_text']) if night else None,
            proof={'typed_numeric_claims': night}, formatter='official-night-dwm')
    return MarketDisplayPlan(market=market, assessment_date=assessment_date, completed_session=completed,
        internal_source_sha256=digest(source), eligible_refs=tuple(sorted(eligible)), items=tuple(items))


def render_display_plan(plan, source, narrative):
    expected = build_display_plan(source, market=plan.market, assessment_date=plan.assessment_date,
                                  eligible_refs=plan.eligible_refs)
    if plan != expected:
        raise ValueError('selected_market_display_binding_mismatch')
    if any(char.isnumeric() for char in narrative):
        raise ValueError('untyped_market_narrative_number')
    return '\n\n'.join(narrative if item.block_id == 'judgment' else item.text for item in plan.items)


def final_display_audit(text, plan, source, narrative):
    expected = render_display_plan(plan, source, narrative)
    return dict(status='PASS' if text == expected else 'FAIL',
        errors=[] if text == expected else ['selected_display_final_text_mismatch'],
        selected_fact_ids=sorted({ref for item in plan.items for ref in item.fact_ids}),
        plan_sha256=digest(plan.model_dump(mode='json')), text_sha256=digest(text))
