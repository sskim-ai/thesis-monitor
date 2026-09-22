"""New current R6 source/message proof under the unchanged accepted stock policy."""
import argparse
from pathlib import Path

from scripts.m12ds_r4_r4_reproof import Reproof as Previous
from scripts.m12ds_r4_r1_reproof import stage
from scripts.m12ds_r4_r1_freeze import freeze as freeze_repair
from scripts import m12ds_r6_market as market


class Reproof(Previous):
    MARKET_OWNER = market
    INSTRUCTIONS = Previous.INSTRUCTIONS.parent / '20260922-m12ds-r6'
    PREFIX = 'M12DS_R6'
    SUCCESS = 'M12DS_R6_CURRENT_INFERENCE_COMPLETE'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=('repair-freeze','stage','prepare','freeze','run','capture'))
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    if args.mode=='repair-freeze':
        freeze_repair(args.root,instruction_sha='cfb6f939858a2b87be70c4f46a4b51eaf068aee5',
                      selected_source_contract='m12ds-r6-message-information-coverage-v1')
    elif args.mode=='stage':
        stage(args.root)
    else:
        proof=Reproof(args.root)
        if args.mode!='capture':
            getattr(proof,args.mode)()
        if args.mode in {'run','capture'} and len(proof.brows)==22:
            from scripts.m12ds_r4_r1_accepted_capture import capture
            capture(proof)


if __name__=='__main__':
    main()
