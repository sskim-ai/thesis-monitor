"""Explicit selected research Source scope; legacy Full22 plans remain unchanged.

Compilation freezes requests, not credentials or financial eligibility. A live
registration Owner and original native metadata are required before dispatch.
"""
from datetime import datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import Field, model_validator

from app.macro.providers.eia import EIA_SERIES
from app.macro.providers.fred import FRED_SERIES
from app.macro.providers.market import MARKET_SYMBOLS
from app.services.bounded_financial_acquisition import make_plan
from app.services.kiwoom_kr_market_context_service import kiwoom_market_reads
from app.services.market_session import korea_market_session, us_market_session
from app.services.scoped_source_plan import ScopedStockRead
from app.services.sealed_fresh_dispatch import RequestPlan
from app.services.unified_snapshot_contract import ContractModel, digest
from app.services.unified_stock_acquisition import ROLES, stock_read_fields

SCOPE = 'SELECTED_ORIGINAL_RESEARCH_V1'
STOCK_CONTRACT = 'selected-original-stock-plan-v1'
WIRE_CONTRACT = 'selected-original-source-request-plan-v1'
COUNTS = dict(adjusted_daily=1000,adjusted_weekly=700,adjusted_monthly=300,unadjusted_weekly_valuation=700)


class SelectedStockPlan(ContractModel):
    contract: Literal['selected-original-stock-plan-v1'] = STOCK_CONTRACT
    market: Literal['us','kr']
    subjects: tuple[str,...] = Field(min_length=1,max_length=22)
    run_id: str
    acquisition_id: str
    frozen_at: datetime
    instruction_sha: str = Field(pattern=r'^[a-f0-9]{40}$')
    implementation_sha: str = Field(pattern=r'^[a-f0-9]{40}$')
    universe_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    reads: tuple[ScopedStockRead,...]
    owner_files: dict[str,str]
    owner_head: str | None
    settings_sha256: str | None
    request_environment_sha256: str | None
    planning_only: bool = True
    automatic_retries: Literal[0] = 0
    maximum_auth_requests: Literal[1] = 1

    @property
    def universe(self):
        return {self.market:self.subjects}

    @model_validator(mode='after')
    def selected_complete(self):
        expected={f'{self.market}:{t}:{r}' for t in self.subjects for r in ROLES}
        if (self.frozen_at.utcoffset() is None or not self.run_id or not self.acquisition_id
                or tuple(sorted(set(self.subjects)))!=self.subjects
                or len(self.reads)!=len(expected) or {r.entry_id for r in self.reads}!=expected
                or any(r.market!=self.market or r.count!=COUNTS[r.role] for r in self.reads)):
            raise ValueError('selected_exact_original_four_roles_required')
        for t in self.subjects:
            rows=[r for r in self.reads if r.subject==t]
            if len({(r.canonical_security_id,r.latest_completed_session) for r in rows})!=1:
                raise ValueError('selected_stock_identity_or_session_conflict')
        if not self.planning_only and (not self.owner_files or not all((self.owner_head,
                self.settings_sha256,self.request_environment_sha256))):
            raise ValueError('selected_original_native_metadata_required')
        return self


def build_stock_plan(*,market,identities,at,generation,code_sha,counts,native=None,registration_sha256=None):
    state=(us_market_session if market=='us' else korea_market_session)(at)
    names=tuple(sorted(identities))
    reads=tuple(ScopedStockRead(**stock_read_fields(subject=t,identity=identities[t],market=market,
        role=r,count=counts[r],at=at,state=state)) for t in names for r in ROLES)
    native=native or {}
    return SelectedStockPlan(market=market,subjects=names,run_id=generation,
        acquisition_id=generation+':stock',frozen_at=at,instruction_sha=code_sha,implementation_sha=code_sha,
        universe_sha256=digest(dict(market=market,subjects=names,registration_sha256=registration_sha256)),reads=reads,
        owner_files=native.get('owner_files',{}),owner_head=native.get('owner_head'),
        settings_sha256=native.get('settings_sha256'),request_environment_sha256=native.get('request_environment_sha256'),
        planning_only=not bool(native and registration_sha256))


