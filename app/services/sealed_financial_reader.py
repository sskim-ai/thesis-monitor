"""Existing financial acquisition owner with network owned by sealed slots only."""
from datetime import datetime
import json
from pathlib import Path
import re

import httpx

from app.services.bounded_financial_acquisition import AcquisitionDenied, BoundedReader, SystemicStop
from app.services.dart_report_artifact import document_error_status, extract_dart_xml
from app.services.bounded_financial_acquisition import sec_base, sec_document_identity, sec_selection
from app.services.sealed_fresh_dispatch import consume_bound_result, decode_request_plan, wire_identity
from app.services.sealed_opendart_contract import opendart_headers
from app.services.sealed_response_binding import SlotNotSelected
from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.unified_run_artifacts import durable_bytes, durable_json, sha256_bytes
from app.services.unified_snapshot_contract import digest


def _plain_read(path):
    path = Path(path)
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file():
        raise ValueError('retained_sec_regular_file_required')
    return path.read_bytes()


def verify_retained_sec_document(descriptor, wire, filing, proof, raw, *, frozen_at, selected_at, discovery_finished_at):
    """Validate an old 200 without replacing either generation's clock."""
    binding = descriptor.response_binding
    if (descriptor.provider != 'sec_edgar' or descriptor.market != 'us' or binding is None
            or binding.kind not in {'SEC_PRIMARY', 'SEC_INDEX', 'SEC_EXHIBIT'}
            or descriptor.endpoint_operation != ('index' if binding.kind == 'SEC_INDEX' else 'document')
            or not isinstance(filing, dict) or wire.get('method') != 'GET'):
        raise ValueError('retained_sec_requires_current_document_selection')
    plan = json.loads(binding.policy_json)
    pin, request, original = (proof[key] for key in ('pin', 'original_request', 'original_receipt'))
    expected_identity = dict(ticker=descriptor.subject, issuer=plan['issuer'],
        canonical_security_id=plan['security']['canonical_security_id'])
    stage, url = descriptor.endpoint_operation, wire['url']
    if (pin['identity'] != expected_identity or pin['origin_generation'] == plan['run_id']
            or request['url'] != url or request['method'] != 'GET' or request['params']
            or original['stage'] != stage or request['stage'] != stage
            or request['logical_id'] != original['logical_id']
            or request['plan_sha256'] != original['plan_sha256'] or request['plan_sha256'] != pin['original_plan_sha256']
            or digest(request) != original['request_sha256'] or digest(original) != pin['original_receipt_sha256']
            or original.get('retained_sec_origin') is not None or original.get('HTTP_status') != 200
            or any(original.get(k) is not None for k in ('failure_class','error_type','systemic_reason','provider_status'))
            or request['filing'] != original['filing']
            or {k:v for k,v in original['filing'].items() if k != 'role'} != {k:v for k,v in filing.items() if k != 'role'}
            or sec_document_identity(url,plan,filing) != url
            or (stage == 'index' and url != sec_base(plan,filing)+'index.json')
            or sha256_bytes(raw) != original['raw_sha256'] or pin['raw_sha256'] != original['raw_sha256']):
        raise ValueError('retained_sec_document_origin_mismatch')
    origin_cutoff, began, retrieved, discovered, selected = map(datetime.fromisoformat, (
        pin['original_cutoff'], original['started_at'], original['finished_at'], discovery_finished_at, selected_at))
    if (any(t.utcoffset() is None for t in (origin_cutoff,began,retrieved,frozen_at,discovered,selected))
            or not origin_cutoff <= began <= retrieved < frozen_at <= discovered <= selected
            or filing['filingDate'] > retrieved.date().isoformat()
            or filing['filingDate'] > plan['cutoff'][:10]):
        raise ValueError('retained_sec_document_time_mismatch')
    return original


