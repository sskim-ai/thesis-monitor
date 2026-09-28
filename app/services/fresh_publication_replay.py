"""Fresh captured HTTP bytes replayed through existing publication providers.

Credentials are deliberately absent. The original query, response and receipt
time are bound before invoking the same provider parser on a private transport.
"""

import asyncio
from datetime import datetime

import httpx
from pydantic import TypeAdapter
from sqlalchemy import delete
from sqlmodel import Session, create_engine

from app.macro.providers.base import MacroProviderResult
from app.macro.providers.ecos import EcosProvider
from app.macro.providers.eia import EiaProvider
from app.macro.providers.fred import FredProvider
from app.macro.storage import persist_observation
from app.models.macro import MacroObservation
from app.services.macro_source_time import CONTRACT as SOURCE_TIME_CONTRACT
from app.services.unified_run_artifacts import sha256_bytes
from app.services.unified_snapshot_contract import digest


PROVIDERS = {'fred': FredProvider, 'eia': EiaProvider, 'ecos': EcosProvider}


def _bind_same_response_changes(result, as_of):
    """Reuse native delta arithmetic with only this response's ordered rows.

    No persisted briefing is loaded. Previous observation is a source-period
    comparison, not evidence that a new daily briefing signal has occurred.
    """
    engine = create_engine('sqlite://')
    MacroObservation.__table__.create(engine)
    try:
        with Session(engine) as session:
            previous = {}
            for observation in sorted(result.observations, key=lambda row: (row.series_code, row.observed_at)):
                temporal = observation.raw_payload['publication_context']
                key = (observation.series_code, temporal['response_sha256'], observation.unit, observation.frequency)
                prior = previous.get(key)
                if prior is not None:
                    observation.previous_value = prior.value
                # The private table must not bridge distinct HTTP responses.
                session.exec(delete(MacroObservation))
                session.commit()
                row, _ = persist_observation(session, result.provider, observation, as_of)
                observation.previous_value = row.previous_value
                observation.change_value = row.change_value
                observation.change_pct = row.change_pct
                if prior is not None:
                    observation.raw_payload['previous_observation_date'] = prior.observed_at.date().isoformat()
                    observation.raw_payload['change_input_response_sha256'] = temporal['response_sha256']
                previous[key] = observation
    finally:
        engine.dispose()


def public_request(request):
    route = str(request.url.copy_with(query=None))
    if request.url.host == 'ecos.bok.or.kr':
        parts = route.split('/')
        if len(parts) > 5 and parts[4] == 'KeyStatisticList':
            parts[5] = '[REDACTED]'
        route = '/'.join(parts)
    params = {k: '[REDACTED]' if k == 'api_key' else v for k, v in request.url.params.items()}
    return {'method': request.method, 'route': route, 'params': params}


def replay_fresh_publications(*, run_id, run_started_at, acquisition_cutoff, as_of,
                              providers, policy):
    times = (run_started_at, acquisition_cutoff, as_of)
    if any(t.utcoffset() is None for t in times) or not run_started_at <= as_of <= acquisition_cutoff:
        raise ValueError('fresh_publication_generation_time_invalid')
    if set(providers) != set(PROVIDERS):
        raise ValueError('fresh_publication_exact_provider_set_required')

    async def replay(name, inputs):
        policy.require(name)
        receipts, bodies, hashes = inputs['receipts'], inputs['bodies'], inputs['body_hashes']
        if not receipts or set(bodies) != set(hashes) or any(sha256_bytes(b) != hashes[k] for k, b in bodies.items()):
            raise ValueError('fresh_publication_raw_hash_mismatch')
        seen = set()
        for row in receipts:
            artifact = row['artifact']
            start, end = (datetime.fromisoformat(row[k]) for k in ('requested_at', 'received_at'))
            if (row['run_id'] != run_id or row['provider'] != name or artifact in seen
                    or row['artifact_sha256'] != hashes.get(artifact)
                    or row['outcome'] != 'HTTP_RESPONSE'
                    or any(t.utcoffset() is None for t in (start, end))
                    or not run_started_at <= as_of <= start <= end <= acquisition_cutoff):
                raise ValueError('fresh_publication_original_receipt_invalid')
            seen.add(artifact)
        if seen != set(bodies):
            raise ValueError('fresh_publication_unused_body')

        class ReplayTransport(httpx.AsyncBaseTransport):
            index = 0
            received_at = None
            errors = []

            async def handle_async_request(self, request):
                if self.index >= len(receipts):
                    self.errors.append('undeclared_request')
                    raise ValueError('fresh_publication_undeclared_request')
                row = receipts[self.index]
                self.index += 1
                if public_request(request) != row['request']:
                    self.errors.append('request_mismatch')
                    raise ValueError('fresh_publication_request_mismatch')
                self.received_at = datetime.fromisoformat(row['received_at'])
                return httpx.Response(row['http_status'], content=bodies[row['artifact']], request=request)

        transport = ReplayTransport()
        provider = PROVIDERS[name](transport=transport, clock=lambda: transport.received_at)
        provider.settings = provider.settings.model_copy(update={name + '_api_key': 'offline-no-credential'})
        result = await provider.collect(as_of)
        if transport.errors or transport.index != len(receipts):
            raise ValueError('fresh_publication_request_replay_not_exact')
        _bind_same_response_changes(result, as_of)
        value = TypeAdapter(MacroProviderResult).dump_python(result, mode='json')
        for observation in value['observations']:
            temporal = observation['raw_payload']['publication_context']
            if temporal['response_sha256'] not in hashes.values():
                raise ValueError('fresh_publication_unbound_observation')
        return dict(value=value, value_sha256=digest(value), original_receipts=receipts, source_hashes=hashes)

    async def run():
        output = {}
        for name in sorted(PROVIDERS):
            output[name] = await replay(name, providers[name])
        return output

    values = asyncio.run(run())
    return dict(contract='fresh-publication-replay-v1', run_id=run_id,
        run_started_at=run_started_at.isoformat(), acquisition_cutoff=acquisition_cutoff.isoformat(),
        query_as_of=as_of.isoformat(), providers=values, external_provider_calls=0,
        currentness_owner=SOURCE_TIME_CONTRACT, value_sha256=digest(values))
