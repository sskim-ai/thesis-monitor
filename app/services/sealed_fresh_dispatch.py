"""Opt-in sealed request/response-slot boundary, never production registration."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Literal
from urllib.parse import urlsplit

import httpx
from pydantic import Field, model_validator

from app.services.bounded_financial_acquisition import retryable
from app.services.fresh_source_run_contract import MAX_KR_REQUEST_PAGES
from app.services.sealed_response_binding import (
    ResponseBinding, SlotNotSelected, binding_owner_hash, resolve_response_binding,
)
from app.services.unified_live_source_transport import BoundedTransport, SourceSafetyStop
from app.services.unified_run_artifacts import durable_bytes, durable_json, sha256_bytes
from app.services.unified_snapshot_contract import ContractModel, digest, encoded
from app.services.unified_source_observer import _secret_field
from app.services.secret_safe_redirect import redirect_metadata

HOSTS = {
    'kiwoom': {'api.kiwoom.com'}, 'sec_edgar': {'data.sec.gov', 'www.sec.gov'},
    'opendart': {'opendart.fss.or.kr'}, 'fred': {'api.stlouisfed.org'},
    'eia': {'api.eia.gov'}, 'ecos': {'ecos.bok.or.kr'},
    'krx_night_futures': {'data-dbg.krx.co.kr'},
    'finnhub': {'finnhub.io'}, 'google_news_rss': {'news.google.com'}, 'naver_news': {'openapi.naver.com'},
}
HASH = r'^[a-f0-9]{64}$'
ID = r'^[A-Za-z0-9_.:-]+$'


def read_route(provider, method, path):
    routes = {
        'kiwoom': r'(?:/api/(?:us/(?:chart|stkinfo)|dostk/(?:chart|sect|mrkcond))|/oauth2/token)',
        'sec_edgar': r'/(?:submissions/CIK\d{10}\.json|api/xbrl/companyfacts/CIK\d{10}\.json|Archives/edgar/data/\d+/\d{18}/[A-Za-z0-9_.-]+)',
        'opendart': r'/api/(?:list|fnlttSinglAcntAll)\.json',
        'fred': r'/fred/series/observations', 'eia': r'/v2/seriesid/[A-Z0-9.]+',
        'ecos': r'/api/KeyStatisticList/(?:\[REDACTED\]|%5BREDACTED%5D)/json/kr/1/100',
        'krx_night_futures': r'/svc/apis/drv/fut_bydd_trd',
        'finnhub': r'/api/v1/stock/metric', 'google_news_rss': r'/rss/search',
        'naver_news': r'/v1/search/news\.json',
    }
    return method == ('POST' if provider == 'kiwoom' else 'GET') and bool(re.fullmatch(routes[provider], path))


def stamp():
    return datetime.now(timezone.utc).isoformat()


def wire_identity(request, secrets=()):
    """Bind all explicit headers and bytes; redact only known credential values."""
    redact = BoundedTransport(root=None, maximum_logical=1, guard=lambda: None, secrets=secrets)
    body = request.content.decode('utf-8')
    if body and request.headers.get('content-type', '').startswith('application/json'):
        body = encoded(json.loads(body)).decode()
    public = dict(method=request.method, url=str(request.url),
        headers=sorted([k, v] for k, v in request.headers.items()
            if k not in {'host', 'content-length', 'accept-encoding', 'connection'}
            and not (k == 'accept' and v == '*/*')
            and not (k == 'user-agent' and v == 'python-httpx/' + httpx.__version__)),
        body=body)
    return encoded(redact.public_request(public)).decode()


class FreshRequestDescriptor(ContractModel):
    generation_id: str = Field(pattern=ID)
    logical_request_id: str = Field(pattern=ID)
    provider: str
    source_family: str = Field(min_length=1)
    role_id: str = Field(min_length=1)
    market: Literal['us', 'kr', 'global']
    subject: str = Field(min_length=1)
    endpoint_operation: str = Field(min_length=1)
    request_json: str
    target_period: str = Field(min_length=1)
    mandatory: bool
    group_id: str = Field(pattern=ID)
    page_ordinal: int = Field(ge=1)
    max_pages: int = Field(ge=1, le=100)
    document_ordinal: int = Field(ge=1)
    max_documents: int = Field(ge=1, le=128)
    timeout_seconds: int = Field(ge=1, le=600)
    transient_retry_max: int = Field(ge=0, le=2)
    raw_path: str
    normalizer: str = Field(min_length=1)
    consumer_role: str = Field(min_length=1)
    owner_sha256: str = Field(pattern=HASH)
    config_identity_sha256: str = Field(pattern=HASH)
    response_binding: ResponseBinding | None = None

    @model_validator(mode='after')
    def exact(self):
        value = json.loads(self.request_json)
        if set(value) != {'method', 'url', 'headers', 'body'} or encoded(value).decode() != self.request_json:
            raise ValueError('canonical_exact_request_required')
        url = urlsplit(value['url'])
        if (self.provider not in HOSTS or url.scheme != 'https' or url.netloc not in HOSTS[self.provider]
                or url.fragment or url.username or value['method'] not in {'GET', 'POST'}):
            raise ValueError('undeclared_provider_or_route')
        if not read_route(self.provider, value['method'], url.path):
            raise ValueError('nonreadonly_or_undeclared_operation')
        if self.page_ordinal > self.max_pages or self.document_ordinal > self.max_documents:
            raise ValueError('descriptor_page_document_budget_exceeded')
        path = Path(self.raw_path)
        if path.is_absolute() or not path.parts or '..' in path.parts:
            raise ValueError('relative_raw_artifact_required')
        if path != Path('raw') / self.logical_request_id / 'source.body':
            raise ValueError('unique_descriptor_raw_path_required')
        if self.response_binding:
            rule = self.response_binding
            provider = 'kiwoom' if rule.kind.startswith('KIWOOM_') else 'sec_edgar' if rule.kind.startswith('SEC_') else 'opendart'
            if provider != self.provider:
                raise ValueError('binding_provider_mismatch')
            if provider != 'kiwoom':
                policy = json.loads(rule.policy_json)
                if policy['run_id'] != self.generation_id or policy['ticker'] != self.subject:
                    raise ValueError('binding_generation_subject_mismatch')
        return self

    @property
    def request_semantic_sha256(self):
        return (digest({'template': self.request_json, 'binding': self.response_binding.model_dump(mode='json')})
                if self.response_binding else sha256_bytes(self.request_json.encode()))

    @property
    def descriptor_sha256(self):
        return digest(self.model_dump(mode='json'))

    @property
    def max_transport_attempts(self):
        return 1 + self.transient_retry_max


class ProviderPlan(ContractModel):
    generation_id: str = Field(pattern=ID)
    code_sha: str = Field(pattern=r'^[a-f0-9]{40}$')
    policy_schema_sha256: str = Field(pattern=HASH)
    rev10_receipt_sha256: str = Field(pattern=HASH)
    frozen_at: datetime
    descriptors: tuple[FreshRequestDescriptor, ...]
    mandatory_roles: tuple[str, ...]
    unresolved_roles: tuple[str, ...] = ()
    binding_owner_sha256: str | None = Field(default=None, pattern=HASH)

    @model_validator(mode='after')
    def closed(self):
        if self.frozen_at.utcoffset() is None or not self.mandatory_roles:
            raise ValueError('plan_time_roles_required')
        if len(set(self.mandatory_roles)) != len(self.mandatory_roles):
            raise ValueError('duplicate_mandatory_role')
        for attr in ('logical_request_id', 'raw_path', 'request_semantic_sha256'):
            vals = [getattr(d, attr) for d in self.descriptors]
            if len(vals) != len(set(vals)):
                raise ValueError('duplicate_descriptor_identity')
        groups = {}
        for d in self.descriptors:
            if d.generation_id != self.generation_id:
                raise ValueError('descriptor_generation_mismatch')
            groups.setdefault(d.group_id, []).append(d)
        for group in groups.values():
            if len({(d.max_pages, d.max_documents, d.provider, d.role_id) for d in group}) != 1:
                raise ValueError('inconsistent_group_budget')
            pairs = {(d.document_ordinal, d.page_ordinal) for d in group}
            if len(pairs) != len(group):
                raise ValueError('duplicate_page_document')
            for doc in {d.document_ordinal for d in group}:
                pages = sorted(d.page_ordinal for d in group if d.document_ordinal == doc)
                if pages != list(range(1, len(pages) + 1)):
                    raise ValueError('descriptor_page_chain_incomplete')
        seen = {}
        for d in self.descriptors:
            if d.response_binding:
                if not self.binding_owner_sha256:
                    raise ValueError('response_binding_owner_required')
                rule = d.response_binding
                if any(p not in seen for p in rule.parents):
                    raise ValueError('binding_parent_must_precede_slot')
                parents = [seen[p] for p in rule.parents]
                exchange_discovery = rule.kind == 'KIWOOM_US_EXCHANGE' and all(
                    p.provider == 'kiwoom' and p.role_id == 'us_market:exchange_discovery'
                    and p.endpoint_operation == 'usa10099' for p in parents)
                if not exchange_discovery and any((p.provider, p.subject, p.role_id) != (d.provider, d.subject, d.role_id) for p in parents):
                    raise ValueError('binding_parent_scope_mismatch')
                if rule.kind == 'KIWOOM_CONTINUATION':
                    p = parents[0]
                    if (p.group_id, p.page_ordinal + 1, p.document_ordinal) != (d.group_id, d.page_ordinal, d.document_ordinal):
                        raise ValueError('binding_nonadjacent_page')
                if rule.kind.startswith('SEC_') or rule.kind.startswith('DART_'):
                    policy = json.loads(rule.policy_json)
                    expected = (f'https://data.sec.gov/submissions/CIK{policy["issuer"]}.json'
                                if d.provider == 'sec_edgar' else 'https://opendart.fss.or.kr/api/list.json')
                    if str(httpx.URL(json.loads(parents[0].request_json)['url']).copy_with(query=None)) != expected:
                        raise ValueError('binding_discovery_parent_mismatch')
            seen[d.logical_request_id] = d
        return self

    @property
    def plan_sha256(self):
        return digest(self.model_dump(mode='json'))

    def admission(self, *, rev10_receipt, owners, config_identities, credential_presence):
        # Root receipt identity is checked, never recomputed with altered policies.
        issues = list(self.unresolved_roles)
        if self.binding_owner_sha256 is not None and self.binding_owner_sha256 != binding_owner_hash():
            issues.append('response_binding_owner_drift')
        if (sha256_bytes(encoded(rev10_receipt) + b'\n') != self.rev10_receipt_sha256
                or rev10_receipt.get('status') != 'PASS' or rev10_receipt.get('dispatch_allowed') is not True):
            issues.append('rev10_root_receipt_mismatch')
        covered = {d.consumer_role for d in self.descriptors if d.mandatory}
        issues += ['missing_role:' + r for r in self.mandatory_roles if r not in covered]
        for d in self.descriptors:
            if owners.get(d.normalizer) != d.owner_sha256:
                issues.append('owner_binding:' + d.logical_request_id)
            if config_identities.get(d.provider) != d.config_identity_sha256:
                issues.append('config_binding:' + d.logical_request_id)
            if credential_presence.get(d.provider) is not True:
                issues.append('credential_presence:' + d.provider)
        budget = {}
        for d in self.descriptors:
            row = budget.setdefault(d.provider, dict(logical=0, maximum_transport_attempts=0))
            row['logical'] += 1
            row['maximum_transport_attempts'] += d.max_transport_attempts
        return dict(status='R2B_R9_REV11_PROVIDER_PLAN_GAP' if issues else 'R2B_R9_REV11_FINAL_PROVIDER_PLAN_PASS',
            live_dispatch_allowed=not issues, plan_sha256=self.plan_sha256,
            descriptor_count=len(self.descriptors), gaps=sorted(set(issues)), budgets=budget,
            total_theoretical_max=sum(v['maximum_transport_attempts'] for v in budget.values()))


def kr_request_budget(*, global_cap, row_count, verified_minimum_rows_per_page,
                      consumer_complete, single_response=False):
    """An estimate or global capability is not a guaranteed consumer page bound."""
    base = dict(global_configured_cap=global_cap, accepted_bound=MAX_KR_REQUEST_PAGES,
                production_setting_modified=False)
    if single_response:
        required = 1
    elif (not consumer_complete or type(row_count) is not int or row_count < 1
          or type(verified_minimum_rows_per_page) is not int or verified_minimum_rows_per_page < 1):
        return dict(base, status='PAGE_REQUIREMENT_UNPROVEN', required_max_pages=None)
    else:
        required = (row_count + verified_minimum_rows_per_page - 1) // verified_minimum_rows_per_page
    return dict(base, required_max_pages=required,
        status='PASS' if required <= min(global_cap, MAX_KR_REQUEST_PAGES)
            else 'R2B_R9_REV11_KR_PAGE_BUDGET_INSUFFICIENT')


class SealedDispatcher:
    """One transport call per attempt; receipt first, no redirects or recursion.

