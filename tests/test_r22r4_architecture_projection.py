import json
import subprocess
import sys

import pytest

from app.services import reviewed_fixture_authority as owner
from app.services.fixture_context_authority import reject_test_only_production
from app.services.direction_timing_ownership_service import canonical_sha256
from scripts import integrated_main_monitored_shadow_diagnostic_m12af as probe


def architecture():
    generation = 'm12ae-r2-architecture-proof'
    _, owned, _, contexts = probe.m12.fictional_inputs(generation)
    tickers = probe.m12.CONTEXTS[0]
    rows = [{**contexts[ticker], 'core_snapshot_sha256':'0'*64,
             'frozen_stage1_core':{'ticker':ticker, 'status':'FROZEN_PROBE'}} for ticker in tickers]
    text = probe.base._stage2_prompt(packet_id=generation, tickers=tickers, contexts=rows)
    return owned, contexts, tickers, text


def test_exact_architecture_public_bytes_preserve_typed_ownership():
    owned, contexts, tickers, text = architecture()
    assert canonical_sha256(text) == probe.EXPECTED_STAGE2_PROMPT_SHA256
    assert len(text.encode()) == 25134
    for ticker in tickers:
        assert 'test_only_provenance' not in contexts[ticker]
        assert owner.verify_reviewed_owned_fixture(owned[ticker], consumer='OWNED_CONTEXT') == owned[ticker].backend_seal
        with pytest.raises(ValueError, match='production_test_only_fixture_forbidden'):
            reject_test_only_production(contexts[ticker])
    with pytest.raises(ValueError, match='production_test_only_fixture_forbidden'):
        reject_test_only_production({'prompt':text, 'response_schema':{'type':'object'}})


def test_architecture_projection_cannot_outlive_or_change_owner():
    owned, _, tickers, _ = architecture()
    original = owned[tickers[0]]
    modified = original.model_copy(update={'backend_seal':original.backend_seal.model_copy(update={'purpose':'FROZEN_DELTA_SEMANTICS'})})
    with pytest.raises(ValueError, match='reviewed_fixture_consumer_forbidden'):
        owner.fixture_metadata(modified, consumer='OWNED_CONTEXT')
    owner.revoke_reviewed_fixture(original)
    with pytest.raises(ValueError, match='reviewed_fixture_unissued_revoked_or_changed'):
        owner.fixture_metadata(original, consumer='OWNED_CONTEXT')
    other = owner.build_reviewed_owned_fixture('financial:FIC-FIN-01',generation='m12ap-fixture')
    assert owner.fixture_metadata(other, consumer='OWNED_CONTEXT')['test_only_provenance']['provenance']=='TEST_ONLY'
    unselected = owner.build_reviewed_owned_fixture('financial:FIC-FIN-05',generation='m12ae-r2-architecture-proof')
    assert owner.fixture_metadata(unselected, consumer='OWNED_CONTEXT')['test_only_provenance']['provenance']=='TEST_ONLY'


def test_architecture_prompt_fresh_process_denial_without_issuance():
    _, _, _, text = architecture()
    code = '''import json,sys
from app.services.fixture_context_authority import reject_test_only_production
from app.services import reviewed_fixture_authority as owner
assert not owner._ISSUED
try:
    reject_test_only_production(json.load(sys.stdin))
except ValueError as exc:
    assert str(exc) == 'production_test_only_fixture_forbidden'
else:
    raise AssertionError('fixture Stage2 prompt escaped')
'''
    result = subprocess.run([sys.executable,'-B','-c',code],input=json.dumps({'prompt':text,'response_schema':{'type':'object'}}),text=True,capture_output=True,timeout=30,check=False)
    assert result.returncode == 0, result.stderr
