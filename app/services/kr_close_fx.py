from dataclasses import dataclass, field
from datetime import date, datetime, timezone
import json
import math
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, StrictFloat

from app.models.macro import MacroBriefing


FX_LABELS = {
    "USDKRW_KR_CLOSE": "원/달러",
    "JPYKRW100_KR_CLOSE": "원/100엔",
    "EURKRW_KR_CLOSE": "원/유로",
}


@dataclass(frozen=True)
class KrCloseFxItem:
    series_code: str
    label: str
    value: float
    change_value: float | None = None
    change_pct: float | None = None
    observation_date: str | None = None
    comparison_date: str | None = None
    observed_at: str | None = None


@dataclass(frozen=True)
class KrCloseFxSummary:
    items: list[KrCloseFxItem] = field(default_factory=list)
    missing_labels: list[str] = field(default_factory=list)
    stale_as_of: str | None = None


def _json(value: str, fallback: object) -> object:
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return fallback


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


class KrCloseFxObservation(BaseModel):
    """Fields already emitted by the close collector; never opens a store."""
    model_config = ConfigDict(extra='forbid', frozen=True, allow_inf_nan=False)
    provider: str
    series_code: str
    market_session: str
    unit: str
    value: StrictFloat
    observed_at: datetime
    retrieved_at: datetime
    provider_last_refreshed: str
    provider_timezone: str
    from_currency: str
    to_currency: str
    raw_rate: StrictFloat
    scale: StrictFloat

    @classmethod
    def from_retained_row(cls, row):
        payload = json.loads(row.raw_payload)
        fields = ('provider_last_refreshed','provider_timezone','from_currency','to_currency','raw_rate','scale')
        return cls(**{key:payload[key] for key in fields},provider=row.provider,series_code=row.series_code,
            market_session=row.market_session,unit=row.unit,value=row.value,
            observed_at=row.observed_at if row.observed_at.tzinfo else row.observed_at.replace(tzinfo=timezone.utc),
            retrieved_at=row.retrieved_at if row.retrieved_at.tzinfo else row.retrieved_at.replace(tzinfo=timezone.utc))


def retained_fx_display(observations, *, completed, cutoff, source_policy):
    """Compare approved like-for-like dated rows, not same-day re-polls."""
    from app.macro.providers.alpha_vantage_fx import PAIRS, _provider_timestamp
    from app.services.unified_source_policy import UnifiedSourcePolicy
    from app.services.unified_snapshot_contract import digest

    if not isinstance(source_policy, UnifiedSourcePolicy) or cutoff.tzinfo is None:
        raise ValueError('retained_fx_requires_explicit_source_policy_and_cutoff')
    specs = {series:(currency,scale,unit) for currency,series,scale,unit in PAIRS}
    kst = ZoneInfo('Asia/Seoul')
    completed = date.fromisoformat(completed)
    groups = {}
    for row in observations:
        if not source_policy.permits(row.provider) or row.series_code not in specs:
            continue
        currency,scale,unit = specs[row.series_code]
        if (row.market_session != 'kr_close' or (row.from_currency,row.to_currency,row.scale,row.unit) != (currency,'KRW',scale,unit)
                or row.observed_at.tzinfo is None or row.retrieved_at.tzinfo is None
                or _provider_timestamp(row.provider_last_refreshed,row.provider_timezone) != row.observed_at
                or not row.observed_at <= row.retrieved_at <= cutoff
                or row.retrieved_at.astimezone(kst).date() > completed
                or row.value < 0 or row.raw_rate < 0 or not math.isclose(row.raw_rate*scale,row.value,rel_tol=1e-12,abs_tol=1e-9)):
            continue
        key = (row.provider,row.series_code,row.observed_at,row.retrieved_at)
        groups.setdefault(key,[]).append(row)
    rows = [items[0] for items in groups.values() if len(items)==1]
    result = {}
    for series,label in FX_LABELS.items():
        current = max((row for row in rows if row.series_code == series and row.value > 0),
            key=lambda r:(r.observed_at,r.retrieved_at,r.provider),default=None)
        if current is None:
            continue
        day = current.observed_at.astimezone(kst).date()
        previous = max((row for row in rows if row.series_code==series and row.provider==current.provider
                and row.observed_at.astimezone(kst).date()<day and row.retrieved_at.astimezone(kst).date()<day),
            key=lambda r:(r.observed_at,r.retrieved_at),default=None)
        change = current.value-previous.value if day==completed and previous is not None and previous.value>0 else None
        pct = change/previous.value*100 if change is not None else None
        if pct is not None and not math.isfinite(pct):
            change = pct = None
        item = KrCloseFxItem(series,label,current.value,change,pct,day.isoformat(),
            previous.observed_at.astimezone(kst).date().isoformat() if change is not None else None,
            current.observed_at.isoformat())
        proof = dict(provider=current.provider,session='kr_close',unit=current.unit,scale=current.scale,
            observation_date=item.observation_date,observed_at=item.observed_at,retrieved_at=current.retrieved_at.isoformat(),
            current_sha256=digest(current.model_dump(mode='json')),comparison_date=item.comparison_date,
            comparison_sha256=digest(previous.model_dump(mode='json')) if change is not None else None,
            stale=day!=completed,observation_only=True,directional_authority_added=False)
        result[series] = item,proof
    return result


