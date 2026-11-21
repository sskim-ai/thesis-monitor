"""Disabled-by-default single-run entrypoint; no implicit legacy adapter fallback."""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager, ExitStack
import fcntl
import json
import os
from pathlib import Path
import pwd
import re
import stat
import subprocess
import tempfile
import time
from typing import Literal

from pydantic import Field

from app.config import get_settings
from app.services.unified_market_run import KST, RunConfiguration, UnifiedMarketRun
from app.services.unified_run_artifacts import SECRET_KEY
from app.services.unified_snapshot_contract import ContractModel, digest
from app.services.production_source_configuration import ProtocolFile
from app.services.model_timeout_retry import B2_PER_TICKER_ONE_RETRY_V1, B2_US2_DIAGNOSTIC_V1, B2_SR5_DIAGNOSTIC_V1


LOCAL_BASIS = 'LOCAL_OPERATOR_SCHEDULED_NO_SEND'
LOCAL_CAPS = {
    'us': dict(kiwoom=552, sec_edgar=86, finnhub=28, google_news_rss=14,
        fred=13, krx_night_futures=7, opendart=6, eia=3, ecos=1),
    'kr': dict(kiwoom=190, kis=85, opendart=48, naver_news=8, ecos=1),
}
ROOT = Path(__file__).resolve().parents[2]
US2_SUBJECTS = ('GOOGL','MU')
US2_CAPS = dict(kiwoom=120,sec_edgar=8,finnhub=4,google_news_rss=2,
    fred=13,krx_night_futures=7,opendart=0,eia=3,ecos=1)
SR5_SUBJECTS = ('CRCL','HUT','SKHY','TSM','WULF')
SR5_CAPS = dict(kiwoom=228,sec_edgar=40,finnhub=10,google_news_rss=5,
    fred=13,krx_night_futures=7,opendart=6,eia=3,ecos=1)
US_FULL_20261121_SLOTS = {
    'us-20261121-0610a1b2': '2026-11-21T06:10:00+09:00',
    'us-20261121-0810c3d4': '2026-11-21T08:10:00+09:00',
    'us-20261121-c28d7e1f': '2026-11-21T11:00:00+09:00',
    'us-20261121-c29a6b3d': '2026-11-21T11:40:00+09:00',
    'us-20261121-c31a9f6e': '2026-11-21T13:25:00+09:00',
    'us-20261121-c32b8e4d': '2026-11-21T15:20:00+09:00',
}


def _us_full_one_shot_window(tag):
    start = US_FULL_20261121_SLOTS.get(tag)
    if start is None:
        return None
    start = datetime.fromisoformat(start)
    return start, start + timedelta(minutes=10)


def _one_shot_deadline(tag):
    window = _us_full_one_shot_window(tag)
    return (window[0] + timedelta(hours=4, minutes=30) if window else
            datetime.fromisoformat('2026-11-21T00:00:00+09:00'))


def one_shot_scope(market, tag):
    if tag is None:
        return False
    if market == 'us' and tag in US_FULL_20261121_SLOTS:
        return False
    match = re.fullmatch(r'(us|us2|us5|kr)-20261120-[a-f0-9]{8}',tag)
    if match is None or ('us' if match[1] in ('us2','us5') else match[1]) != market:
        raise ValueError('local_one_shot_tag_scope_invalid')
    return match[1] in ('us2','us5')


class LocalScheduleConfiguration(ContractModel):
    """Operator-managed local settings, not a signed grant or serialized Owner."""
    basis: Literal['LOCAL_OPERATOR_SCHEDULED_NO_SEND'] = LOCAL_BASIS
    enabled: bool = Field(default=False, strict=True)
    mode: Literal['LIVE_NO_SEND'] = 'LIVE_NO_SEND'
    market: Literal['us', 'kr']
    code_commit: str = Field(pattern=r'^[a-f0-9]{40}$')
    run_root: str
    settings_env_file: str
    shared_lease_path: str
    source_configuration: ProtocolFile
    model_binding: ProtocolFile
    endpoint_rules: ProtocolFile
    auxiliary_issuer: ProtocolFile | None = None


def _absolute_local_path(value):
    path = Path(value)
    if not path.is_absolute() or '..' in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('local_schedule_absolute_nonsymlink_path_required')
    return path


