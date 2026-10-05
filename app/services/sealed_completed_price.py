"""Completed-close slots use the existing sealed transport, never a side channel."""
from pathlib import Path
import json
import httpx

from app.providers.kiwoom_rest_client import KiwoomRestClient
from app.services.completed_price_state import require_plan, required_slot
from app.services.kiwoom_completed_close_owner import OFFICIAL_SPEC_SHA256
from app.services.sealed_fresh_dispatch import ProviderPlan
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_stock_acquisition import StockPlan


def documentation(root, frozen):
    item = frozen.get('completed_close_documentation')
    if not item or item['sha256'] != OFFICIAL_SPEC_SHA256:
        raise ValueError('completed_close_locked_documentation_required')
    path = Path(root) / item['path']
    if (Path(item['path']).is_absolute() or '..' in Path(item['path']).parts
            or any(p.is_symlink() for p in (path, *path.parents))):
        raise ValueError('completed_close_documentation_path')
    raw = path.read_bytes()
    if sha256_bytes(raw) != OFFICIAL_SPEC_SHA256:
        raise ValueError('completed_close_documentation_drift')
    return raw


async def collect_one(*, slot, settings, sealed):
    client = KiwoomRestClient(app_key=settings.kiwoom_app_key, secret_key=settings.kiwoom_secret_key,
        base_url=settings.kiwoom_rest_base_url, timeout_seconds=slot.timeout_seconds, max_retries=0,
        request_interval_seconds=settings.kiwoom_rest_request_interval_seconds, transport=sealed)
    wire = json.loads(slot.request_json)
    # The general client request method is KR-only. Reuse its credential owner
    # but submit the exact US read through the same sealed budgeted transport.
    async with httpx.AsyncClient(base_url=client.base_url, transport=sealed,
                                 timeout=slot.timeout_seconds, follow_redirects=False) as http:
        token = await client._access_token(http)
        await client._rate_limit()
        await http.post('/api/us/mrkcond', json=json.loads(wire['body']), headers={
            'Content-Type': 'application/json;charset=UTF-8', 'api-id': 'usa20590',
            'authorization': 'Bearer ' + token, 'cont-yn': 'N', 'next-key': ''})
    final = sealed.dispatcher.results.get(slot.logical_request_id)
    if final is None:
        raise ValueError('completed_close_attempt_missing')
    return {'receipt_sha256': final['receipt_sha256'], 'status': final['status']}


def replay_source(*, root, frozen, outcome, read):
    plan = ProviderPlan.model_validate(frozen['plan'])
    require_plan(plan, StockPlan.model_validate(frozen['stock_plan']))
    d = required_slot(plan, read)
    final = outcome['logical_results'].get(d.logical_request_id)
    if final is None:
        raise ValueError('completed_close_mandatory_request_not_attempted')
    artifacts = {}
    def capture(relative, expected=None):
        path = Path(root) / relative
        if (Path(relative).is_absolute() or '..' in Path(relative).parts
                or any(p.is_symlink() for p in (path, *path.parents))):
            raise ValueError('completed_price_artifact_path')
        raw = path.read_bytes()
        sha = sha256_bytes(raw)
        if expected and sha != expected:
            raise ValueError('completed_price_artifact_drift')
        artifacts[relative] = raw
        return dict(path=relative, sha256=sha)
    name = 'dispatch/receipts/' + d.logical_request_id + '/final.json'
    final_item = capture(name)
    if json.loads(artifacts[name]) != final:
        raise ValueError('completed_price_outcome_receipt_drift')
    # Preserve and verify every attempted body, including failed HTTP responses.
    for attempt in final['attempts']:
        if attempt.get('artifact'):
            relative = 'dispatch/' + attempt['artifact']
            capture(relative, attempt['raw_sha256'])
            # The pure owner resolves dispatcher-relative artifact names.
            artifacts[attempt['artifact']] = artifacts[relative]
    raw_doc = documentation(root, frozen)
    doc = frozen['completed_close_documentation']
    artifacts[doc['path']] = raw_doc
    return dict(source=dict(provider_plan=plan.model_dump(mode='json'), final=final_item,
                            documentation=doc), artifacts=artifacts)
