"""Opt-in Korean FY1 evidence, separate from business-direction authority."""
from datetime import datetime
from decimal import Decimal
import math
from typing import Literal

from pydantic import Field, model_validator

from app.services.current_fresh_valuation import CurrentValuationView
from app.services.numeric_semantic_registry import build_numeric_registry
from app.services.unified_snapshot_contract import ContractModel, digest

CONTEXT = 'kr-fy1-valuation-calibration-context-v1'
METRICS = ('CURRENT_FY1_FPER', 'RESEARCH_FY1_PER', 'FY1_EPS')
LABELS = dict(zip(METRICS, ('현재가 기준 fPER(FY1)', 'KIS 리서치 fPER(FY1)', 'FY1 EPS'), strict=True))
PROMPT = '''The typed valuation_context is only for NewBuyer/Holder valuation
calibration, never Overall, Core, Pass-A, business direction, directional balance,
or supporting/contradicting business refs. Preserve the existing axis capability.
PER/PBR are existing Kiwoom snapshots. CURRENT_FY1_FPER is independently derived
from a qualified unadjusted completed-session KIS close and dated KIS FY1 EPS.
RESEARCH_FY1_PER is a separate dated KIS house-research snapshot. FY1_EPS is also
KIS house research, NOT consensus, NTM or 12M forward. Never conflate the two
forward PERs or use either as a fair value, target or discount calculation.
Select exact qualified refs only in new_buyer_valuation_refs/holder_valuation_refs.
Unavailable and N/M are not zero; they cannot provide numeric refs. Do not invent
a multiple. Rationale may explain the valuation implication without exact numbers;
the typed valuation renderer exclusively owns values, dates and display labels.
Missing valuation does not change business-direction evidence or force a verdict.'''


class KrForwardValuationView(ContractModel):
    contract: Literal['kr-fresh-fy1-valuation-view-v1'] = 'kr-fresh-fy1-valuation-view-v1'
    native: CurrentValuationView
    kis: dict
    as_of: datetime
    fresh_plan_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    source_corpus_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    overall_direction_use: Literal[False] = False

    @model_validator(mode='after')
    def bound(self):
        from scripts.kis_current_fy1_owner import validate_current_fper, eps_receipt
        from scripts.kis_eps_wire_calibration import verified
        from scripts.kis_output3_protocol_owner import SNAPSHOT
        from scripts.kis_fy1_semantic_owner import ALLOWED_ROLES, PROHIBITED_ROLES
        row, code = self.kis, self.native.ticker
        if (not code.isascii() or not code.isdigit() or len(code) != 6
                or row['security_code'] != code or self.as_of.utcoffset() is None
                or self.native.currency != 'KRW'):
            raise ValueError('kr_forward_security_or_time_gap')
        for name, state, metric in (('eps','KIS_FY1_EPS_ESTIMATE_SNAPSHOT','EPS'),
                                    ('provider_per','KIS_PROVIDER_FY1_PER_SNAPSHOT','PER')):
            receipt = row[name]
            if receipt['state'] == state:
                verified(receipt, SNAPSHOT)
                when = datetime.fromisoformat(receipt['query_time'])
                if (when.utcoffset() is None or not Decimal(receipt['value']).is_finite()
                        or receipt['unit'] != ('KRW_PER_SHARE' if metric == 'EPS' else 'MULTIPLE')):
                    raise ValueError('kr_forward_unit_value_time_gap')
                if (receipt['security_code'] != code or receipt['metric'] != metric
                        or receipt['source_kind'] != 'KIS_HOUSE_RESEARCH_NOT_CONSENSUS'
                        or receipt['overall_direction_use'] is not False
                        or tuple(receipt['allowed_roles']) != ALLOWED_ROLES
                        or tuple(receipt['prohibited_roles']) != PROHIBITED_ROLES
                        or when < self.as_of):
                    raise ValueError('kr_forward_snapshot_identity_freshness_authority_gap')
                if metric == 'EPS':
                    eps_receipt(receipt)
            elif receipt.get('value') is not None or not receipt['state'].startswith('UNAVAILABLE_'):
                raise ValueError('kr_forward_unavailable_value_leak')
        if row['price'] is not None and row['price']['canonical_security_id'] != self.native.security_id:
            raise ValueError('kr_forward_current_security_mismatch')
        if row['provider_per']['state'] == 'KIS_PROVIDER_FY1_PER_SNAPSHOT':
            if row['eps']['state'] != 'KIS_FY1_EPS_ESTIMATE_SNAPSHOT' or any(
                    row['provider_per'][key] != row['eps'][key]
                    for key in ('security', 'period', 'estdate', 'estimate_sha256')):
                raise ValueError('kr_forward_research_fiscal_security_gap')
        validate_current_fper(row['current_fper'],row['eps'],row['price'],row['action'])
        if any(m.metric == 'fPER' and m.status == 'QUALIFIED' for m in self.native.metrics):
            raise ValueError('kr_forward_native_fper_owner_collision')
        return self


