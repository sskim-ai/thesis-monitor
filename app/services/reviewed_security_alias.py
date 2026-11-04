"""Backend-reviewed, time-bounded name translation, never security substitution."""
from copy import deepcopy
from datetime import datetime
from urllib.parse import urlsplit
from app.services.vnext_research_store import digest

CONTRACT = 'official-security-alias-proof-v1'
IDENTITY = ('ticker', 'canonical_security_id', 'canonical_company_id', 'country',
            'exchange', 'security_type', 'issuer_type', 'company_name')
OPTIONAL_ID = ('corp_code','cik','share_class','ordinary_share_identifier','adr_ratio')


class ReviewedSecurityAliases:
    """Only trusted backend bootstrap supplies the source and review callbacks.

    Public request JSON cannot construct a capability. Mechanical span checks
    complement, but do not replace, the recorded semantic source review.
    """
    def __init__(self, source_owner, review_owner):
        if not callable(source_owner) or not callable(review_owner):
            raise ValueError('backend_alias_review_capabilities_required')
        self._source_owner, self._review_owner = source_owner, review_owner
        self._revoked = set()
        self._pins = self._identity(*self._load())

    @staticmethod
    def _identity(sources, reviews):
        return digest([reviews, {k:dict(v,raw=digest(v['raw'])) for k,v in sources.items()}])

    def _load(self):
        sources, reviews = self._source_owner(), self._review_owner()
        if not isinstance(sources, dict) or not isinstance(reviews, list):
            raise ValueError('alias_source_review_shape')
        for review in reviews:
            if (review.get('contract') != CONTRACT or review.get('decision') != 'NAME_MAPPING_ONLY'
                or not review.get('authority') or not review.get('review_method')
                or not review.get('evidence') or not review.get('instrument_class_review')):
                raise ValueError('alias_semantic_review_missing')
            start, end = map(datetime.fromisoformat, (review['observed_from'], review['observed_through']))
            if start.tzinfo is None or end.tzinfo is None or start > end:
                raise ValueError('alias_interval')
            if any(not review['security'].get(k) for k in IDENTITY):
                raise ValueError('alias_canonical_identity_incomplete')
            for evidence in review['evidence']:
                source = sources[evidence['sha256']]
                url = urlsplit(source['url'])
                if (digest(source['raw']) != evidence['sha256'] or source['status'] != 200
                    or url.scheme != 'https' or url.hostname not in review['official_hosts']
                    or url.username or url.password or url.port not in (None, 443)
                    or source['url'] != evidence['url'] or not evidence['span']
                    or evidence['span'] not in source['raw'].decode(source.get('encoding', 'utf-8'))):
                    raise ValueError('alias_official_source_or_span')
            if not review.get('provider_name') or not review.get('listed_name') or not review.get('legal_name'):
                raise ValueError('alias_names_incomplete')
        return sources, reviews

    def revoke(self, review_digest):
        self._revoked.add(review_digest)

    def binding_digest(self):
        return digest([self._pins,sorted(self._revoked)])

    def translate(self, *, security, provider, provider_code, provider_name,
                  market, provider_class, observed_at):
        sources, reviews = self._load()
        if self._identity(sources, reviews) != self._pins:
            raise ValueError('alias_review_or_source_changed')
        at = datetime.fromisoformat(observed_at)
        if at.tzinfo is None:
            raise ValueError('alias_observation_timezone_required')
        matches = [r for r in reviews if all(security.get(k) == r['security'].get(k) for k in (*IDENTITY,*OPTIONAL_ID))
                   and r['provider'] == provider and r['provider_security_code'] == provider_code
                   and r['provider_name'] == provider_name and r['market'] == market
                   and r['provider_class'] == provider_class
                   and datetime.fromisoformat(r['observed_from']) <= at <= datetime.fromisoformat(r['observed_through'])]
        if len(matches) != 1 or digest(matches[0]) in self._revoked:
            raise ValueError('alias_no_unique_active_exact_binding')
        r = matches[0]
        return dict(contract=CONTRACT, status='IDENTITY_VALIDATED_BY_VERSIONED_PROOF',
                    registered_name=security['company_name'], provider_name=provider_name,
                    canonical_security_id=security['canonical_security_id'], review_sha256=digest(r),
                    source_sha256=[e['sha256'] for e in r['evidence']], observed_at=observed_at,
                    warnings=deepcopy(r.get('warnings', [])), allowed_use='NAME_MAPPING_ONLY',
                    valuation_grant=False, direction_grant=False)
