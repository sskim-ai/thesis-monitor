"""Freeze reviewed code and offline gates before any new current source collection."""
import argparse
from pathlib import Path
import subprocess

from scripts.m12dr_offline_source_closure import read, write, sha
from scripts.m12ds_r4_source_preflight import REPO, OPERATING, git_state
from scripts.approved_scope_descendants import PINS, approved_descendant

R3 = '1665c2fc77116da22472461409a56bb2787fb997'
POLICY_FILES = ('scripts/m12ds_r3_policy.py', 'scripts/m12ds_r3_schemas.py',
    'scripts/m12ds_r3_transport.py', 'scripts/m12ds_r3_valuation_authority.py',
    'scripts/m12ds_r2_judgment_policy.py', 'scripts/m12ds_r2_schemas.py',
    'scripts/m12ds_r2_ranges.py', 'scripts/m12ds_r3_market.py')


def freeze(root, *, instruction_sha='19bedb64a2238934fb8b5c34ab1b70f0c713f0d3', selected_source_contract=None):
    if (root / 'repair-freeze.json').exists():
        raise ValueError('repair_already_frozen')
    current = git_state(REPO)
    if current['status'] or git_state(OPERATING)['status']:
        raise ValueError('clean_worktrees_required')
    checks = read(root / 'validation-final/receipt.json')
    if any(row['status'] != 'PASS' for row in checks.values()) or read(root / 'offline/receipt.json')['status'] != 'PASS':
        raise ValueError('offline_gates_required')
    subprocess.run(['git', 'diff', '--quiet', R3, '--', *POLICY_FILES], cwd=REPO, check=True)
    changes = subprocess.check_output(['git', 'diff', '--name-only', R3, 'HEAD', '--', 'app'], cwd=REPO, text=True).splitlines()
    inherited = subprocess.check_output(['git', 'diff', '--name-only', git_state(OPERATING)['head'], R3, '--', 'app'], cwd=REPO, text=True).splitlines()
    descendants = {path: approved_descendant(path) for path in PINS}
    if not all(descendants.values()):
        raise ValueError('approved_scope_lineage_required')
    write(root / 'repair-freeze.json', dict(status='PASS', candidate_implementation_sha=current['head'],
        instruction_sha=instruction_sha, selected_source_contract=selected_source_contract,
        controller=current, operating=git_state(OPERATING), accepted_r3=R3,
        exact_production_imported_files={n: sha(REPO / n) for n in changes},
        inherited_production_imported_files={n: sha(REPO / n) for n in inherited if (REPO / n).is_file()},
        r3_policy_neutrality={n: sha(REPO / n) for n in POLICY_FILES},
        approved_scope_descendants=descendants, validation_sha256=sha(root / 'validation-final/receipt.json'),
        offline_sha256=sha(root / 'offline/receipt.json'),
        semantic_total_revenue='UNRESOLVED_WITHOUT_STATEMENT_ROLE_EVIDENCE',
        field_quality_contract='sec-business-field-quality-v1',
        night_consumer_contract='official-krx-night-market-consumption-v1',
        production_capture_contract='accepted-calibration-message-v1',
        model='gpt-5.6-sol', effort='xhigh', timeout_seconds=1200,
        logical_calls=26, max_processes=52, retry='ONE_IDENTICAL_TYPED_TRANSIENT_ONLY',
        main_merge=0, push=0, deploy=0, production_mutations=0))
    print('Repair/code/offline freeze PASS: ' + current['head'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    freeze(parser.parse_args().root)
