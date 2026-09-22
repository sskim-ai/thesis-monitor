"""Bounded official month-history collection; selected contracts never change."""
from datetime import datetime

import httpx

from app.config import get_settings
from app.jobs.probe_krx_night_futures import KRX_FUTURES_DAILY_URL, USER_AGENT
from app.services.krx_night_history_service import (
    _session_dates, load_history, load_cached_response, persist_krx_response,
)


async def backfill_selected_month(root, selections, *, as_of: datetime, transport=None):
    if not selections or len({r.session_date for r in selections}) != 1:
        raise ValueError('same_reference_pair_required')
    reference = selections[0].session_date
    expected = _session_dates(reference.replace(day=1), reference)
    settings = get_settings()
    ledger = []
    async with httpx.AsyncClient(transport=transport, timeout=settings.macro_provider_timeout_seconds,
        headers={'AUTH_KEY': settings.krx_open_api_key or '', 'User-Agent': USER_AGENT}) as client:
        for day in expected:
            row = dict(query_date=day.isoformat(), requested=False, source='OFFICIAL_KRX_NIGHT')
            try:
                cached = load_cached_response(root, day)
                if cached and cached[0].fetched_at <= as_of:
                    receipt, body = cached
                    row['cache_hit'] = True
                    fetched = receipt.fetched_at
                else:
                    row['requested'] = True
                    response = await client.get(KRX_FUTURES_DAILY_URL, params={'basDd': day.strftime('%Y%m%d')})
                    response.raise_for_status()
                    body, fetched = response.content, as_of
                    row['cache_hit'] = False
                receipt, normalized, _ = persist_krx_response(root=root, query_date=day,
                    fetched_at=fetched, http_status=200, raw_body=body)
                row.update(raw_payload_sha256=receipt.raw_payload_sha256,
                    raw_relative_path=receipt.raw_relative_path, rejection_count=len(normalized.rejections),
                    selected_contracts_present=[s.contract_code for s in selections if any(
                        b.reference_date == day and b.contract_code == s.contract_code and b.bar_finality == 'FINAL'
                        for b in normalized.bars)])
            except (httpx.HTTPError, ValueError, OSError) as exc:
                row['error'] = type(exc).__name__
            ledger.append(row)
    coverage = []
    for selected in selections:
        bars = load_history(root, instrument_root=selected.product, contract_code=selected.contract_code,
                            start=reference.replace(day=1), end=reference)
        included = sorted({b.reference_date for b in bars if b.bar_finality == 'FINAL'})
        coverage.append(dict(product=selected.product, contract_code=selected.contract_code,
            reference_date=reference.isoformat(), expected_dates=[d.isoformat() for d in expected],
            included_dates=[d.isoformat() for d in included],
            missing_dates=[d.isoformat() for d in expected if d not in included]))
    return dict(authority='OFFICIAL_KRX_NIGHT', rows=ledger, coverage=coverage,
                request_count=sum(r['requested'] for r in ledger), retries=0,
                contract_mixing=False, kiwoom_substitution=False)
