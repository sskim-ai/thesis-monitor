"""R3 rev1 fresh same-blind proof; official online retries only, never offline substitution."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import shutil

from scripts.m12ds_r2_shadow_reproof import Reproof as R2, p
from scripts import m12ds_r3_policy as policy, m12ds_r3_schemas as schemas
from scripts import m12ds_r3_market as market, m12ds_r3_valuation_authority as valuation
from scripts import m12ds_r3_transport as transport

BASE = Path('/Users/sskim/Documents/Codex/Reports/20260922-m12ds-r2-policy-calibration')
INSTRUCTIONS = p.REPO / 'docs/work-instructions/20260922-m12ds-r3-rev1'


def stage(root):
    p.require(not root.exists(), 'NEW_R3_ROOT_REQUIRED')
    intake = p.read(INSTRUCTIONS / 'intake.json')
    p.require(p.sha(BASE / 'm12dr-live-data-blind-pack.zip') == intake['blind_sha256'], 'BLIND_IDENTITY_MISMATCH')
    for name in ('source', 'snapshot'):
        shutil.copytree(BASE / name, root / name)
    for name in ('source-coverage.json', 'source-input-binding.json', 'quality-receipts.json', 'issuer-business-projection.json',
                 'blind-leakage-audit.json', 'host-context.json', 'launch-parity.json'):
        (root / 'report').mkdir(exist_ok=True)
        shutil.copy2(BASE / 'report' / name, root / 'report' / name)
    shutil.copy2(BASE / 'm12dr-live-data-blind-pack.zip', root / 'm12dr-live-data-blind-pack.zip')
    p.write(root / 'report/preparation.json', {'generation_id': '20260922-m12ds-r3-rev1-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),
        'blind_sha256': intake['blind_sha256'], 'source_generation_id': intake['source_generation_id'],
        'old_outputs_read': False, 'source_refetch': 0, 'review_attachment_read': False,
        'intake_sha256': p.sha(INSTRUCTIONS / 'intake.json')})


class Reproof(R2):
    POLICY, SCHEMAS, MARKET_OWNER = policy, schemas, market
    INSTRUCTIONS = INSTRUCTIONS
    PREFIX = 'M12DS_R3_REV1'
    SUCCESS = 'M12DS_R3_REV1_RESIDUAL_POLICY_AND_RUNTIME_PASS_READY_FOR_CHAT'

    def __init__(self, root):
        super().__init__(root)
        self.dependencies = {}

    def chain(self, ticker, market_name, atomic):
        super().chain(ticker, market_name, atomic)
        evidence = next(e for e in self.contexts[market_name].model_dump(mode='json')['evidence_packets'] if e['ticker'] == ticker)
        rows, catalog = self.subjects[ticker]['decision_evidence'], self.catalogs[ticker]
        enhanced = valuation.extend_authority(self.authorities[ticker], packet=self.packets[market_name],
                                               evidence_packet=evidence, metadata=rows)
        authority = enhanced['authority']
        expected = p.owner.freeze_source_use_input_expectation(ticker=ticker, source_generation_id=self.source_gen,
            execution_generation_id=self.gen, catalog=catalog, source_metadata=rows, authority_manifest=authority)
        projection = p.owner.build_source_use_projection(ticker=ticker, input_generation_id=self.source_gen,
            execution_generation_id=self.gen, catalog=catalog, authority_manifest=authority, current_input_expectation=expected)
        binding = p.owner.freeze_source_use_binding(projection=projection, authority_manifest=authority, current_input_expectation=expected)
        valid = p.owner.validate_source_use_current_input(projection, binding, expected, ticker=ticker,
            source_generation_id=self.source_gen, execution_generation_id=self.gen, catalog=catalog, source_metadata=rows)
        p.require(valid['status'] == 'PASS', 'R3_EXACT_VALUATION_AUTHORITY_BINDING_FAILED')
        self.authorities[ticker] = enhanced
        self.chains[ticker] = dict(authority=authority, expectation=expected, projection=projection, binding=binding,
                                  validation=valid, source_generation_id=self.source_gen, execution_generation_id=self.gen)

    def capture(self, stage_name, spec, context, schema, prompt):
        receipt = super().capture(stage_name, spec, context, schema, prompt)
        receipt.update(attempt_limit=2, retries='ONE_IDENTICAL_TYPED_TRANSIENT_RETRY_ONLY')
        p.write(Path(receipt['directory']) / 'request-receipt.json', receipt)
        return receipt

    def prepare(self):
        super().prepare()
        p.write(self.report / 'valuation-source-entitlement.json', {'rows': [r for a in self.authorities.values()
                   for r in a['earnings_valuation_receipts']], 'blanket_grants': 0})
        p.write(self.report / 'market-source-parity.json', {m: {k: c[k] for k in (
            'parity_matrix', 'parity_status', 'packet_eligible_refs', 'request_eligible_refs', 'source_market_sha256')}
            for m, packet in self.packets.items() for c in [market.market_context(packet)]})

    def freeze(self):
        super().freeze()
        self.frozen['retry_policy'] = transport.POLICY
        self.frozen['max_processes'] = 52
        self.frozen['retry'] = 'ONE_IDENTICAL_TYPED_TRANSIENT_RETRY_ONLY'
        self.frozen['preflight_audits'] = {n: p.sha(self.report / n) for n in ('valuation-source-entitlement.json', 'market-source-parity.json')}
        p.write(self.report / 'execution-freeze.json', self.frozen)
        self.verify()

    def verify(self):
        super().verify()
        if self.frozen.get('retry_policy') and self.frozen['retry_policy'] != transport.POLICY:
            raise p.SystemicFailure('RETRY_POLICY_DRIFT')
        for name, digest in self.frozen.get('preflight_audits', {}).items():
            if p.sha(self.report / name) != digest:
                raise p.SystemicFailure('SOURCE_PREFLIGHT_AUDIT_DRIFT')
        for name, digest in self.dependencies.items():
            if p.sha(self.root / name) != digest:
                raise p.SystemicFailure('FROZEN_UPSTREAM_DEPENDENCY_DRIFT')

    def before_a(self):
        path = self.root / 'sealed/fresh-core-freeze.json'
        if path.exists():
            self.dependencies['sealed/fresh-core-freeze.json'] = p.sha(path)
            self.cores = {t: policy.canonical_core(c) for t, c in p.read(path)['cores'].items()}
        return super().before_a()

    def before_b(self):
        path = self.root / 'sealed/fresh-a-freeze.json'
        if path.exists():
            self.dependencies['sealed/fresh-a-freeze.json'] = p.sha(path)
        requests = super().before_b()
        material = self.sealed / 'deterministic-materialization.json'
        self.dependencies[str(material.relative_to(self.root))] = p.sha(material)
        return requests

    def preinvoke(self, stage_name, spec, request):
        self.verify()
        src = Path(request['directory'])
        p.require(p.manifest(src) == {**request['files'], 'request-receipt.json': p.sha(src / 'request-receipt.json')}
                  if 'files' in request else True, 'REQUEST_RECEIPT_FILE_DRIFT')
        if stage_name == 'pass-b':
            contexts = p.read(src / 'subject-context.json')
            for t in spec['subjects']:
                self.cores[t] = policy.canonical_core(self.cores[t])
                actual = policy.axis_capability(self.cores[t], self.chains[t], self.catalogs[t], self.subjects[t]['decision_evidence'])
                if actual != self.caps[t] or actual != contexts[t]['r2_policy_capability']:
                    raise p.SystemicFailure('PREINVOKE_CAPABILITY_BINDING_DRIFT')
        p.write(self.report / 'preinvoke' / stage_name / spec['market'] / f"batch-{spec['batch']:02d}.json",
                {'status': 'PASS', 'logical_generation_id': self.gen,
                 'request_sha256': p.owner.canonical_sha256(p.manifest(src)),
                 'upstream_dependencies': self.dependencies, 'canonical_order_owner': 'FROZEN_ATOMIC_CLAIM_ARRAY'})

    def invoke(self, stage_name, spec, request):
        return transport.invoke(self, stage_name, spec, request)

    def bounded(self, stage_name, spec, callback):
        super().bounded(stage_name, spec, callback)
        row = self.ledger[-1]
        if row['status'] == 'PASS' and row['attempts'] == 2:
            row['status'] = 'PASS_AFTER_SINGLE_TRANSIENT_RETRY'
            self.publish()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('stage', 'prepare', 'freeze', 'run'))
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    stage(args.root) if args.mode == 'stage' else getattr(Reproof(args.root), args.mode)()


if __name__ == '__main__':
    main()
