"""Original-field replay of auxiliary purpose evidence, not fresh owner authority."""
from copy import deepcopy
from weakref import WeakKeyDictionary

from app.services.sec_fpi_purpose_evidence_owner import qualify_purpose
from app.services.sec_fpi_purpose_probe import _verified_receipts, replay_probe
from app.services.unified_snapshot_contract import digest

CONTRACT = 'sec-fpi-auxiliary-purpose-reconciliation-v1'
_ISSUED = WeakKeyDictionary()
_FILING = ('form', 'accessionNumber', 'primaryDocument', 'filingDate', 'reportDate')


class PurposeReconciliation:
    """Live parent capability. Serialized audit receipts cannot instantiate it."""
    def resolve(self, *, plan=None, acquisition=None, receipts=None):
        if self not in _ISSUED:
            raise ValueError('purpose_reconciliation_unissued_capability')
        build, frozen = _ISSUED[self]
        current = build()
        if current != frozen:
            raise ValueError('purpose_reconciliation_source_or_review_drift')
        if plan is not None and current['original_plan_sha256'] != digest(plan):
            raise ValueError('purpose_reconciliation_wrong_original_plan')
        if acquisition is not None and current['original_acquisition_sha256'] != digest(acquisition):
            raise ValueError('purpose_reconciliation_wrong_original_acquisition')
        if receipts is not None and current['original_receipts_sha256'] != digest(receipts):
            raise ValueError('purpose_reconciliation_wrong_original_receipts')
        return current


def issue_reconciliation(*, original_plan, original_acquisition, original_directory,
                         original_receipts, probe_plan, probe_directory, source_anchor,
                         target_manifest, expected_capture_sha256,
                         media_by_accession=None, media_validator=None):
    original_plan, original_acquisition, original_receipts, probe_plan, source_anchor, target_manifest = deepcopy(
        (original_plan, original_acquisition, original_receipts, probe_plan, source_anchor, target_manifest))
    # Preserve opaque tokens; copying or serializing them must not create authority.
    media = {k: tuple(v) for k, v in (media_by_accession or {}).items()}

    def build():
        replay = replay_probe(probe_plan, original_plan, original_acquisition,
            original_directory, original_receipts, probe_directory,
            source_anchor=source_anchor, target_manifest=target_manifest,
            expected_capture_sha256=expected_capture_sha256)
        probe_receipts, bodies = _verified_receipts(probe_plan, probe_directory)
        rows = []
        for filing in probe_plan['filings']:
            accession = filing['accessionNumber']
            if (accession, 'document') not in bodies or (accession, 'index') not in bodies:
                raise ValueError('purpose_reconciliation_primary_index_required')
            rows.append(qualify_purpose(bodies[(accession, 'document')][0], bodies[(accession, 'index')][0],
                probe_plan=probe_plan, probe_receipts=probe_receipts, source_anchor=source_anchor,
                expected_capture_sha256=expected_capture_sha256, filing=filing,
                media_observations=media.get(accession, ()), media_validator=media_validator))
        if set(media) - {f['accessionNumber'] for f in probe_plan['filings']}:
            raise ValueError('purpose_reconciliation_unbound_media')
        result = dict(contract=CONTRACT, original_plan_sha256=digest(original_plan),
            original_acquisition_sha256=digest(original_acquisition), original_receipts_sha256=digest(original_receipts),
            original_generation=original_plan['run_id'], original_cutoff=original_plan['cutoff'],
            auxiliary_generation=probe_plan['run_id'], auxiliary_cutoff=probe_plan['cutoff'],
            auxiliary_capture_sha256=expected_capture_sha256, original_probe_replay_sha256=digest(replay),
            original_candidate_plan=deepcopy(probe_plan['economic_candidate_plan']), records=rows,
            current_owner_eligible=False, source_use_eligible=False, direction_eligible=False,
            temporal_authority='HISTORICAL_AUXILIARY_REPLAY_ONLY_NOT_ORIGINAL_RUN_KNOWLEDGE',
            current_owner_blocker='AUXILIARY_PURPOSE_CURRENT_GENERATION_USE_NOT_AUTHORIZED')
        result['receipt_sha256'] = digest(result)
        return result

    frozen = build()
    capability = PurposeReconciliation()
    _ISSUED[capability] = (build, frozen)
    return capability


def resolve(capability, **bindings):
    if type(capability) is not PurposeReconciliation:
        raise ValueError('purpose_reconciliation_backend_capability_required')
    return capability.resolve(**bindings)


def matching_nonfinancial(review, filing):
    matches = [row for row in review['records']
        if all(row['binding']['filing'].get(k) == filing.get(k) for k in _FILING)]
    return bool(len(matches) == 1 and matches[0]['classification'] == 'CONFIRMED_NON_FINANCIAL'
        and matches[0]['field_absence_audit']['complete_for_purpose']
        and not matches[0]['unresolved_assets'] and not matches[0]['denial_reasons'])
