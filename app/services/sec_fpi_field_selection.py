"""Field-local FPI authority for the opt-in bounded reported-interim route."""
from datetime import date

from app.services.sec_business_field_quality_service import FIELDS
from app.services.sec_foreign_comparison_service import foreign_comparison_quality, occurrences
from app.services.sec_fpi_financial_purpose import FINANCIAL

POLICY = 'EXACT_REPORTED_QUARTER_OR_HALF_YEAR_NO_SUBTRACTION'


def select_fields(documents, rows, *, ticker, cutoff, uncaptured=(), allow_inline_annual=False):
    selected, audit = [], {}
    qualities = {i: foreign_comparison_quality(formal=r, candidates=rows, ticker=ticker,
        cutoff=date.fromisoformat(cutoff[:10]), allow_reported_half_year=True,
        allow_inline_annual=allow_inline_annual) for i, r in enumerate(rows)}
    for metric in FIELDS:
        candidates = [(i, r) for i, r in enumerate(rows) if getattr(r, metric) is not None]
        reasons = []
        if not candidates:
            audit[metric] = {'status': 'BLOCKED', 'denial_reasons': ['NO_EXACT_FIELD_OBSERVATION']}
            continue
        end = max(r.financial_period_end for _, r in candidates)
        latest = [(i, r) for i, r in candidates if r.financial_period_end == end]
        # Prefer an explicitly reported quarter at the same endpoint, never subtract H1.
        role = next((p for p in ('single-quarter', 'half-year', 'annual') if any(r.period_scope == p for _, r in latest)), None)
        latest = [(i, r) for i, r in latest if r.period_scope == role]
        eligible = [(i, r) for i, r in latest if qualities[i]['fields'][metric]['status'] == 'PASS']
        if not eligible:
            reasons.append('LATEST_FIELD_COMPARISON_NOT_QUALIFIED')
        # A reviewed statement outranks an unreviewed release for the same tuple.
        # Ambiguous peers remain blocked even if they happen to contain equal values.
        def rank(pair):
            i, _ = pair
            comparison = next(c for c in qualities[i]['comparative_observations'] if c['metric'] == metric)
            cls = comparison['current']['lineage']['occurrence'].get('document_evidence_class', {})
            return int(cls.get('evidence_class') == 'AUDITOR_REVIEWED_INTERIM_STATEMENT')
        if eligible:
            best = max(map(rank, eligible))
            eligible = [p for p in eligible if rank(p) == best]
        if len(eligible) > 1:
            reasons.append('AMBIGUOUS_CURRENT_FIELD_AUTHORITY')
        chosen = eligible[0][1] if len(eligible) == 1 else None
        selected_date = chosen.filing_date.isoformat() if chosen else max(r.filing_date.isoformat() for _, r in latest)
        relevant_unknowns = []
        financial_accessions = {d['accession'] for d in documents if d['financial_authority']}
        for doc in documents:
            if any(c['field'] == metric for c in doc.get('source_precedence_conflicts', [])) and doc['filing_date'] >= selected_date:
                reasons.append('INLINE_TABLE_CONFLICT')
            if (doc['accession'] in financial_accessions
                    and not (allow_inline_annual and doc.get('unresolved_financial_content'))):
                continue
            if (doc['purpose'] == 'UNKNOWN_PURPOSE' or doc['purpose'] in FINANCIAL) and doc['filing_date'] >= selected_date:
                relevant_unknowns.append(doc['document_identity'])
        relevant_unknowns.extend(f['accessionNumber'] for f in uncaptured if f['filingDate'] >= selected_date)
        if relevant_unknowns:
            reasons.append('NEWER_DOCUMENT_PURPOSE_UNRESOLVED')
        # Known later field periods cannot silently disappear through a parser/quality failure.
        later = [o['occurrence_id'] for d in documents for o in d['occurrences']
                 if o.get('field') == metric and o.get('period_end') and o['period_end'] > end.isoformat()]
        if later:
            reasons.append('LATEST_FIELD_PERIOD_UNAVAILABLE_NO_OLDER_SUBSTITUTION')
        if chosen:
            selected_occurrences = [o for o in occurrences(chosen) if o['field'] == metric
                and o['period_end'] == end.isoformat() and o['period_scope'] == role]
            tuple_keys = ('provider', 'issuer_cik', 'semantic', 'statement_basis', 'currency', 'unit_scale', 'period_start', 'period_end')
            tuples = {tuple(o.get(k) for k in tuple_keys) for o in selected_occurrences}
            peers = [o for _, r in latest for o in occurrences(r) if o['field'] == metric
                and o['period_end'] == end.isoformat() and o['period_scope'] == role]
            if any(tuple(o.get(k) for k in tuple_keys) not in tuples for o in peers):
                reasons.append('CURRENT_FIELD_AUTHORITY_BASIS_MISMATCH')
        record = {'status': 'BLOCKED' if reasons else 'PASS', 'period_end': end.isoformat(),
            'period_scope': role, 'source_accession': chosen.source_filing_id if chosen else None,
            'source_url': chosen.source if chosen else None, 'unresolved_sources': relevant_unknowns,
            'later_unavailable_occurrence_ids': later, 'denial_reasons': sorted(set(reasons)),
            'selection': 'latest_economic_field_period_then_reviewed_statement_authority_not_value_or_filing_date'}
        if not reasons:
            comparison = next(c for c in qualities[eligible[0][0]]['comparative_observations'] if c['metric'] == metric)
            record['prior_source_accession'] = comparison['comparison']['lineage']['receipt']
            isolated = chosen.model_copy(deep=True)
            for other in FIELDS:
                if other != metric:
                    setattr(isolated, other, None)
            selected.append(isolated)
            record['selected_metric'] = metric
        audit[metric] = record
    return selected, {'contract': 'sec-fpi-field-economic-supersession-v1', 'fields': audit,
        'status': 'PASS' if selected else 'BLOCKED',
        'period_end': max((r.financial_period_end.isoformat() for r in selected), default=None),
        'source_accessions': sorted({r.source_filing_id for r in selected}),
        'denial_reasons': sorted({reason for row in audit.values() for reason in row['denial_reasons']})}


