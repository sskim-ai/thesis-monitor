"""Visibility-only market selection, bound to the unchanged internal fact catalog."""

from datetime import date, datetime
from math import isclose
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.macro.providers.market import MARKET_SYMBOLS
from app.services.market_numeric_claim_service import digest, number, numeric_catalog
from app.services.macro_source_time import CONTRACT as TIME_CONTRACT
from app.services.market_display_view import MarketUserDisplayView, verify_display_view
from app.services.dated_macro_display_claims import MacroCaptureSelection
from app.services.daily_sector_observations import detailed_count, sector_observations
from app.services.kr_close_fx import (
    FX_LABELS, KrCloseFxItem, KrCloseFxObservation, RetainedEcosFxCapture, format_dated_fx, retained_ecos_fx_display, retained_fx_display,
)
from app.services.unified_source_policy import UnifiedSourcePolicy

CONTRACT = 'market-selected-display-v1'
US_SECTORS = tuple(k for k, v in MARKET_SYMBOLS.items() if v == 'sector')
US_MACRO = ('DGS3', 'DGS5', 'DGS10', 'DGS30', 'DFII10', 'T10YIE', 'DCOILWTICO', 'VIXCLS', 'DTWEXBGS')


def _night_unavailable_dates_text(ownership):
    detail = ownership.get('date_only_detail') or {}
    if detail.get('date_basis') != 'KRX_API_REFERENCE_DATE':
        return None
    expected = detail.get('required_krx_reference_date')
    returned = detail.get('latest_returned_krx_reference_date')
    try:
        valid = (isinstance(expected, str) and date.fromisoformat(expected).isoformat() == expected
            and (returned is None or isinstance(returned, str)
                and date.fromisoformat(returned).isoformat() == returned and returned <= expected))
    except ValueError:
        valid = False
    if not valid or expected != (ownership.get('observation_clock') or {}).get('expected_reference_date'):
        return None
    status = '기준일에 맞는 확정 수치 미확보' if returned == expected else '최신 세션 미확보'
    return ('한국 야간선물 · KOSPI200\n' + status
        + '\n필요 KRX 기준일: ' + expected
        + '\n이번 수집에서 확인한 야간 기준일: ' + (returned or '미확보')
        + '\n이번 야간 방향 판단에서 제외')


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
    display_view: MarketUserDisplayView | None = None
    sector_taxonomy_version: Literal['sector-universe-user-confirmed-v2'] | None = Field(default=None, exclude_if=lambda v: v is None)
    macro_display_capture: MacroCaptureSelection | None = Field(default=None, exclude_if=lambda v: v is None)
    sector_observation_audit: tuple[dict, ...] = Field(default=(), exclude_if=lambda v: not v)
    fx_observations: tuple[KrCloseFxObservation, ...] = Field(default=(), exclude_if=lambda v: not v)
    fx_provider_scope: tuple[str, ...] = Field(default=(), exclude_if=lambda v: not v)
    fx_cutoff: datetime | None = Field(default=None, exclude_if=lambda v: v is None)
    ecos_fx_body: str | None = Field(default=None, exclude_if=lambda v: v is None)
    ecos_fx_prior: tuple[RetainedEcosFxCapture, ...] = Field(default=(), exclude_if=lambda v: not v)