The caller must provide the exact sealed request and a registered source owner.
The live source controller has no route here until the *whole* plan is admitted.
"""
    def __init__(self, *, plan, root, rev10_receipt, owners, config_identities, credential_presence, secrets=()):
        self.plan = ProviderPlan.model_validate(plan)
        self.admission = self.plan.admission(rev10_receipt=rev10_receipt,
            owners=owners, config_identities=config_identities, credential_presence=credential_presence)
        if not self.admission['live_dispatch_allowed']:
            raise ValueError('whole_provider_plan_not_admitted')
        self.root = Path(root)
        if self.root.exists() or any(p.is_symlink() for p in self.root.parents):
            raise ValueError('new_nonsymlink_dispatch_root_required')
        self.secrets = tuple(s for s in secrets if s)
        self.used = set()
        self.results = {}
        self.halted = False
        self.credential_response = None
        durable_json(self.root / 'plan.json', self.plan.model_dump(mode='json'), exclusive=True)
        durable_json(self.root / 'admission.json', self.admission, exclusive=True)

    def _save(self, path, data, *, raw=False):
        path = self.root / path
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise SourceSafetyStop('dispatch_artifact_symlink')
        (durable_bytes if raw else durable_json)(path, data, exclusive=True)

    def resolve(self, logical_id):
        """Resolve only from this dispatcher's immutable, verified parent receipts."""
        d = next(d for d in self.plan.descriptors if d.logical_request_id == logical_id)
        if not d.response_binding:
            return d.request_json, {}, None
        if self.plan.binding_owner_sha256 != binding_owner_hash():
            raise SourceSafetyStop('response_binding_owner_drift')
        parents = {}
        receipts = {}
        for key in d.response_binding.parents:
            final = self.results.get(key)
            if final is None:
                raise SourceSafetyStop('binding_parent_not_executed')
            receipts[key] = final['receipt_sha256']
            parents[key] = _binding_parent(self.root, self.plan, key, final['receipt_sha256'])
        resolved, selected = resolve_response_binding(d.request_json, d.response_binding, parents)
        if d.response_binding.kind == 'KIWOOM_CONTINUATION':
            cursor = dict(json.loads(resolved)['headers'])['next-key']
            previous = d.response_binding.parents[0]
            while previous:
                row = next(p for p in self.plan.descriptors if p.logical_request_id == previous)
                proof = _binding_parent(self.root, self.plan, previous, self.results[previous]['receipt_sha256'])
                if cursor == dict(proof['request']['headers']).get('next-key'):
                    raise SourceSafetyStop('binding_cursor_cycle')
                previous = row.response_binding.parents[0] if row.response_binding else None
        return resolved, receipts, selected

    async def execute(self, logical_id, request, *, transport, normalize):
        if self.halted:
            raise SourceSafetyStop('systemic_stop_latched')
        if encoded(json.loads((self.root / 'plan.json').read_bytes())) != encoded(self.plan.model_dump(mode='json')):
            raise SourceSafetyStop('sealed_plan_drift')
        choices = [d for d in self.plan.descriptors if d.logical_request_id == logical_id]
        if len(choices) != 1 or logical_id in self.used:
            raise SourceSafetyStop('unplanned_or_repeated_request')
        d = choices[0]
        credential_exchange = json.loads(d.request_json)['url'] == 'https://api.kiwoom.com/oauth2/token'
        if credential_exchange and (d.consumer_role != 'kiwoom:credential_exchange' or d.endpoint_operation != 'credential_exchange'):
            raise SourceSafetyStop('credential_exchange_role_required')
        resolved, parents, selected = self.resolve(logical_id)
        if wire_identity(request, self.secrets) != resolved:
            raise SourceSafetyStop('request_not_exact_descriptor')
        if normalize.identity != (d.normalizer, d.owner_sha256):
            raise SourceSafetyStop('normalizer_identity_mismatch')
        self.used.add(logical_id)
        base = Path('receipts') / logical_id
        binding = dict(generation_id=d.generation_id, logical_request_id=logical_id,
            descriptor_sha256=d.descriptor_sha256, request_sha256=d.request_semantic_sha256,
            plan_sha256=self.plan.plan_sha256, role=d.consumer_role,
            resolved_request_sha256=sha256_bytes(resolved.encode()), parent_receipts=parents)
        self._save(base / 'plan.json', dict(binding, descriptor=d.model_dump(mode='json')))
        self._save(base / 'resolved-request.json', dict(binding, request=json.loads(resolved), selected=selected))
        started = stamp()
        self._save(base / 'start.json', dict(binding, started_at=started))
        final = dict(binding, started_at=started, status='FAILED', attempts=[], raw_sha256=None)
        original = digest([str(request.url), list(request.headers.multi_items()), request.content.hex()])
        try:
            for attempt in range(1, d.max_transport_attempts + 1):
                if original != digest([str(request.url), list(request.headers.multi_items()), request.content.hex()]):
                    raise SourceSafetyStop('retry_request_changed')
                row = dict(binding, attempt=attempt, started_at=stamp(), timeout_seconds=d.timeout_seconds,
                           status=None, error=None, raw_sha256=None, retry=attempt > 1)
                self._save(base / f'attempt-{attempt}.start.json', row)
                response = None
                raw = None
                retry = False
                request.extensions['timeout'] = {k: float(d.timeout_seconds) for k in ('connect', 'read', 'write', 'pool')}
                async def receive():
                    result = await transport.handle_async_request(request)
                    try:
                        await result.aread()
                    finally:
                        await result.aclose()
                    return result
                try:
                    response = await asyncio.wait_for(receive(), timeout=d.timeout_seconds)
                    raw = response.content
                    row['status'] = response.status_code
                    row['response_headers'] = {k: v for k, v in response.headers.items() if k in {'cont-yn', 'next-key'}}
                    if not 200 <= response.status_code < 300:
                        row['redirect_metadata'] = redirect_metadata(request, response, self.secrets).model_dump(mode='json')
                    if credential_exchange:
                        # The actual credential body stays in memory. Its hash
                        # and a minimal sanitized receipt are the only artifacts.
                        row['credential_body_sha256'] = sha256_bytes(raw)
                        row['credential_body_exported'] = False
                        payload = response.json() if response.status_code == 200 else {}
                        token = payload.get('token') if isinstance(payload, dict) else None
                        if token and response.status_code == 200:
                            self.credential_response = response
                            self.secrets = (*self.secrets, token)
                        raw = encoded(dict(exchange_succeeded=bool(token), http_status=response.status_code))
                        if response.status_code == 200 and not token:
                            row['error'] = 'CREDENTIAL_RESPONSE_INVALID'
                    try:
                        secret_field = _secret_field(json.loads(raw))
                    except (ValueError, UnicodeDecodeError):
                        secret_field = False
                    if (secret_field or any(s.encode() in raw for s in self.secrets)
                            or any(s in encoded(row['response_headers']).decode() for s in self.secrets)):
                        raw = None
                        row['error'] = 'SECRET_IN_SOURCE_BODY'
                        row['response_headers'] = {}
                    else:
                        row['raw_sha256'] = sha256_bytes(raw)
                        row['artifact'] = str(base / f'attempt-{attempt}.body')
                        self._save(row['artifact'], raw, raw=True)
                    retry = retryable(status=response.status_code)
                    if d.provider == 'opendart' and response.status_code == 200 and raw is not None:
                        try:
                            row['provider_status'] = json.loads(raw).get('status')
                        except (ValueError, AttributeError):
                            row['provider_status'] = None
                        retry = retryable(provider_status=row.get('provider_status'))
                except (httpx.HTTPError, TimeoutError) as exc:
                    row['error'] = type(exc).__name__
                    retry = retryable(exc=exc)
                row['finished_at'] = stamp()
                row['transient'] = retry
                self._save(base / f'attempt-{attempt}.json', row)
                final['attempts'].append(row)
                if row['error'] in {'SECRET_IN_SOURCE_BODY', 'CREDENTIAL_RESPONSE_INVALID'} or row['status'] in {401, 403}:
                    raise SourceSafetyStop('source_secret_or_authorization_failure')
                if response is not None and response.status_code == 200 and raw is not None and not retry:
                    self._save(d.raw_path, raw, raw=True)
                    final['raw_sha256'] = sha256_bytes(raw)
                    try:
                        normalized = normalize(raw)
                        if set(normalized) != {'value', 'source_period', 'consumer_complete'} or not normalized['source_period']:
                            raise ValueError('source_observation_period_required')
                        if normalized['consumer_complete'] is not True:
                            raise ValueError('consumer_incomplete_or_cap_exhausted')
                        if _secret_field(normalized) or any(s in encoded(normalized).decode() for s in self.secrets):
                            raise SourceSafetyStop('normalized_secret_failure')
                    except (ValueError, KeyError, TypeError) as exc:
                        final['failure'] = 'NORMALIZATION_' + type(exc).__name__
                        self._save(base / 'normalization.json', dict(binding, status='FAILED', failure=final['failure']))
                        break
                    norm = dict(binding, status='PASS', source_sha256=final['raw_sha256'],
                        owner=d.normalizer, owner_sha256=d.owner_sha256, **normalized)
                    self._save(base / 'normalization.json', norm)
                    role = dict(binding, status='PASS', normalization_sha256=digest(norm), source_sha256=final['raw_sha256'])
                    self._save(base / 'role-binding.json', role)
                    final.update(status='PASS', normalization_sha256=digest(norm), role_binding_sha256=digest(role),
                        source_period=normalized['source_period'], retrieval_time=row['finished_at'],
                        response_headers=row['response_headers'])
                    break
                if not retry or attempt == d.max_transport_attempts:
                    final['failure'] = row['error'] or 'HTTP_' + str(row['status'])
                    break
                await asyncio.sleep(attempt)
        except SourceSafetyStop:
            final['status'] = 'SYSTEMIC_STOP'
            self.halted = True
            raise
        finally:
            for name in ('normalization', 'role-binding'):
                if not (self.root / base / (name + '.json')).exists():
                    self._save(base / (name + '.json'), dict(binding, status='NOT_ELIGIBLE', cause=final['status']))
            final['finished_at'] = stamp()
            final['receipt_sha256'] = digest(final)
            self._save(base / 'final.json', final)
            self.results[logical_id] = final
        return final

    def skip_unselected(self, logical_id):
        """Only a deterministic no-selection result can consume a slot without I/O."""
        if self.halted or logical_id in self.used:
            raise SourceSafetyStop('unplanned_or_repeated_request')
        if encoded(json.loads((self.root / 'plan.json').read_bytes())) != encoded(self.plan.model_dump(mode='json')):
            raise SourceSafetyStop('sealed_plan_drift')
        try:
            self.resolve(logical_id)
        except SlotNotSelected as exc:
            reason = str(exc)
        else:
            raise SourceSafetyStop('selected_slot_cannot_be_skipped')
        d = next(d for d in self.plan.descriptors if d.logical_request_id == logical_id)
        binding = dict(generation_id=d.generation_id, logical_request_id=logical_id,
            descriptor_sha256=d.descriptor_sha256, request_sha256=d.request_semantic_sha256,
            plan_sha256=self.plan.plan_sha256, role=d.consumer_role,
            parent_receipts={k: self.results[k]['receipt_sha256'] for k in d.response_binding.parents})
        base = Path('receipts') / logical_id
        self.used.add(logical_id)
        self._save(base / 'plan.json', dict(binding, descriptor=d.model_dump(mode='json')))
        self._save(base / 'start.json', dict(binding, started_at=stamp(), transport_started=False))
        for name in ('normalization', 'role-binding'):
            self._save(base / (name + '.json'), dict(binding, status='NOT_SELECTED', reason=reason))
        final = dict(binding, status='NOT_SELECTED', reason=reason, attempts=[], finished_at=stamp())
        final['receipt_sha256'] = digest(final)
        self._save(base / 'final.json', final)
        self.results[logical_id] = final
        return final


