"""Opt-in read-only archive projection, never a renewed Source Owner.

Generation identities remain original. A dated view is not registration; the
registered packet edge separately re-enters the genuine live Intake Owner.
"""
from dataclasses import dataclass
import json

from app.services.public_capture_storage import FileCaptureArchive
from app.services.vnext_composite_research import CompositeView, PUBLIC_ID, instant
from app.services.vnext_legacy_reuse import native_valuation_inputs
from app.services.provider_native_valuation_snapshot import derive_provider_snapshots, derive_forward_snapshot
from app.services.vnext_research_store import digest, encoded

CONTRACT = 'DATED_FILE_CAPTURE_RESEARCH_V1'
ENABLED_BY_DEFAULT = False


@dataclass(frozen=True)
class DatedEvidenceBundle:
    """Immutable locator, not a serialized grant or a caller-supplied value."""
    root: str
    manifest_sha256: str
    capture_seal_sha256: str
    run_id: str
    ticker: str
    canonical_security_id: str
    as_of: str


def _replay(bundle):
    if type(bundle) is not DatedEvidenceBundle:
        raise ValueError('dated_typed_locator_required')
    store = FileCaptureArchive.open_sealed_read_only(bundle.root,
        expected_manifest_sha256=bundle.manifest_sha256,
        expected_capture_seal_sha256=bundle.capture_seal_sha256)
    securities = [s for s in store.identities() if s['ticker'] == bundle.ticker]
    if (store._manifest['run_id'] != bundle.run_id or len(securities) != 1
            or securities[0]['canonical_security_id'] != bundle.canonical_security_id):
        raise ValueError('dated_run_ticker_security_binding')
    security = securities[0]
    if security.get('country') != 'US':
        raise ValueError('dated_provider_adapter_not_implemented')
    inputs = native_valuation_inputs(store, bundle.run_id, security, 'finnhub',
        cutoff=instant(bundle.as_of))
    snapshots = [*derive_provider_snapshots(inputs, security=security, run_id=bundle.run_id),
        derive_forward_snapshot(inputs, security=security, run_id=bundle.run_id)]
    captures = []
    for path, text in store.list_captures(bundle.run_id, 'Finnhub'):
        receipt = json.loads(text)
        if instant(receipt['captured_at']) > instant(bundle.as_of):
            continue
        captures.append((path, receipt))
    return store, security, snapshots, captures


def bind_dated_archive(*, root, manifest_sha256, capture_seal_sha256, run_id,
                       ticker, canonical_security_id, as_of, enabled=False):
    if enabled is not True:
        raise ValueError('dated_research_explicit_enable_required')
    bundle = DatedEvidenceBundle(str(root), manifest_sha256, capture_seal_sha256,
        run_id, ticker, canonical_security_id, instant(as_of).isoformat())
    _replay(bundle)
    return bundle


class _ArchiveView(CompositeView):
    """Original CompositeView entry/packet validators, with no SQL persistence."""
    def __init__(self, bundle):
        store, security, snapshots, captures = _replay(bundle)
        self.bundle = bundle
        self.cutoff = instant(bundle.as_of)
        self.as_of = self.cutoff.isoformat()
        self.identities = {bundle.ticker: {k: security.get(k) for k in PUBLIC_ID}}
        self.reported_context = False
        self.registration_admission = None
        self.runs = {bundle.run_id: dict(run_id=bundle.run_id,
            started_at=store.run_started_at(bundle.run_id), as_of=bundle.as_of,
            status='SEALED_ORIGINAL_DATED_REFERENCE')}
        self.proofs = {}
        for _, receipt in captures:
            key = (bundle.run_id, receipt['raw_sha256'])
            proof = dict(capture_id=digest(receipt), run_id=bundle.run_id,
                origin_run=bundle.run_id, provider='Finnhub',
                raw_sha256=receipt['raw_sha256'], receipt_sha256=digest(receipt),
                captured_at=receipt['captured_at'], available_at=receipt['captured_at'],
                receipt_kind='CURRENT_HTTP_AT_ORIGINAL_GENERATION',
                original_receipt_sha256=digest(receipt), dependencies=[])
            if key in self.proofs and self.proofs[key] != proof:
                raise ValueError('dated_source_receipt_ambiguous')
            self.proofs[key] = proof
        self.rows = []
        for snapshot in snapshots:
            data = snapshot.model_dump(mode='json')
            field = 'valuation.' + ('FPER' if data['metric'] == 'FORWARD_PE' else data['metric'])
            status = 'SOURCE_REFERENCE' if data['display_eligible'] else 'POLICY_DENIED'
            payload = dict(snapshot=data, strict_native=False, current_capture=False,
                source_captured_this_run=False, source_captured_at=data['retrieval_timestamp'])
            self.rows.append((data['snapshot_sha256'], bundle.run_id, bundle.ticker,
                field, status, data['raw_sha256'], encoded(payload).decode()))
        self.rows = tuple(self.rows)
        self.snapshot_sha = digest(dict(contract=CONTRACT, locator=bundle.__dict__,
            observations=self.rows, proofs=list(self.proofs.values())))

    def source(self, run, sha, capture_id=None):
        # Re-verify sealed bytes on every consume, not merely at bind time.
        _replay(self.bundle)
        proof = self.proofs.get((run, sha))
        if proof is None or (capture_id is not None and capture_id != proof['capture_id']):
            raise ValueError('dated_original_source_receipt_missing')
        return json.loads(encoded(proof))

    def packet(self, ticker):
        self._check_projection()
        packet = super().packet(ticker)
        packet['dated_archive_contract'] = CONTRACT
        packet['registration_status'] = 'ARCHIVED_IDENTITY_ONLY_NOT_CURRENT_REGISTRATION'
        packet['source_generation_reissued'] = False
        return packet

    def _check_projection(self):
        expected = _ArchiveView(self.bundle)
        for name in ('cutoff', 'as_of', 'identities', 'runs', 'rows', 'proofs', 'snapshot_sha'):
            if getattr(self, name) != getattr(expected, name):
                raise ValueError('dated_projection_changed')

    def entry(self, row):
        self._check_projection()
        if row not in self.rows:
            raise ValueError('dated_unrecorded_observation')
        return super().entry(row)

    def unified_premodel(self, *, registry):
        """Re-enter the original builder; missing registry remains a hard gate."""
        from app.services.vnext_optional_fy1_research import attach
        from app.services.vnext_unified_judgment import build_bundle
        from app.services.vnext_codex_research import numeric_catalog
        base = self.packet(self.bundle.ticker)
        # Same catalog builder as cold_packet(), not Composite's display catalog.
        base['numeric_catalog'] = numeric_catalog(base)
        return build_bundle(attach(base), registry=registry)

    def packet_pending_research(self, *, ticker, owner, generation_id, policy):
        from app.services.prospective_class_c_owner import source_intake_snapshot
        identities, receipt, _, _ = source_intake_snapshot(owner,
            generation_id=generation_id, subjects=(ticker,), policy=policy)
        expected = self.identities.get(ticker)
        if expected is None or any(identities[ticker].get(k) != expected.get(k) for k in PUBLIC_ID):
            raise ValueError('dated_current_registered_security_mismatch')
        packet = self.packet(ticker)
        packet['registration_status'] = 'GENUINE_INTAKE_RESEARCH_ONLY'
        packet['registration_admission'] = dict(generation_id=generation_id,
            receipt_sha256=digest(receipt), current_production=False, send=False)
        return packet


def dated_archive_view(bundle, *, enabled=False):
    if enabled is not True:
        raise ValueError('dated_research_explicit_enable_required')
    return _ArchiveView(bundle)
