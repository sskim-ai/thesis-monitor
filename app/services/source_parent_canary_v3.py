"""Opt-in trusted Source canary policy, not an OS sandbox or a new Source Owner.

The SQLite boundary protects the original audited query path, not arbitrary
native code in its trusted parent. The isolated Source child remains unchanged.
"""
from dataclasses import dataclass
import hashlib
import math
import os
from pathlib import Path
from weakref import WeakKeyDictionary

CONTRACT = 'official-manual-scoped-source-parent-v3'
DB_POLICY = 'TRUSTED_ORIGINAL_SQLITE_READONLY_V3'
GIB = 1024**3
_READS = WeakKeyDictionary()


def require(value, code):
    if not value:
        raise ValueError('official_v3_' + code)


@dataclass(frozen=True)
class CanaryScope:
    markets: tuple[str, ...] = ('kr', 'us')
    kr_including_auth: int = 20
    us_http: int = 12
    total_http: int = 20

    def validate(self):
        require(self.markets in (('kr',), ('kr', 'us')), 'market_scope')
        require(type(self.kr_including_auth) is int and self.kr_including_auth == 20
                and type(self.total_http) is int and self.total_http == 20
                and type(self.us_http) is int
                and self.us_http == (12 if 'us' in self.markets else 0), 'budget_scope')
        return self

    def public(self):
        self.validate()
        return dict(markets=list(self.markets), provider='kiwoom',
            KR_plus_auth_max=self.kr_including_auth, US_max=self.us_http,
            combined_max=self.total_http, retries=0, role='adjusted_daily', rows=1000,
            DB_sessions=1, SELECT=5, models=0, delivery='NO_SEND')


def validate_plan(handle, scope):
    from app.services import manual_scoped_source_runtime as manual
    scope.validate()
    _, wire, _ = manual.inputs(handle)
    reads = wire['stock_reads']
    require(len(reads) == len(scope.markets) and {r.market for r in reads} == set(scope.markets)
            and all(r.role == 'adjusted_daily' and r.count == 1000 for r in reads), 'D1000_scope')
    counts = {'kr': 0, 'us': 0, 'auth': 0}
    for d in wire['request_plan'].descriptors:
        require(d.provider == 'kiwoom' and d.transient_retry_max == 0
                and d.max_transport_attempts == 1, 'original_provider_no_retry')
        if d.endpoint_operation == 'credential_exchange':
            counts['auth'] += 1
        else:
            require(d.market in scope.markets and d.endpoint_operation ==
                    ('ka10081' if d.market == 'kr' else 'usa06012'), 'original_D_route')
            counts[d.market] += 1
    require(counts['auth'] == 1 and counts['kr'] + counts['auth'] <= scope.kr_including_auth
            and counts['us'] <= scope.us_http and sum(counts.values()) <= scope.total_http,
            'frozen_plan_exceeds_grant')
    return dict(scope=scope.public(), planned=counts, planned_total=sum(counts.values()))


def check_space(paths, scope):
    scope.validate()
    # Original response cap 4 MiB; raw + normalization + two replays/cold and
    # bounded IPC/logs are conservatively budgeted at 512 MiB for <=20 attempts.
    from app.services.current_scoped_source_dispatch import MAX_RESPONSE_BYTES
    require(MAX_RESPONSE_BYTES == 4*1024**2, 'response_bound_changed')
    peak, reserve, margin = 512*1024**2, 4*GIB, GIB
    needed = max(6*GIB, peak+reserve+margin)
    rows = []
    for value in paths:
        p = Path(value)
        require(p.is_absolute() and p.is_dir() and not any(x.is_symlink() for x in (p,*p.parents)),
                'writer_path')
        s = os.statvfs(p); free = s.f_bavail*s.f_frsize
        require(free >= needed, 'writer_headroom')
        rows.append(dict(path=str(p),device=p.stat().st_dev,free_bytes=free,
            expected_peak_bytes=peak,reserve_bytes=reserve,margin_bytes=margin,required_bytes=needed))
    require(bool(rows), 'writer_missing')
    return rows


def validate_activation(*, activation, state, anchor, lock_identity, current_boot, implementation_sha):
    from app.services.unified_snapshot_contract import digest
    require(set(activation) == {'protocol','generation','boot_identity','implementation_sha256'}, 'activation_shape')
    require(activation == anchor['activation'] and digest(activation) == anchor['official_digest'],
            'activation_release_rebase_required')
    require(activation['protocol'] == 'kiwoom-host-global-lane-v1'
            and activation['implementation_sha256'] == implementation_sha
            and activation['boot_identity'] == current_boot, 'activation_security_identity')
    require(list(lock_identity) == anchor['lock_identity'], 'lock_identity')
    require(set(state) == {'protocol','generation','boot_identity','last_end','in_flight','halted','sequence','pid'},
            'state_shape')
    require(all(state[k] == activation[k] for k in ('protocol','generation','boot_identity')), 'state_epoch')
    require(state['halted'] is False and state['in_flight'] is False, 'stop_or_inflight')
    require(type(state['sequence']) is int and state['sequence'] >= 0
            and type(state['pid']) is int and state['pid'] >= 0
            and (state['last_end'] is None or (type(state['last_end']) in (int,float)
                 and math.isfinite(state['last_end']) and state['last_end'] >= 0)), 'state_values')
    return dict(status='RELEASE_ANCHOR_MATCH_ORIGINAL_LANE_STILL_REQUIRED',
                sequence_observed=state['sequence'])


