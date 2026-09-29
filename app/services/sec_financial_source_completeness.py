"""Bounded official absence, distinct from an unimplemented financial owner."""
from app.services.unified_snapshot_contract import digest

UNAVAILABLE = 'FORMAL_FINANCIAL_SOURCE_COMPLETE_NO_QUALIFIED_FIELD'


def completeness(*, plan, acquisition, inventory, documents, uncaptured, acquisition_denials):
    candidates = inventory['current_financial_plan']['candidates']
    captured = {d['accession'] for d in documents}
    unresolved = []
    if uncaptured or acquisition_denials or not candidates:
        unresolved.append('FROZEN_SOURCE_PLAN_INCOMPLETE')
    if any(c['accessionNumber'] not in captured for c in candidates):
        unresolved.append('FROZEN_CANDIDATE_NOT_CAPTURED')
    for doc in documents:
        if doc['purpose'] == 'UNKNOWN_PURPOSE':
            unresolved.append('PURPOSE_UNRESOLVED')
        inline = doc.get('inline_owner', {})
        if inline.get('status') != 'RAN' or not doc.get('table_owner_ran'):
            unresolved.append('EXACT_PARSER_NOT_EXECUTED')
        if doc.get('source_precedence_conflicts'):
            unresolved.append('SOURCE_PRECEDENCE_CONFLICT')
        if any(r['reason'] != 'INLINE_DIMENSIONED_CONTEXT' for r in inline.get('denials', [])):
            unresolved.append('EXACT_PARSER_OR_LINEAGE_UNRESOLVED')
        if doc['occurrences'] and not doc['valid_occurrence_ids']:
            unresolved.append('TABLE_OR_INLINE_LINEAGE_UNRESOLVED')
        if doc['purpose'] in {'FINANCIAL_STATEMENTS', 'FINANCIAL_RESULTS_OR_EARNINGS'} and not doc['valid_occurrence_ids']:
            unresolved.append('FINANCIAL_DOCUMENT_WITHOUT_RESOLVED_FIELD_CONTEXT')
    # This is not a claim of searching every filing. Outside-bound financial
    # candidates prohibit an absence verdict; known fields use normal selection.
    if any(r['reason'] == 'OUTSIDE_FROZEN_TWO_CANDIDATE_BOUND'
           for r in inventory['current_financial_plan']['outside_bound']):
        unresolved.append('ADDITIONAL_FINANCIAL_CANDIDATES_OUTSIDE_BOUND')
    any_field = any(d['valid_occurrence_ids'] for d in documents)
    state = 'QUALIFIED_FIELDS_PRESENT' if any_field else UNAVAILABLE if not unresolved else 'SOURCE_OWNER_UNRESOLVED'
    value = dict(contract='bounded-fpi-source-completeness-v1', state=state,
        plan_sha256=digest(plan), acquisition_sha256=digest(acquisition), documents_sha256=digest(documents),
        candidate_plan_sha256=digest(inventory['current_financial_plan']), reasons=sorted(set(unresolved)),
        source_history_exhausted=False, bounded_plan_complete=not unresolved,
        financial_fact_count=sum(len(d['valid_occurrence_ids']) for d in documents), direction_eligible=False)
    value['receipt_sha256'] = digest(value)
    return value
