"""Hash-only offline closure and fail-stop A/B continuation of sealed R5 outputs."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import traceback
import zipfile

from scripts import r2b_r2_contract as c
from scripts import r2b_r2_preflight as pre
from scripts import r2b_r4_preflight as r4
from scripts import r2b_r5_execution as r5
from scripts import r2b_sealed_blind_preflight as io
from scripts import m12dr_fresh_blind_reproof as p
from scripts import m12ds_launch_context as launch
from scripts.m12da_source_use_contract import canonical_sha256
from scripts.sealed_cohort_offline_proof import network_guard

R5_SHA = '06a6f53db269a2ed344bc29a94e02c429a3cfcf799de075ddc8ea96165009695'
R5_GENERATION = '20260928-r2b-r5-20260928T012541Z'
BASE = '8b607b74b02e1b32776564a87e5384f676b3c69d'
STAGES = ('pass-a', 'pass-b')
CATALOG_OWNER = 'scripts.m12da_source_use_contract.canonical_sha256'
BLIND_SOURCE = Path('/Users/sskim/Documents/Codex/Reports/20260927-r2b-sealed-source-blind-review/thesis-monitor-20260927-r2b-BLIND_SOURCE_REVIEW.zip')


def stage(root, archive_path):
    network_guard()
    p.require(not root.exists(), 'new_root_required')
    p.require(p.sha(archive_path) == R5_SHA, 'R2B_R6_UPSTREAM_MARKET_CORE_FREEZE_DRIFT')
    with zipfile.ZipFile(archive_path) as archive:
        manifest = json.loads(archive.read('result/bundle-manifest.json'))
        names = archive.namelist()
        p.require(len(names) == len(set(names)) and set(names) ==
                  {'result/' + name for name in manifest} | {'result/bundle-manifest.json'}, 'upstream_manifest_set')
        for name, entry in manifest.items():
            path = Path(name)
            p.require(not path.is_absolute() and '..' not in path.parts, 'unsafe_archive_path')
            raw = archive.read('result/' + name)
            p.require(io.sha(raw) == entry['sha256'] and len(raw) == entry['bytes'], 'upstream_manifest_integrity')
        root.mkdir(parents=True)
        for name in manifest:
            io.durable_bytes(root/'upstream'/name, archive.read('result/' + name), exclusive=True)
        io.durable_bytes(root/'upstream/bundle-manifest.json', archive.read('result/bundle-manifest.json'), exclusive=True)
    shutil.copytree(root/'upstream/execution/inputs', root/'inputs')
    p.write(root/'report/identity.json', dict(generation_id='20260928-r2b-r6-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),
        upstream_generation_id=R5_GENERATION, upstream_zip_sha256=R5_SHA,
        upstream_manifest_entries=len(manifest), independent_assessment_content_read=False))


class Continuation(r5.Execution):
    def __init__(self, root):
        super().__init__(root)
        self.upstream = root/'upstream/execution'
        self.gen = p.read(root/'report/identity.json')['generation_id']
        self.inherited = p.read(self.upstream/'report/model-structural-ledger.json')['rows']
        market = p.read(self.upstream/'sealed/market-output-freeze.json')
        core = p.read(self.upstream/'sealed/core-output-freeze.json')
        self.markets, self.cores = market['accepted'], core['accepted']
        self.limits['core'] = core['limits']
        if (self.sealed/'pass-a-request-freeze.json').exists():
            self.stage_manifests['pass-a'] = p.sha(self.sealed/'pass-a-request-freeze.json')

    def upstream_proof(self):
        frozen = p.read(self.upstream/'report/execution-freeze.json')
        complete = p.read(self.upstream/'report/execution-complete.json')
        p.require(frozen['generation_id'] == R5_GENERATION and complete['generation_id'] == R5_GENERATION, 'upstream_generation')
        p.require(complete['calls'] == {'market': 2, 'core': 8, 'pass-a': 0, 'pass-b': 0}, 'upstream_call_count')
        p.require(len(self.markets) == 2 and len(self.cores) == 21 and len(self.limits['core']) == 1, 'upstream_subject_count')
        p.require(p.manifest(self.root/'inputs') == frozen['inputs'], 'upstream_input_drift')
        p.require(p.manifest(self.upstream/'inputs') == frozen['inputs'], 'upstream_frozen_input_drift')
        p.require(p.sha(self.upstream/'sealed/initial-requests.json') == frozen['initial_request_manifest_sha256'], 'upstream_initial_requests')
        r4.verify_receipt((self.root/'inputs/neutral-v2.json').read_bytes())
        p.require(frozen['source_hashes'] == p.read(self.root/'inputs/stock/summary.json')['source_hashes'], 'source_hashes_changed')
        p.require(frozen['quality_supplement_sha256'] == r4.SUPPLEMENT_SHA, 'quality_supplement_changed')
        initial = p.read(self.upstream/'sealed/initial-requests.json')
        rows = []
        for stage in ('market', 'core'):
            output = p.read(self.upstream/'sealed'/f'{stage}-output-freeze.json')
            p.require(output['generation_id'] == R5_GENERATION and output['call_files'] ==
                      p.manifest(self.upstream/'sealed/calls'/stage), 'upstream_output_freeze_drift')
            request_manifest = self.upstream/'sealed'/f'{stage}-request-freeze.json'
            p.require(p.sha(request_manifest) == frozen['stage_manifests'][stage], 'upstream_request_freeze_drift')
            p.require(p.manifest(self.upstream/'sealed/requests'/stage) == p.read(request_manifest)['files'], 'upstream_request_files')
            for request in initial[stage]:
                m, b = request['market'], request['batch']
                relative = Path(stage)/m/f'batch-{b:02d}'
                req = self.upstream/'sealed/requests'/relative
                dest = self.upstream/'sealed/calls'/relative
                ledger = next(row for row in self.inherited if row['stage'] == stage and row['market'] == m and row['batch'] == b)
                p.require(ledger['status'] == 'PASS' and ledger['attempts'] == 1, 'upstream_call_not_pass')
                for filename, key in [('prompt.txt', 'prompt_sha256'), ('provider-wire-schema.json', 'schema_sha256')]:
                    p.require(p.sha(req/filename) == ledger[key], 'upstream_prompt_schema_drift')
                p.require(p.sha(dest/'raw-output.json') == ledger['raw_output_sha256'], 'upstream_raw_drift')
                raw = p.read(dest/'raw-output.json')
                for name in ('provider-wire-schema.json', 'internal-semantic-schema.json'):
                    p.require(not p.owner.validate_json_schema(raw, p.read(req/name)), 'upstream_schema_replay')
                if stage == 'market':
                    p.require(raw == p.read(dest/'accepted.json') == self.markets[m], 'upstream_market_accepted_drift')
                    p.require(r5.market_owner.validate_market(raw, self.projected[m]['context'])['status'] == 'PASS', 'upstream_market_semantic')
                else:
                    inputs = p.read(req/'subject-context.json')
                    accepted = {t:c.policy.materialize_core(t, raw['cores'][t], inputs[t]['metadata'], inputs[t]['authority'],
                                                          inputs[t]['frozen_fact_fields']) for t in self.partition(request)}
                    p.require(accepted == p.read(dest/'accepted.json') == {t:self.cores[t] for t in accepted}, 'upstream_core_accepted_drift')
                    for t, row in raw.get('limits', {}).items():
                        p.require(row == self.limits['core'][t], 'upstream_limit_changed')
                        c.validate_unknown(row, mode='UNKNOWN_LIMIT', recovery=self.prepared[t]['recovery'],
                                           capability={k:[] for k in c.DIRECTION_BUCKETS})
                rows.append(dict(stage=stage, market=m, batch=b, subjects=request['subjects'], status='PASS',
                    prompt_sha256=p.sha(req/'prompt.txt'), schema_sha256=p.sha(req/'provider-wire-schema.json'),
                    raw_sha256=p.sha(dest/'raw-output.json'), accepted_sha256=p.sha(dest/'accepted.json'),
                    transport_receipt_sha256=p.sha(dest/'transport-receipt.json')))
        p.require(len(rows) == len(self.inherited) == 10, 'upstream_ledger_count')
        return dict(status='PASS', R5_zip_sha256=R5_SHA, generation_id=R5_GENERATION, rows=rows,
                    Market=2, Core=22, ordinary=21, UNKNOWN_LIMIT=1, new_model_calls=0)

    def offline(self):
        network_guard()
        p.require(not (self.sealed/'pass-a-request-freeze.json').exists(), 'offline_proof_already_exists')
        before = p.manifest(self.root/'inputs')
        p.write(self.report/'upstream-market-core-verification.json', self.upstream_proof())
        old = {row['ticker']:row for row in p.read(self.root/'upstream/poststop-hash-forensics.json')['rows']}
        rows = []
        for t, data in self.prepared.items():
            if data['mode'] == 'UNKNOWN_LIMIT':
                rows.append(dict(ticker=t, mode='UNKNOWN_LIMIT', status='PASS', content_changed=False))
                continue
            self.chain(t, self.cores[t]['atomic_claims'])
            catalog, chain = self.catalogs[t], self.chains[t]
            p.require(c.digest(catalog) == old[t]['producer_catalog_sha256'], 'R2B_R6_MODEL_VIEW_CHANGED_BY_HASH_REPAIR')
            p.require(canonical_sha256(catalog) == old[t]['consumer_catalog_sha256'], 'R2B_R6_MODEL_VIEW_CHANGED_BY_HASH_REPAIR')
            p.require(catalog['atomic_claims'] == self.cores[t]['atomic_claims'], 'core_claim_content_changed')
            expected = canonical_sha256(catalog)
            p.require(all(chain[key]['catalog_sha256'] == expected for key in ('authority', 'expectation', 'projection')), 'R2B_R6_CANONICAL_CATALOG_HASH_GAP')
            p.require(chain['validation']['status'] == 'PASS', 'source_input_expectation_failed')
            original = {row['ref_id']:row for row in data['source_authority']['authority']['authority_records']}
            for record in chain['authority']['authority_records']:
                for key in ('allowed_uses', 'prohibited_uses', 'authority_state'):
                    p.require(record[key] == original[record['ref_id']][key], 'authority_widened')
            rows.append(dict(ticker=t, status='PASS', semantic_object='source-use catalog', producer='r2b_r2_contract.bound_chain',
                consumer='freeze_source_use_input_expectation', previous_serializer='unified_snapshot_contract.digest',
                canonical_owner=CATALOG_OWNER, before_sha256=old[t]['producer_catalog_sha256'], after_sha256=expected,
                parsed_object_equality=True, claim_content_unchanged=True, authority_widened=False,
                before_validation='PASS' if old[t]['actual_claims_hash_equal'] else 'HASH_MISMATCH',
                expectation_sha256=canonical_sha256(chain['expectation']), binding_sha256=canonical_sha256(chain['binding'])))
        requests = self.before_a()
        p.require(sum(len(row['subjects']) for row in requests) == 22 and len(requests) == 8, 'a_input_cohort_incomplete')
        matrix = []
        for request in requests:
            contexts = p.read(Path(request['directory'])/'subject-context.json')
            for t, context in contexts.items():
                matrix.append(dict(ticker=t, input_sha256=c.digest(context), mode=self.prepared[t]['mode']))
        p.require(p.manifest(self.root/'inputs') == before, 'source_input_mutated')
        p.write(self.report/'core-to-a-catalog-hash-owner-matrix.json', rows)
        p.write(self.report/'a-input-hash-matrix.json', matrix)
        p.write(self.report/'offline-closure.json', dict(status='PASS', ordinary_catalogs=21, UNKNOWN_LIMIT=1,
            A_input_ready=22, A_requests=8, model_calls=0, provider_calls=0, blind_fairness='PASS_V2',
            independent_assessment_content_read=False, economic_content_changed=False,
            before_comparison='Exact R5 pre-gate catalog digest and inherited claim objects; no full R5 A request existed.',
            source_input_files_unchanged=True, authority_widened=False))
        print('R6 offline closure PASS: Market2/Core22 exact, A22 ready, calls=0', flush=True)

    def hydrate_a(self):
        requests = p.read(self.sealed/'pass-a-request-freeze.json')['requests']
        for request in requests:
            expected = p.read(Path(request['directory'])/'subject-context.json')
            contexts = {}
            for t in request['subjects']:
                if self.prepared[t]['mode'] == 'UNKNOWN_LIMIT':
                    contexts[t] = self.limit_context(t)
                else:
                    self.chain(t, self.cores[t]['atomic_claims'])
                    data = self.prepared[t]
                    gate = pre.a_input(data['view'], self.catalogs[t], self.subjects[t], self.chains[t], data['source_authority'])
                    p.require(gate['receipt']['status'] == 'PASS', 'a_hydration_gate')
                    self.actx[t] = contexts[t] = gate['model_context']
            p.require(contexts == expected, 'a_frozen_input_changed')
        return requests

    def freeze(self):
        p.require(self.frozen is None and not p.git_state(p.REPO)['status'], 'clean_new_freeze_required')
        validation = p.read(self.root/'validation/validation.json')
        p.require(validation['status'] == 'PASS' and validation['head'] == p.git_state(p.REPO)['head'], 'exact_validation_required')
        p.require(p.read(self.report/'offline-closure.json')['status'] == 'PASS', 'offline_closure_required')
        self.upstream_proof()
        self.hydrate_a()
        old = p.read(self.upstream/'report/execution-freeze.json')
        original = (self.root/'upstream/contract-owner-sources/scripts/r2b_r2_contract.py').read_bytes()
        repaired = original.replace(b'build_source_use_projection, canonical_source_metadata_sha256,',
            b'build_source_use_projection, canonical_sha256, canonical_source_metadata_sha256,').replace(
            b'derivative.update(catalog_sha256=digest(cat),', b'derivative.update(catalog_sha256=canonical_sha256(cat),')
        p.require((p.REPO/'scripts/r2b_r2_contract.py').read_bytes() == repaired, 'repair_scope_changed')
        p.require(all(p.sha(p.REPO/name) == expected for name,expected in old['code'].items()
                      if name != 'scripts/r2b_r2_contract.py'), 'unrelated_existing_code_changed')
        p.require(p.sha(BLIND_SOURCE) == r4.r1.BLIND_SHA, 'blind_source_zip_changed')
        p.require(old['source_hashes'] == r4.r1.SOURCE_HASHES, 'sealed_source_hash_contract_drift')
        p.write(self.report/'serializer-contract-audit.json', dict(status='PASS',
            changed_existing_code=['scripts/r2b_r2_contract.py'], exact_import_and_catalog_assignment_only=True,
            all_other_existing_code_unchanged=True, global_source_digest_unchanged=True,
            source_hashes=old['source_hashes'], blind_source_zip_sha256=p.sha(BLIND_SOURCE),
            independent_assessment_content_read=False, existing_canonical_owner=CATALOG_OWNER))
        host = launch.context_receipt()
        p.require(host['state_access']['effective_open_readwrite_without_write'], 'host_launch_unready')
        p.write(self.report/'host-context.json', host)
        self.frozen = dict(status='ISSUED_R2B_R6_AFTER_CORE_FREEZE', generation_id=self.gen,
            upstream_generation_id=R5_GENERATION, upstream_zip_sha256=R5_SHA, upstream_manifest=p.manifest(self.root/'upstream'),
            upstream_output_freezes={stage:p.sha(self.upstream/'sealed'/f'{stage}-output-freeze.json') for stage in ('market', 'core')},
            source_hashes=old['source_hashes'], quality_supplement_sha256=r4.SUPPLEMENT_SHA,
            neutral_receipt_sha256=r4.RECEIPT_SHA, blind_fairness='PASS_V2', independent_assessment_content_read=False,
            catalog_hash_owner=CATALOG_OWNER, controller=p.git_state(p.REPO), operating=p.git_state(p.OPERATING),
            code=p.code_manifest(), inputs=p.manifest(self.root/'inputs'),
            validation_sha256=p.sha(self.root/'validation/validation.json'),
            host_context_sha256=p.sha(self.report/'host-context.json'),
            launch_contract_sha256=p.sha(launch.INSTRUCTION/'m12ds-launch-context-parity-contract.json'),
            stage_manifests=self.stage_manifests, proof_manifest=p.manifest(self.sealed/'pre-a'),
            A_subject_input_hash_matrix_sha256=p.sha(self.report/'a-input-hash-matrix.json'),
            decision_modes={t:data['mode'] for t,data in self.prepared.items()},
            stored_price_rule_versions_pass=p.read(self.root/'inputs/stock/summary.json')['stored_price_rule_versions_pass'],
            limitation_policy_sha256=p.sha(p.REPO/'scripts/r2b_r2_contract.py'),
            closure_sha256=p.sha(self.report/'offline-closure.json'),
            serializer_audit_sha256=p.sha(self.report/'serializer-contract-audit.json'),
            model='gpt-5.6-sol', effort='xhigh', timeout_seconds=1200,
            new_call_budget=dict(market=0, core=0, **{'pass-a':8, 'pass-b':8}),
            inherited_calls=dict(market=2, core=8), retries=0, repair=0, fallback=0, judge=0,
            frozen_at=p.now(), downstream='B exact requests frozen only after full new A validation')
        p.write(self.report/'execution-freeze.json', self.frozen)
        self.verify()
        print(json.dumps(dict(status=self.frozen['status'], generation_id=self.gen, new_model_calls=0)), flush=True)

    def verify(self):
        super().verify()
        p.require(p.manifest(self.root/'upstream') == self.frozen['upstream_manifest'], 'upstream_stage_artifact_drift')
        p.require(p.sha(self.report/'offline-closure.json') == self.frozen['closure_sha256'], 'closure_receipt_drift')
        p.require(p.sha(self.report/'serializer-contract-audit.json') == self.frozen['serializer_audit_sha256'], 'serializer_audit_drift')
        p.require(p.manifest(self.sealed/'pre-a') == self.frozen['proof_manifest'], 'pre_a_proof_drift')
        p.require(p.sha(self.report/'a-input-hash-matrix.json') == self.frozen['A_subject_input_hash_matrix_sha256'], 'a_input_matrix_drift')
        p.require(all(row['stage'] in STAGES for row in self.ledger) and sum(row['attempts'] for row in self.ledger) <= 16,
                  'r6_new_call_budget')

    def invoke(self, stage, spec, request):
        p.require(stage in STAGES, 'r6_market_core_dispatch_forbidden')
        return super().invoke(stage, spec, request)

    def run(self):
        p.require(not (self.report/'model-structural-ledger.json').exists(), 'one_execution_only')
        stage = 'pass-a'
        terminal = 'R2B_R6_A_MODEL_FAILURE'
        try:
            self.verify()
            requests = self.hydrate_a()
            for stage in STAGES:
                if stage == 'pass-b':
                    requests = self.before_b()
                    p.write(self.report/'b-input-hash-matrix.json', [dict(ticker=t, input_sha256=c.digest(ctx))
                        for request in requests for t,ctx in p.read(Path(request['directory'])/'subject-context.json').items()])
                for request in requests:
                    self.bounded(stage, {key:request[key] for key in ('market', 'batch', 'subjects')}, request)
                accepted = self.arows if stage == 'pass-a' else self.brows
                p.require(len(accepted) + len(self.limits[stage]) == 22, 'stage_incomplete')
                p.write(self.sealed/(stage+'-output-freeze.json'), dict(generation_id=self.gen, upstream_generation_id=R5_GENERATION,
                    accepted=accepted, limits=self.limits[stage], call_files=p.manifest(self.sealed/'calls'/stage)))
            stage = 'render'
            self.render()
            terminal = 'R2B_R6_MONITORING_AI_24_MESSAGE_PASS_READY_FOR_BLIND_COMPARISON'
        except Exception as exc:
            terminal = {'pass-a':'R2B_R6_A_MODEL_FAILURE', 'pass-b':'R2B_R6_B_MODEL_FAILURE',
                        'render':'R2B_R6_RENDER_VALIDATION_FAILURE'}[stage]
            p.write(self.sealed/'failure.json', dict(stage=stage, type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc()))
        finally:
            calls = {s:sum(row['attempts'] for row in self.ledger if row['stage'] == s) for s in STAGES}
            p.write(self.report/'execution-complete.json', dict(terminal=terminal, generation_id=self.gen,
                upstream_generation_id=R5_GENERATION, calls=dict(market=0, core=0, **calls),
                cumulative_calls=dict(market=2, core=8, **calls), accepted=dict(Market=2, Core=21, A=len(self.arows), B=len(self.brows)),
                accepted_limits={s:len(v) for s,v in self.limits.items()}, messages=len(list((self.root/'messages').glob('*.txt'))),
                independent_assessment_content_read=False, reveal_gate='CLOSED_UNTIL_FULL_RESULT_SEAL',
                provider_refresh=0, production_side_effects=0, retry=0))
            inherited = [dict(deepcopy(row), stage_generation_id=R5_GENERATION, provenance='R5_FROZEN') for row in self.inherited]
            new = [dict(deepcopy(row), stage_generation_id=self.gen, provenance='R6_CONTINUATION') for row in self.ledger]
            p.write(self.report/'cumulative-model-ledger.json', dict(rows=inherited + new))
            self.publish()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('stage', 'offline', 'freeze', 'run'))
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--r5-zip', type=Path)
    args = parser.parse_args()
    audit = pre.SourceReadAudit([args.r5_zip] if args.r5_zip else [],
        [Path('/tmp/codex-remote-attachments'), Path.home()/'Library/Mobile Documents/com~apple~CloudDocs', p.OPERATING/'data'])
    sys.addaudithook(audit)
    try:
        if args.mode == 'stage':
            p.require(args.r5_zip is not None, 'r5_zip_required')
            stage(args.root, args.r5_zip)
        else:
            getattr(Continuation(args.root), args.mode)()
    finally:
        if args.root.exists():
            p.write(args.root/'report'/('read-audit-'+args.mode+'.json'), audit.receipt())


if __name__ == '__main__':
    main()
