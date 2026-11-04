"""Explicit issuer-level SEC statement basis policy, not a financial-use grant."""
from datetime import date, datetime
import json
import re

from app.models.financial import FinancialSnapshot
from app.services.bounded_financial_acquisition import sec_document_identity
from app.services.sec_foreign_statement_scope import inspect_scopes
from app.services.sec_foreign_comparison_service import (
    current_projection, foreign_comparison_quality, StatementTables, grid,
    semantic, amount, period_from_headers,
)
from app.services.sec_foreign_statement_boundary_service import Document, boundary, text
from app.services.unified_snapshot_contract import digest

POLICY = 'SEC_FPI_LEGAL_ISSUER_CONSOLIDATED_REQUIRED_V1'
RULE = json.dumps(dict(policy=POLICY, version=1, subject='SEC_FPI_LEGAL_ISSUER_BUSINESS_FINANCIALS',
    selected_basis='consolidated', separate_fallback=False,
    authority='NG40_EXPLICIT_HUMAN_POLICY_APPROVAL',
    periods=['single-quarter','half-year'], fields=['revenue','operating_income'],
    require_original_occurrence_and_comparison_quality=True,
    automatic_current_financial_owner=False, automatic_native_use=False,
    per_share=False, valuation=False, investment_direction=False),sort_keys=True)


def unresolved_consolidated_cells(raw, resolved_cells=()):
    """Retain source cells dropped by the original boundary parser, never admit them."""
    html=raw.decode('utf-8',errors='replace')
    document=Document();document.feed(html)
    nodes={}
    def visit(node):
        nodes[node['path']]=node
        for child in node['children']:visit(child)
    visit(document.root)
    parser=StatementTables();parser.feed(html)
    rejected=[]
    for table in parser.tables:
        if table['nested']:continue
        owner=boundary(document.tables[table['index']])
        fragments=' '.join(text(nodes[p]) for p in owner['metadata_dom_paths'])
        mixed_caption=bool(re.search(r'\bconsolidated\b',fragments,re.I) and re.search(r'\bseparate\b',fragments,re.I))
        if not (owner['statement_basis']=='consolidated'
                or re.search(r'\bconsolidated\b',fragments,re.I)):
            continue
        headers=[]
        for ri,row in enumerate(grid(table)):
            labels=[c for c in row if c and semantic(c['text'])[0]]
            if not labels:
                if not any(amount(c['text']) is not None and not re.fullmatch(r'20\d{2}',c['text']) for c in row if c):
                    headers.append(row)
                continue
            if len({c['cell_index'] for c in labels})!=1:continue
            label=labels[0];field,_=semantic(label['text']);seen=set()
            for ci,cell in enumerate(row):
                if not cell or cell['cell_index'] in seen or ci<=label['column_index'] or amount(cell['text']) is None:continue
                seen.add(cell['cell_index'])
                owners=[h[ci] for h in headers if ci<len(h) and h[ci] and h[ci]['text']]
                texts=list(dict.fromkeys(c['text'] for c in owners))
                if any(re.fullmatch(r'notes?',t.strip(),re.I) or '%' in t or re.search(r'\b(yoy|qoq)\b',t,re.I) for t in texts):continue
                period=period_from_headers(texts)
                if (table['index'],ri,ci,cell['cell_index']) in resolved_cells:
                    continue
                if owner['status']=='PASS' and not mixed_caption and period['period_start'] and period['period_end']:
                    continue
                rejected.append(dict(field=field,statement_boundary=owner,source_cell=dict(table=table['index'],row=ri,
                    column=ci,cell=cell['cell_index'],value_text=cell['text'],headers=texts),
                    policy_denial='MIXED_SCOPE_CAPTION' if mixed_caption else 'ORIGINAL_BOUNDARY_UNRESOLVED'
                        if owner['status']!='PASS' else 'PERIOD_OWNERSHIP_UNRESOLVED',**period))
    return rejected