def build_display_plan(source, *, market, assessment_date, eligible_refs, display_view=None,
                       sector_taxonomy_version=None, macro_display_capture=None,
                       fx_observations=(), fx_source_policy=None, fx_cutoff=None,ecos_fx_body=None,ecos_fx_prior=()):
    macro_claims = {}
    if macro_display_capture is not None:
        # A pinned archive is not a current Parent/run/cutoff authorization.
        raise ValueError('sealed_macro_capture_offline_source_only_not_current_owner')
    if sector_taxonomy_version not in (None, 'sector-universe-user-confirmed-v2'):
        raise ValueError('display_sector_taxonomy_version')
    from app.services.confirmed_sector_taxonomy import auxiliary_label, relative_rank_text, REGISTRY_SHA256, PROVIDERS
    session = source.get('session') or {}
    completed = session.get('latest_completed_regular_session_date')
    if (market not in {'us', 'kr'} or date.fromisoformat(completed) > date.fromisoformat(assessment_date)
            or session.get('market', market) != market
            or session.get('assessment_date', assessment_date) != assessment_date):
        raise ValueError('display_session_mismatch')
    facts = source.get('fact_catalog') or []
    by_id = {f['fact_id']: f for f in facts}
    sector_refs = {f['fact_id'] for f in facts if f['fact_type'] in {'market_cross_section_sector','market_sector'}}
    nonsectors = [f['fact_id'] for f in facts if f['fact_type'] not in {'market_cross_section_sector','market_sector'}]
    if len(set(nonsectors)) != len(nonsectors) or set(nonsectors) & sector_refs:
        raise ValueError('display_duplicate_fact')
    registry = {}
    bad_sector_registry = set()
    for row in source.get('numeric_registry') or []:
        key = (row['fact_id'], row['field_path'])
        if key in registry:
            if key[0] not in sector_refs:
                raise ValueError('display_duplicate_registry_key')
            bad_sector_registry.add(key)
        registry[key] = row
    eligible = set(eligible_refs)
    display_fields = None
    bound_alias_fields = set()
    if display_view is not None:
        display_view = verify_display_view(display_view, source)
        if (display_view.market != market or display_view.assessment_date != assessment_date
                or set(display_view.origin.directional_refs) != eligible):
            raise ValueError('display_view_directional_identity_mismatch')
        display_fields = {d.fact_ref:set(d.allowed_fields) for d in display_view.decisions if d.status == 'ELIGIBLE'}
        bound_alias_fields = {(b.canonical_ref, b.semantic_field) for b in display_view.identity_bindings}
        eligible = set(display_view.eligible_refs)
    items = []
    retained_fx = {}
    fx_scope = ()
    fx_observations = tuple(fx_observations)
    if fx_observations:
        if market != 'kr' or not isinstance(fx_source_policy,UnifiedSourcePolicy) or fx_cutoff is None:
            raise ValueError('retained_fx_requires_explicit_source_policy_and_cutoff')
        if display_view is not None and fx_cutoff > datetime.fromisoformat(display_view.origin.query_as_of):
            raise ValueError('retained_fx_after_original_source_cutoff')
        fx_scope = tuple(sorted(fx_source_policy.allowed_providers))
        fx_observations = tuple(r for r in fx_observations if fx_source_policy.permits(r.provider))
        retained_fx = retained_fx_display(fx_observations,completed=completed,cutoff=fx_cutoff,source_policy=fx_source_policy)
    if not fx_observations:
        fx_scope,fx_cutoff = (),None
    ecos_fx_prior = tuple(ecos_fx_prior)
    if ecos_fx_prior and ecos_fx_body is None:
        raise ValueError('retained_ecos_fx_current_capture_required')
    if ecos_fx_body is not None:
        if market!='kr' or display_view is None or not isinstance(fx_source_policy,UnifiedSourcePolicy):
            raise ValueError('retained_ecos_fx_requires_verified_display_origin_and_policy')
        matches = [f for f in facts if f['fields'].get('series_code')=='USDKRW']
        if len(matches)!=1:
            raise ValueError('retained_ecos_fx_usd_anchor_missing')
        anchor = matches[0]
        origin = display_view.origin.publication_origins.get(anchor['fact_id'],{})
        extras = retained_ecos_fx_display(ecos_fx_body,publication=anchor['fields']['publication_context'],
            source_hashes=origin.get('source_hashes',()),anchor_value=anchor['fields']['value'],source_policy=fx_source_policy,
            prior_captures=ecos_fx_prior)
        retained_fx.update({k:v for k,v in extras.items() if k not in retained_fx})
        fx_scope = tuple(sorted(fx_source_policy.allowed_providers))

    def bind(fact, field, units, *, observation=False):
        fields = fact['fields']
        row = registry.get((fact['fact_id'], 'fields.' + field), {})
        if (not number(fields.get(field))
                or (not observation and (fact['fact_id'] not in eligible
                or (display_fields is not None and 'fields.' + field not in display_fields.get(fact['fact_id'], set()))
                or (row.get('prose_allowed') is not True and (fact['fact_id'], 'fields.' + field) not in bound_alias_fields)))
                or row.get('registered') is not True
                or row.get('scope') not in {'market', 'both'} or row.get('unit') not in units
                or row.get('value') != fields[field]):
            return None
        return DisplayBinding(fact_id=fact['fact_id'], field_path='fields.' + field,
            value=fields[field], unit=row['unit'], registry_row_sha256=digest(row), fact_sha256=digest(fact))

    def add(block, label, rows=(), bindings=(), *, text=None, proof=None,
            formatter='canonical-two-decimal', unavailable_text=None):
        available = text is not None
        items.append(DisplayItem(block_id=block, display_order=len(items), label=label,
            fact_ids=tuple(r['fact_id'] for r in rows), bindings=tuple(bindings),
            observation_dates=tuple(sorted({r['as_of_date'] for r in rows})),
            status='AVAILABLE' if available else 'UNAVAILABLE', format_id=formatter,
            text=text if available else (unavailable_text or label + ': 자료 부족'), proof=proof or {}))

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
        rsp = unique_series('RSP')
        if rsp and current(rsp) and (ret := bind(rsp, 'return_pct', {'pct','percent'})):
            add('style', 'S&P500 동일가중', [rsp], [ret], text=f"RSP 동일가중: {ret.value:+.2f}% · {completed}")
    elif display_view is not None:
        for symbol in ('KOSPI', 'KOSDAQ'):
            matches = [f for f in facts if f['fact_type'] == 'market_cross_section_index'
                       and f['fields'].get('symbol') == symbol]
            if len(matches) > 1:
                raise ValueError('ambiguous_display_index:' + symbol)
            fact = matches[0] if matches else None
            bindings = [bind(fact, 'close', {'index'}), bind(fact, 'return_pct', {'pct'})] if fact else []
            valid = bool(fact and current(fact) and len(bindings) == 2 and all(bindings))
            add('indices', symbol, [fact] if valid else [], bindings if valid else [],
                text=(f"{symbol}: {fact['fields']['close']:,.2f} · {fact['fields']['return_pct']:+.2f}%") if valid else None)

    def macro(series):
        fact = unique_series(series)
        fields = fact['fields'] if fact else {}
        publication = fields.get('publication_context') or {}
        is_fx = series == 'USDKRW' or series in FX_LABELS
        key, units, suffix = ('value', {'KRW'}, '원') if is_fx else (
            ('price_usd_per_barrel', {'USD_per_barrel'}, 'USD/배럴') if series == 'DCOILWTICO' else
            ('level', {'index', 'points', 'point'}, '') if series in {'VIXCLS', 'DTWEXBGS'} else
            ('level_pct', {'pct', 'percent'}, '%'))
        binding = bind(fact, key, units, observation=is_fx and display_view is None) if fact else None
        valid = bool(fact and binding and publication.get('contract') == TIME_CONTRACT
            and publication.get('latest_available_at_query_time') is True
            and publication.get('display_eligible') is True
            and publication.get('series_code') == series
            and publication.get('freshness_state') in {'CURRENT_SESSION_OR_DATE', 'LATEST_PUBLISHED_VERIFIED'}
            and publication.get('observation_date') == fact['as_of_date']
            and fact['as_of_date'] <= assessment_date
            and publication.get('response_sha256')
            and (not is_fx or publication.get('observation_precision') == 'daily'))
        if valid and is_fx:
            from app.services.latest_published_fx import validate_context
            # A published FX observation need not share the equity close date.
            valid = fields.get('provider')=='ecos' and validate_context(publication, observation_date=fact['as_of_date'],
                response_hashes={publication['response_sha256']}, query_as_of=publication['query_as_of'], series=series)
            if series != 'USDKRW':
                from app.macro.providers.ecos_daily_fx import DAILY_FX
                valid = bool(valid and fields.get('fx_quote_unit') == DAILY_FX[series][2]
                    and fields.get('fx_series_basis') == 'ECOS_OFFICIAL_DAILY')
        label = fields.get('label', series)
        text = f"{label}: {binding.value:,.2f}{suffix} ({fact['as_of_date']} 관측)" if valid else None
        bindings = [binding] if valid else []
        derived = macro_claims.get(series)
        if valid and derived is not None:
            if (derived['raw_sha256'] != publication['response_sha256'] or derived['level'] != fields[key]
                    or derived['observation_date'] != fact['as_of_date']
                    or derived['query_as_of'] != publication['query_as_of']):
                raise ValueError('display_macro_original_fact_binding')
            if series in {'DGS3','DGS5','DGS10','DGS30'}:
                from app.services.dated_macro_display_claims import yield_line
                text = yield_line(label, derived['level'], derived['delta_bp'], derived['observation_date'], derived['previous_observation_date'])
            elif series in {'DCOILWTICO','DTWEXBGS','VIXCLS'}:
                delta = f"{derived['change_pct']:+.2f}%" if derived['change_pct'] is not None else '변동률 자료 부족'
                previous = derived['previous_observation_date'] or '자료 부족'
                text += f' · {delta} (직전 {previous} 대비)'
        if valid and not is_fx and display_view is not None:
            from app.services.market_display_view import publication_comparison_fields
            change_fields = publication_comparison_fields(fact)
            prior_date = fields.get('previous_observation_date')
            delta_key, delta_units = ('change_bp', {'bp'}) if key == 'level_pct' else ('return_pct', {'pct','percent'})
            prior_key = 'previous_level_pct' if key == 'level_pct' else 'previous_value'
            if {'fields.' + delta_key, 'fields.' + prior_key} <= change_fields:
                previous, delta = bind(fact, prior_key, units), bind(fact, delta_key, delta_units)
                if previous and delta:
                    bindings.extend([previous, delta])
                    suffix_delta = 'bp' if delta_key == 'change_bp' else '%'
                    text += f" · {delta.value:+.2f}{suffix_delta} (직전 {prior_date} 대비)"
                    if series == 'VIXCLS' and 'fields.change_value' in change_fields:
                        points = bind(fact, 'change_value', {'points'})
                        if points:
                            bindings.append(points)
                            text += f" · {points.value:+.2f}pt"
        if valid and is_fx:
            if series == 'USDKRW' and (display_view is None or 'fields.change_pct' not in display_fields.get(fact['fact_id'], set())):
                text = format_dated_fx(KrCloseFxItem(series, '원/달러',
                    binding.value, observation_date=fact['as_of_date']))
            else:
                previous = bind(fact, 'previous_value', {'KRW'}, observation=display_view is None)
                delta = bind(fact, 'change_value', {'KRW'}, observation=display_view is None)
                pct = bind(fact, 'change_pct', {'pct'}, observation=display_view is None)
                prior_date = fields.get('previous_observation_date')
                try:
                    comparable = bool(previous and delta and pct and previous.value > 0
                        and date.fromisoformat(prior_date) < date.fromisoformat(fact['as_of_date'])
                        and fields.get('change_input_response_sha256') == publication['response_sha256']
                        and isclose(binding.value-previous.value, delta.value, rel_tol=1e-12, abs_tol=1e-9)
                        # The shared macro storage owner records four decimals.
                        and isclose(round(delta.value/previous.value*100, 4), pct.value,
                                    rel_tol=1e-12, abs_tol=1e-9))
                except (TypeError, ValueError):
                    comparable = False
                if comparable:
                    bindings.extend([previous, delta, pct])
                text = format_dated_fx(KrCloseFxItem(series, FX_LABELS.get(series, '원/달러'), binding.value,
                    change_value=delta.value if comparable else None,
                    change_pct=pct.value if comparable else None,
                    observation_date=fact['as_of_date'], comparison_date=prior_date if comparable else None))
                text += ' · ECOS 일별 환율'
        add('fx' if is_fx else 'macro', label, [fact] if valid else [], bindings, text=text,
            proof={'publication_context_sha256': digest(publication), **({'display_only_derived_claim_id':derived['claim_id'],
                'derived_registry_sha256':digest(derived['numeric_registry']), 'direction_eligible':False} if derived else {})} if valid else {})

    if market == 'us':
        for series in US_MACRO:
            macro(series)
        display_only = sorted({ref for item in items if item.block_id == 'macro'
            and item.status == 'AVAILABLE' for ref in item.fact_ids
            if ref not in set(eligible_refs)})
        if display_only:
            add('macro_note', '거시 관측 사용 범위',
                text='최신 발표 거시 관측은 실제 관측일의 금융 여건을 설명하며, 완료장 시장 방향의 직접 근거와 구분합니다.',
                proof={'display_only_refs': display_only, 'directional_authority_added': False},
                formatter='display-only-note')
    add('judgment', '시장 판단', text='', formatter='accepted-numeric-free-narrative')

    observed, sector_audit = sector_observations(facts, registry, market=market,
        completed=completed, bad_registry=bad_sector_registry)
    for venue in (('US',) if market == 'us' else ('KOSPI', 'KOSDAQ')):
        candidates = []
        for v, code, category, fact, row in observed:
            if v != venue:
                continue
            binding = DisplayBinding(fact_id=fact['fact_id'],field_path='fields.return_pct',
                value=row['value'],unit=row['unit'],registry_row_sha256=digest(row),fact_sha256=digest(fact))
            if category in {'KR_DETAILED_INDUSTRY','US_BROAD_SECTOR'}:
                candidates.append((code,fact,binding))
            elif category in {'US_SEMICONDUCTOR_WATCH','KR_SIZE_STYLE_INDEX'}:
                label = auxiliary_label(market, venue, code)
                add('sector_auxiliary',venue+' '+label,[fact],[binding],
                    text=f"{venue} {label} {fact['fields'].get('sector') or code}: {binding.value:+.2f}% · {completed}",
                    proof=dict(provider=PROVIDERS[market],registry_sha256=REGISTRY_SHA256,category=category,observation_only=True))
        partial = len(candidates) < detailed_count(venue)
        proof = dict(venue=venue, session=completed,
            taxonomy='configured-sector-etf-proxies' if market == 'us' else 'kiwoom-sector-index-v1',
            observed_universe_fact_ids=sorted(f['fact_id'] for _, f, _ in candidates),
            partial=partial, tie_break='sector_code_ascending', directional_authority_added=False)
        for ranking, sign in (('TOP3',-1),('BOTTOM3',1)):
            label = relative_rank_text(venue+' '+ranking)
            selected = sorted(candidates,key=lambda x:(sign*x[2].value,x[0]))[:3]
            if not selected:
                add('sectors',label,proof=proof,unavailable_text=label+': 관측값 미확보')
                continue
            values = [f"{f['fields'].get('sector') or f['fields'].get('label') or code}: {b.value:+.2f}%" for code,f,b in selected]
            add('sectors',label,[f for _,f,_ in selected],[b for _,_,b in selected],
                text=label+(' (확보 업종 기준)' if partial else '')+' · '+' / '.join(values),proof=proof)

    if market == 'kr':
        # Existing aggregate flow claims remain market-level observations;
        # their display does not grant stock attribution or directional rights.
        catalog = numeric_catalog(source, market=market, assessment_date=assessment_date, eligible_refs=eligible_refs)
        for claim in catalog['claims']:
            if claim['claim_type'] != 'DATED_AGGREGATE_FLOW':
                continue
            ref = claim['components'][0]['source_fact_ref']
            fact = by_id.get(ref)
            if fact is None:
                continue
            flow_binding = bind(fact, 'net_buy_amount', {'KRW'}, observation=True)
            if flow_binding:
                from decimal import Decimal
                amount = Decimal(str(flow_binding.value)) / Decimal(100000000)
                labels = {'foreign':'외국인','institution':'기관','retail':'개인'}
                fields = fact['fields']
                text = f"{fields['market_scope']} {labels[fields['actor']]} {amount:+,.2f}억원"
                add('flows', '시장 수급', [fact], [flow_binding], text=text,
                    proof={'existing_numeric_claim_id':claim['claim_id'],
                           'scope':'AGGREGATE_ONLY_NOT_STOCK_ATTRIBUTION'})
        add('fx_note','환율 관측',text='환율은 실제 관측일의 금융 여건이며, 당일 수급의 원인으로 단정하지 않습니다.',formatter='display-only-note')
        for series,label in FX_LABELS.items():
            if series != 'USDKRW_KR_CLOSE' and unique_series(series) is not None:
                macro(series)
            elif series in retained_fx:
                item,proof = retained_fx[series]
                anchor = unique_series('USDKRW') if series=='USDKRW_KR_CLOSE' and 'raw_response_sha256' in proof else None
                basis = ' · ECOS 매매기준율' if proof.get('series_basis')=='ECOS_REFERENCE_RATE' else ''
                add('fx',label,[anchor] if anchor else [],text=format_dated_fx(item)+basis,proof=proof,formatter='dated-fx-observation')
            elif series=='USDKRW_KR_CLOSE':
                macro('USDKRW')
            else:
                add('fx',label,unavailable_text=label+': 관측값 미확보')
    else:
        catalog = numeric_catalog(source, market=market, assessment_date=assessment_date, eligible_refs=eligible_refs)
        night = [c for c in catalog['claims'] if c['claim_type'] == 'OFFICIAL_NIGHT']
        night_ownership = source.get('night_futures_ownership') or {}
        from app.services.optional_night_source import FAILURE_NOTICES
        if night_ownership.get('state') == 'EXCLUDED_BEFORE_COLLECTION':
            from scripts.m12ds_r4_r4_market import NIGHT_EXCLUSION_NOTICE
            if (night or source.get('night_futures')
                    or any(f['fact_type'].startswith('night_futures') for f in facts)):
                raise ValueError('excluded_night_display_has_observations')
            add('night', '한국 야간선물', unavailable_text=NIGHT_EXCLUSION_NOTICE,
                proof={'night_ownership': night_ownership}, formatter='excluded-before-collection-note')
        elif night_ownership.get('state') in FAILURE_NOTICES:
            if (night or source.get('night_futures')
                    or any(f['fact_type'].startswith('night_futures') for f in facts)):
                raise ValueError('unavailable_night_display_has_observations')
            add('night', '한국 야간선물', unavailable_text=FAILURE_NOTICES[night_ownership['state']],
                proof={'night_ownership': night_ownership}, formatter='optional-night-unavailable-note')
        elif (night_ownership.get('state') == 'UNAVAILABLE_NO_CURRENT_FINAL_ROW'
                and (date_notice := _night_unavailable_dates_text(night_ownership))):
            if (night or source.get('night_futures')
                    or any(f['fact_type'].startswith('night_futures') for f in facts)):
                raise ValueError('unavailable_night_display_has_observations')
            add('night', '한국 야간선물', unavailable_text=date_notice,
                proof={'night_ownership': night_ownership}, formatter='optional-night-date-availability-note')
        else:
            if len(night) > 1:
                raise ValueError('configured_night_display_ambiguous')
            refs = {part['source_fact_ref'] for claim in night for part in claim['components']}
            add('night', '한국 야간선물 · KOSPI200', [by_id[ref] for ref in sorted(refs) if ref in by_id],
                text=('한국 야간선물 · KOSPI200\n' + night[0]['rendered_text']) if night else None,
                proof={'typed_numeric_claims': night}, formatter='official-night-dwm',
                unavailable_text='한국 야간선물 · KOSPI200\n일: 자료 부족\n주: 자료 부족\n월: 자료 부족')
    return MarketDisplayPlan(market=market, assessment_date=assessment_date, completed_session=completed,
        internal_source_sha256=digest(source), eligible_refs=tuple(sorted(eligible_refs)), items=tuple(items),
        display_view=display_view, sector_taxonomy_version=sector_taxonomy_version, macro_display_capture=macro_display_capture,
        sector_observation_audit=tuple(sector_audit),fx_observations=fx_observations,
        fx_provider_scope=fx_scope,fx_cutoff=fx_cutoff,ecos_fx_body=ecos_fx_body,ecos_fx_prior=ecos_fx_prior)


def render_display_plan(plan, source, narrative):
    expected = build_display_plan(source, market=plan.market, assessment_date=plan.assessment_date,
                                  eligible_refs=plan.eligible_refs, display_view=plan.display_view,
                                  sector_taxonomy_version=plan.sector_taxonomy_version, macro_display_capture=plan.macro_display_capture,
                                  fx_observations=plan.fx_observations,fx_cutoff=plan.fx_cutoff,
                                  ecos_fx_body=plan.ecos_fx_body,ecos_fx_prior=plan.ecos_fx_prior,
                                  fx_source_policy=UnifiedSourcePolicy(frozenset(plan.fx_provider_scope)) if plan.fx_provider_scope else None)
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
