"""One entry-candidate rule for B selection, B2 timing and presentation.

The input is an already bound B context. This module reads its evidence and
existing ENTRY permissions; it never changes source metadata or grants uses.
"""
from copy import deepcopy
import json

from app.services.entry_price_basis import frame_price_failures
from app.services.new_buyer_base_contract import number
from app.services.unified_snapshot_contract import digest


def _parse_statement(row):
    value = row.get('statement', {})
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {}, 'STATEMENT_INVALID_JSON'
    if not isinstance(value, dict):
        return {}, 'STATEMENT_NOT_OBJECT'
    return value, None


def statement(row):
    """Preserve the existing mapping-only reader without repairing source text."""
    return _parse_statement(row)[0]


def _index(rows):
    result = {row['ref_id']: row for row in rows}
    if len(result) != len(rows):
        raise ValueError('entry_duplicate_evidence_identity')
    return result


def _identity_failures(values, *, ticker, security_id, generation):
    failures = []
    for value in values:
        if 'ticker' in value and value['ticker'] != ticker:
            failures.append('TICKER_MISMATCH')
        for key in ('security_id', 'canonical_security_id'):
            if key in value and value[key] != security_id:
                failures.append('SECURITY_MISMATCH')
        for key in ('source_generation_id', 'source_generation'):
            if key in value and generation is not None and value[key] != generation:
                failures.append('SOURCE_GENERATION_MISMATCH')
    return failures


def assess_entry_candidates(context, *, ticker, security_id, source_generation_id=None):
    """Return copied candidates with exact checks and failure reasons.

    This also diagnoses saved B contexts. If a saved context lacks generation
    metadata, its absence stays visible; callers requesting a generation require
    the existing source binding to match. No historical acceptance is issued.
    """
    evidence = _index(context.get('decision_evidence', []))
    projection = context.get('source_use_projection', {})
    permissions = _index(projection.get('source_permissions', []))
    binding = context.get('source_evidence_binding', {})
    generation = source_generation_id or binding.get('source_generation_id')
    price = context.get('current_price') or {}
    price_ref = price.get('ref_id')
    price_row = evidence.get(price_ref, {})
    price_value, price_error = _parse_statement(price_row)
    daily_ref = 'canonical:chart:daily'
    daily = evidence.get(daily_ref, {})
    daily_value, daily_error = _parse_statement(daily)
    common = [prefix + error for prefix, error in (('PRICE_',price_error), ('DAILY_',daily_error))
              if error is not None]
    common.extend(_identity_failures((context, binding, projection, price, price_row, price_value,
                                     daily, daily_value),
        ticker=ticker, security_id=security_id, generation=generation))
    if source_generation_id is not None and binding.get('source_generation_id') != source_generation_id:
        common.append('SOURCE_GENERATION_MISMATCH')
    if not ticker or not security_id:
        common.append('SECURITY_IDENTITY_MISSING')
    if not price_ref or not price_row:
        common.append('PRICE_EVIDENCE_MISSING')
    checks = (
        ('PRICE_VALUE_MISMATCH', number(price_value.get('current_price')) is not None
            and number(price_value.get('current_price')) == number(price.get('value'))),
        ('PRICE_CURRENCY_MISMATCH', bool(price.get('currency'))
            and price_value.get('currency') == price['currency']),
        ('PRICE_BASIS_MISMATCH', bool(price.get('basis'))
            and price_value.get('price_basis') == price['basis']),
        ('PRICE_SESSION_MISMATCH', bool(price.get('as_of'))
            and price_row.get('as_of') == price['as_of']
            and price_value.get('price_as_of') == price['as_of']),
    )
    if price_error is None:
        common.extend(code for code, passed in checks if not passed)
    if daily_error is None:
        common.extend('DAILY_' + code for code in frame_price_failures(daily_value,
            timeframe='daily', frame_as_of=daily.get('as_of'), price=price, session=price.get('as_of')))
    for ref, name in ((price_ref, 'PRICE'), (daily_ref, 'DAILY')):
        if 'ENTRY' not in permissions.get(ref, {}).get('allowed_uses', []):
            common.append(name + '_ENTRY_DENIED')

    result = []
    candidates = context.get('r2_eligible_range_catalog', {}).get('tactical_candidates', [])
    for candidate in candidates:
        row, proofs = deepcopy(candidate), []
        failures = list(common)
        failures.extend(_identity_failures((row,), ticker=ticker, security_id=security_id,
                                           generation=generation))
        low, high = number(row.get('low')), number(row.get('high'))
        if low is None or high is None or not 0 < low <= high:
            failures.append('ZONE_VALUE_INVALID')
        if row.get('currency') != price.get('currency'):
            failures.append('ZONE_CURRENCY_MISMATCH')
        if 'as_of' in row and row['as_of'] != price.get('as_of'):
            failures.append('ZONE_SESSION_MISMATCH')
        if 'price_basis' in row and row['price_basis'] != price.get('basis'):
            failures.append('ZONE_PRICE_BASIS_MISMATCH')
        refs = row.get('evidence_refs') or []
        if not refs or len(refs) != len(set(refs)):
            failures.append('ZONE_EVIDENCE_MISSING_OR_DUPLICATE')
        candidate_failures = list(failures)
        for ref in refs:
            ev = evidence.get(ref, {})
            zone, zone_error = _parse_statement(ev)
            chart_ref = 'canonical:chart:' + str(zone.get('timeframe')) if zone_error is None else None
            chart = evidence.get(chart_ref, {})
            chart_value, chart_error = _parse_statement(chart)
            local = _identity_failures((ev, zone, chart, chart_value), ticker=ticker,
                security_id=security_id, generation=generation)
            label = ev.get('label')
            if label == 'chart_price_rules':
                local.append('STORED_PRICE_RULE_REFERENCE_ONLY')
            elif label == 'chart_price_structure_v3_zone':
                # Its current producer emits raw levels and source_refs but no
                # frame/basis link. Do not infer one from a label or price.
                local.append('V3_COMPLETED_FRAME_BASIS_MISSING')
            elif label != 'chart_support_zone':
                local.append('SUPPORT_EVIDENCE_MISSING_OR_UNSUPPORTED')
            else:
                if ev.get('as_of') != price.get('as_of'):
                    local.append('ZONE_SESSION_MISMATCH')
                if zone_error is not None:
                    local.append('ZONE_' + zone_error)
                else:
                    if (number(zone.get('zone_low')), number(zone.get('zone_high'))) != (low, high):
                        local.append('ZONE_BOUNDS_MISMATCH')
                    if zone.get('currency') != price.get('currency'):
                        local.append('ZONE_CURRENCY_MISMATCH')
                    if chart_error is not None:
                        local.append('SUPPORT_' + chart_error)
                    else:
                        local.extend('SUPPORT_' + code for code in frame_price_failures(chart_value,
                            timeframe=zone.get('timeframe'), frame_as_of=chart.get('as_of'),
                            price=price, session=price.get('as_of')))
                    if 'ENTRY' not in permissions.get(chart_ref, {}).get('allowed_uses', []):
                        local.append('SUPPORT_FRAME_ENTRY_DENIED')
            if 'ENTRY' not in permissions.get(ref, {}).get('allowed_uses', []):
                local.append('SUPPORT_ENTRY_DENIED')
            local = list(dict.fromkeys(local))
            proof_failures = list(dict.fromkeys(candidate_failures + local))
            proofs.append(dict(ref=ref, chart_ref=chart_ref, zone_sha256=digest(ev),
                chart_sha256=digest(chart), price_sha256=digest(price_row),
                passed=not proof_failures, failure_reasons=proof_failures))
            failures.extend(local)
        failures = list(dict.fromkeys(failures))
        passed = bool(proofs) and not failures
        # Attach derived evaluation fields only after the original source
        # values passed. Never overwrite an original candidate date or basis.
        row.setdefault('ticker', ticker)
        row.setdefault('security_id', security_id)
        if passed:
            row.setdefault('as_of', price['as_of'])
            row.setdefault('price_basis', price['basis'])
        row.update(eligible=passed, relation_basis_proven=passed,
                   basis_proofs=proofs, failure_reasons=failures)
        result.append(row)
    return result


