"""Parent-issued research-only source selection, separate from Financial L3.

Trusted backend bootstrap supplies the policy-owner decision and accountable
semantic review callbacks. Neither is accepted from model/request JSON. This
capability is process-local; archived receipts document, but cannot reissue, it.
"""
from copy import deepcopy
from datetime import date
from decimal import Decimal
import math
import os
import secrets
import time
from weakref import WeakKeyDictionary

from app.services.sec_documentary_field_review import compare_field
from app.services.unified_snapshot_contract import digest

POLICY = 'field-local-exact-research-source-selection-v1'
USE = 'RESEARCH_EXACT_SOURCE_REFERENCE'
CONSUMER = 'vnext-composite-research'
RULE = dict(policy=POLICY, use=USE, consumer=CONSUMER,
    fields=['revenue','operating_income'], exact_basis='CFS',
    complete_inventory=True, semantic_review_required=True,
    unresolved_same_field_conflict='DENY_AFFECTED_FIELD',
    compatible_rounded_unknown_basis='CAVEAT_NOT_REPLACEMENT_OR_CORROBORATION',
    currentness='HISTORICAL_SOURCE_DATES_UNCHANGED',
    strict_financial_L3=False, native=False, direction=False,
    EPS_ADS_valuation=False, causal_recurrence=False)
POLICY_SHA256 = digest(RULE)


class ResearchReference:
    __slots__ = ('__weakref__',)


