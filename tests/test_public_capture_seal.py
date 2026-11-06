"""New cross-process seal and original atomic denial boundaries."""
from datetime import datetime,timezone
import json
import pytest
from test_public_file_capture import archive,pair,SECURITY
from app.services.public_capture_storage import FileCaptureArchive
from app.services.vnext_legacy_reuse import native_valuation_inputs
from app.services.provider_native_valuation_snapshot import derive_provider_snapshots,derive_forward_snapshot


def test_sealed_restart_replays_original_owner(archive):
    pair(archive);seal=archive.seal_captures()
    reopened=FileCaptureArchive.open_sealed_read_only(archive.path.parent,
        expected_manifest_sha256=archive.manifest_sha256,expected_capture_seal_sha256=seal)
    inputs=native_valuation_inputs(reopened,'SYNTHETIC',SECURITY,'finnhub')
    assert all(x.display_eligible for x in derive_provider_snapshots(inputs,security=SECURITY,run_id='SYNTHETIC'))


def test_modified_receipt_or_seal_cannot_rebind(archive):
    pair(archive);seal=archive.seal_captures()
    p=next((archive.path.parent/'captures').iterdir());p.write_text('{}')
    with pytest.raises(ValueError,match='seal_or_inventory'):
        FileCaptureArchive.open_sealed_read_only(archive.path.parent,
            expected_manifest_sha256=archive.manifest_sha256,expected_capture_seal_sha256=seal)


@pytest.mark.parametrize('change',['ads','currency','ticker','stale'])
def test_original_atomic_owner_denials_unchanged(archive,change):
    pair(archive);security=dict(SECURITY)
    if change=='ads':security['issuer_type']='adr';security['security_type']='ads'
    if change=='currency':security['currency']='KRW'
    if change=='ticker':security['ticker']='OTHER'
    inputs=native_valuation_inputs(archive,'SYNTHETIC',SECURITY,'finnhub')
    if change=='stale':
        import copy
        from app.services.vnext_research_store import digest,encoded
        inputs=copy.deepcopy(inputs);body=json.loads(inputs['raw']);body['isStale']=True
        inputs['raw']=encoded(body);inputs['receipt']['source_sha256']=digest(inputs['raw'])
    if change in ('ads','currency','ticker'):
        with pytest.raises(ValueError):derive_provider_snapshots(inputs,security=security,run_id='SYNTHETIC')
    else:
        values=derive_provider_snapshots(inputs,security=security,run_id='SYNTHETIC')
        assert all(not x.display_eligible for x in values)
