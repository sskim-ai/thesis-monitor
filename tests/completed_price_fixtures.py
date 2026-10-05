"""Fictional request/attempt bytes; only the immutable public spec is real."""
from datetime import timedelta
from functools import lru_cache
import gzip
import json
from pathlib import Path

import httpx

from app.services.sealed_fresh_dispatch import FreshRequestDescriptor, ProviderPlan, wire_identity
from app.services.unified_snapshot_contract import digest, encoded
from app.services.unified_run_artifacts import sha256_bytes


@lru_cache
def official_spec():
    raw = gzip.decompress(Path(__file__).with_name('fixtures').joinpath('kiwoom_completed_close_official.json.gz').read_bytes())
    assert sha256_bytes(raw) == '42a7b3912c9d9588c83bdc2db7779c8d2e038703a2b5562e54ef46ae905cba79'
    return raw


def source(plan, security, *, value=105, kind='available'):
    read = next(r for r in plan.reads if r.subject == security['ticker'] and r.role == 'adjusted_daily')
    key = 'completed_close:' + read.subject
    wire = httpx.Request('POST', 'https://api.kiwoom.com/api/us/mrkcond',
        headers={'api-id': 'usa20590', 'Content-Type': 'application/json'},
        json=dict(stex_tp=read.exchange, stk_cd=read.subject, base_dt=read.latest_completed_session.replace('-', '')))
    d = FreshRequestDescriptor(generation_id=plan.run_id, logical_request_id=key, provider='kiwoom',
        source_family='completed_close', role_id=key, market='us', subject=read.subject,
        endpoint_operation='usa20590', request_json=wire_identity(wire), target_period=read.latest_completed_session,
        mandatory=True, group_id=key, page_ordinal=1, max_pages=1, document_ordinal=1, max_documents=1,
        timeout_seconds=600, transient_retry_max=0, raw_path='raw/' + key + '/source.body',
        normalizer='app/services/sealed_source_transport.py', consumer_role=key, owner_sha256='1'*64, config_identity_sha256='2'*64)
    provider = ProviderPlan(generation_id=plan.run_id, code_sha=plan.implementation_sha,
        policy_schema_sha256='3'*64, rev10_receipt_sha256='4'*64, frozen_at=plan.frozen_at,
        descriptors=(d,), mandatory_roles=(key,))
    binding = dict(generation_id=plan.run_id, logical_request_id=key, descriptor_sha256=d.descriptor_sha256,
        request_sha256=d.request_semantic_sha256, plan_sha256=provider.plan_sha256, role=key,
        resolved_request_sha256=sha256_bytes(d.request_json.encode()), parent_receipts={})
    row = dict(dt=read.latest_completed_session.replace('-', ''), cur_prc=str(value),
        open_pric=str(value), high_pric=str(value + 1), low_pric=str(value - 1))
    body = dict(return_code=0, result_list=[row])
    if kind == 'missing':
        body['result_list'] = []
    elif kind == 'integrity':
        row['high_pric'] = str(value - 1)
    elif kind == 'field_missing':
        row.pop('cur_prc')
    elif kind == 'provider_failed':
        body['return_code'] = 1
    raw = encoded(body)
    at = plan.frozen_at + timedelta(seconds=1)
    end = at + timedelta(seconds=1)
    artifact = 'receipts/' + key + '/attempt-1.body'
    attempt = dict(binding, attempt=1, started_at=at.isoformat(), finished_at=end.isoformat(),
        timeout_seconds=600, retry=False, transient=False, status=302 if kind == 'http' else 200,
        error=None, raw_sha256=sha256_bytes(raw), artifact=artifact)
    artifacts = {'price-documentation': official_spec()}
    if kind == 'transport':
        attempt.update(status=None, error='ConnectTimeout', raw_sha256=None)
        attempt.pop('artifact')
    else:
        artifacts[artifact] = raw
    final = dict(binding, status='FAILED' if kind in {'transport', 'http', 'provider_failed'} else 'PASS',
        started_at=at.isoformat(), finished_at=end.isoformat(), attempts=[attempt],
        raw_sha256=attempt['raw_sha256'])
    final['receipt_sha256'] = digest(final)
    artifacts['price-final'] = encoded(final)
    source = dict(provider_plan=provider.model_dump(mode='json'),
        final=dict(path='price-final', sha256=sha256_bytes(artifacts['price-final'])),
        documentation=dict(path='price-documentation', sha256=sha256_bytes(artifacts['price-documentation'])))
    return source, artifacts


def reseal_final(source, artifacts, mutate):
    final = json.loads(artifacts[source['final']['path']])
    mutate(final)
    final.pop('receipt_sha256')
    final['receipt_sha256'] = digest(final)
    artifacts[source['final']['path']] = encoded(final)
    source['final']['sha256'] = sha256_bytes(encoded(final))
