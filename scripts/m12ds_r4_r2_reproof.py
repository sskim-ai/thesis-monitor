"""R4-R2 orchestration reuses R4-R1 production capture and unchanged R3 policy."""
import argparse
from pathlib import Path

from scripts.m12ds_r4_r1_reproof import Reproof as R1, stage
from scripts.m12ds_r4_r1_freeze import freeze as freeze_repair
from scripts.m12ds_r4_r2_selected_source_quality import CONTRACT


class Reproof(R1):
    INSTRUCTIONS = R1.INSTRUCTIONS.parent / '20260922-m12ds-r4-r2'
    PREFIX = 'M12DS_R4_R2'
    SUCCESS = 'M12DS_R4_R2_CURRENT_INFERENCE_COMPLETE'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('repair-freeze', 'stage', 'prepare', 'freeze', 'run'))
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'repair-freeze':
        freeze_repair(args.root, instruction_sha='9ce5cc1ad14b4756daa8ce1ef5b3be76ded6fe0c',
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
