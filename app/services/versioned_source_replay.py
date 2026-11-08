"""Opt-in binding to a live, isolated original Source producer.

A stored packet or receipt alone cannot create this capability. The trusted
backend must supply the bounded producer RPC and immutable source verification.
This grants no current-source, execution, account, or delivery authority.
"""
from copy import deepcopy
from app.services.vnext_research_store import digest
from app.services.vnext_daily_research import UseRegistry

CONTRACT = 'VERSIONED_ORIGINAL_SOURCE_REPLAY_V1'


class VersionedSourceReplay:
    def __init__(self, *, producer, verify_environment, packet, consumer_schema,
                 consumer_identity, registry, enabled=False):
        if not enabled:
            raise ValueError('versioned_source_default_off')
        if not callable(producer) or not callable(verify_environment):
            raise ValueError('versioned_live_producer_required')
        if type(registry) is not UseRegistry:
            raise ValueError('versioned_live_use_registry_required')
        self._registry = registry
        self._producer = producer
        self._verify_environment = verify_environment
        self._packet = deepcopy(packet)
        self._schema = deepcopy(consumer_schema)
        self._consumer = deepcopy(consumer_identity)
        self._revoked = False
        original = self._read()
        if original['packet'] != self._packet or original['schema'] != self._schema:
            raise ValueError('versioned_original_packet_or_schema_mismatch')
        self._economic_sha = digest(original['economic'])
        self._producer_identity = deepcopy(original['producer_identity'])

    def _read(self):
        if self._revoked or self._verify_environment() is not True:
            raise ValueError('versioned_source_environment_changed_or_closed')
        security = self._packet['base']['public_security']['canonical_security_id']
        if any(self._registry.revoked(security, evidence)
               for evidence in self._packet['base']['evidence']):
            raise ValueError('versioned_source_use_revoked')
        result = self._producer('rebuild')
        if (result.get('contract') != CONTRACT or result.get('dated_only') is not True
                or result.get('original_owner_replayed') is not True
                or result.get('current_source') is not False):
            raise ValueError('versioned_original_owner_required')
        return result

    def source_loader(self):
        result = self._read()
        if (result['packet'] != self._packet or digest(result['economic']) != self._economic_sha
                or result['producer_identity'] != self._producer_identity):
            raise ValueError('versioned_source_changed')
        return deepcopy(result['packet'])

    def economic_loader(self):
        result = self._read()
        if result['packet'] != self._packet or digest(result['economic']) != self._economic_sha:
            raise ValueError('versioned_economic_source_changed')
        return deepcopy(result['economic'])

    def rebuild(self, economic, *, packet, consumer_schema, options, registry):
        if (registry is not self._registry or options
                or economic != self.economic_loader() or packet != self._packet):
            raise ValueError('versioned_exact_owner_input_required')
        self.require_consumer(packet=packet, schema=consumer_schema,
                              identity=self._consumer, mode='DATED_REPLAY')
        return self.source_loader()

    def require_consumer(self, *, packet, schema, identity, mode):
        if (mode != 'DATED_REPLAY' or packet != self._packet or schema != self._schema
                or identity != self._consumer):
            raise ValueError('versioned_source_consumer_binding')
        if self._verify_environment() is not True or self._revoked:
            raise ValueError('versioned_source_environment_changed_or_closed')
        return dict(contract=CONTRACT, packet_sha256=digest(self._packet),
                    producer=deepcopy(self._producer_identity),
                    consumer=deepcopy(self._consumer), current_source=False,
                    dated_only=True, stage_accepted=False, send=False)

    def revoke(self):
        self._revoked = True
