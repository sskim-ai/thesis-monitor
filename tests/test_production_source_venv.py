"""Only venv-path boundaries; no financial, model, account or operating DB calls."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import venv

import pytest

from app.services.production_source_configuration import ProductionSourceConfiguration, ProtocolFile
from app.services.unified_run_artifacts import sha256_bytes
from tests.test_manual_source_budget import offline_only


@pytest.fixture
def configuration(tmp_path):
    root = tmp_path/'env'
    venv.EnvBuilder(with_pip=False, symlinks=True).create(root)
    native = tmp_path/'native'
    native.mkdir()
    protocol = tmp_path/'protocol.json'
    protocol.write_text('{}')
    item = dict(path=str(protocol),sha256=sha256_bytes(protocol.read_bytes()),purpose='PUBLIC_PROTOCOL')
    return dict(database_path=str(tmp_path/'metadata-only.sqlite3'),native_owner_root=str(native),
        native_python=str(root/'bin/python'),completed_close=item,issuer_identity=item,
        kr_listing_routing=dict(item,purpose='IDENTITY_ROUTING_ONLY'),kis_protocols={'protocol.json':item})


def test_real_venv_leaf_keeps_literal_subprocess_argument(configuration, tmp_path, monkeypatch):
    from app.services import production_source_context as context
    config = ProductionSourceConfiguration.model_validate(configuration)
    literal = configuration['native_python']
    assert Path(literal).is_symlink() and config.native_python == literal
    observed = []
    def inspected(argv, **kwargs):
        observed.append(argv)
        Path(argv[-1]).write_text(json.dumps(dict(owner_clean=True,credentials_present=True,
            live_provider=True,environment='real',base_url='https://api.kiwoom.com')))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(context.subprocess,'run',inspected)
    context.inspect_native(config,tmp_path)
    assert observed[0][0] == literal != str(Path(literal).resolve())
    assert observed[0][3:5] == ['inspect','--owner-root']


def test_symlink_parent_is_still_rejected(configuration, tmp_path):
    link = tmp_path/'parent-link'
    link.symlink_to(Path(configuration['native_python']).parent.parent, target_is_directory=True)
    with pytest.raises(ValueError,match='production_native_python_venv_required'):
        ProductionSourceConfiguration.model_validate(dict(configuration,native_python=str(link/'bin/python')))


def test_database_native_and_protocol_symlinks_remain_denied(configuration, tmp_path):
    for field in ('database_path','native_owner_root'):
        link = tmp_path/('linked-'+field)
        link.symlink_to(configuration[field],target_is_directory=field=='native_owner_root')
        with pytest.raises(ValueError,match='production_runtime_path_not_deployed'):
            ProductionSourceConfiguration.model_validate(dict(configuration,**{field:str(link)}))
    link = tmp_path/'linked-protocol.json'
    link.symlink_to(configuration['completed_close']['path'])
    with pytest.raises(ValueError,match='production_protocol_path_not_deployed'):
        ProtocolFile.model_validate(dict(configuration['completed_close'],path=str(link))).read()


def test_broken_missing_and_nonexecutable_venvs_rejected(configuration, tmp_path):
    python = Path(configuration['native_python'])
    python.unlink()
    python.symlink_to(tmp_path/'missing-python')
    with pytest.raises(ValueError,match='production_native_python_venv_unqualified'):
        ProductionSourceConfiguration.model_validate(configuration)
    python.unlink()
    python.write_bytes(b'not executable')
    python.chmod(0o600)
    with pytest.raises(ValueError,match='production_native_python_venv_unqualified'):
        ProductionSourceConfiguration.model_validate(configuration)
    (python.parent.parent/'pyvenv.cfg').unlink()
    with pytest.raises(ValueError,match='production_native_python_venv_required'):
        ProductionSourceConfiguration.model_validate(configuration)


def test_forged_venv_arbitrary_executable_and_bad_metadata_rejected(configuration):
    python = Path(configuration['native_python'])
    python.unlink()
    python.symlink_to('/bin/ls')
    with pytest.raises(ValueError,match='production_native_python_venv_unqualified'):
        ProductionSourceConfiguration.model_validate(configuration)
    python.unlink()
    python.symlink_to(Path(sys._base_executable).resolve())
    cfg = python.parent.parent/'pyvenv.cfg'
    cfg.write_text('executable = /bin/ls\nversion = 3.11\ninclude-system-site-packages = false\n')
    with pytest.raises(ValueError,match='production_native_python_venv_unqualified'):
        ProductionSourceConfiguration.model_validate(configuration)


def test_base_python_substitution_and_forbidden_paths_rejected(configuration, tmp_path):
    with pytest.raises(ValueError,match='production_native_python_venv_required'):
        ProductionSourceConfiguration.model_validate(dict(configuration,native_python=str(Path(sys._base_executable).resolve())))
    with pytest.raises(ValueError,match='production_native_python_venv_required'):
        ProductionSourceConfiguration.model_validate(dict(configuration,native_python='relative/bin/python'))
    blocked = tmp_path/'Reports/env'
    blocked.mkdir(parents=True)
    with pytest.raises(ValueError,match='production_native_python_venv_required'):
        ProductionSourceConfiguration.model_validate(dict(configuration,native_python=str(blocked/'bin/python')))
