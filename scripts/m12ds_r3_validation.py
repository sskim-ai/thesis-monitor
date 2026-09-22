"""Archive fresh offline checks; no model/provider or production operations."""
import argparse
from pathlib import Path
import subprocess
import sys

from scripts.m12dr_fresh_blind_reproof import read, write, sha, REPO


def run(root):
    prior = read(root.parent / '20260922-m12ds-r2-policy-calibration/validation/receipt.json')
    tests = [x for x in prior['offline-regression']['command'] if x.startswith('tests/')]
    tests += ['tests/test_m12ds_r3_policy.py', 'tests/test_m12ds_r3_transport.py']
    files = sorted(str(p.relative_to(REPO)) for pattern in ('scripts/m12ds_r3_*.py', 'tests/test_m12ds_r3_*.py')
                   for p in REPO.glob(pattern))
    files += ['scripts/m12ds_r2_shadow_reproof.py', 'scripts/m12ds_r2_offline_proof.py']
    commands = {'offline-regression': [sys.executable, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *tests],
                'ruff': [str(Path(sys.executable).parent / 'ruff'), 'check', *files],
                'diff-check': ['git', 'diff', '--check']}
    receipt = {}
    for name, cmd in commands.items():
        result = subprocess.run(cmd, cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
        log = root / 'validation' / (name + '.txt')
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(result.stdout)
        receipt[name] = {'status': 'PASS' if result.returncode == 0 else 'FAIL', 'exit_code': result.returncode,
                         'command': cmd, 'log_sha256': sha(log)}
        print(name, receipt[name]['status'], result.stdout[-1200:], flush=True)
    source = read(root / 'validation/full-source-offline-proof.json')
    receipt['source-layout-proof'] = {'status': source['status'], 'subjects': source['subjects'], 'model_calls': 0,
        'sha256': sha(root / 'validation/full-source-offline-proof.json')}
    write(root / 'validation/receipt.json', receipt)
    return all(r['status'] == 'PASS' for r in receipt.values())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    sys.exit(0 if run(parser.parse_args().root) else 1)
