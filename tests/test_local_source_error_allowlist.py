"""Only the newly confirmed finite diagnostic-code omission; no Source replay."""
import ast
from hashlib import sha256
import inspect
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.jobs import unified_market_snapshot as job
from app.services import production_source_transport as transport


def record(tmp_path, error):
    try:
        raise error
    except ValueError as exc:
        job._record_local_failure(tmp_path, exc,
            config=SimpleNamespace(market='us', code_commit='e'*40),
            session='2026-11-19', generation='synthetic-us-source', before_owner_cleanup=True)
    return json.loads((tmp_path/'failure-diagnostic.json').read_bytes())


def test_exact_current_collection_stop_literal_is_recorded(tmp_path):
    value=record(tmp_path, ValueError('production_source_systemic_stop'))
    assert value['stable_error_code']=='production_source_systemic_stop'
    assert value['recorded_before_owner_cleanup'] is True
    assert value['source_seal_file_sha256'] is None
    path=tmp_path/'failure-diagnostic.json'
    integrity=json.loads((tmp_path/'failure-diagnostic-sha256.json').read_bytes())
    assert integrity['sha256']==sha256(path.read_bytes()).hexdigest()


@pytest.mark.parametrize('error', [
    ValueError('production_source_systemic_stop:SYNTHETIC_PRIVATE_DETAIL'),
    ValueError('production_source_systemic_stop', 'SYNTHETIC_PRIVATE_DETAIL'),
])
def test_dynamic_or_multiargument_detail_remains_redacted(tmp_path, error):
    assert record(tmp_path,error)['stable_error_code'] is None
    assert b'SYNTHETIC_PRIVATE_DETAIL' not in (tmp_path/'failure-diagnostic.json').read_bytes()


def test_added_code_matches_current_static_raise_not_exception_text_rule():
    tree=ast.parse(Path(transport.__file__).read_text())
    literals={node.exc.args[0].value for node in ast.walk(tree)
        if isinstance(node,ast.Raise) and isinstance(node.exc,ast.Call)
        and isinstance(node.exc.func,ast.Name) and node.exc.func.id=='ValueError'
        and len(node.exc.args)==1 and isinstance(node.exc.args[0],ast.Constant)}
    assert 'production_source_systemic_stop' in literals
    helper=ast.parse(inspect.getsource(job._record_local_failure))
    allowed=next(n.value for n in ast.walk(helper) if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='allowed_codes' for t in n.targets))
    assert isinstance(allowed,ast.Set) and all(isinstance(n,ast.Constant) and type(n.value) is str for n in allowed.elts)
    assert len(allowed.elts)==10
