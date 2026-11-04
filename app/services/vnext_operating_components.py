"""Research-only accounting components from original capture and period owners."""
import copy
import json
import uuid
from app.services.vnext_earnings_composition import verify as verify_composition
from app.services.bounded_financial_projection import _raw
from app.services.vnext_research_store import digest

CONTRACT = 'vnext-reported-operating-components-v1'
from app.services.vnext_component_facts import COMPONENTS, TOTAL, verified_account_facts


def attachment(packet, *, original_context):
    base, _ = verify_composition(packet, original_context=original_context)
    ctx = original_context
    plan = ctx['plan']
    if plan['provider'] != 'opendart':
        raise ValueError('component_provider_not_supported')
    op = next(e for e in base['evidence'] if e['field'] == 'financial.operating_income')
    f = op['data']['fields']
    if f['statement_basis'] != 'consolidated':
        raise ValueError('component_consolidated_required')
    bind = next(x for x in packet['earnings_composition']['bindings'] if x['metric'] == 'operating_income')
    rs = [r for r in ctx['receipts'] if r.get('raw_sha256') == bind['raw_sha256'] and not r.get('failure_class')]
    if len(rs) != 1:
        raise ValueError('component_receipt_not_unique')
    receipt = rs[0]
    request = json.loads((ctx['directory'] / (receipt['logical_id'].split(':')[-1]+'.plan.json')).read_bytes())
    # Original capture replay already binds this frozen request to its receipt.
    if (request.get('params') or {}).get('fs_div') != 'CFS':
        raise ValueError('component_request_scope_unproven')
    body = json.loads(_raw(ctx['directory'], receipt['artifact'], ctx['receipts']))
    facts = verified_account_facts(body, plan=plan, request=request, fields=f, raw_sha=bind['raw_sha256'])
    return dict(contract=CONTRACT,base_packet_sha=digest(packet),security=copy.deepcopy(plan['security']),
        source_generation=plan['run_id'],source_cutoff=plan['cutoff'],source_receipt_sha=digest(receipt),
        projection_sha=digest(ctx['expected_projection']),supporting_refs=[op['ref']],facts=facts,
        independent_lineages=1,consumer='VNEXT_ECONOMIC_RESEARCH_EXPLANATION',use='RESEARCH_ONLY',
        provenance='SOURCE_BOUND_EXISTING_RAW',recurrence_verified=False,investment_direction_grant=False,
        valuation_denominator_grant=False,strict_native=False,
        limits=['Accounting contribution is not economic causation or future persistence.',
                'No independent corroboration is added. Insurance revenue margin remains denied.'])


def catalog(att):
    result=[]
    for i,f in enumerate(att['facts']):
        if f['account_id']==TOTAL:continue
        n=dict(fact_id=att['supporting_refs'][0],field_path='/operating_components/facts/'+str(i),
            value=f['value'],unit='KRW',basis='SOURCE_BOUND_EXISTING_RAW_RESEARCH_ONLY',
            as_of=f['period_start']+'/'+f['period_end'],source_sha=f['source_sha'],
            supporting_refs=att['supporting_refs'],occurrences=[f['occurrence']],account_id=f['account_id'])
        n['catalog_id']='c'+digest(n)[:16];result.append(n)
    return result


def enrich(packet, *, original_context):
    result=copy.deepcopy(packet); att=attachment(packet,original_context=original_context)
    result['operating_components']=att;result['numeric_catalog']+=catalog(att)
    return result


def replay(packet, *, original_context):
    base=copy.deepcopy(packet);att=base.pop('operating_components');extra=catalog(att)
    if base['numeric_catalog'][-len(extra):]!=extra:raise ValueError('component_numeric_drift')
    base['numeric_catalog']=base['numeric_catalog'][:-len(extra)]
    if attachment(base,original_context=original_context)!=att:raise ValueError('component_original_replay_mismatch')
    return base,extra


class ResearchComponentOwner:
    """Live parent capability; public receipt JSON cannot restore issuance."""
    def __init__(self):
        self.registry_id=uuid.uuid4().hex
        self._issued={}

    def issue(self, base, *, original_context, invocation):
        if not isinstance(invocation,str) or not invocation:raise ValueError('component_invocation_required')
        packet=enrich(base,original_context=original_context)
        receipt=dict(id=uuid.uuid4().hex,registry=self.registry_id,invocation=invocation,
            packet_sha=digest(packet),contract=CONTRACT,consumer='VNEXT_ECONOMIC_RESEARCH_EXPLANATION',
            use='RESEARCH_ONLY')
        self._issued[receipt['id']]=copy.deepcopy(receipt)
        return packet,receipt

    def consume(self, packet, receipt, *, invocation, consumer='VNEXT_ECONOMIC_RESEARCH_EXPLANATION', use='RESEARCH_ONLY'):
        if (self._issued.get(receipt.get('id'))!=receipt or receipt.get('registry')!=self.registry_id
                or receipt.get('invocation')!=invocation or receipt.get('packet_sha')!=digest(packet)
                or receipt.get('consumer')!=consumer or receipt.get('use')!=use):
            raise ValueError('component_owner_use_denied')
        return copy.deepcopy(receipt)

    def revoke(self, receipt):
        self._issued.pop(receipt.get('id'),None)
