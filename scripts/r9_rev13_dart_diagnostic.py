"""One sealed current-owner list diagnostic, never final-proof source evidence."""
import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import subprocess

import httpx

from app.config import Settings
from app.services.bounded_financial_acquisition import make_plan
from app.services.sealed_financial_slots import financial_slots
from app.services.sealed_fresh_dispatch import ProviderPlan, wire_identity
from app.services.sealed_opendart_contract import header_contract
from app.services.secret_safe_redirect import redirect_metadata
from app.services.unified_run_artifacts import durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest, encoded
from scripts.r9_rev11_live import exact_rev10_receipt, require_disk_capacity

ROOT = Path(__file__).resolve().parents[1]
STOP = 'R2B_R9_REV13_OPENDART_HEADER_ROUTE_UNRESOLVED'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def classify(status, raw):
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        value = None
    valid = (status == 200 and isinstance(value, dict) and value.get('status') in {'000', '013'}
             and isinstance(value.get('message'), str) and bool(value['message'].strip()))
    return ('PASS' if valid else STOP), value if isinstance(value, dict) else None


async def diagnose_once(descriptor, secret, transport):
    public = json.loads(descriptor.request_json)
    if public['headers'] != [list(pair) for pair in header_contract()['headers']]:
        raise ValueError('diagnostic_exact_header_contract_required')
    request = httpx.Request(public['method'], public['url'].replace('[REDACTED]', secret),
                           headers=public['headers'], content=public['body'])
    if wire_identity(request, (secret,)) != descriptor.request_json or descriptor.transient_retry_max != 0:
        raise ValueError('diagnostic_exact_wire_one_attempt_required')
    request.extensions['timeout'] = {k: float(descriptor.timeout_seconds) for k in ('connect', 'read', 'write', 'pool')}
    async def receive():
        response = await transport.handle_async_request(request)
        try:
            await response.aread()
        finally:
            await response.aclose()
        return response
    try:
        response = await asyncio.wait_for(receive(), timeout=descriptor.timeout_seconds)
    except (httpx.HTTPError, TimeoutError) as exc:
        return dict(status=STOP, http_status=None, content_type=None, json_status=None,
            json_message=None, response_sha256=None, redirect_metadata=None, error_class=type(exc).__name__)
    status, value = classify(response.status_code, response.content)
    if secret.encode() in response.content:
        status, value = STOP, None
    def safe(value):
        if not isinstance(value, str):
            return None
        return '[REDACTED]' if secret in value or 'http://' in value or 'https://' in value else value[:240]
    content_type = response.headers.get('content-type', '')
    return dict(status=status, http_status=response.status_code,
        content_type=safe(content_type) if content_type.startswith(('application/json', 'text/html', 'text/plain')) else None,
        json_status=safe(value.get('status')) if value else None,
        json_message=safe(value.get('message')) if value else None,
        response_sha256=sha256_bytes(response.content),
        redirect_metadata=redirect_metadata(request, response, (secret,)).model_dump(mode='json')
            if not 200 <= response.status_code < 300 else None)


async def run(args):
    if args.output.exists() or git('status', '--porcelain'):
        raise ValueError('new_diagnostic_clean_commit_required')
    head = git('rev-parse', 'HEAD')
    validation = json.loads(args.validation.read_bytes())
    if validation.get('head') != head or validation.get('status') != 'PASS':
        raise ValueError('exact_offline_validation_required')
    disk = require_disk_capacity(args.output.parent)
    settings = Settings(_env_file=args.operating / '.env')
    secret = settings.opendart_api_key
    if not secret:
        raise ValueError('configured_dart_key_required')
    settings_hash = digest(settings.model_dump(mode='json'))
    db = args.operating / 'data/thesis_monitor.sqlite3'
    with sqlite3.connect(f'{db.as_uri()}?mode=ro', uri=True) as connection:
        connection.execute('PRAGMA query_only=ON')
        connection.row_factory = sqlite3.Row
        rows = connection.execute('SELECT * FROM securitymaster WHERE ticker=?', ('000660',)).fetchall()
        if len(rows) != 1 or rows[0]['corp_code'] != '00164779':
            raise ValueError('current_representative_identity_required')
        security = dict(rows[0])
    at = datetime.now(timezone.utc)
    run_id = 'rev13-dart-diagnostic-' + at.strftime('%Y%m%dT%H%M%SZ')
    policy = make_plan(security, market='kr', cutoff=at, run_id=run_id, all_subjects_fresh=True)
    owner = 'app/services/sealed_financial_reader.py'
    owner_hash = sha256_bytes((ROOT / owner).read_bytes())
    config = digest([secret])
    slots = financial_slots(policy, owner=owner, owner_sha256=owner_hash, config_sha256=config)
    d = slots[0].model_copy(update={'transient_retry_max': 0})
    public = json.loads(d.request_json)
    contract = header_contract()
    if public['headers'] != [list(pair) for pair in contract['headers']] or d.response_binding:
        raise ValueError('exact_sealed_header_contract_required')
    root_receipt = exact_rev10_receipt(args.rev10_receipt)
    plan = ProviderPlan(generation_id=run_id, code_sha=head, policy_schema_sha256=digest({
        'diagnostic': sha256_bytes(Path(__file__).read_bytes()), 'header_contract': contract,
        'dispatch': sha256_bytes((ROOT / 'app/services/sealed_fresh_dispatch.py').read_bytes())}),
        rev10_receipt_sha256=sha256_bytes(encoded(root_receipt) + b'\n'), frozen_at=at,
        descriptors=(d,), mandatory_roles=(d.role_id,))
    admission = plan.admission(rev10_receipt=root_receipt, owners={owner: owner_hash},
        config_identities={'opendart': config}, credential_presence={'opendart': True})
    if not admission['live_dispatch_allowed']:
        raise ValueError('diagnostic_plan_not_admitted')
    if (git('rev-parse', 'HEAD') != head or git('status', '--porcelain')
            or digest(Settings(_env_file=args.operating / '.env').model_dump(mode='json')) != settings_hash):
        raise ValueError('diagnostic_code_config_drift')
    durable_json(args.output / 'diagnostic-started.json', dict(generation_id=run_id, code_sha=head,
        descriptor_sha256=d.descriptor_sha256, header_contract_sha256=digest(contract),
        maximum_attempts=1, retries=0, redirects_followed=0, diagnostic_only=True), exclusive=True)
    async with httpx.AsyncHTTPTransport(retries=0) as transport:
        response = await diagnose_once(d, secret, transport)
    result = dict(generation_id=run_id, code_sha=head, **response,
        provider_attempts=1, model_calls=0, diagnostic_only=True, eligible_for_final_source_graph=False,
        redirects_followed=0, retries=0, disk=disk, raw_body_persisted=False,
        header_contract=contract, header_contract_sha256=digest(contract),
        descriptor_sha256=d.descriptor_sha256, source_policy_sha256=digest(policy))
    durable_json(args.output / 'diagnostic-summary.json', result, exclusive=True)
    print(json.dumps(result, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    for name in ('output', 'validation', 'operating', 'rev10-receipt'):
        parser.add_argument('--' + name, type=Path, required=True)
    asyncio.run(run(parser.parse_args()))


if __name__ == '__main__':
    main()