def read_local_configuration(path, market):
    path = _absolute_local_path(path)
    st = path.stat()
    if not path.is_file() or st.st_uid != os.getuid() or st.st_mode & 0o077 or st.st_size > 65536:
        raise ValueError('local_schedule_operator_private_configuration_required')
    config = LocalScheduleConfiguration.model_validate_json(path.read_bytes())
    if market != config.market:
        raise ValueError('local_schedule_market_scope_mismatch')
    for value in (config.run_root, config.settings_env_file, config.shared_lease_path):
        _absolute_local_path(value)
    return config


@contextmanager
def _local_lock(path, *, existing=False):
    flags = os.O_RDONLY if existing else os.O_RDWR | os.O_CREAT
    fd = os.open(path, flags | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def _local_model_runtime(execution):
    """Private generation scratch outside Git, independent of launchd HOME."""
    from app.services.research_artifact_budget import FREE_GUARD

    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,159}', execution):
        raise ValueError('local_model_runtime_generation_invalid')
    uid = os.getuid()
    home = _absolute_local_path(pwd.getpwuid(uid).pw_dir)
    if not home.is_dir() or home.stat().st_uid != uid:
        raise ValueError('local_model_runtime_os_home_owner_required')
    base = _absolute_local_path(str(home/'Library/Application Support/ThesisMonitor/private-model-runtime'))
    if any((p/'.git').exists() for p in (base.resolve(), *base.resolve().parents)):
        raise ValueError('production_model_input_root_inside_repository')
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    info = base.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != uid or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError('local_model_runtime_private_directory_required')
    fs = os.statvfs(base)
    if fs.f_bavail*fs.f_frsize < FREE_GUARD:
        raise ValueError('local_model_runtime_free_space_guard')
    runtime = Path(tempfile.mkdtemp(prefix=execution+'-', dir=base))
    info = runtime.lstat()
    if (runtime.is_symlink() or info.st_uid != uid or stat.S_IMODE(info.st_mode) != 0o700
            or any((p/'.git').exists() for p in (runtime.resolve(), *runtime.resolve().parents))):
        runtime.rmdir()
        raise ValueError('local_model_runtime_private_directory_required')
    return runtime


def _record_local_failure(directory, exc, *, config, session, generation=None, before_owner_cleanup=False):
    """Keep the first bounded code-only diagnostic; cleanup cannot overwrite it."""
    from app.services.unified_run_artifacts import durable_json, sha256_bytes

    try:
        frames = []
        source_frame = False
        trace = exc.__traceback__
        while trace is not None:
            code = trace.tb_frame.f_code
            filename = Path(code.co_filename).resolve()
            if filename.is_relative_to(ROOT) and filename.relative_to(ROOT).parts[0] in ('app', 'scripts'):
                frames.append(dict(basename=filename.name, function=code.co_name, line=trace.tb_lineno))
                source_frame |= filename.name == 'production_source_backend.py' and code.co_name == 'prepare_registered'
            trace = trace.tb_next
        allowed_codes = {
            'production_registered_selected_plan_required', 'production_source_seal_changed',
            'production_source_systemic_stop',
            'selected_whole_original_stock_incomplete', 'selected_registration_frozen_receipt_drift',
            'selected_original_coverage_required_cells_incomplete', 'selected_forward_coverage_context_drift',
            'selected_original_issuer_projection_denied', 'scoped_research_registered_source_coverage',
            'scoped_research_inconsistent_stock_cutoffs',
        }
        error_code = exc.args[0] if len(exc.args) == 1 and type(exc.args[0]) is str else None
        stage = 'SOURCE_PREPARATION_OR_COLLECTION' if source_frame else 'LOCAL_REGISTERED_CYCLE'
        marker = directory/'source-time-result.json'
        if source_frame and marker.is_file() and marker.stat().st_size <= 4096:
            if json.loads(marker.read_bytes()).get('status') == 'COLLECTOR_RETURNED_REQUIRES_SOURCE_ADMISSION':
                stage = 'SOURCE_POST_COLLECTION'
        seal = directory/'source-seal.json'
        seal_sha = sha256_bytes(seal.read_bytes()) if seal.is_file() and seal.stat().st_size <= 65536 else None
        path = directory/'failure-diagnostic.json'
        durable_json(path, dict(exception_class=type(exc).__name__,
            last_application_frame=frames[-1] if frames else None, application_frames=frames[-8:],
            stable_error_code=error_code if error_code in allowed_codes else None, stage=stage, NO_SEND=True,
            market=config.market, target_session=session, source_generation=generation,
            code_commit=config.code_commit, runtime_module_sha256=sha256_bytes(Path(__file__).read_bytes()),
            source_seal_file_sha256=seal_sha, recorded_before_owner_cleanup=before_owner_cleanup), exclusive=True)
        body = path.read_bytes()
        durable_json(directory/'failure-diagnostic-sha256.json', dict(
            file=path.name, bytes=len(body), sha256=sha256_bytes(body)), exclusive=True)
    except Exception:
        pass  # Diagnostic failure must not replace the original STOP.