def _binding_parent(root, plan, key, receipt_sha256):
    base = Path(root) / 'receipts' / key
    if any(p.is_symlink() for p in (base, *base.parents)):
        raise ValueError('binding_parent_symlink_denied')
    final = json.loads((base / 'final.json').read_bytes())
    if (final.get('receipt_sha256') != receipt_sha256 or
            digest({k: v for k, v in final.items() if k != 'receipt_sha256'}) != receipt_sha256):
        raise ValueError('binding_parent_receipt_mismatch')
    if final['status'] == 'NOT_SELECTED':
        d = next(d for d in plan.descriptors if d.logical_request_id == key)
        if (final['descriptor_sha256'] != d.descriptor_sha256 or final['plan_sha256'] != plan.plan_sha256
                or final['generation_id'] != plan.generation_id or not d.response_binding
                or set(final['parent_receipts']) != set(d.response_binding.parents)):
            raise ValueError('binding_parent_not_selected_identity')
        parents = {k: _binding_parent(root, plan, k, h) for k, h in final['parent_receipts'].items()}
        try:
            resolve_response_binding(d.request_json, d.response_binding, parents)
        except SlotNotSelected as exc:
            if str(exc) != final['reason']:
                raise ValueError('binding_parent_not_selected_reason') from exc
        else:
            raise ValueError('binding_parent_selected_but_skipped')
        return {'status': 'NOT_SELECTED', 'raw': None}
    consume_bound_result(root=root, plan=plan, logical_id=key, receipt_sha256=receipt_sha256)
    resolved_path = base / 'resolved-request.json'
    if resolved_path.is_symlink():
        raise ValueError('binding_parent_symlink_denied')
    resolved = json.loads(resolved_path.read_bytes())
    request = resolved['request']
    if digest(request) != final['resolved_request_sha256']:
        raise ValueError('binding_parent_wire_identity')
    d = next(d for d in plan.descriptors if d.logical_request_id == key)
    return dict(status='PASS', raw=(Path(root) / d.raw_path).read_bytes(), request=request,
                response_headers=final['response_headers'])


