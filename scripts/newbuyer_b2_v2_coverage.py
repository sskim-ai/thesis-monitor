"""Opt-in, pre-model coverage over sealed source owners. No I/O or model input.

The consumer contract and category decisions are unchanged. Collection receipts
bind the input bytes; typed source owners, not the seal itself, own decisions.
"""
from collections import Counter
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
import json
from pathlib import Path

from app.services import canonical_business_quality_owner as business
from app.services.unavailable_price_valuation import parse_view
from app.services.kr_forward_valuation_context import KrForwardValuationView
from app.services.kr_forward_valuation_context import calibration_context as kr_context
from app.services.provider_valuation_calibration_context import calibration_context
from scripts import newbuyer_coverage_cells as cells
from scripts import newbuyer_fper_prerequisite_scope as scope
from scripts import kis_no_estimate_owner as availability
from scripts import newbuyer_b2_contract as v1
from scripts import newbuyer_b2_v2_policy as policy
from scripts.kis_eps_wire_calibration import digest, sealed, verified
from scripts.newbuyer_b2_shadow import qualified_facts

CONTRACT = 'REV56COfflineCoverageReproofV1'
INPUT_CONTRACT = 'FreshSourceCoverageInputsV1'
SEMANTICS = 'REV56B_CATEGORY_CELLS_PLUS_REV56C_NO_ESTIMATE_SCOPE'
MODEL_KEYS = {'core', 'cores', 'pass_a', 'pass_b', 'accepted', 'frozen_authority',
              'frozen_overall', 'frozen_holder', 'blind_labels', 'model_stances'}


@dataclass(frozen=True, kw_only=True)
class SourceOwners:
    generation: str
    stock: dict
    security: dict
    collection_receipt_sha256: str
    business_projection: dict | None = None
    kis_row: dict | None = None
    kis_plan: dict | None = None
    kis_corpus_sha256: str | None = None
    availability_inputs: dict | None = None


def require(value, reason):
    if not value:
        raise ValueError('fresh_coverage:' + reason)


def hash_value(value):
    require(isinstance(value, str) and len(value) == 64
            and all(c in '0123456789abcdef' for c in value), 'sha256_required')


def source_binding(value):
    require(type(value) is SourceOwners, 'source_owner_input_required_no_model_authority')
    require(not MODEL_KEYS.intersection(value.stock), 'model_output_not_coverage_authority')
    require(bool(value.generation), 'generation_required')
    hash_value(value.collection_receipt_sha256)
    # Bytes are reduced to their content hash, never decoded or put in a prompt.
    raw = (value.availability_inputs or {}).get('raw')
    availability_inputs = None if value.availability_inputs is None else {
        **value.availability_inputs, 'raw': sha256(raw).hexdigest() if raw is not None else None}
    return dict(generation=value.generation, stock_sha256=digest(value.stock),
        security_sha256=digest(value.security), collection_receipt_sha256=value.collection_receipt_sha256,
        business_projection_sha256=digest(value.business_projection),
        kis_row_sha256=digest(value.kis_row), kis_plan_sha256=digest(value.kis_plan),
        kis_corpus_sha256=value.kis_corpus_sha256,
        availability_inputs_sha256=digest(availability_inputs))


def seal_inputs(owners, *, subjects, semantics_version):
    require(semantics_version == SEMANTICS, 'unreviewed_dataflow_semantics')
    dataflow = dataflow_proof()
    require(subjects and len(set(subjects)) == len(subjects) and set(subjects) == set(owners),
            'cohort_binding')
    return sealed(dict(contract=INPUT_CONTRACT, subjects=sorted(subjects),
        semantics_version=semantics_version,
        rows={ticker: source_binding(owners[ticker]) for ticker in sorted(subjects)},
        dataflow_sha256=digest(dataflow), model_inputs_used=False))


def dataflow_proof():
    """Positive non-consumption needs the exact reviewed producer code, not absence."""
    root = Path(__file__).resolve().parents[1]
    expected = json.loads(Path(__file__).with_name('newbuyer_coverage_dataflow.json').read_bytes())
    require(expected and all(sha256((root / path).read_bytes()).hexdigest() == value
                             for path, value in expected.items()), 'producer_dataflow_changed')
    return expected