class ResearchSourceRegistry:
    def __init__(self, original_replay, authorized_review, *, clock=time.monotonic):
        if not callable(original_replay) or not callable(authorized_review):
            raise ValueError('trusted_replay_and_policy_review_required')
        self._replay,self._review,self._clock=original_replay,authorized_review,clock
        self._pid=os.getpid();self._id=secrets.token_hex(16);self._issued=WeakKeyDictionary()

    def _inputs(self):
        if os.getpid()!=self._pid:raise ValueError('research_parent_changed')
        original=deepcopy(self._replay());review=deepcopy(self._review())
        if (review.get('policy')!=POLICY or review.get('policy_sha256')!=POLICY_SHA256
            or review.get('use')!=USE or review.get('consumer')!=CONSUMER
            or not all(review.get(k) for k in ('owner_approval_sha256','reviewer_provenance','execution_generation','limitations'))
            or review.get('original_sha256')!=digest(original)):
            raise ValueError('research_policy_or_review_binding')
        inventory={i['id']:i for i in original['inventory']}
        if not inventory or len(inventory)!=len(original['inventory']):raise ValueError('research_inventory_duplicate')
        required=('raw_sha256','receipt_sha256','source_generation','issuer','accession','url')
        if any(not all(i.get(k) for k in required) for i in inventory.values()):raise ValueError('research_source_binding')
        if set(review['inventory_review'])!=set(inventory):raise ValueError('research_inventory_omitted')
        if sorted(review.get('source_generations',[]))!=sorted({i['source_generation'] for i in inventory.values()}):
            raise ValueError('research_generation_binding')
        for key,item in inventory.items():
            r=review['inventory_review'][key]
            if r.get('raw_sha256')!=item['raw_sha256'] or not r.get('evidence_sha256') or not r.get('scope_and_limitations'):
                raise ValueError('research_review_evidence_missing')
        cells=original['exact_cells'];ids=[c['occurrence_id'] for c in cells]
        if not cells or len(set(ids))!=len(ids) or set(review['field_review'])!=set(ids):
            raise ValueError('research_occurrence_review_domain')
        return original,review,inventory

    def issue(self, packet, *, ttl_seconds=3600):
        if type(ttl_seconds) not in (int,float) or not math.isfinite(ttl_seconds) or not 0<ttl_seconds<=86400:
            raise ValueError('research_lifetime_bound')
        original,review,inventory=self._inputs();identity=packet['public_security']
        if (packet.get('model')!='OFF' or any(packet.get(k) is not False for k in
            ('send','strict_ready','holdings_included','user_thesis_included'))
            or not identity.get('canonical_security_id') or packet['ticker']!=identity['ticker']):
            raise ValueError('research_public_request_scope')
        facts=[];denials=[]
        for cell in original['exact_cells']:
            source=inventory.get(cell.get('source_id'));fr=review['field_review'][cell['occurrence_id']]
            if (not source or source['raw_sha256']!=cell.get('raw_sha256') or
                any(source[k]!=cell.get(k) for k in ('issuer','accession')) or
                str(identity.get('cik','')).zfill(10)!=str(cell['issuer']).zfill(10)):
                raise ValueError('research_issuer_or_occurrence_binding')
            if source['source_generation'] not in review['source_generations']:
                raise ValueError('research_generation_binding')
            if (cell.get('basis')!='CFS' or cell.get('field') not in RULE['fields'] or
                not cell.get('source_span') or not cell.get('currency') or
                date.fromisoformat(cell['period_start'])>date.fromisoformat(cell['period_end']) or
                cell['period_end']>packet['as_of'][:10]):
                raise ValueError('research_exact_basis_period_or_type')
            value,scale=Decimal(str(cell['value'])),Decimal(str(cell['scale']))
            if not value.is_finite() or not scale.is_finite() or scale<=0:raise ValueError('research_value_unit')
            reasons=[]
            if set(fr['sources'])!=set(inventory):raise ValueError('research_field_inventory_omitted')
            if fr.get('exact_cell_sha256')!=digest(cell):raise ValueError('research_exact_cell_changed')
            for key,disposition in fr['sources'].items():
                if disposition not in ('ORIGINAL_EXACT','NO_COMPETING_EXACT_FIELD','DISCLOSURES_REVIEWED'):
                    reasons.append(key+':UNRESOLVED_SOURCE_CONTENT')
            for disclosure in review['disclosures']:
                item=inventory.get(disclosure.get('source_id'))
                if not item or disclosure.get('raw_sha256')!=item['raw_sha256'] or any(disclosure.get(k)!=cell[k] for k in ('issuer','accession')):
                    raise ValueError('research_disclosure_source')
                if disclosure.get('field')!=cell['field']:continue
                if disclosure.get('category')=='FORWARD_GUIDANCE':continue
                if disclosure.get('revised_period'):
                    reasons.append('REVISED_PERIOD_UNRESOLVED');continue
                if disclosure.get('period_end')!=cell['period_end']:continue
                comparison=compare_field(cell,disclosure)
                status=comparison['status']
                if status=='BASIS_UNVERIFIED':status=comparison.get('numerical_compatibility')
                if status not in ('EXACT_EQUAL','CONSISTENT_AT_DISCLOSED_PRECISION'):
                    reasons.append('DISCLOSURE_'+str(status))
            if reasons:
                denials.append(dict(occurrence_id=cell['occurrence_id'],reasons=reasons));continue
            facts.append(dict(cell,source_generation=source['source_generation'],source_url=source['url'],
                source_receipt_sha256=source['receipt_sha256'],use=USE,
                lineage_group='issuer-filing:'+cell['issuer']+':'+cell['accession']))
        projection=dict(contract=POLICY,policy_sha256=POLICY_SHA256,registry=self._id,
            security=identity,input_sha256=digest(packet),original_sha256=digest(original),review_sha256=digest(review),
            owner_approval_sha256=review['owner_approval_sha256'],reviewer_provenance=review['reviewer_provenance'],
            execution_generation=review['execution_generation'],facts=facts,denials=denials,
            limitations=review['limitations'],use=USE,consumer=CONSUMER,
            strict_financial_L3=False,strict_native=False,investment_direction_grant=False,
            valuation_denominator_grant=False,independent_corroboration=False,source_refetched=False)
        projection['receipt_sha256']=digest(projection)
        issued=self._clock()
        if not math.isfinite(issued):raise ValueError('research_clock_invalid')
        handle=ResearchReference();self._issued[handle]=(digest(original),digest(review),issued,issued+ttl_seconds,projection)
        return handle

    def project(self, packet, handle):
        if type(handle) is not ResearchReference or handle not in self._issued:raise ValueError('research_live_receipt_required')
        original,review,_=self._inputs();o,r,start,end,projection=self._issued[handle]
        if digest(original)!=o or digest(review)!=r or digest(packet)!=projection['input_sha256']:
            raise ValueError('research_source_review_or_invocation_changed')
        now=self._clock()
        if not math.isfinite(now) or not start<=now<=end:raise ValueError('research_receipt_expired')
        return deepcopy(projection)

    def revoke(self,handle):
        if os.getpid()!=self._pid or handle not in self._issued:raise ValueError('research_live_receipt_required')
        del self._issued[handle]


def project(packet, capability):
    registry,handle=capability
    if type(registry) is not ResearchSourceRegistry:raise ValueError('research_backend_registry_required')
    return registry.project(packet,handle)


def catalog(projection):
    numbers=[]
    for f in projection['facts']:
        row=dict(field='research_exact.'+f['field'],path=f['occurrence_id'],value=float(f['value']),
            unit=f['currency']+' x'+str(f['scale']),basis='CFS HISTORICAL RESEARCH ONLY',
            as_of=f['period_start']+'/'+f['period_end'],source_sha=f['raw_sha256'],lineage_group=f['lineage_group'])
        numbers.append(dict(row,catalog_id='r'+digest(row)[:24]))
    return numbers
