"""Zero-inference source, authority, serializer, and policy probe for R3."""
import argparse
from pathlib import Path

from scripts import m12ds_r3_policy, m12ds_r3_schemas
from scripts.m12ds_r2_offline_proof import run
from scripts.m12ds_r3_shadow_reproof import Reproof


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    run(args.root, proof_class=Reproof, policy=m12ds_r3_policy, schemas=m12ds_r3_schemas)
