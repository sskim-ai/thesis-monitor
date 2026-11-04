"""Shadow-only comparison authority, layered after the unchanged M12DK owner."""

from copy import deepcopy
from datetime import date
from urllib.parse import urlparse

from app.models.financial import FinancialSnapshot
from app.services.cross_market_decision_engine_service import _compact
from app.services.financial_observation_quality_service import (
    CONTRACT,
    build_reported_observation_quality,
    digest,
)
from app.services.sec_business_field_quality_service import reported_comparison_quality
from scripts.m12da_source_use_contract import SourceUse, canonical_sha256
from scripts.m12dk_current_source_authority import build_current_source_authority
from scripts.m12dp_observed_business_coverage import _validate_issuer_binding
from app.services.reported_business_projection import comparative_admission_errors, ISSUER_CONTRACT
from app.services.reported_comparison_facts import comparative_facts


FAMILY = "OBSERVED_COMPARATIVE_FINANCIAL_FACT"
ISSUER_CONTEXT_FAMILY = "ISSUER_REPORTED_CONTEXT"
_ALLOWED = {SourceUse.CONTEXT.value, SourceUse.BUSINESS_CONTEXT.value,
            SourceUse.PASS_A_ARCHETYPE.value, SourceUse.OVERALL_DIRECTION.value}


def source_quality(bundle):
    """Recompute from declared immutable source inputs, never trust a PASS flag."""
    expected = bundle["source_inputs_sha256"]
    inputs = bundle["source_inputs"]
    if digest(inputs) != expected:
        raise ValueError("reported_quality_frozen_source_digest_mismatch")
    if bundle.get("selected_source_identity"):
        from scripts.m12ds_r4_r2_selected_source_quality import identity
        if identity(FinancialSnapshot.model_validate(inputs["formal"])) != bundle["selected_source_identity"]:
            raise ValueError("reported_quality_selected_source_identity_mismatch")
    if inputs["formal"].get("provider") == "sec_companyfacts":
        return reported_comparison_quality(
            formal=FinancialSnapshot.model_validate(inputs["formal"]),
            comparison=(FinancialSnapshot.model_validate(inputs["comparison"])
                        if inputs.get("comparison") else None),
            ticker=inputs["ticker"], cutoff=date.fromisoformat(inputs["cutoff"]),
            fiscal_policy=inputs.get('issuer_fiscal_policy'), allow_annual=inputs.get('exact_annual_owner') is True,
        )
    if inputs["formal"].get("provider") == "sec_foreign_filing":
        from app.services.sec_foreign_comparison_service import foreign_comparison_quality
        return foreign_comparison_quality(
            formal=FinancialSnapshot.model_validate(inputs["formal"]),
            candidates=[FinancialSnapshot.model_validate(r) for r in inputs.get("foreign_candidates", [])],
            ticker=inputs["ticker"], cutoff=date.fromisoformat(inputs["cutoff"]),
            allow_reported_half_year=inputs.get('foreign_period_policy') == 'EXACT_REPORTED_QUARTER_OR_HALF_YEAR_NO_SUBTRACTION',
            allow_inline_annual=inputs.get('exact_annual_owner') is True,
            source_documents=inputs.get('foreign_source_documents'),
        )
    return build_reported_observation_quality(
        formal=FinancialSnapshot.model_validate(inputs["formal"]),
        preliminary=(FinancialSnapshot.model_validate(inputs["preliminary"])
                     if inputs.get("preliminary") else None),
        ticker=inputs["ticker"], cutoff=date.fromisoformat(inputs["cutoff"]),
    )


