import json

import pytest

from app.config import Settings
from app.services.production_runtime_preflight import kis_binding


def test_kis_comments_not_active(tmp_path, monkeypatch):
    for key in ("KIS_APP_KEY", "KIS_APP_SECRET", "KIS_SECRET_APP_KEY"):
        monkeypatch.delenv(key, raising=False)
    env = tmp_path / "synthetic.env"
    env.write_text("# KIS_APP_KEY=synthetic-key\n# KIS_APP_SECRET=synthetic-secret\n")
    with pytest.raises(ValueError, match="active_binding_missing"):
        kis_binding(Settings(_env_file=env), required=True)


@pytest.mark.parametrize("name", ["kis_app_secret", "kis_secret_app_key"])
def test_explicit_kis_binding_presence_only(name):
    settings = Settings(_env_file=None, kis_app_key="synthetic-key", **{name: "synthetic-secret"})
    receipt = kis_binding(settings, required=True)
    assert receipt["present"]
    assert receipt["app_secret_name"] == name.upper()
    assert "synthetic" not in json.dumps(receipt)
    assert "synthetic" not in repr(settings.kis_app_key)


def test_conflicting_aliases_fail_closed():
    with pytest.raises(ValueError, match="conflicting"):
        kis_binding(Settings(_env_file=None, kis_app_key="synthetic", kis_app_secret="one", kis_secret_app_key="two"), required=True)


def test_disabled_by_default():
    settings = Settings(_env_file=None)
    assert settings.unified_snapshot_adapter_version == "disabled"
    assert settings.unified_snapshot_live_delivery_authorized is False
