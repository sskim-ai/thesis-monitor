import json
import os
from pathlib import Path

import pytest

os.environ["THESIS_MONITOR_ENV_FILE"] = ""

from app.config import get_settings

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["DATA_DIR"] = "/tmp/thesis-monitor-tests"
os.environ["ENABLE_LIVE_PROVIDERS"] = "false"
os.environ["ACTION_API_KEY"] = "test-action-key"
os.environ["MONITOR_RETRY_BASE_SECONDS"] = "0"
os.environ["NOTIFICATION_DRY_RUN"] = "true"
get_settings.cache_clear()


_ROOT = Path(__file__).resolve().parents[1]
_CLEAN_HISTORY_EXCLUSIONS = (
    _ROOT / "manifests" / "clean_history_excluded_proof_tests.json"
)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if not _CLEAN_HISTORY_EXCLUSIONS.is_file():
        return
    payload = json.loads(_CLEAN_HISTORY_EXCLUSIONS.read_text(encoding="utf-8"))
    excluded = {row["nodeid"] for row in payload["tests"]}
    marker = pytest.mark.skip(
        reason="clean-history excludes nonportable historical proof inputs"
    )
    for item in items:
        if item.nodeid in excluded:
            item.add_marker(marker)
