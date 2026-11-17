"""Data-only chart reference adapter. No price/financial Owner is issued."""
from datetime import date, datetime
import hashlib
import json
import math

from app.services.provider_native_technical import build_provider_native_view
from app.services.unified_snapshot_contract import digest

CONTRACT = 'dated-ohlcv-reference-price-v1'


def _derive(*, proof, ticker, market):
    from app.services.market_session import market_session_for_ticker
    from app.services.ohlcv_client import OhlcvClient
    if (not isinstance(proof, dict) or set(proof) != {'response_body', 'observed_at', 'analysis_cutoff'}
            or any(not isinstance(proof[k], str) for k in proof)
            or len(proof['response_body'].encode('utf-8')) > 16 * 1024**2
            or market not in {'kr', 'us'} or market != ('kr' if ticker.isdigit() else 'us')):
        raise ValueError('dated_reference_source_or_market_invalid')
    observed = datetime.fromisoformat(proof['observed_at'])
    cutoff = date.fromisoformat(proof['analysis_cutoff'])
    if observed.utcoffset() is None:
        raise ValueError('dated_reference_observation_timezone_required')
    session = market_session_for_ticker(ticker, observed)
    if cutoff > session.latest_completed_regular_session_date:
        raise ValueError('dated_reference_after_completed_session')
    raw = proof['response_body'].encode('utf-8')
    payload = json.loads(raw)
    rows, supply, provider = OhlcvClient._decode_period_payload(payload,ticker=ticker,
        period='daily',adjusted=True,response_body_sha256=hashlib.sha256(raw).hexdigest())
    _, rows = OhlcvClient._complete_period_response(count=1000,period='daily',bars=rows,supply_demand=supply)
    if provider != 'kiwoom':
        raise ValueError('dated_reference_original_provider_required')
    from app.services.dated_bar_admission import admit_rows
    rows, _ = admit_rows(rows,ticker=ticker,market=market,timeframe='daily',cutoff=cutoff)
    native = build_provider_native_view(ticker=ticker,market=market,periods={'daily': rows},
        cutoff=cutoff,observed_at=observed,historical_reference=True)
    period = native.periods['daily']
    if period.status != 'AVAILABLE' or not period.rows:
        raise ValueError('dated_reference_no_eligible_daily_row')
    row = period.rows[-1]
    capture = row['_native_capture']
    reference = dict(contract=CONTRACT,ticker=ticker,market=market,
        currency='KRW' if market == 'kr' else 'USD',value=row['close'],timeframe='daily',
        reference_date=row['date'],analysis_cutoff=cutoff.isoformat(),observed_at=observed.isoformat(),
        adjustment_basis='adjusted_close',role='DATED_TECHNICAL_REFERENCE',provider='ohlcv_analyst',
        source_response_sha256=capture['response_body_sha256'],native_period_sha256=digest(period.model_dump(mode='json')),
        row_fingerprint=capture['normalized_bar_sha256'],
        finality_or_historical_eligibility='HISTORICAL_CHART_OBSERVATION_NOT_OFFICIAL_CLOSE',
        allowed_use=['ONBOARDING_TECHNICAL','PRICE_LOCATION'])
    return reference, native


def build_reference(*, native, response_body, observed_at):
    proof = dict(response_body=response_body.decode('utf-8'),observed_at=observed_at.isoformat(),
        analysis_cutoff=native.cutoff)
    reference, replay = _derive(proof=proof,ticker=native.provider_code,market=native.market)
    if native.periods['daily'] != replay.periods['daily']:
        raise ValueError('dated_reference_native_period_replay_mismatch')
    return reference, proof


def validate_reference(reference, proof, *, ticker, market, as_of=None):
    if not isinstance(reference, dict):
        raise ValueError('dated_reference_missing')
    if reference.get('ticker') != ticker or reference.get('market') != market:
        raise ValueError('dated_reference_source_replay_mismatch')
    expected, _ = _derive(proof=proof,ticker=ticker,market=market)
    if reference != expected:
        raise ValueError('dated_reference_source_replay_mismatch')
    if (type(reference['value']) not in (int, float) or not math.isfinite(reference['value'])
            or reference['value'] <= 0):
        raise ValueError('dated_reference_nonpositive_or_nonfinite')
    if as_of is not None:
        current = datetime.fromisoformat(as_of) if isinstance(as_of, str) else as_of
        if current.utcoffset() is None or datetime.fromisoformat(reference['observed_at']) > current:
            raise ValueError('dated_reference_future_observation')
    return reference


def validate_price_reference(price, *, ticker, market):
    reference = price.dated_reference_price
    if reference is None:
        return None
    return validate_reference(reference,price.dated_reference_evidence,
        ticker=ticker,market=market)


def technical_context_from_references(evidence, *, ticker, market, period_sources=None):
    """Replay retained HTTP bodies as dated native technical context, not price rights."""
    from app.services.ohlcv_client import OhlcvClient
    from app.services.packet_owned_technical_context_service import build_native_packet_context
    if not isinstance(evidence, dict) or not evidence.get('as_of'):
        raise ValueError('onboarding_native_evidence_as_of_required')
    reference = validate_reference(evidence.get('dated_reference_price'),
        evidence.get('dated_reference_evidence'), ticker=ticker, market=market,
        as_of=evidence['as_of'])
    proof = evidence['dated_reference_evidence']
    sources = dict(period_sources or {})
    if set(sources) - {'weekly', 'monthly'}:
        raise ValueError('onboarding_native_period_scope_invalid')
    sources['daily'] = dict(response_body=proof['response_body'],
        response_sha256=reference['source_response_sha256'], observed_at=proof['observed_at'])
    periods = {}
    observations = []
    for period, source in sources.items():
        if not isinstance(source, dict) or set(source) != {'response_body', 'response_sha256', 'observed_at'}:
            raise ValueError('onboarding_native_original_response_required')
        raw = source['response_body'].encode('utf-8')
        observed = datetime.fromisoformat(source['observed_at'])
        if (len(raw) > 16*1024**2 or hashlib.sha256(raw).hexdigest() != source['response_sha256']
                or observed.utcoffset() is None or observed > datetime.fromisoformat(evidence['as_of'])):
            raise ValueError('onboarding_native_response_binding_invalid')
        payload = json.loads(raw)
        rows, supply, provider = OhlcvClient._decode_period_payload(payload, ticker=ticker,
            period=period, adjusted=True, response_body_sha256=source['response_sha256'])
        _, rows = OhlcvClient._complete_period_response(
            count={'daily': 1000, 'weekly': 700, 'monthly': 300}[period],
            period=period, bars=rows, supply_demand=supply)
        if provider != 'kiwoom':
            raise ValueError('dated_reference_original_provider_required')
        from app.services.dated_bar_admission import admit_rows
        rows, _ = admit_rows(rows,ticker=ticker,market=market,timeframe=period,
            cutoff=date.fromisoformat(reference['analysis_cutoff']))
        periods[period] = rows
        observations.append(observed)
    view = build_provider_native_view(ticker=ticker, market=market, periods=periods,
        cutoff=date.fromisoformat(reference['analysis_cutoff']),
        observed_at=max(observations), historical_reference=True)
    return build_native_packet_context(view=view, session=reference['reference_date'], as_of=evidence['as_of'])