def _source_context(ticker, owners):
    stock, security = owners.stock, owners.security
    view = parse_view(stock['valuation_view'])
    require(stock['ticker'] == security['ticker'] == view.ticker == ticker, 'ticker_binding')
    require(stock['fresh_run_id'] == view.run_id == owners.generation, 'generation_binding')
    require(view.security_sha256 == digest(security)
            and view.security_id == security['canonical_security_id'], 'security_binding')
    require(stock['packet_sha256'] == digest(stock['packet']), 'packet_hash_binding')
    require(stock['input_hashes']['valuation'] == digest(stock['valuation_view']), 'valuation_hash_binding')
    for metric in view.metrics:
        native = metric.native_snapshot
        if native is not None:
            for value in (native.raw_sha256, native.source_receipt_sha256, native.snapshot_sha256):
                hash_value(value)
            identity = native.security_identity_receipt
            require(identity.get('run_id') == owners.generation
                    and identity.get('security_sha256') == digest(security), 'native_owner_generation_binding')
    quality = stock['quality_view']
    receipt, fact = quality['receipt'], quality['fact']
    verified(receipt, business.CONTRACT)
    require(fact is not None and receipt['inputs_complete'], 'selected_business_owner_required')
    require(receipt['source_generation_id'] == owners.generation
            and receipt['ticker'] == ticker and receipt['fact_sha256'] == digest(fact), 'business_binding')
    require(fact['fields'].get('decision_version') and fact['as_of_date'], 'business_decision_time')
    date.fromisoformat(fact['as_of_date'])
    require(stock['input_hashes']['quality'] == digest(quality), 'business_hash_binding')
    catalog = {f['fact_id']: f for f in stock['packet']['stocks'][0]['fact_catalog']}
    selected = [catalog[ref] for ref in receipt['input_fact_sha256']]
    projection = owners.business_projection if owners.business_projection is not None else stock['projection']
    require(receipt['projection_sha256'] == digest(projection), 'selected_business_projection_binding')
    from app.services.selected_financial_owner import validate as validate_selected_owner
    validate_selected_owner(stock['selected_financial_owner'], projection=projection,
        facts=selected, bridge=fact['issuer_business_bridge'])
    replay = business.derive_fresh(projection=projection, facts=selected, ticker=ticker,
        security_id=view.security_id, run_id=owners.generation,
        source_ticker=fact['source_ticker'], bridge=fact['issuer_business_bridge'])
    require(replay == quality, 'business_owner_replay')
    require(all(o['metadata'].get('filing_date') and o['quality'].get('decision_version')
                and o['quality'].get('fields') for o in receipt['owner_outputs']), 'business_temporal_decision_provenance')
    packet_stock = stock['packet']['stocks'][0]
    require(view.price_context_sha256 == digest(packet_stock['current_price_context']), 'price_owner_binding')
    completed = stock.get('completed_session_current_price')
    if completed is not None:
        require(completed['generation_id'] == owners.generation
                and completed['canonical_security_id'] == view.security_id
                and completed['current_price'] == view.price, 'completed_price_owner_binding')
    if view.price is None:
        require(stock.get('current_price_state') == view.price_state.model_dump(mode='json')
                == packet_stock.get('current_price_state')
                == packet_stock['current_price_context'].get('price_state'), 'typed_price_owner_binding')
    if owners.kis_row is None:
        require(owners.kis_plan is None and owners.availability_inputs is None,
                'partial_kis_input')
        context = calibration_context(view)
    else:
        plan = owners.kis_plan
        require(plan is not None and plan['generation_id'] == owners.generation, 'kis_generation_binding')
        verified(plan, plan['contract'])
        require(plan['securities'][ticker]['canonical_security_id'] == view.security_id
                and plan['securities'][ticker]['ticker'] == ticker, 'kis_security_binding')
        hash_value(owners.kis_corpus_sha256)
        context = kr_context(KrForwardValuationView(native=view, kis=owners.kis_row,
            as_of=plan['as_of'], fresh_plan_sha256=plan['receipt_sha256'],
            source_corpus_sha256=owners.kis_corpus_sha256))
    facts = qualified_facts({'valuation_context': context}, ticker, owners.generation)
    return context, facts


