"""Versioned /ohlcv projection. Native indicators are data, never recomputed.

Count limits are collection ceilings, not admission minima. Completion and
source identity remain separate from count and from current-price authority.
"""
from copy import deepcopy
from datetime import date, datetime, timedelta
import calendar as civil_calendar
import math
import re
from typing import Any, Callable, Literal, Mapping
from pydantic import BaseModel, ConfigDict
from app.services.unified_snapshot_contract import digest
from app.services.ohlcv_completed_bar_finality_service import assess_completed_bar_finality

CONTRACT = 'provider-native-technical-view-v2'
MAX_COUNTS = {'daily': 1000, 'weekly': 700, 'monthly': 300}
PIVOT_LOOKBACKS = {'daily': 300, 'weekly': 120, 'monthly': 60}
# Schema copied from the pinned Analyst INDICATOR_COLUMNS, not a calculator.
INDICATORS = ('MA33','MA111','MA144','MA222','MA288',
    'BB_36_1.541_MID','BB_36_1.541_UPPER','BB_36_1.541_LOWER',
    'BB_50_2.25_MID','BB_50_2.25_UPPER','BB_50_2.25_LOWER',
    'BB_60_1.541_MID','BB_60_1.541_UPPER','BB_60_1.541_LOWER',
    'BB_144_1.541_MID','BB_144_1.541_UPPER','BB_144_1.541_LOWER',
    'BB_288_1.541_MID','BB_288_1.541_UPPER','BB_288_1.541_LOWER',
    'BB_300_3.33_MID','BB_300_3.33_UPPER','BB_300_3.33_LOWER',
    'ENV_200_20_LOWER','ENV_200_20_UPPER','RSI14','MACD','MACD_SIGNAL','MACD_HIST',
    'MACD_OSC_20_40_9','MACD_OSC_40_80_9','MACD_OSC_80_160_9','MACD_OSC_320_640_9',
    'VOLUME_MA20','VOLUME_RATIO_20','RETURN_20D','RETURN_60D','DRAWDOWN_52W')
FORMULA_VERSION = 'ohlcv-analyst-native-38-v1'
FORMULAS = dict(RSI14='rolling-simple-gain-loss-14; NOT Wilder',
    MACD='EMA adjust=False 12/26/9; provider seed',
    BB='rolling mean and sample std ddof=1; exact field period/multiplier',
    RETURN_20D='20 bars, not calendar days',RETURN_60D='60 bars, not calendar days',
    DRAWDOWN_52W='252 bars of the requested timeframe; provider field name retained')


