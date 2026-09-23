"""User-authorized second fresh R6 run, 600 seconds and at most two transient retries."""
import argparse
from pathlib import Path

from scripts.m12ds_r6_reproof import Reproof as R6, stage
from scripts.m12ds_r3_shadow_reproof import p
from scripts.m12ds_r3_transport import REPEAT_POLICY


def bind_transport_receipt(request):
    request.update(timeout_seconds=600, attempt_limit=3,
                   retries='TWO_IDENTICAL_TYPED_TRANSIENT_RETRIES_ONLY')
    if 'request_sha256' in request:
        identity_keys = ('stage', 'market', 'batch', 'subjects', 'model', 'effort',
                         'timeout_seconds', 'execution_generation_id',
                         'request_composition', 'file_sha256')
        request['request_sha256'] = p.owner.canonical_sha256({key: request[key] for key in identity_keys})
    p.write(Path(request['directory']) / 'request-receipt.json', request)


class Reproof(R6):
    TRANSPORT_POLICY = REPEAT_POLICY
    RETRY_LABEL = 'TWO_IDENTICAL_TYPED_TRANSIENT_RETRIES_ONLY'

    def freeze_stage(self, stage_name, requests):
        # Generic A/B capture precedes the transport owner; bind before stage freeze.
        for request in requests:
            bind_transport_receipt(request)
        super().freeze_stage(stage_name, requests)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('stage', 'prepare', 'freeze', 'run', 'capture'))
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'stage':
        stage(args.root)
        return
    proof = Reproof(args.root)
    if args.mode != 'capture':
        getattr(proof, args.mode)()
    if args.mode in {'run', 'capture'} and len(proof.brows) == 22:
        from scripts.m12ds_r4_r1_accepted_capture import capture
        capture(proof)


if __name__ == '__main__':
    main()