def verify_retained_financial_use(plan, directory, receipt):
    """Replay the existing dispatcher binding rather than trust projector flags."""
    directory = Path(directory)
    root = directory.parents[1]/'dispatch'
    if directory.name != plan['ticker'] or directory.parent.name != 'financial':
        raise ValueError('retained_sec_financial_directory_scope')
    kind = 'dart' if 'retained_dart_origin' in receipt else 'sec'
    origin = f'retained_{kind}_origin'
    key = receipt['sealed_logical_id']
    if not re.fullmatch(r'[A-Za-z0-9_.:-]+',key) or key in {'.','..'}:
        raise ValueError('retained_sec_logical_id_scope')
    dispatch_plan = decode_request_plan(json.loads(_plain_read(root/'plan.json')))
    descriptor = next((d for d in dispatch_plan.descriptors if d.logical_request_id == key),None)
    final = json.loads(_plain_read(root/'receipts'/key/'final.json'))
    resolved = json.loads(_plain_read(root/'receipts'/key/'resolved-request.json'))
    local = receipt['logical_id'].split(':')[-1]
    if not re.fullmatch(r'request-\d{3}', local):
        raise ValueError('retained_sec_projector_logical_id_scope')
    request = json.loads(_plain_read(directory/(local+'.plan.json')))
    if (descriptor is None or descriptor.response_binding is None or descriptor.subject != plan['ticker']
            or json.loads(descriptor.response_binding.policy_json) != plan
            or dispatch_plan.generation_id != plan['run_id'] or receipt['sealed_generation_id'] != plan['run_id']
            or receipt['sealed_descriptor_sha256'] != descriptor.descriptor_sha256
            or final.get(origin) is None or final[origin] != receipt[origin]
            or receipt['selected_at'] != final['finished_at'] or receipt['finished_at'] != final['retrieval_time']
            or receipt['artifact'] != local+'-retained.body' or receipt['raw_sha256'] != final['raw_sha256']
            or sha256_bytes(_plain_read(directory/receipt['artifact'])) != final['raw_sha256']
            or request['url'] != (resolved['request']['url'].split('?')[0] if kind == 'dart' else resolved['request']['url'])
            or request['filing'] != resolved['selected']
            or request['filing'] != receipt['filing'] or request['stage'] != descriptor.endpoint_operation
            or request['stage'] != receipt['stage'] or request['method'] != 'GET'
            or request['params'] != (dict(rcept_no=receipt['filing']['receipt_no']) if kind == 'dart' else {})
            or receipt['attempt'] != 0 or receipt['HTTP_status'] is not None or receipt['failure_class'] is not None):
        raise ValueError('retained_sec_financial_use_mismatch')
    consume_bound_result(root=root,plan=dispatch_plan,logical_id=key,receipt_sha256=receipt['sealed_final_receipt_sha256'])
    original = json.loads(_plain_read(root/'receipts'/key/f'retained-{kind}-origin.json'))['original_receipt']
    if receipt['started_at'] != original['started_at']:
        raise ValueError('retained_sec_original_time_changed')
    return datetime.fromisoformat(receipt['selected_at'])


class FinancialFragment:
    def __init__(self, descriptor, filing=None):
        self.filing = filing
        self.identity = (descriptor.normalizer, descriptor.owner_sha256)
        self.descriptor = descriptor

    def __call__(self, raw):
        if not raw:
            raise ValueError('empty_financial_fragment')
        if self.descriptor.endpoint_operation == 'dart_report':
            status = document_error_status(raw)
            if status and status not in {'013', '014'}:
                raise SourceSafetyStop('dart_document_provider_denied:' + str(status))
            extract_dart_xml(raw, self.filing['receipt_no'], corp_code=self.filing['corp_code'],
                             report_code=self.filing['report_code'])
        elif self.descriptor.provider == 'opendart':
            if json.loads(raw).get('status') not in {'000', '013'}:
                raise ValueError('dart_provider_status_denied')
        elif self.descriptor.endpoint_operation != 'document':
            if not isinstance(json.loads(raw), dict):
                raise ValueError('financial_metadata_object_required')
        return dict(value={'bytes': len(raw), 'qualified_financial_fact': False},
            source_period='SOURCE_FRAGMENT_PENDING_FINANCIAL_OWNER', consumer_complete=True)


