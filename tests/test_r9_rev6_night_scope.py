from copy import deepcopy
from datetime import date, datetime, timezone
from types import SimpleNamespace

from app.jobs.probe_krx_night_futures import parse_krx_futures_payloads
from app.services.night_futures_product_scope import PRODUCTS, SERIES, complete_series
from app.services.unified_snapshot_contract import digest
from test_krx_night_futures_probe import _row


def test_extra_wrong_product_cannot_change_selected_economic_semantics():
    at = datetime(2026, 8, 14, tzinfo=timezone.utc)
    payloads = {
        date(2026, 8, 13): {'OutBlock_1': [_row('KOSPI 200 선물', '정규', 'A0169000',
            '코스피200 F 202609', '100', '20260813')]},
        date(2026, 8, 14): {'OutBlock_1': [_row('KOSPI 200 선물', '야간', 'A0169000',
            '코스피200 F 202609 야간', '101', '20260814', '1')]},
    }
    original = parse_krx_futures_payloads(payloads, fetched_at=at)
    extra = deepcopy(payloads)
    extra[date(2026, 8, 14)]['OutBlock_1'].append(_row('KOSDAQ 150 선물', '야간', 'A0669000',
        '코스닥150 F 202609 야간', '999', '20260814'))
    after = parse_krx_futures_payloads(extra, fetched_at=at)
    assert PRODUCTS == ('KOSPI200',) and len(original.observations) == len(after.observations) == 1
    # Raw corpus hashes must differ; only selected economic semantics are invariant.
    exclude = {'night_source_payload_sha256', 'reference_source_payload_sha256'}
    assert digest(original.observations[0].model_dump(mode='json', exclude=exclude)) == digest(
        after.observations[0].model_dump(mode='json', exclude=exclude))
    assert original.observations[0].night_source_payload_sha256 != after.observations[0].night_source_payload_sha256
    assert complete_series([SimpleNamespace(series_code=SERIES[0])])
    assert not complete_series([])
    assert not complete_series([SimpleNamespace(series_code='KRX_KOSDAQ150_NIGHT_FUT')])
    wrong_only = {date(2026, 8, 14): {'OutBlock_1': extra[date(2026, 8, 14)]['OutBlock_1'][1:]}}
    assert not parse_krx_futures_payloads(wrong_only, fetched_at=at).observations