def select_basis(raw, *, plan, filing, source_url, policy, execution_generation, quarter_period_policy=None):
    rules=json.loads(RULE)
    if policy != POLICY or not isinstance(execution_generation,str) or not execution_generation:
        raise ValueError('sec_fpi_basis_explicit_policy_and_execution_required')
    security=plan['security']
    if (plan['provider']!='sec_edgar' or plan.get('financial_owner_policy')!='EXACT_FISCAL_ANNUAL_AND_CURRENT_FPI_V1'
            or filing['form'].split('/')[0] not in {'6-K','20-F'}
            or digest(security)!=plan['identity_sha256']
            or str(security.get('cik','')).zfill(10)!=str(plan['issuer']).zfill(10)
            or not all(security.get(k) for k in ('canonical_company_id','canonical_security_id'))):
        raise ValueError('sec_fpi_basis_issuer_identity_mismatch')
    sec_document_identity(source_url,plan,filing)
    audit=inspect_scopes(raw,issuer_cik=plan['issuer'],filing=filing,
        source_url=source_url,cutoff=plan['cutoff'],quarter_period_policy=quarter_period_policy)
    from app.services.sec_reported_quarter_period import source_record
    sources=source_record(raw,issuer_cik=plan['issuer'],accession=filing['accessionNumber'],
        document_type=filing['form'],filing_date=filing['filingDate'],source_url=source_url) if quarter_period_policy else None
    selected=next((p['occurrences'] for p in audit['partitions'] if p['statement_basis']=='consolidated'),[])
    valid_ids={r['occurrence_id'] for r in audit['occurrence_validation'] if not r['denial_reasons']}
    resolved_cells={tuple(o['source_cell'][k] for k in ('table','row','column','cell')) for o in selected
        if o.get('period_source_proof') and o['occurrence_id'] in valid_ids}
    unresolved=unresolved_consolidated_cells(raw,resolved_cells)
    field_decisions=[]; admitted=set()
    cutoff=date.fromisoformat(plan['cutoff'][:10])
    for role in rules['periods']:
        projection=current_projection(selected,required_role=role,source_documents=sources)
        quality=None
        if projection:
            end=date.fromisoformat(projection['period_end'])
            row=FinancialSnapshot(ticker=plan['ticker'],period=end.isoformat(),
                financial_period_end=end,financials_as_of=end,filing_date=date.fromisoformat(filing['filingDate']),
                source_filing_id=filing['accessionNumber'],source=source_url,provider='sec_foreign_filing',
                currency=projection['currency'],period_scope=role,unit_scale=1,
                created_at=datetime.fromisoformat(plan['cutoff']),
                raw_financial_fields=json.dumps([dict(field='foreign_business_occurrences',occurrences=selected)]),
                **{k:projection.get(k) for k in rules['fields']})
            if role=='half-year': row.is_cumulative=True; row.period_type=role
            quality=foreign_comparison_quality(formal=row,candidates=[row],ticker=plan['ticker'],
                cutoff=cutoff,allow_reported_half_year=True,allow_inline_annual=True,source_documents=sources)
        for field in rules['fields']:
            reasons=[]; comparisons=[]
            current_end=max((o['period_end'] or '' for o in selected+unresolved
                if o['field']==field and o['period_scope']==role),default=None)
            if not projection:
                reasons.append('CONSOLIDATED_EXACT_CURRENT_PROJECTION_UNAVAILABLE')
            else:
                comparisons=[c for c in quality['comparative_observations'] if c['metric']==field]
                reasons.extend(quality['fields'][field]['denial_reasons'])
                if current_end and current_end>projection['period_end']:
                    reasons.append('CONSOLIDATED_NEWER_CURRENT_UNRESOLVED')
                prior_ends={c['comparison']['lineage']['occurrence']['period_end'] for c in comparisons}
                if any(o['field']==field and o['period_scope'] in (role,None) and
                    (not o['period_end'] or o['period_end']>=projection['period_end'] or o['period_end'] in prior_ends)
                    for o in unresolved):
                    reasons.append('CONSOLIDATED_COMPETING_STATEMENT_BOUNDARY_UNRESOLVED')
                current=[o for o in selected if o['field']==field and o['period_scope']==role
                    and o['period_end']==projection['period_end']]
                keys=('value','semantic','period_start','period_end','currency','unit_scale','statement_basis')
                if (len({tuple(o.get(k) for k in keys) for o in current})!=1
                        or len({digest(o['statement_boundary']) for o in current})!=1):
                    reasons.append('CONSOLIDATED_CURRENT_AUTHORITY_AMBIGUOUS')
                for comp in comparisons:
                    prior=comp['comparison']['lineage']['occurrence']
                    peers=[o for o in selected if o['field']==field and o['period_scope']==role
                        and o['period_end']==prior['period_end']]
                    if (len({tuple(o.get(k) for k in keys) for o in peers})!=1
                            or len({digest(o['statement_boundary']) for o in peers})!=1):
                        reasons.append('CONSOLIDATED_PRIOR_AUTHORITY_AMBIGUOUS')
            if not comparisons:
                reasons.append('CONSOLIDATED_SAME_SCOPE_COMPARISON_REQUIRED')
            ids=sorted({c[side]['lineage']['occurrence']['occurrence_id']
                for c in comparisons for side in ('current','comparison')}) if not reasons else []
            field_decisions.append(dict(field=field,period_role=role,status='BLOCKED' if reasons else 'PASS',
                observed_current_period_end=current_end,
                selected_occurrence_ids=ids,denial_reasons=sorted(set(reasons)),
                original_comparison_quality_sha256=digest(quality) if quality else None,
                original_quality_field=quality['fields'][field] if quality else None))
    for decision in field_decisions:
        quarter=next(d for d in field_decisions if d['field']==decision['field'] and d['period_role']=='single-quarter')
        if (decision['period_role']=='half-year' and decision['status']=='PASS' and quarter['status']=='BLOCKED'
                and quarter['observed_current_period_end'] and quarter['observed_current_period_end']>=decision['observed_current_period_end']):
            decision.update(status='BLOCKED',selected_occurrence_ids=[],
                denial_reasons=decision['denial_reasons']+['UNRESOLVED_REPORTED_QUARTER_NO_HALF_YEAR_SUBSTITUTION'])
        admitted.update(decision['selected_occurrence_ids'])
    result=dict(contract='sec-fpi-reported-issuer-basis-owner-v1',policy=rules,policy_sha256=digest(rules),
        authority_scope='ACCOUNTING_BASIS_ONLY_NOT_FINANCIAL_OR_NATIVE_USE',
        security_identity=security,issuer_cik=str(plan['issuer']).zfill(10),
        source_generation=plan['run_id'],execution_generation=execution_generation,
        lineage='SAME_GENERATION' if plan['run_id']==execution_generation else 'HISTORICAL_REPLAY_NEW_POLICY_EVENT',
        cutoff=plan['cutoff'],source_url=source_url,filing=filing,plan_sha256=digest(plan),
        document_sha256=audit['document_sha256'],document_bytes=len(raw),
        original_scope_audit=audit,unresolved_consolidated_cells=unresolved,field_decisions=field_decisions,
        selected_occurrence_ids=sorted(admitted),
        selected_basis='consolidated' if admitted else None,status='PASS' if admitted else 'BLOCKED',
        rejected_alternate_scopes=[dict(statement_basis=p['statement_basis'],
            occurrence_ids=[o['occurrence_id'] for o in p['occurrences']],reason='NOT_AUTHORIZED_BY_CONSOLIDATED_REQUIRED_POLICY')
            for p in audit['partitions'] if p['statement_basis']!='consolidated'],
        source_use_eligible=False,direction_eligible=False,valuation_eligible=False,
        separate_fallback=False)
    return {**result,'receipt_sha256':digest(result)}


def selected_occurrences(receipt):
    """Internal projection helper; accepting callers must recompute via select_basis."""
    ids=set(receipt['selected_occurrence_ids'])
    return [o for p in receipt['original_scope_audit']['partitions'] for o in p['occurrences']
        if o['occurrence_id'] in ids]


def verify_basis(receipt,raw,**inputs):
    expected=select_basis(raw,**inputs)
    if receipt!=expected:
        raise ValueError('sec_fpi_basis_source_replay_mismatch')
    return expected