def format_dated_fx(item):
    text = f'{item.label}: {item.value:,.2f}원 ({item.observation_date} 관측)'
    if item.change_value is None or item.change_pct is None:
        return text+' · 비교 자료 미확보'
    return text+f' · {item.change_value:+,.2f}원 ({item.change_pct:+.2f}%, {item.comparison_date} 대비)'


class RetainedEcosFxCapture(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    body: str
    publication: dict
    source_hashes: tuple[str, ...]


def _ecos_fx_rows(body, publication, source_hashes):
    from app.services.latest_published_fx import validate_context
    from app.services.unified_run_artifacts import sha256_bytes
    from app.services.unified_snapshot_contract import digest

    raw = body.encode()
    pin = sha256_bytes(raw)
    day = publication['observation_date']
    if (len(raw)>512*1024 or pin!=publication['response_sha256'] or not validate_context(publication,
            observation_date=day,response_hashes=set(source_hashes),query_as_of=publication['query_as_of'])):
        raise ValueError('retained_ecos_fx_original_response_mismatch')
    rows = json.loads(raw)['KeyStatisticList']['row']
    specs = {
        'USDKRW_KR_CLOSE': ('원/달러 환율(종가)','KRW per USD','ECOS_PUBLISHED_CLOSE'),
        'JPYKRW100_KR_CLOSE': ('원/엔(100엔) 환율(매매기준율)','KRW per 100 JPY','ECOS_REFERENCE_RATE'),
        'EURKRW_KR_CLOSE': ('원/유로 환율(매매기준율)','KRW per EUR','ECOS_REFERENCE_RATE'),
    }
    query_day = datetime.fromisoformat(publication['query_as_of']).date()
    result = {}
    for series,(title,unit,basis) in specs.items():
        for row in rows:
            if (row.get('CLASS_NAME'),row.get('KEYSTAT_NAME'),row.get('UNIT_NAME'))!=('환율',title,'원'):
                continue
            try:
                observed = datetime.strptime(row['CYCLE'],'%Y%m%d').date()
                value = _number(float(row['DATA_VALUE']))
            except (KeyError, ValueError, TypeError, OverflowError):
                continue
            if row['CYCLE']!=observed.strftime('%Y%m%d') or observed>query_day:
                continue
            row_day = observed.isoformat()
            result.setdefault(series,{}).setdefault(row_day,[]).append((value,dict(
                provider='ecos',unit=unit,series_basis=basis,observation_date=row_day,
                retrieved_at=publication['retrieved_at'],query_as_of=publication['query_as_of'],
                observed_at=None,comparison_date=None,raw_response_sha256=pin,raw_row_sha256=digest(row),
                observation_only=True,directional_authority_added=False)))
    return result


def retained_ecos_fx_display(body, *, publication, source_hashes, anchor_value, source_policy, prior_captures=()):
    """Use each ECOS row's own date; compare only pinned, like-for-like rows."""
    source_policy.require('ecos')
    current = _ecos_fx_rows(body, publication, source_hashes)
    day = publication['observation_date']
    result = {}
    prior = []
    for capture in prior_captures:
        if not isinstance(capture,RetainedEcosFxCapture):
            raise ValueError('retained_ecos_fx_prior_capture_required')
        try:
            rows = _ecos_fx_rows(capture.body,capture.publication,capture.source_hashes)
            if datetime.fromisoformat(capture.publication['retrieved_at']) <= datetime.fromisoformat(publication['query_as_of']):
                prior.append(rows)
        except (KeyError, TypeError, ValueError):
            continue
    for series, by_day in current.items():
        row_day = day if series=='USDKRW_KR_CLOSE' else max(by_day)
        rows = by_day.get(row_day,())
        if len(rows)!=1 or rows[0][0] is None or rows[0][0]<=0:
            continue
        value,proof = rows[0]
        comparable = {}
        for observations in (current,*prior):
            for earlier, candidates in observations.get(series,{}).items():
                if earlier < row_day:
                    for old_value, old_proof in candidates:
                        comparable.setdefault(earlier,{}).setdefault(old_proof['raw_row_sha256'],(old_value,old_proof))
        change = pct = previous_day = None
        if comparable:
            latest = max(comparable)
            candidates = comparable[latest]
            if len(candidates)==1:
                old_value,old_proof = next(iter(candidates.values()))
                identity = ('provider','series_basis','unit')
                if old_value is not None and old_value>0 and all(proof[k]==old_proof[k] for k in identity):
                    delta = value-old_value
                    relative = delta/old_value*100
                    if math.isfinite(relative):
                        change,pct,previous_day = delta,relative,latest
                        proof = dict(proof,comparison_date=latest,
                            comparison_response_sha256=old_proof['raw_response_sha256'],
                            comparison_row_sha256=old_proof['raw_row_sha256'],
                            comparison_retrieved_at=old_proof['retrieved_at'])
        result[series] = KrCloseFxItem(series,FX_LABELS[series],value,change,pct,row_day,previous_day),proof
    if 'USDKRW_KR_CLOSE' not in result or result['USDKRW_KR_CLOSE'][0].value!=anchor_value:
        raise ValueError('retained_ecos_fx_usd_anchor_mismatch')
    return result


def summarize_kr_close_fx(briefing: MacroBriefing | None) -> KrCloseFxSummary:
    if briefing is None:
        return KrCloseFxSummary()
    market = _json(briefing.market_summary, {})
    quality = _json(briefing.data_quality, [])
    fx = market.get("fx", []) if isinstance(market, dict) else []
    items: list[KrCloseFxItem] = []
    stale_dates: list[str] = []
    for item in fx if isinstance(fx, list) else []:
        if not isinstance(item, dict):
            continue
        series_code = str(item.get("series_code") or "")
        label = FX_LABELS.get(series_code)
        value = _number(item.get("value"))
        if label is None or value is None:
            continue
        items.append(
            KrCloseFxItem(
                series_code=series_code,
                label=label,
                value=value,
                change_value=_number(item.get("change_value")),
                change_pct=_number(item.get("change_pct")),
            )
        )
        if item.get("quality_status") == "stale" and item.get("as_of"):
            stale_dates.append(str(item["as_of"])[:10])
    quality_items = quality if isinstance(quality, list) else []
    unavailable = [
        str(item.get("warning", ""))
        for item in quality_items
        if isinstance(item, dict) and str(item.get("warning", "")).endswith(":unavailable")
    ]
    missing_labels = [
        label
        for series_code, label in FX_LABELS.items()
        if any(warning.startswith(series_code) for warning in unavailable)
    ]
    return KrCloseFxSummary(
        items=items,
        missing_labels=missing_labels,
        stale_as_of=max(stale_dates) if stale_dates else None,
    )


def render_kr_close_fx(summary: KrCloseFxSummary) -> str:
    if not summary.items:
        return "⚠️ 환율 자료를 이번 조회에서 확인하지 못했습니다."
    lines = ["💱 환율"]
    for item in summary.items:
        line = f"• {item.label} {item.value:,.1f}원"
        if item.change_value is not None and item.change_pct is not None:
            line += f" · {item.change_value:+,.1f}원 ({item.change_pct:+.2f}%)"
        lines.append(line)
    if summary.missing_labels:
        lines.append(
            f"⚠️ {', '.join(summary.missing_labels)} 환율은 이번 조회에서 확인하지 못했습니다."
        )
    if summary.stale_as_of:
        lines.append(f"⚠️ 환율 최신 관측은 {summary.stale_as_of} 기준입니다.")
    return "\n".join(lines)
