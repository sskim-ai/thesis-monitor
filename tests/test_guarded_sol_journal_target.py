from pathlib import Path

from maintenance.guarded_sol_canary import same_journal_target

TARGET = Path('/private/tmp/synthetic-task-only/research.sqlite3')


def test_original_store_plain_and_local_uris_same_exact_target():
    for value in (TARGET, str(TARGET), TARGET.as_uri()+'?mode=ro', TARGET.as_uri()+'?mode=rw'):
        assert same_journal_target(value, TARGET)


def test_other_path_and_remote_uri_do_not_expand_authority():
    for value in ('/private/tmp/other/research.sqlite3', 'file://other-host'+str(TARGET)+'?mode=ro',
                  str(TARGET.parent/'..'/'research.sqlite3')):
        assert not same_journal_target(value, TARGET)


def test_uri_query_cannot_change_the_original_open_contract():
    for suffix in ('?mode=rwc', '?mode=ro&mode=rw', '?mode=ro&immutable=1', '?mode=ro#other'):
        assert not same_journal_target(TARGET.as_uri()+suffix, TARGET)