def issuer_projection_receipt(*, security_stock, underlying_ticker, issuer_binding, cutoff):
    """Bind issuer business only; never copy an ADR ratio or denominator."""
    valuation = security_stock.get("valuation") or {}
    provenance = valuation.get("security_identity_provenance") or {}
    evidence = provenance.get("evidence") or {}
    fields = provenance.get("field_provenance") or {}
    errors = []
    try:
        issuer_ok = _validate_issuer_binding(
            issuer_binding, expected_sha256=canonical_sha256(issuer_binding), ticker=underlying_ticker,
            generation=issuer_binding.get("source_generation_id"), market="kr")
    except (ValueError, KeyError, TypeError):
        issuer_ok = False
    if (
        valuation.get("security_identity_state") != "verified_depositary"
        or valuation.get("security_identity_conflict_reasons")
        or provenance.get("contract_version") != "authoritative-security-identity-v1"
        or provenance.get("provider") != "sec_official_identity"
        or provenance.get("source_tier") != "tier_a_authoritative"
        or not issuer_ok
        or issuer_binding.get("ticker") != underlying_ticker
        or issuer_binding.get("source_record", {}).get("ticker") != underlying_ticker
    ):
        errors.append("issuer_projection_owner_unverified")
    expected = {"ticker": security_stock["ticker"], "ordinary_share_identifier": underlying_ticker,
                "cik": evidence.get("cik")}
    for key, value in expected.items():
        row = fields.get(key) or {}
        url = urlparse(str(row.get("source_url") or ""))
        try:
            temporal = date.fromisoformat(row["as_of"]) <= date.fromisoformat(cutoff)
        except (KeyError, TypeError, ValueError):
            temporal = False
        if (
            not value or row.get("value") != value or evidence.get(key) != value
            or row.get("verification_status") != "verified"
            or row.get("provider") != "sec_official_identity"
            or row.get("source_tier") != "tier_a_authoritative"
            or not temporal or row.get("filing_accession") != evidence.get("filing_accession")
            or not row.get("filing_accession") or url.scheme != "https"
            or url.hostname != "www.sec.gov" or not url.path.startswith("/Archives/edgar/data/")
            or row.get("source_url") != evidence.get("source_url")
        ):
            errors.append("issuer_projection_field_unverified:" + key)
    return {
        "contract": CONTRACT, "status": "FAIL" if errors else "PASS", "errors": errors,
        "security_ticker": security_stock["ticker"], "underlying_ticker": underlying_ticker,
        "issuer_id": issuer_binding.get("issuer_id"),
        "identity_provenance_sha256": digest(provenance),
        "issuer_binding_sha256": canonical_sha256(issuer_binding),
        "source_refs": [fields.get(k, {}).get("source_reference") for k in expected],
        "scope": "issuer_business_only", "security_valuation_transfer": False,
    }


