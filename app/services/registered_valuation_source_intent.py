"""Default-off capture intent; identity metadata is not a financial-use grant."""
from datetime import datetime,timedelta,timezone
import fcntl
import os
from pathlib import Path
from weakref import WeakKeyDictionary

from app.services import prospective_class_c_owner as registration
from app.services.vnext_research_store import digest,plain

PURPOSE='REGISTERED_VALUATION_SOURCE_ONLY_V1'
_LIVE=WeakKeyDictionary()


class RegisteredValuationSourceIntent:
    __slots__=('__weakref__',)


def code_pins():
    root=Path(__file__).resolve().parents[2]
    names=('app/services/registered_valuation_source_intent.py',
        'app/services/prospective_class_c_owner.py','app/services/onboarding_readiness_service.py',
        'app/services/public_capture_storage.py','app/services/vnext_public_capture.py',
        'app/services/vnext_legacy_reuse.py','app/services/provider_native_valuation_acquisition.py',
        'app/services/provider_native_valuation_snapshot.py',
        'app/services/registered_valuation_source_parent.py','app/services/kis_estimate_source_contract.py',
        'app/services/pending_source_parent.py','app/services/market_component_execution.py',
        'app/services/current_scoped_source_dispatch.py','scripts/current_scoped_source_worker.py')
    return {str(root/n):digest((root/n).read_bytes()) for n in names}


def issue_intent(*,approval,capture,generation_id,policy,enabled=False):
    if enabled is not True:raise ValueError('valuation_source_explicit_enable_required')
    discovery,receipt=registration.issue_identity_discovery_owner(approval=approval,capture=capture,
        generation_id=generation_id,policy=policy)
    decision=registration._approval(approval)
    cutoff=datetime.now(timezone.utc)
    handle=RegisteredValuationSourceIntent()
    identities={t:registration.require_identity_discovery(discovery,generation_id=generation_id,ticker=t)
        for t in decision.subjects}
    _LIVE[handle]=dict(pid=os.getpid(),approval=approval,discovery=discovery,identities=identities,
        generation_id=generation_id,pins=code_pins(),claims={},expires=min(decision.expires_at,cutoff+timedelta(minutes=30)))
    return handle,dict(contract=PURPOSE,generation_id=generation_id,
        registration_receipt_sha256=digest(receipt),cutoff=cutoff.isoformat(),
        economic_use=False,native_use=False,production=False,send=False)


def require_intent(handle,*,generation_id,provider,subjects):
    if type(handle) is not RegisteredValuationSourceIntent or handle not in _LIVE:
        raise ValueError('valuation_source_live_intent_required')
    s=_LIVE[handle];registration._approval(s['approval'])
    if (s['pid']!=os.getpid() or s['generation_id']!=generation_id
            or datetime.now(timezone.utc)>=s['expires'] or s['pins']!=code_pins()
            or provider not in ('kiwoom','finnhub','kis') or not subjects or len(set(subjects))!=len(subjects)):
        raise ValueError('valuation_source_process_generation_expiry_or_code')
    result={}
    for ticker in subjects:
        original=registration.require_identity_discovery(s['discovery'],generation_id=generation_id,ticker=ticker)
        if original!=s['identities'].get(ticker):raise ValueError('valuation_source_registration_changed')
        if (provider=='finnhub' and original['country']!='US'
                or provider in ('kiwoom','kis') and original['country']!='KR'):
            raise ValueError('valuation_source_provider_country')
        result[ticker]=original
    return result


def revoke_intent(handle):
    if type(handle) is not RegisteredValuationSourceIntent or handle not in _LIVE:
        raise ValueError('valuation_source_live_intent_required')
    registration.revoke_identity_discovery(_LIVE[handle]['discovery'])
    del _LIVE[handle]


def claim_provider(handle,*,generation_id,provider,subjects,plan_sha256):
    require_intent(handle,generation_id=generation_id,provider=provider,subjects=subjects)
    s=_LIVE[handle]
    if provider in s['claims']:raise ValueError('valuation_source_provider_already_claimed')
    s['claims'][provider]=plan_sha256


class ProviderAccountLock:
    """Single host/account capture lock; remote concurrency is not observable.

    It never resets Provider STOP or claims participation by unknown clients.
    Kiwoom must additionally retain its original GlobalKiwoomLane.
    """
    def __init__(self,provider,credential,*,root='/private/tmp/thesis-monitor-provider-capture-locks-v1'):
        if provider not in ('finnhub','kis') or not isinstance(credential,str) or not credential:
            raise ValueError('provider_account_lock_scope')
        path=plain(root);path.mkdir(mode=0o700,parents=True,exist_ok=True)
        if path.stat().st_uid!=os.getuid() or path.stat().st_mode&0o077:
            raise ValueError('provider_account_lock_private_root')
        name=digest((provider+':'+credential).encode())
        self.fd=os.open(plain(path/name),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        try:
            stat=os.fstat(self.fd)
            if stat.st_nlink!=1 or stat.st_uid!=os.getuid():raise ValueError('provider_account_lock_identity')
            fcntl.flock(self.fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BaseException:
            os.close(self.fd);raise
        self.pid=os.getpid()

    def require(self):
        if self.fd is None or self.pid!=os.getpid():raise ValueError('provider_account_lock_not_owned')
        fcntl.flock(self.fd,fcntl.LOCK_EX|fcntl.LOCK_NB)

    def close(self):
        if self.fd is not None:
            fcntl.flock(self.fd,fcntl.LOCK_UN);os.close(self.fd);self.fd=None
