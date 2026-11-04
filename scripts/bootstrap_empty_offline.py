"""Create a fresh, disabled schema; seed identities are planning inputs only."""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys


def bootstrap(destination):
    destination = Path(destination)
    if not destination.is_absolute() or destination.exists() or '..' in destination.parts:
        raise ValueError('fresh_absolute_destination_required')
    if any(x.is_symlink() for x in destination.parents):
        raise ValueError('symlink_destination_denied')
    if any(v for k, v in os.environ.items() if k.upper().endswith(
            ('API_KEY', 'APP_KEY', 'SECRET_KEY', 'APP_SECRET', 'BOT_TOKEN'))):
        raise ValueError('credential_free_environment_required')
    destination.mkdir(mode=0o700)
    db = destination / 'empty.sqlite3'
    os.environ.update(THESIS_MONITOR_ENV_FILE='', DATA_DIR=str(destination),
        DATABASE_URL='sqlite:///' + str(db), ENABLE_LIVE_PROVIDERS='false',
        NOTIFICATION_DRY_RUN='true', AI_REVIEW_MODE='off',
        ONBOARDING_RECONCILER_ENABLED='false', MACRO_MONITOR_ENABLED='false',
        VNEXT_RUNTIME_ENABLED='0', VNEXT_PROVIDER_ENABLED='0',
        VNEXT_MODEL_ENABLED='0', VNEXT_SEND_ENABLED='0')

    def guard(event, args):
        if event.startswith(('socket.connect', 'socket.getaddrinfo', 'subprocess.Popen')):
            raise RuntimeError('offline_bootstrap_external_operation_denied')
        if event == 'open' and isinstance(args[0], str) and Path(args[0]).name.startswith('.env'):
            raise RuntimeError('credential_file_denied')
    sys.addaudithook(guard)
    from app.database import engine, init_db
    from app.config import get_settings
    from app.services.vnext_research_store import ResearchStore
    init_db()
    engine.dispose()
    ResearchStore(destination / 'empty-research.sqlite3')
    settings = get_settings()
    assert not settings.enable_live_providers and settings.notification_dry_run
    assert settings.ai_review_mode == 'off'
    cohort = json.loads((Path(__file__).resolve().parents[1] /
                        'app/fixtures/rebuild_cohort_v1.json').read_text())
    subjects = cohort['subjects']
    assert len(subjects) == len({r['ticker'] for r in subjects}) == 22
    assert sum(r['market'] == 'KR' for r in subjects) == 8
    assert sum(r['market'] == 'US' for r in subjects) == 14
    counts = {}
    for file in (db, destination / 'empty-research.sqlite3'):
        with sqlite3.connect(file.as_uri() + '?mode=ro', uri=True) as c:
            names = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
            values = {name: c.execute('SELECT count(*) FROM "' + name.replace('"', '""') + '"').fetchone()[0] for name in names}
            assert all(v == 0 for k, v in values.items() if k != 'research_meta')
            counts[file.name] = values
    result = dict(contract='empty-disabled-bootstrap-v1', schema='PASS', counts=counts,
        identity_configuration_count=22, persisted_registration_count=0,
        registration_note='Private seed preserved separately; no historical eligibility imported.',
        SourceCurrent='0/28', MarketCurrent='0/2', StrictREADY='0/22',
        automatic_HTTP=0, model_calls=0, send=False, default_enabled=False)
    (destination / 'bootstrap.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--destination', required=True)
    args = parser.parse_args()
    print(json.dumps(bootstrap(args.destination), indent=2))
