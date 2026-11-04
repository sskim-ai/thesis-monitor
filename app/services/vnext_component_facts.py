"""Pure original reported-component checks; no Settings, stores or ownership."""
from decimal import Decimal, InvalidOperation
from app.services.kr_financial_lineage_service import opendart_field_lineage

COMPONENTS = ('ifrs-full_InsuranceServiceResult', 'dart_InvestmentIncomeExpenses',
              'ifrs-full_OtherOperatingIncomeExpense')
TOTAL = 'ifrs-full_ProfitLossFromOperatingActivities'


def select_account_family(body, *, provider, statement_basis):
    """Discover a supported accounting schema, never an issuer classification."""
    descriptor = dict(contract='reported-component-account-schema-v1',
                      family='insurance_investment_other_operating',
                      accounts=list(COMPONENTS), total=TOTAL,
                      required_period='single_quarter', authority='NONE_UNTIL_ORIGINAL_REPLAY')
    if provider != 'opendart' or statement_basis != 'consolidated':
        return dict(status='DENIED', reason='UNSUPPORTED_PROVIDER_OR_BASIS')
    counts = {a: sum(r.get('account_id') == a and r.get('sj_div') in ('IS','CIS')
                     for r in body.get('list', [])) for a in (*COMPONENTS, TOTAL)}
    if not any(counts[a] for a in COMPONENTS):
        return dict(status='NOT_APPLICABLE', reason='ACCOUNT_SCHEMA_NOT_PRESENT')
    if any(n != 1 for n in counts.values()):
        return dict(status='DENIED', reason='ACCOUNT_SCHEMA_MISSING_OR_AMBIGUOUS')
    return dict(status='CANDIDATE_REQUIRES_REPLAY', descriptor=descriptor)


def verified_account_facts(body, *, plan, request, fields, raw_sha):
    f = fields
    if body.get('status') != '000':
        raise ValueError('component_source_status_denied')
    rows = body.get('list', [])
    facts = []
    for account in (*COMPONENTS, TOTAL):
        selected = [r for r in rows if r.get('account_id') == account and r.get('sj_div') in ('IS','CIS')]
        if len(selected) != 1:
            raise ValueError('component_account_missing_or_ambiguous')
        row = selected[0]
        if (str(row.get('corp_code')) != str(plan['issuer']) or row.get('rcept_no') != f['source_receipt']
                or row.get('reprt_code') != request['params']['reprt_code']):
            raise ValueError('component_source_identity_mismatch')
        for role, column in (('current','thstrm_amount'),('comparison','frmtrm_q_amount')):
            lineage = opendart_field_lineage(row, logical_field='reported_operating_component',
                report_code=request['params']['reprt_code'], source_column=column,
                selected=True, requested_fs_div='CFS')
            period = (f['period_start'],f['period_end']) if role == 'current' else (f['prior_period_start'],f['prior_period_end'])
            if (not lineage['lineage_verified'] or lineage['statement_basis'] != f['statement_basis']
                    or lineage['amount_period_type'] != 'single_quarter' or lineage['currency'] != f['currency']
                    or (lineage['amount_period_start'],lineage['amount_period_end']) != period):
                raise ValueError('component_period_basis_currency_denied')
            try:
                exact = Decimal(str(row[column]).replace(',',''))
                if not exact.is_finite() or exact != exact.to_integral_value() or exact != Decimal(str(lineage['amount'])):
                    raise ValueError('component_exact_amount_denied')
            except (InvalidOperation,KeyError) as exc:
                raise ValueError('component_exact_amount_denied') from exc
            facts.append(dict(account_id=account, account_name=row['account_nm'], role=role,
                value=int(exact),currency=f['currency'],unit='KRW',unit_scale=1,period_start=period[0],period_end=period[1],
                statement_basis=f['statement_basis'],occurrence=lineage['source_row_identity'],
                source_sha=raw_sha,source_filing=f['source_receipt'],lineage=lineage))
    for role,key in (('current','current_value'),('comparison','prior_comparable_value')):
        group=[x for x in facts if x['role']==role]; total=next(x['value'] for x in group if x['account_id']==TOTAL)
        if total != f[key] or sum(x['value'] for x in group if x['account_id']!=TOTAL) != total:
            raise ValueError('component_operating_reconciliation_denied')
    return facts