def reconcile_historical_denials(reconciliation, documents, selection):
    """Keep old acquisition defects, scope only proven unrelated filings out of use."""
    result = dict(reconciliation)
    scope = []
    fields = [f for f in selection['fields'].values() if f['status'] == 'PASS']
    if not fields:
        return result
    selected_ids = {f['source_accession'] for f in fields}
    selected_dates = [d['filing_date'] for d in documents if d['accession'] in selected_ids]
    for row in reconciliation['diagnostics']:
        filing = row['filing']
        owned = [d for d in documents if d['accession'] == filing['accessionNumber']]
        explicitly_nonfinancial = bool(owned) and all(d['purpose'] not in FINANCIAL | {'UNKNOWN_PURPOSE'} for d in owned)
        historical = bool(selected_dates) and filing['filingDate'] < min(selected_dates)
        same_document_priors = all(f['prior_source_accession'] == f['source_accession'] for f in fields)
        excluded = explicitly_nonfinancial or (historical and same_document_priors and filing['accessionNumber'] not in selected_ids)
        scope.append({'accession': filing['accessionNumber'], 'historical': historical,
            'explicitly_nonfinancial': explicitly_nonfinancial, 'outside_selected_field_authority': excluded})
    removable = {'SEC_DOCUMENT_BOUND_EXHAUSTED', 'SEC_LINKED_EXHIBIT_NOT_CAPTURED'}
    if scope and all(r['outside_selected_field_authority'] for r in scope):
        result['effective_denials'] = [r for r in reconciliation['effective_denials'] if r not in removable]
    result['field_relevance_audit'] = scope
    result['historical_denials_preserved'] = reconciliation['effective_denials']
    return result