def _row(ticker, owners, context, facts):
    source, security = owners.stock, owners.security
    view, categories, relevant = source['valuation_view'], [], []
    for metric in context['metric_states']:
        if metric['metric'] not in {'PER', 'FORWARD_PE', 'CURRENT_FY1_FPER'}:
            continue
        name = metric['metric']
        ref = metric['fact_ref'] or 'unavailable-slot:' + view['security_id'] + ':' + name
        relevant.append(ref)
        family = 'DERIVED_KIS' if name == 'CURRENT_FY1_FPER' else 'ATOMIC'
        for requirement in cells.requirements(name, family, security):
            if family == 'ATOMIC':
                owned = next(m for m in view['metrics'] if m['metric'] == name)
                snapshot = owned['native_snapshot']
                if snapshot is None and owned.get('price_dependency') == 'CURRENT_PRICE_ARITHMETIC_REQUIRED':
                    categories.append(cells.price_prerequisite_cell(requirement, ticker, ref, source, owned))
                else:
                    require(snapshot is not None, 'native_owner_missing')
                    categories.append(cells.native_cell(requirement, ticker, ref, source, snapshot, security))
            else:
                categories.append(cells.kis_cell(requirement, ticker, ref, source, owners.kis_row, digest(context)))
    require(relevant, 'relevant_metric_universe_missing')
    categories.append(cells.business_cell(ticker, source))
    unresolved = [c for c in categories if c['coverage_disposition'] == 'UNRESOLVED']
    row = sealed(dict(contract=cells.CONTRACT, ticker=ticker,
        receipt_ref='source-coverage:' + digest([owners.generation, ticker, categories]),
        canonical_security_id=view['security_id'], source_generation=owners.generation,
        source_packet_sha256=digest(source['packet']), decision_axis='NEWBUYER',
        relevant_valuation_metric_refs=relevant,
        qualified_relevant_valuation_refs=sorted(v1.usable_facts({'facts': facts})),
        denied_relevant_valuation_refs=sorted({c['metric_ref'] for c in categories
            if c['category'] == 'VALUATION_SOURCE_QUALITY' and c['owner_state'] == 'DENIED'}),
        categories=categories, coverage_complete=not unresolved, coverage_incomplete_reasons=unresolved,
        owner_provenance_complete=not unresolved, temporal_provenance_complete=not unresolved,
        decision_provenance_complete=not unresolved, current_newbuyer_blocker_refs=None,
        global_valuation_blocker_refs=None, legacy_context_refs=[], legacy_context_veto_status='NOT_CONSUMED_PRE_MODEL',
        input_sha256=digest(source_binding(owners)), artifact_type='PRE_MODEL_SOURCE_OWNER_COMPOSITION'))
    if owners.kis_row is not None and owners.kis_row['current_fper']['state'] == 'UNAVAILABLE_EPS':
        inputs = owners.availability_inputs
        require(inputs is not None and inputs['generation'] == owners.generation
                and inputs['code'] == ticker and inputs['plan'] == owners.kis_plan, 'availability_generation_binding')
        assessment = availability.assess(**inputs)
        availability.validate_assessment(assessment, **inputs)
        if assessment['normal_empty_confirmed'] and assessment['owner_complete']:
            args = dict(evidence_inputs=inputs, old_eps=owners.kis_row['eps'], old_fper=owners.kis_row['current_fper'])
            prerequisite = scope.prerequisite_scope(assessment, **args)
            row, _ = scope.apply_to_coverage(row, assessment, prerequisite, **args)
    return row


def compose(owners, *, subjects, generations, input_seal, input_seal_sha256, semantics_version):
    """Produce coverage before model execution; incomplete coverage has no census."""
    verified(input_seal, INPUT_CONTRACT)
    require(input_seal['receipt_sha256'] == input_seal_sha256, 'input_seal_hash')
    require(input_seal == seal_inputs(owners, subjects=subjects, semantics_version=semantics_version), 'source_seal_drift')
    require(set(generations) == set(subjects)
            and all(generations[t] == owners[t].generation for t in subjects), 'requested_generation_binding')
    contexts, facts, rows = {}, {}, []
    for ticker in sorted(subjects):
        context, selected = _source_context(ticker, owners[ticker])
        contexts[ticker], facts[ticker] = context, selected
        rows.append(_row(ticker, owners[ticker], context, selected))
    counts = Counter(c['coverage_disposition'] for r in rows for c in r['categories'])
    complete = all(r['coverage_complete'] for r in rows)
    coverage = sealed(dict(contract=CONTRACT, subjects=len(rows),
        complete_subjects=sum(r['coverage_complete'] for r in rows), coverage_complete=complete,
        unresolved_required_cells=counts.get('UNRESOLVED', 0),
        owner_provenance_complete=complete, temporal_provenance_complete=complete,
        decision_provenance_complete=complete, total_cells=sum(counts.values()), cell_counts=dict(counts), rows=rows,
        current_blocker_count=None, census_phase='PRE_CENSUS_COVERAGE_GATE', runtime_enabled=False,
        producer_semantics=semantics_version, input_seal_sha256=input_seal_sha256,
        source_generations=sorted(set(generations.values())), historical_model_inputs_used=False))
    census = scope.blocker_census(rows, expected_subjects=subjects) if complete else None
    resolutions = {}
    if complete:
        policy.coverage_gate(coverage, census, coverage['receipt_sha256'], census['receipt_sha256'])
        for row in rows:
            ticker = row['ticker']
            subject = dict(ticker=ticker, security_id=row['canonical_security_id'],
                source_generation_id=row['source_generation'], facts=facts[ticker])
            value, metrics, all_unusable = policy.evaluability(subject, row, census, coverage['receipt_sha256'])
            resolutions[ticker] = dict(evaluability=value, metrics=metrics, all_unusable=all_unusable)
    return dict(coverage=coverage, census=census, resolutions=resolutions, contexts=contexts,
        producer=dict(path='scripts/newbuyer_b2_v2_coverage.py', semantics_version=semantics_version,
            code_sha256=sha256(Path(__file__).read_bytes()).hexdigest(), model_authority_inputs=0))
