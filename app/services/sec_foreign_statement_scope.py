"""Source-recomputed accounting-scope diagnostics, never a basis-use grant."""
from datetime import date
from hashlib import sha256

from app.services.sec_foreign_comparison_service import (
    current_projection, extract_occurrences, occurrence_errors,
)
from app.services.unified_snapshot_contract import digest

CONTRACT = 'foreign-reported-statement-scope-audit-v1'


def inspect_scopes(raw, *, issuer_cik, filing, source_url, cutoff, quarter_period_policy=None):
    """Partition structural scopes without choosing issuer-level authority.

    The acquisition owner authenticates the document and receipt upstream.
    Recompute cells here so a caller-rehashed occurrence cannot select a basis.
    """
    payload_sha = sha256(raw).hexdigest()
    found = extract_occurrences(raw.decode('utf-8', errors='replace'),
        issuer_cik=issuer_cik, accession=filing['accessionNumber'],
        document_type=filing['form'], filing_date=filing['filingDate'],
        source_url=source_url, payload_sha256=payload_sha, quarter_period_policy=quarter_period_policy)
    from app.services.sec_reported_quarter_period import source_record
    sources = source_record(raw, issuer_cik=issuer_cik, accession=filing['accessionNumber'],
        document_type=filing['form'], filing_date=filing['filingDate'], source_url=source_url) if quarter_period_policy else None
    validation = [dict(occurrence_id=o['occurrence_id'],
        denial_reasons=occurrence_errors(o, date.fromisoformat(cutoff[:10]), source_documents=sources)) for o in found]
    valid = {r['occurrence_id'] for r in validation if not r['denial_reasons']}
    partitions = []
    for basis in sorted({o['statement_basis'] for o in found}):
        members = [o for o in found if o['statement_basis'] == basis]
        # Invalid observations stay visible but cannot enter diagnostic projection.
        eligible = [o for o in members if o['occurrence_id'] in valid]
        projections = {role: current_projection(eligible, required_role=role, source_documents=sources)
                       for role in ('single-quarter', 'half-year')}
        partitions.append(dict(statement_basis=basis, occurrences=members,
            valid_occurrence_ids=sorted(o['occurrence_id'] for o in eligible),
            invalid_occurrence_ids=sorted(o['occurrence_id'] for o in members if o['occurrence_id'] not in valid),
            boundary_ids=sorted({digest(o['statement_boundary']) for o in members}),
            diagnostic_projections=projections,
            disposition='UNSELECTED_ACCOUNTING_SCOPE_NOT_CONTRADICTORY_BY_BASIS_ALONE'))
    result = dict(contract=CONTRACT, issuer_cik=str(issuer_cik).zfill(10),
        filing=dict(filing), source_url=source_url, cutoff=cutoff,
        document_sha256=payload_sha, document_bytes=len(raw),
        original_occurrences_sha256=digest(found), occurrence_validation=validation,
        partitions=partitions, selected_basis=None,
        status='FOREIGN_STATEMENT_BASIS_POLICY_AUTHORITY_PENDING',
        purpose='NON_GRANTING_DIAGNOSTIC_ONLY', source_use_eligible=False,
        direction_eligible=False, valuation_eligible=False,
        limitations=['No cross-provider CFS priority inferred.',
                    'Original quality, complete source inventory and selected Owner remain mandatory.',
                    'Projection inside one scope is not an approved FinancialSnapshot or current Owner.'])
    return {**result, 'receipt_sha256': digest(result)}


def verify_scope_audit(receipt, raw, **source):
    expected = inspect_scopes(raw, **source)
    if receipt != expected:
        raise ValueError('foreign_statement_scope_source_replay_mismatch')
    return expected