def forward_states(view):
    view = KrForwardValuationView.model_validate(view)
    source = (view.kis['current_fper'],view.kis['provider_per'],view.kis['eps'])
    rows=[]
    for metric, receipt in zip(METRICS,source,strict=True):
        qualified = receipt['state'] in {'QUALIFIED','KIS_PROVIDER_FY1_PER_SNAPSHOT','KIS_FY1_EPS_ESTIMATE_SNAPSHOT'}
        rows.append(dict(metric=metric,label=LABELS[metric],state=receipt['state'],
            value=receipt.get('value') if qualified else None,
            fact_ref=f'kr-forward-valuation:{view.native.security_id}:{metric}' if qualified else None,
            estimate_date=receipt.get('eps_estimate_date',receipt.get('estdate')),
            price_date=receipt.get('session_date'), period=receipt.get('fy1_period',receipt.get('period')),
            input_receipt_sha256=receipt.get('receipt_sha256',digest(receipt)),
            overall_direction_use=False))
    return rows


def forward_bindings(view):
    view = KrForwardValuationView.model_validate(view)
    result={}
    for row in forward_states(view):
        if row['fact_ref'] is None:
            continue
        field='forward_eps' if row['metric']=='FY1_EPS' else 'forward_pe'
        value=float(Decimal(row['value']))
        if not math.isfinite(value):
            raise ValueError('kr_forward_registry_nonfinite')
        fact=dict(fact_id=row['fact_ref'],fact_type='valuation',ticker=view.native.ticker,
            as_of_date=row['estimate_date'],fields={field:value,'currency':'KRW'},
            decimal_value=row['value'],metric_family=row['metric'],
            input_receipt_sha256=row['input_receipt_sha256'],
            valuation_view_sha256=digest(view.model_dump(mode='json')),overall_direction_use=False)
        registry=build_numeric_registry([fact])
        if len(registry)!=1 or not registry[0]['registered'] or registry[0]['unit'] != ('KRW' if field=='forward_eps' else 'x'):
            raise ValueError('kr_forward_numeric_registry_gap')
        result[row['metric']]=dict(fact=fact,registry=registry[0])
    return result


