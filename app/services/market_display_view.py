"""Independent display permission; never a Market directional permission grant.

The sealed adapter supplies provenance only after its authority checks. Display
decisions and alias bindings are rebuilt against the exact canonical source at
render time. Publication permission is field-scoped to the published level.
"""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.services.macro_source_time import CONTRACT as TIME_CONTRACT
from app.services.market_numeric_claim_service import digest, number
from app.services.numeric_semantic_registry import build_numeric_registry


class Frozen(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class MarketDirectionalModelView(Frozen):
    contract: Literal['market-directional-model-view-v1'] = 'market-directional-model-view-v1'
    market: str
    generation_id: str
    context_sha256: str
    schema_sha256: str
    eligible_refs: tuple[str, ...]


class MarketDisplayEligibilityDecision(Frozen):
    fact_ref: str
    generation_id: str
    source_sha256: str
    fact_sha256: str
    observation_date: str
    status: Literal['ELIGIBLE', 'DENIED']
    basis: str
    allowed_fields: tuple[str, ...]
    reasons: tuple[str, ...]
    directional_permission_granted: Literal[False] = False


class MarketDisplayIdentityBinding(Frozen):
    alias_ref: str
    canonical_ref: str
    alias_field: str
    semantic_field: str
    semantic_type: str
    value: float
    unit: str
    session: str
    generation_id: str
    source_sha256: str
    binding_sha256: str


class MarketDisplayOrigin(Frozen):
    generation_id: str
    query_as_of: str
    authority_sha256: str
    source_packet_sha256: str
    source_sha256: str
    component_sha256: str
    publication_origins: dict[str, dict]
    alias_payloads: dict[str, dict]
    alias_audit: dict
    directional_refs: tuple[str, ...]


class MarketUserDisplayView(Frozen):
    contract: Literal['market-user-display-view-v1'] = 'market-user-display-view-v1'
    market: str
    assessment_date: str
    completed_session: str
    origin: MarketDisplayOrigin
    decisions: tuple[MarketDisplayEligibilityDecision, ...]
    identity_bindings: tuple[MarketDisplayIdentityBinding, ...]

    @property
    def eligible_refs(self):
        return tuple(d.fact_ref for d in self.decisions if d.status == 'ELIGIBLE')


def _require(ok, reason):
    if not ok:
        raise ValueError('market_display_' + reason)


def display_origin(packet, seed, source, context, aliases, authority_sha256, refs):
    """Called by the sealed adapter after source/occurrence/numeric validation."""
    publications = packet['publication_context']
    origins = {}
    if publications.get('contract') == 'fresh-publication-replay-v1':
        _require(publications['run_id'] == seed['parent_run_id'], 'publication_generation')
        for fact in source['fact_catalog']:
            paths = refs.get(fact['fact_id'], [])
            for path in paths:
                parts = path.split('/')
                if len(parts) != 6 or parts[:2] != ['publication_context', 'providers']:
                    continue
                doc = publications['providers'][parts[2]]
                observation = doc['value']['observations'][int(parts[-1])]
                temporal = observation['raw_payload']['publication_context']
                _require(temporal == fact['fields'].get('publication_context'), 'publication_occurrence')
                row = dict(generation_id=publications['run_id'], query_as_of=temporal['query_as_of'],
                    source_hashes=sorted(doc['source_hashes'].values()),
                    publication_context_sha256=digest(temporal), observation_sha256=digest(observation),
                    provider_value_sha256=doc['value_sha256'], fact_sha256=digest(fact), source_path=path)
                _require(fact['fact_id'] not in origins or origins[fact['fact_id']] == row,
                         'publication_ambiguous_origin')
                origins[fact['fact_id']] = row
    return MarketDisplayOrigin(generation_id=seed['parent_run_id'], query_as_of=seed['started_at'],
        authority_sha256=authority_sha256, source_packet_sha256=digest(packet), source_sha256=digest(source),
        component_sha256=digest(packet['market_sources']['component']), publication_origins=origins,
        alias_payloads={r:p for r,p in context['facts'].items() if p.get('kind') == 'indices' and 'fields' not in p},
        alias_audit=aliases, directional_refs=tuple(sorted(context['request_eligible_refs'])))


def _bindings(source, origin, registry, completed):
    _require(origin.alias_audit.get('status') == 'PASS', 'alias_audit_failed')
    by_id = {f['fact_id']:f for f in source['fact_catalog']}
    bindings, keys, canonical_keys = [], set(), set()
    for row in origin.alias_audit.get('rows', []):
        alias = row['alias_ref']
        if alias not in origin.alias_payloads:
            continue
        payload = origin.alias_payloads[alias]
        ref, field = row['canonical_ref'], row['canonical_path']
        canonical = by_id.get(ref, {})
        reg = registry.get((ref, field), {})
        key = (alias, row['alias_path'])
        _require(key not in keys, 'alias_duplicate_conflict')
        _require((ref, field) not in canonical_keys, 'alias_duplicate_canonical')
        keys.add(key)
        canonical_keys.add((ref, field))
        _require(alias in origin.directional_refs and payload.get('source_ref') == alias,
                 'alias_unbound')
        _require(canonical.get('fact_type') == 'market_cross_section_index'
                 and payload.get('symbol') == canonical.get('fields', {}).get('symbol')
                 and payload.get('as_of_date') == canonical.get('as_of_date') == completed,
                 'alias_identity_or_session')
        _require(field == 'fields.' + row['alias_path'] and row['alias_path'] in {'close', 'return_pct'},
                 'alias_field')
        _require(reg.get('registered') is True
                 and number(row['value']) and row.get('registered') is True
                 and row['value'] == payload.get(row['alias_path']) == reg.get('value')
                 == canonical['fields'].get(row['alias_path'])
                 and row.get('unit') == reg.get('unit')
                 and row.get('semantic_type') == reg.get('semantic_type'), 'alias_numeric_semantic')
        # A typed index label can own deterministic display even when generic
        # prose has no series_code label. It cannot override a quality denial.
        _require(reg.get('financial_quality_state') in {'verified_usable','caution_usable'}
                 and not reg.get('denial_reason') and not reg.get('financial_quality_reason_codes')
                 and (reg.get('prose_allowed') is True or (
                     row['alias_path'] == 'return_pct' and reg['semantic_type'] == 'index_return_pct'
                     and reg['unit'] == 'pct' and reg.get('canonical_label_required') is True
                     and reg.get('canonical_label') is None)), 'alias_display_quality')
        data = dict(alias_ref=alias, canonical_ref=ref, alias_field=row['alias_path'], semantic_field=field,
            semantic_type=reg['semantic_type'], value=float(row['value']), unit=reg['unit'], session=completed,
            generation_id=origin.generation_id, source_sha256=origin.source_sha256)
        bindings.append(MarketDisplayIdentityBinding(**data, binding_sha256=digest(data)))
    for alias in origin.alias_payloads:
        _require({(alias, 'close'), (alias, 'return_pct')} <= keys, 'alias_incomplete')
    return tuple(sorted(bindings, key=lambda b:(b.alias_ref, b.alias_field)))


def build_display_view(source, *, market, assessment_date, origin):
    origin = MarketDisplayOrigin.model_validate(origin)
    _require(origin.source_sha256 == digest(source), 'source_hash')
    _require(bool(origin.generation_id) and all(len(h) == 64 for h in
        (origin.authority_sha256, origin.source_packet_sha256, origin.component_sha256)), 'origin_identity')
    query = datetime.fromisoformat(origin.query_as_of)
    _require(query.utcoffset() is not None, 'query_timezone')
    session = source['session']
    completed = session['latest_completed_regular_session_date']
    _require(session['market'] == market and session['assessment_date'] == assessment_date
             and completed <= assessment_date, 'session_identity')
    facts = source['fact_catalog']
    _require(len({f['fact_id'] for f in facts}) == len(facts), 'duplicate_fact')
    registry = {(r['fact_id'], r['field_path']):r for r in source['numeric_registry']}
    _require(len(registry) == len(source['numeric_registry']), 'duplicate_registry')
    expected_registry = {(r['fact_id'], r['field_path']):r for r in build_numeric_registry(facts)}
    _require(registry == expected_registry, 'registry_semantic_identity')
    bindings = _bindings(source, origin, registry, completed)
    alias_fields = {}
    for b in bindings:
        alias_fields.setdefault(b.canonical_ref, set()).add(b.semantic_field)
    decisions = []
    for fact in sorted(facts, key=lambda f:f['fact_id']):
        ref, fields = fact['fact_id'], fact['fields']
        eligible_fields = {p for (r,p),v in registry.items() if r == ref and v.get('registered') is True
                           and v.get('prose_allowed') is True and v.get('scope') in {'market','both'}
                           and number(v.get('value'))}
        allowed, reasons, basis = set(), [], 'NO_DISPLAY_OWNER'
        publication = fields.get('publication_context')
        if publication is not None:
            basis = 'LATEST_PUBLISHED_LEVEL_ONLY'
            provenance = origin.publication_origins.get(ref, {})
            try:
                observed = date.fromisoformat(fact['as_of_date'])
                retrieved = datetime.fromisoformat(publication['retrieved_at'])
                published = publication.get('published_at')
                valid = (publication.get('contract') == TIME_CONTRACT
                    and publication.get('display_eligible') is True
                    and publication.get('latest_available_at_query_time') is True
                    and publication.get('freshness_state') in {'CURRENT_SESSION_OR_DATE','LATEST_PUBLISHED_VERIFIED'}
                    and publication.get('series_code') == fields.get('series_code')
                    and publication.get('provider') == fact.get('source')
                    and publication.get('observation_date') == fact['as_of_date']
                    and observed <= query.date() and fact['as_of_date'] <= assessment_date
                    and datetime.fromisoformat(publication['query_as_of'])
                        == datetime.fromisoformat(provenance['query_as_of']) == query
                    and provenance.get('generation_id') == origin.generation_id
                    and publication.get('response_sha256') in provenance.get('source_hashes', [])
                    and provenance.get('publication_context_sha256') == digest(publication)
                    and provenance.get('fact_sha256') == digest(fact)
                    and retrieved.utcoffset() is not None and retrieved >= query
                    and (published is None or (datetime.fromisoformat(published).utcoffset() is not None
                                              and datetime.fromisoformat(published) <= query)))
            except (KeyError, TypeError, ValueError):
                valid = False
            if valid:
                allowed = eligible_fields & {'fields.level_pct','fields.level','fields.price_usd_per_barrel','fields.value'}
            else:
                reasons.append('publication_current_generation_or_latest_unproven')
        elif ref in alias_fields:
            basis, allowed = 'EXACT_ALIAS_CANONICAL', alias_fields[ref]
        elif ref in origin.directional_refs:
            basis = 'EXISTING_CURRENT_DIRECTIONAL_OWNER'
            allowed = eligible_fields
        if (fields.get('source_unavailable') or fields.get('renderer_only')
                or fields.get('quality', 'fresh') not in {'fresh','verified'}):
            allowed = set()
            reasons.append('hard_display_quality_denial')
        if not allowed and not reasons:
            reasons.append('no_owned_display_fields')
        decisions.append(MarketDisplayEligibilityDecision(fact_ref=ref, generation_id=origin.generation_id,
            source_sha256=origin.source_sha256, fact_sha256=digest(fact), observation_date=fact['as_of_date'],
            status='ELIGIBLE' if allowed else 'DENIED', basis=basis, allowed_fields=tuple(sorted(allowed)),
            reasons=tuple(reasons)))
    return MarketUserDisplayView(market=market, assessment_date=assessment_date, completed_session=completed,
        origin=origin, decisions=tuple(decisions), identity_bindings=bindings)


def verify_display_view(view, source):
    view = MarketUserDisplayView.model_validate(view)
    expected = build_display_view(source, market=view.market, assessment_date=view.assessment_date, origin=view.origin)
    _require(view == expected, 'view_binding_mismatch')
    return view


def market_views(source, context, schema, *, market, assessment_date, origin):
    directional = MarketDirectionalModelView(market=market, generation_id=origin.generation_id,
        context_sha256=digest(context), schema_sha256=digest(schema), eligible_refs=origin.directional_refs)
    display = build_display_view(source, market=market, assessment_date=assessment_date, origin=origin)
    # Display-only permission cannot enter even an alias in the directional view.
    display_only = {d.fact_ref for d in display.decisions
                    if d.status == 'ELIGIBLE' and d.basis == 'LATEST_PUBLISHED_LEVEL_ONLY'}
    _require(not (display_only & set(context['request_eligible_refs'])), 'directional_display_leak')
    _require(not any(f.get('fields', {}).get('publication_context') for f in context['facts'].values()),
             'directional_publication_alias_leak')
    return dict(directional=directional.model_dump(mode='json'), display=display.model_dump(mode='json'),
        receipt=dict(status='PASS', directional_sha256=digest(directional.model_dump(mode='json')),
            display_sha256=digest(display.model_dump(mode='json')), display_only_refs=sorted(display_only),
            directional_context_sha256=digest(context), schema_sha256=digest(schema),
            alias_bindings_sha256=digest([b.model_dump(mode='json') for b in display.identity_bindings])))
