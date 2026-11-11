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
    allowed_use: Literal['DATED_TECHNICAL_ANALYSIS'] = 'DATED_TECHNICAL_ANALYSIS'

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
        for period in result['periods'].values():period.pop('rows')
        result['formula_semantics']=FORMULAS
        result['stored_price_rules_owner']='SEPARATE_NOT_MODIFIED'
        return result


def _valid_number(value):
    try:return type(value) in (int,float) and math.isfinite(value)
    except OverflowError:return False


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
