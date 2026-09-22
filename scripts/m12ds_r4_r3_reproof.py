"""R4-R3 exact foreign source extension; unchanged R3 inference and R4-R1 capture."""
import argparse
from pathlib import Path

from app.services.sec_foreign_comparison_service import CONTRACT
from scripts.m12ds_r4_r1_reproof import Reproof as R1, stage
from scripts.m12ds_r4_r1_freeze import freeze as freeze_repair


class Reproof(R1):
    INSTRUCTIONS = R1.INSTRUCTIONS.parent / '20260922-m12ds-r4-r3'
    PREFIX = 'M12DS_R4_R3'
    SUCCESS = 'M12DS_R4_R3_CURRENT_INFERENCE_COMPLETE'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('repair-freeze', 'stage', 'prepare', 'freeze', 'run'))
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'repair-freeze':
        freeze_repair(args.root, instruction_sha='f74dd137ff560bb8e97be48df7d6f1e9e38b12ff',
                      selected_source_contract=CONTRACT)
    elif args.mode == 'stage':
        stage(args.root)
    else:
        proof = Reproof(args.root)
        getattr(proof, args.mode)()
        if args.mode == 'run' and len(proof.brows) == 22:
            from scripts.m12ds_r4_r1_accepted_capture import capture
            capture(proof)


if __name__ == '__main__':
    main()
