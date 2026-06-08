import os

from app.config import get_settings

os.environ["ENABLE_LIVE_PROVIDERS"] = "false"
get_settings.cache_clear()