def build_source_authority(*, quality_bundles, issuer_bindings, versioned_business_inputs=None,
                           persisted_event_inputs=None, fresh_business_inputs=None, **kwargs):
    current = build_current_source_authority(**kwargs)
    ticker = kwargs["ticker"]
    packet = kwargs["source_packet"]
    stock = next(s for s in packet["stocks"] if s["ticker"] == ticker)
    metadata = {r["ref_id"]: r for r in kwargs["source_metadata"]}
    records = {r["ref_id"]: r for r in current["authority"]["authority_records"]}
    quality = None
    projection = None
    versioned = None
    fresh = None
    if fresh_business_inputs is not None:
        from app.services.fresh_financial_stock_owner import assemble_fresh_stock
        if quality_bundles or issuer_bindings or versioned_business_inputs or persisted_event_inputs:
            raise ValueError('fresh_business_authority_ambiguous_owner')
        fresh = assemble_fresh_stock(**fresh_business_inputs)
        if (fresh['status'] != 'PASS' or fresh['packet'] != packet
                or fresh['evidence_packet'] != kwargs['evidence_packet']
                or fresh['fresh_run_id'] != kwargs['source_generation_id']):
            raise ValueError('fresh_business_authority_replay_mismatch')
        source_ticker = None
    elif versioned_business_inputs is not None:
        from app.services.versioned_business_stock_owner import replay_version
        if quality_bundles or issuer_bindings or versioned_business_inputs.get('ticker') != ticker:
            raise ValueError('versioned_business_authority_ambiguous_owner')
        if versioned_business_inputs['cutoff'].isoformat() != packet.get('generated_at'):
            raise ValueError('versioned_business_authority_cutoff_mismatch')
        versioned = replay_version(**versioned_business_inputs)
        source_ticker = None
    elif ticker in quality_bundles:
        source_ticker = ticker
    else:
        source_ticker = ((stock.get("valuation") or {}).get("security_identity_provenance") or {}).get(
            "evidence", {}).get("ordinary_share_identifier")
    if fresh is not None:
        expected_facts = [f for f in fresh['packet']['stocks'][0]['fact_catalog']
                          if 'canonical:' + f['fact_id'] in fresh['comparative_fact_refs']]
    elif versioned is not None:
        expected_facts = versioned['facts']
    elif source_ticker in quality_bundles:
        bundle = quality_bundles[source_ticker]
        if (bundle.get("source_generation_id") != kwargs["source_generation_id"]
                or bundle["source_inputs"].get("ticker") != source_ticker
                or bundle["source_inputs"].get("cutoff") != packet["assessment_date"]):
            raise ValueError("quality_source_generation_subject_or_cutoff_mismatch")
        quality = source_quality(bundle)
        if ticker != source_ticker:
            projection = issuer_projection_receipt(
                security_stock=stock, underlying_ticker=source_ticker,
                issuer_binding=issuer_bindings[source_ticker], cutoff=packet["assessment_date"])
        expected_facts = comparative_facts(quality, ticker=ticker,
                                          issuer_id=issuer_bindings[source_ticker]["issuer_id"],
                                          projection=projection)
    else:
        expected_facts = []
    expected = {"canonical:" + f["fact_id"]: f for f in expected_facts}
    actual = {"canonical:" + f["fact_id"]: f for f in stock.get("fact_catalog", ())
              if f.get("fact_type") == "earnings_comparison"}
    for receipt in current["family_receipts"]:
        ref = receipt["ref_id"]
        row, record = metadata[ref], records[ref]
        if not str(row.get("source_ref", "")).startswith("stock.fact_catalog.earnings_comparison:"):
            continue
        if row.get("reported_comparison") is not None:
            from app.services.reported_comparison_context import context_for_fact, CONTRACT as CONTEXT_CONTRACT
            fact = expected.get(ref)
            if fresh is None or fact is None or actual.get(ref) != fact:
                raise ValueError("comparison_context_original_owner_required")
            expected_context = context_for_fact(stock, fact, ticker=ticker,
                packet_id=kwargs["evidence_packet"]["packet_id"],
                assessment_date=packet["assessment_date"])
            if (expected_context is None or expected_context.model_dump(mode="json") != row["reported_comparison"]
                    or record["source_family"] != "unclassified"):
                raise ValueError("comparison_context_authority_mismatch")
            allowed = {SourceUse.CONTEXT.value}
            record.update(authority_state="RESOLVED", authority_basis=CONTEXT_CONTRACT,
                source_type="HISTORICAL_REPORTED_CONTEXT", source_family="HISTORICAL_REPORTED_CONTEXT",
                source_scope="historical_source_attribution_not_collection_start_possession_or_direction",
                allowed_uses=sorted(allowed),
                prohibited_uses=sorted({u.value for u in SourceUse} - allowed),
                denial_reasons=["NO_DIRECTIONAL_AUTHORITY", "NO_COLLECTION_START_POSSESSION_CLAIM"],
                compatible_source_versions=[CONTEXT_CONTRACT])
            receipt.update(errors=[], source_family=record["source_family"],
                authority_state=record["authority_state"], authority_basis=CONTEXT_CONTRACT,
                allowed_uses=record["allowed_uses"], comparison_context_sha256=digest(row["reported_comparison"]),
                selected_owner_sha256=fresh["selected_financial_owner"]["envelope_sha256"])
            continue
        fact = expected.get(ref)
        errors = comparative_admission_errors(fact=actual.get(ref), expected=fact,
            statement=row.get("statement"), expected_statement=_compact(fact["fields"]) if fact else None,
            category=row.get("category"), as_of=row.get("as_of"), source_family=record["source_family"])
        # Purpose follows the replayed owner, not presence of a caller-visible tag.
        issuer_context = bool((fresh and fresh.get('issuer_business_bridge'))
                              or projection or (fact or {}).get('issuer_projection'))
        tagged_context = (row.get('reported_business') or {}).get('kind') == 'ISSUER_CONTEXT'
        if tagged_context:
            from app.services.reported_business_projection import projection_for_fact
            if fresh is None or not fresh.get('issuer_business_bridge') or fact is None:
                raise ValueError('issuer_context_original_fresh_owner_required')
            owned_context = projection_for_fact(stock, fact, ticker=ticker,
                packet_id=kwargs['evidence_packet']['packet_id'], assessment_date=packet['assessment_date'],
                market=packet['market'])
            if (owned_context is None or owned_context.model_dump(mode='json') != row['reported_business']
                    or owned_context.contract != ISSUER_CONTRACT or owned_context.allowed_uses != ('CONTEXT',)):
                raise ValueError('issuer_context_authority_mismatch')
        owner = quality["contract"] if quality else CONTRACT
        receipt.update(source_family=FAMILY, errors=errors, quality_contract=owner,
                       quality_receipt_sha256=quality["receipt_sha256"] if quality else None)
        if fresh is not None:
            receipt.update(source_acquisition_class='FRESH_CURRENT_RUN',
                fresh_run_id=fresh['fresh_run_id'], fresh_owner_sha256=digest(fresh),
                quality_receipt_sha256=fact['quality_receipt_sha256'] if fact else None)
        if versioned is not None:
            receipt.update(source_acquisition_class='VERSIONED_PERSISTED_ALLOWED',
                source_version_sha256=versioned['version_sha256'],
                original_source_artifact_sha256=versioned['original_source_artifact_sha256'],
                current_eligibility_sha256=digest(versioned['eligibility']),
                quality_receipt_sha256=fact['quality_receipt_sha256'] if fact else None)
        if not errors:
            allowed = {SourceUse.CONTEXT.value} if issuer_context else _ALLOWED
            record.update(authority_state="RESOLVED", authority_basis=CONTRACT,
                          source_type=FAMILY, source_family=FAMILY,
                          source_scope="exact_comparative_issuer_business_no_valuation",
                          allowed_uses=sorted(allowed),
                          prohibited_uses=sorted({u.value for u in SourceUse} - allowed),
                          denial_reasons=["no_recurring_profit_or_security_valuation_authority"],
                          compatible_source_versions=[CONTRACT, owner] if owner != CONTRACT else [CONTRACT])
            if issuer_context:
                record.update(authority_basis=ISSUER_CONTRACT,
                    source_type=ISSUER_CONTEXT_FAMILY, source_family=ISSUER_CONTEXT_FAMILY,
                    source_scope='issuer_context_only_no_security_direction_or_valuation',
                    denial_reasons=['NO_SECURITY_DIRECTIONAL_TRANSFER', 'NO_SECURITY_VALUATION_TRANSFER'],
                    compatible_source_versions=[ISSUER_CONTRACT])
        receipt.update(source_family=record['source_family'],
                       allowed_uses=record["allowed_uses"], authority_state=record["authority_state"],
                       authority_basis=record["authority_basis"])
    manifest = current["authority"]
    if fresh is not None and fresh.get('issuer_business_bridge'):
        from app.services.reported_business_projection import projection_for_fact
        facts_by_ref = {'canonical:' + f['fact_id']: f for f in stock['fact_catalog']}
        original_rows = {row['ref_id']: row for row in fresh['evidence_packet']['evidence']}
        quality_ref = fresh['quality_view']['receipt']['canonical_ref']
        for receipt in current['family_receipts']:
            ref = receipt['ref_id']
            value = metadata[ref].get('reported_business')
            legacy_quality = ref == quality_ref and not value
            if not legacy_quality and (not value or value.get('contract') != ISSUER_CONTRACT):
                continue
            if legacy_quality:
                if metadata[ref] != original_rows.get(ref):
                    raise ValueError('issuer_context_legacy_quality_replay_mismatch')
                kind = 'QUALITY'
            else:
                owned = projection_for_fact(stock, facts_by_ref[ref], ticker=ticker,
                    packet_id=kwargs['evidence_packet']['packet_id'], assessment_date=packet['assessment_date'],
                    market=packet['market'])
                if owned is None or owned.model_dump(mode='json') != value:
                    raise ValueError('issuer_context_authority_mismatch')
                kind = owned.kind
            record = records[ref]
            quality_narrowing = (kind == 'QUALITY'
                and record['source_family'] == 'typed_quality'
                and record['authority_state'] == 'RESOLVED'
                and set(record['allowed_uses']) == {'CONTEXT', 'CONFIDENCE'})
            if not quality_narrowing and record['source_family'] not in {'unclassified', ISSUER_CONTEXT_FAMILY}:
                raise ValueError('issuer_context_existing_restrictive_owner')
            allowed = {SourceUse.CONTEXT.value}
            record.update(authority_state='RESOLVED', authority_basis=ISSUER_CONTRACT,
                source_type=ISSUER_CONTEXT_FAMILY, source_family=ISSUER_CONTEXT_FAMILY,
                source_scope='issuer_attribution_only_no_security_economic_effect',
                allowed_uses=sorted(allowed), prohibited_uses=sorted({u.value for u in SourceUse} - allowed),
                denial_reasons=['NO_SECURITY_DIRECTIONAL_TRANSFER', 'NO_SECURITY_CONFIDENCE_OR_QUALITY_TRANSFER'],
                compatible_source_versions=[ISSUER_CONTRACT])
            receipt.update(errors=[], source_family=ISSUER_CONTEXT_FAMILY, authority_state='RESOLVED',
                authority_basis=ISSUER_CONTRACT, allowed_uses=record['allowed_uses'],
                selected_owner_sha256=fresh['selected_financial_owner']['envelope_sha256'])
    if fresh is not None and fresh.get('context_fact_refs'):
        for receipt in current['family_receipts']:
            if receipt['ref_id'] not in fresh['context_fact_refs']:
                continue
            record = records[receipt['ref_id']]
            if record['source_family'] != 'unclassified':
                raise ValueError('fresh_context_existing_restrictive_owner')
            allowed = {SourceUse.CONTEXT.value}
            record.update(authority_state='RESOLVED', authority_basis='reported-comparison-applicability-v1',
                source_family='REPORTED_ABSOLUTE_CONTEXT', source_type='REPORTED_ABSOLUTE_CONTEXT',
                source_scope='current_reported_context_no_comparison_quality_or_direction',
                allowed_uses=sorted(allowed), prohibited_uses=sorted({u.value for u in SourceUse} - allowed),
                denial_reasons=['ABSOLUTE_CURRENT_FINANCIAL_IS_NOT_DIRECTIONAL_EVIDENCE'])
            receipt.update(errors=[], source_family=record['source_family'],
                authority_state=record['authority_state'], authority_basis=record['authority_basis'],
                allowed_uses=record['allowed_uses'],
                fresh_owner_sha256=digest(fresh), comparison_applicability=fresh['quality_view']['receipt'])
            receipt.pop('earnings_lineage', None)
    if persisted_event_inputs is not None:
        from app.services.persisted_business_event_owner import replay_persisted_event
        from app.services.unified_stock_event_input import replay_news
        from app.services.canonical_fact_service import canonical_event_fact
        source, receipt = replay_persisted_event(**persisted_event_inputs)
        if (receipt['ticker'] != ticker or receipt['current_run_id'] != kwargs['source_generation_id']
                or receipt['current_eligibility_cutoff'] != packet['generated_at']):
            raise ValueError('persisted_event_authority_current_identity_mismatch')
        replayed = replay_news(source, security=source.read.security,
            business_cutoff=persisted_event_inputs['cutoff'], policy=persisted_event_inputs['policy'])
        expected_events = [canonical_event_fact(r) for r in replayed['evidence']]
        if (stock.get('evidence') != replayed['evidence'] or
                [f for f in stock['fact_catalog'] if f['fact_id'].startswith('event:')] != expected_events):
            raise ValueError('persisted_event_authority_source_mismatch')
        manifest['persisted_business_event_source'] = receipt
        for item in current['family_receipts']:
            if item['ref_id'] in {'canonical:' + f['fact_id'] for f in expected_events}:
                item['persisted_business_event_receipt_sha256'] = digest(receipt)
                record = records[item['ref_id']]
                # Resolving the source bytes is not permission to confirm the
                # headline or use it as decisive directional/valuation evidence.
                if (record['source_family'] == 'unclassified'
                        and record['allowed_uses'] == [SourceUse.CONTEXT.value]):
                    record.update(authority_state='RESOLVED', authority_basis=receipt['contract'],
                        source_type=receipt['state'], source_family=receipt['state'],
                        source_scope='source_verified_headline_context_only_requires_review',
                        denial_reasons=['linked_headline_not_confirmed_contract_or_official_financial'],
                        required_metadata=['exact_raw_source_replay', 'historical_acquisition_identity',
                                           'current_eligibility', 'requires_review'],
                        compatible_source_versions=[receipt['contract']])
                    item.update(source_family=receipt['state'], authority_state=record['authority_state'],
                                authority_basis=record['authority_basis'])
    if fresh is not None and fresh.get('event_view') is not None:
        event = fresh['event_view']['receipt']
        manifest['fresh_controller_event_source'] = event
        for item in current['family_receipts']:
            if item['ref_id'] not in fresh['event_fact_refs']:
                continue
            record = records[item['ref_id']]
            if record['source_family'] != 'unclassified' or record['allowed_uses'] != ['CONTEXT']:
                raise ValueError('fresh_event_existing_restrictive_authority')
            family = ('PERSISTED_SOURCE_OWNED_BUSINESS_EVENT' if event['acquisition_class'] ==
                      'PERSISTED_SOURCE_RECHECK' else 'FRESH_SOURCE_OWNED_BUSINESS_EVENT')
            record.update(source_family=family, source_type=family, authority_state='RESOLVED',
                authority_basis=event['contract'], source_scope='source_verified_headline_context_only_requires_review',
                allowed_uses=event['allowed_uses'], prohibited_uses=event['prohibited_uses'],
                denial_reasons=['linked_headline_not_confirmed_contract_or_official_financial'])
            item.update(errors=[], source_family=family, authority_state='RESOLVED',
                authority_basis=event['contract'], allowed_uses=event['allowed_uses'],
                current_event_eligibility_sha256=event['receipt_sha256'])
    manifest.update(reported_quality_owner_contract=CONTRACT,
                    current_source_family_receipts_sha256=canonical_sha256(current["family_receipts"]))
    manifest.pop("authority_manifest_sha256")
    manifest["authority_manifest_sha256"] = canonical_sha256(manifest)
    return current
