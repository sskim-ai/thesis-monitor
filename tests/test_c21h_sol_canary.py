from pathlib import Path
import pytest

from maintenance.c21h_sol_canary import require_fresh, validate_authorization, validate_scope
from maintenance.guarded_sol_host import TASK, digest


def test_fresh_runtime_rejects_any_prior_journal_or_marker(tmp_path):
    root, runtime, journal = (tmp_path/n for n in ('root', 'runtime', 'journal'))
    root.mkdir(); runtime.mkdir()
    require_fresh(root, runtime, journal)
    journal.mkdir()
    with pytest.raises(ValueError, match='JOURNAL_ALREADY_EXISTS'):
        require_fresh(root, runtime, journal)
    other_journal = tmp_path/'new-journal'
    (runtime/'host-control-ledger.json').write_text('[]')
    with pytest.raises(ValueError, match='RUNTIME_ALREADY_USED'):
        require_fresh(root, runtime, other_journal)


def test_old_approval_or_changed_request_is_not_new_issuance():
    scope = dict(run_id='C21H_SOL_HIGH_20261107_test', request_sha256='a'*64)
    auth = dict(task='C21H', approved=True, confirmed_no_concurrent_use=True,
        run_id=scope['run_id'], scope_sha256=digest(scope), request_sha256='a'*64,
        head='b'*40, model='gpt-6.1-sol', effort='high', maximum_contexts=2,
        stage_seconds=600, input_bytes=393216, output_bytes=131072, retries=0,
        financial_HTTP=0, operating_DB=0, send=False, approval_basis='SYNTHETIC_TEST_ONLY')
    validate_authorization(auth, scope, 'b'*40)
    for key, changed in [('task', 'C21G'), ('request_sha256', 'c'*64), ('confirmed_no_concurrent_use', False),
                         ('effort', 'medium'), ('retries', 1), ('head', 'd'*40)]:
        with pytest.raises(ValueError, match='CURRENT_EXPLICIT_APPROVAL_REQUIRED'):
            validate_authorization(dict(auth, **{key: changed}), scope, 'b'*40)


def test_capability_reuse_still_requires_fresh_paths_and_scope(tmp_path):
    root = tmp_path/'20261107-c21h'
    runtime = tmp_path/'c21h-20261107'
    journal = tmp_path/'c21h-sol-stage-journal-20261107'
    scope = dict(task='C21H', model='gpt-6.1-sol', effort='high', maximum_contexts=2,
        stage_seconds=600, input_bytes=393216, output_bytes=131072, retries=0, send=False,
        run_id='C21H_SOL_HIGH_20261107_test', root=str(root), runtime=str(runtime), journal=str(journal),
        guard_capability=TASK, packet_sha256='a'*64, scope_sha256='b'*64)
    class SyntheticBinding:
        scope_sha256 = 'b'*64
        def verify(self):
            return dict(owner_sha256='a'*64)
    binding = SyntheticBinding()
    binding.root, binding.scope = runtime, root/'private/scope.json'
    validate_scope(scope, binding)
    with pytest.raises(ValueError, match='FRESH_PATH_NAMES'):
        validate_scope(dict(scope, runtime=str(tmp_path/'c21g-20261107')), binding)
    with pytest.raises(ValueError, match='SOURCE_SCOPE_PIN'):
        validate_scope(dict(scope, scope_sha256='c'*64), binding)
