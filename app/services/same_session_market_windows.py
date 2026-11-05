"""Capped accounting windows inside ONE original dispatcher/token/Worker scope.

This is the original-contract alternative to unproved reauthentication carry.
It never creates child RequestPlans, copies next-key, renews a token, changes
authorization, or increases an existing Parent budget. Full-plan admission is
still required separately; each physical window is capped at20 including auth.
"""
from copy import deepcopy
from datetime import datetime,timezone
import json,os,time
from pathlib import Path
from weakref import WeakKeyDictionary
from zoneinfo import ZoneInfo
import httpx

from app.services.current_scoped_source_dispatch import CurrentScopedDispatcher
from app.services.sealed_source_transport import SealedSourceTransport
from app.services.sealed_fresh_dispatch import consume_bound_result
from app.services.unified_snapshot_contract import digest

CONTRACT='same-session-market-physical-windows-v1'
_CLAIMED=WeakKeyDictionary()


class SameSessionWindows(httpx.AsyncBaseTransport):
    def __init__(self,transport,*,maximum=20,expires_monotonic=None):
        from app.services.kiwoom_global_lane import GlobalKiwoomLane
        if (type(transport) is not SealedSourceTransport or type(transport.dispatcher) is not CurrentScopedDispatcher
                or type(transport.dispatcher._account_pacer) is not GlobalKiwoomLane
                or type(maximum)is not int or not 1<=maximum<=20):
            raise ValueError('market_window_original_dispatch_and_cap_required')
        self.transport=transport;self.run=transport.dispatcher
        self.run._require_parent()
        if self.run in _CLAIMED or self.run.used or self.run.physical_attempts:
            raise ValueError('market_window_new_one_use_dispatch_required')
        if any(not d.logical_request_id.startswith(('kr_market:','us_market:','kiwoom:auth'))
               or d.transient_retry_max!=0 for d in self.run.plan.descriptors):
            raise ValueError('market_window_original_market_plan_only')
        _CLAIMED[self.run]=True
        self.maximum=maximum;self.pid=os.getpid();self.plan_sha=self.run.plan.plan_sha256
        self.code=digest(Path(__file__).read_bytes().hex())
        self.expires=expires_monotonic if expires_monotonic is not None else time.monotonic()+600
        if not time.monotonic()<self.expires<=time.monotonic()+601:
            raise ValueError('market_window_bounded_resume_time')
        self.token=None;self.token_expires=None;self.base=0;self.windows=[];self.receipts={};self.busy=False;self.closed=False

    def _check(self):
        self.run._require_parent()
        if (self.pid!=os.getpid() or self.code!=digest(Path(__file__).read_bytes().hex())
                or self.closed or self.run.halted or self.run.plan.plan_sha256!=self.plan_sha
                or time.monotonic()>=self.expires):
            raise ValueError('market_window_scope_process_code_or_STOP_changed')
        if self.token is not None and self.run.credential_response is not self.token:
            raise ValueError('market_window_reauthentication_not_proven')
        if self.token_expires is not None and datetime.now(timezone.utc)>=self.token_expires:
            raise ValueError('market_window_credential_expired')
        for key,sha in self.receipts.items():
            consume_bound_result(root=self.run.root,plan=self.run.plan,logical_id=key,receipt_sha256=sha)

    def _checkpoint(self):
        count=self.run.physical_attempts-self.base
        if not 0<count<=self.maximum:raise ValueError('market_window_actual_physical_cap')
        self.windows.append(dict(first=self.base+1,last=self.run.physical_attempts,physical_attempts=count,
            session_scope='SAME_LIVE_DISPATCH_TOKEN_NOT_REAUTH',plan_sha256=self.plan_sha,
            receipt_bindings=deepcopy(self.receipts)))
        self.base=self.run.physical_attempts

    async def handle_async_request(self,request):
        if self.busy:raise ValueError('market_window_parallel_use_denied')
        self._check();self.busy=True
        try:
            if self.run.physical_attempts-self.base==self.maximum:self._checkpoint()
            before=set(self.run.results);ordinal=self.run.physical_attempts
            response=await self.transport.handle_async_request(request)
            self._check()
            if not 0<=self.run.physical_attempts-ordinal<=1:
                raise ValueError('market_window_one_physical_attempt_per_call')
            if self.run.physical_attempts-self.base>self.maximum:
                raise ValueError('market_window_actual_physical_cap')
            for key in set(self.run.results)-before:
                self.receipts[key]=self.run.results[key]['receipt_sha256']
            if self.token is None and self.run.credential_response is not None:
                # Original cached-token path, no renewal across windows. Validate
                # the original expiry without retaining/exporting token contents.
                token=json.loads(self.run.credential_response.content)
                expires=datetime.strptime(token['expires_dt'],'%Y%m%d%H%M%S').replace(tzinfo=ZoneInfo('Asia/Seoul'))
                if expires<=datetime.now(timezone.utc):raise ValueError('market_window_credential_expired')
                self.token=self.run.credential_response
                self.token_expires=expires
            return response
        except BaseException:
            self.run.halted=True;self.closed=True
            raise
        finally:self.busy=False

    def finish(self):
        self._check()
        for d in self.run.plan.descriptors:
            if d.logical_request_id not in self.run.used:
                # Only original response binding can prove an unselected tail.
                self.run.skip_unselected(d.logical_request_id)
        if self.run.physical_attempts>self.base:self._checkpoint()
        self.closed=True
        return dict(contract=CONTRACT,windows=deepcopy(self.windows),actual_physical=self.run.physical_attempts,
            original_plan_sha256=self.plan_sha,no_reauthentication=True,
            Parent='NOT_ISSUED',scope='SOURCE_COMPONENTS_ONLY')

    async def aclose(self):pass


