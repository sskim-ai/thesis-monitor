import os

os.environ["THESIS_MONITOR_ENV_FILE"] = ""

from app.config import get_settings

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["DATA_DIR"] = "/tmp/thesis-monitor-tests"
os.environ["ENABLE_LIVE_PROVIDERS"] = "false"
os.environ["ACTION_API_KEY"] = "test-action-key"
os.environ["MONITOR_RETRY_BASE_SECONDS"] = "0"
os.environ["NOTIFICATION_DRY_RUN"] = "true"
get_settings.cache_clear()
