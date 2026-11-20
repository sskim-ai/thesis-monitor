"""Native acquisition transports with bounded child ownership and raw receipts."""
import asyncio
import json
import os
import re
from pathlib import Path
import sys
import time

import httpx

from app.services.canonical_source_acquisition import acquire_all
from app.services.production_source_context import POLICY
from app.services.production_source_dispatch import ProductionSourceDispatcher
from app.services.production_source_seal import read
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest
from app.services.unified_live_source_transport import SourceSafetyStop

ROOT = Path(__file__).resolve().parents[2]


def require_selected_issuer_scope(root, frozen, rebuilt, runtime_cap):
    from app.services.issuer_business_bridge import issuer_identity_errors
    from app.services.selected_source_plan import require_issuer_descriptors

    path='static/official-security-identity.json'
    candidate=rebuilt['candidate']
    dependency=require_issuer_descriptors(rebuilt['plan'],candidate)
    roles=runtime_cap.get('market_subjects',{}).get('us',())
    try:
        raw=(root/path).read_bytes()
        official=json.loads(raw)
        if (candidate==frozen['candidate'] and '000660' in roles
                and sha256_bytes(raw)==frozen.get('protected_input_hashes',{}).get(path)
                and not issuer_identity_errors(target=candidate['financial_plans']['SKHY']['security'],
                    source=candidate['financial_plans']['000660']['security'],official=official,
                    expected_official_sha256=dependency.official_identity_sha256,
                    cutoff=dependency.cutoff.isoformat())):
            return dependency
    except (OSError, TypeError, KeyError, ValueError):
        pass
    raise ValueError('PLAN_INCOMPLETE:us:issuer_auxiliary')


async def acquire_kis_worker(*, root, frozen, plan, credentials, remaining, run_ledger=None):
    path = root / "production-frozen-source-plan.json"
    if frozen.get('scope')=='SELECTED_ORIGINAL_RESEARCH_V1':
        if run_ledger is None or frozen.get('shared_run_ledger')!=run_ledger.worker_binding():
            raise ValueError('selected_kis_shared_budget_required_before_worker')
    frame = dict(contract="production-kis-worker-authorization-v1", root=str(root),
        frozen_sha256=sha256_bytes(path.read_bytes()), plan_sha256=digest(plan), seconds_remaining=remaining,
        credentials=dict(app_key=credentials["kis"][0], app_secret=credentials["kis"][1]))
    env = {k: os.environ[k] for k in ("PATH", "HOME", "TMPDIR", "LANG") if k in os.environ}
    env.update(PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE="1", THESIS_MONITOR_ENV_FILE="",
        DATABASE_URL="sqlite://", NOTIFICATION_DRY_RUN="true", ENABLE_LIVE_PROVIDERS="false",
        UNIFIED_SNAPSHOT_ENABLED="false")
    process = await asyncio.create_subprocess_exec(sys.executable, "-B", "-m", "app.jobs.production_kis_worker",
        cwd=ROOT, env=env, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(json.dumps(frame).encode()), remaining)
    except BaseException:
        if process.returncode is None:
            process.kill()
        await process.wait()
        durable_json(root / "kis-worker-exit.json", dict(status="INTERRUPTED", child_reaped=True), exclusive=True)
        raise
    finally:
        frame["credentials"].clear()
    try:
        diagnostic = json.loads(stdout) if len(stdout) <= 4096 else {}
        if not isinstance(diagnostic, dict):
            diagnostic = {}
    except (ValueError, UnicodeError):
        diagnostic = {}
    terminal_ok = diagnostic.get('terminal') == 'KIS_FRESH_ACQUISITION_COMPLETE_REPLAY_REQUIRED'
    error_type = diagnostic.get('error_type', '')
    receipt = dict(status="PASS" if process.returncode == 0 and terminal_ok else "FAIL",
        returncode=process.returncode, stage='KIS_WORKER', child_reaped=True, generation_id=frozen["generation_id"],
        error_type=error_type if type(error_type) is str and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,79}', error_type) else 'UNREPORTED',
        stdout_bytes=len(stdout), stderr_bytes=len(stderr),
        stdout_sha256=sha256_bytes(stdout), stderr_sha256=sha256_bytes(stderr))
    durable_json(root / "kis-worker-exit.json", receipt, exclusive=True)
    if process.returncode != 0 or not terminal_ok:
        if run_ledger is not None:run_ledger.stop('KIS_WORKER_FAILED')
        raise ValueError("production_kis_acquisition_failed")