class NativePeriod(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    timeframe: str
    status: Literal['AVAILABLE','UNAVAILABLE','INVALID']
    returned_count: int
    max_count: int
    completed_count: int
    source_hash: str
    provider: str
    completed_as_of: str | None
    raw_bar_date: str | None
    rows: tuple[dict[str, Any], ...] = ()
    indicators: dict[str, Any]
    indicator_quality: dict[str, str]
    quarantined_count: int = 0
    reasons: tuple[str, ...] = ()


class ProviderNativeTechnicalView(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    contract: Literal['provider-native-technical-view-v2'] = CONTRACT
    provider: str = 'ohlcv_analyst'
    provider_code: str
    market: Literal['kr','us']
    adjusted: Literal[True] = True
    cutoff: str
    indicator_schema: str = FORMULA_VERSION
    periods: dict[str, NativePeriod]
    source_hash: str
    view_sha256: str
    current_price_qualified: Literal[False] = False
    strict_ready: Literal[False] = False
    allowed_use: Literal['DATED_TECHNICAL_ANALYSIS', 'MONITORING_TECHNICAL'] = 'DATED_TECHNICAL_ANALYSIS'

    def verify(self):
        if digest(self.model_dump(mode='json', exclude={'view_sha256'})) != self.view_sha256:
            raise ValueError('native_technical_view_changed')
        return self

    def completed_periods(self):
        self.verify()
        return {tf:deepcopy(list(p.rows)) for tf,p in self.periods.items()}

    def prompt_payload(self):
        self.verify()
        result=self.model_dump(mode='json')
        for timeframe, period in result['periods'].items():
            period.pop('rows')
            if self.allowed_use == 'MONITORING_TECHNICAL':
                comparison = recent_completed_comparison(self.periods[timeframe])
                if comparison is not None:
                    period['recent_comparison'] = comparison
                recent = recent_completed_path(self.periods[timeframe])
                if recent is not None:
                    period['recent_path'] = recent
        if self.allowed_use == 'MONITORING_TECHNICAL':
            result['comparison_version'] = 1
        result['formula_semantics']=FORMULAS
        result['stored_price_rules_owner']='SEPARATE_NOT_MODIFIED'
        return result


def _valid_number(value):
    try:return type(value) in (int,float) and math.isfinite(value)
    except OverflowError:return False


RECENT_PATH_FIELDS = ('RSI14','MACD','MACD_HIST','VOLUME_RATIO_20')


def recent_completed_path(period):
    """Exact last twenty completed observations; no interpolation/calculation."""
    if (period.status != 'AVAILABLE' or not period.rows
            or str(period.rows[-1]['date'])[:10] != period.completed_as_of):
        return None
    rows = period.rows[-20:]
    def finite(value):
        return value if _valid_number(value) else None
    fields = {field: [finite((r.get('indicators') or {}).get(field)) for r in rows]
              for field in RECENT_PATH_FIELDS
              if period.indicator_quality.get(field) == 'PROVIDER_NATIVE'
              and _valid_number(period.indicators.get(field))}
    return dict(dates=[str(r['date'])[:10] for r in rows],
                close=[finite(r.get('close')) for r in rows],
                volume=[finite(r.get('volume')) for r in rows],
                indicators=fields)


def recent_completed_comparison(period):
    """Compact observations from the verified native period, not recalculated indicators.

    The caller's period.source_hash already binds the artifact and completed rows.
    Lag slots are literal completed-row offsets; never search backwards for a null.
    Relation strings cover only their explicitly listed dates (not an older crossing).
    """
    rows = period.rows
    if (period.status != 'AVAILABLE' or not rows
            or str(rows[-1]['date'])[:10] != period.completed_as_of):
        return None
    samples = [rows[-1-n] if len(rows) > n else None for n in (0, 1, 5)]
    def finite(row, key):
        value = row.get(key) if row is not None else None
        return value if _valid_number(value) else None
    def native_value(row, field):
        values = row.get('indicators') if row is not None else None
        return finite(values if isinstance(values, Mapping) else None, field)
    fields = [f for f in INDICATORS if period.indicator_quality.get(f) == 'PROVIDER_NATIVE'
              and _valid_number(period.indicators.get(f))]
    prior = {f: [native_value(row, f) for row in samples[1:]] for f in fields}
    prior = {f: values for f, values in prior.items() if any(v is not None for v in values)}
    recent = rows[-6:]
    def relation(row, field):
        close, level = finite(row, 'close'), native_value(row, field)
        if close is None or level is None:
            return '?'
        return 'A' if close > level else 'B' if close < level else 'E'
    # Compact dated A/B/E/? sequence lets the model distinguish a maintained
    # relation from an observed intervening breach/recovery. No synthetic dates.
    relations = {f: ''.join(relation(row, f) for row in recent) for f in fields
                 if f in INDICATORS[:5] or f.startswith(('BB_', 'ENV_'))}
    relations = {f: value for f, value in relations.items() if len(value.replace('?', '')) > 1}
    return dict(dates=[str(row['date'])[:10] if row is not None else None for row in samples],
        close=[finite(row, 'close') for row in samples],
        volume=[finite(row, 'volume') for row in samples],
        prior_indicators=prior, relation_dates=[str(row['date'])[:10] for row in recent],
        close_relations=relations)


def _completed(row, *, timeframe, cutoff, verifier):
    if verifier is not None:
        # Only a trusted backend may supply an original, reviewed completion
        # Owner. No HTTP response boolean creates this callback or an Owner.
        return verifier(row, timeframe, cutoff) is True
    if timeframe != 'daily':
        return False  # Existing provider W/M label registry is still unproven.
    finality=assess_completed_bar_finality(row,cutoff=cutoff)
    return finality.state == 'FINAL'


def historical_period_eligibility(row, *, timeframe, market, cutoff, observed_at, later_dates, calendar=None):
    """Closed historical chart observations, not official/final close ownership.

    A later native period plus the exchange calendar avoids relying on whether
    the provider's date labels the start or end session of a historical bucket.
    The newest W/M bucket is intentionally not admitted by this fallback.
    """
    from app.services.price_structure_wave_fibonacci_v3_service import _calendar_for_range
    if observed_at is None or observed_at.utcoffset() is None:
        return False
    capture = row.get('_native_capture', {})
    if capture.get('provider') != 'kiwoom':
        return False
    day = date.fromisoformat(row['date'])
    marker = str(row.get('bar_state') or row.get('completion_state') or '').upper()
    if marker in {'PROVISIONAL', 'PARTIAL', 'OPEN', 'LIVE', 'UNCONFIRMED', 'UNKNOWN'}:
        return False
    if timeframe == 'daily':
        start = end = day
        later = any(d > day for d in later_dates)
    elif timeframe == 'weekly':
        start = day - timedelta(days=day.weekday())
        end = start + timedelta(days=6)
        later = any(d > end for d in later_dates)
    elif timeframe == 'monthly':
        start = day.replace(day=1)
        end = day.replace(day=civil_calendar.monthrange(day.year, day.month)[1])
        later = any(d > end for d in later_dates)
    else:
        return False
    if not later:
        return False
    exchange = calendar
    if exchange is None:
        _, exchange = _calendar_for_range(market.upper(), start=start, end=end)
    try:
        sessions = exchange.sessions_in_range(start, end)
        if not len(sessions) or (timeframe == 'daily' and not exchange.is_session(day)):
            return False
        last = sessions[-1]
        return last.date() <= cutoff and exchange.session_close(last).to_pydatetime() <= observed_at
    except (ValueError, IndexError, TypeError):
        return False


def build_provider_native_view(*, ticker, market, periods, cutoff,
                               completion_verifier: Callable | None = None,
                               observed_at: datetime | None = None, historical_reference=False):
    output={}
    for tf,maximum in MAX_COUNTS.items():
        raw=deepcopy(list(periods.get(tf,())))
        source_hash=digest(raw);reasons=[];valid=[];dates=[];invalid=False;captures=set()
        source_dates = []
        for source in raw:
            try:source_dates.append(date.fromisoformat(source['date']))
            except (ValueError, KeyError, TypeError):pass
        historical_calendar = None
        if historical_reference and source_dates:
            from app.services.price_structure_wave_fibonacci_v3_service import _calendar_for_range
            _, historical_calendar = _calendar_for_range(market.upper(), start=min(source_dates),
                end=max(max(source_dates), cutoff) + timedelta(days=40))
        for row in raw:
            if not isinstance(row,Mapping):invalid=True;reasons.append('INVALID_ROW');continue
            capture=row.get('_native_capture')
            if (not isinstance(capture,Mapping) or capture.get('code')!=ticker
                    or capture.get('market')!=market or capture.get('adjusted') is not True
                    or capture.get('timeframe')!=tf
                    or not re.fullmatch('[a-f0-9]{64}',capture.get('response_body_sha256') or '')):
                invalid=True;reasons.append('NATIVE_IDENTITY_OR_BASIS_REQUIRED');continue
            captures.add((capture.get('provider'),capture.get('response_body_sha256'),capture.get('response_sha256'),capture.get('exchange')))
            original={k:v for k,v in row.items() if k not in ('_native_capture','supply_demand')}
            if digest(original)!=capture.get('normalized_bar_sha256'):
                invalid=True;reasons.append('NATIVE_SOURCE_HASH_MISMATCH');continue
            try:d=date.fromisoformat(row['date'])
            except (ValueError,KeyError,TypeError):invalid=True;reasons.append('INVALID_DATE');continue
            dates.append(d)
            values=[row.get(k) for k in ('open','high','low','close')]
            if (not all(_valid_number(v) and v>0 for v in values)
                    or not values[2]<=values[0]<=values[1] or not values[2]<=values[3]<=values[1]
                    or (row.get('volume') is not None and (not _valid_number(row['volume']) or row['volume']<0))):
                invalid=True;reasons.append('INVALID_OHLCV');continue
            if d>cutoff:
                reasons.append('FUTURE_OR_UNCOMPLETED_QUARANTINED');continue
            completed = _completed(row,timeframe=tf,cutoff=cutoff,verifier=completion_verifier)
            if historical_reference and completion_verifier is None:
                completed = False  # An HTTP FINAL marker is not a new price grant.
            historical = (historical_reference and historical_period_eligibility(row,
                timeframe=tf,market=market,cutoff=cutoff,observed_at=observed_at,later_dates=source_dates,
                calendar=historical_calendar))
            if not completed and not historical:
                reasons.append('FINALITY_OR_PERIOD_LABEL_UNPROVEN');continue
            if historical and not completed:
                reasons.append('HISTORICAL_CHART_REFERENCE_NOT_OFFICIAL_FINAL_CLOSE')
            valid.append(row)
        if dates!=sorted(set(dates)):
            invalid=True;reasons.append('DUPLICATE_OR_UNORDERED_DATE')
        if len(captures)>1:
            invalid=True;reasons.append('CONFLICTING_SOURCE_CAPTURES')
        if invalid:valid=[]
        selected=valid[-maximum:]
        native=selected[-1].get('indicators') if selected else None
        values={key:deepcopy(native.get(key)) if isinstance(native,dict) else None for key in INDICATORS}
        quality={}
        for key,value in values.items():
            quality[key]='PROVIDER_NATIVE' if _valid_number(value) else 'UNAVAILABLE_PROVIDER_NULL_OR_MISSING'
            if value is not None and not _valid_number(value):
                quality[key]='INVALID_PROVIDER_VALUE'
            if key.startswith('MACD_OSC_'):
                slow=int(key.split('_')[-2]);signal=int(key.split('_')[-1])
                if len(selected)<slow+signal and value is not None:quality[key]='WARMUP_NOT_PROVEN'
        output[tf]=NativePeriod(timeframe=tf,status='INVALID' if invalid else 'AVAILABLE' if selected else 'UNAVAILABLE',
            provider=str(raw[0].get('_native_capture',{}).get('provider','UNKNOWN')) if raw and isinstance(raw[0],dict) else 'UNKNOWN',
            returned_count=len(raw),max_count=maximum,completed_count=len(selected),source_hash=source_hash,
            completed_as_of=selected[-1]['date'] if selected else None,
            raw_bar_date=raw[-1].get('date') if raw and isinstance(raw[-1],dict) else None,
            rows=tuple(selected),indicators=values,indicator_quality=quality,
            quarantined_count=len(raw)-len(valid),reasons=tuple(dict.fromkeys(reasons)))
    data=dict(provider_code=ticker,market=market,cutoff=cutoff.isoformat(),periods=output,
              source_hash=digest({tf:p.source_hash for tf,p in output.items()}))
    provisional=ProviderNativeTechnicalView(**data,view_sha256='')
    return provisional.model_copy(update={'view_sha256':digest(provisional.model_dump(mode='json',exclude={'view_sha256'}))})


def build_owned_provider_native_view(*, ticker, market, periods, native_indicators, cutoff):
    """Project already-owned indicator artifacts onto the existing completed view.

    The stock acquisition owner validates each separate artifact against its
    original bar receipt. This projection selects values; it never calculates
    indicators or fabricates an HTTP capture. Derived partial W/M bars cannot
    borrow indicators from a provider's different period row.
    """
    from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows

    if not isinstance(native_indicators, Mapping) or set(native_indicators) - set(MAX_COUNTS):
        raise ValueError('native_indicator_timeframe_mapping_invalid')
    output = {}
    schemas = set()
    for timeframe, maximum in MAX_COUNTS.items():
        rows = deepcopy(list(periods.get(timeframe, ())))
        artifact = native_indicators.get(timeframe)
        # Inspect before finality filtering: an invalid historical row may have
        # influenced the provider's EMA even when finality excludes that row.
        # Date cutoff is handled by selection below, so a normal later/partial
        # row alone does not invalidate the earlier provider calculation.
        inspection = inspect_normalized_ohlcv_rows(rows, timeframe=timeframe)
        completed = [row for row in rows
            if assess_completed_bar_finality(row, cutoff=cutoff).state == 'FINAL']
        selected = completed[-maximum:]
        last_date = str(selected[-1]['date'])[:10] if selected else None
        reasons = []
        structural = {'INVALID_BAR_DATE', 'DUPLICATE_TIMESTAMP', 'DUPLICATE_CONFLICT', 'BAR_TIMESTAMP_ORDERING'}
        valid_source = not any(issue.bar_date is None or issue.violation.value in structural
            or last_date is None or issue.bar_date <= last_date for issue in inspection.issues)
        if not valid_source:
            reasons.append('NATIVE_INDICATOR_SOURCE_ROWS_INVALID')
        if artifact is not None:
            if (not isinstance(artifact, Mapping)
                    or artifact.get('contract') != 'provider-native-stock-indicators-v1'
                    or artifact.get('provider') != 'ohlcv_analyst'
                    or not isinstance(artifact.get('indicator_schema'), str)
                    or not artifact['indicator_schema']
                    or artifact.get('status') not in {'AVAILABLE', 'UNAVAILABLE'}):
                raise ValueError('native_indicator_artifact_contract_invalid')
            if artifact['status'] == 'AVAILABLE':
                schemas.add(artifact['indicator_schema'])
            projected_rows = artifact.get('rows') or []
            by_date = {row['date']: row['indicators'] for row in projected_rows}
            if len(by_date) != len(projected_rows):
                raise ValueError('native_indicator_duplicate_date')
        else:
            by_date = {}
            reasons.append('NATIVE_INDICATOR_ARTIFACT_UNAVAILABLE')
        supplied = by_date.get(last_date)
        available = bool(valid_source and selected and artifact
            and artifact['status'] == 'AVAILABLE' and isinstance(supplied, Mapping))
        if artifact and artifact['status'] == 'UNAVAILABLE':
            reasons.append(str(artifact.get('reason') or 'NATIVE_INDICATORS_UNAVAILABLE'))
        elif selected and supplied is None:
            reasons.append('NATIVE_COMPLETED_ROW_INDICATORS_UNAVAILABLE')
        if not selected:
            reasons.append('COMPLETED_NATIVE_ROWS_UNAVAILABLE')
        values = {field: deepcopy(supplied.get(field)) if available else None for field in INDICATORS}
        quality = {field: ('PROVIDER_NATIVE' if _valid_number(value)
            else 'UNAVAILABLE_PROVIDER_NULL_OR_MISSING' if value is None else 'INVALID_PROVIDER_VALUE')
            for field, value in values.items()}
        # Original finite values remain usable on short history. The producer's
        # row count is descriptive, never a second minimum-history admission.
        enriched = tuple({**row, 'indicators': deepcopy(by_date.get(str(row['date'])[:10], {}))}
            for row in selected)
        source_hash = digest(dict(artifact=artifact, completed_analysis_rows=selected))
        output[timeframe] = NativePeriod(timeframe=timeframe,
            status='INVALID' if not valid_source else 'AVAILABLE' if available else 'UNAVAILABLE',
            returned_count=int(artifact.get('calculation_row_count', 0)) if artifact else 0,
            max_count=maximum, completed_count=len(selected), source_hash=source_hash,
            provider='ohlcv_analyst', completed_as_of=last_date,
            raw_bar_date=str(rows[-1]['date'])[:10] if rows else None,
            rows=enriched, indicators=values, indicator_quality=quality,
            quarantined_count=len(rows) - len(completed), reasons=tuple(dict.fromkeys(reasons)))
    if len(schemas) > 1:
        raise ValueError('native_indicator_mixed_schema')
    value = ProviderNativeTechnicalView(provider_code=ticker, market=market,
        cutoff=cutoff.isoformat(), periods=output,
        indicator_schema=next(iter(schemas), FORMULA_VERSION),
        source_hash=digest({tf: period.source_hash for tf, period in output.items()}),
        view_sha256='', allowed_use='MONITORING_TECHNICAL')
    return value.model_copy(update={'view_sha256': digest(value.model_dump(mode='json', exclude={'view_sha256'}))})
