"""One final-code predicate/candidate test; one synthetic Cold, no live Parent."""
from copy import deepcopy
from datetime import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

import pytest

from app.services import wm_period_currentness as wm
from app.services import registered_source_batch as batch
from app.services.scoped_source_plan import ScopedStockRead

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT.parents[1] / 'maintenance/20261104-p3d-final-release'


def test_final_strict_basis_capture_only_candidate_and_one_cold(tmp_path_factory, monkeypatch):
    spec = importlib.util.spec_from_file_location('p3d_inherited_fixture', ROOT / 'tests/test_wm_chain_readback.py')
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    root, data, reader, context = fixture.sample.__wrapped__(tmp_path_factory)
    receipt = data['receipts'][0]
    read = ScopedStockRead.model_validate(data['expected_reads'][0])
    rows = reader(data['artifacts'][0])[1]
    evidence = receipt['period_evidence']
    parser_pin = evidence['parser_pins']['app/providers/kiwoom.py']['sha256']
    with monkeypatch.context() as scoped:
        scoped.setattr(wm, '_LABEL_CONTRACTS', {(read.provider, read.api_id, read.timeframe):
            wm._LabelSpec('SESSION_DATE', 'dt', 'a' * 64, parser_pin)})
        with pytest.raises(ValueError, match='^wm_reviewed_label_parser_binding_required$'):
            wm.source_period_proof(rows, read=read, receipt=evidence['source_receipt'],
                original_proof=evidence['original_proof'], cutoff=datetime.fromisoformat(evidence['cutoff']),
                parser_pins=evidence['parser_pins'])
    assert not wm._LABEL_CONTRACTS
    for item in data['receipts']:
        proof = item['period_proof']
        assert proof['state'] == 'SOURCE_ONLY_HISTORICAL_OR_PROVISIONAL'
        assert proof['label_basis'] == 'UNKNOWN'
        assert proof['completed_rows'] is proof['provisional_rows'] is None
        assert proof['current_source_authority'] is False
    # Fail if this readback unexpectedly tries to construct a live Parent.
    from app.services import current_scoped_source_owner as owner
    def forbidden(*args, **kwargs):
        raise AssertionError('Cold must not construct or renew live Parent')
    monkeypatch.setattr(owner, 'issue_parent', forbidden)
    result = batch.validate_cold_roles(data, reader, wm_context=context)
    assert len(result['roles']) == 4 and result['new_live_authority'] is False
    rejected = []
    for mutation in ('raw', 'page', 'replay', 'receipt'):
        altered = deepcopy(data)
        value = altered['receipts'][0]
        if mutation == 'raw':
            value['raw_sha256'] = ['0' * 64]
        elif mutation == 'page':
            value['period_evidence']['source_receipt']['pages'][0]['page_ordinal'] = 999
        elif mutation == 'replay':
            value['period_evidence']['replays'][1][0]['status'] = 'GAP'
        else:
            value['source_receipt_sha256'] = '0' * 64
        value.pop('receipt_sha256')
        value['receipt_sha256'] = batch.digest(value)
        with pytest.raises((ValueError, KeyError, TypeError)):
            batch.validate_cold_roles(altered, reader, wm_context=context)
        rejected.append(mutation)
    launcher = ROOT / 'scripts/official_source_canary_v3.py'
    scope = {'__file__': str(launcher), '__name__': 'p3d_final_candidate_check'}
    exec(compile(launcher.read_bytes(), str(launcher), 'exec'), scope)
    candidate = ROOT / 'ops/source-parent-candidates/p3c-wm-chain-v1.json'
    candidate_sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
    manifest, cli = scope['validate_manifest'](candidate, candidate_sha, candidate=True)
    release = json.loads((ROOT / 'ops/source-parent-candidates/p3c-batch-release-v2.json').read_bytes())
    assert release['manifest_candidate']['sha256'] == candidate_sha
    assert all(manifest['source_pins'][name] == pin == scope['pin'](ROOT / name)
               for name, pin in release['new_pins'].items())
    assert manifest['default_enabled'] is manifest['owner_approved'] is False
    assert 'SESSION_DATE' not in wm.source_period_proof.__code__.co_consts
    request = root / 'p3d-cold-input.json'
    fixture.write(request, data)
    process = subprocess.run(['/Users/sskim/Codex/thesis-monitor/.venv/bin/python', '-I', '-B',
        str(ROOT / 'scripts/official_source_batch_cold.py'), str(request),
        hashlib.sha256(request.read_bytes()).hexdigest()], capture_output=True, timeout=60,
        env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'PYTHONDONTWRITEBYTECODE': '1'}, cwd=root)
    assert process.returncode == 0 and not process.stderr, process.stdout
    cold = json.loads(process.stdout)
    assert cold['pid'] != os.getpid() and cold['test_only'] is True
    assert len(cold['roles']) == 4 and cold['new_live_authority'] is False
    assert cold['HTTP'] == cold['DB'] == cold['models'] == 0
    fixture.write(TASK / 'FINAL_GUARD_AND_COLD_RECEIPT.json', dict(
        final_predicate_SESSION_DATE_rejected=True, unreviewed_capture_only=True,
        changed_branch_negative_checks=rejected, inherited_P3C_mutations=11,
        candidate_sha256=candidate_sha, current_candidate_exact_pins=True,
        separate_Cold_processes=1, synthetic_roles=4, live_Parent='NOT_RUN',
        cold=cold, stderr_bytes=len(process.stderr), exit=process.returncode,
        existing_receipts_not_reissued=True, current_source_authority=False))