async def _local_registered_cycle(config, directory, session, *, one_shot_tag=None):
    from app.config import Settings
    from app.macro.providers.market import MARKET_SYMBOLS
    from app.services import prospective_class_c_owner as registration
    from app.services.codex_runtime_binding import binding_from_json, parent_environment, validate_binding
    from app.services.kiwoom_global_lane import configured_lane
    from app.services.production_source_configuration import ProductionSourceConfiguration
    from app.services.production_source_context import POLICY, credential_binding, inspect_native
    from app.services.selected_run_lifecycle import SelectedRunLedger
    from app.services.selected_source_context import freeze_registered_child
    from app.services.selected_source_plan import SelectedConsumerPolicy, SelectedRequestPlan, request_budget
    from app.services.selected_source_registration import capture_approved_markets, database_target
    from app.services.unified_run_artifacts import durable_json, sha256_bytes
    from app.services.unified_stock_acquisition import UNIVERSE
    from app.services.vnext_execution_profile import SOL_HIGH_V1

    market = config.market
    diagnostic = one_shot_scope(market,one_shot_tag)
    sr5 = bool(one_shot_tag and one_shot_tag.startswith('us5-'))
    subjects = SR5_SUBJECTS if sr5 else US2_SUBJECTS if diagnostic else UNIVERSE[market]
    caps = SR5_CAPS if sr5 else US2_CAPS if diagnostic else LOCAL_CAPS[market]
    max_models = 15 if sr5 else 8 if diagnostic else 42 if market=='us' else 18
    retry_policy = B2_SR5_DIAGNOSTIC_V1 if sr5 else B2_US2_DIAGNOSTIC_V1 if diagnostic else B2_PER_TICKER_ONE_RETRY_V1 if market=='us' else None
    master = 'local-' + market + '-' + session
    if one_shot_tag is not None:
        master += '-once-' + one_shot_tag
    generation, execution = master+'-source', master+'-consumer'
    runtime = _local_model_runtime(execution)
    durable_json(directory/'model-runtime-preflight.json', dict(
        execution=execution, runtime_root=str(runtime), uid=runtime.stat().st_uid,
        mode=stat.S_IMODE(runtime.stat().st_mode), git_markers=[],
        journal_path=str(runtime/'invocation-ledger'/execution/'events.jsonl'),
        artifact_roots={str(directory):'source', str(directory/'results'):'result', str(runtime):'scratch'},
        before_registration_and_financial_HTTP=True), exclusive=True)
    source_config = ProductionSourceConfiguration.model_validate_json(config.source_configuration.read())
    binding = json.loads(config.model_binding.read())
    bound = binding_from_json(binding)
    # Use the reviewed CLI's existing environment, not launchd's default PATH.
    # Keep override variables visible so validate_binding can still reject them.
    reviewed = parent_environment(bound)
    for key in ('HOME', 'PATH', 'CODEX_HOME'):
        if key in reviewed:
            os.environ[key] = reviewed[key]
        elif key == 'CODEX_HOME':
            os.environ.pop(key, None)
    os.environ['KIWOOM_GLOBAL_LANE_REQUIRED'] = '1'
    validate_binding(bound, str(bound.executable), profile=SOL_HIGH_V1)
    endpoints = json.loads(config.endpoint_rules.read())
    if set(endpoints) != set(LOCAL_CAPS[market]):
        raise ValueError('local_schedule_original_provider_scope_required')
    settings = Settings(_env_file=config.settings_env_file, notification_dry_run=True,
        unified_snapshot_enabled=True, unified_snapshot_adapter_version='production-v1',
        unified_snapshot_runtime_contract='unified-query-time-snapshot-v2',
        unified_snapshot_live_delivery_authorized=False, data_dir=str(directory/'results'),
        us_price_structure_v3_enabled=True, kr_price_structure_v3_enabled=True)
    runtime_db_root = Path(config.settings_env_file).parent
    target, device, inode = database_target(settings, runtime_directory=runtime_db_root)
    if str(target) != source_config.database_path:
        raise ValueError('local_schedule_active_database_mismatch')
    lane = configured_lane()
    if lane is None:
        raise ValueError('local_schedule_existing_global_lane_required')
    # Read under the original lock; never recover/reset an unavailable Lane.
    with os.fdopen(lane._open(), 'rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lane._state()
    source_root = directory/'source'
    protocols = source_config.seal_protocols(source_root, market)
    native = inspect_native(source_config, source_root, settings_env_file=config.settings_env_file, settings=settings)
    credentials = credential_binding(settings, market)
    now = datetime.now(timezone.utc)
    children = {m: dict(generation=generation if m == market else master+'-reference',
        execution_generation=execution, subjects=list(UNIVERSE[m]))
        for m in (('us',) if market == 'us' else ('kr', 'us'))}
    approval = ledger = None
    owners = {}
    try:
        approval = registration.record_backend_approval(registration.ApprovalDecision(
            event_id=master, approved=True, user_message_sha256=digest(config.model_dump(mode='json')),
            effective_at=now, expires_at=min(now+timedelta(hours=4, minutes=30),
                _one_shot_deadline(one_shot_tag)) if one_shot_tag else now+timedelta(hours=4,minutes=30),
            subjects=tuple(t for child in children.values() for t in child['subjects']),
            **(dict(routine_us_no_send_source_seconds=1800) if market == 'us' else {})))
        ledger = SelectedRunLedger(path=directory/'campaign.jsonl', approval=approval, master_id=master,
            children=children, provider_caps=caps, max_http=sum(caps.values()),
            max_models=max_models, staged_markets=True,
            b2_retry_policy=retry_policy, wallclock_seconds_max=16200,
            database_identity=dict(path=str(target), device=device, inode=inode),
            capture_max_private_export_bytes=64*1024**2,
            runtime_cap=dict(endpoints=endpoints, market_subjects={'us':[*MARKET_SYMBOLS,*(('000660',) if not diagnostic or 'SKHY' in subjects else ())], 'kr':[]},
                stop_on_first_external_failure=True,
                **(dict(optional_news_429='SELECTED_US_OPTIONAL_NEWS_429_V1') if market == 'us' else {})))
        _, owners, _ = capture_approved_markets(settings=settings, runtime_directory=runtime_db_root,
            approval=approval, generations={market:generation}, policy=POLICY, ledger=ledger,
            enabled=True, monitoring_only=True, subject_limits={market:len(subjects)},
            priority_subjects={market:subjects}, **(dict(source_subjects={market:subjects}) if diagnostic else {}))
        _, receipt = registration._state(owners[market])
        if receipt['calendar']['target'] != session or set(receipt['bindings']) != set(subjects):
            raise ValueError('local_schedule_completed_session_or_roster_drift')
        listing = json.loads((source_root/'static/kr-list-routing.json').read_bytes())['list'] if market == 'kr' else []
        official = json.loads((source_root/'static/official-security-identity.json').read_bytes())
        auxiliary = (dict(security=json.loads(config.auxiliary_issuer.read()), official_identity_sha256=digest(official))
            if market == 'us' and 'SKHY' in subjects and config.auxiliary_issuer else None)
        frozen, compiler, kis, private_seed = freeze_registered_child(registration_owner=owners[market],
            policy=POLICY, code_sha=config.code_commit, native=native, native_owner_root=source_config.native_owner_root,
            config_identities={p:digest(v) for p,v in credentials.items()},
            configured_kr_pages=settings.kiwoom_rest_max_pages, listing_rows=listing,
            kis_static_hashes={n:p.sha256 for n,p in source_config.kis_protocols.items()},
            completed_close_documentation=(dict(path='static/completed-close-documentation.json',
                sha256=source_config.completed_close.sha256) if market == 'us' else None),
            consumer_policy=SelectedConsumerPolicy(), master_id=master,
            ohlcv_source_url=settings.ohlcv_base_url.rstrip('/')+'/ohlcv', run_ledger=ledger, enabled=True,
            include_kr_stock_flow=market == 'kr', kr_stock_chart_v3=market == 'kr',
            us_runtime_settings=settings if market == 'us' else None, issuer_auxiliary=auxiliary)
        plan = SelectedRequestPlan.model_validate(frozen['plan'])
        if market == 'kr':
            from app.services.selected_kis_sources import validate_plan, require_persisted_plan
            if kis is None or digest(kis) != plan.kis_plan_sha256 or validate_plan(kis) != plan.subjects:
                raise ValueError('local_schedule_kis_plan_binding_gap')
            durable_json(source_root/'kis-plan.json', kis, exclusive=True)
            require_persisted_plan(source_root, kis, plan)
        budget = request_budget({'plan':plan}, kis)
        if budget['total'] > ledger.identity['max_http'] or any(
                n > caps.get(p, 0) for p,n in budget['providers'].items()):
            raise ValueError('local_schedule_frozen_plan_exceeds_original_caps')
        frozen.update(protocol_inputs=protocols, private_export_limit_bytes=64*1024**2,
            available_evidence_policy='FIELD_LOCAL_DATED_USE_V1',
            protected_input_hashes={str(p.relative_to(source_root)):sha256_bytes(p.read_bytes())
                for p in (source_root/'static').rglob('*') if p.is_file()})
        durable_json(source_root/'production-frozen-source-plan.json', frozen, exclusive=True)
        ledger.bind_source_plan(market, plan)
        if diagnostic:
            financial_subjects=set(subjects)|({'000660'} if auxiliary else set())
            if (tuple(plan.subjects)!=subjects or tuple(compiler['stock'].subjects)!=subjects
                    or set(frozen['candidate']['financial_plans'])!=financial_subjects
                    or {d.subject for d in plan.descriptors if d.consumer_role.startswith('events:')}!=set(subjects)):
                raise ValueError('local_diagnostic_frozen_scope_before_HTTP')
            durable_json(directory/('us5-before-http.json' if sr5 else 'us2-before-http.json'),dict(subjects=list(subjects),
                stock_plan_sha256=digest(frozen['stock_plan']),request_plan_sha256=plan.plan_sha256,
                financial_subjects=sorted(frozen['candidate']['financial_plans']),
                actual_plan_budget=budget,defensive_caps=caps,max_HTTP=sum(caps.values()),
                expected_base_model_slots=11 if sr5 else 6,
                expected_B2_subjects=[t for t in subjects if not sr5 or t!='SKHY'],max_models=max_models,
                financial_HTTP_before_this_receipt=0),exclusive=True)
        source = dict(registration_owner=owners[market], run_ledger=ledger, root=source_root,
            frozen=frozen, compiler=compiler, kis_plan=kis, credentials=credentials, policy=POLICY,
            deadline=time.monotonic()+(1800 if market == 'us' else 600),
            execution_generation=execution, mixed_limitations=market == 'us', native_settings=settings)
        from app.services.research_artifact_budget import ResearchArtifactBudget, artifact_scope
        artifacts = ResearchArtifactBudget(roots={directory:'source', directory/'results':'result', runtime:'scratch'})
        model = dict(binding=binding, runtime_root=runtime,
            journal_path=runtime/'invocation-ledger'/execution/'events.jsonl', run_ledger=ledger,
            approved_max_invocations=ledger.identity['max_models'],
            b2_retry_policy=retry_policy,
            artifact_budget=artifacts)
        with artifact_scope(artifacts):
            return await run_registered(settings, source=source, model=model, mode='LIVE_NO_SEND',
                record_market_terminal=True,
                **(dict(routine_us_no_send_source_seconds=1800) if market == 'us' else {}))
    except BaseException as exc:
        _record_local_failure(directory, exc, config=config, session=session,
            generation=generation, before_owner_cleanup=True)
        raise
    finally:
        for owner in owners.values():
            registration.revoke_prospective_owner(owner)
        if ledger is not None and ledger.state()['state'] not in {'STOPPED_NO_SEND', 'RENDERED_NO_SEND'}:
            ledger.stop('LOCAL_SCHEDULE_CYCLE_CLOSED_NO_REPLAY')
        if approval is not None:
            registration.revoke_approval(approval)
        for values in credentials.values():
            values.clear()
        try:
            runtime.rmdir()
        except OSError:
            pass  # Keep nonempty current invocation evidence; retire only empty scratch.


def latest_one_shot_us_session(now, *, one_shot_tag=None):
    from app.services.market_session import us_market_session, _exchange_session_close, NEW_YORK, is_exchange_session_date

    window = _us_full_one_shot_window(one_shot_tag)
    local_date, target = ('2026-11-21', '2026-11-20') if window else ('2026-11-20', '2026-11-19')
    if now.utcoffset() is None or now.astimezone(KST).date().isoformat() != local_date:
        return None
    session = us_market_session(now).latest_completed_regular_session_date
    close = _exchange_session_close('XNYS', session, NEW_YORK)
    if session.isoformat() != target or not is_exchange_session_date('XNYS', session) or close is None or close > now:
        return None
    return session


def latest_one_shot_session(market,now, *, one_shot_tag=None):
    if market=='us':
        return latest_one_shot_us_session(now, one_shot_tag=one_shot_tag)
    from app.services.market_session import korea_market_session, _exchange_session_close, SEOUL, is_exchange_session_date
    if now.utcoffset() is None or now.astimezone(KST).date().isoformat()!='2026-11-20':
        return None
    session=korea_market_session(now).latest_completed_regular_session_date
    close=_exchange_session_close('XKRX',session,SEOUL)
    return session if (session.isoformat()=='2026-11-20' and is_exchange_session_date('XKRX',session)
        and close is not None and close<=now) else None


async def run_local_scheduled(configuration, market, *, now=None, one_shot_tag=None):
    """One market/session through original ports. This function installs nothing."""
    from app.services.unified_market_run import target_session
    from app.services.unified_run_artifacts import durable_json

    config = read_local_configuration(configuration, market)
    if not config.enabled:
        return dict(status='DISABLED', basis=LOCAL_BASIS, normal_messages_sent=False)
    now = now or datetime.now(KST)
    if now.utcoffset() is None:
        raise ValueError('local_schedule_timezone_required')
    window = None
    if one_shot_tag is not None:
        diagnostic=one_shot_scope(market,one_shot_tag)
        window = _us_full_one_shot_window(one_shot_tag)
        local_date = window[0].date().isoformat() if window else '2026-11-20'
        if now.astimezone(KST).date().isoformat() != local_date:
            return dict(status='NO_RUN', reason='ONE_SHOT_DATE_CLOSED', normal_messages_sent=False)
        if window and not window[0] <= now < window[1]:
            return dict(status='NO_RUN', reason='ONE_SHOT_SLOT_CLOSED', normal_messages_sent=False)
    else:
        diagnostic=False
    sr5=bool(one_shot_tag and one_shot_tag.startswith('us5-'))
    session = latest_one_shot_session(market,now,one_shot_tag=one_shot_tag) if one_shot_tag is not None else target_session(market, now)
    if session is None:
        return dict(status='NO_RUN', reason='SESSION_NOT_COMPLETED_OR_CLOSED', normal_messages_sent=False)
    if one_shot_tag is not None and session.isoformat() != ('2026-11-20' if window else '2026-11-19' if market=='us' else '2026-11-20'):
        return dict(status='NO_RUN', reason='ONE_SHOT_SESSION_MISMATCH', normal_messages_sent=False)
    head = subprocess.check_output(['/usr/bin/git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['/usr/bin/git', '-C', str(ROOT), 'status', '--porcelain', '--',
        'app', 'scripts', 'docs/operations'], text=True)
    if head != config.code_commit or dirty:
        raise ValueError('local_schedule_clean_code_pin_required')
    os.umask(0o077)
    relative = Path(market+'-'+session.isoformat()) if one_shot_tag is None else Path('one-shot')/local_date/one_shot_tag
    directory = _absolute_local_path(str(Path(config.run_root)/relative))
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    locks = ExitStack()
    try:
        locks.enter_context(_local_lock(config.shared_lease_path, existing=True))
        locks.enter_context(_local_lock(directory/'cycle.lock'))
    except BlockingIOError:
        locks.close()
        return dict(status='NO_RUN', reason='NO_RUN_LOCK_BUSY' if window else 'EXISTING_SHARED_OR_SESSION_LOCK_BUSY', normal_messages_sent=False)
    except BaseException:
        locks.close()
        raise
    with locks:
        # Same durable intent/terminal conventions as the canonical cycle.
        # Any interrupted/failed attempt is consumed, not a retry invitation.
        if any((directory/name).exists() for name in ('intent.json', 'terminal.json', 'campaign.jsonl', 'STOP')):
            return dict(status='NO_RUN', reason='SESSION_ALREADY_CONSUMED', normal_messages_sent=False)
        if one_shot_tag:
            once_intent = directory.parent/(one_shot_tag+'.intent.json' if window else 'intent.json')
            if once_intent.exists():
                return dict(status='NO_RUN', reason='ONE_SHOT_ALREADY_CONSUMED', normal_messages_sent=False)
            durable_json(once_intent, dict(one_shot_tag=one_shot_tag, session=session.isoformat(),
                date=local_date, code_commit=head, normal_messages_sent=False), exclusive=True)
        durable_json(directory/'intent.json', dict(basis=LOCAL_BASIS, market=market,
            session=session.isoformat(), code_commit=head, configuration_sha256=digest(config.model_dump(mode='json')),
            consent_basis='LOCAL_USER_MANAGED_CONFIGURATION_NOT_EXTERNAL_OR_DAILY_HUMAN_SIGNATURE',
            source_seconds=1800 if market == 'us' else 600, model_per_call_seconds=600,
            max_http=sum(SR5_CAPS.values()) if sr5 else sum(US2_CAPS.values()) if diagnostic else sum(LOCAL_CAPS[market].values()),
            max_models=15 if sr5 else 8 if diagnostic else 42 if market == 'us' else 18,
            b2_retry_policy=B2_SR5_DIAGNOSTIC_V1 if sr5 else B2_US2_DIAGNOSTIC_V1 if diagnostic else B2_PER_TICKER_ONE_RETRY_V1 if market == 'us' else None,
            normal_messages_sent=False,
            **(dict(one_shot_tag=one_shot_tag,one_shot_date=local_date) if one_shot_tag else {})), exclusive=True)
        try:
            remaining=(_one_shot_deadline(one_shot_tag)-datetime.now(KST)).total_seconds() if one_shot_tag else 16200
            async with asyncio.timeout(min(16200,remaining)):
                result = await _local_registered_cycle(config, directory, session.isoformat(),
                    **(dict(one_shot_tag=one_shot_tag) if one_shot_tag else {}))
        except BaseException as exc:
            _record_local_failure(directory, exc, config=config, session=session.isoformat())
            durable_json(directory/'terminal.json', dict(status='STOPPED_NO_SEND',
                error_type=type(exc).__name__, normal_messages_sent=False), exclusive=True)
            raise
        durable_json(directory/'terminal.json', result, exclusive=True)
        return result


class UnqualifiedAdapter:
    async def policy(self, market, session, run_id):
        raise RuntimeError("unified_production_adapter_not_qualified")

    async def collect(self, request, directory):
        raise RuntimeError("unified_production_adapter_not_qualified")

    async def stage(self, request, directory):
        raise RuntimeError("unified_production_adapter_not_qualified")

    async def notify_failure(self, payload):
        from app.services.notification_service import TelegramNotifier

        # Existing production recipient contract. No recipient literal or investment AI.
        text = "[MONITORING OPERATIONAL FAILURE]\n" + "\n".join(
            f"{key}: {value}" for key, value in payload.items() if key != "kind")
        result = await TelegramNotifier().send({"text": text, "use_llm": False})
        return {"status": result}


def load_adapter(settings, **prepared):
    if settings.unified_snapshot_adapter_version == "production-v1":
        from app.services.production_adapter_factory import build_production_adapter
        return build_production_adapter(settings, **prepared)
    if prepared:
        raise ValueError('prepared_cycle_production_registry_required')
    return UnqualifiedAdapter()


def build_engine(settings, adapter, *, repo_commit, adapter_fingerprint, clock=None):
    config = RunConfiguration(
        root=Path(settings.data_dir) / "unified-snapshot-runs",
        debug_destination=(Path(settings.unified_snapshot_debug_destination)
                           if settings.unified_snapshot_debug_destination else None),
        repo_commit=repo_commit, scheduler_identity="unified-runtime",
        adapter_fingerprint=adapter_fingerprint,
        runtime_contract=settings.unified_snapshot_runtime_contract,
        stage_timeout_seconds=600 if settings.unified_snapshot_runtime_contract.endswith("-v2") else 1200,
        collection_timeout_seconds=600 if settings.unified_snapshot_runtime_contract.endswith("-v2") else 1200,
        secrets=tuple(value.get_secret_value() if hasattr(value, "get_secret_value") else str(value)
                      for key, value in settings.model_dump().items() if value and SECRET_KEY.search(key)),
    )
    return UnifiedMarketRun(config, adapter, clock=clock)


async def run_selected(market, engine, day):
    results = []
    for selected in ("us", "kr") if market == "all" else (market,):
        results.append(await engine.run(selected, day))
    return results


async def run_registered(settings, *, source, model=None, mode='SOURCE_ONLY', clock=None,
                         manual_source_seconds=None, routine_us_no_send_source_seconds=None,
                         record_market_terminal=False):
    """Explicit registered cycle for manual and future scheduler callers.

    Callers supply the original approval/Owner/ledger and already frozen plan;
    neither settings nor this entry issues permissions or installs a trigger.
    """
    from app.services.production_source_backend import CanonicalProductionSourceBackend
    from app.services.unified_snapshot_contract import digest

    if mode not in {'SOURCE_ONLY', 'LIVE_NO_SEND'} or mode == 'SOURCE_ONLY' and model is not None:
        raise ValueError('registered_cycle_source_only_or_explicit_no_send_required')
    if mode == 'LIVE_NO_SEND' and (not model or model.get('run_ledger') is not source.get('run_ledger')):
        raise ValueError('registered_cycle_same_source_model_ledger_required')
    if type(record_market_terminal) is not bool or record_market_terminal and mode != 'LIVE_NO_SEND':
        raise ValueError('registered_market_terminal_requires_no_send')
    if manual_source_seconds is not None and mode != 'LIVE_NO_SEND':
        raise ValueError('registered_manual_source_budget_requires_no_send')
    if manual_source_seconds is not None and routine_us_no_send_source_seconds is not None:
        raise ValueError('registered_manual_and_routine_source_budget_exclusive')
    if {'manual_source_seconds', 'manual_no_send', 'routine_us_no_send_source_seconds'} & source.keys():
        raise ValueError('registered_manual_source_budget_requires_explicit_entry_argument')
    options = {} if manual_source_seconds is None else dict(
        manual_no_send=True, manual_source_seconds=manual_source_seconds)
    if routine_us_no_send_source_seconds is not None:
        options['routine_us_no_send_source_seconds'] = routine_us_no_send_source_seconds
    child, proof = await CanonicalProductionSourceBackend.prepare_registered(settings=settings, **source, **options)
    try:
        child.verify()
        if mode == 'SOURCE_ONLY':
            return dict(status='SOURCE_ADMISSION_PASS', market=child.market,
                model_plan_sha256=child.plan.sha256, model_slots=len(child.plan.slots),
                source_acceptance_sha256=digest(child.owner.acceptance()), normal_messages_sent=False)
        model_options = dict(model)
        model_options.setdefault('approved_plan_sha256', child.plan.sha256)
        adapter = load_adapter(settings, child=child, clock=clock, **model_options)
        source['run_ledger'].bind_model_plan(child)
        engine = build_engine(settings, adapter, repo_commit=source['frozen']['stock_plan']['implementation_sha'],
            adapter_fingerprint=digest(child.binding()), clock=clock)
        result = await engine.run(child.market, datetime.fromisoformat(child.plan.cohort.cutoff).astimezone(KST).date())
        if record_market_terminal:
            source['run_ledger'].rendered_market(child, result)
        return result
    finally:
        child.owner.close()


async def main():
    parser = argparse.ArgumentParser(description="Run one immutable market snapshot cycle")
    parser.add_argument("--market", choices=("us", "kr", "all"), required=True)
    parser.add_argument('--local-scheduled', action='store_true')
    parser.add_argument('--configuration')
    parser.add_argument('--one-shot-tag')
    args = parser.parse_args()
    if args.local_scheduled:
        try:
            if not args.configuration or args.market == 'all':
                raise ValueError('local_schedule_one_market_configuration_required')
            result = await run_local_scheduled(args.configuration, args.market, one_shot_tag=args.one_shot_tag)
            print(json.dumps({k:result[k] for k in ('status', 'reason', 'normal_messages_sent') if k in result}))
            return
        except Exception as exc:
            print(json.dumps(dict(status='STOPPED_NO_SEND', error_type=type(exc).__name__, normal_messages_sent=False)))
            raise SystemExit(1)
    if args.configuration:
        parser.error('--configuration requires --local-scheduled')
    if args.one_shot_tag:
        parser.error('--one-shot-tag requires --local-scheduled')
    settings = get_settings()
    if not settings.unified_snapshot_enabled:
        print(json.dumps({"status": "DISABLED", "mutations": 0}))
        return
    adapter = load_adapter(settings)
    engine = build_engine(settings, adapter, repo_commit=getattr(adapter, "repository_commit", "UNQUALIFIED"),
                          adapter_fingerprint=getattr(adapter, "adapter_fingerprint", "UNQUALIFIED"))
    result = await run_selected(args.market, engine,
                                datetime.now(KST).date())
    print(json.dumps([{"run_id": r["run_id"], "status": r["status"]} for r in result]))
    if any(r["status"] == "FAILED" for r in result):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
