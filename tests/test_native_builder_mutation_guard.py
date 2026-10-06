"""Actual native Market request construction with the actual parent audit hook."""
import json
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize('market', ['US', 'KR'])
def test_native_builder_guarded_request_bytes_and_cleanup_parity(tmp_path, market):
    code = r'''
import json, sys
from pathlib import Path
from scripts.qualified_official_launch_context import ManualMutationGuard
from scripts.strict_blind_monitoring import MonitoringAdapter
from scripts.strict_blind_native_market_proof import packet, market_owner
from scripts.strict_blind_run_plan import execution_plan
from scripts.sealed_cohort_offline_proof import network_guard
from app.services.unified_snapshot_contract import digest, encoded
network_guard()
root=Path(sys.argv[1]); market=sys.argv[2]; generation='offline-guard-composition'
names=[t for row in execution_plan(['fixture'])['stages']['CORE'] if row['market']==market for t in row['subjects']]
stocks={t:dict(fictional_source=t) for t in names}
prepared={t:dict(mode='EVIDENCE_BASED',initial_chain=dict(source_generation_id=generation,
    execution_generation_id=generation),view_receipt=dict(raw_source_sha256=digest(stocks[t]))) for t in names}
source=dict(prepared=prepared,stocks=stocks,valuation_contexts={},source_generation_id=generation,
    markets={market.lower():dict(context=market_owner.market_context(packet(market)))})
view=dict(source=dict(generation=generation,monitoring_inputs={market:source}))
adapter=MonitoringAdapter('MARKET',market,1)
before=adapter.build(view)
guard=ManualMutationGuard([Path.cwd(),root/'operating',root/'sealed-source'])
sys.addaudithook(guard)
after=adapter.build(view)
assert encoded(before)==encoded(after)
created=[Path(r['targets'][0]['canonical_entry']) for r in guard.receipts
    if r['operation']=='os.mkdir' and r['targets'] and
    Path(r['targets'][0]['canonical_entry']).name.startswith('strict-native-request-')]
assert len(created)==1 and not created[0].exists()
cleanup=[r for r in guard.receipts if r['operation'] in ('os.remove','os.rmdir')]
assert cleanup and all(r['decision']=='ALLOW' and all(
    Path(t['canonical_entry']).is_relative_to(created[0]) for t in r['targets']) for r in cleanup)
assert guard.blocked_attempts==0
assert all(not t['protected_roots'] for r in guard.receipts for t in r['targets'])
assert any(t['fd_identity'] for r in cleanup for t in r['targets'])
print(json.dumps(dict(status='PASS',market=market,request_sha256=digest(after),
    bytes_equal=True,cleanup_events=len(cleanup),guard_installed=True,model_provider_calls=0)))
'''
    result = subprocess.run([sys.executable, '-B', '-c', code, str(tmp_path), market],
        cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True, timeout=120)
    assert result.returncode == 0, result.stderr
    proof = json.loads(result.stdout)
    assert proof['status'] == 'PASS' and proof['bytes_equal']
    assert proof['cleanup_events'] > 0 and proof['model_provider_calls'] == 0
