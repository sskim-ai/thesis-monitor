"""Default-OFF launchd event verification, independent of source/model authority.

No job is installed here. An explicitly approved backend installer must retain
the exact plist and code identity. A CLI label, fake clock or serialized receipt
cannot substitute for the current OS-owned process identity.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import plistlib
import re
import subprocess
import sys
from zoneinfo import ZoneInfo

from app.services.unified_runtime_v2 import scheduled_slots
from app.services.vnext_no_send_controller import calendar_gate
from app.services.vnext_research_store import digest

CONTRACT = 'one-shot-no-send-scheduled-event-v1'


def one_shot_plan(*, label, market, local_date, program, working_directory, binding):
    if (not re.fullmatch(r'local\.thesis-monitor\.one-shot\.[a-z0-9-]+',label) or
            market not in ('kr','us') or len(program) < 2 or
            any(not isinstance(s,str) or not s for s in program) or not Path(program[0]).is_absolute() or
            not Path(working_directory).is_absolute() or
            set(binding) != {'store','account_scope','security','session','plan_sha256','context_sha256'}):
        raise ValueError('one_shot_exact_registration_required')
    slots = scheduled_slots(market,local_date)
    gate = calendar_gate(market,slots[0])
    if gate['state'] != 'SOURCE_CHECK_PLAN' or gate['session'] != binding['session']:
        raise ValueError('one_shot_original_calendar_or_session')
    log_root=Path(binding['store']).parent.parent
    if not log_root.is_relative_to('/private/tmp'):
        raise ValueError('one_shot_isolated_log_store_required')
    plist = dict(Label=label,ProgramArguments=program,WorkingDirectory=working_directory,
        StandardOutPath=str(log_root/'launchd-stdout.log'),StandardErrorPath=str(log_root/'launchd-stderr.log'),
        RunAtLoad=False,KeepAlive=False,StartCalendarInterval=[dict(Month=s.month,Day=s.day,Hour=s.hour,Minute=s.minute) for s in slots])
    return dict(contract=CONTRACT,label=label,market=market,binding=deepcopy(binding),plist=plist,
        slots=[s.isoformat() for s in slots],deadline=(slots[-1]+timedelta(minutes=10)).isoformat(),
        one_shot=True,installation_authority=False,send=False,provider_authority=False,model_authority=False)


def _registered_process(plan, plist_path, pid):
    path = Path(plist_path)
    if path.is_symlink() or not path.is_file() or path.stat().st_uid != os.getuid():
        raise ValueError('scheduled_plist_not_owned_plain_file')
    raw = path.read_bytes()
    if plistlib.loads(raw) != plan['plist']:
        raise ValueError('scheduled_registration_changed')
    try:
        result = subprocess.run(['/bin/launchctl','print',f'gui/{os.getuid()}/{plan["label"]}'],
            capture_output=True,text=True,timeout=10)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise ValueError('scheduled_os_event_unobservable') from exc
    if result.returncode != 0:
        raise ValueError('scheduled_os_event_unobservable')
    found = re.search(r'^\s*pid = (\d+)\s*$',result.stdout,re.M)
    source = re.search(r'^\s*path = (.+)\s*$',result.stdout,re.M)
    if not found or int(found[1]) != pid or not source or Path(source[1].strip()).resolve() != path.resolve():
        raise ValueError('scheduled_os_pid_or_plist_mismatch')
    return dict(kind='LAUNCHD_REGISTERED_PROCESS',label=plan['label'],pid=pid,parent_pid=1,
        plist_sha256=digest(raw),os_receipt_sha256=digest(result.stdout.encode()),host=os.uname().nodename)


def inspect_launchd(plan, plist_path):
    """Query only this registered label; denied access is a hard event rejection."""
    if os.getppid() != 1:
        raise ValueError('scheduled_registration_or_launchd_parent')
    expected = plan['plist']['ProgramArguments']
    if (Path(sys.executable).resolve() != Path(expected[0]).resolve() or
            [str(Path(sys.argv[0]).resolve()),*sys.argv[1:]] != [str(Path(expected[1]).resolve()),*expected[2:]] or
            Path.cwd() != Path(plan['plist']['WorkingDirectory'])):
        raise ValueError('scheduled_registered_executor_mismatch')
    return _registered_process(plan,plist_path,os.getpid())


class ScheduledDailyEvent:
    """Live OS event + separate revocable schedule permission, never an API grant."""
    def __init__(self, *, plan, plist_path, approval, implementation_check):
        if not callable(approval) or not callable(implementation_check) or plan.get('contract') != CONTRACT:
            raise ValueError('scheduled_backend_authority_required')
        self._plan = deepcopy(plan)
        self._pin = digest(plan)
        self._approval, self._implementation = approval, implementation_check
        self._path = Path(plist_path)
        self._pid = os.getpid()
        self._event = inspect_launchd(plan,self._path)
        self._created = datetime.now(timezone.utc)
        self._receipt = self._validate()

    def _validate(self):
        # Forked host workers inherit the verified capability; they cannot issue
        # it themselves. Recheck the live parent before any costly side effect.
        if (digest(self._plan) != self._pin or self._approval(deepcopy(self._plan)) != self._pin or
                not self._implementation()):
            raise ValueError('scheduled_authority_revoked_or_drift')
        if os.getpid() == self._pid:
            current=inspect_launchd(self._plan,self._path)
            # Resource counters in launchctl output are deliberately not stable.
            for key in ('kind','label','pid','parent_pid','plist_sha256','host'):
                if current[key] != self._event[key]:raise ValueError('scheduled_event_changed')
        else:
            guardian=os.getppid()
            if guardian != os.getpgrp():raise ValueError('scheduled_capability_wrong_parent')
            try:
                lineage=subprocess.run(['/bin/ps','-o','ppid=','-p',str(guardian)],capture_output=True,text=True,timeout=5)
            except (OSError,subprocess.TimeoutExpired) as exc:
                raise ValueError('scheduled_parent_unobservable') from exc
            if (lineage.returncode != 0 or
                    lineage.stdout.strip() != str(self._pid)):
                raise ValueError('scheduled_capability_wrong_parent')
            _registered_process(self._plan,self._path,self._pid)
        at = datetime.now(timezone.utc)
        first = datetime.fromisoformat(self._plan['slots'][0])
        deadline = datetime.fromisoformat(self._plan['deadline'])
        if not first <= at < deadline or (at-self._created).total_seconds() > 600:
            raise ValueError('scheduled_event_outside_one_shot_window')
        gate = calendar_gate(self._plan['market'],at)
        if gate['session'] != self._plan['binding']['session'] or gate['state'] != 'SOURCE_CHECK_PLAN':
            raise ValueError('scheduled_calendar_session_changed')
        return dict(contract=CONTRACT,event=self._event,registered_plan_sha256=self._pin,
            actual_started_at_UTC=self._created.isoformat(),
            actual_started_at_KST=self._created.astimezone(ZoneInfo('Asia/Seoul')).isoformat(),
            planned_slots=self._plan['slots'],cycle_session=gate['session'],slot=gate['slot'],
            provider_authority=False,model_authority=False,send=False)

    def check(self, config, bridge, account_scope, authority):
        authority.check(config,bridge)
        actual=dict(store=str(config.validate()[0]),account_scope=account_scope,
            security=bridge.registration['security']['canonical_security_id'],session=bridge.session,
            plan_sha256=bridge.request['plan_sha256'],context_sha256=digest(authority.context))
        if actual != self._plan['binding']:
            raise ValueError('scheduled_execution_scope_mismatch')
        self._validate()
        return deepcopy(self._receipt)
