"""Offline proposal evaluator only. This is NOT installed in any HTTP guard."""
from urllib.parse import urlsplit
import re


class ProposedBootstrap:
    def __init__(self, *, transport_account_fingerprint, owner_generation,
                 source_packet_sha256, consumer_identity):
        if (not isinstance(owner_generation, str) or not owner_generation
                or not re.fullmatch('[a-f0-9]{64}', transport_account_fingerprint)
                or not re.fullmatch('[a-f0-9]{64}', source_packet_sha256)):
            raise ValueError('EXACT_SYNTHETIC_BINDING_REQUIRED')
        self.account = transport_account_fingerprint
        self.generation = owner_generation
        self.packet = source_packet_sha256
        self.consumer = consumer_identity
        self.attempted = False

    def evaluate(self, request, *, owner_generation, source_packet_sha256,
                 consumer_identity, before_stage, redirect=False):
        if self.attempted:
            raise ValueError('BOOTSTRAP_ALREADY_CONSUMED')
        self.attempted = True
        if (owner_generation != self.generation or source_packet_sha256 != self.packet
                or consumer_identity != self.consumer or before_stage is not True):
            raise ValueError('EXACT_PRE_STAGE_BINDING_REQUIRED')
        url = urlsplit(request['url'])
        if (set(request) != {'method','url','body','authorization_present','transport_account_fingerprint'}
                or request['url'] not in ('https://chatgpt.com/backend-api/wham/accounts/check',
                    'https://chatgpt.com:443/backend-api/wham/accounts/check')
                or request['method'] != 'GET' or url.scheme != 'https'
                or url.hostname != 'chatgpt.com' or url.port not in (None, 443)
                or url.username is not None or url.password is not None
                or url.path != '/backend-api/wham/accounts/check'
                or url.query or url.fragment or request.get('body') is not None
                or redirect):
            raise ValueError('EXACT_BOOTSTRAP_SHAPE_REQUIRED')
        if (request.get('authorization_present') is not True
                or request.get('transport_account_fingerprint') != self.account):
            raise ValueError('AUTH_ACCOUNT_BINDING_REQUIRED')
        return dict(proposal_shape_valid=True,network_authorized=False,
                    source_authority=False,model_authorized=False)