def cold_window_readback(*,plan,root,record):
    """Independent original slot replay. It cannot mint a live Parent."""
    from app.services.current_scoped_source_dispatch import CurrentScopedRequestPlan
    from app.services.current_scoped_source_results import _read,_root
    plan=CurrentScopedRequestPlan.model_validate(plan);root=_root(root)
    if record.get('contract')!=CONTRACT or record.get('original_plan_sha256')!=plan.plan_sha256:
        raise ValueError('market_window_cold_plan')
    last=0
    for row in record['windows']:
        if (row['first']!=last+1 or row['last']-row['first']+1!=row['physical_attempts']
                or not 1<=row['physical_attempts']<=20 or row['plan_sha256']!=plan.plan_sha256):
            raise ValueError('market_window_cold_physical_gap_or_cap')
        last=row['last']
    if last!=record['actual_physical']:
        raise ValueError('market_window_cold_total')
    receipts=record['windows'][-1]['receipt_bindings']
    pages={}
    ordinals=[]
    for number in range(1,last+1):
        r=json.loads(_read(root,f'physical/attempt-{number:04d}.json'))
        if r['ordinal']!=number or r.get('http_status')!=200:
            raise ValueError('market_window_cold_physical_receipt')
        ordinals.append(r['logical_request_id'])
    if len(set(ordinals))!=len(ordinals) or set(ordinals)!=set(receipts):
        raise ValueError('market_window_cold_duplicate_or_missing_slot')
    for key,sha in receipts.items():
        consume_bound_result(root=root,plan=plan,logical_id=key,receipt_sha256=sha)
        d=next(d for d in plan.descriptors if d.logical_request_id==key)
        if d.endpoint_operation=='ka10066':pages.setdefault(d.group_id,[]).append(d.page_ordinal)
    for group,values in pages.items():
        if sorted(values)!=list(range(1,len(values)+1)):
            raise ValueError('market_window_cold_page_chain')
        descriptors=[d for d in plan.descriptors if d.group_id==group and d.logical_request_id in receipts]
        final=json.loads(_read(root,'receipts/'+max(descriptors,key=lambda d:d.page_ordinal).logical_request_id+'/final.json'))
        if final['response_headers'].get('cont-yn')!='N':
            raise ValueError('market_window_cold_continuation_incomplete')
    return dict(status='ORIGINAL_SEALED_SLOT_COLD_PASS_NOT_PARENT',
        pages={g:len(v) for g,v in pages.items()},physical=last,reauthentication_proven=False,
        carry_mode='SAME_ORIGINAL_DISPATCH_TOKEN_AND_PROCESS',MarketParent='NOT_ISSUED',native=False)
