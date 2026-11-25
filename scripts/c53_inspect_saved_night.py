"""Explain saved KRX night rows without collecting, replaying, or accepting data.

The optional broker reference is a user observation used only for comparison.
It never replaces a provider row or changes a provider/session date.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
import json
import math
from pathlib import Path

from app.jobs import probe_krx_night_futures as krx
from app.services.market_session import preceding_exchange_session_date
from app.services.night_futures_session_mapping_service import resolve_us_morning_night_reference_date
from scripts.c52_inspect_saved_night import failure, read_capture


RAW_FIELDS = ('BAS_DD', 'PROD_NM', 'MKT_NM', 'ISU_CD', 'ISU_NM',
    'TDD_OPNPRC', 'TDD_HGPRC', 'TDD_LWPRC', 'TDD_CLSPRC', 'SETL_PRC',
    'CMPPREVDD_PRC', 'ACC_TRDVOL')
BAR_FIELDS = dict(open='TDD_OPNPRC', high='TDD_HGPRC', low='TDD_LWPRC',
                  close='TDD_CLSPRC', volume='ACC_TRDVOL')


def _maturity(value):
    value = str(value).replace('-', '')
    if len(value) != 6 or not value.isdigit() or not 1 <= int(value[4:]) <= 12:
        raise ValueError('night_diagnostic_maturity_invalid')
    return value[:4] + '-' + value[4:]


def _matches(left, right):
    return left is not None and right is not None and math.isclose(left, right, rel_tol=0, abs_tol=1e-8)


def _target_hint(raw, maturity):
    # Include recognizable target rows even if the production parser rejects a
    # malformed product/session/price; unrelated instruments stay out of the report.
    names = ''.join(str(raw.get(k, '')) for k in ('PROD_NM', 'ISU_NM')).replace(' ', '').upper()
    if '미니' in names or 'MINI' in names or ' SP ' in f" {str(raw.get('ISU_NM', ''))} ":
        return False
    return ('KOSPI200' in names or '코스피200' in names) and krx._maturity(str(raw.get('ISU_NM', ''))) == maturity


def _parser_reasons(raw):
    checks = {
        'INVALID_BAS_DD': krx._business_date(raw.get('BAS_DD')) is None,
        'PRODUCT_NOT_SELECTED': krx._target_product(raw.get('PROD_NM'), raw.get('ISU_NM')) not in krx.TARGET_PRODUCTS,
        'SESSION_UNRECOGNIZED': krx._session(raw.get('MKT_NM')) is None,
        'CONTRACT_IDENTITY_MISSING': not str(raw.get('ISU_CD') or '').strip() or not str(raw.get('ISU_NM') or '').strip(),
        'CLOSE_NOT_NUMERIC': krx._number(raw.get('TDD_CLSPRC')) is None,
    }
    return [code for code, failed in checks.items() if failed]


def _comparisons(night, rows):
    parsed = night['parsed']
    day = preceding_exchange_session_date('XKRX', parsed.business_date)
    matches = [row for row in rows if row['parsed'] is not None
        and row['parsed'].product == parsed.product and row['parsed'].session == 'regular'
        and row['parsed'].business_date == day and row['parsed'].contract_code == parsed.contract_code
        and row['parsed'].maturity == parsed.maturity]
    result = dict(night_row_id=night['row_id'], preceding_day_date=str(day) if day else None,
                  same_contract_day_row_ids=[row['row_id'] for row in matches])
    if len(matches) != 1:
        result['comparison_status'] = 'DAY_MISSING' if not matches else 'DAY_AMBIGUOUS'
        return result
    reference = matches[0]
    close, settlement = reference['parsed'].close, krx._number(reference['raw'].get('SETL_PRC'))
    settlement = settlement if settlement is not None and settlement > 0 else None
    change = parsed.provider_change_point
    close_change = parsed.close - close
    settlement_change = parsed.close - settlement if settlement is not None else None
    result.update(comparison_status='SAME_CONTRACT_DAY_FOUND', day_close=close,
        day_settlement=settlement, provider_change_point=change,
        derived_change_from_day_close=round(close_change, 8),
        derived_change_from_day_settlement=round(settlement_change, 8) if settlement_change is not None else None,
        provider_matches_day_close=_matches(change, close_change) if change is not None else None,
        provider_matches_day_settlement=_matches(change, settlement_change) if change is not None else None,
        legacy_close_only_check_would_reject=change is not None and not _matches(change, close_change))
    return result


def _broker_comparison(reference, rows, maturity):
    if (reference.get('source_kind') != 'USER_BROKER_SCREENSHOT'
            or reference.get('product') != 'KOSPI200' or _maturity(reference.get('maturity')) != maturity):
        raise ValueError('night_diagnostic_broker_reference_invalid')
    date.fromisoformat(reference['chart_date'])
    expected = {key: krx._number(reference.get(key)) for key in BAR_FIELDS}
    if any(value is None or value < 0 for value in expected.values()) or expected['close'] <= 0:
        raise ValueError('night_diagnostic_broker_bar_invalid')
    matches = []
    for row in rows:
        parsed = row['parsed']
        if parsed is None or parsed.product != 'KOSPI200' or parsed.session != 'night':
            continue
        fields = {key: _matches(expected[key], krx._number(row['raw'].get(field)))
                  for key, field in BAR_FIELDS.items()}
        matches.append(dict(row_id=row['row_id'], provider_bas_dd=str(parsed.business_date),
            matching_fields=fields, close_matches=fields['close'], all_ohlcv_match=all(fields.values())))
    previous = krx._number(reference.get('previous_night_close'))
    header_change = krx._number(reference.get('header_change_point'))
    implied = expected['close'] - header_change if header_change is not None else None
    return dict(purpose='USER_REFERENCE_COMPARISON_ONLY_NOT_PROVIDER_EVIDENCE',
        broker=reference.get('broker'), broker_chart_date=reference['chart_date'], maturity=maturity,
        expected_ohlcv=expected, saved_night_comparisons=matches,
        prior_night_change_pct=round((expected['close'] / previous - 1) * 100, 8) if previous and previous > 0 else None,
        header_implied_reference_price=round(implied, 8) if implied is not None else None,
        header_reference_kind='UNCONFIRMED', provider_dates_modified=False)


def inspect(source_root, *, maturity, broker_reference=None):
    root = Path(source_root).absolute()
    report = dict(contract='saved-night-row-audit-v1', source_root=str(root), status='FAILED',
        purpose='SAVED_CAPTURE_DIAGNOSTIC_NOT_SOURCE_OR_MODEL_ACCEPTANCE', financial_http_calls=0,
        model_calls=0, production_db_calls=0, source_acceptances=0, source_files_modified=0)
    stage = 'read_saved_capture'
    try:
        maturity = _maturity(maturity)
        frozen, at, receipts, bodies, phase = read_capture(root)
        mapping = resolve_us_morning_night_reference_date(at)
        expected = mapping.expected_reference_date if mapping else None
        payloads, hashes, rows, queries = {}, {}, [], []
        for receipt in receipts:
            day = datetime.strptime(receipt['request']['params']['basDd'], '%Y%m%d').date()
            payload = json.loads(bodies[receipt['artifact']])
            payloads[day], hashes[day] = payload, receipt['artifact_sha256']
            raw_rows = krx._rows(payload)
            target = []
            for index, raw in enumerate(raw_rows):
                if not _target_hint(raw, maturity):
                    continue
                parsed = krx._parse_row(raw)
                row = dict(row_id=f'{day}:{index}', query_date=day, raw=raw, parsed=parsed)
                rows.append(row)
                target.append(dict(row_id=row['row_id'], raw={key: raw.get(key) for key in RAW_FIELDS},
                    parser_accepted=parsed is not None, parser_reasons=_parser_reasons(raw),
                    parsed_session=parsed.session if parsed else None))
            queries.append(dict(query_date=str(day), http_status=receipt['http_status'],
                requested_at=receipt['requested_at'], received_at=receipt['received_at'],
                raw_body_path=str(root / 'dispatch' / receipt['artifact']), body_sha256=receipt['artifact_sha256'],
                raw_row_count=len(raw_rows), target_rows=target))
        report.update(generation_id=frozen['generation_id'], observed_at=at.isoformat(),
            maturity=maturity, expected_reference_date=str(expected) if expected else None,
            expected_date_origin='CURRENT_CODE_USING_SAVED_FROZEN_AT',
            original_phase={k: phase.get(k) for k in ('status', 'error_class')}, queries=queries)
        stage = 'inspect_current_parser'
        parsed = krx.parse_krx_futures_payloads(payloads, fetched_at=at,
            queried_dates=list(payloads), payload_sha256_by_date=hashes)
        observations = [item.model_dump(mode='json') for item in parsed.observations]
        report['current_parser'] = dict(status=parsed.status, parser_status=parsed.parser_status,
            canonicalization_status=parsed.canonicalization_status,
            source_date=str(parsed.source_date) if parsed.source_date else None,
            warnings=parsed.warnings, observations=observations,
            product_statuses=[item.model_dump(mode='json') for item in krx._product_statuses(
                payloads, expected, parsed, finality_valid=mapping is not None and
                mapping.session_clock_finality == 'FINAL_BY_06_00_KST')])
        nights = [row for row in rows if row['parsed'] is not None and row['parsed'].product == 'KOSPI200'
                  and row['parsed'].session == 'night']
        report['same_contract_comparisons'] = [_comparisons(row, rows) for row in nights]
        current = [row for row in nights if row['parsed'].business_date == expected]
        raw_current = [row for row in rows if krx._session(row['raw'].get('MKT_NM')) == 'night'
            and (krx._business_date(row['raw'].get('BAS_DD')) == expected or row['query_date'] == expected)]
        selected = [item for item in observations if item['product'] == 'KOSPI200'
                    and item['maturity'] == maturity and item['session_date'] == str(expected)]
        diagnosis = ('EXPECTED_DATE_UNRESOLVED' if expected is None else
            'EXPECTED_TARGET_SELECTED' if selected else
            'EXPECTED_TARGET_PRESENT_PARSER_NOT_SELECTED' if current else
            'EXPECTED_QUERY_TARGET_ROWS_FILTERED_OR_DATE_MISMATCH' if raw_current else
            'EXPECTED_TARGET_NIGHT_ABSENT' if expected in payloads else 'EXPECTED_QUERY_NOT_CAPTURED')
        report['finding'] = dict(diagnosis=diagnosis,
            latest_saved_target_night_date=max((str(row['parsed'].business_date) for row in nights), default=None),
            stale_fallback_selected=bool(expected and parsed.source_date and parsed.source_date < expected),
            absence_scope='RECORDED_RESPONSES_ONLY_NOT_PROVIDER_WIDE_AVAILABILITY')
        if broker_reference is not None:
            stage = 'compare_user_broker_reference'
            report['broker_comparison'] = _broker_comparison(broker_reference, rows, maturity)
        report['status'] = 'SAVED_NIGHT_AUDIT_COMPLETE'
    except Exception as exc:
        report['failure'] = failure(stage, exc)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--maturity', required=True, help='Contract month, e.g. 202612')
    parser.add_argument('--broker-reference', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve().is_relative_to(args.source_root.resolve()):
        parser.error('--output must be outside the saved source generation')
    reference = json.loads(args.broker_reference.read_text()) if args.broker_reference else None
    report = inspect(args.source_root, maturity=args.maturity, broker_reference=reference)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=report['status'], finding=report.get('finding'), output=str(args.output))))
    return 0 if report['status'] == 'SAVED_NIGHT_AUDIT_COMPLETE' else 2


if __name__ == '__main__':
    raise SystemExit(main())