class KrValuationCalibrationContext(ContractModel):
    contract: Literal['kr-fy1-valuation-calibration-context-v1'] = CONTEXT
    ticker: str
    run_id: str
    security_id: str
    valuation_view_sha256: str
    metric_states: tuple[dict, ...]
    facts: dict
    overall_direction_use: Literal[False] = False
    allowed_axes: tuple[Literal['NEW_BUYER','HOLDER'], ...] = ('NEW_BUYER','HOLDER')
    context_sha256: str

    @model_validator(mode='after')
    def bound(self):
        if self.context_sha256 != digest(self.model_dump(mode='json',exclude={'context_sha256'})):
            raise ValueError('kr_valuation_context_hash_mismatch')
        if tuple(r['metric'] for r in self.metric_states) != ('PER','PBR',*METRICS):
            raise ValueError('kr_valuation_family_set_gap')
        expected={r['fact_ref'] for r in self.metric_states if r['fact_ref'] is not None}
        if expected != set(self.facts):
            raise ValueError('kr_valuation_fact_set_gap')
        for row in self.metric_states:
            if row.get('overall_direction_use') is not False:
                raise ValueError('kr_valuation_direction_permission_leak')
            if row['fact_ref'] is None and row['value'] is not None:
                raise ValueError('kr_valuation_unavailable_value_leak')
            if row['fact_ref'] is not None:
                fact=self.facts[row['fact_ref']]['fact']
                if fact['overall_direction_use'] is not False or fact['ticker'] != self.ticker:
                    raise ValueError('kr_valuation_fact_authority_gap')
        return self


def calibration_context(view):
    from app.services.provider_valuation_calibration_context import calibration_context as native_context
    view=KrForwardValuationView.model_validate(view)
    native=native_context(view.native)
    rows=native['metric_states'][:2]+forward_states(view)
    facts={k:v for k,v in native['facts'].items() if k in {r['fact_ref'] for r in rows[:2]}}
    facts.update({v['fact']['fact_id']:v for v in forward_bindings(view).values()})
    value=KrValuationCalibrationContext.model_construct(ticker=view.native.ticker,run_id=view.native.run_id,
        security_id=view.native.security_id,valuation_view_sha256=digest(view.model_dump(mode='json')),
        metric_states=tuple(rows),facts=facts,context_sha256='').model_dump(mode='json',exclude={'context_sha256'})
    return KrValuationCalibrationContext.model_validate({**value,'context_sha256':digest(value)}).model_dump(mode='json')


def validate_output(raw, context):
    from app.services.provider_valuation_calibration_context import require_direction_isolation, VALUATION_TERMS
    context=KrValuationCalibrationContext.model_validate(context)
    require_direction_isolation(raw['overall'])
    if VALUATION_TERMS.search(raw['overall']['overall_reason']) or 'FY1' in raw['overall']['overall_reason']:
        raise ValueError('kr_valuation_overall_reason_scope')
    selected={}
    for axis in ('new_buyer','holder'):
        row=raw[axis+'_axis']
        field=axis+'_valuation_refs'
        refs=row[field]
        if not isinstance(refs,list) or len(refs)!=len(set(refs)) or not set(refs)<=set(context.facts):
            raise ValueError('kr_valuation_axis_ref_not_owned')
        require_direction_isolation({k:v for k,v in row.items() if k!=field})
        text=row[axis+'_reason']
        mentioned={t.casefold() for t in VALUATION_TERMS.findall(text)}
        groups=[]
        if mentioned & {'per','p/e','주가수익비율'}:
            groups.append({'PER'})
        if mentioned & {'pbr','p/b','주가순자산비율'}:
            groups.append({'PBR'})
        if 'fper' in mentioned:
            groups.append({'RESEARCH_FY1_PER'} if '리서치' in text and '현재가' not in text else
                          {'CURRENT_FY1_FPER'} if '현재가' in text and '리서치' not in text else
                          {'CURRENT_FY1_FPER','RESEARCH_FY1_PER'})
        if 'EPS' in text.upper():
            groups.append({'FY1_EPS'})
        for group in groups:
            available={r['fact_ref'] for r in context.metric_states if r['metric'] in group and r['fact_ref'] is not None}
            if available and not available.intersection(refs):
                raise ValueError('kr_valuation_reason_requires_axis_ref')
        selected[axis]=refs
    return dict(status='PASS',context_sha256=context.context_sha256,selected_refs=selected,
        overall_direction_use=False,business_capabilities_modified=False)
