"""Exactly one diagnostic OpenDART request, never final-proof source evidence."""
import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

import httpx

from app.config import Settings
from app.services.sealed_fresh_dispatch import FreshRequestDescriptor, ProviderPlan, SealedDispatcher
from app.services.sealed_source_transport import CapturedFragment
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest, encoded
from scripts.r9_rev11_live import require_disk_capacity

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def classify(final, root):
    if len(final['attempts']) != 1:
        raise ValueError('diagnostic_exact_one_attempt_required')
    row = final['attempts'][0]
    if row['status'] == 200 and row.get('artifact'):
        try:
            value = json.loads((root / row['artifact']).read_bytes())
        except (ValueError, UnicodeError):
            value = None
        if isinstance(value, dict) and value.get('status') in {'000', '013'}:
            return 'DIRECT_OFFICIAL_API_200'
    meta = row.get('redirect_metadata', {})
    if row['status'] in {301, 302, 307, 308} and meta.get('route_class') == 'EXACT_SAME_API_SEMANTICS':
        # This is evidence for review, not permission to follow or retry.
        return 'SAME_ORIGIN_PATTERN_REQUIRES_PRESEALED_DIRECT_ROUTE'
    return 'R2B_R9_REV12_REV2_OPENDART_REDIRECT_ROUTE_UNRESOLVED'


async def main():
    parser = argparse.ArgumentParser()
    for name in ('reference', 'output', 'validation', 'operating', 'market-proof'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or git('status', '--porcelain'):
        raise ValueError('new_diagnostic_clean_commit_required')
    head = git('rev-parse', 'HEAD')
    validation = json.loads(args.validation.read_bytes())
    if validation.get('head') != head or validation.get('status') != 'PASS':
        raise ValueError('exact_offline_validation_required')
    proof = json.loads(args.market_proof.read_bytes())
    if proof.get('status') != 'PASS' or len(proof.get('observations', [])) != 22 or proof.get('network_calls') != 0:
        raise ValueError('offline_us_market_22_required')
    disk = require_disk_capacity(args.output.parent)
    old = json.loads(args.reference.read_bytes())
    descriptors = [d for d in old['plan']['descriptors'] if d['provider'] == 'opendart'
        and d['subject'] == '000660' and d['page_ordinal'] == 1 and not d['response_binding']]
    if len(descriptors) != 1:
        raise ValueError('exact_existing_dart_discovery_required')
    settings = Settings(_env_file=args.operating / '.env')
    secret = settings.opendart_api_key
    if not secret:
        raise ValueError('configured_dart_key_required')
    run_id = 'rev12-rev2-dart-diagnostic-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    key = 'diagnostic:opendart:000660:list'
    owner = 'app/services/sealed_source_transport.py'
    owner_hash = sha256_bytes((ROOT / owner).read_bytes())
    config = digest([secret])
    d = FreshRequestDescriptor(**(descriptors[0] | dict(generation_id=run_id, logical_request_id=key,
        group_id=key, raw_path=f'raw/{key}/source.body', transient_retry_max=0, max_pages=1,
        max_documents=1, normalizer=owner, owner_sha256=owner_hash, config_identity_sha256=config)))
    root_receipt = old['rev10_receipt']
    plan = ProviderPlan(generation_id=run_id, code_sha=head,
        policy_schema_sha256=digest({'diagnostic': sha256_bytes(Path(__file__).read_bytes()),
            'dispatch': sha256_bytes((ROOT / 'app/services/sealed_fresh_dispatch.py').read_bytes())}),
        rev10_receipt_sha256=sha256_bytes(encoded(root_receipt) + b'\n'),
        frozen_at=datetime.now(timezone.utc), descriptors=(d,), mandatory_roles=(d.role_id,))
    run = SealedDispatcher(plan=plan, root=args.output, rev10_receipt=root_receipt,
        owners={owner: owner_hash}, config_identities={'opendart': config},
        credential_presence={'opendart': True}, secrets=(secret,))
    public = json.loads(d.request_json)
    url = public['url'].replace('%5BREDACTED%5D', secret).replace('[REDACTED]', secret)
    request = httpx.Request(public['method'], url, headers=public['headers'], content=public['body'])
    if git('rev-parse', 'HEAD') != head or git('status', '--porcelain'):
        raise ValueError('diagnostic_code_drift')
    async with httpx.AsyncHTTPTransport(retries=0) as transport:
        final = await run.execute(key, request, transport=transport, normalize=CapturedFragment(d))
    result = dict(generation_id=run_id, code_sha=head, status=classify(final,args.output),
        provider_attempts=len(final['attempts']), model_calls=0, diagnostic_only=True,
        eligible_for_final_source_graph=False, redirects_followed=0, retries=0, disk=disk,
        original_request_unchanged=descriptors[0]['request_json'] == d.request_json,
        original_request_sha256=sha256_bytes(descriptors[0]['request_json'].encode()),
        receipt_sha256=final['receipt_sha256'], http_status=final['attempts'][0]['status'],
        redirect_metadata=final['attempts'][0].get('redirect_metadata'))
    durable_json(args.output / 'diagnostic-summary.json', result, exclusive=True)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    asyncio.run(main())