class NativeProductionSourceTransport:
    def __init__(self, settings, *, http_transport_factory=None, kis_worker=acquire_kis_worker,
                 run_ledger=None, registration_owner=None, source_policy=None, native_settings=None):
        self.settings = settings
        self.http_transport_factory = http_transport_factory or (lambda: httpx.AsyncHTTPTransport(retries=0))
        self.kis_worker = kis_worker
        self.run_ledger,self.registration_owner,self.source_policy=run_ledger,registration_owner,source_policy
        self.native_settings = native_settings

    async def collect(self, *, root, frozen, compiler, kis_plan, credentials, deadline, retained_sec=None):
        plan_path = root / "production-frozen-source-plan.json"
        initial = sha256_bytes(plan_path.read_bytes())

        def guard():
            if time.monotonic() >= deadline:
                raise SourceSafetyStop('source_deadline_exceeded')
            if sha256_bytes(plan_path.read_bytes()) != initial:
                raise SourceSafetyStop('source_frozen_plan_drift')

        options=dict(plan=frozen['plan'],root=root/'dispatch',compiler_args=compiler,kis_plan=kis_plan,
            config_identities=frozen['config_identities'],credential_presence={k:all(v) for k,v in credentials.items()},
            repository_root=ROOT,secrets=tuple(v for values in credentials.values() for v in values if v!='NO_CREDENTIAL_REQUIRED'))
        selected=frozen.get('scope')=='SELECTED_ORIGINAL_RESEARCH_V1'
        retained_pins = {t:sorted((entry['proof']['pin'] for entry in items.values()),key=digest)
                         for t,items in (retained_sec or {}).items() if items}
        if (retained_pins != frozen.get('retained_sec_documents',{}) or (retained_pins and
                (not selected or frozen.get('selected_market')!='us'
                 or set(retained_pins)-set(frozen['candidate']['financial_plans'])))):
            raise ValueError('production_retained_sec_frozen_scope_mismatch')
        if selected:
            if self.run_ledger is None or self.registration_owner is None or self.source_policy is None:
                raise ValueError('selected_original_transport_ledger_and_registration_required')
            from app.services.selected_source_dispatch import SelectedSourceDispatcher
            from app.services.selected_source_plan import request_budget,compile_selected_plan
            rebuilt=compile_selected_plan(compiler_args=compiler,kis_plan=kis_plan)
            if frozen.get('selected_market') == 'kr':
                from app.services.selected_kis_sources import require_persisted_plan
                require_persisted_plan(root, kis_plan, rebuilt['plan'])
            if frozen.get('selected_market')=='us' and 'SKHY' in rebuilt['plan'].subjects:
                require_selected_issuer_scope(root,frozen,rebuilt,self.run_ledger.identity['runtime_cap'])
            dispatcher=SelectedSourceDispatcher(**options,registration_owner=self.registration_owner,
                policy=self.source_policy,approved_plan_sha256=rebuilt['plan'].plan_sha256,
                approved_provider_caps=request_budget(rebuilt,kis_plan)['providers'],guard=guard,
                enabled=True,run_ledger=self.run_ledger)
        else:
            if self.run_ledger is not None:
                raise ValueError('selected_campaign_cannot_enter_full22_transport')
            dispatcher=ProductionSourceDispatcher(**options)

        await acquire_all(root=root, frozen=frozen, settings=self.settings, dispatcher=dispatcher,
            inner=self.http_transport_factory(), policy=POLICY, guard=guard, native_settings=self.native_settings, **(
                dict(retained_sec=retained_sec) if retained_pins else {}))
        outcome = read(root / "acquisition-outcome.json")
        if "systemic_stop" in outcome["phases"]:
            raise ValueError("production_source_systemic_stop")
        if kis_plan is not None:
            guard()
            await self.kis_worker(root=root, frozen=frozen, plan=kis_plan, credentials=credentials,
                                  remaining=min(600, deadline - time.monotonic()),
                                  **({'run_ledger':self.run_ledger} if selected else {}))
        return outcome