class SealedFinancialReader(BoundedReader):
    """Keep collect/project contracts; preserve their receipt dialect losslessly.

    Adapted receipts additionally bind the sealed final receipt. This reader does
    not retry: only the dispatcher owns the frozen transient-attempt budget.
    """
    def __init__(self, plan, output, *, dispatcher, transport, retained_sec=None, **credentials):
        super().__init__(plan, output, **credentials)
        self.dispatcher, self.wire_transport = dispatcher, transport
        self.retained_sec = retained_sec or {}
        if plan['run_id'] != dispatcher.plan.generation_id:
            raise ValueError('sealed_financial_generation_mismatch')
        slots = [d for d in dispatcher.plan.descriptors if d.subject == plan['ticker'] and d.provider == plan['provider']]
        if (not slots or any(d.response_binding and json.loads(d.response_binding.policy_json) != plan for d in slots)):
            raise ValueError('sealed_financial_policy_mismatch')

    async def read(self, stage, url, params=None, *, filing=None):
        params = dict(params or {})
        self._scope(stage, url, params)
        if digest(self.plan) != self.plan_sha:
            raise SystemicStop('financial_policy_drift')
        if self.guard:
            self.guard()
        wire_params = dict(params, crtfc_key=self.api_key) if self.plan['provider'] == 'opendart' else params
        headers = {'User-Agent': self.user_agent, 'Accept': 'application/json'} if self.user_agent else {}
        if self.plan['provider'] == 'opendart':
            headers = opendart_headers(document=stage == 'dart_report')
        request = httpx.Request('GET', url, params=wire_params, headers=headers)
        public = wire_identity(request, self.dispatcher.secrets)
        matches = []
        for descriptor in self.dispatcher.plan.descriptors:
            if (descriptor.subject != self.plan['ticker'] or descriptor.provider != self.plan['provider']
                    or descriptor.endpoint_operation != stage or descriptor.logical_request_id in self.dispatcher.used):
                continue
            if descriptor.response_binding and any(k not in self.dispatcher.results for k in descriptor.response_binding.parents):
                continue
            if (filing and descriptor.response_binding
                    and descriptor.response_binding.kind.startswith('SEC_')):
                # Do not resolve a sibling accession's attachment selector while
                # looking up a reserved primary slot. Its denial is still audited.
                parent = next(d for d in self.dispatcher.plan.descriptors
                              if d.logical_request_id == descriptor.response_binding.parents[0])
                payload = json.loads((self.dispatcher.root / parent.raw_path).read_bytes())
                selected_filings = sec_selection(payload, self.plan)
                ordinal = descriptor.response_binding.selection_ordinal
                if ordinal > len(selected_filings) or selected_filings[ordinal-1] != filing:
                    continue
            try:
                resolved, _, _ = self.dispatcher.resolve(descriptor.logical_request_id)
            except SlotNotSelected:
                continue
            if resolved == public:
                matches.append(descriptor)
        if len(matches) != 1:
            raise SystemicStop('financial_request_not_unique_sealed_slot')
        d = matches[0]
        _, _, selected = self.dispatcher.resolve(d.logical_request_id)
        if stage in {'index', 'document', 'dart_report'} and filing != selected:
            raise SystemicStop('sealed_financial_filing_metadata_mismatch')
        if stage == 'statement' and filing != dict(role=selected['role'], receipt_no=selected['receipt_no'], basis=d.response_binding.basis):
            raise SystemicStop('sealed_financial_statement_metadata_mismatch')
        self.logical += 1
        name = f'request-{self.logical:03d}'
        frozen = dict(stage=stage, method='GET', url=url, params=params, filing=filing,
            plan_sha256=self.plan_sha, logical_id=self.plan['ticker'] + ':' + name)
        durable_json(self.output / (name + '.plan.json'), frozen, exclusive=True)
        retained = None
        if self.plan['provider'] == 'sec_edgar' and stage in {'document','index'}:
            entry = self.retained_sec.get(url)
            if entry is not None:
                original = entry['proof']['original_receipt']
                comparable = lambda row: {k:v for k,v in row.items() if k != 'role'}
                if comparable(original['filing']) == comparable(filing):
                    raw = _plain_read(entry['body'])
                    retained = (entry['proof'], raw)
        store = getattr(self.dispatcher, 'dart_report_store', None) if stage == 'dart_report' else None
        invalid_origin = False
        if store is not None:
            try:
                retained = store.find(self.plan, filing)
            except (ValueError, OSError):
                invalid_origin = True
        try:
            final = await self.dispatcher.execute(d.logical_request_id, request,
                transport=self.wire_transport, normalize=FinancialFragment(d, filing),
                **({'unavailable_dart_origin': True} if invalid_origin else {}), **(
                    {('retained_dart_document' if stage == 'dart_report' else 'retained_sec_document'): retained}
                    if retained is not None else {}))
        except SourceSafetyStop as exc:
            raise SystemicStop('sealed_financial_systemic_stop') from exc
        if retained is not None:
            artifact = name+'-retained.body'
            original = retained[0]['original_receipt']
            receipt = dict(logical_id=frozen['logical_id'], stage=stage, plan_sha256=self.plan_sha,
                request_sha256=digest(frozen), attempt=0, started_at=original['started_at'],
                finished_at=original['finished_at'], selected_at=final['finished_at'],
                HTTP_status=None, failure_class=None, filing=filing, raw_sha256=final['raw_sha256'],
                artifact=artifact, **({'retained_dart_origin': final['retained_dart_origin']} if stage == 'dart_report'
                                     else {'retained_sec_origin': final['retained_sec_origin']}),
                sealed_generation_id=d.generation_id, sealed_logical_id=d.logical_request_id,
                sealed_final_receipt_sha256=final['receipt_sha256'], sealed_descriptor_sha256=d.descriptor_sha256)
            durable_bytes(self.output / artifact, retained[1], exclusive=True)
            durable_json(self.output / (name+'-retained.receipt.json'), receipt, exclusive=True)
            verify_retained_financial_use(self.plan,self.output,receipt)
            self.receipts.append(receipt)
            return retained[1],receipt
        for row in final['attempts']:
            self.attempts += 1
            artifact = f'{name}-attempt-{row["attempt"]}.body' if row.get('artifact') else None
            provider_status = None
            if artifact:
                raw = (self.dispatcher.root / row['artifact']).read_bytes()
                durable_bytes(self.output / artifact, raw, exclusive=True)
                if stage == 'dart_report':
                    provider_status = document_error_status(raw)
                elif self.plan['provider'] == 'opendart':
                    try:
                        provider_status = json.loads(raw).get('status')
                    except ValueError:
                        pass
            success = row['attempt'] == len(final['attempts']) and final['status'] == 'PASS'
            receipt = dict(logical_id=frozen['logical_id'], stage=stage, plan_sha256=self.plan_sha,
                request_sha256=digest(frozen), attempt=row['attempt'], attempt_ordinal=self.attempts,
                started_at=row['started_at'], finished_at=row['finished_at'], timeout_seconds=d.timeout_seconds,
                retry=row['attempt'] > 1, retry_reason='TRANSIENT_PROVIDER' if row['attempt'] > 1 else None,
                page=params.get('page_no'), filing=filing, HTTP_status=row['status'], provider_status=provider_status,
                error_type=row['error'], failure_class=None if success else 'TRANSIENT_PROVIDER' if row['transient'] else 'PROVIDER_DENIAL',
                systemic_reason=None, raw_sha256=row['raw_sha256'], artifact=artifact,
                sealed_generation_id=d.generation_id, sealed_logical_id=d.logical_request_id,
                sealed_final_receipt_sha256=final['receipt_sha256'], sealed_descriptor_sha256=d.descriptor_sha256)
            durable_json(self.output / f'{name}-attempt-{row["attempt"]}.receipt.json', receipt, exclusive=True)
            self.receipts.append(receipt)
        if final['status'] != 'PASS':
            if self.plan['provider'] == 'opendart' and any(
                    r['status'] is not None and 300 <= r['status'] < 400 for r in final['attempts']):
                raise SystemicStop('R2B_R9_REV13_OPENDART_HEADER_ROUTE_UNRESOLVED')
            raise AcquisitionDenied(final.get('failure', 'SEALED_FINANCIAL_SOURCE_FAILED'))
        consume_bound_result(root=self.dispatcher.root, plan=self.dispatcher.plan, logical_id=d.logical_request_id,
                             receipt_sha256=final['receipt_sha256'])
        if self.plan['provider'] == 'opendart' and stage == 'discovery':
            # A statement depends on page 1 and on page 2's captured/unused receipt.
            for slot in self.dispatcher.plan.descriptors:
                if (slot.subject == d.subject and slot.response_binding
                        and slot.response_binding.kind == 'DART_NEXT_PAGE' and slot.logical_request_id not in self.dispatcher.used):
                    try:
                        self.dispatcher.resolve(slot.logical_request_id)
                    except SlotNotSelected:
                        self.dispatcher.skip_unselected(slot.logical_request_id)
        raw = (self.dispatcher.root / d.raw_path).read_bytes()
        if store is not None:
            try:
                store.put(self.plan, filing, raw, final)
            except (OSError, ValueError):
                # The capture and its verified current-generation receipt remain available.
                self.output_state.setdefault('source_notes', []).append(
                    {'stage': stage, 'reason': 'DART_REPORT_CACHE_WRITE_UNAVAILABLE'})
        return raw, self.receipts[-1]
