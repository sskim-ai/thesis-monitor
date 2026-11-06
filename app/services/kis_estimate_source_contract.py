"""Bounded estimate/identity Source only; original full FY1 Owner unchanged."""
from datetime import datetime
from scripts import kr8_kis_integration as original
from scripts import kis_estimate_capability_probe as base
from scripts.kis_protocol_stage_b_probe import IDENTITY_PATH,IDENTITY_TR
from scripts.kis_eps_wire_calibration import sealed

CONTRACT='kis-estimate-identity-source-only-v1'


def build_source_plan(*,generation_id,as_of,securities):
    if set(securities)!=set(original.SUBJECTS):
        raise ValueError('kis_source_original_kr8_set_required')
    if (datetime.fromisoformat(as_of).utcoffset() is None or any(
            s['ticker']!=t or s.get('country')!='KR' for t,s in securities.items())):
        raise ValueError('kis_source_original_identity_required')
    requests=[dict(kind='estimate',subject=t,method='GET',path=base.DATA_PATH,
        tr_id=base.TR_ID,params={'SHT_CD':t}) for t in sorted(securities)]
    requests += [dict(kind='identity',subject=t,method='GET',path=IDENTITY_PATH,
        tr_id=IDENTITY_TR,params={'PDNO':t,'PRDT_TYPE_CD':'300'}) for t in sorted(securities)]
    return sealed(dict(contract=CONTRACT,generation_id=generation_id,as_of=as_of,
        securities=securities,calendar=original.price.calendar_receipt(as_of),requests=requests,
        auth_max=1,stage1_max=9,total_physical_max=17,retries=0,
        price_calls=0,action_calls=0,qualified_FY1=False,FPER=False,send=False))


class EstimateSourceProbe(original.FreshProbe):
    def __init__(self,*args,plan,enabled=False,**kwargs):
        if enabled is not True or plan!=build_source_plan(generation_id=plan['generation_id'],
                as_of=plan['as_of'],securities=plan['securities']):
            raise ValueError('kis_source_exact_enabled_plan_required')
        super().__init__(*args,plan=plan,**kwargs)

    def fetch(self,code,kind,*,eps=None):
        if kind not in ('estimate','identity') or eps is not None:
            raise base.ProbeStop('KIS_SOURCE_PRICE_ACTION_OR_FY1_DENIED')
        if kind=='identity' and not all((t,'estimate') in self.calls for t in self.plan['securities']):
            raise base.ProbeStop('KIS_SOURCE_ESTIMATE_STAGE_INCOMPLETE')
        if self.auth_count+self.data_count>=17:
            raise base.ProbeStop('KIS_SOURCE_SEVENTEEN_PHYSICAL_CAP')
        return super().fetch(code,kind)


def cold_source(root,plan):
    """Verify original non-auth raw receipts; does not infer any EPS metric."""
    import json
    from pathlib import Path
    from hashlib import sha256
    from scripts.kis_current_fy1_owner import _source
    root=Path(root)
    if plan!=build_source_plan(generation_id=plan['generation_id'],as_of=plan['as_of'],securities=plan['securities']):
        raise ValueError('kis_source_cold_plan_changed')
    rows=[]
    for r in plan['requests']:
        path=root/r['kind']/(r['subject']+'-receipt.json')
        if not path.exists():continue
        if path.is_symlink():raise ValueError('kis_source_symlink_denied')
        receipt=json.loads(path.read_bytes());body=path.with_name(r['subject']+'.body')
        if body.is_symlink():raise ValueError('kis_source_symlink_denied')
        evidence=original.evidence(body)
        _source(evidence,receipt,r['path'],r['tr_id'],r['params'])
        if receipt['request']['plan_sha256']!=plan['receipt_sha256']:
            raise ValueError('kis_source_cold_plan_binding')
        rows.append(dict(subject=r['subject'],kind=r['kind'],raw_sha256=sha256(evidence.raw).hexdigest(),
            raw_received=True,qualified_FY1=False,FPER=False))
    return dict(contract=CONTRACT,status='SOURCE_ONLY_COLD_PASS' if rows else 'NO_CAPTURE',rows=rows,
        required_for_FY1=['original inventory','documentation/controls/scale','original period and units'],
        required_for_FPER=['original qualified EPS','price','corporate action/share unit guard'],
        new_economic_owner=False)