def consume_bound_result(*, root, plan, logical_id, receipt_sha256):
    """Resolve generation + exact descriptor + final receipt, never loose JSON."""
    plan = ProviderPlan.model_validate(plan)
    descriptor = next((d for d in plan.descriptors if d.logical_request_id == logical_id), None)
    if descriptor is None:
        raise ValueError('unplanned_consumer_request')
    base = Path(root) / 'receipts' / logical_id
    def read(path):
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError('consumer_symlink_denied')
        return json.loads(path.read_bytes())
    final = read(base / 'final.json')
    expected = dict(generation_id=plan.generation_id, logical_request_id=logical_id,
        descriptor_sha256=descriptor.descriptor_sha256, plan_sha256=plan.plan_sha256,
        request_sha256=descriptor.request_semantic_sha256, role=descriptor.consumer_role)
    if (final.get('receipt_sha256') != receipt_sha256
            or digest({k: v for k, v in final.items() if k != 'receipt_sha256'}) != receipt_sha256
            or final.get('status') != 'PASS' or any(final.get(k) != v for k, v in expected.items())):
        raise ValueError('consumer_receipt_identity_mismatch')
    resolved_path = base / 'resolved-request.json'
    resolved = read(resolved_path)
    if descriptor.response_binding:
        if plan.binding_owner_sha256 != binding_owner_hash():
            raise ValueError('consumer_response_binding_owner_drift')
        if set(final['parent_receipts']) != set(descriptor.response_binding.parents):
            raise ValueError('consumer_parent_set_mismatch')
        parents = {k: _binding_parent(root, plan, k, h) for k, h in final['parent_receipts'].items()}
        expected_wire, selected = resolve_response_binding(descriptor.request_json, descriptor.response_binding, parents)
        if selected != resolved['selected']:
            raise ValueError('consumer_selected_metadata_mismatch')
    else:
        expected_wire = descriptor.request_json
    if (encoded(resolved['request']).decode() != expected_wire
            or final['resolved_request_sha256'] != sha256_bytes(expected_wire.encode())):
        raise ValueError('consumer_resolved_wire_mismatch')
    raw_path = Path(root) / descriptor.raw_path
    if any(p.is_symlink() for p in (raw_path, *raw_path.parents)):
        raise ValueError('consumer_raw_symlink_denied')
    raw = raw_path.read_bytes()
    norm, role = read(base / 'normalization.json'), read(base / 'role-binding.json')
    if (sha256_bytes(raw) != final['raw_sha256'] or digest(norm) != final['normalization_sha256']
            or digest(role) != final['role_binding_sha256']
            or any(norm.get(k) != v or role.get(k) != v for k, v in expected.items())
            or norm.get('source_sha256') != final['raw_sha256'] or role.get('normalization_sha256') != digest(norm)):
        raise ValueError('consumer_artifact_hash_mismatch')
    return norm