def restrict_entry_candidates(context, entries, *, ticker, security_id, source_generation_id):
    """Narrow the model's B selection and preserve each exclusion for diagnosis."""
    result, selected = deepcopy(context), deepcopy(entries)
    result['r2_eligible_range_catalog'] = deepcopy(entries)
    eligible_ids = {row['candidate_id'] for row in entries.get('tactical_candidates', [])}
    # The earlier source-use/currency filter may already have removed a row.
    # Diagnose it too, while keeping that earlier exclusion authoritative.
    original = context.get('tactical_candidates', [])
    result['r2_eligible_range_catalog']['tactical_candidates'] += [deepcopy(row) for row in original
        if row['candidate_id'] not in eligible_ids]
    assessed = assess_entry_candidates(result, ticker=ticker, security_id=security_id,
                                       source_generation_id=source_generation_id)
    for row in assessed:
        if row['candidate_id'] not in eligible_ids:
            row.update(eligible=False, relation_basis_proven=False)
            row['failure_reasons'].append('SOURCE_USE_OR_CURRENCY_INELIGIBLE')
            for proof in row['basis_proofs']:
                proof['passed'] = False
                proof['failure_reasons'].append('SOURCE_USE_OR_CURRENCY_INELIGIBLE')
    selected['tactical_candidates'] = [row for row in assessed if row['eligible']]
    result['r2_eligible_range_catalog'] = deepcopy(selected)
    result['tactical_candidates'] = deepcopy(selected['tactical_candidates'])
    result['entry_candidate_diagnostics'] = [dict(candidate_id=row['candidate_id'],
        evidence_refs=row.get('evidence_refs', []), source_label=row.get('source_label'),
        eligible=row['eligible'], failure_reasons=row['failure_reasons'], basis_proofs=row['basis_proofs'])
        for row in assessed]
    if not selected['tactical_candidates']:
        result['tactical_unresolved_reason'] = 'NO_ELIGIBLE_COMPLETED_SUPPORT'
    return result, selected
