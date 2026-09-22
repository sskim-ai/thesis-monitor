"""Fresh R4-R1 facts with unchanged R3 policy and an opt-in production capture path."""
import argparse
from pathlib import Path
import shutil
import zipfile

from scripts.m12ds_r3_shadow_reproof import Reproof as R3, p
from scripts import m12ds_r2_shadow_reproof as r2
from scripts import m12ds_r4_r1_market as market
from scripts import m12ds_launch_context as launch


def stage(root):
    p.require(not (root / 'report/preparation.json').exists(), 'NEW_PREPARATION_REQUIRED')
    gate = p.read(root / 'report/source-coverage.json')
    p.require(gate['allow_core_preflight'], 'WHOLE_SOURCE_GATE_REQUIRED')
    blind = root / 'm12dr-live-data-blind-pack.zip'
    with zipfile.ZipFile(blind, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((root / 'snapshot').glob('*.json')):
            archive.write(path, 'BLIND_DATA_PACK/' + path.name)
    p.write(root / 'report/preparation.json', dict(generation_id=gate['source_generation_id'] + '-inference',
        source_generation_id=gate['source_generation_id'], blind_sha256=p.sha(blind),
        old_outputs_read=False, fresh_source=True))
    p.write(root / 'report/host-context.json', launch.context_receipt())
    shutil.copytree(root.parent.parent / 'validation-final', root / 'validation')


class Reproof(R3):
    MARKET_OWNER = market
    INSTRUCTIONS = p.REPO / 'docs/work-instructions/20260922-m12ds-r4-r1'
    PREFIX = 'M12DS_R4_R1'
    SUCCESS = 'M12DS_R4_R1_CURRENT_INFERENCE_COMPLETE'

    def prepare(self):
        r2.Reproof.prepare(self)
        p.write(self.report / 'valuation-source-entitlement.json', {'rows': [r for a in self.authorities.values()
            for r in a['earnings_valuation_receipts']], 'blanket_grants': 0})
        p.write(self.report / 'market-source-parity.json', {m: {k: c[k] for k in (
            'parity_matrix', 'parity_status', 'packet_eligible_refs', 'request_eligible_refs', 'source_market_sha256')}
            for m, packet in self.packets.items() for c in [self.MARKET_OWNER.market_context(packet)]})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('stage', 'prepare', 'freeze', 'run'))
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'stage':
        stage(args.root)
        return
    proof = Reproof(args.root)
    getattr(proof, args.mode)()
    if args.mode == 'run' and len(proof.brows) == 22:
        from scripts.m12ds_r4_r1_accepted_capture import capture
        capture(proof)


if __name__ == '__main__':
    main()
