"""Field-local FPI authority for the opt-in bounded reported-interim route."""
from datetime import date

from app.services.sec_business_field_quality_service import FIELDS
from app.services.sec_foreign_comparison_service import foreign_comparison_quality, occurrences
from app.services.sec_fpi_financial_purpose import FINANCIAL

POLICY = 'EXACT_REPORTED_QUARTER_OR_HALF_YEAR_NO_SUBTRACTION'


def select_fields(documents, rows, *, ticker, cutoff, uncaptured=(), allow_inline_annual=False, purpose_reconciliation=None, current_purpose_intake=None, source_documents=None, documentary_review=None):
    documentary = None
    if documentary_review is not None:
        from app.services.sec_documentary_field_review import DocumentaryReviewRegistry
        registry, handle = documentary_review
        if type(registry) is not DocumentaryReviewRegistry:
            raise ValueError('documentary_original_registry_required')
        documentary = registry.resolve(handle, documents=documents, rows=rows, ticker=ticker, cutoff=cutoff)
    review = None
    if purpose_reconciliation is not None and current_purpose_intake is not None:
        raise ValueError('purpose_diagnostic_and_current_routes_exclusive')
    if purpose_reconciliation is not None:
        from app.services.sec_fpi_purpose_reconciliation import resolve
        review = resolve(purpose_reconciliation)
    if current_purpose_intake is not None:
        from app.services.current_financial_purpose_intake import resolve
        review = resolve(current_purpose_intake)
        if review['parent']['cutoff'] != cutoff:
            raise ValueError('current_purpose_field_cutoff_mismatch')
    selected, audit = [], {}
    qualities = {i: foreign_comparison_quality(formal=r, candidates=rows, ticker=ticker,
        cutoff=date.fromisoformat(cutoff[:10]), allow_reported_half_year=True,
        allow_inline_annual=allow_inline_annual, source_documents=source_documents) for i, r in enumerate(rows)}
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
            if (allow_inline_annual and doc['filing_date'] >= selected_date
                    and any(p['end'] > end.isoformat() for p in doc['economic_periods'])
                    and any(r.get('field') == metric and r['reason'] != 'INLINE_DIMENSIONED_CONTEXT'
                            for r in doc.get('inline_owner', {}).get('denials', []))):
                reasons.append('LATEST_FIELD_EXACT_OWNER_UNRESOLVED')
            if allow_inline_annual and doc.get('document_graph_conflict'):
                reasons.append('CONFLICTING_FINANCIAL_ATTACHMENTS')
            if any(c['field'] == metric for c in doc.get('source_precedence_conflicts', [])) and doc['filing_date'] >= selected_date:
                reasons.append('INLINE_TABLE_CONFLICT')
            if (doc['accession'] in financial_accessions and (
                    not allow_inline_annual or doc['financial_authority']
                    or (doc.get('filing_form', '').split('/')[0] in {'20-F','40-F'}
                        and not doc.get('unresolved_financial_content'))
                    or doc['purpose'] in {'FORWARDING_COVER', 'OFFICIAL_AUXILIARY_ASSET'})):
                continue
            if (doc['purpose'] == 'UNKNOWN_PURPOSE' or doc['purpose'] in FINANCIAL) and doc['filing_date'] >= selected_date:
                relevant_unknowns.append(doc['document_identity'])
        auxiliary_scope = []
        for filing in uncaptured:
            if review is not None:
                from app.services.sec_fpi_purpose_reconciliation import matching_nonfinancial
                cleared = matching_nonfinancial(review, filing)
                auxiliary_scope.append(dict(accession=filing['accessionNumber'], filing_date=filing['filingDate'],
                    selected_filing_date=selected_date, newer_or_same=filing['filingDate'] >= selected_date,
                    verified_nonfinancial=cleared, original_uncaptured_record_preserved=True))
            else:
                cleared = False
            if filing['filingDate'] >= selected_date and not cleared:
                relevant_unknowns.append(filing['accessionNumber'])
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
        if review is not None and current_purpose_intake is None:
            record['auxiliary_purpose_reconciliation'] = dict(receipt_sha256=review['receipt_sha256'],
                original_uncaptured_scope=auxiliary_scope, current_owner_eligible=False,
                limitation=review['temporal_authority'])
        elif review is not None:
            record['current_purpose_applicability'] = dict(receipt_sha256=review['receipt_sha256'],
                original_uncaptured_scope=auxiliary_scope, scope=review['scope'],
                financial_authority=False, source_history_exhausted=False)
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
    result = {'contract': 'sec-fpi-field-economic-supersession-v1', 'fields': audit,
        'status': 'PASS' if selected else 'BLOCKED',
        'period_end': max((r.financial_period_end.isoformat() for r in selected), default=None),
        'source_accessions': sorted({r.source_filing_id for r in selected}),
        'denial_reasons': sorted({reason for row in audit.values() for reason in row['denial_reasons']})}
    if documentary is not None:
        # Diagnostics are visible without removing any purpose/quality denial.
        result['documentary_review'] = documentary
    return selected, result


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
