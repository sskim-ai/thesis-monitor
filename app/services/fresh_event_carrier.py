"""Opt-in fresh-controller event provenance; no acquisition or persistence."""
import base64
from datetime import datetime, timedelta
import json
from typing import Literal

from pydantic import model_validator

from app.services.canonical_fact_service import canonical_event_fact
from app.services.persisted_business_event_owner import replay_persisted_event
from app.services.unified_snapshot_contract import ContractModel, digest
from app.services.unified_stock_event_input import BoundNewsInput, replay_news


class EventRunWindow(ContractModel):
    run_id: str
    collection_started_at: datetime
    source_query_cutoff: datetime
    business_availability_cutoff: datetime

    @model_validator(mode='after')
    def ordered(self):
        times = (self.collection_started_at, self.source_query_cutoff, self.business_availability_cutoff)
        if any(t.utcoffset() is None for t in times) or not times[0] <= times[1] <= times[2]:
            raise ValueError('event_run_window_invalid')
        return self


class FreshEventCarrier(ContractModel):
    contract: Literal['fresh-event-carrier-v1'] = 'fresh-event-carrier-v1'
    acquisition_class: Literal['FRESH_CURRENT_RUN', 'PERSISTED_SOURCE_RECHECK']
    window: EventRunWindow
    source: BoundNewsInput | None = None
    persisted: dict | None = None

    @model_validator(mode='after')
    def exclusive_source(self):
        if self.acquisition_class == 'FRESH_CURRENT_RUN':
            if self.source is None or self.persisted is not None:
                raise ValueError('fresh_event_exact_source_required')
        elif self.source is not None or self.persisted is None:
            raise ValueError('persisted_event_exact_source_required')
        return self


def replay_carrier(carrier, *, plan, ticker, security, policy):
    carrier = FreshEventCarrier.model_validate(carrier)
    window = carrier.window
    if window.run_id != plan.run_id or window.collection_started_at != plan.frozen_at:
        raise ValueError('event_carrier_current_generation_mismatch')
    markets = {r.market for r in plan.reads if r.subject == ticker}
    if len(markets) != 1:
        raise ValueError('event_carrier_market_ambiguous')
    market = next(iter(markets))
    persisted_receipt = None
    if carrier.source is not None:
        source = carrier.source
        if source.read.run_id != plan.run_id:
            raise ValueError('fresh_event_cannot_relabel_original_run')
    else:
        value = carrier.persisted
        if set(value) != {'artifacts_b64', 'hashes', 'security_records', 'current_news_denial'}:
            raise ValueError('persisted_event_carrier_shape')
        artifacts = {k: base64.b64decode(v, validate=True) for k, v in value['artifacts_b64'].items()}
        original_cutoff = datetime.fromisoformat(json.loads(artifacts['normalization.json'])['cutoff'])
        source, persisted_receipt = replay_persisted_event(artifacts=artifacts, hashes=value['hashes'],
            security_records=value['security_records'], ticker=ticker, market=market,
            current_run_id=plan.run_id, cutoff=window.business_availability_cutoff,
            current_news_denial=value['current_news_denial'], policy=policy,
            source_query_cutoff=original_cutoff)
    if source.read.subject != ticker or source.read.market != market:
        raise ValueError('event_carrier_subject_market_mismatch')
    receipt = json.loads(base64.b64decode(source.response_receipt_b64, validate=True))
    start, end = (datetime.fromisoformat(receipt[k]) for k in ('requested_at', 'received_at'))
    if any(t.utcoffset() is None for t in (start, end)) or not start <= end <= window.business_availability_cutoff:
        raise ValueError('event_carrier_response_outside_availability')
    if carrier.source is not None and start < window.collection_started_at:
        raise ValueError('fresh_event_receipt_predates_collection')
    if carrier.persisted is not None and end > window.collection_started_at:
        raise ValueError('persisted_event_not_available_before_current_collection')
    normalized = json.loads(base64.b64decode(source.normalization_b64, validate=True))
    query_cutoff = (window.source_query_cutoff if carrier.source is not None else
                    datetime.fromisoformat(normalized['cutoff']))
    binding = replay_news(source, security=security, business_cutoff=window.business_availability_cutoff,
        policy=policy, source_query_cutoff=query_cutoff)
    selected = [r for r in binding['selected'] if r['status'] == 'PASS']
    earliest = window.source_query_cutoff.date() - timedelta(days=source.read.lookback_days)
    if any(not earliest <= datetime.fromisoformat(r['published_at']).date() <= window.source_query_cutoff.date()
           for r in selected):
        raise ValueError('event_carrier_current_eligibility_window')
    facts = [canonical_event_fact(row) for row in binding['evidence']]
    if any(f is None for f in facts) or len({f['fact_id'] for f in facts}) != len(facts):
        raise ValueError('event_carrier_fact_identity_invalid')
    # Existing RSS/news authority is a source-verified headline, not a confirmed
    # contract. Acquisition freshness never increases economic authority.
    from scripts.m12da_source_use_contract import SourceUse
    allowed = ['CONTEXT']
    output = dict(contract=carrier.contract, acquisition_class=carrier.acquisition_class,
        ticker=ticker, canonical_security_id=security['canonical_security_id'],
        canonical_company_id=security['canonical_company_id'], current_run_id=plan.run_id,
        original_run_id=source.read.run_id, original_acquisition_id=source.read.acquisition_id,
        window=window.model_dump(mode='json'), request_started_at=start.isoformat(), received_at=end.isoformat(),
        source_query_cutoff=query_cutoff.isoformat(), source_sha256=digest(source.model_dump(mode='json')),
        source_receipt_sha256=binding['source_receipt_sha256'], raw_sha256=binding['raw_sha256'],
        normalization_sha256=binding['normalization_sha256'], selected=selected,
        allowed_uses=allowed, prohibited_uses=sorted(u.value for u in SourceUse if u.value not in allowed),
        original_persisted_receipt=persisted_receipt, denial=binding['denial'],
        canonical_fact_hashes={f['fact_id']: digest(f) for f in facts})
    output['receipt_sha256'] = digest(output)
    return dict(receipt=output, facts=facts, evidence=binding['evidence'], binding=binding)
