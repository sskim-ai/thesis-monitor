"""New full cohort proof under the final-boundary contracts; no deployment."""
import argparse
from pathlib import Path

from scripts.m12ds_r4_r1_reproof import Reproof as R1, stage
from scripts.m12ds_r4_r1_freeze import freeze as freeze_repair
from scripts import m12ds_r4_r4_market as market, m12ds_r4_r4_policy as policy, m12ds_r4_r4_schemas as schemas

CONTRACT = 'm12ds-r4-r4-final-boundary-contract-v1'


class Reproof(R1):
    TYPED_PRESENTATION = True
    POLICY, SCHEMAS, MARKET_OWNER = policy, schemas, market
    INSTRUCTIONS = R1.INSTRUCTIONS.parent / '20260922-m12ds-r4-r4'
    PREFIX = 'M12DS_R4_R4'
    SUCCESS = 'M12DS_R4_R4_CURRENT_INFERENCE_COMPLETE'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode',choices=('repair-freeze','stage','prepare','freeze','run'))
    parser.add_argument('--root',type=Path,required=True)
    args = parser.parse_args()
    if args.mode=='repair-freeze':
        freeze_repair(args.root,instruction_sha='29e5ed3ed69a12a58ee6d938f6c56bbe9c373914',selected_source_contract=CONTRACT)
    elif args.mode=='stage':
        stage(args.root)
    else:
        proof = Reproof(args.root)
        getattr(proof,args.mode)()
        if args.mode=='run' and len(proof.brows)==22:
            from scripts.m12ds_r4_r1_accepted_capture import capture
            capture(proof)


if __name__=='__main__':
    main()
