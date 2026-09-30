"""C1 opt-in official-host continuation; exact REV31 requests, no recollection."""
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import subprocess
import sys

from app.services.unified_run_artifacts import durable_json
from scripts import qualified_official_launch_context as q
from scripts.r9_rev11_models import FreshExecution
from scripts import m12dr_fresh_blind_reproof as p

AUTHORITY = p.REPO/'docs/work-instructions/20260930-rev31-c1-state-ownership-clarification.md'
SOURCE_ONLY_SHA = 'af3b16102ec4e66d60f2d283efb2aad542ee77da84703a8b5b070cd330b66c19'


class QualifiedFreshExecution(FreshExecution):
    def __init__(self, root, sources, prior, source_only):
        super().__init__(root, sources)
        self.prior, self.source_only = prior, source_only
        self.qualified = None
        self.context_freeze_sha = None
        self.names = q.inventory_names()
        self.entry_environment = q.environment(self.names)
        self.guard = q.ManualMutationGuard([
            p.OPERATING, Path.home()/'.codex', self.sources, self.prior.parent, self.source_only,
            Path.home()/'Library/LaunchAgents'])

    def prepare(self):
        from scripts.sealed_cohort_offline_proof import network_guard
        network_guard()
        p.require(not self.root.exists(), 'C1_NEW_CONTINUATION_ROOT_REQUIRED')
        old = p.read(self.prior/'report/execution-freeze.json')
        p.require(all(v == 0 for v in p.read(self.prior/'report/execution-complete.json')['calls'].values()),
                  'C1_PRIOR_TRANSMISSION_NOT_ZERO')
        p.require(p.sha(self.source_only) == SOURCE_ONLY_SHA, 'C1_SOURCE_ONLY_ARCHIVE_DRIFT')
        p.require(p.manifest(self.sources) == old['sources'], 'C1_SEALED_SOURCE_DRIFT')
        p.require(p.manifest(self.prior/'inputs') == old['inputs'], 'C1_PRIOR_INPUT_DRIFT')
        self.report.mkdir(parents=True)
        self.sealed.mkdir()
        # APFS copy-on-write copies preserve bytes without duplicating source blocks.
        for src, dst in [(self.prior/'inputs', self.root/'inputs'),
                         (self.prior/'sealed/requests', self.requests)]:
            subprocess.run(['/bin/cp','-cR',str(src),str(dst)],check=True)
        for name in ('initial-requests.json','market-request-freeze.json','core-request-freeze.json'):
            shutil.copy2(self.prior/'sealed'/name,self.sealed/name)
        shutil.copy2(self.prior/'report/host-context.json',self.report/'host-context.json')
        self.frozen = {**old, 'controller':p.git_state(p.REPO), 'code':p.code_manifest(),
            'prior_execution_freeze_sha256':p.sha(self.prior/'report/execution-freeze.json'),
            'prior_requests':p.manifest(self.prior/'sealed/requests'),
            'source_only_zip_sha256':SOURCE_ONLY_SHA,'maintenance_authorization_sha256':p.sha(AUTHORITY),
            'context_contract':q.CONTRACT,'continuation':'REV31-C1',
            'preparation_receipt_role':'PROVENANCE_ONLY_ACTUAL_HOST_MUST_QUALIFY'}
        p.require(not self.frozen['controller']['status'], 'C1_IMPLEMENTATION_NOT_COMMITTED')
        durable_json(self.report/'execution-freeze.json',self.frozen,exclusive=True)
        self.stage_manifests = dict(old['stage_manifests'])
        self.verify()

    def verify(self):
        super().verify()
        p.require(p.sha(self.prior/'report/execution-freeze.json') == self.frozen['prior_execution_freeze_sha256'],
                  'C1_PRIOR_FREEZE_DRIFT')
        p.require(p.manifest(self.prior/'sealed/requests') == self.frozen['prior_requests'], 'C1_PRIOR_REQUEST_DRIFT')
        for name, sha in self.frozen['prior_requests'].items():
            p.require(p.sha(self.requests/name) == sha, 'C1_REQUEST_BYTES_DRIFT')
        p.require(p.sha(self.source_only) == SOURCE_ONLY_SHA, 'C1_SOURCE_ONLY_ARCHIVE_DRIFT')
        p.require(p.sha(AUTHORITY) == self.frozen['maintenance_authorization_sha256'], 'C1_STATE_AUTHORITY_DRIFT')
        p.require(self.guard.blocked_attempts == 0, 'C1_MANUAL_MUTATION_ATTEMPT')

    def identity(self):
        return q.LaunchIdentity(implementation_sha=self.frozen['controller']['head'],source_generation_id=self.source_gen,
            whole_source_sha256=self.frozen['fresh_source_replay']['first_sha256'],source_only_zip_sha256=SOURCE_ONLY_SHA,
            request_freeze_sha256=p.sha(self.report/'execution-freeze.json'),
            prompt_schema_sha256=q.digest(self.frozen['prior_requests']),
            executable_sha256=p.binding().executable_sha256,
            launcher_sha256=p.sha(p.REPO/'app/services/official_codex_shadow_transport_service.py'),
            qualification_sha256=p.binding().qualification_sha256,cwd_sha256=q.legacy.digest(str(p.REPO)))

    def qualify_host(self, secret_scan):
        self.verify()
        p.require(self.qualified is None, 'C1_HOST_ALREADY_QUALIFIED')
        context = self.current_launch_context()
        evidence = q.StateWriteEvidence('CONTROLLER_ONLY_OFFICIAL_MAINTENANCE_AUTHORIZED',0,0,
            q.digest(context),p.binding().executable_sha256,
            p.sha(p.REPO/'app/services/official_codex_shadow_transport_service.py'),p.sha(AUTHORITY))
        identity = self.identity()
        qualified = q.QualifiedOfficialModelLaunchContext.qualify(identity=identity,expected_identity=identity,
            preparation=p.read(self.prior/'report/host-context.json'),
            preparation_sha256=self.frozen['host_context_sha256'],
            actual_preparation_sha256=p.sha(self.prior/'report/host-context.json'),context=context,
            entry_environment=self.entry_environment,state_evidence=evidence,binding_verified=True,
            provider_calls=0,secret_scan_passed=secret_scan(dict(context=context,identity=asdict(identity),evidence=asdict(evidence))),
            expected_maintenance_authorization_sha256=self.frozen['maintenance_authorization_sha256'])
        durable_json(self.report/'qualified-actual-host.json',qualified.receipt(),exclusive=True)
        durable_json(self.report/'launch-context-transition.json',dict(status='PASS',
            preparation_sha256=self.frozen['host_context_sha256'],qualified_host_sha256=qualified.sha256,
            observed_difference_names=list(qualified.transition_differences),
            unexplained_difference_count=0,markers_modified=False),exclusive=True)
        freeze=dict(contract=q.CONTRACT,authority=qualified.receipt(),authority_sha256=qualified.sha256,
            receipt_file_sha256=p.sha(self.report/'qualified-actual-host.json'),
            qualified_at=p.now(),native_internal_maintenance='AUTHORIZED_NOT_MEASURED_AS_ZERO',
            direct_db_write_calls=0,permission_mutations=0,source_only_sha256=p.sha(self.source_only))
        durable_json(self.report/'official-model-execution-context-freeze.json',freeze,exclusive=True)
        self.qualified = qualified
        self.context_freeze_sha = p.sha(self.report/'official-model-execution-context-freeze.json')

    def current_launch_context(self):
        return q.capture_context(self.names)

    def authorize_launch_context(self, context):
        p.require(self.qualified is not None, 'C1_QUALIFIED_HOST_REQUIRED')
        self.verify()
        p.require(p.sha(self.report/'official-model-execution-context-freeze.json') == self.context_freeze_sha,
                  'C1_CONTEXT_FREEZE_REWRITE')
        frozen=p.read(self.report/'official-model-execution-context-freeze.json')
        p.require(p.sha(self.report/'qualified-actual-host.json') == frozen['receipt_file_sha256'], 'C1_HOST_RECEIPT_REWRITE')
        receipt=self.qualified.verify(context=context,identity=self.identity(),
            preparation_sha256=p.sha(self.prior/'report/host-context.json'),freeze_sha256=frozen['authority_sha256'])
        receipt.update(source_only_sha256=p.sha(self.source_only),free_bytes=shutil.disk_usage(self.root).free,
                       direct_mutation_attempts=self.guard.blocked_attempts)
        durable_json(self.report/'per-call-contexts'/f'{len(self.ledger):02d}.json',receipt,exclusive=True)

    def run_qualified(self, secret_scan):
        self.guard.roots += tuple(path.resolve() for path in [self.root/'inputs',
            self.report/'execution-freeze.json',self.report/'host-context.json',
            self.sealed/'initial-requests.json',self.requests/'core',self.requests/'market',
            self.sealed/'core-request-freeze.json',self.sealed/'market-request-freeze.json'])
        sys.addaudithook(self.guard)
        self.qualify_host(secret_scan)
        self.guard.roots += tuple((self.report/name).resolve() for name in [
            'qualified-actual-host.json','launch-context-transition.json','official-model-execution-context-freeze.json'])
        print('C1_QUALIFIED_HOST_FROZEN; launching unchanged Market/Core/A/B',flush=True)
        super().run()
        durable_json(self.report/'direct-mutation-guard.json',dict(blocked_attempts=self.guard.blocked_attempts,
            direct_db_writes=0,permission_mutations=0,native_internal_state_management='AUTHORIZED_CLI_OWNED'),exclusive=True)
        print(json.dumps(p.read(self.report/'execution-complete.json')),flush=True)
