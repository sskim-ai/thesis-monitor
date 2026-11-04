"""Pure accepted business-plan binding shared by runtime and offline capture."""
from app.services.accepted_calibration_message_service import AcceptedCalibrationPlan, digest


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def stock_plan(proof, ticker, ep, *, require=_require):
    row, entries = proof.brows[ticker], proof.entries[ticker]
    cap = proof.POLICY.axis_capability(proof.cores[ticker], proof.chains[ticker],
        proof.catalogs[ticker], proof.subjects[ticker]['decision_evidence'])
    require(cap == proof.caps[ticker], 'CAPTURE_CAPABILITY_DRIFT')
    check = proof.POLICY.validate_decision(row, cap, proof.ranges[ticker])
    require(check['status'] == 'PASS', 'CAPTURE_POLICY_NOT_ACCEPTED')
    lineage = {c['claim_ref']: tuple(c['parent_source_refs']) for c in proof.cores[ticker]['atomic_claims']}
    receipt = dict(status='PASS', errors=[], ticker=ticker, source_generation_id=proof.source_gen,
        execution_generation_id=proof.gen, evidence_packet_sha256=digest(ep.model_dump(mode='json')),
        decision_sha256=digest(row), entries_sha256=digest(entries), claim_lineage_sha256=digest(lineage))
    quote = None
    provenance = None
    if getattr(proof, 'DETAILED_PRESENTATION', False):
        provenance = dict(core_sha256=digest(proof.cores[ticker]), pass_a_sha256=digest(proof.arows[ticker]),
            pass_b_input_sha256=digest(proof.bctx[ticker]), pass_b_sha256=digest(row),
            fresh_stock_sha256=digest(proof.fresh_stocks[ticker]))
        receipt['stage_provenance_sha256'] = digest(provenance)
    if getattr(proof, 'TYPED_PRESENTATION', False):
        stock = next(s for packet in proof.packets.values() for s in packet['stocks'] if s['ticker']==ticker)
        candidate = stock.get('current_price_context')
        if candidate and candidate.get('availability') == 'ready' and any(entries.get(k) is not None for k in ('fundamental_entry_low','tactical_watch_low')):
            quote = candidate
            receipt['quote_context_sha256'] = digest(quote)
    plan_type, extra = AcceptedCalibrationPlan, {}
    if provenance is not None:
        from app.services.accepted_calibration_message_service import AcceptedDetailedCalibrationPlan
        plan_type, extra = AcceptedDetailedCalibrationPlan, {'stage_provenance': provenance}
    return plan_type(ticker=ticker, source_generation_id=proof.source_gen,
        execution_generation_id=proof.gen, evidence_packet_sha256=receipt['evidence_packet_sha256'],
        decision=row, entries=entries, claim_lineage=lineage, acceptance=receipt, acceptance_sha256=digest(receipt),
        quote_context=quote, **extra)
