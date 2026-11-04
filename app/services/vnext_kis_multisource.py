"""Backend-reviewed, immutable multi-parent KIS dated research, not current L3.

The callback is trusted archive/receipt bootstrap code. It is never supplied by
model or API JSON. Consumer lookup rechecks that live capability and every parent.
"""
from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
import json

from app.services.vnext_research_store import digest
from app.services.vnext_kis_source_state import ReviewedKISSourceObservations
from scripts.kis_fy1_semantic_owner import Evidence, Documentation, security_binding
from scripts import kis_output3_protocol_owner as protocol
from scripts import kis_current_fy1_owner as price
from scripts import kis_exact_action_guard as action
from scripts.kr8_kis_integration import normalized_inventory

CONTRACT = 'kis-reviewed-multisource-research-v1'
POLICY = {
    'version': 'kis-dated-research-temporal-use-v1',
    'authority': 'NG82_TASK_AUTHORIZED_DATED_RESEARCH',
    'allowed_use': 'PUBLIC_RESEARCH_REFERENCE_ONLY',
    'value_status': 'DATED_RESEARCH_ONLY',
    'latest_fiscal_at_consumer_cutoff': 'UNVERIFIED',
    'strict_financial_l3': False, 'direction_allowed': False,
    'consensus': False, 'current_valuation': False,
}
POLICY_DIGEST = digest(POLICY)
IDENTITY = ('ticker','canonical_security_id','canonical_company_id','country',
            'exchange','security_type','issuer_type','corp_code')


def instant(value):
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise ValueError('explicit_parent_time_required')
    return d


def evidence(raw):
    return Evidence(raw.encode(), digest(raw.encode()))


def parent(role, item, run, cutoff, *, fiscal=False):
    raw, r = item['raw'].encode(), item['receipt']
    at = item['original_owner_receipt']['finished_at'] if fiscal else r['ended_at']
    if (not run or len(raw) > 2*1024**2 or digest(raw) != r['raw_sha256']
            or r['http_status'] != 200 or instant(at) > instant(cutoff)
            or r.get('bytes', len(raw)) != len(raw)):
        raise ValueError('original_parent_receipt_binding')
    if fiscal:
        o = item['original_owner_receipt']
        if (r['generation_id'] != run or o['sealed_generation_id'] != run
                or o['raw_sha256'] != r['raw_sha256'] or o['failure_class']
                or o['sealed_final_receipt_sha256'] != r['sealed_final_receipt_sha256']):
            raise ValueError('fiscal_original_receipt_binding')
    else:
        req = r['request']
        if (req['method'] != 'GET' or req.get('redirects', False)
                or req.get('retries', 0) != 0 or instant(req['started_at']) > instant(at)):
            raise ValueError('original_parent_request_binding')
    return dict(role=role,source_run=run,raw_sha256=digest(raw),
                original_receipt_sha256=digest(r),captured_at=at,
                as_of_scope=item.get('as_of',at),request_sha256=digest(r['request']))