def acquisition_plan(stock,identities,*,kr_max_pages,exact_financial_owner=False,
                     auxiliary_security=None,auxiliary_identity_sha256=None,transient_retry_max=None):
    if (type(stock) is not SelectedStockPlan or set(identities)!=set(stock.subjects)
            or transient_retry_max!=0 or auxiliary_security is not None or auxiliary_identity_sha256 is not None):
        raise ValueError('selected_explicit_no_retry_scope_required')
    # Direct financial ownership is generic. An issuer bridge is not guessed
    # from a ticker/CIK and cannot transfer per-share or price authority.
    financial={t:make_plan(s,market=stock.market,cutoff=stock.frozen_at,run_id=stock.run_id,
        all_subjects_fresh=True,exact_financial_owner=exact_financial_owner,maximum_retries_per_request=0)
        for t,s in identities.items()}
    kr=() if stock.market=='us' else kiwoom_market_reads(
        session_date=korea_market_session(stock.frozen_at).latest_completed_regular_session_date,
        max_pages=kr_max_pages,max_requests_per_page=1)
    day=stock.frozen_at.astimezone(ZoneInfo('Asia/Seoul')).date()
    begin=day.replace(day=1)-timedelta(days=7)
    days=[(begin+timedelta(days=i)).isoformat() for i in range((day-begin).days+1)]
    macro={'ecos':{'route':'KeyStatisticList','start':1,'end':100,'period_field':'CYCLE'}}
    if stock.market=='us':
        macro.update(fred={'series':list(FRED_SERIES),'limit':5,'sort_order':'desc','observation_end':stock.frozen_at.date().isoformat()},
            eia={'series':list(EIA_SERIES),'length':1})
    value=dict(contract='selected-original-acquisition-plan-v1',run_id=stock.run_id,
        started_at=stock.frozen_at.isoformat(),scope=SCOPE,selected_market=stock.market,
        current_subjects=list(stock.subjects),retained_subjects=[],financial_plans=financial,
        kr_market_reads=[r.model_dump(mode='json') for r in kr],
        us_market_symbols=list(MARKET_SYMBOLS) if stock.market=='us' else [],
        night_query_dates=days,macro_queries=macro,dispatch_allowed=False,
        source_identity_sha256=digest(identities),source_use='NOT_ISSUED')
    return dict(value,plan_sha256=digest(value))


class SelectedRequestPlan(RequestPlan):
    contract: Literal['selected-original-source-request-plan-v1'] = WIRE_CONTRACT
    purpose: Literal['SELECTED_ORIGINAL_RESEARCH_V1'] = SCOPE
    market: Literal['us','kr']
    subjects: tuple[str,...]
    stock_plan_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    compiler_input_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    compiler_output_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    kis_plan_sha256: str | None = Field(default=None,pattern=r'^[a-f0-9]{64}$')

    @model_validator(mode='after')
    def required_scope(self):
        if (not self.subjects or tuple(sorted(set(self.subjects)))!=self.subjects
                or self.unresolved_roles or any(d.transient_retry_max!=0 for d in self.descriptors)):
            raise ValueError('selected_complete_bounded_wire_required')
        for t in self.subjects:
            if any(not any(d.subject==t and d.consumer_role=='stock:'+f'{self.market}:{t}:{r}'
                    for d in self.descriptors) for r in ROLES):
                raise ValueError('selected_stock_family_missing')
            if not any(d.subject==t and d.consumer_role=='financial:'+t for d in self.descriptors):
                raise ValueError('selected_financial_family_missing')
        if self.market=='us' and {d.subject for d in self.descriptors if d.consumer_role.startswith('completed_close:')}!=set(self.subjects):
            raise ValueError('selected_original_us_completed_close_required')
        if (self.market=='kr')!=(self.kis_plan_sha256 is not None):
            raise ValueError('selected_kis_market_binding')
        return self


def compile_selected_plan(*,compiler_args,kis_plan=None):
    from app.services.canonical_source_plan import compile_slots
    from app.services.production_source_plan import _compiler_identity
    stock=compiler_args['stock']
    if stock.market == 'kr':
        from app.services.selected_kis_sources import validate_plan
        if (kis_plan is None or validate_plan(kis_plan)!=stock.subjects
                or kis_plan['generation_id']!=stock.run_id
                or datetime.fromisoformat(kis_plan['as_of'])!=stock.frozen_at
                or kis_plan['securities']!={t:dict(s,currency='KRW') for t,s in compiler_args['identities'].items()}):
            raise ValueError('selected_kis_same_generation_required')
    elif kis_plan is not None:
        raise ValueError('selected_us_kis_scope_denied')
    result=compile_slots(**compiler_args,selected_research_v1=True)
    raw=result['plan'].model_dump()
    result['plan']=SelectedRequestPlan(**raw,market=stock.market,subjects=stock.subjects,
        stock_plan_sha256=digest(stock.model_dump(mode='json')),
        compiler_input_sha256=_compiler_identity(compiler_args),
        compiler_output_sha256=digest({k:v for k,v in result.items() if k!='plan'}),
        kis_plan_sha256=digest(kis_plan) if kis_plan is not None else None)
    return result


def decode_stock_plan(frozen):
    if frozen.get('scope')==SCOPE:
        return SelectedStockPlan.model_validate(frozen['stock_plan'])
    from app.services.unified_stock_acquisition import StockPlan
    return StockPlan.model_validate(frozen['stock_plan'])


def request_budget(compiled, kis_plan=None):
    """Physical ceilings, including auth and every possible continuation slot."""
    budget = {}
    for d in compiled['plan'].descriptors:
        budget[d.provider] = budget.get(d.provider,0)+d.max_transport_attempts
    if kis_plan is not None:
        from app.services.selected_kis_sources import validate_plan
        validate_plan(kis_plan)
        budget['kis'] = kis_plan['maximum_physical_HTTP']
    return dict(providers=budget,total=sum(budget.values()),retries=0,
        interpretation='UPPER_BOUND_NOT_MINIMUM_OR_ACTUAL_COUNT')
