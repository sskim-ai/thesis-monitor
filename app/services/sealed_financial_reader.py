"""Existing financial acquisition owner with network owned by sealed slots only."""
import json

import httpx

from app.services.bounded_financial_acquisition import AcquisitionDenied, BoundedReader, SystemicStop
from app.services.sealed_fresh_dispatch import consume_bound_result, wire_identity
from app.services.sealed_response_binding import SlotNotSelected
from app.services.unified_live_source_transport import SourceSafetyStop
from app.services.unified_run_artifacts import durable_bytes, durable_json
from app.services.unified_snapshot_contract import digest


class FinancialFragment:
    def __init__(self, descriptor):
        self.identity = (descriptor.normalizer, descriptor.owner_sha256)
        self.descriptor = descriptor

    def __call__(self, raw):
        if not raw:
            raise ValueError('empty_financial_fragment')
        if self.descriptor.provider == 'opendart':
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
    def __init__(self, plan, output, *, dispatcher, transport, **credentials):
        super().__init__(plan, output, **credentials)
        self.dispatcher, self.wire_transport = dispatcher, transport
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
        request = httpx.Request('GET', url, params=wire_params, headers=headers)
        public = wire_identity(request, self.dispatcher.secrets)
        matches = []
        for descriptor in self.dispatcher.plan.descriptors:
            if (descriptor.subject != self.plan['ticker'] or descriptor.provider != self.plan['provider']
                    or descriptor.endpoint_operation != stage or descriptor.logical_request_id in self.dispatcher.used):
                continue
            if descriptor.response_binding and any(k not in self.dispatcher.results for k in descriptor.response_binding.parents):
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
        if stage in {'index', 'document'} and filing != selected:
            raise SystemicStop('sealed_financial_filing_metadata_mismatch')
        if stage == 'statement' and filing != dict(role=selected['role'], receipt_no=selected['receipt_no'], basis=d.response_binding.basis):
            raise SystemicStop('sealed_financial_statement_metadata_mismatch')
        self.logical += 1
        name = f'request-{self.logical:03d}'
        frozen = dict(stage=stage, method='GET', url=url, params=params, filing=filing,
            plan_sha256=self.plan_sha, logical_id=self.plan['ticker'] + ':' + name)
        durable_json(self.output / (name + '.plan.json'), frozen, exclusive=True)
        try:
            final = await self.dispatcher.execute(d.logical_request_id, request,
                transport=self.wire_transport, normalize=FinancialFragment(d))
        except SourceSafetyStop as exc:
            raise SystemicStop('sealed_financial_systemic_stop') from exc
        for row in final['attempts']:
            self.attempts += 1
            artifact = f'{name}-attempt-{row["attempt"]}.body' if row.get('artifact') else None
            provider_status = None
            if artifact:
                raw = (self.dispatcher.root / row['artifact']).read_bytes()
                durable_bytes(self.output / artifact, raw, exclusive=True)
                if self.plan['provider'] == 'opendart':
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
        return (self.dispatcher.root / d.raw_path).read_bytes(), self.receipts[-1]
