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
    accounting = acquisition.get('document_slot_accounting')
    if accounting is not None and (len(accounting)!=len(candidates)
            or any(s['state'] not in {'EXECUTED','VALID_NOT_SELECTED'} for r in accounting for s in r['slots'])):
        unresolved.append('FROZEN_DOCUMENT_SLOTS_INCOMPLETE')
    for doc in documents:
        if doc.get('document_graph_conflict'):
            unresolved.append('CONFLICTING_FINANCIAL_ATTACHMENTS')
        if doc['purpose']=='OFFICIAL_AUXILIARY_ASSET' and doc.get('auxiliary_verified'):
            continue
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


def field_completeness(selection, documents, complete):
    """Absence is per metric and never inferred from a sibling's success."""
    rows = {}
    for metric in ('revenue', 'operating_income'):
        owned = selection['fields'][metric]
        observed = [o for d in documents for o in d['occurrences'] if o['field']==metric]
        valid = [o for d in documents for o in d['occurrences']
                 if o['field']==metric and o['occurrence_id'] in d['valid_occurrence_ids']]
        invalid = [o for o in observed if o not in valid]
        parser = [r for d in documents for r in d.get('inline_owner',{}).get('denials',[])
                  if r.get('field')==metric and r['reason']!='INLINE_DIMENSIONED_CONTEXT']
        if owned['status']=='PASS':
            state='QUALIFIED_CURRENT_PRIOR_PAIR'
        elif not complete['bounded_plan_complete']:
            state='ACQUISITION_INCOMPLETE' if any(r in complete['reasons'] for r in (
                'FROZEN_SOURCE_PLAN_INCOMPLETE','FROZEN_CANDIDATE_NOT_CAPTURED')) else 'PURPOSE_OR_FIELD_UNRESOLVED'
        elif invalid or parser:
            state='PURPOSE_OR_FIELD_UNRESOLVED'
        elif not observed:
            state='SOURCE_COMPLETE_NO_QUALIFIED_FIELD'
        else:
            state='PURPOSE_OR_FIELD_UNRESOLVED'
        rows[metric]=dict(state=state, selection=owned, valid_occurrence_refs=[o['occurrence_id'] for o in valid],
            unresolved_occurrence_refs=[o['occurrence_id'] for o in invalid], parser_denials=parser,
            source_completeness_sha256=complete['receipt_sha256'])
    states={r['state'] for r in rows.values()}
    value=dict(contract='fpi-metric-independent-completeness-v1', fields=rows,
        partial_field_consumption_allowed=(bool(states & {'QUALIFIED_CURRENT_PRIOR_PAIR'})
            and states <= {'QUALIFIED_CURRENT_PRIOR_PAIR','SOURCE_COMPLETE_NO_QUALIFIED_FIELD'}
            and (len(states)==1 or complete['bounded_plan_complete'])),
        document_source_sha256=digest(documents))
    value['receipt_sha256']=digest(value)
    return value