class ReviewedMultisourceKIS:
    def __init__(self, reviewed_capture):
        if not callable(reviewed_capture):
            raise ValueError('trusted_multisource_bootstrap_required')
        self._read = reviewed_capture
        b = deepcopy(reviewed_capture())
        self._pin, self._revoked, self._parents = digest(b), False, set()
        source = ReviewedKISSourceObservations(lambda:b['source'])
        source.original_batch()
        ids = [e['security']['ticker'] for e in b['entries']]
        if not 1 <= len(ids) <= 500 or len(ids) != len(set(ids)):
            raise ValueError('multisource_subject_bound')

    def revoke(self, parent_sha=None):
        if parent_sha is None:
            self._revoked = True
        else:
            self._parents.add(parent_sha)

    def original_batch(self):
        b = deepcopy(self._read())
        if self._revoked or digest(b) != self._pin:
            raise ValueError('multisource_changed_or_revoked')
        return b

    def capsule(self, security):
        b = self.original_batch()
        matches = [e for e in b['entries'] if e['security']['ticker']==security['ticker']]
        if not matches:
            return None
        if len(matches)!=1 or any(matches[0]['security'].get(k)!=security.get(k) for k in IDENTITY):
            raise ValueError('multisource_security_binding')
        return dict(contract=CONTRACT,policy=POLICY,policy_digest=POLICY_DIGEST,
                    review_digest=self._pin,entry=matches[0])

    def snapshots(self, *, security, cutoff):
        cap = self.capsule(security)
        if cap is None:
            return []
        e=cap['entry'];s=e['security'];code=s['ticker'];b=self.original_batch()
        if (s['country']!='KR' or s['exchange'] not in ('KRX','KOSPI','KOSDAQ')
                or s['security_type'].lower() not in ('common stock','common_stock')
                or s['issuer_type'].lower() in ('ads','adr','unknown')
                or any(e['historical_security'].get(k)!=s.get(k) for k in
                       ('ticker','canonical_security_id','canonical_company_id','country','exchange','corp_code'))):
            raise ValueError('dated_domestic_ordinary_identity_required')
        original = ReviewedKISSourceObservations(lambda:b['source'])
        source = original.project(security=s,as_of=cutoff)
        match = [x for x in b['source']['captures'] if x['security']['ticker']==code]
        if len(match)!=1 or match[0]!=e['estimate'] or not source or not source.get('estimate_date'):
            raise ValueError('original_estimate_capture_required')
        f=e['fiscal'];i=e['identity'];d=e['static']
        edges=[parent('estimate',e['estimate'],b['source']['plan']['generation_id'],cutoff),
               parent('security_identity',i,i['source_run'],cutoff),
               parent('fiscal_inventory',f,f['source_run'],cutoff,fiscal=True)]
        if date.fromisoformat(f['as_of']) > date.fromisoformat(source['captured_at'][:10]):
            raise ValueError('fiscal_anchor_after_estimate_capture')
        inv,projection=normalized_inventory(evidence(f['raw']),f['receipt'],code=code,corp_code=s['corp_code'])
        if projection!=f['projection']:
            raise ValueError('fiscal_projection_changed')
        if e['review']['scope']!='SEALED_INPUTS_ONLY_NO_CURRENT_FILING_CENSUS' or e['review']['observed_conflicts']:
            raise ValueError('observed_fiscal_or_share_conflict')
        docs=Documentation(evidence(d['docs']))
        row=protocol.qualify(code,evidence(e['estimate']['raw']),evidence(i['raw']),inv,s['corp_code'],
            date.fromisoformat(f['as_of']),docs,[evidence(r) for r in d['controls']],d['scale'],
            e['estimate']['receipt']['ended_at'],date.fromisoformat(cutoff[:10]))
        eps=row['eps'];value=price.eps_receipt(eps)
        if eps['unit']!='KRW_PER_SHARE' or eps['factor']!='0.1':
            raise ValueError('original_eps_unit_required')
        if any(x['raw_sha256'] in self._parents for x in edges):
            raise ValueError('multisource_parent_revoked')
        common=dict(contract=CONTRACT,policy_version=POLICY['version'],policy_digest=POLICY_DIGEST,
            review_digest=self._pin,canonical_security_id=s['canonical_security_id'],
            requested_security_id=code,period=eps['period'],estimate_date=eps['estdate'],
            fiscal_inventory_as_of=f['as_of'],fiscal_annual=eps['fiscal']['report_name'],
            fiscal_receipt_id=eps['fiscal']['receipt_id'],latest_fiscal_at_consumer_cutoff='UNVERIFIED',
            source_kind='KIS_HOUSE_RESEARCH_NOT_CONSENSUS',retrieval_timestamp=eps['query_time'],
            allowed_use=POLICY['allowed_use'],value_status='DATED_RESEARCH_ONLY',
            display_eligible=True,strict_native=False,strict_financial_l3=False,
            direction_allowed=False,current_valuation=False,consensus=False,
            original_eps_receipt_sha256=eps['receipt_sha256'],
            source_generation=b['source']['plan']['generation_id'],
            caveat='Dated provider house forecast; latest annual filings at consumer cutoff unverified. Not consensus or investment direction.')
        def snapshot(metric,exact,unit,basis,parents):
            return dict(common,metric=metric,value=float(Decimal(exact)),exact_value=str(exact),
                        unit=unit,metric_semantic=basis,parents=parents,lineage_sha256=digest(parents))
        result=[snapshot('FY1_EPS',str(value),'KRW_PER_SHARE','DATED_KIS_HOUSE_FY1_EPS',edges)]
        support=e.get('support')
        if support:
            # Price/action eligibility remains independent of standalone EPS.
            try:
                plan=support['plan'];sr=plan['generation_id'];se=support['identity']
                extra=[parent('price_identity',se,sr,cutoff),parent('unadjusted_close',support['price'],sr,cutoff)]
                bound=security_binding(code,json.loads(e['estimate']['raw']),evidence(se['raw']))
                if bound['standard_code']!=eps['security']['standard_code'] or plan['subjects']!=[code]:
                    raise ValueError('price_security_identity_conflict')
                pr=protocol.qualify(code,evidence(e['estimate']['raw']),evidence(se['raw']),inv,s['corp_code'],
                    date.fromisoformat(f['as_of']),docs,[evidence(r) for r in d['controls']],d['scale'],
                    eps['query_time'],date.fromisoformat(plan['as_of'][:10]))
                pe=pr['eps']
                close=price.price_receipt(pe,dict(s,currency='KRW',standard_code=bound['standard_code']),
                    evidence(support['price']['raw']),support['price']['receipt'],plan['calendar'],d['price_docs'])
                if set(support['actions'])!=set(action.VARIANTS):
                    raise ValueError('six_distinct_action_families_required')
                families={}
                for variant,item in support['actions'].items():
                    extra.append(parent('action:'+variant,item,sr,cutoff))
                    families[variant]=action.family_receipt(variant,code,pe['estdate'],close['session_date'],
                        [(evidence(item['raw']),item['receipt'])],d['action_docs'])
                guard=action.compatibility_receipt(pe,close,families)
                fper=price.current_fper(pe,close,guard)
                old=support['original_owner']
                if (close!=old['price'] or guard!=old['action'] or fper!=old['current_fper']
                        or fper['state']!='QUALIFIED' or any(x['raw_sha256'] in self._parents for x in extra)):
                    raise ValueError('original_fper_replay_or_revocation')
                result.append(dict(snapshot('FPER',fper['display_value'],'multiple',
                    'DATED_UNADJUSTED_CLOSE_DIVIDED_BY_KIS_HOUSE_FY1_EPS',edges+extra),
                    price_session=close['session_date'],price_value=close['close'],share_unit_guard=guard['receipt_sha256']))
            except (ValueError,KeyError,TypeError) as exc:
                result[0]['FPER_gap']=str(exc)
        else:
            result[0]['FPER_gap']='MISSING_SECURITY_SPECIFIC_CLOSE_AND_SIX_ACTION_FAMILIES'
        return result

    def verify(self,capsule,snapshot,*,security,cutoff):
        if capsule!=self.capsule(security) or snapshot not in self.snapshots(security=security,cutoff=cutoff):
            raise ValueError('unissued_or_changed_multisource_observation')
        return snapshot

    def capsule_for_snapshot(self, security, snapshot):
        if snapshot.get('review_digest') != self._pin:
            raise ValueError('unknown_multisource_review')
        return self.capsule(security)


