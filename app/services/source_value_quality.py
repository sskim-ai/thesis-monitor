"""Narrow typed value denial; never turns malformed custody into soft failure."""
import json
from typing import Literal

from app.services.unified_snapshot_contract import ContractModel
from app.services.unified_run_artifacts import sha256_bytes
from app.services.kiwoom_completed_close_owner import validate_completed_daily_row, _wire_price
from app.services.ohlcv_provider_integrity_service import inspect_normalized_ohlcv_rows


class StrictCloseUnavailable(ContractModel):
    contract: Literal['strict-close-source-quality-denial-v1'] = 'strict-close-source-quality-denial-v1'
    status: Literal['STRICT_COMPLETED_CLOSE_UNAVAILABLE_SOURCE_QUALITY'] = 'STRICT_COMPLETED_CLOSE_UNAVAILABLE_SOURCE_QUALITY'
    strict_close_eligible: Literal[False] = False
    source_sha256: str
    logical_request_id: str
    target_session: str
    observed_at: str
    violations: tuple[str, ...]
    native_use: Literal[False] = False
    valuation_use: Literal[False] = False


def strict_close_quality(raw, *, target, logical_request_id, observed_at):
    try:
        validate_completed_daily_row(raw, target)
        return None
    except ValueError as exc:
        if str(exc) != 'completed_close_own_ohlc_integrity_failed':
            raise
    payload = json.loads(raw)
    selected = [r for r in payload['result_list'] if r['dt'] == target.strftime('%Y%m%d')]
    if len(selected) != 1:
        raise ValueError('strict_close_quality_target_identity_lost')
    source = selected[0]
    row = dict(date=str(target), **{k:_wire_price(source[f]) for k,f in
        (('open','open_pric'),('high','high_pric'),('low','low_pric'),('close','cur_prc'))})
    quality = inspect_normalized_ohlcv_rows([row],timeframe='daily',cutoff=target)
    allowed={'HIGH_LT_OPEN','HIGH_LT_CLOSE','LOW_GT_OPEN','LOW_GT_CLOSE','LOW_GT_HIGH'}
    codes=tuple(sorted({i.violation.value for i in quality.issues}))
    if quality.valid or not codes or not set(codes)<=allowed:
        raise ValueError('strict_close_quality_unrecognized_integrity_failure')
    return StrictCloseUnavailable(source_sha256=sha256_bytes(raw),logical_request_id=logical_request_id,
        target_session=str(target),observed_at=observed_at,violations=codes)
