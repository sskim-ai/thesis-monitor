"""Adapter boundaries only; actual dated Owner evidence is a separate replay."""
import json
from pathlib import Path

import pytest

from app.services import retained_scoped_technical_reference as adapter


def args(tmp_path):
    return dict(security={'ticker': 'EXAMPLE'}, receipt_paths=[],
        parser_root=tmp_path, parser_pins=tmp_path/'pins.json', enabled=True)


@pytest.mark.parametrize('enabled,paths', [(False, []), (True, []), (False, ['unused'])])
def test_default_and_empty_fail_closed(tmp_path, enabled, paths):
    with pytest.raises(ValueError, match='disabled_or_empty'):
        adapter.build_owner(**dict(args(tmp_path), enabled=enabled, receipt_paths=paths))


@pytest.mark.parametrize('ticker,adjusted,timeframe,role', [
    ('OTHER', True, 'daily', 'adjusted_daily'),
    ('EXAMPLE', False, 'weekly', 'unadjusted_weekly_valuation'),
    ('EXAMPLE', False, 'daily', 'adjusted_daily'),
    ('EXAMPLE', True, 'annual', 'adjusted_annual'),
    ('EXAMPLE', True, 'daily', 'adjusted_monthly'),
    ('EXAMPLE', True, 'weekly', 'adjusted_daily'),
    ('EXAMPLE', True, 'monthly', 'unadjusted_monthly'),
    ('EXAMPLE', True, '', 'adjusted_'),
])
def test_role_security_and_basis_are_not_coerced(tmp_path, ticker, adjusted, timeframe, role):
    p=tmp_path/'receipt.json'
    p.write_text(json.dumps({'entry':dict(subject=ticker,adjusted=adjusted,timeframe=timeframe,role=role)}))
    with pytest.raises(ValueError, match='subject_or_adjustment'):
        adapter.build_owner(**dict(args(tmp_path),receipt_paths=[p]))


@pytest.mark.parametrize('kind', ['file', 'parent', 'dangling'])
def test_symlinks_rejected(tmp_path, kind):
    original=tmp_path/'original';original.mkdir()
    receipt=original/'receipt.json';receipt.write_text('{}')
    link=tmp_path/'link'
    link.symlink_to(receipt if kind=='file' else original if kind=='parent' else tmp_path/'absent')
    p=link/'receipt.json' if kind=='parent' else link
    with pytest.raises(ValueError, match='symlink'):
        adapter.build_owner(**dict(args(tmp_path),receipt_paths=[p]))


@pytest.mark.parametrize('text', ['not json', '[]', '{}', '{"entry":{}}'])
def test_malformed_receipt_not_treated_as_denial_permission(tmp_path, text):
    p=tmp_path/'receipt.json';p.write_text(text)
    with pytest.raises((ValueError,KeyError,TypeError)):
        adapter.build_owner(**dict(args(tmp_path),receipt_paths=[p]))


def test_parser_pin_mismatch_rejected_before_original_owner(tmp_path):
    root=tmp_path/'capture';stocks=root/'worker/stocks';stocks.mkdir(parents=True)
    p=stocks/'role-001.receipt.json'
    p.write_text(json.dumps({'entry':dict(subject='EXAMPLE',adjusted=True,timeframe='daily',role='adjusted_daily')}))
    (root/'frozen.json').write_text(json.dumps({'external_pins':{'parser':'a'*64}}))
    pins=tmp_path/'pins.json';pins.write_text(json.dumps({'parser':'b'*64}))
    with pytest.raises(ValueError, match='parser_pin_drift'):
        adapter.build_owner(**dict(args(tmp_path),receipt_paths=[p],parser_pins=pins))


def test_no_ticker_dispatch_or_network_in_adapter():
    text=Path(adapter.__file__).read_text()
    assert all(token not in text for token in ('SKHY','000660','CPNG','httpx','requests.','sqlite3','Settings'))
