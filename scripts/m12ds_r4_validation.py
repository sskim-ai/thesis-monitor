"""Bounded local regression receipts; no live source/model entrypoint."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from scripts.m12ds_r4_source_preflight import REPO, helpers


def run(root, name):
    if Path(name).name != name:
        raise ValueError('validation_name_must_be_basename')
    prior = helpers.read_json(root.parent / '20260922-m12ds-r3-rev1-calibration/validation/receipt.json')
    tests = {x for x in prior['offline-regression']['command'] if x.startswith('tests/')}
    tests.update(str(p.relative_to(REPO)) for pattern in ('tests/test_*night*.py', 'tests/test_*render*.py',
        'tests/test_*notification*.py', 'tests/test_*message*.py', 'tests/test_m12ds_r4_*.py') for p in REPO.glob(pattern))
    files = sorted(str(p.relative_to(REPO)) for pattern in ('scripts/m12ds_r4_*.py', 'tests/test_m12ds_r4_*.py')
                   for p in REPO.glob(pattern))
    commands = {
        'focused': [sys.executable, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *sorted(tests)],
        'full-pytest': [sys.executable, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider'],
        'ruff-changed': [str(Path(sys.executable).parent / 'ruff'), 'check', *files],
        'ruff-full': [str(Path(sys.executable).parent / 'ruff'), 'check', '.'],
        'diff-check': ['git', 'diff', '--check'],
    }
    environment = {**os.environ, 'THESIS_MONITOR_ENV_FILE': '/dev/null', 'DATABASE_URL': 'sqlite://',
        'DATA_DIR': '/private/tmp/m12ds-r4-validation', 'ENABLE_LIVE_PROVIDERS': 'false',
        'NOTIFICATION_DRY_RUN': 'true', 'PYTHONDONTWRITEBYTECODE': '1'}
    # Tests own their dummy credential fixtures; blank process overrides mask those fixtures.
    for key in ('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'TELEGRAM_TEST_CHAT_ID'):
        environment.pop(key, None)
    receipt = {}
    for check, command in commands.items():
        log = root / name / f'{check}.txt'
        log.parent.mkdir(parents=True, exist_ok=True)
        if log.exists():
            raise ValueError('validation_output_already_exists:' + check)
        print(check + ': START', flush=True)
        with log.open('w') as stream:
            try:
                result = subprocess.run(command, cwd=REPO, env=environment,
                    stdout=stream, stderr=subprocess.STDOUT, timeout=600)
                code = result.returncode
            except subprocess.TimeoutExpired:
                code = 124
        receipt[check] = {'command': command, 'exit_code': code, 'status': 'PASS' if code == 0 else 'FAIL',
                         'log_sha256': helpers.sha256_file(log), 'timeout_seconds': 600}
        helpers.write_json(root / name / 'receipt.json', receipt)
        print(json.dumps({check: receipt[check]['status'], 'summary': log.read_text()[-1800:]}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--name', default='validation')
    args = parser.parse_args()
    run(args.root.resolve(), args.name)