def admit_parent(manifest, cli):
    import importlib
    modules = tuple(importlib.import_module(n) for n in cli.MODULES)
    lane, maintenance, participant = modules[:3]
    require(str(lane.DEFAULT_ROOT) == manifest['lane_root'], 'original_lane_root')
    maintenance.assert_operation_allowed()
    before = cli.lane_snapshot(lane.DEFAULT_ROOT)
    session = participant.ParticipatingSession(modules=modules, caller_kind='CLI')
    try:
        a = session.attestation()
        proof = validate_activation(activation=a['activation'],state=lane._read(lane.DEFAULT_ROOT/'state.json'),
            anchor=manifest['activation_anchor'],lock_identity=session._lane.lock_identity,
            current_boot=a['boot_identity'],implementation_sha=cli.pin(lane.__file__)['sha256'])
        require(before == cli.lane_snapshot(lane.DEFAULT_ROOT), 'lane_changed_during_admission')
        return session, dict(parent=a,release=proof,lane_before=before,lane_after=before,
            physical_slots=0,credentials_read=False,database_sessions=0,
            account_exclusivity='REQUIRES_CURRENT_OPERATOR_CONFIRMATION',
            effective_child_isolation='NOT_RUN_UNTIL_ORIGINAL_WORKER')
    except BaseException:
        session.close_admission()
        raise


class TrustedReadonlyRegistration:
    __slots__ = ('__weakref__',)


def _identity(database):
    p = Path(database)
    require(p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)), 'database_plain_path')
    s = p.stat()
    require(p.is_file() and s.st_nlink == 1 and s.st_uid == os.getuid(), 'database_identity')
    return p, (s.st_dev,s.st_ino)


def admit_readonly(database, approval, *, enabled=False):
    from app.services import prospective_class_c_owner as owner
    from app.services.official_registered_source_runtime import registered_subjects
    require(enabled is True, 'default_off')
    decision = owner._approval(approval)
    require(tuple(sorted(decision.subjects)) == registered_subjects(), 'registered22_scope')
    p, identity = _identity(database)
    h = TrustedReadonlyRegistration()
    _READS[h] = dict(database=p,identity=identity,approval=approval,pid=os.getpid(),reads=0,
        source=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    return h


def require_readonly(handle, database, approval, *, consume=False):
    from app.services import prospective_class_c_owner as owner
    require(type(handle) is TrustedReadonlyRegistration and handle in _READS, 'live_readonly_handle')
    s = _READS[handle]
    require(s['pid'] == os.getpid() and s['source'] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
            and s['approval'] is approval, 'readonly_process_code_approval')
    owner._approval(approval)
    p, identity = _identity(database)
    require(p == s['database'] and identity == s['identity'], 'readonly_database_changed')
    if consume:
        require(s['reads'] == 0, 'readonly_session_already_consumed')
        s['reads'] = 1
    else:
        require(s['reads'] == 1, 'readonly_session_not_consumed')
    return identity


def retire_readonly(handle):
    if type(handle) is TrustedReadonlyRegistration:
        _READS.pop(handle, None)


def confirm_grant(manifest_sha, invocation, configuration, scope):
    from datetime import datetime, timedelta, timezone
    import sys
    from app.services.prospective_class_c_owner import ApprovalDecision, record_backend_approval
    from app.services.official_registered_source_runtime import registered_subjects
    require(sys.stdin.isatty() and sys.stdout.isatty(), 'owner_terminal_required')
    public = scope.public()
    phrase = f"APPROVE {invocation} {manifest_sha} {configuration['execution_plan_sha256']} NO_CONCURRENT_USE"
    print('One current execution only; no prior preflight/approval is reused.')
    print(public)
    print('Database:', configuration['database'])
    print('US requests are', 'explicitly included' if scope.us_http else 'NOT AUTHORIZED')
    print('No models, sending, orders, services, DB writes, or automatic retry.')
    print(phrase, flush=True)
    require(input().strip() == phrase, 'scope_confirmation_denied')
    now = datetime.now(timezone.utc)
    return record_backend_approval(ApprovalDecision(event_id=invocation,
        user_message_sha256=hashlib.sha256(phrase.encode()).hexdigest(),approved=True,
        effective_at=now,expires_at=now+timedelta(minutes=55),subjects=registered_subjects()))