class ReviewedMultisourceKISHistory(ReviewedMultisourceKIS):
    """Live backend capabilities for exact original and later derived reviews.

    This preserves stored parents instead of rewriting old observations to the
    latest review. Public capsule JSON cannot register an additional authority.
    """
    def __init__(self, current, *historical):
        owners=(current,*historical)
        if any(type(o) is not ReviewedMultisourceKIS for o in owners):
            raise ValueError('original_live_multisource_owners_required')
        self._owners={digest(o.original_batch()):o for o in owners}
        if len(self._owners)!=len(owners):
            raise ValueError('duplicate_multisource_review')
        super().__init__(current.original_batch)

    def capsule_for_snapshot(self, security, snapshot):
        self.original_batch()
        owner=self._owners.get(snapshot.get('review_digest'))
        if owner is None:raise ValueError('unknown_multisource_review')
        return owner.capsule_for_snapshot(security,snapshot)

    def verify(self,capsule,snapshot,*,security,cutoff):
        expected=self.capsule_for_snapshot(security,snapshot)
        if capsule!=expected:raise ValueError('multisource_review_capsule_mismatch')
        return self._owners[snapshot['review_digest']].verify(capsule,snapshot,security=security,cutoff=cutoff)

    def revoke(self,parent_sha=None):
        super().revoke(parent_sha)
        for owner in self._owners.values():owner.revoke(parent_sha)
